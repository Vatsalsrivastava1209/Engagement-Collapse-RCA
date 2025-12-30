
\set ON_ERROR_STOP on

TRUNCATE TABLE engagement_events;

-- Load CSV data
COPY engagement_events (
    event_id,
    user_id,
    event_type,
    content_id,
    device,
    app_version,
    region,
    timestamp
)
FROM '/absolute/path/to/engagement_logs.csv'
DELIMITER ','
CSV HEADER;

-- Verify load
SELECT COUNT(*) AS total_rows_loaded FROM engagement_events;
