"""Admin API endpoints."""

from flask import Blueprint, jsonify, request

from backend.logger import get_logger
from backend.repositories.generation_repository import GenerationRepository

logger = get_logger(__name__)

# Blueprint will be created by factory function
admin_bp = Blueprint("admin", __name__)


def create_admin_blueprint(
    generation_repo: GenerationRepository, user_repository=None, db_connection=None
) -> Blueprint:
    """
    Factory function to create admin blueprint with injected dependencies.

    Args:
        generation_repo: GenerationRepository instance
        user_repository: Optional UserRepository for user management
        db_connection: Optional psycopg2 connection for direct queries

    Returns:
        Configured Blueprint
    """

    @admin_bp.route("/api/admin/users", methods=["GET"])
    def admin_get_users():
        """
        Get all users (admin only).

        Response:
        {
            "users": [
                {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "is_premium": false,
                    "provider": "email",
                    "role": "user",
                    "created_at": "2025-01-15T12:00:00",
                    "generation_count": 5
                }
            ],
            "total": 1
        }
        """
        if not user_repository or not db_connection:
            return jsonify({"error": "Admin features not available"}), 503

        try:
            cursor = db_connection.cursor()

            cursor.execute(
                """
                SELECT u.id, u.email, u.full_name, u.is_premium, u.provider, u.role, u.created_at,
                       COUNT(g.id) as generation_count
                FROM users u
                LEFT JOIN generations g ON u.id = g.user_id
                GROUP BY u.id, u.email, u.full_name, u.is_premium, u.provider, u.role, u.created_at
                ORDER BY u.created_at DESC
                """
            )

            users_data = cursor.fetchall()
            cursor.close()

            users = []
            for user in users_data:
                users.append(
                    {
                        "id": user[0],
                        "email": user[1],
                        "full_name": user[2],
                        "is_premium": user[3],
                        "provider": user[4],
                        "role": user[5],
                        "created_at": user[6].isoformat() if user[6] else None,
                        "generation_count": user[7],
                    }
                )

            return jsonify({"users": users, "total": len(users)}), 200

        except Exception as e:
            logger.error(f"Admin get users error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/users/<int:user_id>/premium", methods=["POST"])
    def admin_toggle_premium(user_id: int):
        """
        Toggle user's premium status (admin only).

        Response:
        {
            "success": true,
            "user_id": 1,
            "is_premium": true
        }
        """
        if not db_connection:
            return jsonify({"error": "Admin features not available"}), 503

        try:
            cursor = db_connection.cursor()

            # Toggle premium status
            cursor.execute(
                """
                UPDATE users
                SET is_premium = NOT is_premium,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING is_premium
                """,
                (user_id,),
            )

            result = cursor.fetchone()

            if not result:
                cursor.close()
                return jsonify({"error": "User not found"}), 404

            is_premium = result[0]

            db_connection.commit()
            cursor.close()

            logger.info(f"Toggled premium status for user {user_id}: is_premium={is_premium}")

            return jsonify({"success": True, "user_id": user_id, "is_premium": is_premium}), 200

        except Exception as e:
            if db_connection:
                db_connection.rollback()
            logger.error(f"Admin toggle premium error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/generations", methods=["GET"])
    def admin_get_all_generations():
        """
        Get all generations with user info (admin only).

        Query params:
        - user_id: Filter by user ID (optional)
        - limit: Maximum records (default: 100)
        - offset: Skip records (default: 0)

        Response:
        {
            "generations": [
                {
                    "id": 1,
                    "user_id": 1,
                    "user_email": "user@example.com",
                    "user_name": "John Doe",
                    "category": "auto",
                    "status": "completed",
                    "person_image_url": "person.jpg",
                    "garment_image_url": "garment.jpg",
                    "result_image_url": "result.jpg",
                    "created_at": "2025-01-15T12:00:00"
                }
            ],
            "total": 1
        }
        """
        if not db_connection:
            return jsonify({"error": "Admin features not available"}), 503

        try:
            # Get query parameters
            user_id = request.args.get("user_id", type=int)
            limit = request.args.get("limit", 100, type=int)
            offset = request.args.get("offset", 0, type=int)

            cursor = db_connection.cursor()

            if user_id:
                # Get generations for specific user
                cursor.execute(
                    """
                    SELECT g.id, g.user_id, u.email, u.full_name, g.category, g.status,
                           g.person_image_url, g.garment_image_url, g.result_image_url,
                           g.created_at
                    FROM generations g
                    JOIN users u ON g.user_id = u.id
                    WHERE g.user_id = %s
                    ORDER BY g.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
            else:
                # Get all generations
                cursor.execute(
                    """
                    SELECT g.id, g.user_id, u.email, u.full_name, g.category, g.status,
                           g.person_image_url, g.garment_image_url, g.result_image_url,
                           g.created_at
                    FROM generations g
                    LEFT JOIN users u ON g.user_id = u.id
                    ORDER BY g.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )

            generations_data = cursor.fetchall()
            cursor.close()

            generations = []
            for gen in generations_data:
                generations.append(
                    {
                        "id": gen[0],
                        "user_id": gen[1],
                        "user_email": gen[2],
                        "user_name": gen[3],
                        "category": gen[4],
                        "status": gen[5],
                        "person_image_url": gen[6],
                        "garment_image_url": gen[7],
                        "result_image_url": gen[8],
                        "created_at": gen[9].isoformat() if gen[9] else None,
                    }
                )

            return jsonify({"generations": generations, "total": len(generations)}), 200

        except Exception as e:
            logger.error(f"Admin get generations error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @admin_bp.route("/api/admin/stats", methods=["GET"])
    def admin_get_stats():
        """
        Get admin statistics (admin only).

        Response:
        {
            "users": {
                "total": 100,
                "premium": 20,
                "free": 80,
                "admins": 2
            },
            "generations": {
                "total": 500,
                "today": 25,
                "by_category": [
                    {"category": "auto", "count": 300},
                    {"category": "tops", "count": 200}
                ]
            }
        }
        """
        if not db_connection:
            # Return stats from GenerationRepository only
            try:
                gen_stats = generation_repo.get_stats()
                return jsonify({"users": {}, "generations": gen_stats}), 200
            except Exception as e:
                logger.error(f"Admin get stats error: {e}", exc_info=True)
                return jsonify({"error": str(e)}), 500

        try:
            cursor = db_connection.cursor()

            # Get user stats
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")
            premium_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_users = cursor.fetchone()[0]

            # Get generation stats using repository
            gen_stats = generation_repo.get_stats()

            cursor.close()

            return (
                jsonify(
                    {
                        "users": {
                            "total": total_users,
                            "premium": premium_users,
                            "free": total_users - premium_users,
                            "admins": admin_users,
                        },
                        "generations": gen_stats,
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Admin get stats error: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    return admin_bp
