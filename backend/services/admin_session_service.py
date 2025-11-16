"""
Admin session management service.

Provides server-side session storage for admin users to keep the admin panel reliable.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from backend.logger import get_logger

logger = get_logger(__name__)


class AdminSessionService:
    """Handles creation and validation of admin sessions stored in the database."""

    def __init__(self, db_connection, session_hours: int = 12):
        self.db = db_connection
        self.session_duration = timedelta(hours=session_hours)

    def is_available(self) -> bool:
        return self.db is not None

    def _utcnow(self) -> datetime:
        return datetime.now(timezone.utc)

    def create_session(self, user_id: int, ip_address: Optional[str], user_agent: Optional[str]) -> Optional[str]:
        """Create session for admin user and return session id."""
        if not self.is_available():
            logger.warning("[ADMIN-SESSION] Service unavailable, cannot create session")
            return None

        session_id = secrets.token_urlsafe(48)
        expires_at = self._utcnow() + self.session_duration

        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO admin_sessions (session_id, user_id, ip_address, user_agent, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, user_id, ip_address, user_agent, expires_at),
            )
            self.db.commit()
            logger.info("[ADMIN-SESSION] Created session for user_id=%s", user_id)
            return session_id
        except Exception as e:
            self.db.rollback()
            logger.error(f"[ADMIN-SESSION] Failed to create session: {e}", exc_info=True)
            return None
        finally:
            cursor.close()

    def delete_session(self, session_id: str) -> None:
        if not self.is_available() or not session_id:
            return

        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM admin_sessions WHERE session_id = %s", (session_id,))
            self.db.commit()
            logger.info("[ADMIN-SESSION] Deleted session %s", session_id[:8])
        except Exception as e:
            self.db.rollback()
            logger.error(f"[ADMIN-SESSION] Failed to delete session: {e}", exc_info=True)
        finally:
            cursor.close()

    def delete_user_sessions(self, user_id: int) -> None:
        if not self.is_available():
            return

        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM admin_sessions WHERE user_id = %s", (user_id,))
            self.db.commit()
            logger.info("[ADMIN-SESSION] Deleted sessions for user_id=%s", user_id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"[ADMIN-SESSION] Failed to delete user sessions: {e}", exc_info=True)
        finally:
            cursor.close()

    def get_session_user(self, session_id: str) -> Optional[Dict]:
        """Return admin user linked to session if valid (not expired)."""
        if not self.is_available() or not session_id:
            return None

        cursor = self.db.cursor()
        try:
            cursor.execute(
                """
                SELECT s.user_id,
                       s.expires_at,
                       u.email,
                       u.full_name,
                       u.role,
                       u.is_premium,
                       u.avatar_url
                FROM admin_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.session_id = %s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            user_id, expires_at, email, full_name, role, is_premium, avatar_url = row

            if expires_at <= self._utcnow():
                logger.info("[ADMIN-SESSION] Session expired for user_id=%s", user_id)
                cursor.close()
                self.delete_session(session_id)
                return None

            if role != "admin":
                logger.warning("[ADMIN-SESSION] Non-admin role detected for session (user_id=%s)", user_id)
                return None

            return {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "role": role,
                "is_premium": is_premium,
                "avatar_url": avatar_url,
            }
        except Exception as e:
            logger.error(f"[ADMIN-SESSION] Failed to validate session: {e}", exc_info=True)
            return None
        finally:
            cursor.close()

    def cleanup_expired(self) -> None:
        if not self.is_available():
            return

        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM admin_sessions WHERE expires_at <= NOW()")
            deleted = cursor.rowcount
            self.db.commit()
            if deleted:
                logger.info("[ADMIN-SESSION] Cleaned up %s expired sessions", deleted)
        except Exception as e:
            self.db.rollback()
            logger.error(f"[ADMIN-SESSION] Failed to cleanup sessions: {e}", exc_info=True)
        finally:
            cursor.close()

