"""Generation repository for tracking virtual try-on operations."""

from typing import Any, Dict, List, Optional

from backend.logger import get_logger

logger = get_logger(__name__)


class GenerationRepository:
    """
    Tracks virtual try-on generation records in PostgreSQL.

    Each generation represents one person+garment combination processed
    through the NanoBanana AI API.
    """

    def __init__(self, db_connection):
        """
        Initialize repository with database connection.

        Args:
            db_connection: psycopg2 connection object
        """
        self.db = db_connection

    def create(
        self,
        user_id: Optional[int],
        device_fingerprint: Optional[str],
        category: str,
        person_image_url: str,
        garment_image_url: str,
        result_image_url: Optional[str] = None,
        status: str = "pending",
    ) -> Dict[str, Any]:
        """
        Record a new generation attempt.

        Args:
            user_id: User ID (None for anonymous)
            device_fingerprint: Device identifier for anonymous users
            category: Garment category ("upper", "lower", "auto")
            person_image_url: URL to person image
            garment_image_url: URL to garment image
            result_image_url: URL to result (None initially)
            status: Generation status (default: "pending")

        Returns:
            Generation record dictionary:
            {
                'id': int,
                'user_id': int,
                'device_fingerprint': str,
                'category': str,
                'person_image_url': str,
                'garment_image_url': str,
                'result_image_url': str,
                'status': str,
                'created_at': datetime,
                'updated_at': datetime
            }

        Raises:
            Exception: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                INSERT INTO generations
                    (user_id, device_fingerprint, category,
                     person_image_url, garment_image_url, result_image_url, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, device_fingerprint, category,
                          person_image_url, garment_image_url, result_image_url,
                          status, created_at, updated_at
                """,
                (
                    user_id,
                    device_fingerprint,
                    category,
                    person_image_url,
                    garment_image_url,
                    result_image_url,
                    status,
                ),
            )

            row = cursor.fetchone()
            self.db.commit()
            cursor.close()

            return {
                "id": row[0],
                "user_id": row[1],
                "device_fingerprint": row[2],
                "category": row[3],
                "person_image_url": row[4],
                "garment_image_url": row[5],
                "result_image_url": row[6],
                "status": row[7],
                "created_at": row[8],
                "updated_at": row[9],
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating generation record: {e}", exc_info=True)
            raise

    def update_status(
        self, generation_id: int, status: str, result_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update generation status and optionally result URL.

        Args:
            generation_id: Generation record ID
            status: New status ("pending", "completed", "failed")
            result_url: Result image URL (optional)

        Returns:
            Updated generation record

        Raises:
            ValueError: If generation not found
            Exception: If database operation fails
        """
        try:
            cursor = self.db.cursor()

            if result_url:
                cursor.execute(
                    """
                    UPDATE generations
                    SET status = %s,
                        result_image_url = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, user_id, device_fingerprint, category,
                              person_image_url, garment_image_url, result_image_url,
                              status, created_at, updated_at
                    """,
                    (status, result_url, generation_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE generations
                    SET status = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, user_id, device_fingerprint, category,
                              person_image_url, garment_image_url, result_image_url,
                              status, created_at, updated_at
                    """,
                    (status, generation_id),
                )

            row = cursor.fetchone()

            if not row:
                cursor.close()
                raise ValueError(f"Generation {generation_id} not found")

            self.db.commit()
            cursor.close()

            return {
                "id": row[0],
                "user_id": row[1],
                "device_fingerprint": row[2],
                "category": row[3],
                "person_image_url": row[4],
                "garment_image_url": row[5],
                "result_image_url": row[6],
                "status": row[7],
                "created_at": row[8],
                "updated_at": row[9],
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating generation {generation_id}: {e}", exc_info=True)
            raise

    def update_r2_storage(
        self,
        generation_id: int,
        r2_key: str,
        r2_url: str,
        upload_size: int = None
    ) -> bool:
        """
        Update generation with R2 storage information.

        Args:
            generation_id: Generation record ID
            r2_key: Object key in R2 bucket
            r2_url: Public URL for the result
            upload_size: Size of uploaded file in bytes

        Returns:
            True if updated successfully
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                UPDATE generations
                SET result_r2_key = %s,
                    result_r2_url = %s,
                    r2_upload_size = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (r2_key, r2_url, upload_size, generation_id),
            )

            self.db.commit()
            cursor.close()

            logger.info(f"Updated R2 storage for generation {generation_id}: {r2_url}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating R2 storage for generation {generation_id}: {e}", exc_info=True)
            return False

    def set_favorite(self, generation_id: int, user_id: int, is_favorite: bool = True) -> bool:
        """
        Mark generation as favorite/unfavorite.

        Args:
            generation_id: Generation record ID
            user_id: User ID (for ownership verification)
            is_favorite: True to favorite, False to unfavorite

        Returns:
            True if updated successfully
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                UPDATE generations
                SET is_favorite = %s,
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s
                """,
                (is_favorite, generation_id, user_id),
            )

            affected = cursor.rowcount
            self.db.commit()
            cursor.close()

            return affected > 0

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting favorite for generation {generation_id}: {e}", exc_info=True)
            return False

    def set_title(self, generation_id: int, user_id: int, title: str) -> bool:
        """
        Set title for a generation.

        Args:
            generation_id: Generation record ID
            user_id: User ID (for ownership verification)
            title: New title

        Returns:
            True if updated successfully
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                UPDATE generations
                SET title = %s,
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s
                """,
                (title, generation_id, user_id),
            )

            affected = cursor.rowcount
            self.db.commit()
            cursor.close()

            return affected > 0

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting title for generation {generation_id}: {e}", exc_info=True)
            return False

    def list_by_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's generation history.

        Args:
            user_id: User ID
            limit: Maximum records to return (default: 100)
            offset: Pagination offset (default: 0)

        Returns:
            List of generation records, newest first
        """
        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                SELECT id, user_id, device_fingerprint, category,
                       person_image_url, garment_image_url, result_image_url,
                       status, created_at, updated_at
                FROM generations
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )

            rows = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "device_fingerprint": row[2],
                    "category": row[3],
                    "person_image_url": row[4],
                    "garment_image_url": row[5],
                    "result_image_url": row[6],
                    "status": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error listing generations for user {user_id}: {e}", exc_info=True)
            return []

    def list_all(
        self, limit: int = 100, offset: int = 0, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all generations (admin operation).

        Args:
            limit: Maximum records to return (default: 100)
            offset: Pagination offset (default: 0)
            user_id: Filter by user ID (optional)

        Returns:
            List of generation records with user info, newest first
        """
        try:
            cursor = self.db.cursor()

            if user_id:
                # Filter by specific user
                cursor.execute(
                    """
                    SELECT g.id, g.user_id, u.email, g.device_fingerprint,
                           g.category, g.person_image_url, g.garment_image_url,
                           g.result_image_url, g.status, g.created_at, g.updated_at
                    FROM generations g
                    LEFT JOIN users u ON g.user_id = u.id
                    WHERE g.user_id = %s
                    ORDER BY g.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
            else:
                # All generations
                cursor.execute(
                    """
                    SELECT g.id, g.user_id, u.email, g.device_fingerprint,
                           g.category, g.person_image_url, g.garment_image_url,
                           g.result_image_url, g.status, g.created_at, g.updated_at
                    FROM generations g
                    LEFT JOIN users u ON g.user_id = u.id
                    ORDER BY g.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )

            rows = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "user_email": row[2],
                    "device_fingerprint": row[3],
                    "category": row[4],
                    "person_image_url": row[5],
                    "garment_image_url": row[6],
                    "result_image_url": row[7],
                    "status": row[8],
                    "created_at": row[9],
                    "updated_at": row[10],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error listing all generations: {e}", exc_info=True)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get generation statistics.

        Returns:
            Dictionary with stats:
            {
                'total': int,
                'today': int,
                'by_category': {
                    'upper': int,
                    'lower': int,
                    'auto': int
                },
                'by_status': {
                    'completed': int,
                    'pending': int,
                    'failed': int
                }
            }
        """
        try:
            cursor = self.db.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) FROM generations")
            total = cursor.fetchone()[0]

            # Today's count
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM generations
                WHERE DATE(created_at) = CURRENT_DATE
                """
            )
            today = cursor.fetchone()[0]

            # By category
            cursor.execute(
                """
                SELECT category, COUNT(*)
                FROM generations
                GROUP BY category
                """
            )
            by_category = {row[0]: row[1] for row in cursor.fetchall()}

            # By status
            cursor.execute(
                """
                SELECT status, COUNT(*)
                FROM generations
                GROUP BY status
                """
            )
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.close()

            return {
                "total": total,
                "today": today,
                "by_category": by_category,
                "by_status": by_status,
            }

        except Exception as e:
            logger.error(f"Error getting generation stats: {e}", exc_info=True)
            return {
                "total": 0,
                "today": 0,
                "by_category": {},
                "by_status": {},
            }
