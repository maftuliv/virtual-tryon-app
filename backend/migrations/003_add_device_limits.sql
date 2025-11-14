-- Migration: Add device fingerprint tracking for anonymous users
-- Prevents abuse by tracking device fingerprints instead of just localStorage

CREATE TABLE IF NOT EXISTS device_limits (
    id SERIAL PRIMARY KEY,
    device_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    generations_used INTEGER DEFAULT 0,
    limit_date DATE NOT NULL,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_device_fingerprint ON device_limits(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_limit_date ON device_limits(limit_date);

-- Function to clean old records (older than 30 days)
CREATE OR REPLACE FUNCTION clean_old_device_limits()
RETURNS void AS $$
BEGIN
    DELETE FROM device_limits
    WHERE last_used_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE device_limits IS 'Tracks daily generation limits for anonymous users using device fingerprinting';
COMMENT ON COLUMN device_limits.device_fingerprint IS 'Unique device identifier combining canvas, WebGL, audio, and screen fingerprints';
COMMENT ON COLUMN device_limits.generations_used IS 'Number of generations used today';
COMMENT ON COLUMN device_limits.limit_date IS 'Date of the current limit (resets daily)';
