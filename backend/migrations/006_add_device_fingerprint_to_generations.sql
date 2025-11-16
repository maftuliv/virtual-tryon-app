-- Migration: Add device_fingerprint and updated_at columns to generations table
-- This allows tracking generations for anonymous users and provides update timestamps

-- Add device_fingerprint column for anonymous user tracking
ALTER TABLE generations ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255);

-- Add updated_at column for tracking modifications
ALTER TABLE generations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Create index for device_fingerprint queries
CREATE INDEX IF NOT EXISTS idx_generations_device_fingerprint ON generations(device_fingerprint);

-- Update existing records to have updated_at = created_at
UPDATE generations SET updated_at = created_at WHERE updated_at IS NULL;
