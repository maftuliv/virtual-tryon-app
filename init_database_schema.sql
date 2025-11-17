-- =============================================================
-- Complete Database Schema Initialization for TapToLook
-- Run this script to create all tables in a fresh database
-- Date: 2025-11-17
-- =============================================================

-- ============================================================
-- Table: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    provider VARCHAR(50) DEFAULT 'email' NOT NULL,
    provider_id VARCHAR(255),
    is_premium BOOLEAN DEFAULT FALSE,
    premium_until TIMESTAMP,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    CONSTRAINT email_lowercase CHECK (email = LOWER(email)),
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider, provider_id);
CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================
-- Table: generations
-- ============================================================
CREATE TABLE IF NOT EXISTS generations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    device_fingerprint VARCHAR(255),
    person_image_url TEXT,
    garment_image_url TEXT,
    result_image_url TEXT,
    result_r2_key TEXT,
    result_r2_url TEXT,
    thumbnail_url TEXT,
    title VARCHAR(255),
    is_favorite BOOLEAN DEFAULT FALSE,
    r2_upload_size INTEGER,
    category VARCHAR(50),
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generations_user_id ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_generations_created_at ON generations(created_at);
CREATE INDEX IF NOT EXISTS idx_generations_session_id ON generations(session_id);
CREATE INDEX IF NOT EXISTS idx_generations_device_fingerprint ON generations(device_fingerprint);

-- ============================================================
-- Table: daily_limits
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE DEFAULT CURRENT_DATE NOT NULL,
    generations_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_limits_user_date ON daily_limits(user_id, date);

-- ============================================================
-- Table: device_limits (for anonymous users)
-- ============================================================
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

CREATE INDEX IF NOT EXISTS idx_device_fingerprint ON device_limits(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_limit_date ON device_limits(limit_date);
CREATE INDEX IF NOT EXISTS idx_ip_address ON device_limits(ip_address);
CREATE INDEX IF NOT EXISTS idx_fp_date ON device_limits(device_fingerprint, limit_date);
CREATE INDEX IF NOT EXISTS idx_ip_date ON device_limits(ip_address, limit_date);

-- ============================================================
-- Table: sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================
-- Table: admin_sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_sessions_user_id ON admin_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires_at ON admin_sessions(expires_at);

-- ============================================================
-- Table: admin_audit_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER,
    payload JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_id ON admin_audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON admin_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_target ON admin_audit_logs(target_type, target_id);

-- ============================================================
-- Table: feedback (optional, if exists in production)
-- ============================================================
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    message TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);

-- ============================================================
-- Functions and Triggers
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for daily_limits updated_at
DROP TRIGGER IF EXISTS update_daily_limits_updated_at ON daily_limits;
CREATE TRIGGER update_daily_limits_updated_at
    BEFORE UPDATE ON daily_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for generations updated_at
DROP TRIGGER IF EXISTS update_generations_updated_at ON generations;
CREATE TRIGGER update_generations_updated_at
    BEFORE UPDATE ON generations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for device_limits updated_at
DROP TRIGGER IF EXISTS update_device_limits_updated_at ON device_limits;
CREATE TRIGGER update_device_limits_updated_at
    BEFORE UPDATE ON device_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to check and update premium status
CREATE OR REPLACE FUNCTION check_premium_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.premium_until IS NOT NULL AND NEW.premium_until < NOW() THEN
        NEW.is_premium = FALSE;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update premium status
DROP TRIGGER IF EXISTS check_user_premium_status ON users;
CREATE TRIGGER check_user_premium_status
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION check_premium_status();

-- Function to clean old device_limits records
CREATE OR REPLACE FUNCTION clean_old_device_limits()
RETURNS void AS $$
BEGIN
    DELETE FROM device_limits
    WHERE last_used_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Verification
-- ============================================================

SELECT 'Schema created successfully!' AS status;

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
