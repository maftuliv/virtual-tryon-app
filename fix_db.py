import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway')
    cursor = conn.cursor()

    print("1. Dropping UNIQUE constraint...")
    cursor.execute("ALTER TABLE device_limits DROP CONSTRAINT IF EXISTS device_limits_device_fingerprint_key")

    print("2. Creating IP index...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_address ON device_limits(ip_address)")

    print("3. Creating composite indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fp_date ON device_limits(device_fingerprint, limit_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_date ON device_limits(ip_address, limit_date)")

    conn.commit()

    print("\nVerifying indexes:")
    cursor.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'device_limits' ORDER BY indexname")
    for row in cursor.fetchall():
        print("  - " + row[0])

    cursor.close()
    conn.close()

    print("\nMigration completed successfully!")
    sys.exit(0)

except Exception as e:
    print("ERROR: " + str(e))
    sys.exit(1)
