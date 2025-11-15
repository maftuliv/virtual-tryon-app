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
    conn = psycopg2.connect(**parse_database_url())
    cursor = conn.cursor()

    print("Dropping UNIQUE constraint...")
    cursor.execute("ALTER TABLE device_limits DROP CONSTRAINT IF EXISTS device_limits_device_fingerprint_key;")

    print("Creating IP index...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_address ON device_limits(ip_address);")

    print("Creating composite indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fp_date ON device_limits(device_fingerprint, limit_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_date ON device_limits(ip_address, limit_date);")

    conn.commit()

    print("\nVerifying indexes:")
    cursor.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'device_limits' ORDER BY indexname")
    for idx in cursor.fetchall():
        print(f"  - {idx[0]}")

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
