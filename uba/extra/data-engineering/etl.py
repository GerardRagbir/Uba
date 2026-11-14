"""UBA ETL — build the reporting warehouse from the operational database.

Extract  : read the app's tables (users, drivers, destinations, bookings).
Transform: shape them into star-schema rows (e.g. pre-compute revenue_ttd,
           derive date attributes).
Load     : (re)create the analytics.* tables and insert.

It is a FULL REFRESH and it is IDEMPOTENT: run it as often as you like, the
result is the same. Connection string from UBA_DATABASE_URL.

Run:  python etl.py
"""

from __future__ import annotations

import os
import pathlib

from sqlalchemy import create_engine, text

DB_URL = os.environ.get(
    "UBA_DATABASE_URL",
    "postgresql+psycopg://uba:uba-dev-password@postgres:5432/uba",
)
engine = create_engine(DB_URL)
HERE = pathlib.Path(__file__).parent


def create_schema() -> None:
    """Run warehouse_schema.sql — creates analytics.* and clears old rows."""
    sql = (HERE / "warehouse_schema.sql").read_text()
    with engine.begin() as cx:
        # SQLAlchemy sends one statement at a time; exec_driver_sql runs the
        # whole script (multiple statements) through the raw driver.
        cx.exec_driver_sql(sql)
    print("schema ready (analytics.*)")


# Each load step is: read from the operational side, write to the warehouse.
# INSERT ... SELECT keeps the transform in SQL, which is where it belongs.

LOADS = {
    "dim_passenger": """
        INSERT INTO analytics.dim_passenger (passenger_id, username, name, signed_up_on)
        SELECT id, username, name, created_at::date FROM users WHERE role = 'pax'
    """,
    "dim_driver": """
        INSERT INTO analytics.dim_driver (driver_id, username, name, has_vehicle, vehicle_plate)
        SELECT u.id, u.username, u.name, (v.plate IS NOT NULL), v.plate
        FROM users u LEFT JOIN vehicles v ON v.driver_id = u.id
        WHERE u.role = 'driver'
    """,
    "dim_destination": """
        INSERT INTO analytics.dim_destination (destination_id, name, base_fare)
        SELECT id, name, fare FROM destinations
    """,
    "dim_date": """
        -- one row per day that actually has a booking
        INSERT INTO analytics.dim_date (date_key, year, month, day, weekday, is_weekend)
        SELECT d::date,
               extract(year  FROM d)::int,
               extract(month FROM d)::int,
               extract(day   FROM d)::int,
               extract(isodow FROM d)::int - 1,          -- 0 = Monday
               extract(isodow FROM d)::int >= 6          -- Sat/Sun
        FROM (SELECT DISTINCT date_trunc('day', created_at) AS d FROM bookings) days
    """,
    "fact_booking": """
        INSERT INTO analytics.fact_booking (
            booking_id, booking_date, passenger_id, driver_id, pickup_id,
            destination_id, fare, status, is_completed, is_cancelled, rating, revenue_ttd)
        SELECT b.id,
               b.created_at::date,
               b.pax_id,
               b.driver_id,
               b.pickup_id,
               b.destination_id,
               b.fare,
               b.status,
               b.status = 'completed',
               b.status = 'cancelled',
               b.rating,
               CASE WHEN b.status = 'completed' THEN b.fare ELSE 0 END
        FROM bookings b
    """,
}


def load() -> None:
    with engine.begin() as cx:
        for table, sql in LOADS.items():
            cx.execute(text(sql))
            count = cx.execute(text(f"SELECT count(*) FROM analytics.{table}")).scalar()
            print(f"  loaded analytics.{table:<16} {count} rows")


def main() -> None:
    print(f"ETL → {DB_URL.split('@')[-1]}")
    create_schema()
    load()
    print("done. Try: SELECT sum(revenue_ttd) FROM analytics.fact_booking;")


if __name__ == "__main__":
    main()

# TRY: make this an INCREMENTAL load. Keep the dimensions as full refresh, but
#      only insert fact rows whose updated_at is newer than the last run. What
#      new problem does that create for rows that CHANGE status after loading?
