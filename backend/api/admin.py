"""
Admin API endpoints protected by server-side admin sessions.
"""

from functools import wraps
from typing import Optional

from flask import Blueprint, jsonify, make_response, request
from pydantic import BaseModel, Field, ValidationError, field_validator

from backend.auth import ADMIN_SESSION_COOKIE, clear_admin_session_cookie
from backend.logger import get_logger
from backend.services.admin_service import AdminService
from backend.services.admin_session_service import AdminSessionService

logger = get_logger(__name__)


# ============================================================
# Pydantic Schemas for Request Validation
# ============================================================


class ChangeRoleRequest(BaseModel):
    """Request schema for changing user role."""

    role: str = Field(..., description="New role ('user' or 'admin')")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate role value."""
        if v not in ["user", "admin"]:
            raise ValueError("Role must be 'user' or 'admin'")
        return v


class TogglePremiumRequest(BaseModel):
    """Request schema for toggling premium status."""

    enable: bool = Field(..., description="True to grant, False to revoke")
    days: int = Field(30, description="Days to grant premium", ge=1, le=365)


# ============================================================
# Blueprint Factory
# ============================================================


def create_admin_blueprint(
    admin_service: AdminService, admin_session_service: Optional[AdminSessionService] = None
) -> Blueprint:
    """
    Create admin API blueprint.

    Args:
        admin_service: AdminService instance

    Returns:
        Configured Blueprint with admin routes
    """
    admin_bp = Blueprint("admin", __name__)

    def require_session(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not admin_session_service or not admin_session_service.is_available():
                return jsonify({"error": "Admin session service unavailable"}), 503

            session_id = request.cookies.get(ADMIN_SESSION_COOKIE)
            if not session_id:
                return jsonify({"error": "Admin session required"}), 401

            admin_user = admin_session_service.get_session_user(session_id)
            if not admin_user:
                response = make_response(jsonify({"error": "Admin session expired"}), 401)
                clear_admin_session_cookie(response)
                return response

            return f(admin_user, *args, **kwargs)

        return wrapper

    @admin_bp.route("/api/admin/summary", methods=["GET"])
    @require_session
    def get_summary(current_user):
        """
        Get dashboard summary statistics.

        Requires: admin role

        Returns:
            {
                "users_total": int,
                "premium_total": int,
                "generations_today": int,
                "feedback_pending": int,
                "oauth_enabled": bool
            }
        """
        try:
            if not admin_service.is_available():
                return jsonify({"error": "Admin service not available"}), 503

            summary = admin_service.get_summary()

            logger.info(
                f"[ADMIN-API] Summary requested by admin {current_user['id']}"
            )

            return jsonify({"success": True, "data": summary}), 200

        except Exception as e:
            logger.error(f"[ADMIN-API] Summary failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/users", methods=["GET"])
    @require_session
    def get_users(current_user):
        """
        Get paginated list of users.

        Requires: admin role

        Query params:
            search: Optional search query
            page: Page number (default: 1)
            page_size: Items per page (default: 20, max: 100)

        Returns:
            {
                "users": [...],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        """
        try:
            if not admin_service.is_available():
                return jsonify({"error": "Admin service not available"}), 503

            # Parse query params
            search = request.args.get("search")
            page = int(request.args.get("page", 1))
            page_size = min(int(request.args.get("page_size", 20)), 100)

            if page < 1:
                return jsonify({"error": "Page must be >= 1"}), 400
            if page_size < 1:
                return jsonify({"error": "Page size must be >= 1"}), 400

            result = admin_service.get_users(
                search=search, page=page, page_size=page_size
            )

            logger.info(
                f"[ADMIN-API] Users list requested by admin {current_user['id']}: "
                f"page={page}, search={search}"
            )

            return jsonify({"success": True, "data": result}), 200

        except ValueError as e:
            logger.warning(f"[ADMIN-API] Invalid request: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(f"[ADMIN-API] Get users failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/users/<int:user_id>/role", methods=["PATCH"])
    @require_session
    def change_user_role(current_user, user_id):
        """
        Change user role.

        Requires: admin role

        Path params:
            user_id: Target user ID

        Body:
            {
                "role": "admin" | "user"
            }

        Returns:
            {
                "user_id": int,
                "old_role": str,
                "new_role": str
            }
        """
        try:
            if not admin_service.is_available():
                return jsonify({"error": "Admin service not available"}), 503

            # Validate request body
            try:
                data = ChangeRoleRequest(**request.get_json())
            except ValidationError as e:
                return jsonify({"error": "Validation failed", "details": e.errors()}), 400

            # Get client IP
            ip_address = request.remote_addr

            # Perform action
            result = admin_service.change_user_role(
                user_id=user_id,
                new_role=data.role,
                admin_id=current_user["id"],
                ip_address=ip_address,
            )

            logger.info(
                f"[ADMIN-API] User {user_id} role changed to {data.role} by admin {current_user['id']}"
            )

            return jsonify(result), 200

        except ValueError as e:
            logger.warning(f"[ADMIN-API] Invalid request: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(
                f"[ADMIN-API] Change role failed: {e}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/users/<int:user_id>/premium", methods=["PATCH"])
    @require_session
    def toggle_premium(current_user, user_id):
        """
        Toggle premium status for user.

        Requires: admin role

        Path params:
            user_id: Target user ID

        Body:
            {
                "enable": bool,
                "days": int  // optional, default 30
            }

        Returns:
            {
                "user_id": int,
                "is_premium": bool,
                "premium_until": str | null
            }
        """
        try:
            if not admin_service.is_available():
                return jsonify({"error": "Admin service not available"}), 503

            # Validate request body
            try:
                data = TogglePremiumRequest(**request.get_json())
            except ValidationError as e:
                return jsonify({"error": "Validation failed", "details": e.errors()}), 400

            # Get client IP
            ip_address = request.remote_addr

            # Perform action
            result = admin_service.toggle_premium(
                user_id=user_id,
                enable=data.enable,
                days=data.days,
                admin_id=current_user["id"],
                ip_address=ip_address,
            )

            logger.info(
                f"[ADMIN-API] User {user_id} premium {'granted' if data.enable else 'revoked'} "
                f"by admin {current_user['id']}"
            )

            return jsonify(result), 200

        except ValueError as e:
            logger.warning(f"[ADMIN-API] Invalid request: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(
                f"[ADMIN-API] Toggle premium failed: {e}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
    @require_session
    def delete_user(current_user, user_id):
        """
        Delete a user from the system.

        Requires: admin role

        Path params:
            user_id: Target user ID

        Returns:
            {
                "user_id": int,
                "deleted": bool
            }
        """
        try:
            if not admin_service.is_available():
                return jsonify({"error": "Admin service not available"}), 503

            # Get client IP
            ip_address = request.remote_addr

            # Perform action
            result = admin_service.delete_user(
                user_id=user_id, admin_id=current_user["id"], ip_address=ip_address
            )

            logger.info(
                f"[ADMIN-API] User {user_id} deleted by admin {current_user['id']}"
            )

            return jsonify(result), 200

        except ValueError as e:
            logger.warning(f"[ADMIN-API] Invalid request: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(
                f"[ADMIN-API] Delete user failed: {e}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/users/<int:user_id>/reset-limit", methods=["POST"])
    @require_session
    def reset_user_limit(current_user, user_id):
        """
        Reset daily generation limit for user.

        Requires: admin role

        Path params:
            user_id: Target user ID

        Returns:
            {
                "user_id": int,
                "limit_reset": bool
            }
        """
        try:
            if not admin_service.is_available():
                return jsonify({"error": "Admin service not available"}), 503

            # Get client IP
            ip_address = request.remote_addr

            # Perform action
            result = admin_service.reset_user_limit(
                user_id=user_id, admin_id=current_user["id"], ip_address=ip_address
            )

            logger.info(
                f"[ADMIN-API] User {user_id} limit reset by admin {current_user['id']}"
            )

            return jsonify(result), 200

        except ValueError as e:
            logger.warning(f"[ADMIN-API] Invalid request: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(
                f"[ADMIN-API] Reset limit failed: {e}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/feedback", methods=["GET"])
    @require_session
    def get_feedback(current_user):
        """
        Get feedback/support requests.

        Requires: admin role

        Query params:
            status: Optional filter by status

        Returns:
            [
                {
                    "id": int,
                    "email": str,
                    "message": str,
                    "category": str | null,
                    "created_at": str,
                    "status": str | null
                },
                ...
            ]
        """
        try:
            status = request.args.get("status")

            feedback_list = admin_service.get_feedback(status=status)

            logger.info(
                f"[ADMIN-API] Feedback list requested by admin {current_user['id']}: "
                f"status={status}"
            )

            return jsonify({"success": True, "data": feedback_list}), 200

        except Exception as e:
            logger.error(
                f"[ADMIN-API] Get feedback failed: {e}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/audit", methods=["GET"])
    @require_session
    def get_audit_logs(current_user):
        """
        Get recent audit logs.

        Requires: admin role

        Query params:
            limit: Max records to return (default: 20, max: 100)

        Returns:
            [
                {
                    "id": int,
                    "admin_id": int,
                    "admin_email": str,
                    "action": str,
                    "target_type": str,
                    "target_id": int | null,
                    "payload": object,
                    "ip_address": str | null,
                    "created_at": str
                },
                ...
            ]
        """
        try:
            limit = min(int(request.args.get("limit", 20)), 100)

            if limit < 1:
                return jsonify({"error": "Limit must be >= 1"}), 400

            logs = admin_service.get_audit_logs(limit=limit)

            logger.info(
                f"[ADMIN-API] Audit logs requested by admin {current_user['id']}: "
                f"limit={limit}"
            )

            return jsonify({"success": True, "data": logs}), 200

        except ValueError as e:
            logger.warning(f"[ADMIN-API] Invalid request: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            logger.error(
                f"[ADMIN-API] Get audit logs failed: {e}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500

    return admin_bp
