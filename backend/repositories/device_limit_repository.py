"""Device limit repository for PostgreSQL."""

from datetime import date, datetime
from typing import Any, Dict, Optional

import psycopg2

from backend.logger import get_logger

logger = get_logger(__name__)


class DeviceLimitRepository:
    """Manages device limit records in PostgreSQL database."""

    def __init__(self, db_connection):
        """
        Initialize repository with database connection.

        Args:
            db_connection: psycopg2 connection object or connection pool
        """
        self.db = db_connection

    def ensure_service_available(self) -> bool:
        """
        Check if database service is available.

        Returns:
            True if database is available, False otherwise
        """
        try:
            if self.db is None:
                return False
            # Test connection with a simple query
            cursor = self.db.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Database service unavailable: {e}")
            return False

    def get_limit_status(
        self, device_fingerprint: str, ip_address: str, limit_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get device limit status for a specific date.

        Args:
            device_fingerprint: Unique device identifier
            ip_address: Client IP address
            limit_date: Date to check limits for

        Returns:
            Dictionary with limit record or None if not found:
            {
                'id': int,
                'device_fingerprint': str,
                'ip_address': str,
                'generations_used': int,
                'limit_date': date,
                'last_used_at': datetime,
                'created_at': datetime,
                'updated_at': datetime
            }
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT id, device_fingerprint, ip_address, generations_used,
                       limit_date, last_used_at, created_at, updated_at
                FROM device_limits
                WHERE device_fingerprint = %s
                  AND ip_address = %s
                  AND limit_date = %s
                """,
                (device_fingerprint, ip_address, limit_date),
            )

            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                "id": row[0],
                "device_fingerprint": row[1],
                "ip_address": row[2],
                "generations_used": row[3],
                "limit_date": row[4],
                "last_used_at": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            }

        except Exception as e:
            logger.error(f"Error getting limit status: {e}", exc_info=True)
            return None

    def create_or_reset_record(
        self, device_fingerprint: str, ip_address: str, user_agent: str, limit_date: date
    ) -> Dict[str, Any]:
        """
        Create new device limit record or reset if date changed.

        If record exists for same device but different date, reset counter.
        If record exists for same date, return existing.

        Args:
            device_fingerprint: Unique device identifier
            ip_address: Client IP address
            user_agent: User agent string
            limit_date: Date for limit tracking

        Returns:
            Device limit record dictionary

        Raises:
            Exception: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            # Check if record exists for today
            existing = self.get_limit_status(device_fingerprint, ip_address, limit_date)

            if existing:
                cursor.close()
                return existing

            # Check if record exists for a different date (need to reset)
            cursor.execute(
                """
                SELECT id, limit_date
                FROM device_limits
                WHERE device_fingerprint = %s AND ip_address = %s
                ORDER BY limit_date DESC
                LIMIT 1
                """,
                (device_fingerprint, ip_address),
            )

            old_record = cursor.fetchone()

            if old_record and old_record[1] != limit_date:
                # Different date - reset counter
                cursor.execute(
                    """
                    UPDATE device_limits
                    SET generations_used = 0,
                        limit_date = %s,
                        updated_at = NOW()
                    WHERE device_fingerprint = %s AND ip_address = %s
                    RETURNING id, device_fingerprint, ip_address, generations_used,
                              limit_date, last_used_at, created_at, updated_at
                    """,
                    (limit_date, device_fingerprint, ip_address),
                )
            else:
                # No record at all - create new
                cursor.execute(
                    """
                    INSERT INTO device_limits
                        (device_fingerprint, ip_address, user_agent, generations_used, limit_date)
                    VALUES (%s, %s, %s, 0, %s)
                    RETURNING id, device_fingerprint, ip_address, generations_used,
                              limit_date, last_used_at, created_at, updated_at
                    """,
                    (device_fingerprint, ip_address, user_agent, limit_date),
                )

            row = cursor.fetchone()
            self.db.commit()
            cursor.close()

            return {
                "id": row[0],
                "device_fingerprint": row[1],
                "ip_address": row[2],
                "generations_used": row[3],
                "limit_date": row[4],
                "last_used_at": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating/resetting record: {e}", exc_info=True)
            raise

    def increment_usage(
        self, device_fingerprint: str, ip_address: str, limit_date: date, increment: int = 1
    ) -> Dict[str, Any]:
        """
        Atomically increment generations_used counter.

        Args:
            device_fingerprint: Unique device identifier
            ip_address: Client IP address
            limit_date: Date to increment for
            increment: Amount to increment (default: 1)

        Returns:
            Updated device limit record

        Raises:
            Exception: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                UPDATE device_limits
                SET generations_used = generations_used + %s,
                    last_used_at = NOW(),
                    updated_at = NOW()
                WHERE device_fingerprint = %s
                  AND ip_address = %s
                  AND limit_date = %s
                RETURNING id, device_fingerprint, ip_address, generations_used,
                          limit_date, last_used_at, created_at, updated_at
                """,
                (increment, device_fingerprint, ip_address, limit_date),
            )

            row = cursor.fetchone()

            if not row:
                cursor.close()
                raise ValueError(
                    f"No device limit record found for {device_fingerprint} on {limit_date}"
                )

            self.db.commit()
            cursor.close()

            return {
                "id": row[0],
                "device_fingerprint": row[1],
                "ip_address": row[2],
                "generations_used": row[3],
                "limit_date": row[4],
                "last_used_at": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error incrementing usage: {e}", exc_info=True)
            raise

    def calculate_total_usage(
        self, device_fingerprint: str, ip_address: str, limit_date: date
    ) -> int:
        """
        Calculate total generations used for device on specific date.

        Args:
            device_fingerprint: Unique device identifier
            ip_address: Client IP address
            limit_date: Date to check

        Returns:
            Total generation count
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                SELECT COALESCE(SUM(generations_used), 0)
                FROM device_limits
                WHERE device_fingerprint = %s
                  AND ip_address = %s
                  AND limit_date = %s
                """,
                (device_fingerprint, ip_address, limit_date),
            )

            total = cursor.fetchone()[0]
            cursor.close()

            return int(total) if total else 0

        except Exception as e:
            logger.error(f"Error calculating usage: {e}", exc_info=True)
            return 0

    def reset_all_for_date(self, limit_date: date) -> int:
        """
        Reset all device limits for a specific date (admin operation).

        Args:
            limit_date: Date to reset limits for

        Returns:
            Number of records updated
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                UPDATE device_limits
                SET generations_used = 0, updated_at = NOW()
                WHERE limit_date = %s
                RETURNING id
                """,
                (limit_date,),
            )

            count = cursor.rowcount
            self.db.commit()
            cursor.close()

            logger.info(f"Reset {count} device limit records for {limit_date}")
            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resetting limits: {e}", exc_info=True)
            raise
