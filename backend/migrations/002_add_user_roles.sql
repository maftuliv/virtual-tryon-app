-- ============================================================
-- Migration: Add user roles (admin/user)
-- Date: 2025-11-14
-- Description: Adds role column to users table for admin panel
-- ============================================================

-- Add role column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

-- Add check constraint to ensure valid roles
ALTER TABLE users ADD CONSTRAINT valid_role CHECK (role IN ('admin', 'user'));

-- Create index for faster role queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Set admin role for specific user
UPDATE users
SET role = 'admin'
WHERE email = 'maftul4d@gmail.com';

-- Display confirmation
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Admin user: maftul4d@gmail.com';
END $$;
