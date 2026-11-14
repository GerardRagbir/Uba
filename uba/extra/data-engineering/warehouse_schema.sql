-- ============================================================
-- UBA reporting warehouse — a star schema
-- ============================================================
-- Lives in its own `analytics` schema so it never collides with the app's
-- operational tables. etl.py creates this automatically; it is here to read.
--
-- Star schema = one FACT (bookings) + DIMENSIONS (passenger, driver,
-- destination, date). Keys are the app's own ids, which keeps the demo simple
-- (a real warehouse would mint its own surrogate keys).

CREATE SCHEMA IF NOT EXISTS analytics;

-- Rebuild cleanly every run (full refresh). Drop facts before dimensions.
DROP TABLE IF EXISTS analytics.fact_booking;
DROP TABLE IF EXISTS analytics.dim_passenger;
DROP TABLE IF EXISTS analytics.dim_driver;
DROP TABLE IF EXISTS analytics.dim_destination;
DROP TABLE IF EXISTS analytics.dim_date;

-- ---------- dimensions ----------

CREATE TABLE analytics.dim_passenger (
    passenger_id   INTEGER PRIMARY KEY,
    username       TEXT,
    name           TEXT,
    signed_up_on   DATE
);

CREATE TABLE analytics.dim_driver (
    driver_id      INTEGER PRIMARY KEY,
    username       TEXT,
    name           TEXT,
    has_vehicle    BOOLEAN,
    vehicle_plate  TEXT
);

CREATE TABLE analytics.dim_destination (
    destination_id INTEGER PRIMARY KEY,
    name           TEXT,
    base_fare      INTEGER
);

CREATE TABLE analytics.dim_date (
    date_key       DATE PRIMARY KEY,
    year           INTEGER,
    month          INTEGER,
    day            INTEGER,
    weekday        INTEGER,   -- 0 = Monday
    is_weekend     BOOLEAN
);

-- ---------- fact ----------
-- One row per booking. Foreign keys point at the dimensions above. The measures
-- (what you SUM and AVG) are fare and the boolean flags.

CREATE TABLE analytics.fact_booking (
    booking_id        INTEGER PRIMARY KEY,
    booking_date      DATE REFERENCES analytics.dim_date(date_key),
    passenger_id      INTEGER REFERENCES analytics.dim_passenger(passenger_id),
    driver_id         INTEGER REFERENCES analytics.dim_driver(driver_id),
    pickup_id         INTEGER REFERENCES analytics.dim_destination(destination_id),
    destination_id    INTEGER REFERENCES analytics.dim_destination(destination_id),
    fare              INTEGER,
    status            TEXT,
    is_completed      BOOLEAN,
    is_cancelled      BOOLEAN,
    rating            TEXT,
    revenue_ttd       INTEGER   -- fare when completed, else 0 (pre-computed for easy SUM)
);

CREATE INDEX ix_fact_booking_date   ON analytics.fact_booking(booking_date);
CREATE INDEX ix_fact_booking_status ON analytics.fact_booking(status);

-- With this in place, a monthly-revenue report is just:
--   SELECT date_trunc('month', booking_date) AS month, sum(revenue_ttd)
--   FROM analytics.fact_booking GROUP BY month ORDER BY month;
