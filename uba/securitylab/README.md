# UBA Security Lab

An **intentionally vulnerable** practice service, for students on a
cybersecurity path. It is the odd one out in this project: every other service
is written to be safe, and this one is broken on purpose so you can learn to
find, understand and **fix** web vulnerabilities by hand.

It is the same idea as well-known training targets such as OWASP Juice Shop,
DVWA and WebGoat.

## ⚠ Rules of the lab (not optional)

1. **Attack only this lab, only on your own machine.** Port-scanning or
   attacking computers you do not own is a crime in most countries, including
   under Trinidad and Tobago's Computer Misuse Act. Your skills are legal only
   against targets you own or have **written** permission to test.
2. **Nothing in the lab is real.** The users, passwords, notes and "flags" are
   invented. The lab has its own throwaway database and shares nothing with the
   real app, the real PostgreSQL, or any real person's data. Breaking it
   teaches the technique and leaks nothing.
3. **Never deploy it.** It is published on `127.0.0.1` only and must never be
   put on a real network or the internet. Why that matters is lesson one.

## Start it

From the `uba` folder:

```
docker compose up -d --build securitylab
```

It listens on http://localhost:8100 (your machine only). Visit that address for
a list of endpoints. To stop just this service: `docker compose stop securitylab`.

## Part 1 - Audit (reconnaissance)

Before attacking anything, an auditor maps the target. Run the lab's own audit
helper, which does a small **port scan** and lists endpoints reachable without
logging in:

```
python3 securitylab/audit.py
```

If you have `nmap` installed, compare it with a real scanner against the same
authorised target:

```
nmap -sV -p 1-10000 127.0.0.1
```

Questions to answer: Which ports are open? Which service and version is on
8100? Which endpoints answer with no login? Everything reachable without
credentials is **attack surface** - the smaller, the better.

## Part 2 - Find, exploit, and FIX each flaw

Work through these in order. For each one: see it, exploit it against the fake
data, then read the fix and find where the **real backend** already does it
right. The fix is the whole point.

The code is tagged so you can study it: `grep -n "VULN\|DETECT\|FIX" securitylab/app/main.py`.

### 1. Information disclosure

- **See it:** open http://localhost:8100/docs and http://localhost:8100/debug.
- **Why it's bad:** `/docs` hands an attacker the whole map of the API, and
  `/debug` leaks environment variables (where real apps often keep secrets).
- **Fix:** don't ship debug endpoints; keep secrets out of responses; turn off
  or lock down API docs in production. The real backend keeps docs under
  `/api/docs` and a production build would disable them.

### 2. SQL injection (the big one)

  We use `curl -G --data-urlencode` below so the shell does not fight the
  quotes; the payload is the part after the `=`.
- **Detect it:** put a single quote in the username and watch for a database
  error:
  ```
  curl -s -G http://localhost:8100/login --data-urlencode "username=admin'" --data-urlencode "password=x"
  ```
- **Exploit it:** log in with no valid password by turning input into code.
  The first comments out the password check; the second makes the WHERE
  clause always true:
  ```
  curl -s -G http://localhost:8100/login --data-urlencode "username=admin' -- " --data-urlencode "password=anything"
  curl -s -G http://localhost:8100/login --data-urlencode "username=admin" --data-urlencode "password=' OR '1'='1"
  ```
  (Tip: `' OR '1'='1` has to go where it is not cancelled by the `AND password`
  that follows it - a good exercise is to work out on paper why putting it in
  the *password* field works but in the username field it does not.)
- **Fix:** never build SQL by joining strings. Use parameterised queries with
  `?` placeholders. Compare `securitylab/app/main.py` (the broken `f"...{username}..."`)
  with `backend/app/routers/auth.py`, which uses SQLAlchemy and bound
  parameters and is **not** injectable.

### 3. Verbose errors

- **See it:** the quote above returns the raw SQL error and the query.
- **Why it's bad:** it confirms the injection and reveals table and column
  names for the next step.
- **Fix:** log the detail on the server, return a generic message to the user.

### 4. Broken access control (IDOR)

- **Exploit it:** read other people's notes with no login, just by counting:
  ```
  curl http://localhost:8100/notes/1
  curl http://localhost:8100/notes/2
  curl http://localhost:8100/notes/3
  ```
- **Fix:** require a logged-in user and check they **own** the record before
  returning it. See how `backend/app/routers/bookings.py` refuses a booking
  that belongs to another passenger (returns 404, not someone else's data).

### 5. Reflected XSS

- **Detect it:** the search term is echoed back as raw HTML:
  ```
  curl "http://localhost:8100/search?q=<b>hello</b>"
  ```
  A real browser would run `<script>` sent this way.
- **Fix:** escape output, set a Content-Security-Policy, and prefer a framework
  that escapes by default. The real frontend uses React, which escapes text
  automatically, so the same input is shown, not executed.

### 6. Weak and plaintext credentials

- **Exploit it:** the admin password is `admin`; and via the SQL injection you
  can dump the `users` table and read every password, because they are stored
  in clear text.
- **Fix:** store a strong **hash** (the real backend uses Argon2), never the
  password itself, and reject weak passwords at registration.

## Part 3 - Defender's view

Switch sides. With the app running and the observability stack up
(`docker compose up -d`), repeat your attacks and watch what a defender sees:

- **Logs:** `docker compose logs -f securitylab` and `... backend` - attacks
  leave a trail (bursts of 401s, errors, odd paths).
- **Metrics / rate limiting:** the real backend counts failed logins
  (`uba_logins_total{result="failed"}`) and Traefik rate-limits `/api/auth`.
  Try your password-guessing against the **real** login and watch it get
  throttled, then find the failed-login spike on the Grafana dashboard.

Discussion: how would you detect each attack in production? What would you
alert on? This is the bridge from "attacker" to "defender", and most security
jobs are the defender.

## A map of OWASP

Each flaw here maps to an item in the OWASP Top 10, the industry's standard
list of the most common web risks. Looking it up is good homework:

| Lab flaw | OWASP Top 10 category |
|---|---|
| SQL injection, XSS | A03: Injection |
| IDOR | A01: Broken Access Control |
| Default/plaintext passwords | A07: Identification & Authentication Failures |
| /debug, /docs, verbose errors | A05: Security Misconfiguration |

## Exercises

1. Fix vulnerability #2 (SQL injection) in `app/main.py` using a parameterised
   query, rebuild the lab, and prove your exploit no longer works.
2. Fix the IDOR so `/notes/{id}` requires the note's owner.
3. Add a 7th deliberate flaw of your own and write its detect/fix notes.
4. Write a short incident report: as the defender, how did you notice attack
   #2, and what would you change to stop it?
