-- Migration: Create authentication and user management tables
-- Date: 2025-11-14
-- Description: Tables for users, authentication, premium subscriptions, and daily limits

-- ============================================================
-- Table: users
-- Description: Store user accounts and authentication data
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL for OAuth users
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    provider VARCHAR(50) DEFAULT 'email' NOT NULL,  -- 'email', 'google', 'vk', 'telegram'
    provider_id VARCHAR(255),  -- ID from OAuth provider
    is_premium BOOLEAN DEFAULT FALSE,
    premium_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    CONSTRAINT email_lowercase CHECK (email = LOWER(email))
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_provider ON users(provider, provider_id);
CREATE INDEX idx_users_premium ON users(is_premium);

-- ============================================================
-- Table: generations
-- Description: Store user's virtual try-on generation history
-- ============================================================
CREATE TABLE IF NOT EXISTS generations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    person_image_url TEXT,
    garment_image_url TEXT,
    result_image_url TEXT,
    category VARCHAR(50),  -- 'upper', 'lower', 'overall'
    status VARCHAR(50) DEFAULT 'completed',  -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for generations table
CREATE INDEX idx_generations_user_id ON generations(user_id);
CREATE INDEX idx_generations_created_at ON generations(created_at);
CREATE INDEX idx_generations_session_id ON generations(session_id);

-- ============================================================
-- Table: daily_limits
-- Description: Track daily generation limits for free users
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

-- Indexes for daily_limits table
CREATE INDEX idx_daily_limits_user_date ON daily_limits(user_id, date);

-- ============================================================
-- Table: sessions
-- Description: Store active user sessions (optional, for session management)
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

-- Indexes for sessions table
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

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
CREATE TRIGGER update_daily_limits_updated_at
    BEFORE UPDATE ON daily_limits
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
CREATE TRIGGER check_user_premium_status
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION check_premium_status();

-- ============================================================
-- Insert demo users (optional, for testing)
-- ============================================================

-- Demo free user
INSERT INTO users (email, password_hash, full_name, provider)
VALUES (
    'demo@taptolook.net',
    'pbkdf2:sha256:600000$demo$demo_hash_placeholder',  -- Password: "demo123"
    'Demo User',
    'email'
) ON CONFLICT (email) DO NOTHING;

-- Demo premium user
INSERT INTO users (email, password_hash, full_name, provider, is_premium, premium_until)
VALUES (
    'premium@taptolook.net',
    'pbkdf2:sha256:600000$premium$premium_hash_placeholder',  -- Password: "premium123"
    'Premium User',
    'email',
    TRUE,
    NOW() + INTERVAL '30 days'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- Grant permissions (adjust based on your database user)
-- ============================================================

-- Grant permissions to your application database user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON users TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON generations TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON daily_limits TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON sessions TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ============================================================
-- Verification queries
-- ============================================================

-- Check table creation
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('users', 'generations', 'daily_limits', 'sessions');

-- Show table structures
-- \d users
-- \d generations
-- \d daily_limits
-- \d sessions
