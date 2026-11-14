"""A small analyst's report over the UBA database.

Run:  python analyze.py            (real data)
      python analyze.py --demo     (add synthetic bookings first, so there is
                                     something to look at on a fresh database)

It reads with SQL, shapes with pandas, and prints a KPI summary. If matplotlib
is installed it also saves a revenue chart to revenue_by_day.png.

Connection string comes from UBA_DATABASE_URL, defaulting to the demo stack.
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = os.environ.get(
    "UBA_DATABASE_URL",
    "postgresql+psycopg://uba:uba-dev-password@postgres:5432/uba",
)
engine = create_engine(DB_URL)


def read(sql: str) -> pd.DataFrame:
    """Run a query and hand back a DataFrame — the analyst's basic move."""
    return pd.read_sql(text(sql), engine)


def maybe_seed_demo() -> None:
    """Add synthetic completed/cancelled bookings so the report is not empty.

    NOTICE: this writes made-up data. Only runs with --demo, and only uses
    passengers, drivers and destinations that already exist.
    """
    with engine.begin() as cx:
        pax = [r[0] for r in cx.execute(text("SELECT id FROM users WHERE role='pax'"))]
        drivers = [r[0] for r in cx.execute(text("SELECT id FROM users WHERE role='driver'"))]
        dests = [r[0] for r in cx.execute(text("SELECT id, fare FROM destinations"))]
        if not (pax and drivers and dests):
            print("Cannot seed demo data: need at least one pax, driver and destination.")
            return
        rows = []
        for _ in range(300):
            when = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 29), hours=random.randint(0, 23)
            )
            pickup, dest = random.sample(dests, 2)
            status = random.choices(["completed", "cancelled"], weights=[0.8, 0.2])[0]
            rating = random.choices(["up", "down", None], weights=[0.6, 0.15, 0.25])[0]
            rows.append({
                "pax": random.choice(pax), "drv": random.choice(drivers),
                "pu": pickup[0], "de": dest[0], "fare": dest[1],
                "st": status, "rt": rating if status == "completed" else None, "ts": when,
            })
        cx.execute(text(
            "INSERT INTO bookings (pax_id, driver_id, pickup_id, destination_id, fare, "
            "status, rating, created_at, updated_at) VALUES "
            "(:pax, :drv, :pu, :de, :fare, :st, :rt, :ts, :ts)"
        ), rows)
    print("Seeded 300 synthetic bookings (demo mode).\n")


def main() -> None:
    if "--demo" in sys.argv:
        maybe_seed_demo()

    print("=" * 56)
    print("UBA — analyst report  (", DB_URL.split("@")[-1], ")")
    print("=" * 56)

    funnel = read("""
        SELECT count(*) AS total,
               count(*) FILTER (WHERE status='completed') AS completed,
               count(*) FILTER (WHERE status='cancelled') AS cancelled,
               coalesce(sum(fare) FILTER (WHERE status='completed'),0) AS revenue
        FROM bookings
    """).iloc[0]

    total = int(funnel["total"])
    if total == 0:
        print("\nNo bookings yet. Use the app, or re-run with --demo.")
        return

    completion = 100 * funnel["completed"] / total
    print(f"\nBookings: {total}   Completed: {funnel.completed}   "
          f"Cancelled: {funnel.cancelled}   Completion: {completion:.1f}%")
    print(f"Revenue (completed only): TT${int(funnel.revenue):,}")

    print("\nRevenue by destination")
    by_dest = read("""
        SELECT d.name AS destination, count(*) AS trips, sum(b.fare) AS revenue
        FROM bookings b JOIN destinations d ON d.id = b.destination_id
        WHERE b.status='completed'
        GROUP BY d.name ORDER BY revenue DESC
    """)
    print(by_dest.to_string(index=False) if not by_dest.empty else "  (none yet)")

    print("\nDriver utilisation")
    drivers = read("""
        SELECT u.username AS driver,
               count(b.id) FILTER (WHERE b.status='completed') AS trips,
               coalesce(sum(b.fare) FILTER (WHERE b.status='completed'),0) AS revenue
        FROM users u LEFT JOIN bookings b ON b.driver_id = u.id
        WHERE u.role='driver' GROUP BY u.username ORDER BY trips DESC
    """)
    print(drivers.to_string(index=False) if not drivers.empty else "  (none yet)")

    # A chart, only if matplotlib is available.
    daily = read("""
        SELECT date_trunc('day', created_at)::date AS day, sum(fare) AS revenue
        FROM bookings WHERE status='completed' GROUP BY day ORDER BY day
    """)
    if not daily.empty:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            ax = daily.plot(x="day", y="revenue", kind="bar", legend=False, color="#fbbf24")
            ax.set_title("UBA daily revenue (TT$)")
            ax.set_xlabel("")
            plt.tight_layout()
            plt.savefig("revenue_by_day.png", dpi=120)
            print("\nSaved chart: revenue_by_day.png")
        except ImportError:
            print("\n(install matplotlib to also get a revenue chart)")


if __name__ == "__main__":
    main()
