-- =========================================
-- indexes.sql
-- Purpose: Performance optimization for analytics queries
-- =========================================

-- -----------------------------------------
-- Core Indexes (Must-Have)
-- -----------------------------------------

-- User-based analysis (DAU, retention, sessions)
CREATE INDEX IF NOT EXISTS idx_engagement_user
ON engagement_events (user_id);

-- Time-series analysis (daily trends, drops)
CREATE INDEX IF NOT EXISTS idx_engagement_timestamp
ON engagement_events (timestamp);

-- Regional segmentation
CREATE INDEX IF NOT EXISTS idx_engagement_region
ON engagement_events (region);

-- Event filtering (app_open, video_play, etc.)
CREATE INDEX IF NOT EXISTS idx_engagement_event_type
ON engagement_events (event_type);

-- -----------------------------------------
-- Composite Indexes (FAANG-level)
-- -----------------------------------------

-- Fast DAU per region per day
CREATE INDEX IF NOT EXISTS idx_event_date_region
ON engagement_events (DATE(timestamp), region);

-- Session & funnel analysis
CREATE INDEX IF NOT EXISTS idx_user_event_time
ON engagement_events (user_id, timestamp);

-- Content-level engagement analysis
CREATE INDEX IF NOT EXISTS idx_content_event
ON engagement_events (content_id, event_type);

-- -----------------------------------------
-- Verification
-- -----------------------------------------

SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'engagement_events';
