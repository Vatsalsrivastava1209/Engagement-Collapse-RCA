
CREATE TABLE IF NOT EXISTS raw_events_raw (
    raw JSONB
);


CREATE TABLE IF NOT EXISTS raw_events (
    event_id TEXT,
    user_id INT,
    event_type TEXT,
    content_id TEXT,
    device TEXT,
    app_version TEXT,
    region TEXT,
    ts TIMESTAMPTZ,
    seek_seconds INT,
    raw JSONB
);


CREATE MATERIALIZED VIEW IF NOT EXISTS events_with_ts AS
SELECT 
    *,
    ts::timestamp AS event_timestamp,
    ts::date AS event_date
FROM raw_events;
