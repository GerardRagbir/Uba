-- ============================================================
-- Data-quality checks for the UBA warehouse
-- ============================================================
-- Run AFTER etl.py:   psql "$UBA_DATABASE_URL" -f data_quality.sql
--
-- A pipeline you do not test is a pipeline you do not trust. Each query below
-- is an ASSERTION: it should return ZERO rows (or a PASS). If any returns rows,
-- the load is wrong and you do not ship the numbers. This is the SQL version of
-- the tests you already write in Python.

\echo '--- Check 1: every fact points at a real passenger (no orphans) ---'
SELECT f.booking_id
FROM analytics.fact_booking f
LEFT JOIN analytics.dim_passenger p ON p.passenger_id = f.passenger_id
WHERE p.passenger_id IS NULL;

\echo '--- Check 2: every fact points at a real destination ---'
SELECT f.booking_id
FROM analytics.fact_booking f
LEFT JOIN analytics.dim_destination d ON d.destination_id = f.destination_id
WHERE d.destination_id IS NULL;

\echo '--- Check 3: status is one of the four allowed values ---'
SELECT DISTINCT status
FROM analytics.fact_booking
WHERE status NOT IN ('pending', 'accepted', 'completed', 'cancelled');

\echo '--- Check 4: revenue_ttd is consistent (= fare when completed, else 0) ---'
SELECT booking_id, fare, status, revenue_ttd
FROM analytics.fact_booking
WHERE revenue_ttd <> CASE WHEN status = 'completed' THEN fare ELSE 0 END;

\echo '--- Check 5: no negative fares ---'
SELECT booking_id, fare FROM analytics.fact_booking WHERE fare < 0;

\echo '--- Reconciliation: warehouse revenue must equal operational revenue ---'
-- The single most important test: does the warehouse agree with the source?
SELECT
    (SELECT coalesce(sum(revenue_ttd), 0) FROM analytics.fact_booking)        AS warehouse_revenue,
    (SELECT coalesce(sum(fare), 0) FROM bookings WHERE status = 'completed')  AS source_revenue,
    CASE WHEN (SELECT coalesce(sum(revenue_ttd),0) FROM analytics.fact_booking)
            = (SELECT coalesce(sum(fare),0) FROM bookings WHERE status='completed')
         THEN 'PASS ✅' ELSE 'FAIL ❌ — investigate before trusting reports' END AS result;

-- TRY: deliberately break the ETL (e.g. remove the status filter on revenue_ttd),
--      re-run it, and watch the reconciliation check turn to FAIL. That is the
--      check earning its keep.
