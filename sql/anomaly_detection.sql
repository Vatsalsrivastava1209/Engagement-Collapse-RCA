WITH daily AS (
    SELECT
        event_date,
        region,
        CASE WHEN region IN ('IN-North', 'IN-South') THEN 'affected' ELSE 'unaffected' END AS cohort,
        COUNT(DISTINCT user_id) AS active_users,
        SUM(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END) AS video_plays,
        SUM(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END)::DOUBLE / NULLIF(COUNT(DISTINCT user_id), 0) AS plays_per_active_user
    FROM events
    GROUP BY 1,2,3
),
baseline AS (
    SELECT
        region,
        AVG(plays_per_active_user) AS baseline_mean,
        STDDEV_SAMP(plays_per_active_user) AS baseline_sd
    FROM daily
    WHERE event_date < DATE '2025-11-17'
    GROUP BY 1
)
SELECT
    daily.event_date,
    daily.region,
    daily.cohort,
    daily.active_users,
    daily.video_plays,
    daily.plays_per_active_user,
    baseline.baseline_mean,
    baseline.baseline_sd,
    (daily.plays_per_active_user - baseline.baseline_mean) / NULLIF(baseline.baseline_sd, 0) AS z_score,
    CASE
        WHEN daily.event_date >= DATE '2025-11-17'
         AND (daily.plays_per_active_user - baseline.baseline_mean) / NULLIF(baseline.baseline_sd, 0) <= -3
        THEN TRUE ELSE FALSE
    END AS anomaly_flag
FROM daily
JOIN baseline USING (region)
ORDER BY daily.event_date, daily.region;
