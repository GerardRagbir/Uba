# Data analytics track

For the student heading toward **data / business intelligence analyst**.

An analyst does not build the app and does not run the servers. Their job is to
turn the data the app *already produces* into answers the business can act on:
How many rides are we completing? Which routes earn the most? Are drivers busy
enough? Is cancellation creeping up? You answer those with **SQL** to pull the
numbers and a little **Python (pandas)** to shape and chart them.

## What's here

| File | What it is |
|---|---|
| `queries.sql` | A library of analytical SQL questions, each commented with *why you'd ask it*. Run them straight in `psql`. |
| `analyze.py` | A small pandas report that runs the key queries and prints a KPI summary (and a chart if matplotlib is installed). |
| `requirements.txt` | The Python packages this track uses. |

## The questions an analyst asks of UBA

Think in terms of the booking lifecycle (`pending → accepted → completed`, or
`cancelled`) and money (`fare`, counted only when a trip **completes**):

- **Volume** — bookings per day, by status.
- **Conversion** — what share of bookings actually complete vs cancel?
- **Revenue** — TT$ earned, by day and by destination.
- **Supply** — how busy is each driver; who has no vehicle?
- **Experience** — rating mix (👍 / 👎) per driver.

## Run it

Numbers only, straight from the database:

```
psql "$UBA_DATABASE_URL" -f queries.sql
```

The pandas report (see the top-level `extra/README.md` for how to reach the DB):

```
pip install -r requirements.txt
UBA_DATABASE_URL=postgresql+psycopg://uba:uba-dev-password@localhost:5432/uba python analyze.py
```

If the demo database is nearly empty, click around the app first (book, accept,
complete, cancel, rate a few rides) so the numbers have something to show — or
pass `--demo` to `analyze.py` to add synthetic bookings for a fuller picture.

## Deliberately left out (good next steps)

- **A BI tool.** Real analysts publish these to Metabase, Power BI or Superset
  rather than a terminal. The SQL you write here drops straight into any of them.
- **Scheduled refresh.** These run on demand; see the `data-engineering` track
  for turning them into a nightly pipeline.
- **Statistical rigour.** "Cancellation went up" needs a significance test, not
  just a bigger number. That is a whole course on its own.

## What to learn beyond your degree

SQL to a professional level (joins, `GROUP BY`, window functions, CTEs),
pandas, one BI tool, and the habit of asking "compared to what?" of every
number. Everything here is written to push you toward those.
