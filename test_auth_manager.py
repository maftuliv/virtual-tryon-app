#!/usr/bin/env python3
"""Test AuthManager.login_user() directly."""

import sys
sys.path.insert(0, '.')

from backend.config import Settings
import psycopg2
from werkzeug.security import check_password_hash

def main():
    print("=== Testing AuthManager.login_user() logic ===\n")

    config = Settings()
    conn = psycopg2.connect(str(config.database_url))
    cursor = conn.cursor()

    email = 'maftoul.eli@gmail.com'.lower().strip()
    password = 'qHjs7fzFXR1994'

    print(f"Email: {email}")
    print(f"Password: {password}")
    print()

    # This is the exact query from AuthManager.login_user()
    print("Executing query (without provider filter):")
    cursor.execute(
        """
        SELECT id, email, password_hash, full_name, avatar_url, is_premium, premium_until, role
        FROM users
        WHERE email = %s
        """,
        (email,),
    )
    user = cursor.fetchone()

    if not user:
        print("  [ERROR] User not found!")
        return

    print(f"  User ID: {user[0]}")
    print(f"  Email: {user[1]}")
    print(f"  Password hash exists: {bool(user[2])}")
    print(f"  Full name: {user[3]}")
    print(f"  Role: {user[7] if len(user) > 7 else 'user'}")
    print()

    # Verify password
    if user[2]:
        is_valid = check_password_hash(user[2], password)
        print(f"Password check: {'PASSED' if is_valid else 'FAILED'}")

        if is_valid:
            print("\n[SUCCESS] Login should work!")
            print("User data would be:")
            user_data = {
                "id": user[0],
                "email": user[1],
                "full_name": user[3],
                "avatar_url": user[4],
                "is_premium": user[5],
                "premium_until": user[6].isoformat() if user[6] else None,
                "role": user[7] if len(user) > 7 else "user",
            }
            for key, value in user_data.items():
                print(f"  {key}: {value}")
        else:
            print("\n[ERROR] Password verification failed!")
    else:
        print("[ERROR] No password hash set!")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
