#!/usr/bin/env python3
"""Set password for admin user."""

import sys
sys.path.insert(0, '.')

from backend.config import Settings
import psycopg2
from werkzeug.security import generate_password_hash

def main():
    config = Settings()
    conn = psycopg2.connect(str(config.database_url))
    cursor = conn.cursor()

    email = 'maftoul.eli@gmail.com'
    password = 'qHjs7fzFXR1994'

    password_hash = generate_password_hash(password)
    cursor.execute('UPDATE users SET password_hash = %s WHERE email = %s RETURNING id', (password_hash, email))

    result = cursor.fetchone()
    if result:
        conn.commit()
        print(f'✅ Password set successfully for {email} (user_id: {result[0]})')
    else:
        print(f'❌ User {email} not found!')

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
