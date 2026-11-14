"""A network engineer's latency & traffic report, from Prometheus.

Pulls the same numbers the Grafana dashboards show, but as a plain text report
you could paste into a ticket. Standard library only.

It reaches Prometheus THROUGH Traefik (the edge), exactly as a browser would:
we connect to 127.0.0.1:80 and set the Host header to prometheus.localhost, so
the proxy routes us to Prometheus. That round trip is itself the lesson.

Usage:  python latency_report.py
Env:    UBA_EDGE (default http://127.0.0.1)  — the Traefik entrypoint
        PROM_HOST (default prometheus.localhost)
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

EDGE = os.environ.get("UBA_EDGE", "http://127.0.0.1")
PROM_HOST = os.environ.get("PROM_HOST", "prometheus.localhost")


def promql(query: str) -> list[dict]:
    """Run an instant PromQL query via Traefik and return the result vector."""
    url = f"{EDGE}/api/v1/query?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={"Host": PROM_HOST})
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = json.load(resp)
    if body.get("status") != "success":
        raise RuntimeError(f"Prometheus error: {body}")
    return body["data"]["result"]


def one(query: str, default: float = 0.0) -> float:
    rows = promql(query)
    return float(rows[0]["value"][1]) if rows else default


def table(query: str, label: str) -> list[tuple[str, float]]:
    rows = promql(query)
    out = [(r["metric"].get(label, "?"), float(r["value"][1])) for r in rows]
    return sorted(out, key=lambda x: x[1], reverse=True)


def main() -> None:
    print("=" * 60)
    print(f"UBA network report  (edge {EDGE}, via Host: {PROM_HOST})")
    print("=" * 60)

    try:
        rps = one("sum(rate(uba_http_requests_total[5m]))")
    except Exception as error:  # noqa: BLE001
        print(f"\nCould not reach Prometheus through Traefik: {error}")
        print("Is the stack up (docker compose up -d) and has it had traffic?")
        return

    err = one('sum(rate(uba_http_requests_total{status=~"5.."}[5m]))')
    err_pct = (err / rps * 100) if rps else 0.0
    print(f"\nThroughput : {rps:.2f} req/s")
    print(f"Errors(5xx): {err_pct:.2f}% of requests")

    print("\nLatency (seconds), whole API:")
    for q, label in [("0.50", "p50"), ("0.95", "p95"), ("0.99", "p99")]:
        v = one(f"histogram_quantile({q}, sum(rate(uba_http_request_duration_seconds_bucket[5m])) by (le))")
        print(f"  {label}: {v*1000:7.1f} ms")

    print("\nBusiest routes (req/s):")
    for route, v in table("sum(rate(uba_http_requests_total[5m])) by (path)", "path")[:8]:
        print(f"  {v:6.2f}  {route}")

    print("\nSlowest routes (p95, ms):")
    slow = table(
        "histogram_quantile(0.95, sum(rate(uba_http_request_duration_seconds_bucket[5m])) by (le, path))",
        "path",
    )
    for route, v in [r for r in slow if r[1] > 0][:8]:
        print(f"  {v*1000:7.1f}  {route}")

    print("\nTraffic seen by the proxy (Traefik), by status code:")
    for code, v in table("sum(rate(traefik_service_requests_total[5m])) by (code)", "code"):
        flag = "  <- rate-limited!" if code == "429" else ""
        print(f"  {v:6.2f}  HTTP {code}{flag}")


if __name__ == "__main__":
    main()
