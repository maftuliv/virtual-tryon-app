"""
Authentication and User Management Module
Handles user registration, login, JWT tokens, and premium features
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import jwt
from flask import Response, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from backend.utils.db_helpers import db_transaction


def _load_jwt_secret() -> str:
    """
    Load JWT secret key from environment variables.
    Falls back to a generated secret for local/dev usage to avoid weak defaults.

    Returns:
        str: JWT secret key for token signing
    """
    value = os.getenv("JWT_SECRET_KEY") or os.getenv("jwt_secret_key")
    if value:
        return value

    generated = secrets.token_urlsafe(64)
    print("[AUTH] ⚠️ JWT_SECRET_KEY not set. Generated a temporary secret for this session.")
    print("[AUTH] ⚠️ Tokens issued before restart will become invalid. Set JWT_SECRET_KEY ASAP.")
    return generated


# JWT Configuration
JWT_SECRET_KEY = _load_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

# Admin session configuration
ADMIN_SESSION_COOKIE = "admin_session"
ADMIN_SESSION_MAX_AGE = 60 * 60 * 12  # 12 hours

# Premium Configuration
FREE_WEEKLY_LIMIT = 3  # Free users get 3 generations per week
PREMIUM_MONTHLY_LIMIT = 50  # Premium users get 50 generations per month
PREMIUM_PRICE = 4.99


class AuthManager:
    """Manages authentication and user operations"""

    def __init__(self, db_connection: Any) -> None:
        """
        Initialize AuthManager with database connection.

        Args:
            db_connection: psycopg2 database connection object
        """
        self.db = db_connection

    # ============================================================
    # JWT Token Management
    # ============================================================

    def generate_token(self, user_id: int) -> str:
        """
        Generate JWT token for user.

        Args:
            user_id: User ID to encode in token

        Returns:
            str: Encoded JWT token
        """
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS),
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    def verify_token(self, token: str) -> Optional[int]:
        """
        Verify JWT token and return user_id.

        Args:
            token: JWT token string

        Returns:
            Optional[int]: User ID if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload["user_id"]
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return full user information.

        Args:
            token: JWT token string

        Returns:
            User dictionary if token is valid, None if invalid/expired
        """
        user_id = self.verify_token(token)
        if not user_id:
            return None

        return self.get_user_by_id(user_id)

    # ============================================================
    # User Registration and Login
    # ============================================================

    def register_user(self, email: str, password: str, full_name: str, provider: str = "email") -> Dict[str, Any]:
        """
        Register new user with email and password.
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            email: User email address
            password: Plain text password (will be hashed)
            full_name: User's full name
            provider: Authentication provider (default: "email", also: "google")

        Returns:
            Dict containing success status, user data, and token
        """
        try:
            # Validate email format
            email = email.lower().strip()
            if "@" not in email or "." not in email.split("@")[1]:
                return {"success": False, "error": "Invalid email format"}

            # Check if user already exists and insert in same transaction
            with db_transaction(self.db) as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return {"success": False, "error": "User with this email already exists"}

                # Hash password
                password_hash = generate_password_hash(password, method="pbkdf2:sha256")

                # Insert user
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, full_name, provider, created_at, last_login)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    RETURNING id, email, full_name, is_premium, created_at, role
                """,
                    (email, password_hash, full_name, provider),
                )
                user = cursor.fetchone()
                # Transaction commits automatically on context exit

            if user:
                user_data = {
                    "id": user[0],
                    "email": user[1],
                    "full_name": user[2],
                    "is_premium": user[3],
                    "created_at": user[4].isoformat() if user[4] else None,
                    "role": user[5] if len(user) > 5 else "user",
                }

                # Generate token outside transaction
                token = self.generate_token(user_data["id"])

                return {"success": True, "user": user_data, "token": token}

            return {"success": False, "error": "Failed to create user"}

        except Exception as e:
            print(f"[AUTH] Registration error: {e}")
            return {"success": False, "error": str(e)}

    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password.
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            email: User email address
            password: Plain text password to verify

        Returns:
            Dict containing success status, user data, and token
        """
        try:
            email = email.lower().strip()
            print(f"[AUTH] login_user: attempting login for {email}")

            with db_transaction(self.db) as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password_hash, full_name, avatar_url, is_premium, premium_until, role
                    FROM users
                    WHERE email = %s
                """,
                    (email,),
                )
                user = cursor.fetchone()

                if not user:
                    print(f"[AUTH] login_user: user not found for {email}")
                    return {"success": False, "error": "Invalid email or password"}

                print(f"[AUTH] login_user: found user_id={user[0]}, has_password_hash={bool(user[2])}")

                # Verify password (user[2] is password_hash)
                # Allow login if user has a password_hash set (even if registered via OAuth)
                if not user[2] or not check_password_hash(user[2], password):
                    print(f"[AUTH] login_user: password verification failed for {email}")
                    return {"success": False, "error": "Invalid email or password"}

                print(f"[AUTH] login_user: password verified successfully for {email}")

                # Update last login in same transaction
                cursor.execute(
                    """
                    UPDATE users SET last_login = NOW() WHERE id = %s
                """,
                    (user[0],),
                )
                # Transaction commits automatically on context exit

            user_data = {
                "id": user[0],
                "email": user[1],
                "full_name": user[3],
                "avatar_url": user[4],
                "is_premium": user[5],
                "premium_until": user[6].isoformat() if user[6] else None,
                "role": user[7] if len(user) > 7 else "user",
            }

            # Generate token outside transaction
            token = self.generate_token(user_data["id"])

            return {"success": True, "user": user_data, "token": token}

        except Exception as e:
            print(f"[AUTH] Login error: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # OAuth User Management
    # ============================================================

    def find_or_create_oauth_user(
        self, email: str, full_name: str, avatar_url: Optional[str], provider: str, provider_id: str
    ) -> Dict[str, Any]:
        """
        Find existing OAuth user or create new one.
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            email: User email address
            full_name: User's full name
            avatar_url: URL to user's avatar image (optional)
            provider: OAuth provider name (e.g., 'google')
            provider_id: Unique ID from OAuth provider

        Returns:
            Dict containing success status, user data, and token
        """
        try:
            email = email.lower().strip()

            with db_transaction(self.db) as cursor:
                # Try to find existing user by email or provider_id
                cursor.execute(
                    """
                    SELECT id, email, full_name, avatar_url, is_premium, premium_until, role
                    FROM users
                    WHERE email = %s OR (provider = %s AND provider_id = %s)
                """,
                    (email, provider, provider_id),
                )
                user = cursor.fetchone()

                if user:
                    # Update last login and OAuth info
                    cursor.execute(
                        """
                        UPDATE users
                        SET last_login = NOW(), provider = %s, provider_id = %s, avatar_url = %s
                        WHERE id = %s
                    """,
                        (provider, provider_id, avatar_url, user[0]),
                    )
                    # Transaction commits automatically on context exit

                    user_data = {
                        "id": user[0],
                        "email": user[1],
                        "full_name": user[2],
                        "avatar_url": avatar_url or user[3],
                        "is_premium": user[4],
                        "premium_until": user[5].isoformat() if user[5] else None,
                        "role": user[6] if len(user) > 6 else "user",
                    }
                else:
                    # Create new OAuth user
                    cursor.execute(
                        """
                        INSERT INTO users (email, full_name, avatar_url, provider, provider_id, created_at, last_login)
                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id, email, full_name, avatar_url, is_premium
                    """,
                        (email, full_name, avatar_url, provider, provider_id),
                    )
                    new_user = cursor.fetchone()
                    # Transaction commits automatically on context exit

                    user_data = {
                        "id": new_user[0],
                        "email": new_user[1],
                        "full_name": new_user[2],
                        "avatar_url": new_user[3],
                        "is_premium": new_user[4],
                        "premium_until": None,
                        "role": "user",
                    }

            # Generate token outside transaction
            token = self.generate_token(user_data["id"])

            return {"success": True, "user": user_data, "token": token}

        except Exception as e:
            print(f"[AUTH] OAuth user creation error: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================
    # User Information
    # ============================================================

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information by ID.
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            user_id: User ID to retrieve

        Returns:
            Optional[Dict]: User data if found, None otherwise
        """
        try:
            with db_transaction(self.db) as cursor:
                cursor.execute(
                    """
                    SELECT id, email, full_name, avatar_url, provider, is_premium, premium_until, created_at, role
                    FROM users
                    WHERE id = %s
                """,
                    (user_id,),
                )
                user = cursor.fetchone()

            if user:
                return {
                    "id": user[0],
                    "email": user[1],
                    "full_name": user[2],
                    "avatar_url": user[3],
                    "provider": user[4],
                    "is_premium": user[5],
                    "premium_until": user[6].isoformat() if user[6] else None,
                    "created_at": user[7].isoformat() if user[7] else None,
                    "role": user[8] if len(user) > 8 else "user",
                }

            return None

        except Exception as e:
            print(f"[AUTH] Get user error: {e}")
            return None

    # ============================================================
    # Premium and Limits Management
    # ============================================================

    def check_daily_limit(self, user_id: int) -> Tuple[bool, int, int]:
        """
        Check if user can generate (returns can_generate, used, limit).
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            user_id: User ID to check limits for

        Returns:
            Tuple[bool, int, int]: (can_generate, generations_used, generation_limit)
                - can_generate: Whether user can make another generation
                - generations_used: Number of generations used today (-1 for unlimited)
                - generation_limit: Daily limit (-1 for unlimited/premium)
        """
        try:
            limit_record = None
            with db_transaction(self.db) as cursor:
                # Check if user is premium or admin
                cursor.execute("SELECT is_premium, role FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()

                if not user:
                    return False, 0, FREE_WEEKLY_LIMIT

                is_premium = user[0]
                role = user[1] if len(user) > 1 else "user"

                # Admins have unlimited generations
                if role == "admin":
                    return True, -1, -1  # -1 means unlimited

                # Premium users have 50 generations per month
                if is_premium:
                    # Count generations this month from generations table
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM generations
                        WHERE user_id = %s
                        AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
                        AND created_at < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                        """,
                        (user_id,),
                    )
                    monthly_used = cursor.fetchone()[0]
                    can_generate = monthly_used < PREMIUM_MONTHLY_LIMIT
                    return can_generate, monthly_used, PREMIUM_MONTHLY_LIMIT

                # Free users: count generations this week from generations table
                # Week starts on Monday (ISO week)
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM generations
                    WHERE user_id = %s
                    AND created_at >= DATE_TRUNC('week', CURRENT_DATE)
                    AND created_at < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week'
                    """,
                    (user_id,),
                )
                weekly_used = cursor.fetchone()[0]
                can_generate = weekly_used < FREE_WEEKLY_LIMIT
                return can_generate, weekly_used, FREE_WEEKLY_LIMIT

            # This return is now inside the with block above
            return True, 0, FREE_WEEKLY_LIMIT

        except Exception as e:
            print(f"[AUTH] Check limit error: {e}")
            return False, 0, FREE_WEEKLY_LIMIT

    def increment_daily_limit(self, user_id: int, increment: int = 1) -> Dict[str, Any]:
        """
        Get updated generation count for user after increment.

        For free users: counts weekly generations from generations table.
        The actual generation record is created by TryonService.

        Args:
            user_id: User ID to get updated count for
            increment: Amount that was incremented (for compatibility)

        Returns:
            Dict with updated limit info:
            {
                'success': bool,
                'used': int,
                'limit': int,
                'remaining': int
            }
        """
        try:
            with db_transaction(self.db) as cursor:
                # Check user type first
                cursor.execute("SELECT is_premium, role FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()

                if not user:
                    return {
                        "success": False,
                        "used": 0,
                        "limit": FREE_WEEKLY_LIMIT,
                        "remaining": FREE_WEEKLY_LIMIT,
                    }

                is_premium = user[0]
                role = user[1] if len(user) > 1 else "user"

                # Admins have unlimited
                if role == "admin":
                    return {
                        "success": True,
                        "used": -1,
                        "limit": -1,
                        "remaining": -1,
                    }

                # Premium users: count monthly
                if is_premium:
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM generations
                        WHERE user_id = %s
                        AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
                        AND created_at < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                        """,
                        (user_id,),
                    )
                    monthly_used = cursor.fetchone()[0]
                    remaining = max(0, PREMIUM_MONTHLY_LIMIT - monthly_used)
                    return {
                        "success": True,
                        "used": monthly_used,
                        "limit": PREMIUM_MONTHLY_LIMIT,
                        "remaining": remaining,
                    }

                # Free users: count weekly from generations table
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM generations
                    WHERE user_id = %s
                    AND created_at >= DATE_TRUNC('week', CURRENT_DATE)
                    AND created_at < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week'
                    """,
                    (user_id,),
                )
                weekly_used = cursor.fetchone()[0]

            remaining = max(0, FREE_WEEKLY_LIMIT - weekly_used)
            return {
                "success": True,
                "used": weekly_used,
                "limit": FREE_WEEKLY_LIMIT,
                "remaining": remaining,
            }

        except Exception as e:
            print(f"[AUTH] Increment limit error: {e}")
            return {
                "success": False,
                "used": 0,
                "limit": FREE_WEEKLY_LIMIT,
                "remaining": FREE_WEEKLY_LIMIT,
            }

    def set_premium(self, user_id: int, days: int = 30) -> bool:
        """
        Set user as premium for specified days.
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            user_id: User ID to grant premium to
            days: Number of days to grant premium (default: 30)

        Returns:
            bool: True if successful, False on error
        """
        try:
            premium_until = datetime.now() + timedelta(days=days)
            with db_transaction(self.db) as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET is_premium = TRUE, premium_until = %s
                    WHERE id = %s
                """,
                    (premium_until, user_id),
                )
                # Transaction commits automatically on context exit
            return True

        except Exception as e:
            print(f"[AUTH] Set premium error: {e}")
            return False

    # ============================================================
    # Generation History
    # ============================================================

    def save_generation(
        self,
        user_id: int,
        person_image_url: str,
        garment_image_url: str,
        result_image_url: str,
        category: str,
        session_id: Optional[str] = None,
    ) -> Optional[int]:
        """
        Save generation to history.
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            user_id: User ID who created the generation
            person_image_url: URL/path to person image
            garment_image_url: URL/path to garment image
            result_image_url: URL/path to result image
            category: Garment category
            session_id: Optional session identifier

        Returns:
            Optional[int]: Generation ID if successful, None on error
        """
        try:
            with db_transaction(self.db) as cursor:
                cursor.execute(
                    """
                    INSERT INTO generations (user_id, session_id, person_image_url, garment_image_url, result_image_url, category, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'completed', NOW())
                    RETURNING id
                """,
                    (user_id, session_id, person_image_url, garment_image_url, result_image_url, category),
                )
                generation_id = cursor.fetchone()[0]
                # Transaction commits automatically on context exit

            return generation_id

        except Exception as e:
            print(f"[AUTH] Save generation error: {e}")
            return None

    def get_user_generations(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get user's generation history.
        
        Uses safe transaction management to prevent "current transaction is aborted" errors.

        Args:
            user_id: User ID to retrieve generations for
            limit: Maximum number of generations to return (default: 50)
            offset: Number of records to skip for pagination (default: 0)

        Returns:
            List[Dict]: List of generation records
        """
        try:
            with db_transaction(self.db) as cursor:
                cursor.execute(
                    """
                    SELECT id, person_image_url, garment_image_url, result_image_url, category, created_at
                    FROM generations
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """,
                    (user_id, limit, offset),
                )
                generations = cursor.fetchall()

            return [
                {
                    "id": g[0],
                    "person_image_url": g[1],
                    "garment_image_url": g[2],
                    "result_image_url": g[3],
                    "category": g[4],
                    "created_at": g[5].isoformat() if g[5] else None,
                }
                for g in generations
            ]

        except Exception as e:
            print(f"[AUTH] Get generations error: {e}")
            return []


# ============================================================
# Flask Decorators for Route Protection
# ============================================================


def create_auth_decorator(auth_manager: AuthManager) -> Tuple[Callable, Callable]:
    """
    Create decorators for protecting routes.

    Args:
        auth_manager: AuthManager instance for token verification

    Returns:
        Tuple[Callable, Callable]: (require_auth, require_admin) decorators
    """

    def require_auth(f: Callable) -> Callable:
        """
        Decorator to require authentication.

        Args:
            f: Flask route function to protect

        Returns:
            Callable: Decorated function that checks JWT token
        """

        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Extract token from cookie/header
            token = get_token_from_request()

            if not token:
                return jsonify({"error": "No authorization token provided"}), 401

            user = decode_token(token)
            if not user:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Attach user info for downstream handlers
            request.user_id = user["id"]

            return f(*args, **kwargs)

        return decorated_function

    def require_admin(f: Callable) -> Callable:
        """
        Decorator to require admin role.

        Args:
            f: Flask route function to protect

        Returns:
            Callable: Decorated function that checks JWT token and admin role
        """

        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            token = get_token_from_request()

            if not token:
                return jsonify({"error": "No authorization token provided"}), 401

            user = decode_token(token, require_admin=True)
            if not user:
                return jsonify({"error": "Access denied. Admin privileges required"}), 403

            request.user_id = user["id"]

            return f(*args, **kwargs)

        return decorated_function

    return require_auth, require_admin


# ============================================================
# Standalone Admin Decorator (for backwards compatibility)
# ============================================================


def require_admin(f: Callable) -> Callable:
    """
    Standalone decorator to require admin role for API endpoints.

    Supports tokens from Authorization header OR auth_token cookie.
    Use this for protecting admin API endpoints (returns JSON).

    Args:
        f: Flask route function to protect

    Returns:
        Callable: Decorated function that checks JWT token and admin role
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        # Get token from header or cookie
        token = get_token_from_request()

        if not token:
            return jsonify({"error": "No authorization token provided"}), 401

        # Decode and validate token with admin check
        user = decode_token(token, require_admin=True)

        if not user:
            return jsonify({"error": "Access denied. Admin privileges required"}), 403

        # Valid admin token → call route handler
        return f(current_user=user, *args, **kwargs)

    return decorated_function


# ============================================================
# Enhanced Token Utilities (Cookie + Header Support)
# ============================================================


def decode_token(token: str, require_admin: bool = False) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT token, optionally checking admin role.

    Args:
        token: JWT token string
        require_admin: If True, verify user has admin role

    Returns:
        Dict with user data if valid, None otherwise
    """
    if not token or not token.strip():
        return None

    try:
        # Decode JWT
        payload = jwt.decode(token.strip(), JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            return None

        # Get database connection from app config
        from flask import current_app
        db = current_app.config.get('db_connection')

        if not db:
            print("[AUTH] Database not available for token validation")
            return None

        # Fetch user from database using safe transaction management
        try:
            with db_transaction(db) as cursor:
                cursor.execute(
                    """
                    SELECT id, email, full_name, role, is_premium, avatar_url, provider
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                user_row = cursor.fetchone()

            if not user_row:
                return None

            user = {
                "id": user_row[0],
                "email": user_row[1],
                "full_name": user_row[2],
                "role": user_row[3],
                "is_premium": user_row[4],
                "avatar_url": user_row[5],
                "provider": user_row[6],
            }

            # Check admin role if required
            if require_admin and user["role"] != "admin":
                return None

            return user

        except Exception as e:
            print(f"[AUTH] Error fetching user during token decode: {e}")
            return None

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        print(f"[AUTH] Unexpected error decoding token: {e}")
        return None


def get_token_from_request() -> Optional[str]:
    """
    Extract JWT token from request (Authorization header or auth_token cookie).

    Returns:
        Token string or None
    """
    # Try HTTP-only cookie first (source of truth after server-issued login)
    token = request.cookies.get("auth_token")
    if token:
        return token.strip()

    # Fall back to Authorization header (legacy/localStorage usage)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "").strip()

    return None


def set_auth_cookie(response: Response, token: str) -> Response:
    """
    Set HTTP-only auth cookie on response.

    Args:
        response: Flask Response object
        token: JWT token to store

    Returns:
        Modified Response object
    """
    # Calculate cookie max age from JWT expiration
    max_age = JWT_EXPIRATION_DAYS * 24 * 60 * 60  # Convert days to seconds

    # Determine if running on localhost (for development)
    is_localhost = request.host.startswith("localhost") or request.host.startswith("127.0.0.1")

    response.set_cookie(
        "auth_token",
        value=token,
        max_age=max_age,
        secure=not is_localhost,  # HTTPS only in production, allow HTTP on localhost
        httponly=True,  # No JS access
        samesite="Strict",  # CSRF protection
        path="/",
    )

    return response


def clear_auth_cookie(response: Response) -> Response:
    """
    Clear auth cookie on logout.

    Args:
        response: Flask Response object

    Returns:
        Modified Response object
    """
    response.delete_cookie("auth_token", path="/")
    return response


def set_admin_session_cookie(response: Response, session_id: str) -> Response:
    """Set admin session cookie."""
    if not session_id:
        return response

    # Determine HTTPS requirement
    is_localhost = request.host.startswith("localhost") or request.host.startswith("127.0.0.1")

    response.set_cookie(
        ADMIN_SESSION_COOKIE,
        value=session_id,
        max_age=ADMIN_SESSION_MAX_AGE,
        secure=not is_localhost,
        httponly=True,
        samesite="Strict",
        path="/",
    )
    return response


def clear_admin_session_cookie(response: Response) -> Response:
    response.delete_cookie(ADMIN_SESSION_COOKIE, path="/")
    return response


# ============================================================
# Admin Page Decorator (Server-Side HTML Protection)
# ============================================================


def require_admin_page(f: Callable) -> Callable:
    """
    Decorator for serving admin HTML with server-side session validation.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        from flask import current_app, redirect
        admin_session_service = current_app.config.get("ADMIN_SESSION_SERVICE")

        if not admin_session_service or not admin_session_service.is_available():
            return redirect("/")

        session_id = request.cookies.get(ADMIN_SESSION_COOKIE)
        if not session_id:
            return redirect("/")

        admin_user = admin_session_service.get_session_user(session_id)
        if not admin_user:
            response = redirect("/")
            clear_admin_session_cookie(response)
            return response

        return f(current_user=admin_user, *args, **kwargs)

    return decorated_function
