#!/usr/bin/env python3
"""Verify admin password hash in database."""

import sys
sys.path.insert(0, '.')

from backend.config import Settings
import psycopg2
from werkzeug.security import check_password_hash, generate_password_hash

def main():
    config = Settings()
    conn = psycopg2.connect(str(config.database_url))
    cursor = conn.cursor()

    email = 'maftoul.eli@gmail.com'
    password = 'qHjs7fzFXR1994'

    # Get user data
    cursor.execute(
        'SELECT id, email, password_hash, provider, role FROM users WHERE email = %s',
        (email,)
    )

    user = cursor.fetchone()
    if not user:
        print(f'[ERROR] User {email} not found!')
        return

    user_id, db_email, password_hash, provider, role = user

    print(f'User ID: {user_id}')
    print(f'Email: {db_email}')
    print(f'Provider: {provider}')
    print(f'Role: {role}')
    print(f'Password hash exists: {bool(password_hash)}')

    if password_hash:
        print(f'Password hash (first 50 chars): {password_hash[:50]}...')

        # Test password verification
        is_valid = check_password_hash(password_hash, password)
        print(f'\n[TEST] Password verification: {"PASSED" if is_valid else "FAILED"}')

        if not is_valid:
            print('\n[WARNING] Password hash does not match! Resetting password...')
            new_hash = generate_password_hash(password)
            cursor.execute(
                'UPDATE users SET password_hash = %s WHERE id = %s',
                (new_hash, user_id)
            )
            conn.commit()
            print(f'[OK] Password reset successfully!')

            # Verify again
            cursor.execute('SELECT password_hash FROM users WHERE id = %s', (user_id,))
            new_stored_hash = cursor.fetchone()[0]
            final_check = check_password_hash(new_stored_hash, password)
            print(f'[FINAL] Verification: {"PASSED" if final_check else "FAILED"}')
    else:
        print('\n[WARNING] No password hash set! Setting password...')
        new_hash = generate_password_hash(password)
        cursor.execute(
            'UPDATE users SET password_hash = %s WHERE id = %s',
            (new_hash, user_id)
        )
        conn.commit()
        print(f'[OK] Password set successfully!')

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
