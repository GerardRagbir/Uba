# ============================================================
# UBA Security Lab - an INTENTIONALLY VULNERABLE practice target
# ============================================================
#
# ⚠  READ THIS FIRST  ⚠
#
# This service is broken ON PURPOSE. It is a safe punching bag for students
# learning how attackers find and exploit web flaws, and - more importantly -
# how to detect and fix them. It is the opposite of the real `backend`
# service: wherever this file does something dangerous, the comment shows
# the FIX, which is usually exactly what the real backend already does.
#
# RULES OF THE LAB (print these on the wall):
#   1. Only ever attack THIS service, running on your own machine.
#      Scanning or attacking computers you do not own is a crime in most
#      countries, including under Trinidad and Tobago's Computer Misuse Act.
#   2. Nothing in here is real. The "users", "secrets" and "notes" below are
#      made-up. There is no connection to the real app, its database, or any
#      real person's data. Breaking this teaches the technique; it leaks
#      nothing.
#   3. This container is published on 127.0.0.1 only and must NEVER be put on
#      a real network or the internet. That restriction is itself lesson one.
#
# Each weakness is tagged so you can grep for them:
#   VULN   - the mistake
#   DETECT - how an auditor would notice it (scanning, reading responses)
#   FIX    - how to make it safe (compare with the real backend)

import os
import sqlite3
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

DB = "/tmp/lab.db"

app = FastAPI(
    title="UBA Security Lab (intentionally vulnerable)",
    description="A deliberately insecure practice target. Do not deploy.",
    # VULN 0 (information disclosure): interactive API docs are left open to
    #   anyone, advertising every endpoint and its parameters.
    # DETECT: browse to /docs or fetch /openapi.json - the whole attack
    #   surface is handed to you.
    # FIX: the real backend serves docs under /api and a production deploy
    #   turns them off or puts them behind a login.
)


# ---------- the lab's fake world (seeded once) ----------

def setup() -> None:
    db = sqlite3.connect(DB)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY, owner TEXT, body TEXT);
        """
    )
    if db.execute("SELECT count(*) FROM users").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            [
                # VULN 1 (weak/default + plaintext passwords): the admin uses
                #   a default password and every password is stored in clear
                #   text. One peek at the table and every account is yours.
                # DETECT: try common pairs (admin/admin); dump the table via
                #   the SQL-injection below and read the passwords directly.
                # FIX: the real backend stores an Argon2 HASH, never the
                #   password, and forbids weak passwords at registration.
                ("admin", "admin", "admin"),
                ("driver_sam", "trinidad1", "driver"),
                ("pax_jo", "password123", "pax"),
            ],
        )
        db.executemany(
            "INSERT INTO notes (owner, body) VALUES (?, ?)",
            [
                ("admin", "FAKE lab flag: UBA{you-found-the-admin-note}"),
                ("driver_sam", "FAKE note: remember to service the FAKE car"),
                ("pax_jo", "FAKE note: book a ride to the FAKE airport"),
            ],
        )
    db.commit()
    db.close()


setup()


@app.get("/", response_class=PlainTextResponse)
def home() -> str:
    return (
        "UBA SECURITY LAB - intentionally vulnerable practice target.\n"
        "Only attack this service, on your own machine. See README.md.\n"
        "Endpoints: /login  /notes/{id}  /search  /debug  /docs\n"
    )


# ---------- VULN 2: SQL injection ----------

@app.get("/login")
def login(username: str, password: str):
    """Log in. This is the single most important lesson in the lab."""
    db = sqlite3.connect(DB)
    try:
        # VULN 2 (SQL injection): the username and password are glued
        #   straight into the SQL string, so input becomes code. Logging in
        #   as   username = admin' --   ignores the password entirely, and
        #   username = ' OR '1'='1    matches every row.
        # DETECT: put a single quote ' in the username. A 500 error / SQL
        #   message leaking back is the classic fingerprint of injection.
        # FIX: never build SQL with +/f-strings. Use a parameterised query
        #   with ? placeholders, exactly as the real backend does:
        #     db.execute("SELECT ... WHERE username = ? AND password = ?",
        #                (username, password))
        query = (
            "SELECT username, role FROM users "
            f"WHERE username = '{username}' AND password = '{password}'"
        )
        row = db.execute(query).fetchone()
    except sqlite3.Error as error:
        # VULN 3 (verbose errors): the raw database error is handed back to
        #   the caller, confirming the injection and revealing table/column
        #   names. DETECT: read the error text. FIX: log the detail server
        #   side and return a generic "something went wrong" to the client.
        return JSONResponse(status_code=500, content={"sql_error": str(error), "query": query})
    finally:
        db.close()

    if row is None:
        return JSONResponse(status_code=401, content={"ok": False, "message": "Wrong username or password"})
    return {"ok": True, "username": row[0], "role": row[1]}


# ---------- VULN 4: broken access control (IDOR) ----------

@app.get("/notes/{note_id}")
def read_note(note_id: int):
    """Read a note by its number."""
    db = sqlite3.connect(DB)
    row = db.execute("SELECT owner, body FROM notes WHERE id = ?", (note_id,)).fetchone()
    db.close()
    if row is None:
        return JSONResponse(status_code=404, content={"message": "No such note"})
    # VULN 4 (IDOR / broken access control): the note is returned to anyone
    #   who asks, with no login and no check that the caller owns it. Just
    #   count up 1, 2, 3 to read everybody's notes.
    # DETECT: fetch /notes/1, /notes/2, ... with no credentials and watch
    #   other people's data come back.
    # FIX: require a logged-in user (as the real backend does with its
    #   session cookie) AND check that note.owner == current_user before
    #   returning it. The real /api/bookings/{id}/cancel does exactly this.
    return {"id": note_id, "owner": row[0], "body": row[1]}


# ---------- VULN 5: reflected cross-site scripting (XSS) ----------

@app.get("/search", response_class=PlainTextResponse)
def search(q: str = ""):
    # VULN 5 (reflected XSS): the search term is echoed back into the page
    #   without escaping, so <script>...</script> in q would run in a
    #   victim's browser.
    # DETECT: send q=<b>hi</b> and see raw HTML come back instead of text.
    # FIX: escape output (html.escape), set a Content-Security-Policy, and
    #   let a framework like React render text - React escapes by default,
    #   which is why the real frontend is not vulnerable here.
    return PlainTextResponse(
        f"<html><body>You searched for: {q}</body></html>",
        media_type="text/html",
    )


# ---------- VULN 6: information disclosure ----------

@app.get("/debug")
def debug(request: Request):
    # VULN 6 (information disclosure): a "debug" endpoint dumps the server's
    #   environment, including any secrets in environment variables, plus
    #   internal details useful for the next stage of an attack.
    # DETECT: fetch /debug - reconnaissance like this is step one of an
    #   audit. Also notice this endpoint needs no authentication.
    # FIX: never ship debug/introspection endpoints to production; keep
    #   secrets out of responses; require admin auth for any diagnostics.
    return {
        "note": "This endpoint should never exist in production.",
        "environment": dict(os.environ),
        "server_time": time.time(),
        "client_ip": request.client.host if request.client else None,
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
