WITH session_rollup AS (
    SELECT
        session_id,
        user_id,
        region,
        device,
        app_version,
        model_version,
        event_date,
        CASE WHEN region IN ('IN-North', 'IN-South') THEN 'affected' ELSE 'unaffected' END AS cohort,
        CASE WHEN event_date >= DATE '2025-11-17' THEN 'post' ELSE 'pre' END AS period,
        MAX(CASE WHEN event_type = 'app_open' THEN 1 ELSE 0 END) AS app_opens,
        MAX(CASE WHEN event_type = 'home_impression' THEN 1 ELSE 0 END) AS impressions,
        MAX(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END) AS video_plays,
        MAX(CASE WHEN event_type = 'video_complete' THEN 1 ELSE 0 END) AS video_completes,
        MAX(CASE WHEN event_type = 'video_play' THEN watch_seconds ELSE 0 END) AS watch_seconds
    FROM events
    GROUP BY 1,2,3,4,5,6,7,8,9
)
SELECT
    cohort,
    period,
    COUNT(DISTINCT user_id) AS active_users,
    COUNT(*) AS sessions,
    SUM(app_opens) AS app_opens,
    SUM(impressions) AS impressions,
    SUM(video_plays) AS video_plays,
    SUM(video_completes) AS video_completes,
    SUM(CASE WHEN app_opens = 1 AND video_plays = 0 THEN 1 ELSE 0 END) AS bounced_sessions,
    SUM(watch_seconds) AS total_watch_seconds,
    SUM(video_plays)::DOUBLE / NULLIF(COUNT(DISTINCT user_id), 0) AS plays_per_active_user,
    SUM(video_plays)::DOUBLE / NULLIF(COUNT(*), 0) AS plays_per_session,
    SUM(video_completes)::DOUBLE / NULLIF(SUM(video_plays), 0) AS completion_rate,
    SUM(CASE WHEN app_opens = 1 AND video_plays = 0 THEN 1 ELSE 0 END)::DOUBLE / NULLIF(SUM(app_opens), 0) AS bounce_rate,
    SUM(watch_seconds)::DOUBLE / NULLIF(SUM(video_plays), 0) AS avg_watch_seconds_per_play
FROM session_rollup
GROUP BY 1,2
ORDER BY cohort, period;
