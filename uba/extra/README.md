# UBA extra tracks — one project, many careers

The main `uba/` project is a production-shaped system, and the folders above it
(`uba-basic` → `uba-gui` → `uba-advanced` → `uba`) teach you to *build* it. But
a real system is not run by builders alone. Around it stands a whole team of
specialists, and most of you will become one of them rather than a
jack-of-all-trades.

So this `extra/` area gives **each kind of specialist their own track**. Every
track treats the running UBA system as its workplace and asks: *what does this
discipline actually contribute to a product like this, and how?* The language is
**Python and SQL wherever possible**, because those two will carry you across
almost all of these fields.

| Track | For the student heading toward… | What they add to UBA |
|---|---|---|
| [`data-analytics/`](data-analytics/) | Data / BI analyst | KPIs, dashboards, answering "how is the business doing?" with SQL + pandas |
| [`data-engineering/`](data-engineering/) | Data engineer | A reporting warehouse (star schema), ETL pipelines, data-quality checks |
| [`sysadmin-azure/`](sysadmin-azure/) | Systems administrator (cloud) | Running UBA on **Microsoft Azure**: provisioning, backups, operations |
| [`network-engineering/`](network-engineering/) | Network / comms engineer | The request path, latency/throughput analysis, log and traffic inspection |
| [`devops/`](devops/) | DevOps / SRE | CI/CD, automated tests, alerting rules, release safety |
| [`financial-churn/`](financial-churn/) | Data scientist / FinTech | Revenue & ARPU reporting, cohort retention, and a churn-prediction model |

## How these fit together

```mermaid
flowchart TD
    subgraph APP ["The running UBA system (docker compose up)"]
        PG[("PostgreSQL<br/>the source of truth")]
        PROM["Prometheus<br/>metrics"]
        LOKI["Loki<br/>logs"]
        TRAEFIK["Traefik<br/>the network edge"]
    end

    PG --> DA["data-analytics<br/>(SQL + pandas)"]
    PG --> DE["data-engineering<br/>(ETL → warehouse)"]
    DE --> DA
    PG --> FC["financial-churn<br/>(reporting + ML)"]
    PROM --> NET["network-engineering"]
    LOKI --> NET
    TRAEFIK --> NET
    PROM --> OPS["devops (alerts, SLOs)"]
    APP --> SYS["sysadmin-azure<br/>(provision & operate)"]
```

## Before you start

Every track assumes the main system is running:

```
cd uba
docker compose up -d
```

Tracks that read the database (analytics, data-engineering, financial-churn)
need to reach PostgreSQL. In the demo, Postgres is only on the private Docker
network, so pick **one** of these:

- **Easiest — run inside the stack's network:**
  ```
  docker compose run --rm --build -v "$PWD/extra:/extra" backend python /extra/<track>/<script>.py
  ```
  (the `backend` image already has Python, psycopg and SQLAlchemy installed)
- **Or expose Postgres to your laptop** by adding a port to the `postgres`
  service in `docker-compose.yml` (`ports: ["5432:5432"]`), then run the
  scripts directly with your own Python.

Each script reads its connection string from the `UBA_DATABASE_URL` environment
variable and falls back to the demo default
(`postgresql+psycopg://uba:uba-dev-password@postgres:5432/uba`). The tracks that
read metrics or logs (network, devops) talk to Prometheus/Loki through Traefik
and need no database.

> These are **starting points**, not finished products — one honest slice of
> each discipline, sized so you can read it in an afternoon and extend it for an
> assignment. Each folder's README says what is here, what is deliberately left
> out, and what to learn next.

## A word on safety and realism

- The demo passwords and connection strings here are the throwaway ones from
  `docker-compose.yml`. Real credentials never live in code — see the
  `sysadmin-azure` and `devops` tracks for how secrets are actually handled.
- The demo database is small, so several scripts can **generate synthetic data**
  so your charts and models have something to chew on. Each one says clearly
  when it is using real data and when it is using made-up data.
