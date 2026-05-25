WITH session_rollup AS (
    SELECT
        session_id,
        region,
        CASE WHEN region IN ('IN-North', 'IN-South') THEN 'affected' ELSE 'unaffected' END AS cohort,
        CASE WHEN event_date >= DATE '2025-11-17' THEN 'post' ELSE 'pre' END AS period,
        MAX(CASE WHEN event_type = 'app_open' THEN 1 ELSE 0 END) AS app_open,
        MAX(CASE WHEN event_type = 'home_impression' THEN 1 ELSE 0 END) AS impression,
        MAX(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END) AS video_play,
        MAX(CASE WHEN event_type = 'video_complete' THEN 1 ELSE 0 END) AS video_complete
    FROM events
    GROUP BY 1,2,3,4
)
SELECT
    cohort,
    period,
    COUNT(*) AS sessions,
    SUM(app_open) AS app_opens,
    SUM(impression) AS impressions,
    SUM(video_play) AS video_plays,
    SUM(video_complete) AS completions,
    SUM(impression)::DOUBLE / NULLIF(SUM(app_open), 0) AS impression_rate,
    SUM(video_play)::DOUBLE / NULLIF(SUM(impression), 0) AS play_through_rate,
    SUM(video_complete)::DOUBLE / NULLIF(SUM(video_play), 0) AS completion_rate,
    1.0 - (SUM(video_play)::DOUBLE / NULLIF(SUM(app_open), 0)) AS bounce_rate
FROM session_rollup
GROUP BY 1,2
ORDER BY cohort, period;
