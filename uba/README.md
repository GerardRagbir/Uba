# UBA Taxi Booking - production-style version

This is the same taxi booking app you built in class, taken to the shape a
software team would actually run. It is still a demo, but every part of it is
a real tool you will meet in industry.

This README has two jobs:

1. Get the system running on your laptop so you can poke at it.
2. Show you **what to learn, beyond your degree, to be able to build this yourself.**

## The same app, four times

| Folder | Screen | Data | Runs as |
|---|---|---|---|
| `uba-basic` | console menus | text files | one Python script |
| `uba-gui` | NiceGUI pages | text files | one Python script |
| `uba-advanced` | NiceGUI pages | SQLite, hashed passwords | one Python script |
| `uba` (this one) | Next.js website | PostgreSQL | seven containers behind a reverse proxy |

The booking rules have not changed since `uba-basic`: a passenger books, a
driver accepts, the trip is completed and rated. Open
`backend/app/routers/bookings.py` and you will recognise every `if`. What
changed is everything *around* those rules. That "everything around" is what
this guide is about.

## 1. Run it

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/)
installed and running. Nothing else: no Python, no Node, no database.

```
docker compose up --build -d
```

The first run downloads and builds for a few minutes. Then open:

| Address | What it is |
|---|---|
| http://localhost | the app |
| http://localhost/api/docs | interactive API documentation, generated from the code |
| http://mail.localhost | Mailpit: every email the app "sends" lands here |
| http://grafana.localhost | dashboards: **UBA overview** and **UBA security** (no login needed to view) |
| http://prometheus.localhost | the raw metrics database |
| http://traefik.localhost | the reverse proxy's dashboard: routes and services |

Demo accounts:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `password123` |
| Driver | `driver` | `password123` |
| Driver | `driver2` | `password123` |
| Passenger | `pax` | `password123` |

Each account's email is its username at `example.com`, for example
`pax@example.com`.

Useful commands:

```
docker compose ps              # is everything healthy?
docker compose logs -f backend # watch the API's logs
docker compose down            # stop (data is kept)
docker compose down --volumes  # stop and wipe all data
```

If port 80 is taken, copy `.env.example` to `.env` and change `HTTP_PORT` and
`UBA_PUBLIC_URL`. If the `*.localhost` addresses do not open in your browser,
use Chrome or Firefox.

## 2. A ten-minute tour

Do these in order. Each one shows off one part of the system.

1. **Watch the map.** Log in as `pax`. The map of Trinidad behind the page
   cannot be dragged, but it follows you: choose a pickup and it flies in to
   that town, choose a destination and it pulls out and flies in there.
2. **See the fare model think.** As `pax`, pick a pickup and destination. The
   fare card shows the distance and a line-by-line breakdown - base fare, a
   time-of-day/traffic surcharge, and a demand multiplier - not just a number.
   To make demand spike, book a few rides without any driver accepting them:
   with more riders waiting than drivers free, the next quote shows ⚡ surge.
   (See `backend/app/fare_model.py`.)
3. **Two users at once.** Log in as `pax` in one browser window and as
   `driver` in a private window. Book a ride as pax. Within five seconds it
   appears for driver. Accept it and watch the passenger's screen change.
4. **Forgot password, done properly.** Log out, click "Forgot password?" and
   enter `pax@example.com`. Open http://mail.localhost, read the email and
   follow the link. The link works once and expires in 30 minutes.
5. **The API without the website.** Open http://localhost/api/docs. Every
   endpoint is listed with the exact data it accepts. The website is only one
   possible client of this API; a mobile app could use the same one.
6. **Watch it being used.** Open http://grafana.localhost. The **UBA overview**
   dashboard shows request rates, response-time percentiles, live booking
   counts, fares and surge - and, at the bottom, the actual log lines from
   Loki. Click around the app and watch the graphs move.
7. **Trip the alarm, then investigate.** Type a wrong password 20 times
   quickly. The proxy starts refusing you (`Too many attempts`). Now open the
   **UBA security** dashboard (top-left dashboard switcher): failed logins and
   rate-limited (429) requests spike, and the "Failed logins" log panel shows
   each attempt with its client IP.
8. **Read a request's story.** Every backend log line is JSON with a
   `request_id`, a severity `level`, and the caller's `user_id` and `client_ip`.
   See them raw with `docker compose logs backend`, or searchable in Grafana's
   log panels (e.g. filter to `level="ERROR"`).
9. **See the front door.** Open http://traefik.localhost and find the routers:
   which addresses go to which container.

## 3. How the pieces fit

```
                       your browser
                            |
                            v
                  +-------------------+
                  |      Traefik      |  reverse proxy: the only way in
                  +-------------------+
                    |               |
        everything else           /api/*
                    v               v
            +------------+    +------------+      +-----------+
            |  frontend  |    |  backend   |----->|  mailpit  |  email
            |  Next.js   |    |  FastAPI   |      +-----------+
            +------------+    +------------+
                                    |
                                    v
                              +------------+
                              |  postgres  |  database
                              +------------+

        Prometheus <---- scrapes /metrics from backend and Traefik   (numbers)
        Loki       <---- Alloy ships every container's logs here      (log lines)
        Grafana    <---- draws graphs from Prometheus AND shows logs from Loki
```

What happens when a passenger presses **Book ride**:

1. The browser sends `POST http://localhost/api/bookings` with the pickup and
   destination ids, and the login cookie.
2. **Traefik** sees the path starts with `/api` and passes it to the backend.
3. **FastAPI** checks the request body against `BookingIn` and rejects it if
   the shape is wrong.
4. The `require_role("pax")` dependency reads the cookie, verifies the token
   and loads the user. No valid cookie, no booking.
5. The route asks the **fare model** to price the ride - from the distance,
   the time, the traffic and how busy things are right now (never a fare sent
   by the browser) - and inserts the booking. (See section 6.)
6. A counter, `uba_booking_events_total`, goes up by one, and a JSON log line
   is written with the request's id and how long it took.
7. The new booking is returned as JSON, and **Next.js** redraws the table.

## 4. Map of the repository

```
uba/
  docker-compose.yml     the whole system in one file: start here
  .env.example           the settings you can change
  Makefile               shortcuts (make up, make down, make test)

  backend/               the API (Python, FastAPI)
    Dockerfile           how the backend image is built
    app/
      main.py            creates the app, health checks
      config.py          every setting, read from environment variables
      database.py        the connection to PostgreSQL
      models.py          the tables, as classes (User -> Pax, Driver, Admin)
      schemas.py         the shape of every request and response
      security.py        password hashing, login tokens, role checks
      observability.py   structured logs, Prometheus metrics, request ids
      fare_model.py      the fare model: prices a ride from distance, time,
                         traffic and live demand (the "AI" in the engine)
      emailer.py         sending email
      seed.py            the demo data
      routers/           the endpoints: auth, bookings, vehicles, ...
    tests/               automated tests for the API

  frontend/              the website (TypeScript, Next.js, Tailwind)
    Dockerfile           how the frontend image is built
    app/                 one folder per page: login, pax, driver, admin, ...
    components/          reusable pieces: buttons, tables, the page frame,
                         and MapBackdrop.tsx, the map behind every page
    lib/                 talking to the API, polling, "who is logged in?"

  infra/                 configuration for the supporting services
    prometheus/          what metrics to scrape
    grafana/             the data sources and the two dashboards (overview + security)
    loki/                the log store's config
    alloy/               the log shipper's config (tails all container logs)

  securitylab/           an INTENTIONALLY VULNERABLE service for security
                         students - see its own README (and section 9 below)
```

Good first files to read, in order: `docker-compose.yml`,
`backend/app/models.py`, `backend/app/routers/bookings.py`,
`frontend/app/pax/page.tsx`.

## 5. What to learn beyond your degree

Your degree gives you the foundations this is built on: programming,
object-oriented design, data structures, how databases and networks work in
principle. You already used most of them in `uba-basic`.

What a degree usually does not have time for is the **tooling and practice** of
running software for real users. Below is that gap, split into ten areas. For
each: what it is, where to see it in this project, and what to study.

### 1. Git and working in a team

*Why:* every other skill here assumes your code is in version control.

- **Learn:** commits, branches, merging, pull requests, resolving conflicts,
  writing a useful commit message, `.gitignore`.
- **In this project:** `.gitignore` keeps secrets (`.env`) and build output out
  of the repository.
- **Start by:** putting your own copy of this project on GitHub and making
  every change through a branch and a pull request, even working alone.

### 2. The command line and Linux

*Why:* servers have no desktop. Containers are small Linux machines.

- **Learn:** moving around the file system, pipes and redirection,
  environment variables, processes and ports, `curl`, `ssh`, reading logs.
- **In this project:** `docker compose exec backend sh` puts you inside the
  backend's Linux container.
- **Start by:** doing the tour in section 2 again using `curl` instead of the
  browser.

### 3. HTTP and API design

*Why:* the frontend and backend are separate programs that only speak HTTP.

- **Learn:** methods (GET, POST, PUT), status codes (200, 201, 401, 403, 404,
  409, 422), headers, cookies, JSON, REST conventions, what "stateless" means.
- **In this project:** `backend/app/routers/`. Notice which status code each
  failure returns, and that they mean different things.
- **Start by:** opening your browser's developer tools (Network tab) and
  watching the requests while you use the app.

### 4. A backend framework: FastAPI

*Why:* nobody writes a web server from scratch.

- **Learn:** Python type hints, Pydantic models, routes, dependency injection
  (`Depends`), async basics, automatic API docs.
- **In this project:** `schemas.py` validates all input before your code runs.
  `Depends(require_role("admin"))` protects a route in one line.
- **Start by:** the official FastAPI tutorial, then add a
  `DELETE /api/destinations/{id}` endpoint here.

### 5. Real databases: PostgreSQL and an ORM

*Why:* SQLite is one file for one program. Real systems share a database
server between many processes.

- **Learn:** SQL joins, primary and foreign keys, unique constraints, indexes,
  transactions, an ORM (SQLAlchemy), **migrations** (Alembic), backups.
- **In this project:** `models.py`. The `accept_booking` route shows a
  transaction problem you only meet with many users: two drivers pressing
  Accept at the same instant.
- **Start by:** `docker compose exec postgres psql -U uba` and writing queries
  by hand. Then replace `create_all` with Alembic migrations.

### 6. Authentication and web security

*Why:* this is where mistakes hurt real people.

- **Learn:** password hashing (Argon2, bcrypt), sessions vs tokens (JWT),
  httpOnly cookies, HTTPS, the OWASP Top 10 (injection, XSS, CSRF, broken
  access control), rate limiting, never trusting the client.
- **In this project:** `security.py` and `routers/auth.py`. Compare the
  forgot-password flow here (one-time emailed link) with the security question
  in `uba-advanced`, and with the plain-text passwords in `uba-basic`.
- **Start by:** reading the OWASP Top 10 and finding where this project
  defends against each item, and where it does not.

### 7. Frontend: TypeScript, React, Next.js, Tailwind

*Why:* users expect a website, and the web has its own language and tools.

- **Learn, in this order:** HTML and CSS, JavaScript (especially `fetch`,
  promises and `async`/`await`), TypeScript, React (components, props, state,
  effects), then Next.js (routing, building), then Tailwind (utility classes).
- **In this project:** `frontend/app/pax/page.tsx` is the passenger page you
  know from `uba-gui`, rewritten in React. Put the two side by side.
  `frontend/components/MapBackdrop.tsx` shows how a third-party library
  (MapLibre, drawing OpenStreetMap tiles) is wrapped so that any page can
  move the map with one function call.
- **Start by:** plain HTML, CSS and JavaScript first. Skipping straight to
  React is the most common mistake; the framework only makes sense once you
  have felt the problem it solves.

### 8. Containers: Docker and Compose

*Why:* "it works on my machine" stops being an excuse. The image that runs on
your laptop is the image that runs in production.

- **Learn:** images vs containers, writing a Dockerfile, layers and caching,
  multi-stage builds, volumes, networks, environment variables, healthchecks,
  Docker Compose.
- **In this project:** the two `Dockerfile`s and `docker-compose.yml`. Every
  line is commented.
- **Start by:** writing a Dockerfile for `uba-advanced` and running it in a
  container.

### 9. Networking and reverse proxies: Traefik

*Why:* users reach one address. Something has to decide which program answers.

- **Learn:** DNS, ports, what a reverse proxy does, routing by host and path,
  TLS certificates and HTTPS (Let's Encrypt), load balancing, rate limiting.
- **In this project:** the `labels:` under each service in
  `docker-compose.yml` are Traefik's routing rules. The login rate limit is
  three of those lines.
- **Start by:** adding a second copy of the backend
  (`docker compose up -d --scale backend=2`) and watching Traefik share
  requests between them.

### 10. Observability, testing and delivery

*Why:* once real people use your software, you need to know when it breaks
before they tell you, and you need to change it without fear.

- **Learn:**
  - **Observability:** structured logs, metrics, traces (the "three
    pillars"), Prometheus and PromQL, Grafana dashboards, alerting.
  - **Testing:** unit and integration tests with `pytest`, what is worth
    testing.
  - **Delivery:** CI/CD (GitHub Actions) to run tests and build images on
    every push; deploying to a cloud provider.
- **In this project:** `observability.py`, `infra/`, and `backend/tests/`.
  The tests cover the booking lifecycle, role checks and password reset.
- **Start by:** running the tests (`make test`), breaking a rule in
  `bookings.py` on purpose, and watching a test catch it.

### A realistic order

Do not try to learn all ten at once. A path that works:

1. Git and the command line (areas 1-2). Everything else needs them.
2. HTTP, then FastAPI, then PostgreSQL (areas 3-5). You can now build an API.
3. Authentication and security (area 6). You can now build one safely.
4. HTML, CSS, JavaScript, then React (area 7). You can now build its website.
5. Docker, then a reverse proxy (areas 8-9). You can now ship it.
6. Tests, observability and CI/CD (area 10). You can now keep it running.

Expect this to take months of steady practice alongside your degree, not
weeks. The fastest way through is to build one small project of your own at
each step rather than only reading.

## 6. The fare model — the "AI" in the booking engine

Early versions of this app charged a flat fare per destination. This version
**prices each ride** with a small model in `backend/app/fare_model.py`. It is
the intelligent part of the booking engine, and it is built from data the
system already has:

| Input | Where it comes from |
|---|---|
| **Route / distance** | the straight-line (haversine) distance between the pickup and destination map coordinates |
| **Time of day** | a late-night / evening surcharge, from the clock |
| **Traffic** | rush hour inferred from the hour and the day of week |
| **Demand** | how many riders are waiting versus how many drivers are free, right now |

The price is the base fare adjusted by one multiplier per factor:

```
final_fare = base_fare × time × traffic × demand      (then rounded)
```

When riders outnumber free drivers the demand multiplier climbs and the quote
goes into **surge** (capped so a fare never more than doubles).

**Why it is written as plain rules, not a trained neural network.** This is a
deliberate teaching choice. The model is *transparent*: the Book-a-ride card
shows the price broken down line by line, and you can read exactly why a fare
moved. A rider deserves that, and so does a student. The file's header explains
the upgrade path: each hand-set weight here is what a real system would instead
**learn** by training a regression on historical trips (the features in, the
price riders accepted out). The shape — turn raw inputs into features, combine
them into one number — is identical; only the source of the weights changes.
That is the honest bridge from "if-statements" to "machine learning", and it is
worth discussing in class: when is a simple, explainable model the *better*
engineering choice than a black box?

Where to look:

- `backend/app/fare_model.py` — the model itself (distance, the three factors,
  the combination), heavily commented.
- `backend/app/routers/fares.py` — `GET /api/fare/estimate`, which quotes a
  live price; the passenger page calls it as you choose, and the booking is
  charged the model's price at the moment you book.
- The **UBA overview** dashboard — median fare, surge rate, and the
  "riders waiting vs drivers free" demand chart are all fed by the model.
- Try it: tour step 2 above walks you through making a fare surge.

## 7. Exercises

Roughly in order of difficulty.

1. Add a new destination through the admin page, then find it in PostgreSQL
   with `psql`.
2. Add a panel to the Grafana dashboard showing completed trips per driver.
   (You will need to add a `driver` label to a metric first.)
3. Add `DELETE /api/destinations/{id}` for admins, with a test, and a button
   on the admin page. What should happen if a booking uses that destination?
4. Let a logged-in user change their own password. It must ask for the
   current password.
5. Let a passenger cancel an *accepted* booking. What should the driver see?
6. Show the passenger's current booking on the map in "My bookings", the way
   the driver page shows the current job.
7. Draw the real road route between pickup and destination instead of a
   straight line. You will need a routing service such as OSRM.
8. Replace the five-second polling with live updates (Server-Sent Events or
   WebSockets).
9. Replace `Base.metadata.create_all` with Alembic migrations, then add a
   `notes` column to bookings without losing data.
10. Write a GitHub Actions workflow that runs the backend tests and builds both
   images on every push.
11. Add tracing with OpenTelemetry so one request can be followed from Traefik
   through the backend to the database.

## 8. What still separates this from real production

This is a teaching system. Before it could serve real customers it would need
at least the following. Each is a topic worth reading about.

- **HTTPS.** Everything here is plain HTTP. Traefik can fetch certificates
  from Let's Encrypt automatically, and the login cookie must then be marked
  `secure`.
- **Real secrets.** The defaults in `docker-compose.yml` (database password,
  token signing key, Grafana `admin`/`admin`) are public. Production uses a
  secret manager and never commits secrets.
- **Locked-down tools.** The Traefik, Prometheus, Grafana and Mailpit pages
  are open to anyone who can reach the server. They must sit behind a login
  or a private network.
- **Database migrations and backups.** Tables are created at start-up and
  nothing is backed up.
- **Real email.** Mailpit only pretends. A real system uses an email service,
  and should also verify a new user's email address.
- **Alerts.** The dashboards only help if someone is looking. Production
  systems page a person when error rates rise.
- **Traces, and production-grade logging.** Logs are now collected centrally
  (Alloy ships them to Loki, searchable in Grafana), but it is a single-node
  demo: no retention limits, no object storage, no auth on Loki. The third
  pillar, distributed **tracing** (e.g. Tempo + OpenTelemetry), is still
  missing - it would let you follow one request across services.
- **CI/CD.** Tests are run by hand. Nothing builds or deploys automatically.
- **More than one machine.** Docker Compose runs everything on one computer.
  If it dies, the app is down. Orchestrators such as Kubernetes handle many
  machines.
- **A map tile provider.** The map tiles come straight from OpenStreetMap's
  free public servers, which are for light use only. A real product pays a
  tile provider or hosts its own tiles. The "© OpenStreetMap contributors"
  credit on every page is required by the map data's licence.
- **Frontend tests and accessibility checks.** Only the backend is tested.

None of these is exotic. Each is a normal next step, and knowing that the
list exists is part of what separates a graduate from an engineer.

## 9. For the security-minded: the vulnerability lab

The `securitylab/` folder holds an extra service that is **broken on purpose**,
for students on a cybersecurity path. It is a safe practice target - like OWASP
Juice Shop or DVWA - for learning to audit a service (port scanning, recon),
spot classic web vulnerabilities (SQL injection, broken access control, XSS,
information disclosure, weak credentials), exploit them against fake data, and
then **fix** them. Each flaw is paired with how to detect it and how the real
`backend` already does it safely, so the lab is the cautionary contrast to the
rest of this project.

It is deliberately kept harmless: a separate image on its own isolated Docker
network with no path to the real database or any real data, published on
`127.0.0.1` only, seeded with invented records. Start it with
`docker compose up -d --build securitylab`, then follow `securitylab/README.md`.

**Only ever run the attacks and scans against this lab, on your own machine.**
Testing systems you do not own or have written permission to test is illegal.
