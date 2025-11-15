-- Migration: Create admin_audit_logs table
-- Purpose: Track all administrative actions for security and compliance
-- Author: Generated with Claude Code
-- Date: 2025-11-15

-- Create admin_audit_logs table
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,  -- e.g., 'change_role', 'toggle_premium', 'reset_limit', 'delete_feedback'
    target_type VARCHAR(50) NOT NULL,  -- e.g., 'user', 'feedback', 'system'
    target_id INTEGER,  -- ID of affected entity (can be NULL for system-wide actions)
    payload JSONB,  -- Additional context: old/new values, reason, etc.
    ip_address VARCHAR(45),  -- IPv4 or IPv6
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX idx_admin_audit_logs_admin_id ON admin_audit_logs(admin_id);
CREATE INDEX idx_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);
CREATE INDEX idx_admin_audit_logs_action ON admin_audit_logs(action);
CREATE INDEX idx_admin_audit_logs_target ON admin_audit_logs(target_type, target_id);

-- Add comment
COMMENT ON TABLE admin_audit_logs IS 'Audit trail for all administrative actions';
COMMENT ON COLUMN admin_audit_logs.action IS 'Type of action performed';
COMMENT ON COLUMN admin_audit_logs.payload IS 'JSON object with action details (old/new values, etc.)';
