#!/usr/bin/env python3
"""
Migration 007: Add R2 storage fields to generations table

Adds fields for permanent image storage in Cloudflare R2:
- result_r2_key: Object key in R2 bucket
- result_r2_url: Public URL for the result image
- thumbnail_url: Optional thumbnail for gallery view
- title: Optional user-given title for the generation
- is_favorite: Whether user marked as favorite
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_migration():
    """Add R2 storage fields to generations table."""
    import psycopg2

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False

    # Fix postgres:// to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("=" * 60)
        print("Migration 007: Adding R2 storage fields to generations")
        print("=" * 60)

        # Check which columns already exist
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'generations'
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        print(f"Existing columns: {existing_columns}")

        # Add result_r2_key
        if 'result_r2_key' not in existing_columns:
            print("Adding result_r2_key column...")
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN result_r2_key TEXT
            """)
            print("✅ Added result_r2_key")
        else:
            print("⏭️  result_r2_key already exists")

        # Add result_r2_url (permanent public URL)
        if 'result_r2_url' not in existing_columns:
            print("Adding result_r2_url column...")
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN result_r2_url TEXT
            """)
            print("✅ Added result_r2_url")
        else:
            print("⏭️  result_r2_url already exists")

        # Add thumbnail_url (for gallery previews)
        if 'thumbnail_url' not in existing_columns:
            print("Adding thumbnail_url column...")
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN thumbnail_url TEXT
            """)
            print("✅ Added thumbnail_url")
        else:
            print("⏭️  thumbnail_url already exists")

        # Add title (user-given name for generation)
        if 'title' not in existing_columns:
            print("Adding title column...")
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN title VARCHAR(255)
            """)
            print("✅ Added title")
        else:
            print("⏭️  title already exists")

        # Add is_favorite flag
        if 'is_favorite' not in existing_columns:
            print("Adding is_favorite column...")
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE
            """)
            print("✅ Added is_favorite")
        else:
            print("⏭️  is_favorite already exists")

        # Add r2_upload_size (track storage usage)
        if 'r2_upload_size' not in existing_columns:
            print("Adding r2_upload_size column...")
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN r2_upload_size INTEGER
            """)
            print("✅ Added r2_upload_size")
        else:
            print("⏭️  r2_upload_size already exists")

        conn.commit()
        cursor.close()
        conn.close()

        print("=" * 60)
        print("✅ Migration 007 completed successfully!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
