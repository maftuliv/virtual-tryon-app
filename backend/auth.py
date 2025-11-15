"""
Authentication and User Management Module
Handles user registration, login, JWT tokens, and premium features
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, Tuple, List, Callable
from flask import request, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash


def _load_jwt_secret() -> str:
    """
    Load JWT secret key from environment variables.
    Falls back to a generated secret for local/dev usage to avoid weak defaults.

    Returns:
        str: JWT secret key for token signing
    """
    value = (
        os.getenv('JWT_SECRET_KEY') or
        os.getenv('jwt_secret_key')
    )
    if value:
        return value

    generated = secrets.token_urlsafe(64)
    print("[AUTH] ⚠️ JWT_SECRET_KEY not set. Generated a temporary secret for this session.")
    print("[AUTH] ⚠️ Tokens issued before restart will become invalid. Set JWT_SECRET_KEY ASAP.")
    return generated


# JWT Configuration
JWT_SECRET_KEY = _load_jwt_secret()
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

# Premium Configuration
FREE_DAILY_LIMIT = 3
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
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS),
            'iat': datetime.utcnow()
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
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # ============================================================
    # User Registration and Login
    # ============================================================

    def register_user(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """
        Register new user with email and password.

        Args:
            email: User email address
            password: Plain text password (will be hashed)
            full_name: User's full name

        Returns:
            Dict containing success status, user data, and token
        """
        try:
            # Validate email format
            email = email.lower().strip()
            if '@' not in email or '.' not in email.split('@')[1]:
                return {'success': False, 'error': 'Invalid email format'}

            # Check if user already exists
            cursor = self.db.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return {'success': False, 'error': 'User with this email already exists'}

            # Hash password
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert user
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, provider, created_at, last_login)
                VALUES (%s, %s, %s, 'email', NOW(), NOW())
                RETURNING id, email, full_name, is_premium, created_at
            """, (email, password_hash, full_name))

            user = cursor.fetchone()
            self.db.commit()
            cursor.close()

            if user:
                user_data = {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'is_premium': user[3],
                    'created_at': user[4].isoformat() if user[4] else None
                }

                # Generate token
                token = self.generate_token(user_data['id'])

                return {
                    'success': True,
                    'user': user_data,
                    'token': token
                }

            return {'success': False, 'error': 'Failed to create user'}

        except Exception as e:
            self.db.rollback()
            print(f"Registration error: {e}")
            return {'success': False, 'error': str(e)}

    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password.

        Args:
            email: User email address
            password: Plain text password to verify

        Returns:
            Dict containing success status, user data, and token
        """
        try:
            email = email.lower().strip()

            cursor = self.db.cursor()
            cursor.execute("""
                SELECT id, email, password_hash, full_name, avatar_url, is_premium, premium_until
                FROM users
                WHERE email = %s AND provider = 'email'
            """, (email,))

            user = cursor.fetchone()

            if not user:
                return {'success': False, 'error': 'Invalid email or password'}

            # Verify password
            if not check_password_hash(user[2], password):
                return {'success': False, 'error': 'Invalid email or password'}

            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = NOW() WHERE id = %s
            """, (user[0],))
            self.db.commit()
            cursor.close()

            user_data = {
                'id': user[0],
                'email': user[1],
                'full_name': user[3],
                'avatar_url': user[4],
                'is_premium': user[5],
                'premium_until': user[6].isoformat() if user[6] else None
            }

            # Generate token
            token = self.generate_token(user_data['id'])

            return {
                'success': True,
                'user': user_data,
                'token': token
            }

        except Exception as e:
            self.db.rollback()
            print(f"Login error: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # OAuth User Management
    # ============================================================

    def find_or_create_oauth_user(
        self,
        email: str,
        full_name: str,
        avatar_url: Optional[str],
        provider: str,
        provider_id: str
    ) -> Dict[str, Any]:
        """
        Find existing OAuth user or create new one.

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

            cursor = self.db.cursor()

            # Try to find existing user by email or provider_id
            cursor.execute("""
                SELECT id, email, full_name, avatar_url, is_premium, premium_until
                FROM users
                WHERE email = %s OR (provider = %s AND provider_id = %s)
            """, (email, provider, provider_id))

            user = cursor.fetchone()

            if user:
                # Update last login and OAuth info
                cursor.execute("""
                    UPDATE users
                    SET last_login = NOW(), provider = %s, provider_id = %s, avatar_url = %s
                    WHERE id = %s
                """, (provider, provider_id, avatar_url, user[0]))
                self.db.commit()

                user_data = {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'avatar_url': avatar_url or user[3],
                    'is_premium': user[4],
                    'premium_until': user[5].isoformat() if user[5] else None
                }
            else:
                # Create new OAuth user
                cursor.execute("""
                    INSERT INTO users (email, full_name, avatar_url, provider, provider_id, created_at, last_login)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id, email, full_name, avatar_url, is_premium
                """, (email, full_name, avatar_url, provider, provider_id))

                new_user = cursor.fetchone()
                self.db.commit()

                user_data = {
                    'id': new_user[0],
                    'email': new_user[1],
                    'full_name': new_user[2],
                    'avatar_url': new_user[3],
                    'is_premium': new_user[4],
                    'premium_until': None
                }

            cursor.close()

            # Generate token
            token = self.generate_token(user_data['id'])

            return {
                'success': True,
                'user': user_data,
                'token': token
            }

        except Exception as e:
            self.db.rollback()
            print(f"OAuth user creation error: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # User Information
    # ============================================================

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            Optional[Dict]: User data if found, None otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT id, email, full_name, avatar_url, provider, is_premium, premium_until, created_at, role
                FROM users
                WHERE id = %s
            """, (user_id,))

            user = cursor.fetchone()
            cursor.close()

            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'avatar_url': user[3],
                    'provider': user[4],
                    'is_premium': user[5],
                    'premium_until': user[6].isoformat() if user[6] else None,
                    'created_at': user[7].isoformat() if user[7] else None,
                    'role': user[8] if len(user) > 8 else 'user'
                }

            return None

        except Exception as e:
            print(f"Get user error: {e}")
            return None

    # ============================================================
    # Premium and Limits Management
    # ============================================================

    def check_daily_limit(self, user_id: int) -> Tuple[bool, int, int]:
        """
        Check if user can generate (returns can_generate, used, limit).

        Args:
            user_id: User ID to check limits for

        Returns:
            Tuple[bool, int, int]: (can_generate, generations_used, generation_limit)
                - can_generate: Whether user can make another generation
                - generations_used: Number of generations used today (-1 for unlimited)
                - generation_limit: Daily limit (-1 for unlimited/premium)
        """
        try:
            cursor = self.db.cursor()

            # Check if user is premium
            cursor.execute("SELECT is_premium FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                cursor.close()
                return False, 0, FREE_DAILY_LIMIT

            # Premium users have unlimited generations
            if user[0]:
                cursor.close()
                return True, -1, -1  # -1 means unlimited

            # Check today's usage
            today = datetime.now().date()
            cursor.execute("""
                SELECT generations_count FROM daily_limits
                WHERE user_id = %s AND date = %s
            """, (user_id, today))

            limit_record = cursor.fetchone()
            cursor.close()

            if not limit_record:
                # No generations yet today - return 0 used
                return True, 0, FREE_DAILY_LIMIT

            used = limit_record[0]

            if used >= FREE_DAILY_LIMIT:
                return False, FREE_DAILY_LIMIT, FREE_DAILY_LIMIT

            return True, used, FREE_DAILY_LIMIT

        except Exception as e:
            print(f"Check limit error: {e}")
            return False, 0, FREE_DAILY_LIMIT

    def increment_daily_limit(self, user_id: int) -> bool:
        """
        Increment user's daily generation count.

        Args:
            user_id: User ID to increment counter for

        Returns:
            bool: True if successful, False on error
        """
        try:
            today = datetime.now().date()
            cursor = self.db.cursor()

            # Insert or update daily limit
            cursor.execute("""
                INSERT INTO daily_limits (user_id, date, generations_count)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id, date)
                DO UPDATE SET
                    generations_count = daily_limits.generations_count + 1,
                    updated_at = NOW()
            """, (user_id, today))

            self.db.commit()
            cursor.close()
            return True

        except Exception as e:
            self.db.rollback()
            print(f"Increment limit error: {e}")
            return False

    def set_premium(self, user_id: int, days: int = 30) -> bool:
        """
        Set user as premium for specified days.

        Args:
            user_id: User ID to grant premium to
            days: Number of days to grant premium (default: 30)

        Returns:
            bool: True if successful, False on error
        """
        try:
            premium_until = datetime.now() + timedelta(days=days)

            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE users
                SET is_premium = TRUE, premium_until = %s
                WHERE id = %s
            """, (premium_until, user_id))

            self.db.commit()
            cursor.close()
            return True

        except Exception as e:
            self.db.rollback()
            print(f"Set premium error: {e}")
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
        session_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Save generation to history.

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
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO generations (user_id, session_id, person_image_url, garment_image_url, result_image_url, category, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'completed', NOW())
                RETURNING id
            """, (user_id, session_id, person_image_url, garment_image_url, result_image_url, category))

            generation_id = cursor.fetchone()[0]
            self.db.commit()
            cursor.close()

            return generation_id

        except Exception as e:
            self.db.rollback()
            print(f"Save generation error: {e}")
            return None

    def get_user_generations(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get user's generation history.

        Args:
            user_id: User ID to retrieve generations for
            limit: Maximum number of generations to return (default: 50)
            offset: Number of records to skip for pagination (default: 0)

        Returns:
            List[Dict]: List of generation records
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT id, person_image_url, garment_image_url, result_image_url, category, created_at
                FROM generations
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))

            generations = cursor.fetchall()
            cursor.close()

            return [{
                'id': g[0],
                'person_image_url': g[1],
                'garment_image_url': g[2],
                'result_image_url': g[3],
                'category': g[4],
                'created_at': g[5].isoformat() if g[5] else None
            } for g in generations]

        except Exception as e:
            print(f"Get generations error: {e}")
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
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization', '')

            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No authorization token provided'}), 401

            token = auth_header.replace('Bearer ', '')
            user_id = auth_manager.verify_token(token)

            if not user_id:
                return jsonify({'error': 'Invalid or expired token'}), 401

            # Attach user_id to request for use in route
            request.user_id = user_id

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
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization', '')

            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No authorization token provided'}), 401

            token = auth_header.replace('Bearer ', '')
            user_id = auth_manager.verify_token(token)

            if not user_id:
                return jsonify({'error': 'Invalid or expired token'}), 401

            # Check if user is admin
            cursor = auth_manager.db.cursor()
            cursor.execute("""
                SELECT role FROM users WHERE id = %s
            """, (user_id,))

            user = cursor.fetchone()
            cursor.close()

            if not user or user[0] != 'admin':
                return jsonify({'error': 'Access denied. Admin privileges required'}), 403

            # Attach user_id to request for use in route
            request.user_id = user_id

            return f(*args, **kwargs)

        return decorated_function

    return require_auth, require_admin
