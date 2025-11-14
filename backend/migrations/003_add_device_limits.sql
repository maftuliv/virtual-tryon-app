-- Migration: Add device fingerprint + IP tracking for anonymous users
-- Multi-factor protection: tracks BOTH fingerprint AND IP address
-- Prevents bypass via incognito mode, browser switching, VPN, etc.

CREATE TABLE IF NOT EXISTS device_limits (
    id SERIAL PRIMARY KEY,
    device_fingerprint VARCHAR(255) NOT NULL,
    generations_used INTEGER DEFAULT 0,
    limit_date DATE NOT NULL,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookups (CRITICAL: both fingerprint AND IP)
CREATE INDEX IF NOT EXISTS idx_device_fingerprint ON device_limits(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_limit_date ON device_limits(limit_date);
CREATE INDEX IF NOT EXISTS idx_ip_address ON device_limits(ip_address);
CREATE INDEX IF NOT EXISTS idx_fp_date ON device_limits(device_fingerprint, limit_date);
CREATE INDEX IF NOT EXISTS idx_ip_date ON device_limits(ip_address, limit_date);

-- Function to clean old records (older than 30 days)
CREATE OR REPLACE FUNCTION clean_old_device_limits()
RETURNS void AS $$
BEGIN
    DELETE FROM device_limits
    WHERE last_used_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE device_limits IS 'Tracks daily generation limits using multi-factor protection (fingerprint + IP)';
COMMENT ON COLUMN device_limits.device_fingerprint IS 'Device identifier combining canvas, WebGL, audio, and screen fingerprints';
COMMENT ON COLUMN device_limits.generations_used IS 'Number of generations used today for this fingerprint/IP';
COMMENT ON COLUMN device_limits.limit_date IS 'Date of the current limit (resets daily)';
COMMENT ON COLUMN device_limits.ip_address IS 'Client IP address for multi-factor limit tracking';
