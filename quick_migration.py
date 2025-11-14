import psycopg2

DATABASE_URL = "postgresql://postgres:rrQVBIrrzIFcRJlZCfjyrqYCmKSDfiKk@gondola.proxy.rlwy.net:15018/railway"

conn = psycopg2.connect(DATABASE_URL)
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
