"""
Application factory for creating Flask app with dependency injection.

This module creates and configures the Flask application with all services,
repositories, and blueprints properly initialized and wired together.
"""

import hashlib
import os
from typing import Optional

import psycopg2
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.api.admin import create_admin_blueprint
from backend.api.auth import create_auth_blueprint
from backend.api.feedback import create_feedback_blueprint
from backend.api.fingerprint import create_fingerprint_blueprint
from backend.api.google_auth import create_google_auth_blueprint
from backend.api.static import create_static_blueprint
from backend.api.tryon import create_tryon_blueprint
from backend.api.upload import create_upload_blueprint
from backend.auth import AuthManager
from backend.clients.nanobanana_client import NanoBananaClient
from backend.clients.telegram_client import TelegramClient
from backend.config import Settings
from backend.logger import get_logger
from backend.repositories.device_limit_repository import DeviceLimitRepository
from backend.repositories.feedback_repository import FeedbackRepository
from backend.repositories.generation_repository import GenerationRepository
from backend.services.admin_service import AdminService
from backend.services.admin_session_service import AdminSessionService
from backend.services.auth_service import AuthService
from backend.services.device_fingerprint_service import DeviceFingerprintService
from backend.services.feedback_service import FeedbackService
from backend.services.google_auth_service import GoogleAuthService
from backend.services.image_service import ImageService
from backend.services.limit_service import LimitService
from backend.services.notification_service import NotificationService
from backend.services.tryon_service import TryonService
from backend.utils.file_helpers import start_cleanup_scheduler

logger = get_logger(__name__)


def create_app(config: Optional[Settings] = None) -> Flask:
    """
    Application factory function.

    Creates Flask app with all dependencies properly initialized and injected.

    Args:
        config: Optional Settings object (uses env vars if None)

    Returns:
        Configured Flask application
    """
    logger.info("=" * 60)
    logger.info("Creating Flask application with factory pattern...")

    # Load configuration
    if config is None:
        config = Settings()

    db_url_str = str(config.database_url) if config.database_url else None
    logger.info(f"Database URL: {db_url_str[:20] if db_url_str else 'NOT SET'}...")
    logger.info(f"NanoBanana API Key: {'SET' if config.nanobanana_api_key else 'NOT SET'}")
    logger.info(f"Telegram Bot Token: {'SET' if config.telegram_bot_token else 'NOT SET'}")

    # Create Flask app
    frontend_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    app = Flask(__name__, static_folder=frontend_folder, static_url_path="")

    # Store config in app
    app.config["SETTINGS"] = config
    app.config["SECRET_KEY"] = config.jwt_secret_key  # For Flask session management (Google OAuth)
    app.config["db_connection"] = None  # Will be set later after DB connection is established

    # Configure CORS
    # Note: supports_credentials=True requires specific origins (cannot use "*")
    allowed_origins = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://taptolook.net",
        "https://www.taptolook.net",
    ]

    CORS(
        app,
        resources={
            r"/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,  # CRITICAL: Allow cookies in CORS requests
            }
        },
    )

    # Configure rate limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per hour", "50 per minute"],
        storage_uri="memory://",
        strategy="fixed-window",
    )

    # Apply rate limiting to specific blueprints later
    app.config["LIMITER"] = limiter

    # Create folder structure
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    results_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    feedback_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback")

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(results_folder, exist_ok=True)
    os.makedirs(feedback_folder, exist_ok=True)

    logger.info(f"Upload folder: {upload_folder}")
    logger.info(f"Results folder: {results_folder}")
    logger.info(f"Feedback folder: {feedback_folder}")

    # Initialize database connection
    db_conn = None
    if config.database_url:
        try:
            db_conn = psycopg2.connect(str(config.database_url))
            app.config["db_connection"] = db_conn  # Store for require_admin decorator
            logger.info("[OK] Database connection established")
        except Exception as e:
            logger.error(f"[ERROR] Database connection failed: {e}")
            db_conn = None
    else:
        logger.warning("[SKIP] DATABASE_URL not set - database features disabled")

    # Initialize repositories
    device_limit_repo = DeviceLimitRepository(db_conn) if db_conn else None
    feedback_repo = FeedbackRepository(db_conn, feedback_folder)
    generation_repo = GenerationRepository(db_conn) if db_conn else None

    # Initialize AuthManager first (needed by UserRepository and GoogleAuthService)
    auth_manager = None
    if db_conn:
        try:
            auth_manager = AuthManager(db_connection=db_conn)
            logger.info("[OK] AuthManager initialized")
        except Exception as e:
            logger.warning(f"[SKIP] AuthManager not available: {e}")

    # Initialize user repository (optional, may have emoji issues on Windows)
    user_repository = None
    if db_conn and auth_manager:
        try:
            from backend.repositories.user_repository import UserRepository

            user_repository = UserRepository(auth_manager=auth_manager)
            logger.info("[OK] UserRepository initialized with AuthManager")
        except Exception as e:
            logger.warning(f"[SKIP] UserRepository not available: {e}")

    # Initialize clients
    nanobanana_client = NanoBananaClient(
        api_key=config.nanobanana_api_key or "", timeout=120
    )

    telegram_client = None
    if config.telegram_bot_token:
        telegram_client = TelegramClient(
            bot_token=config.telegram_bot_token, default_chat_id=config.telegram_chat_id
        )
        logger.info("[OK] TelegramClient initialized")
    else:
        logger.warning("[SKIP] Telegram not configured - notifications disabled")

    # Initialize services
    imgbb_key = os.getenv("IMGBB_API_KEY")  # Optional, not in Settings
    image_service = ImageService(upload_folder=upload_folder, imgbb_api_key=imgbb_key)

    limit_service = LimitService(
        device_limit_repo=device_limit_repo, user_repository=user_repository
    )

    notification_service = (
        NotificationService(telegram_client=telegram_client, feedback_repo=feedback_repo)
        if telegram_client
        else None
    )

    feedback_service = FeedbackService(
        feedback_repo=feedback_repo, notification_service=notification_service
    )

    auth_service = AuthService(user_repository=user_repository) if user_repository else None

    # Admin session service
    admin_session_service = AdminSessionService(db_conn) if db_conn else None
    if admin_session_service and admin_session_service.is_available():
        logger.info("[OK] AdminSessionService initialized")
    else:
        logger.info("[SKIP] AdminSessionService not available (no database connection)")

    app.config["ADMIN_SESSION_SERVICE"] = admin_session_service

    # Initialize Admin service
    admin_service = AdminService(
        user_repository=user_repository,
        feedback_repository=feedback_repo,
        generation_repository=generation_repo,
        db_connection=db_conn,
    ) if db_conn else None

    if admin_service and admin_service.is_available():
        logger.info("[OK] AdminService initialized")
    else:
        logger.info("[SKIP] AdminService not available (no database)")

    # Initialize Google OAuth service (uses auth_manager created earlier)
    google_auth_service = GoogleAuthService(settings=config, auth_manager=auth_manager)
    if google_auth_service.is_enabled():
        logger.info("[OK] GoogleAuthService initialized and enabled")
    else:
        logger.info("[SKIP] GoogleAuthService disabled (not configured or oauth_enabled=False)")

    if config.device_fingerprint_secret:
        fingerprint_secret = config.device_fingerprint_secret
    else:
        derived_secret = hashlib.sha256((config.jwt_secret_key + "|fingerprint").encode("utf-8")).hexdigest()
        fingerprint_secret = derived_secret
        os.environ.setdefault("DEVICE_FINGERPRINT_SECRET", derived_secret)
        logger.info("[INFO] DEVICE_FINGERPRINT_SECRET not set; derived from JWT secret")
    fingerprint_service = DeviceFingerprintService(secret=fingerprint_secret)

    tryon_service = TryonService(
        nanobanana_client=nanobanana_client,
        image_service=image_service,
        limit_service=limit_service,
        result_folder=results_folder,
        notification_service=notification_service,
        generation_repo=generation_repo,
    )

    logger.info("[OK] All services initialized")

    # Create and register blueprints
    logger.info("Registering blueprints...")

    # Tryon blueprint
    tryon_bp = create_tryon_blueprint(tryon_service, auth_service)
    app.register_blueprint(tryon_bp)
    logger.info("  - Tryon blueprint registered")

    # Upload blueprint
    upload_bp = create_upload_blueprint(image_service, upload_folder)
    app.register_blueprint(upload_bp)
    logger.info("  - Upload blueprint registered")

    # Fingerprint blueprint
    fingerprint_bp = create_fingerprint_blueprint(fingerprint_service)
    app.register_blueprint(fingerprint_bp)
    logger.info("  - Fingerprint blueprint registered")

    # Feedback blueprint
    feedback_bp = create_feedback_blueprint(feedback_service)
    app.register_blueprint(feedback_bp)
    logger.info("  - Feedback blueprint registered")

    # Auth blueprint
    if auth_service:
        auth_bp = create_auth_blueprint(auth_service, admin_session_service)
        app.register_blueprint(auth_bp)
        logger.info("  - Auth blueprint registered")
    else:
        logger.warning("  - Auth blueprint skipped (auth not available)")

    # Admin blueprint (requires admin role)
    if admin_service and admin_service.is_available():
        admin_bp = create_admin_blueprint(admin_service, admin_session_service)
        app.register_blueprint(admin_bp)
        logger.info("  - Admin blueprint registered")
    else:
        logger.warning("  - Admin blueprint skipped (admin service not available)")

    # Google OAuth blueprint (always register to return proper 503 when disabled)
    google_auth_bp = create_google_auth_blueprint(google_auth_service, admin_session_service)
    app.register_blueprint(google_auth_bp)
    if google_auth_service.is_enabled():
        logger.info("  - Google OAuth blueprint registered (OAuth enabled)")
    else:
        logger.info("  - Google OAuth blueprint registered (OAuth disabled - will return 503)")

    # Static files blueprint (must be last for SPA fallback)
    static_bp = create_static_blueprint(upload_folder, results_folder, frontend_folder)
    app.register_blueprint(static_bp)
    logger.info("  - Static blueprint registered")

    # Start background cleanup scheduler
    cleanup_folders = [upload_folder, results_folder]
    start_cleanup_scheduler(folders=cleanup_folders, interval_seconds=1800, max_age_seconds=3600)
    logger.info("[OK] File cleanup scheduler started (every 30 min, files older than 1 hour)")

    logger.info("=" * 60)
    logger.info("[SUCCESS] Application created successfully")
    logger.info("=" * 60)

    return app


def create_app_from_env() -> Flask:
    """
    Convenience function to create app using environment variables.

    Returns:
        Configured Flask application
    """
    return create_app(config=None)
