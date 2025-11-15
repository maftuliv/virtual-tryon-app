"""Feedback repository with dual storage (PostgreSQL primary, JSON files backup)."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.logger import get_logger

logger = get_logger(__name__)


class FeedbackRepository:
    """
    Feedback storage with dual persistence strategy.

    Primary: PostgreSQL database (if available)
    Fallback: JSON files in feedback folder

    This ensures feedback is never lost even if DB is temporarily unavailable.
    """

    def __init__(self, db_connection, feedback_folder: str):
        """
        Initialize repository with database and file storage.

        Args:
            db_connection: psycopg2 connection object (can be None)
            feedback_folder: Path to folder for JSON file backups
        """
        self.db = db_connection
        self.feedback_folder = feedback_folder

        # Ensure feedback folder exists
        os.makedirs(feedback_folder, exist_ok=True)

    def is_db_available(self) -> bool:
        """Check if database is available for feedback storage."""
        if self.db is None:
            return False

        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False

    def save(
        self,
        rating: int,
        comment: str,
        session_id: Optional[str],
        ip_address: str,
        telegram_sent: bool = False,
    ) -> Dict[str, Any]:
        """
        Save feedback to database and file backup.

        Strategy:
        1. Try to save to PostgreSQL (primary)
        2. Always save to JSON file (backup)
        3. Return combined result

        Args:
            rating: Rating (1-5)
            comment: User comment text
            session_id: Session identifier (optional)
            ip_address: Client IP address
            telegram_sent: Whether notification was sent to Telegram

        Returns:
            Feedback record dictionary:
            {
                'id': int (or None if DB unavailable),
                'rating': int,
                'comment': str,
                'session_id': str,
                'ip_address': str,
                'telegram_sent': bool,
                'telegram_error': str,
                'created_at': datetime,
                'file_path': str  # Path to JSON backup
            }
        """
        feedback_data = {
            "rating": rating,
            "comment": comment,
            "session_id": session_id,
            "ip_address": ip_address,
            "telegram_sent": telegram_sent,
            "created_at": datetime.now().isoformat(),
        }

        db_id = None
        db_success = False

        # Try database first
        if self.is_db_available():
            try:
                db_id = self._save_to_db(
                    rating, comment, session_id, ip_address, telegram_sent
                )
                db_success = True
                logger.info(f"Feedback saved to database (ID: {db_id})")
            except Exception as e:
                logger.error(f"Failed to save feedback to database: {e}", exc_info=True)

        # Always save to file (backup)
        try:
            file_path = self._save_to_file(feedback_data)
            logger.info(f"Feedback saved to file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save feedback to file: {e}", exc_info=True)
            file_path = None

        return {
            "id": db_id,
            "rating": rating,
            "comment": comment,
            "session_id": session_id,
            "ip_address": ip_address,
            "telegram_sent": telegram_sent,
            "created_at": feedback_data["created_at"],
            "file_path": file_path,
            "db_saved": db_success,
        }

    def _save_to_db(
        self,
        rating: int,
        comment: str,
        session_id: Optional[str],
        ip_address: str,
        telegram_sent: bool,
    ) -> int:
        """
        Save feedback to PostgreSQL database.

        Returns:
            Feedback record ID

        Raises:
            Exception: If database operation fails
        """
        cursor = self.db.cursor()

        cursor.execute(
            """
            INSERT INTO feedback
                (rating, comment, session_id, ip_address, telegram_sent)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (rating, comment, session_id, ip_address, telegram_sent),
        )

        feedback_id = cursor.fetchone()[0]
        self.db.commit()
        cursor.close()

        return feedback_id

    def _save_to_file(self, feedback_data: Dict[str, Any]) -> str:
        """
        Save feedback to JSON file.

        Args:
            feedback_data: Feedback dictionary

        Returns:
            Path to saved JSON file

        Raises:
            Exception: If file write fails
        """
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"feedback_{timestamp}.json"
        file_path = os.path.join(self.feedback_folder, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)

        return file_path

    def list_all(self, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieve all feedback.

        Strategy:
        1. Try PostgreSQL first (primary source)
        2. Fallback to JSON files if DB unavailable

        Args:
            limit: Maximum number of records (default: 100)

        Returns:
            Dictionary with feedback list:
            {
                'source': 'database' or 'files',
                'count': int,
                'feedback': List[Dict]
            }
        """
        # Try database first
        if self.is_db_available():
            try:
                feedback_list = self._load_from_db(limit)
                return {
                    "source": "database",
                    "count": len(feedback_list),
                    "feedback": feedback_list,
                }
            except Exception as e:
                logger.error(f"Failed to load feedback from database: {e}", exc_info=True)

        # Fallback to files
        try:
            feedback_list = self._load_from_files()
            return {
                "source": "files",
                "count": len(feedback_list),
                "feedback": feedback_list[:limit],  # Apply limit
            }
        except Exception as e:
            logger.error(f"Failed to load feedback from files: {e}", exc_info=True)
            return {
                "source": "none",
                "count": 0,
                "feedback": [],
            }

    def _load_from_db(self, limit: int) -> List[Dict[str, Any]]:
        """
        Load feedback from PostgreSQL.

        Args:
            limit: Maximum records

        Returns:
            List of feedback dictionaries
        """
        cursor = self.db.cursor()

        cursor.execute(
            """
            SELECT id, rating, comment, session_id, ip_address,
                   telegram_sent, telegram_error, created_at
            FROM feedback
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )

        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "id": row[0],
                "rating": row[1],
                "comment": row[2],
                "session_id": row[3],
                "ip_address": row[4],
                "telegram_sent": row[5],
                "telegram_error": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
            }
            for row in rows
        ]

    def _load_from_files(self) -> List[Dict[str, Any]]:
        """
        Load all feedback from JSON files.

        Returns:
            List of feedback dictionaries, sorted by created_at (newest first)
        """
        feedback_list = []

        for filename in os.listdir(self.feedback_folder):
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(self.feedback_folder, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["file_path"] = file_path
                    feedback_list.append(data)
            except Exception as e:
                logger.error(f"Failed to load feedback file {filename}: {e}")

        # Sort by created_at (newest first)
        feedback_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return feedback_list

    def get_unsent_telegram(self) -> List[Dict[str, Any]]:
        """
        Get feedback records not yet sent to Telegram.

        Only works with database source.

        Returns:
            List of unsent feedback records
        """
        if not self.is_db_available():
            logger.warning("Cannot get unsent Telegram feedback - database unavailable")
            return []

        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                SELECT id, rating, comment, session_id, ip_address, created_at
                FROM feedback
                WHERE telegram_sent = FALSE
                ORDER BY created_at ASC
                """
            )

            rows = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": row[0],
                    "rating": row[1],
                    "comment": row[2],
                    "session_id": row[3],
                    "ip_address": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting unsent Telegram feedback: {e}", exc_info=True)
            return []

    def mark_telegram_sent(
        self, feedback_id: int, success: bool, error_message: Optional[str] = None
    ):
        """
        Update telegram_sent status for feedback record.

        Args:
            feedback_id: Feedback record ID
            success: True if sent successfully, False if failed
            error_message: Error message if failed (optional)

        Raises:
            Exception: If database operation fails
        """
        if not self.is_db_available():
            logger.warning("Cannot mark Telegram sent - database unavailable")
            return

        try:
            cursor = self.db.cursor()

            cursor.execute(
                """
                UPDATE feedback
                SET telegram_sent = %s,
                    telegram_error = %s
                WHERE id = %s
                """,
                (success, error_message, feedback_id),
            )

            self.db.commit()
            cursor.close()

            logger.debug(f"Marked feedback {feedback_id} as Telegram sent={success}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking Telegram sent for feedback {feedback_id}: {e}", exc_info=True)
            raise
