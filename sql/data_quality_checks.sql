SELECT 'row_count_positive' AS check_name, COUNT(*) > 0 AS passed, COUNT(*)::VARCHAR AS detail
FROM events
UNION ALL
SELECT 'event_id_unique', COUNT(*) = COUNT(DISTINCT event_id), COUNT(DISTINCT event_id)::VARCHAR || ' unique ids'
FROM events
UNION ALL
SELECT 'no_negative_watch_seconds', SUM(CASE WHEN watch_seconds < 0 THEN 1 ELSE 0 END) = 0, SUM(CASE WHEN watch_seconds < 0 THEN 1 ELSE 0 END)::VARCHAR || ' invalid rows'
FROM events
UNION ALL
SELECT 'rollout_limited_to_affected_regions',
       SUM(CASE WHEN model_version = 'v4.2' AND NOT (region IN ('IN-North', 'IN-South') AND event_date >= DATE '2025-11-17') THEN 1 ELSE 0 END) = 0,
       SUM(CASE WHEN model_version = 'v4.2' THEN 1 ELSE 0 END)::VARCHAR || ' v4.2 events'
FROM events;
