-- Migration: Update device_limits for multi-factor IP tracking
-- Removes UNIQUE constraint from device_fingerprint to allow multiple IPs per fingerprint
-- Adds indexes for IP-based lookups

-- Drop the UNIQUE constraint on device_fingerprint
ALTER TABLE device_limits DROP CONSTRAINT IF EXISTS device_limits_device_fingerprint_key;

-- Add new indexes for efficient IP-based queries
CREATE INDEX IF NOT EXISTS idx_ip_address ON device_limits(ip_address);
CREATE INDEX IF NOT EXISTS idx_fp_date ON device_limits(device_fingerprint, limit_date);
CREATE INDEX IF NOT EXISTS idx_ip_date ON device_limits(ip_address, limit_date);

-- Update comments to reflect multi-factor protection
COMMENT ON TABLE device_limits IS 'Tracks daily generation limits using multi-factor protection (fingerprint + IP)';
COMMENT ON COLUMN device_limits.ip_address IS 'Client IP address for multi-factor limit tracking';
