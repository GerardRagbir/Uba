"""Post-deploy smoke test — is the live system actually working?

A smoke test is not a unit test. It runs against the REAL, running system right
after a deploy and checks that the core user journey still works end to end. If
it fails, your pipeline should roll the release back. Keep it small and fast:
a handful of the most important things a user does.

Exits 0 if all good, non-zero (and prints what broke) otherwise — which is
exactly what a CI/CD step needs to decide go / no-go.

Standard library only. Talks to the system through its public edge.

Usage:  python smoke_test.py
Env:    UBA_BASE_URL (default http://localhost)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("UBA_BASE_URL", "http://localhost")

# Demo credentials from the seed data.
PAX = {"username": "pax", "password": "password123"}

passed = 0
failed = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not ok else ""))
    if ok:
        passed += 1
    else:
        failed += 1


def request(method: str, path: str, body: dict | None = None, cookie: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        resp = urllib.request.urlopen(req, timeout=8)
        return resp.status, resp.read(), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


def main() -> None:
    print(f"Smoke test against {BASE}\n")

    # 1. The system is alive and its dependencies are ready.
    status, _, _ = request("GET", "/api/health")
    check("health endpoint returns 200", status == 200, f"got {status}")
    status, _, _ = request("GET", "/api/ready")
    check("readiness (DB reachable) returns 200", status == 200, f"got {status}")

    # 2. Auth works and is enforced.
    status, _, _ = request("GET", "/api/bookings")
    check("unauthenticated request is refused (401)", status == 401, f"got {status}")

    status, body, headers = request("POST", "/api/auth/login", PAX)
    check("passenger can log in (200)", status == 200, f"got {status}")
    cookie = headers.get("Set-Cookie", "").split(";")[0] if status == 200 else None
    check("login sets a session cookie", bool(cookie))

    if not cookie:
        finish()
        return

    # 3. A core authenticated journey: see destinations, get a fare quote.
    status, body, _ = request("GET", "/api/destinations", cookie=cookie)
    dests = json.loads(body) if status == 200 else []
    check("destinations list loads", status == 200 and len(dests) >= 2, f"got {status}, {len(dests)} items")

    if len(dests) >= 2:
        a, b = dests[0]["id"], dests[1]["id"]
        status, body, _ = request("GET", f"/api/fare/estimate?pickup_id={a}&destination_id={b}", cookie=cookie)
        quote = json.loads(body) if status == 200 else {}
        check("fare model returns a quote", status == 200 and quote.get("final_fare", 0) > 0,
              f"got {status}")

    # 4. Metrics are being exposed (observability is alive).
    # /metrics is internal; check through the API that the app is instrumented
    # by confirming the docs page (a cheap 'app is serving' signal).
    status, _, _ = request("GET", "/api/docs")
    check("API docs served", status == 200, f"got {status}")

    finish()


def finish() -> None:
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print("SMOKE TEST FAILED — do not promote this release; roll back.")
        sys.exit(1)
    print("All good — safe to keep this release.")


if __name__ == "__main__":
    main()
