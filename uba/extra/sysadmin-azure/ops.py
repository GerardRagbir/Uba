"""Everyday Azure ops for UBA, wrapped in Python.

Sysadmins automate the boring, error-prone CLI dance. This thin wrapper over the
`az` CLI gives you memorable commands and one place to change settings. Python is
the glue; `az` does the work.

Usage:
    python ops.py status      # show the backend container app + its replicas
    python ops.py url         # print the public URL
    python ops.py logs        # stream the backend logs
    python ops.py restart     # restart the latest revision
    python ops.py scale 3     # set the max replica count

Prereq: az login
"""

from __future__ import annotations

import subprocess
import sys

# Must match provision.sh
RG = "uba-demo-rg"
APP = "uba-backend"


def az(*args: str, capture: bool = False) -> str:
    """Run an `az` command. Fail loudly — a silent ops script is dangerous."""
    cmd = ["az", *args]
    print("+ " + " ".join(cmd))
    result = subprocess.run(cmd, text=True, capture_output=capture)
    if result.returncode != 0:
        sys.exit(f"az failed (exit {result.returncode})")
    return (result.stdout or "").strip()


def status() -> None:
    az("containerapp", "show", "-g", RG, "-n", APP,
       "--query", "{name:name, state:properties.runningStatus, "
                  "fqdn:properties.configuration.ingress.fqdn, "
                  "image:properties.template.containers[0].image}",
       "-o", "yaml")
    az("containerapp", "replica", "list", "-g", RG, "-n", APP, "-o", "table")


def url() -> None:
    fqdn = az("containerapp", "show", "-g", RG, "-n", APP,
              "--query", "properties.configuration.ingress.fqdn", "-o", "tsv", capture=True)
    print(f"https://{fqdn}")


def logs() -> None:
    # --follow streams; Ctrl-C to stop.
    az("containerapp", "logs", "show", "-g", RG, "-n", APP, "--follow", "--tail", "50")


def restart() -> None:
    rev = az("containerapp", "revision", "list", "-g", RG, "-n", APP,
             "--query", "[?properties.active].name | [0]", "-o", "tsv", capture=True)
    az("containerapp", "revision", "restart", "-g", RG, "-n", APP, "--revision", rev)


def scale(n: str) -> None:
    az("containerapp", "update", "-g", RG, "-n", APP, "--max-replicas", n)


COMMANDS = {"status": status, "url": url, "logs": logs, "restart": restart}


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] == "scale":
        if args[:1] == ["scale"] and len(args) == 2:
            scale(args[1])
            return
        sys.exit(__doc__)
    cmd = COMMANDS.get(args[0])
    if not cmd:
        sys.exit(__doc__)
    cmd()


if __name__ == "__main__":
    main()
