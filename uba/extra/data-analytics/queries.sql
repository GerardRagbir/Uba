-- ============================================================
-- UBA analytics — a library of questions, answered in SQL
-- ============================================================
-- Run the whole file:   psql "$UBA_DATABASE_URL" -f queries.sql
-- Or copy one query at a time into psql while you explore.
--
-- The only tables you need are:
--   bookings(id, pax_id, driver_id, pickup_id, destination_id,
--            fare, status, rating, created_at, updated_at)
--   destinations(id, name, fare, latitude, longitude)
--   users(id, username, name, role, created_at, phone, permit_no)
--   vehicles(id, plate, make, model, seats, driver_id)
--
-- NOTICE: revenue is only real when a trip COMPLETES, so every money question
-- filters on status = 'completed'. Getting that filter right is most of the job.


-- 1. Volume: bookings per day, split by status ---------------------------------
-- "Are we growing? Where do rides fall out of the funnel?"
SELECT date_trunc('day', created_at)::date AS day,
       status,
       count(*) AS bookings
FROM bookings
GROUP BY day, status
ORDER BY day, status;


-- 2. Conversion funnel: how many bookings actually complete? --------------------
-- A single headline row. completion_rate is the number a product owner watches.
SELECT count(*)                                                  AS total_bookings,
       count(*) FILTER (WHERE status = 'completed')              AS completed,
       count(*) FILTER (WHERE status = 'cancelled')              AS cancelled,
       round(100.0 * count(*) FILTER (WHERE status = 'completed')
             / nullif(count(*), 0), 1)                           AS completion_rate_pct,
       round(100.0 * count(*) FILTER (WHERE status = 'cancelled')
             / nullif(count(*), 0), 1)                           AS cancel_rate_pct
FROM bookings;


-- 3. Revenue by destination ----------------------------------------------------
-- "Which routes make us the most money?" Completed trips only.
SELECT d.name                       AS destination,
       count(*)                     AS completed_trips,
       sum(b.fare)                  AS revenue_ttd,
       round(avg(b.fare), 0)        AS avg_fare_ttd
FROM bookings b
JOIN destinations d ON d.id = b.destination_id
WHERE b.status = 'completed'
GROUP BY d.name
ORDER BY revenue_ttd DESC NULLS LAST;


-- 4. Daily revenue -------------------------------------------------------------
SELECT date_trunc('day', created_at)::date AS day,
       count(*)                            AS completed_trips,
       sum(fare)                           AS revenue_ttd
FROM bookings
WHERE status = 'completed'
GROUP BY day
ORDER BY day;


-- 5. Driver utilisation --------------------------------------------------------
-- "Who is pulling their weight?" Every driver, even those with zero trips
-- (LEFT JOIN), plus whether they even have a vehicle to work with.
SELECT u.username                                               AS driver,
       (v.plate IS NOT NULL)                                    AS has_vehicle,
       count(b.id) FILTER (WHERE b.status = 'completed')        AS completed_trips,
       coalesce(sum(b.fare) FILTER (WHERE b.status = 'completed'), 0) AS revenue_ttd
FROM users u
LEFT JOIN vehicles v ON v.driver_id = u.id
LEFT JOIN bookings b ON b.driver_id = u.id
WHERE u.role = 'driver'
GROUP BY u.username, has_vehicle
ORDER BY completed_trips DESC;


-- 6. Rating mix per driver -----------------------------------------------------
-- Experience quality. A driver with many 👎 is a retention risk for riders.
SELECT u.username                                     AS driver,
       count(*) FILTER (WHERE b.rating = 'up')        AS thumbs_up,
       count(*) FILTER (WHERE b.rating = 'down')      AS thumbs_down,
       count(*) FILTER (WHERE b.rating IS NULL)       AS unrated
FROM bookings b
JOIN users u ON u.id = b.driver_id
WHERE b.status = 'completed'
GROUP BY u.username
ORDER BY thumbs_down DESC, thumbs_up DESC;


-- 7. Busiest hours of the day --------------------------------------------------
-- Feeds the fare model's surge logic AND tells ops when to have drivers ready.
SELECT extract(hour FROM created_at)::int AS hour_of_day,
       count(*)                           AS bookings
FROM bookings
GROUP BY hour_of_day
ORDER BY hour_of_day;


-- 8. New passengers per day (growth) -------------------------------------------
SELECT date_trunc('day', created_at)::date AS day,
       count(*)                            AS new_passengers
FROM users
WHERE role = 'pax'
GROUP BY day
ORDER BY day;

-- TRY: add a query for "average time from booking to completion" using
--      updated_at - created_at on completed rows. What does a long time suggest?
