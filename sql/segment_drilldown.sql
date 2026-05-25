WITH session_rollup AS (
    SELECT
        session_id,
        user_id,
        region,
        device,
        app_version,
        model_version,
        event_date,
        CASE WHEN event_date >= DATE '2025-11-17' THEN 'post' ELSE 'pre' END AS period,
        MAX(CASE WHEN event_type = 'app_open' THEN 1 ELSE 0 END) AS app_open,
        MAX(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END) AS video_play,
        MAX(CASE WHEN event_type = 'video_complete' THEN 1 ELSE 0 END) AS video_complete,
        MAX(CASE WHEN event_type = 'video_play' THEN watch_seconds ELSE 0 END) AS watch_seconds
    FROM events
    GROUP BY 1,2,3,4,5,6,7,8
)
SELECT
    period,
    region,
    model_version,
    device,
    COUNT(DISTINCT user_id) AS active_users,
    COUNT(*) AS sessions,
    SUM(video_play) AS video_plays,
    SUM(video_complete) AS video_completes,
    SUM(CASE WHEN app_open = 1 AND video_play = 0 THEN 1 ELSE 0 END) AS bounced_sessions,
    SUM(video_play)::DOUBLE / NULLIF(COUNT(DISTINCT user_id), 0) AS plays_per_active_user,
    SUM(CASE WHEN app_open = 1 AND video_play = 0 THEN 1 ELSE 0 END)::DOUBLE / NULLIF(SUM(app_open), 0) AS bounce_rate,
    SUM(video_complete)::DOUBLE / NULLIF(SUM(video_play), 0) AS completion_rate,
    SUM(watch_seconds)::DOUBLE / NULLIF(SUM(video_play), 0) AS avg_watch_seconds_per_play
FROM session_rollup
GROUP BY 1,2,3,4
ORDER BY region, period, device;
