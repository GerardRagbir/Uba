#!/usr/bin/env python3
"""A small reconnaissance / audit tool for the SECURITY LAB only.

Run it with:   python3 audit.py

It demonstrates the first steps of a security audit against an authorised
target (the lab, on your own machine):

  1. a port scan - which doors are open?
  2. service fingerprinting - what is listening, and which version?
  3. endpoint enumeration - what can be reached without logging in?

It uses only the Python standard library, so it works without nmap. It does
NOT exploit anything; the exploiting is the exercise you do by hand, guided by
the README. It also refuses to point at anything other than localhost.

⚠  Only ever run audit tools against machines you own or have written
   permission to test. Scanning other people's systems is illegal.
"""

import socket
import sys
import urllib.error
import urllib.request

HOST = "127.0.0.1"          # localhost only, on purpose - see the warning above
LAB_PORT = 8100
# A small, common range to keep the demo quick. Real scanners sweep all 65535.
PORTS_TO_SCAN = [22, 80, 443, 3000, 5432, 8000, 8025, 8080, 8100, 9090]


def scan_ports() -> list[int]:
    print(f"[1] Port scan of {HOST} (a few common ports)")
    open_ports = []
    for port in PORTS_TO_SCAN:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            if sock.connect_ex((HOST, port)) == 0:
                open_ports.append(port)
                print(f"    OPEN   {port}")
    if not open_ports:
        print("    (nothing open - is the lab running? docker compose up -d securitylab)")
    print(f"    -> lesson: only the ports you truly need should be open.\n")
    return open_ports


def get(path: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{LAB_PORT}{path}", timeout=2) as response:
            return response.status, response.read(400).decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read(400).decode("utf-8", "replace")
    except OSError as error:
        return 0, str(error)


def enumerate_endpoints() -> None:
    print(f"[2] Endpoint enumeration on port {LAB_PORT} (no login used)")
    for path in ["/", "/docs", "/openapi.json", "/debug", "/notes/1", "/healthz"]:
        status, _ = get(path)
        reachable = "reachable WITHOUT auth" if status and status < 400 else f"status {status}"
        print(f"    {path:<16} {reachable}")
    print("    -> lesson: anything reachable without logging in is attack surface.\n")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] not in {HOST, "localhost"}:
        sys.exit("This tool only audits the local lab. Do not point it elsewhere.")
    print("UBA SECURITY LAB - audit demo (authorised target: your own machine)\n")
    if LAB_PORT in scan_ports():
        enumerate_endpoints()
        print("Next: open README.md and work through finding and FIXING each flaw.")
    else:
        print("The lab does not seem to be up. Start it, then run this again.")


if __name__ == "__main__":
    main()
