"""
Admin Service - Business logic for administrative operations.

Responsibilities:
- Dashboard statistics aggregation
- User management (role changes, premium toggling)
- Feedback moderation
- Audit logging

Security:
- All methods assume caller is already authorized (admin role checked by decorator)
- Input validation via Pydantic schemas
- Audit trail for all mutations
"""

from typing import Dict, List, Optional

from backend.logger import get_logger

logger = get_logger(__name__)


class AdminService:
    """Service for administrative operations."""

    def __init__(
        self,
        user_repository=None,
        feedback_repository=None,
        generation_repository=None,
        db_connection=None,
    ):
        """
        Initialize admin service.

        Args:
            user_repository: UserRepository instance
            feedback_repository: FeedbackRepository instance
            generation_repository: GenerationRepository instance
            db_connection: Database connection for audit logging
        """
        self.user_repository = user_repository
        self.feedback_repository = feedback_repository
        self.generation_repository = generation_repository
        self.db = db_connection
        self.logger = get_logger(__name__)

    def is_available(self) -> bool:
        """Check if admin service is available."""
        return self.user_repository is not None and self.db is not None

    # ============================================================
    # Dashboard & Statistics
    # ============================================================

    def get_summary(self) -> Dict:
        """
        Get admin dashboard summary statistics.

        Returns:
            Dictionary with key metrics:
            {
                'users_total': int,
                'premium_total': int,
                'generations_today': int,
                'feedback_pending': int,
                'oauth_enabled': bool
            }
        """
        if not self.is_available():
            raise ValueError("Admin service not available")

        try:
            from backend.utils.db_helpers import db_transaction

            # Count total users
            with db_transaction(self.db) as cursor:
                cursor.execute("SELECT COUNT(*) FROM users")
                users_total = cursor.fetchone()[0]

            # Count premium users
            with db_transaction(self.db) as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE is_premium = TRUE AND (premium_until IS NULL OR premium_until > NOW())"
                )
                premium_total = cursor.fetchone()[0]

            # Count generations today (using DATE() to handle timezone correctly)
            generations_today = 0
            try:
                with db_transaction(self.db) as cursor:
                    # Use DATE(created_at) = CURRENT_DATE for better timezone handling
                    cursor.execute(
                        "SELECT COUNT(*) FROM generations WHERE DATE(created_at) = CURRENT_DATE"
                    )
                    generations_today = cursor.fetchone()[0]
            except Exception as e:
                # If generations table doesn't exist or query fails, log and continue
                self.logger.warning(f"[ADMIN] Failed to count generations today: {e}")
                generations_today = 0

            # Count pending feedback (assuming status field exists)
            feedback_pending = 0
            try:
                with db_transaction(self.db) as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM feedback WHERE status = 'pending' OR status IS NULL"
                    )
                    feedback_pending = cursor.fetchone()[0]
            except Exception as e:
                # If status column doesn't exist or table doesn't exist, return 0
                self.logger.debug(f"[ADMIN] Failed to count pending feedback: {e}")
                feedback_pending = 0

            self.logger.info(
                f"[ADMIN] Dashboard summary: users={users_total}, premium={premium_total}, "
                f"generations_today={generations_today}, feedback_pending={feedback_pending}"
            )

            return {
                "users_total": users_total,
                "premium_total": premium_total,
                "generations_today": generations_today,
                "feedback_pending": feedback_pending,
                "oauth_enabled": True,  # From config, will wire later
            }

        except Exception as e:
            self.logger.error(f"[ADMIN] Failed to get summary: {e}", exc_info=True)
            raise

    # ============================================================
    # User Management
    # ============================================================

    def get_users(
        self, search: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> Dict:
        """
        Get paginated list of users with search.

        Args:
            search: Optional search query (email or name)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with users and pagination:
            {
                'users': [...],
                'total': int,
                'page': int,
                'page_size': int,
                'total_pages': int
            }
        """
        if not self.is_available():
            raise ValueError("Admin service not available")

        try:
            cursor = self.db.cursor()
            offset = (page - 1) * page_size

            # Build query
            if search:
                search_pattern = f"%{search}%"
                count_query = "SELECT COUNT(*) FROM users WHERE email ILIKE %s OR full_name ILIKE %s"
                data_query = """
                    SELECT
                        u.id, u.email, u.full_name, u.is_premium, u.provider,
                        u.role, u.created_at, u.last_login,
                        (SELECT COUNT(*) FROM generations WHERE user_id = u.id) as generations_count
                    FROM users u
                    WHERE u.email ILIKE %s OR u.full_name ILIKE %s
                    ORDER BY u.created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(count_query, (search_pattern, search_pattern))
                total = cursor.fetchone()[0]
                cursor.execute(
                    data_query, (search_pattern, search_pattern, page_size, offset)
                )
            else:
                count_query = "SELECT COUNT(*) FROM users"
                data_query = """
                    SELECT
                        u.id, u.email, u.full_name, u.is_premium, u.provider,
                        u.role, u.created_at, u.last_login,
                        (SELECT COUNT(*) FROM generations WHERE user_id = u.id) as generations_count
                    FROM users u
                    ORDER BY u.created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(count_query)
                total = cursor.fetchone()[0]
                cursor.execute(data_query, (page_size, offset))

            rows = cursor.fetchall()
            cursor.close()

            users = []
            for row in rows:
                users.append(
                    {
                        "id": row[0],
                        "email": row[1],
                        "full_name": row[2],
                        "is_premium": row[3],
                        "provider": row[4],
                        "role": row[5],
                        "created_at": row[6].isoformat() if row[6] else None,
                        "last_login": row[7].isoformat() if row[7] else None,
                        "generations_count": row[8] if len(row) > 8 else 0,
                    }
                )

            total_pages = (total + page_size - 1) // page_size

            self.logger.info(
                f"[ADMIN] Users list requested: page={page}, search={search}"
            )

            return {
                "users": users,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        except Exception as e:
            self.logger.error(f"[ADMIN] Failed to get users: {e}", exc_info=True)
            raise

    def change_user_role(
        self, user_id: int, new_role: str, admin_id: int, ip_address: str = None
    ) -> Dict:
        """
        Change user role (user <-> admin).

        Args:
            user_id: Target user ID
            new_role: New role ('user' or 'admin')
            admin_id: ID of admin performing action
            ip_address: IP address of admin

        Returns:
            Updated user dictionary

        Raises:
            ValueError: If role is invalid or user not found
        """
        if not self.is_available():
            raise ValueError("Admin service not available")

        if new_role not in ["user", "admin"]:
            raise ValueError("Invalid role. Must be 'user' or 'admin'")

        try:
            cursor = self.db.cursor()

            # Get current role
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"User {user_id} not found")

            old_role = row[0]

            # Update role
            cursor.execute(
                "UPDATE users SET role = %s WHERE id = %s", (new_role, user_id)
            )

            # Log audit
            self._log_audit(
                cursor,
                admin_id=admin_id,
                action="change_role",
                target_type="user",
                target_id=user_id,
                payload={"old_role": old_role, "new_role": new_role},
                ip_address=ip_address,
            )

            self.db.commit()
            cursor.close()

            self.logger.info(
                f"[ADMIN] User {user_id} role changed: {old_role} → {new_role} by admin {admin_id}"
            )

            return {"user_id": user_id, "old_role": old_role, "new_role": new_role}

        except Exception as e:
            self.db.rollback()
            self.logger.error(f"[ADMIN] Failed to change role: {e}", exc_info=True)
            raise

    def toggle_premium(
        self,
        user_id: int,
        enable: bool,
        days: int = 30,
        admin_id: int = None,
        ip_address: str = None,
    ) -> Dict:
        """
        Toggle premium status for user.

        Args:
            user_id: Target user ID
            enable: True to grant premium, False to revoke
            days: Number of days to grant premium (default: 30)
            admin_id: ID of admin performing action
            ip_address: IP address of admin

        Returns:
            Updated user dictionary
        """
        if not self.is_available():
            raise ValueError("Admin service not available")

        try:
            cursor = self.db.cursor()

            if enable:
                # Grant premium
                cursor.execute(
                    """
                    UPDATE users
                    SET is_premium = TRUE, premium_until = NOW() + INTERVAL '%s days'
                    WHERE id = %s
                    RETURNING is_premium, premium_until
                    """,
                    (days, user_id),
                )
            else:
                # Revoke premium
                cursor.execute(
                    """
                    UPDATE users
                    SET is_premium = FALSE, premium_until = NULL
                    WHERE id = %s
                    RETURNING is_premium, premium_until
                    """,
                    (user_id,),
                )

            result = cursor.fetchone()
            if not result:
                raise ValueError(f"User {user_id} not found")

            # Log audit
            self._log_audit(
                cursor,
                admin_id=admin_id,
                action="toggle_premium",
                target_type="user",
                target_id=user_id,
                payload={"enable": enable, "days": days if enable else None},
                ip_address=ip_address,
            )

            self.db.commit()
            cursor.close()

            self.logger.info(
                f"[ADMIN] User {user_id} premium {'granted' if enable else 'revoked'} by admin {admin_id}"
            )

            return {
                "user_id": user_id,
                "is_premium": result[0],
                "premium_until": result[1].isoformat() if result[1] else None,
            }

        except Exception as e:
            self.db.rollback()
            self.logger.error(
                f"[ADMIN] Failed to toggle premium: {e}", exc_info=True
            )
            raise

    def reset_user_limit(
        self, user_id: int, admin_id: int, ip_address: str = None
    ) -> Dict:
        """
        Reset generation limit for user.

        Since limits are now based on counting records in generations table
        (weekly for free users, monthly for premium), this function deletes
        the user's generation records for the current period.

        Args:
            user_id: Target user ID
            admin_id: ID of admin performing action
            ip_address: IP address of admin

        Returns:
            Success confirmation with number of records deleted
        """
        if not self.is_available():
            raise ValueError("Admin service not available")

        try:
            cursor = self.db.cursor()

            # Check if user is premium to determine period
            cursor.execute(
                "SELECT is_premium FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if not user:
                raise ValueError(f"User {user_id} not found")

            is_premium = user[0]

            # Delete generations for current period
            if is_premium:
                # Premium: delete this month's generations
                cursor.execute(
                    """
                    DELETE FROM generations
                    WHERE user_id = %s
                    AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
                    AND created_at < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                    """,
                    (user_id,),
                )
            else:
                # Free: delete this week's generations
                cursor.execute(
                    """
                    DELETE FROM generations
                    WHERE user_id = %s
                    AND created_at >= DATE_TRUNC('week', CURRENT_DATE)
                    AND created_at < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week'
                    """,
                    (user_id,),
                )

            deleted_count = cursor.rowcount

            # Log audit
            self._log_audit(
                cursor,
                admin_id=admin_id,
                action="reset_limit",
                target_type="user",
                target_id=user_id,
                payload={
                    "deleted_generations": deleted_count,
                    "period": "month" if is_premium else "week"
                },
                ip_address=ip_address,
            )

            self.db.commit()
            cursor.close()

            self.logger.info(
                f"[ADMIN] User {user_id} limit reset by admin {admin_id}, deleted {deleted_count} generations"
            )

            return {"user_id": user_id, "limit_reset": True, "deleted_count": deleted_count}

        except Exception as e:
            self.db.rollback()
            self.logger.error(
                f"[ADMIN] Failed to reset limit: {e}", exc_info=True
            )
            raise

    # ============================================================
    # Feedback Management
    # ============================================================

    def get_feedback(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get feedback/support requests.

        Args:
            status: Optional filter by status

        Returns:
            List of feedback items
        """
        if not self.feedback_repository:
            return []

        try:
            cursor = self.db.cursor()

            if status:
                query = """
                    SELECT id, email, message, category, created_at, status
                    FROM feedback
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT 100
                """
                cursor.execute(query, (status,))
            else:
                query = """
                    SELECT id, email, message, category, created_at, status
                    FROM feedback
                    ORDER BY created_at DESC
                    LIMIT 100
                """
                cursor.execute(query)

            rows = cursor.fetchall()
            cursor.close()

            feedback_list = []
            for row in rows:
                feedback_list.append(
                    {
                        "id": row[0],
                        "email": row[1],
                        "message": row[2],
                        "category": row[3] if len(row) > 3 else None,
                        "created_at": row[4].isoformat() if row[4] else None,
                        "status": row[5] if len(row) > 5 else None,
                    }
                )

            self.logger.info(f"[ADMIN] Feedback list requested: status={status}")

            return feedback_list

        except Exception as e:
            self.logger.error(f"[ADMIN] Failed to get feedback: {e}", exc_info=True)
            # Return empty list instead of crashing
            return []

    # ============================================================
    # Audit Logging
    # ============================================================

    def get_audit_logs(self, limit: int = 20) -> List[Dict]:
        """
        Get recent audit logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of audit log entries
        """
        if not self.is_available():
            raise ValueError("Admin service not available")

        try:
            cursor = self.db.cursor()

            query = """
                SELECT
                    a.id, a.admin_id, u.email as admin_email, a.action,
                    a.target_type, a.target_id, a.payload, a.ip_address, a.created_at
                FROM admin_audit_logs a
                LEFT JOIN users u ON a.admin_id = u.id
                ORDER BY a.created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))

            rows = cursor.fetchall()
            cursor.close()

            logs = []
            for row in rows:
                logs.append(
                    {
                        "id": row[0],
                        "admin_id": row[1],
                        "admin_email": row[2],
                        "action": row[3],
                        "target_type": row[4],
                        "target_id": row[5],
                        "payload": row[6],
                        "ip_address": row[7],
                        "created_at": row[8].isoformat() if row[8] else None,
                    }
                )

            self.logger.info(f"[ADMIN] Audit logs requested: limit={limit}")

            return logs

        except Exception as e:
            self.logger.error(f"[ADMIN] Failed to get audit logs: {e}", exc_info=True)
            # Return empty list if table doesn't exist yet
            return []

    def _log_audit(
        self,
        cursor,
        admin_id: int,
        action: str,
        target_type: str,
        target_id: Optional[int],
        payload: Dict,
        ip_address: Optional[str] = None,
    ):
        """
        Internal method to log admin action.

        Args:
            cursor: Database cursor
            admin_id: ID of admin performing action
            action: Action type
            target_type: Type of target entity
            target_id: ID of target entity
            payload: Additional action details (JSON)
            ip_address: IP address of admin
        """
        try:
            import json

            cursor.execute(
                """
                INSERT INTO admin_audit_logs
                (admin_id, action, target_type, target_id, payload, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    admin_id,
                    action,
                    target_type,
                    target_id,
                    json.dumps(payload),
                    ip_address,
                ),
            )
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            self.logger.warning(f"[ADMIN] Failed to write audit log: {e}")
