-- ============================================================
-- UBA financial reporting
-- ============================================================
-- Run:  psql "$UBA_DATABASE_URL" -f revenue_reporting.sql
-- Revenue counts a trip only when it COMPLETES. Everything flows from that.

-- 1. Monthly revenue & volume --------------------------------------------------
SELECT date_trunc('month', created_at)::date AS month,
       count(*)                              AS completed_trips,
       sum(fare)                             AS revenue_ttd,
       round(avg(fare), 0)                   AS avg_fare_ttd
FROM bookings
WHERE status = 'completed'
GROUP BY month
ORDER BY month;

-- 2. ARPU — average revenue per active passenger, by month ---------------------
-- "active" = booked at least one completed trip that month. ARPU is the number
-- investors ask for: how much is each paying customer worth to us?
SELECT month,
       revenue_ttd,
       active_passengers,
       round(revenue_ttd::numeric / nullif(active_passengers, 0), 0) AS arpu_ttd
FROM (
    SELECT date_trunc('month', created_at)::date AS month,
           sum(fare)                             AS revenue_ttd,
           count(DISTINCT pax_id)                AS active_passengers
    FROM bookings
    WHERE status = 'completed'
    GROUP BY month
) m
ORDER BY month;

-- 3. Repeat-purchase rate ------------------------------------------------------
-- What share of paying passengers came back for 2+ completed trips? A core
-- health signal: one-and-done customers are expensive to acquire and don't pay off.
SELECT count(*)                                                   AS paying_passengers,
       count(*) FILTER (WHERE trips >= 2)                         AS repeat_passengers,
       round(100.0 * count(*) FILTER (WHERE trips >= 2)
             / nullif(count(*), 0), 1)                            AS repeat_rate_pct
FROM (
    SELECT pax_id, count(*) AS trips
    FROM bookings WHERE status = 'completed'
    GROUP BY pax_id
) per_pax;

-- 4. Revenue concentration — do a few passengers drive most of it? -------------
-- The 80/20 question. If the top 20% of riders are most of the revenue, losing
-- one of them hurts far more than losing an average rider.
WITH per_pax AS (
    SELECT pax_id, sum(fare) AS spend
    FROM bookings WHERE status = 'completed'
    GROUP BY pax_id
), ranked AS (
    SELECT spend, ntile(5) OVER (ORDER BY spend DESC) AS quintile
    FROM per_pax
)
SELECT quintile,                                 -- 1 = top 20% of spenders
       count(*)                 AS passengers,
       sum(spend)               AS revenue_ttd,
       round(100.0 * sum(spend) / sum(sum(spend)) OVER (), 1) AS pct_of_revenue
FROM ranked
GROUP BY quintile
ORDER BY quintile;

-- 5. Retention cohort grid -----------------------------------------------------
-- Group passengers by the month they first completed a trip (their cohort), then
-- see how many were still active in each later month. The diagonal fading out is
-- churn made visible. (Reads best in a BI tool as a heat-map.)
WITH first_trip AS (
    SELECT pax_id,
           date_trunc('month', min(created_at))::date AS cohort_month
    FROM bookings WHERE status = 'completed'
    GROUP BY pax_id
), activity AS (
    SELECT DISTINCT pax_id,
           date_trunc('month', created_at)::date AS active_month
    FROM bookings WHERE status = 'completed'
)
SELECT f.cohort_month,
       a.active_month,
       -- whole months between joining and being active
       (extract(year  FROM age(a.active_month, f.cohort_month)) * 12
        + extract(month FROM age(a.active_month, f.cohort_month)))::int AS months_since_join,
       count(DISTINCT a.pax_id) AS active_passengers
FROM first_trip f
JOIN activity a ON a.pax_id = f.pax_id
GROUP BY f.cohort_month, a.active_month
ORDER BY f.cohort_month, a.active_month;

-- TRY: turn query 1 into month-over-month GROWTH using the lag() window function:
--      (revenue - lag(revenue) over (order by month)) / lag(revenue) ...
