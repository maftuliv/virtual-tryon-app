"""
Pydantic-based configuration for the Virtual Try-On application.

Provides type-safe environment variable validation and sensible defaults.
"""

from typing import Optional

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All environment variables are validated at startup.
    Missing required variables will raise ValidationError.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"  # Ignore unknown env vars
    )

    # ==================== DATABASE CONFIGURATION (REQUIRED) ====================
    database_url: PostgresDsn = Field(
        ..., description="PostgreSQL connection string (postgresql://user:pass@host:port/db)"
    )

    # ==================== SECURITY CONFIGURATION (REQUIRED) ====================
    jwt_secret_key: str = Field(
        ..., min_length=32, description="JWT secret key for token signing (minimum 32 characters)"
    )

    # ==================== API CONFIGURATION ====================
    nanobanana_api_key: str = Field(..., description="Nano Banana API key for virtual try-on")

    fashn_api_key: Optional[str] = Field(
        default=None, description="FASHN API key (optional alternative to Nano Banana)"
    )

    huggingface_api_key: Optional[str] = Field(
        default=None,
        alias="HF_API_KEY",
        description="Hugging Face API key for person detection (also accepts HF_API_TOKEN)",
        validation_alias="HF_API_TOKEN",
    )

    # ==================== SECURITY ENHANCEMENTS ====================
    device_fingerprint_secret: Optional[str] = Field(
        default=None,
        alias="DEVICE_FINGERPRINT_SECRET",
        description="Secret pepper for device fingerprint hashing (defaults to JWT secret if unset)",
    )

    # ==================== GOOGLE OAUTH CONFIGURATION (OPTIONAL) ====================
    google_oauth_enabled: bool = Field(
        default=False,
        description="Enable Google OAuth 2.0 authentication"
    )

    google_client_id: Optional[str] = Field(
        default=None,
        description="Google OAuth 2.0 Client ID (from Google Cloud Console)",
    )

    google_client_secret: Optional[str] = Field(
        default=None,
        description="Google OAuth 2.0 Client Secret (from Google Cloud Console)",
    )

    google_redirect_uri: Optional[str] = Field(
        default=None,
        description="Google OAuth 2.0 Redirect URI (must match Google Cloud Console configuration)",
    )

    frontend_url: Optional[str] = Field(
        default=None,
        description="Frontend URL for OAuth redirects (e.g., https://testtaptolooknet-production.up.railway.app)",
    )

    # ==================== NOTIFICATIONS CONFIGURATION (OPTIONAL) ====================
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram bot token for feedback notifications")

    telegram_chat_id: Optional[str] = Field(default=None, description="Telegram chat ID to receive notifications")

    # ==================== FLASK CONFIGURATION ====================
    flask_env: str = Field(
        default="production",
        pattern="^(development|production|testing)$",
        description="Flask environment (development, production, testing)",
    )

    flask_debug: bool = Field(default=False, description="Enable Flask debug mode (NEVER use in production!)")

    # ==================== SERVER CONFIGURATION ====================
    host: str = Field(default="0.0.0.0", description="Server host to bind to")

    port: int = Field(default=5000, ge=1, le=65535, description="Server port to bind to")

    # ==================== LOGGING CONFIGURATION ====================
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Logging level")

    enable_startup_diagnostics: bool = Field(
        default=False, description="Enable detailed startup diagnostics (for debugging only)"
    )

    # ==================== RATE LIMITING ====================
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")

    rate_limit_storage: str = Field(
        default="memory://", description="Rate limit storage backend (memory:// or redis://)"
    )

    # ==================== FILE CLEANUP ====================
    cleanup_enabled: bool = Field(default=True, description="Enable automatic file cleanup")

    cleanup_interval_minutes: int = Field(default=30, ge=1, description="Cleanup interval in minutes")

    cleanup_max_age_hours: int = Field(default=1, ge=1, description="Maximum file age in hours before cleanup")

    # ==================== CLOUDFLARE R2 STORAGE (OPTIONAL) ====================
    r2_access_key_id: Optional[str] = Field(
        default=None,
        description="Cloudflare R2 Access Key ID for image storage"
    )

    r2_secret_access_key: Optional[str] = Field(
        default=None,
        description="Cloudflare R2 Secret Access Key"
    )

    r2_endpoint_url: Optional[str] = Field(
        default=None,
        description="Cloudflare R2 S3-compatible endpoint URL"
    )

    r2_bucket_name: str = Field(
        default="taptolook",
        description="R2 bucket name for storing images"
    )

    r2_public_url: Optional[str] = Field(
        default=None,
        description="Public URL base for R2 bucket (e.g., https://pub-xxx.r2.dev)"
    )

    # ==================== VALIDATORS ====================

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is sufficiently random and long."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        if v in ["your_secure_random_jwt_secret_key_here", "changeme", "secret"]:
            raise ValueError("JWT_SECRET_KEY must be changed from default value!")
        return v

    @field_validator("flask_debug")
    @classmethod
    def validate_debug_mode(cls, v: bool, info) -> bool:
        """Warn if debug mode is enabled in production."""
        if v and info.data.get("flask_env") == "production":
            import warnings

            warnings.warn(
                "DEBUG MODE ENABLED IN PRODUCTION! This is a SECURITY RISK!", category=RuntimeWarning, stacklevel=2
            )
        return v

    @field_validator("google_redirect_uri")
    @classmethod
    def validate_google_redirect_uri(cls, v: Optional[str], info) -> Optional[str]:
        """Validate Google redirect URI if OAuth is enabled."""
        if info.data.get("google_oauth_enabled") and not v:
            raise ValueError(
                "GOOGLE_REDIRECT_URI is required when google_oauth_enabled=True"
            )
        return v

    @field_validator("google_client_secret")
    @classmethod
    def validate_google_client_secret(cls, v: Optional[str], info) -> Optional[str]:
        """Validate Google client secret if OAuth is enabled."""
        if info.data.get("google_oauth_enabled") and not v:
            raise ValueError(
                "GOOGLE_CLIENT_SECRET is required when google_oauth_enabled=True"
            )
        return v

    @field_validator("google_client_id")
    @classmethod
    def validate_google_client_id(cls, v: Optional[str], info) -> Optional[str]:
        """Validate Google client ID if OAuth is enabled."""
        if info.data.get("google_oauth_enabled") and not v:
            raise ValueError(
                "GOOGLE_CLIENT_ID is required when google_oauth_enabled=True"
            )
        return v

    # ==================== HELPER PROPERTIES ====================

    @property
    def database_url_str(self) -> str:
        """Get database URL as string (for psycopg2 compatibility)."""
        return str(self.database_url)

    @property
    def cleanup_max_age_seconds(self) -> int:
        """Get cleanup max age in seconds."""
        return self.cleanup_max_age_hours * 3600

    @property
    def cleanup_interval_seconds(self) -> int:
        """Get cleanup interval in seconds."""
        return self.cleanup_interval_minutes * 60

    def model_dump_safe(self) -> dict:
        """
        Dump configuration with sensitive values masked.
        Safe for logging and debugging.
        """
        data = self.model_dump()

        # Mask sensitive fields
        sensitive_keys = [
            "database_url",
            "jwt_secret_key",
            "nanobanana_api_key",
            "fashn_api_key",
            "huggingface_api_key",
            "telegram_bot_token",
            "device_fingerprint_secret",
            "google_client_secret",
            "r2_access_key_id",
            "r2_secret_access_key",
        ]

        for key in sensitive_keys:
            if key in data and data[key]:
                value = str(data[key])
                if len(value) > 8:
                    data[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    data[key] = "***"

        return data


# Global settings instance (loaded once at import)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).

    Settings are loaded once and cached for the application lifetime.

    Returns:
        Settings instance with validated configuration

    Raises:
        ValidationError: If required environment variables are missing or invalid

    Example:
        from backend.config import get_settings

        settings = get_settings()
        print(f"Running on port {settings.port}")
        print(f"Database: {settings.database_url_str}")
    """
    global _settings

    if _settings is None:
        _settings = Settings()

    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment (useful for testing).

    Returns:
        Fresh Settings instance
    """
    global _settings
    _settings = None
    return get_settings()


__all__ = ["Settings", "get_settings", "reload_settings"]
