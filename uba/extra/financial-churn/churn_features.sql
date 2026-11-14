-- ============================================================
-- Churn features — one row per passenger (RFM + a churn label)
-- ============================================================
-- Run:  psql "$UBA_DATABASE_URL" -f churn_features.sql
-- This is the table churn_model.py learns from. The whole art of ML is here in
-- the SQL: good features beat a fancy model every time.
--
-- RFM is the classic customer-analytics trio:
--   Recency   — how long since their last completed trip?  (big = bad)
--   Frequency — how many completed trips in total?
--   Monetary  — how much have they spent?
-- CHURN LABEL — we call a passenger churned if their last completed trip was
--   more than 30 days ago (they *used* to ride, and have gone quiet).

WITH pax AS (
    SELECT id FROM users WHERE role = 'pax'
),
trips AS (
    SELECT pax_id,
           count(*)                         AS frequency,
           sum(fare)                         AS monetary,
           round(avg(fare), 1)              AS avg_fare,
           max(created_at)                   AS last_trip,
           min(created_at)                   AS first_trip,
           count(*) FILTER (WHERE rating = 'down') AS thumbs_down
    FROM bookings
    WHERE status = 'completed'
    GROUP BY pax_id
),
cancels AS (
    SELECT pax_id, count(*) AS cancellations
    FROM bookings WHERE status = 'cancelled'
    GROUP BY pax_id
)
SELECT p.id                                                   AS pax_id,
       coalesce(t.frequency, 0)                               AS frequency,
       coalesce(t.monetary, 0)                                AS monetary_ttd,
       coalesce(t.avg_fare, 0)                                AS avg_fare_ttd,
       coalesce(c.cancellations, 0)                           AS cancellations,
       coalesce(t.thumbs_down, 0)                             AS thumbs_down,
       -- days since last completed trip (NULL if they never completed one)
       CASE WHEN t.last_trip IS NOT NULL
            THEN extract(day FROM now() - t.last_trip)::int END AS recency_days,
       -- how long they have been a customer
       CASE WHEN t.first_trip IS NOT NULL
            THEN extract(day FROM now() - t.first_trip)::int END AS tenure_days,
       -- the label we want to predict: 1 = churned, 0 = still active
       CASE
         WHEN t.last_trip IS NULL THEN NULL           -- never rode: not scoreable
         WHEN now() - t.last_trip > interval '30 days' THEN 1
         ELSE 0
       END                                                   AS churned
FROM pax p
LEFT JOIN trips   t ON t.pax_id = p.id
LEFT JOIN cancels c ON c.pax_id = p.id
ORDER BY churned DESC NULLS LAST, recency_days DESC NULLS LAST;

-- NOTICE: passengers who never completed a trip get churned = NULL. You cannot
-- predict churn for someone who was never active; that is a different problem
-- (activation), and mixing the two is a common beginner mistake.
