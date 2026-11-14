-- ============================================================
-- Managed PostgreSQL — a DBA's routine checks
-- ============================================================
-- Works against ANY of the UBA Postgres databases (laptop or Azure Flexible
-- Server). Connect, then run these to answer "is the database healthy?".
--
--   psql "host=<your-pg-host> dbname=uba user=ubaadmin sslmode=require"
--
-- On Azure you rarely VACUUM by hand (autovacuum + managed maintenance handle
-- it), but you absolutely still READ these to spot trouble.

-- 1. Who is connected, and what are they doing right now? -----------------------
SELECT pid, usename, state, wait_event_type,
       now() - query_start AS running_for,
       left(query, 80) AS query
FROM pg_stat_activity
WHERE datname = current_database() AND state <> 'idle'
ORDER BY running_for DESC NULLS LAST;

-- 2. Database size, and the biggest tables ------------------------------------
SELECT pg_size_pretty(pg_database_size(current_database())) AS total_size;

SELECT relname AS table,
       pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
       n_live_tup AS live_rows,
       n_dead_tup AS dead_rows            -- high dead rows => needs vacuum
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- 3. Are the indexes being used? ----------------------------------------------
-- idx_scan = 0 on a big table means a wasted index (costs writes, helps nobody).
SELECT relname AS table, indexrelname AS index,
       idx_scan AS times_used,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC;

-- 4. Cache hit ratio (should be > ~0.99 on a warm database) -------------------
SELECT round(sum(blks_hit) * 100.0 / nullif(sum(blks_hit + blks_read), 0), 2)
       AS cache_hit_pct
FROM pg_stat_database
WHERE datname = current_database();

-- 5. Long-running / idle-in-transaction sessions (a classic outage cause) ------
SELECT pid, usename, state, now() - state_change AS in_state_for, left(query,60) AS query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '5 minutes';

-- 6. Manual maintenance (laptop / on demand) ----------------------------------
-- Reclaims space and refreshes planner statistics. Safe to run; it is online.
-- VACUUM (ANALYZE, VERBOSE) bookings;
-- ANALYZE;

-- TRY: enable the pg_stat_statements extension and query it for the slowest and
--      most frequent statements — the real starting point for tuning.
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- SELECT left(query,70), calls, round(mean_exec_time,1) AS avg_ms, round(total_exec_time,0) AS total_ms
-- FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
