"""API endpoints for user's try-on history."""

from flask import Blueprint, jsonify, request

from backend.auth import get_current_user, token_required
from backend.logger import get_logger
from backend.utils.db_helpers import get_db_connection
from backend.repositories.generation_repository import GenerationRepository

logger = get_logger(__name__)

user_tryons_bp = Blueprint("user_tryons", __name__)


@user_tryons_bp.route("/api/user/tryons", methods=["GET"])
@token_required
def get_user_tryons():
    """
    Get user's try-on history.

    Query params:
        limit: Max results (default 50)
        offset: Pagination offset (default 0)

    Returns:
        JSON with user's generations
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        user_id = user.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid user"}), 401

        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)

        # Cap limits for safety
        limit = min(limit, 100)
        offset = max(offset, 0)

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database not available"}), 503

        try:
            cursor = conn.cursor()

            # Get generations with R2 URLs
            cursor.execute(
                """
                SELECT id, category, person_image_url, garment_image_url,
                       result_image_url, result_r2_url, thumbnail_url,
                       title, is_favorite, status, created_at, updated_at
                FROM generations
                WHERE user_id = %s AND status = 'completed'
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )

            rows = cursor.fetchall()

            # Get total count
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM generations
                WHERE user_id = %s AND status = 'completed'
                """,
                (user_id,),
            )
            total = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            tryons = []
            for row in rows:
                tryon = {
                    "id": row[0],
                    "category": row[1],
                    "person_image": row[2],
                    "garment_image": row[3],
                    "result_url": row[5] if row[5] else row[4],  # Prefer R2 URL
                    "thumbnail_url": row[6],
                    "title": row[7],
                    "is_favorite": row[8] or False,
                    "status": row[9],
                    "created_at": row[10].isoformat() if row[10] else None,
                    "updated_at": row[11].isoformat() if row[11] else None,
                }
                tryons.append(tryon)

            return jsonify({
                "success": True,
                "tryons": tryons,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(tryons)) < total,
            })

        except Exception as e:
            if conn:
                conn.close()
            logger.error(f"Error fetching user tryons: {e}", exc_info=True)
            return jsonify({"error": "Failed to fetch tryons"}), 500

    except Exception as e:
        logger.error(f"Error in get_user_tryons: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@user_tryons_bp.route("/api/user/tryons/<int:tryon_id>/favorite", methods=["POST"])
@token_required
def toggle_favorite(tryon_id):
    """
    Toggle favorite status for a try-on.

    Body:
        is_favorite: bool

    Returns:
        JSON with success status
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        user_id = user.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid user"}), 401

        data = request.get_json() or {}
        is_favorite = data.get("is_favorite", True)

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database not available"}), 503

        try:
            repo = GenerationRepository(conn)
            success = repo.set_favorite(tryon_id, user_id, is_favorite)
            conn.close()

            if success:
                return jsonify({
                    "success": True,
                    "is_favorite": is_favorite,
                })
            else:
                return jsonify({"error": "Try-on not found or not owned by user"}), 404

        except Exception as e:
            if conn:
                conn.close()
            logger.error(f"Error toggling favorite: {e}", exc_info=True)
            return jsonify({"error": "Failed to update favorite"}), 500

    except Exception as e:
        logger.error(f"Error in toggle_favorite: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@user_tryons_bp.route("/api/user/tryons/<int:tryon_id>/title", methods=["PUT"])
@token_required
def update_title(tryon_id):
    """
    Update title for a try-on.

    Body:
        title: string

    Returns:
        JSON with success status
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        user_id = user.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid user"}), 401

        data = request.get_json() or {}
        title = data.get("title", "").strip()

        if not title:
            return jsonify({"error": "Title is required"}), 400

        if len(title) > 255:
            return jsonify({"error": "Title too long (max 255 characters)"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database not available"}), 503

        try:
            repo = GenerationRepository(conn)
            success = repo.set_title(tryon_id, user_id, title)
            conn.close()

            if success:
                return jsonify({
                    "success": True,
                    "title": title,
                })
            else:
                return jsonify({"error": "Try-on not found or not owned by user"}), 404

        except Exception as e:
            if conn:
                conn.close()
            logger.error(f"Error updating title: {e}", exc_info=True)
            return jsonify({"error": "Failed to update title"}), 500

    except Exception as e:
        logger.error(f"Error in update_title: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@user_tryons_bp.route("/api/user/tryons/stats", methods=["GET"])
@token_required
def get_user_stats():
    """
    Get user's try-on statistics.

    Returns:
        JSON with stats: total, favorites, by_category
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        user_id = user.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid user"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database not available"}), 503

        try:
            cursor = conn.cursor()

            # Total completed generations
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM generations
                WHERE user_id = %s AND status = 'completed'
                """,
                (user_id,),
            )
            total = cursor.fetchone()[0]

            # Favorites count
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM generations
                WHERE user_id = %s AND status = 'completed' AND is_favorite = TRUE
                """,
                (user_id,),
            )
            favorites = cursor.fetchone()[0]

            # By category
            cursor.execute(
                """
                SELECT category, COUNT(*)
                FROM generations
                WHERE user_id = %s AND status = 'completed'
                GROUP BY category
                """,
                (user_id,),
            )
            by_category = {row[0]: row[1] for row in cursor.fetchall()}

            # Total R2 storage used
            cursor.execute(
                """
                SELECT COALESCE(SUM(r2_upload_size), 0)
                FROM generations
                WHERE user_id = %s AND r2_upload_size IS NOT NULL
                """,
                (user_id,),
            )
            storage_bytes = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "stats": {
                    "total": total,
                    "favorites": favorites,
                    "by_category": by_category,
                    "storage_used_bytes": storage_bytes,
                    "storage_used_mb": round(storage_bytes / (1024 * 1024), 2),
                },
            })

        except Exception as e:
            if conn:
                conn.close()
            logger.error(f"Error fetching user stats: {e}", exc_info=True)
            return jsonify({"error": "Failed to fetch stats"}), 500

    except Exception as e:
        logger.error(f"Error in get_user_stats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
