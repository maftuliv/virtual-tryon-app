#!/usr/bin/env python3
"""
CLI script to promote a user to admin role.

Usage:
    python scripts/make_admin.py <user_email>

Example:
    python scripts/make_admin.py maftoul.eli@gmail.com
"""

import os
import sys

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from backend.config import Settings


def make_admin(email: str):
    """
    Promote user to admin role.

    Args:
        email: User email address
    """
    # Load config
    config = Settings()

    if not config.database_url:
        print("❌ ERROR: DATABASE_URL not set")
        sys.exit(1)

    # Connect to database
    try:
        conn = psycopg2.connect(str(config.database_url))
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id, email, role FROM users WHERE email = %s", (email.lower().strip(),))
        user = cursor.fetchone()

        if not user:
            print(f"❌ ERROR: User with email '{email}' not found")
            cursor.close()
            conn.close()
            sys.exit(1)

        user_id, user_email, current_role = user

        if current_role == 'admin':
            print(f"ℹ️  User '{user_email}' (ID: {user_id}) is already an admin")
            cursor.close()
            conn.close()
            return

        # Update role to admin
        cursor.execute(
            "UPDATE users SET role = 'admin' WHERE id = %s",
            (user_id,)
        )
        conn.commit()

        print(f"✅ SUCCESS: User '{user_email}' (ID: {user_id}) promoted to admin")
        print(f"   Previous role: {current_role}")
        print(f"   New role: admin")
        print(f"\n🛡️  Admin panel: https://taptolook.net/admin")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/make_admin.py <user_email>")
        print("\nExample:")
        print("  python scripts/make_admin.py maftoul.eli@gmail.com")
        sys.exit(1)

    email = sys.argv[1]
    make_admin(email)
