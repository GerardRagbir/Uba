"""Summarise Traefik's access logs — the edge's own record of every request.

Traefik writes one JSON line per request. Alloy ships those lines to Loki (see
the main uba observability stack). This script queries Loki (through Traefik) for
Traefik's logs and answers the questions a network engineer asks of an access
log: who is hitting us, what are they getting back, and what is slow?

Standard library only. Talks to Loki via the edge, like latency_report.py.

Usage:  python analyze_access_logs.py [minutes]   (default 30)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter

EDGE = os.environ.get("UBA_EDGE", "http://127.0.0.1")
LOKI_HOST = os.environ.get("LOKI_HOST", "grafana.localhost")  # Loki is proxied under Grafana's host? no —
# NOTE: Loki is NOT exposed through Traefik in the demo. The most reliable way to
# read it without publishing a port is through the backend container, which is on
# the same network. See the fallback below if the direct query fails.
LOKI_DIRECT = os.environ.get("LOKI_URL", "http://127.0.0.1:3100")


def query_loki(logql: str, minutes: int) -> list[str]:
    """Return raw log lines for the query over the last `minutes`."""
    end = int(time.time() * 1e9)
    start = end - minutes * 60 * int(1e9)
    params = urllib.parse.urlencode({"query": logql, "start": start, "end": end, "limit": "5000"})
    url = f"{LOKI_DIRECT}/loki/api/v1/query_range?{params}"
    with urllib.request.urlopen(url, timeout=8) as resp:
        body = json.load(resp)
    lines: list[str] = []
    for stream in body.get("data", {}).get("result", []):
        for _ts, line in stream["values"]:
            lines.append(line)
    return lines


def main() -> None:
    minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(f"Reading Traefik access logs from Loki ({LOKI_DIRECT}), last {minutes} min\n")

    try:
        lines = query_loki('{service="traefik"}', minutes)
    except Exception as error:  # noqa: BLE001
        print(f"Could not reach Loki at {LOKI_DIRECT}: {error}\n")
        print("Loki is on the private Docker network. Easiest fix — run this from")
        print("inside the stack:\n")
        print('  docker compose run --rm -v "$PWD/extra:/extra" backend \\')
        print('    python /extra/network-engineering/analyze_access_logs.py')
        print("\n(or publish Loki: add ports ['3100:3100'] to the loki service).")
        return

    statuses: Counter[str] = Counter()
    clients: Counter[str] = Counter()
    routers: Counter[str] = Counter()
    slow: list[tuple[float, str, str]] = []
    parsed = 0

    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # not every Traefik line is JSON (startup banners etc.)
        parsed += 1
        code = str(entry.get("DownstreamStatus", "?"))
        statuses[code] += 1
        clients[entry.get("ClientHost", "?")] += 1
        routers[entry.get("RouterName", entry.get("ServiceName", "?"))] += 1
        # Duration is in nanoseconds in Traefik's JSON log.
        dur_ms = entry.get("Duration", 0) / 1e6
        path = entry.get("RequestPath", "?")
        slow.append((dur_ms, str(code), path))

    if parsed == 0:
        print("No JSON access-log lines found. Generate some traffic and retry.")
        return

    print(f"Requests analysed: {parsed}\n")

    print("By status code:")
    for code, n in statuses.most_common():
        flag = "  <- rate limited" if code == "429" else ("  <- server error" if code.startswith("5") else "")
        print(f"  {n:6}  HTTP {code}{flag}")

    print("\nBusiest clients (watch for one IP dominating = possible abuse):")
    for ip, n in clients.most_common(5):
        print(f"  {n:6}  {ip}")

    print("\nTraffic by router/service:")
    for name, n in routers.most_common(8):
        print(f"  {n:6}  {name}")

    print("\n10 slowest requests (ms):")
    for dur_ms, code, path in sorted(slow, reverse=True)[:10]:
        print(f"  {dur_ms:8.1f}  [{code}]  {path}")


if __name__ == "__main__":
    main()
