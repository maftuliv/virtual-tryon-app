import sys
import psycopg2

# Import centralized database configuration
try:
    from backend.db_config import parse_database_url
except ImportError:
    print("Error: Cannot import backend.db_config")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

try:
    print("Connecting to database...")
    conn = psycopg2.connect(**parse_database_url())
    cursor = conn.cursor()

    print("Dropping old table...")
    cursor.execute("DROP TABLE IF EXISTS device_limits CASCADE")
    conn.commit()

    print("Creating new table WITHOUT unique constraint...")
    cursor.execute("""
    CREATE TABLE device_limits (
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
    )
    """)
    conn.commit()

    print("Creating indexes...")
    cursor.execute("CREATE INDEX idx_device_fingerprint ON device_limits(device_fingerprint)")
    cursor.execute("CREATE INDEX idx_limit_date ON device_limits(limit_date)")
    cursor.execute("CREATE INDEX idx_ip_address ON device_limits(ip_address)")
    cursor.execute("CREATE INDEX idx_fp_date ON device_limits(device_fingerprint, limit_date)")
    cursor.execute("CREATE INDEX idx_ip_date ON device_limits(ip_address, limit_date)")
    conn.commit()

    print("\nTable recreated successfully!")
    print("Indexes:")
    cursor.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'device_limits' ORDER BY indexname")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")

    cursor.close()
    conn.close()
    print("\nDone!")

except ValueError as exc:
    print(f"\n❌ Configuration error: {exc}")
    print("Make sure DATABASE_URL is set in your environment or .env file")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
