-- ========================================================
-- SESSIONIZATION USING 30-MINUTE INACTIVITY BREAK
-- ========================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS events_marked_sessions AS
SELECT
    *,
    CASE 
        WHEN LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) IS NULL THEN 1
        WHEN EXTRACT(EPOCH FROM (ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts))) > 1800 THEN 1
        ELSE 0
    END AS is_new_session
FROM events_with_ts;


-- 2. table with computed session_id per user
CREATE MATERIALIZED VIEW IF NOT EXISTS events_with_session AS
SELECT
    *,
    SUM(is_new_session) OVER (
        PARTITION BY user_id 
        ORDER BY ts 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS session_id
FROM events_marked_sessions;


-- ========================================================
-- fact_watch_sessions
-- ========================================================

CREATE TABLE IF NOT EXISTS fact_watch_sessions AS
SELECT
    user_id,
    session_id,
    MIN(ts) AS session_start,
    MAX(ts) AS session_end,
    EXTRACT(EPOCH FROM (MAX(ts) - MIN(ts)))::INT AS session_seconds,

    -- Engagement features
    SUM(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END) AS video_plays,
    SUM(CASE WHEN event_type = 'video_complete' THEN 1 ELSE 0 END) AS video_completes,
    SUM(CASE WHEN event_type LIKE 'buffer_%' THEN 1 ELSE 0 END) AS buffer_events,
    SUM(CASE WHEN event_type = 'video_seek' THEN 1 ELSE 0 END) AS seek_events,

    -- Session-level date
    (MIN(ts))::DATE AS session_date,
    MIN(region) AS region
FROM events_with_session
GROUP BY user_id, session_id;
