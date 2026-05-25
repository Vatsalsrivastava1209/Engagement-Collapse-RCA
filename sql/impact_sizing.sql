WITH daily AS (
    SELECT
        event_date,
        CASE WHEN region IN ('IN-North', 'IN-South') THEN 'affected' ELSE 'unaffected' END AS cohort,
        COUNT(DISTINCT user_id) AS active_users,
        SUM(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END) AS video_plays,
        SUM(CASE WHEN event_type = 'video_play' THEN watch_seconds ELSE 0 END) AS watch_seconds
    FROM events
    GROUP BY 1,2
),
baseline AS (
    SELECT
        cohort,
        AVG(video_plays::DOUBLE / NULLIF(active_users, 0)) AS baseline_plays_per_user,
        AVG(watch_seconds::DOUBLE / NULLIF(active_users, 0)) AS baseline_watch_seconds_per_user
    FROM daily
    WHERE event_date < DATE '2025-11-17'
    GROUP BY 1
),
post AS (
    SELECT
        daily.*,
        baseline.baseline_plays_per_user,
        baseline.baseline_watch_seconds_per_user,
        baseline.baseline_plays_per_user * daily.active_users AS expected_video_plays,
        baseline.baseline_watch_seconds_per_user * daily.active_users AS expected_watch_seconds
    FROM daily
    JOIN baseline USING (cohort)
    WHERE daily.event_date >= DATE '2025-11-17'
)
SELECT
    cohort,
    SUM(active_users) AS active_user_days,
    SUM(video_plays) AS actual_video_plays,
    SUM(expected_video_plays) AS expected_video_plays,
    SUM(expected_video_plays - video_plays) AS lost_video_plays,
    SUM(watch_seconds) AS actual_watch_seconds,
    SUM(expected_watch_seconds) AS expected_watch_seconds,
    SUM(expected_watch_seconds - watch_seconds) AS lost_watch_seconds
FROM post
GROUP BY 1
ORDER BY cohort;
