# UBA — one taxi-booking app, built four times

A note to my students:

Most courses show you one finished program and ask you to admire it. This repo
does the opposite. It builds **the same taxi-booking application four times
over**, and each version adds one more layer of what real software engineering
actually looks like. The booking rules never really change — a passenger books
a ride, a driver accepts it, the trip is completed and rated — but everything
*around* those rules grows up, version by version, until the last one looks like
something a company would run in production.

My intention is that you **follow the folders in order** and feel each jump for
yourself:

1. **[`uba-basic/`](uba-basic/)** — a console program that stores data in text
   files. Pure Python: variables, `if`, loops, functions, classes, inheritance.
2. **[`uba-gui/`](uba-gui/)** — the same logic with a web interface on top
   (NiceGUI), still saving to text files. You see that a *UI is just a layer*.
3. **[`uba-advanced/`](uba-advanced/)** — a real database (SQLite), hashed
   passwords and a proper "forgot password" flow. You see *data and security*
   grow up.
4. **[`uba/`](uba/)** — the production-shaped system: a FastAPI backend, a
   Next.js + Tailwind frontend, PostgreSQL, Docker, a Traefik reverse proxy,
   full observability (Prometheus, Loki, Grafana), an **AI fare model**, and an
   intentionally vulnerable **security lab** for the cyber-security track.

Each folder has its **own detailed README** — that is where the real teaching
is. This root file is the **map**: it shows, with diagrams, how the versions
relate, what layers each one has, who uses it, and how much of the networking
stack (the OSI model) each one actually exercises.

> How to read this repo: skim this map, then open `uba-basic/README.md` and
> work upward. Don't skip ahead — each version only makes sense once you have
> felt the problem the previous one left unsolved.

---

## How the four versions evolve

```mermaid
flowchart LR
    A["uba-basic<br/>console UI<br/>text files"]
    B["uba-gui<br/>web UI (NiceGUI)<br/>text files"]
    C["uba-advanced<br/>web UI (NiceGUI)<br/>SQLite + hashed passwords"]
    D["uba<br/>Next.js + FastAPI + PostgreSQL<br/>Docker, Traefik, observability,<br/>AI fares, security lab"]

    A -- "add a UI layer<br/>(logic unchanged)" --> B
    B -- "swap files for a real DB<br/>hash passwords, add reset" --> C
    C -- "split into services,<br/>containerise, add the real world" --> D
```

| Folder | Interface | Storage | Runs as | The new idea it teaches |
|---|---|---|---|---|
| `uba-basic` | Console menus | `.txt` files | one Python script | Objects, inheritance, file I/O |
| `uba-gui` | Web pages (NiceGUI) | `.txt` files | one Python script | Separating UI from logic |
| `uba-advanced` | Web pages (NiceGUI) | SQLite database | one Python script | Databases, password hashing, account recovery |
| `uba` | Next.js website | PostgreSQL | 10 containers behind a proxy | Services, HTTP APIs, Docker, proxies, observability, AI, security |

**What stays the same the whole way:** the domain model. A base `User` with
`Pax`, `Driver` and `Admin` inheriting from it; `Vehicle`, `Destination`,
`Booking`. Open `models.py` in any of the first three, or
`uba/backend/app/models.py`, and you will recognise the same shapes.

### A note on the diagrams below

For **each** version you get three views:

- **Layers** — the boxes the program is built from, top (what the user touches)
  to bottom (where data rests).
- **Use cases** — who uses it and what they can do (a UML-style use-case view).
- **OSI footprint** — which of the seven networking layers the version actually
  uses. This is where the evolution is most striking: `uba-basic` touches almost
  none of the stack, while `uba` lights up all seven. (✅ = used in this
  version, ⬜ = not used.)

---

## 1. `uba-basic` — console + text files

A single Python program you run in a terminal. No network, no web, no database.
Everything that matters about objects and inheritance is already here.

**Layers**

```mermaid
flowchart TD
    U["Person at the terminal"] --> M["main.py — menus, input() / print()"]
    M --> F["functions — login, book_ride, accept, ..."]
    F --> O["models.py — User → Pax / Driver / Admin,<br/>Vehicle, Destination, Booking"]
    F --> S["storage.py — read/write text files"]
    S --> D[("data/*.txt")]
```

**Use cases**

```mermaid
flowchart LR
    pax(("Passenger"))
    drv(("Driver"))
    adm(("Admin"))

    pax --> u1(["Register / log in"])
    pax --> u2(["Book a ride"])
    pax --> u3(["View & cancel my bookings"])
    drv --> u4(["See pending bookings"])
    drv --> u5(["Accept / complete a trip"])
    adm --> u6(["Add drivers, vehicles, destinations"])
    adm --> u7(["View all bookings"])
```

**OSI footprint** — only the application and the local disk are involved; there
is no network at all.

```mermaid
flowchart TD
    L7["✅ L7 Application — the console app"]
    L6["✅ L6 Presentation — plain text, pipe-separated .txt"]
    L5["⬜ L5 Session — none (single process)"]
    L4["⬜ L4 Transport — none (no network)"]
    L3["⬜ L3 Network — none"]
    L2["⬜ L2 Data Link — none"]
    L1["✅ L1 Physical — the local disk"]
    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

---

## 2. `uba-gui` — a web UI over the same logic

The exact same `models.py` and `storage.py`, now with a browser interface
(NiceGUI). The lesson: a user interface is a **layer you add**, not a rewrite.
Because NiceGUI runs a small web server, the browser now talks to Python over
HTTP and a WebSocket — so the networking stack starts to wake up (on `localhost`).

**Layers**

```mermaid
flowchart TD
    B["Browser (NiceGUI renders the page)"] <--> SRV["NiceGUI server (localhost)"]
    SRV --> P["pages — login / pax / driver / admin,<br/>all inherit base_page"]
    P --> SE["session — who is logged in, loaded data"]
    P --> O["models.py — User → Pax / Driver / Admin, ..."]
    P --> S["storage.py — read/write text files"]
    S --> D[("data/*.txt")]
```

**Use cases** (same roles, now point-and-click; anyone can self-register)

```mermaid
flowchart LR
    pax(("Passenger"))
    drv(("Driver"))
    adm(("Admin"))

    pax --> u1(["Register (pax/driver/admin)"])
    pax --> u2(["Book a ride, rate a trip"])
    pax --> u3(["Cancel a pending booking"])
    drv --> u4(["Accept / complete / release a job"])
    drv --> u5(["Edit my vehicle"])
    adm --> u6(["Manage users, vehicles, destinations"])
    adm --> u7(["View all bookings"])
```

**OSI footprint** — a browser now talks to the server, so transport and network
layers come into play (over the loopback interface).

```mermaid
flowchart TD
    L7["✅ L7 Application — HTTP + NiceGUI"]
    L6["✅ L6 Presentation — HTML / JSON over the wire"]
    L5["✅ L5 Session — the browser↔server WebSocket"]
    L4["✅ L4 Transport — TCP"]
    L3["✅ L3 Network — IP (loopback 127.0.0.1)"]
    L2["⬜ L2 Data Link — loopback (no real link)"]
    L1["✅ L1 Physical — local disk for data"]
    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

---

## 3. `uba-advanced` — a real database and real security

The screens barely change; the **floor underneath them** is replaced. Text
files become a SQLite database, passwords are no longer stored (only salted
hashes), and there is a security-question "forgot password" flow. This is the
version where *data integrity* and *security* become first-class.

**Layers**

```mermaid
flowchart TD
    B["Browser (NiceGUI)"] <--> SRV["NiceGUI server (localhost)"]
    SRV --> P["pages — login / pax / driver / admin"]
    P --> SE["session — logged-in user, loaded data"]
    P --> SEC["security.py — salted password hashing,<br/>reset questions"]
    P --> DB["database.py — SQL (the only file with SQL)"]
    P --> O["models.py — objects, now with hashes"]
    DB --> SQ[("SQLite — data/uba.db")]
```

**Use cases** (adds account recovery)

```mermaid
flowchart LR
    pax(("Passenger"))
    drv(("Driver"))
    adm(("Admin"))

    pax --> u1(["Register with a security question"])
    pax --> u2(["Forgot password → reset"])
    pax --> u3(["Book, cancel, rate"])
    drv --> u4(["Accept / complete / release, edit vehicle"])
    adm --> u6(["Manage users, vehicles, destinations"])
    adm --> u7(["View all bookings"])
```

**OSI footprint** — same networking shape as `uba-gui` (browser ↔ local server);
the change is *below* the network, in how data is stored and secured.

```mermaid
flowchart TD
    L7["✅ L7 Application — HTTP + NiceGUI"]
    L6["✅ L6 Presentation — HTML / JSON; passwords hashed before storage"]
    L5["✅ L5 Session — browser↔server WebSocket"]
    L4["✅ L4 Transport — TCP"]
    L3["✅ L3 Network — IP (loopback)"]
    L2["⬜ L2 Data Link — loopback"]
    L1["✅ L1 Physical — local disk (SQLite file)"]
    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

---

## 4. `uba` — the production-shaped system

Now the single program is split into **services** that each do one job and talk
over HTTP, all packaged in Docker and fronted by one reverse proxy. This is the
shape of real systems, and the folder's own README is a full tour. See also its
sections on the **AI fare model** and the **security lab**.

**Layers / architecture**

```mermaid
flowchart TD
    BR["Browser — Next.js + Tailwind (React)"]
    BR -->|HTTP| TR["Traefik — reverse proxy, TLS point, rate limiting"]

    TR -->|"/ (pages)"| FE["frontend — Next.js server"]
    TR -->|"/api/*"| BE["backend — FastAPI"]

    subgraph BEI ["backend internals"]
        R["routers — auth, bookings, fares, vehicles, users"]
        R --> FM["fare_model.py — the AI pricing model"]
        R --> SEC["security.py — Argon2 hashes, JWT cookies, roles"]
        R --> SCH["schemas.py — request/response validation"]
        R --> MOD["models.py — ORM objects"]
    end
    BE --> BEI
    BE -->|SQL| PG[("PostgreSQL")]
    BE -->|email| MP["Mailpit (dev mail)"]

    subgraph OBS ["observability"]
        PR["Prometheus — metrics"]
        LK["Loki — logs"]
        AL["Alloy — ships container logs"]
        GR["Grafana — dashboards: overview + security"]
    end
    BE -. "/metrics" .-> PR
    AL -. "logs" .-> LK
    PR --> GR
    LK --> GR

    LAB["security lab — intentionally vulnerable,<br/>isolated network, localhost only"]
```

**Use cases** (passengers, drivers, admins — plus operators and security students)

```mermaid
flowchart LR
    pax(("Passenger"))
    drv(("Driver"))
    adm(("Admin"))
    ops(("Operator"))
    sec(("Security student"))

    pax --> u1(["Register / log in (JWT cookie)"])
    pax --> u2(["Get a live AI fare quote"])
    pax --> u3(["Book, cancel, rate; reset password by email"])
    drv --> u4(["Accept / complete / release jobs"])
    drv --> u5(["Edit vehicle"])
    adm --> u6(["Manage users, vehicles, destinations"])
    adm --> u7(["View all bookings & fares"])
    ops --> u8(["Watch Grafana dashboards & logs"])
    sec --> u9(["Audit & exploit the security lab, then fix it"])
```

**OSI footprint** — a real distributed system now exercises the whole stack.

```mermaid
flowchart TD
    L7["✅ L7 Application — HTTP APIs, Next.js, Traefik routing, FastAPI"]
    L6["✅ L6 Presentation — JSON, HTML; Argon2 hashing; (TLS-ready)"]
    L5["✅ L5 Session — JWT cookies, keep-alive connections"]
    L4["✅ L4 Transport — TCP between browser, proxy, services, DB"]
    L3["✅ L3 Network — IP routing across the Docker network"]
    L2["✅ L2 Data Link — the virtual Docker/bridge network"]
    L1["✅ L1 Physical — host NIC / loopback, disk volumes"]
    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

---

## Where to go next

- Start building your understanding at **[`uba-basic/`](uba-basic/)**.
- Each folder's `README.md` is the detailed guide for that version.
- The production app's guide, **[`uba/README.md`](uba/README.md)**, also lists
  *what to learn beyond your degree* to be able to build a system like it.
- Cyber-security track: **[`uba/securitylab/README.md`](uba/securitylab/README.md)**.

Build each version, break it, and read the next one's README only when you can
say exactly why the previous version needed to grow. That path — from a console
script to a containerised, observable, secured, intelligent system — is the real
subject of this course.
