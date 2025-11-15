# Backend Refactoring Specification - Service Layer Pattern

## Overview
Refactoring backend/app.py (2460 lines) into modular Service Layer architecture.

**Goal**: Separate concerns into API → Service → Repository → Database layers.

---

## Architecture Layers

### Layer 1: API Routes (Thin Handlers)
**Purpose**: HTTP request/response handling only
**Responsibilities**:
- Parse request data
- Call appropriate service methods
- Format response
- Handle HTTP errors (400, 401, 404, etc.)

**Rules**:
- NO business logic
- NO direct database access
- NO external API calls
- Maximum 50 lines per route handler

### Layer 2: Services (Business Logic)
**Purpose**: Orchestrate application workflows
**Responsibilities**:
- Coordinate multiple repositories
- Implement business rules
- Transaction management
- Error handling & logging

**Rules**:
- NO direct database queries (use repositories)
- NO Flask-specific code (framework agnostic)
- Testable without Flask app

### Layer 3: Clients (External APIs)
**Purpose**: Wrap external API integrations
**Responsibilities**:
- HTTP calls to external services
- Response parsing
- Retry logic
- Error mapping

**Rules**:
- One client per external service
- No business logic
- Return domain objects or DTOs

### Layer 4: Repositories (Data Access)
**Purpose**: Database and file storage operations
**Responsibilities**:
- CRUD operations
- Query building
- Connection management
- Data mapping

**Rules**:
- NO business logic
- Return domain models
- Handle DB exceptions

---

## Module Specifications

## 1. REPOSITORIES LAYER

### 1.1 `repositories/device_limit_repository.py`

```python
class DeviceLimitRepository:
    """Manages device limit records in PostgreSQL."""

    def __init__(self, db_connection):
        """
        Args:
            db_connection: psycopg2 connection object
        """
        self.db = db_connection

    def get_limit_status(self, device_fingerprint: str, ip_address: str,
                        limit_date: date) -> Optional[Dict]:
        """
        Get device limit status for a specific date.

        Returns:
            {
                'id': int,
                'device_fingerprint': str,
                'ip_address': str,
                'generations_used': int,
                'limit_date': date,
                'last_used_at': datetime,
                'created_at': datetime,
                'updated_at': datetime
            } or None if not found
        """

    def create_or_reset_record(self, device_fingerprint: str, ip_address: str,
                               user_agent: str, limit_date: date) -> Dict:
        """
        Create new record or reset if date changed.

        Returns: Device limit record dict
        """

    def increment_usage(self, device_fingerprint: str, ip_address: str,
                       limit_date: date, increment: int = 1) -> Dict:
        """
        Atomically increment generations_used counter.

        Returns: Updated device limit record
        """

    def calculate_total_usage(self, device_fingerprint: str, ip_address: str,
                             limit_date: date) -> int:
        """
        Calculate total generations used for device on specific date.

        Returns: Total count
        """

    def reset_all_for_date(self, limit_date: date) -> int:
        """
        Reset all device limits for a specific date (admin operation).

        Returns: Number of records updated
        """
```

**Migration from app.py:**
- Lines 302-428: All device limit functions
- Direct SQL → Repository methods
- Manual transaction handling → Repository encapsulation

---

### 1.2 `repositories/user_repository.py`

```python
class UserRepository:
    """Wraps AuthManager for user operations."""

    def __init__(self, auth_manager):
        """
        Args:
            auth_manager: backend.auth.AuthManager instance
        """
        self.auth_manager = auth_manager

    def create_user(self, email: str, password: str, full_name: str,
                   provider: str = 'email') -> Dict:
        """
        Register new user.

        Returns: User dict with id, email, etc.
        Raises: ValueError if email exists
        """

    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """
        Verify credentials and return user + token.

        Returns: {'user': {...}, 'token': str} or None
        """

    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""

    def get_by_token(self, token: str) -> Optional[Dict]:
        """Validate token and return user."""

    def check_daily_limit(self, user_id: int) -> Dict:
        """
        Check user's daily generation limit.

        Returns: {'can_generate': bool, 'used': int, 'limit': int}
        """

    def increment_daily_limit(self, user_id: int) -> Dict:
        """Increment user's generation counter."""

    def list_all_users(self) -> List[Dict]:
        """Get all users with generation counts (admin)."""

    def toggle_premium(self, user_id: int, enable: bool) -> Dict:
        """Grant/revoke premium status."""
```

**Migration from app.py:**
- Wraps existing `AuthManager` class
- Lines 2052-2419: Auth and admin endpoints logic
- Provides clean interface for services

---

### 1.3 `repositories/generation_repository.py`

```python
class GenerationRepository:
    """Tracks virtual try-on generation records."""

    def __init__(self, db_connection):
        self.db = db_connection

    def create(self, user_id: Optional[int], device_fingerprint: Optional[str],
              category: str, person_image_url: str, garment_image_url: str,
              result_image_url: Optional[str], status: str) -> Dict:
        """
        Record a new generation attempt.

        Returns: Generation record
        """

    def update_status(self, generation_id: int, status: str,
                     result_url: Optional[str] = None) -> Dict:
        """Update generation status (pending → completed/failed)."""

    def list_by_user(self, user_id: int, limit: int = 100,
                    offset: int = 0) -> List[Dict]:
        """Get user's generation history."""

    def list_all(self, limit: int = 100, offset: int = 0,
                user_id: Optional[int] = None) -> List[Dict]:
        """Get all generations (admin, with optional filtering)."""

    def get_stats(self) -> Dict:
        """
        Get generation statistics.

        Returns: {
            'total': int,
            'today': int,
            'by_category': {'upper': int, 'lower': int, ...}
        }
        """
```

**Migration from app.py:**
- Lines 2290-2419: Admin generation tracking
- Currently inline SQL in admin routes
- New repository centralizes this logic

---

### 1.4 `repositories/feedback_repository.py`

```python
class FeedbackRepository:
    """Dual storage: PostgreSQL primary, JSON files fallback."""

    def __init__(self, db_connection, feedback_folder: str):
        self.db = db_connection
        self.feedback_folder = feedback_folder

    def save(self, rating: int, comment: str, session_id: Optional[str],
            ip_address: str, telegram_sent: bool = False) -> Dict:
        """
        Save feedback to DB (primary) and file (backup).

        Returns: Feedback record
        """

    def list_all(self, limit: int = 100) -> Dict:
        """
        Retrieve feedback from DB first, fallback to files.

        Returns: {
            'source': 'database' or 'files',
            'count': int,
            'feedback': List[Dict]
        }
        """

    def get_unsent_telegram(self) -> List[Dict]:
        """Get feedback not yet sent to Telegram."""

    def mark_telegram_sent(self, feedback_id: int, success: bool,
                          error_message: Optional[str] = None):
        """Update telegram_sent status."""

    def _save_to_file(self, feedback: Dict) -> str:
        """Backup to JSON file."""

    def _load_from_files(self) -> List[Dict]:
        """Load all .json files from feedback folder."""
```

**Migration from app.py:**
- Lines 1651-1977: Feedback submission and listing
- Currently uses `backend.database.save_feedback_to_db()`
- Repository provides consistent interface

---

## 2. CLIENTS LAYER

### 2.1 `clients/nanobanana_client.py`

```python
class NanoBananaClient:
    """NanoBanana AI API client for virtual try-on."""

    BASE_URL = "https://api.nanobananaapi.ai"

    def __init__(self, api_key: str, timeout: int = 120):
        self.api_key = api_key
        self.timeout = timeout
        self.logger = get_logger(__name__)

    def generate_tryon(self, person_image_url: str, garment_image_url: str,
                      category: str = "auto") -> Dict:
        """
        Submit virtual try-on task and poll for result.

        Args:
            person_image_url: Public URL to person image
            garment_image_url: Public URL to garment image
            category: "upper", "lower", or "auto"

        Returns: {
            'task_id': str,
            'result_url': str,
            'status': 'completed',
            'processing_time': float
        }

        Raises:
            APIError: If API call fails
            TimeoutError: If polling exceeds timeout
        """

    def _submit_task(self, person_url: str, garment_url: str,
                    category: str) -> str:
        """Submit task and return task_id."""

    def _poll_task_status(self, task_id: str) -> Dict:
        """Poll task status with exponential backoff."""

    def _download_result(self, result_url: str, output_path: str) -> str:
        """Download result image to file."""
```

**Migration from app.py:**
- Lines 645-883: `process_with_nanobanana()` function
- Extract into dedicated client class
- Better error handling and retry logic

---

### 2.2 `clients/telegram_client.py`

```python
class TelegramClient:
    """Telegram Bot API client with retry logic."""

    BASE_URL = "https://api.telegram.org"

    def __init__(self, bot_token: str, default_chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.logger = get_logger(__name__)

    def send_message(self, text: str, chat_id: Optional[str] = None,
                    parse_mode: str = "HTML") -> Dict:
        """
        Send text message with retry.

        Returns: Telegram API response
        Raises: TelegramError
        """

    def send_photo(self, photo_path: str, caption: Optional[str] = None,
                  chat_id: Optional[str] = None) -> Dict:
        """
        Send photo with caption and retry.

        Returns: Telegram API response
        Raises: TelegramError
        """

    def get_bot_info(self) -> Dict:
        """Get bot information (/getMe)."""

    def get_updates(self, limit: int = 10) -> List[Dict]:
        """Get recent messages (/getUpdates)."""

    def auto_detect_chat_id(self) -> Optional[str]:
        """
        Auto-detect chat ID from recent messages.

        Returns: Chat ID or None if not found
        """

    def _retry_request(self, method: Callable, max_retries: int = 3,
                      backoff_factor: int = 1) -> Any:
        """Generic retry logic with exponential backoff."""
```

**Migration from app.py:**
- Lines 1449-1651: Telegram retry functions
- DRY: Single retry mechanism for both message and photo
- Lines 1754-1822: Auto-detect chat ID logic

---

## 3. SERVICES LAYER

### 3.1 `services/image_service.py`

```python
class ImageService:
    """Image processing, validation, and URL generation."""

    def __init__(self, upload_folder: str, results_folder: str,
                railway_domain: Optional[str] = None):
        self.upload_folder = upload_folder
        self.results_folder = results_folder
        self.railway_domain = railway_domain
        self.logger = get_logger(__name__)

    def validate_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""

    def validate_image_quality(self, image_path: str) -> Dict:
        """
        Validate image quality (resolution, aspect ratio, brightness).

        Returns: {
            'valid': bool,
            'warnings': List[str],
            'metadata': {
                'width': int,
                'height': int,
                'brightness': float,
                'aspect_ratio': str
            }
        }
        """

    def preprocess_image(self, image_path: str, max_dimension: int = 2000,
                        quality: int = 95) -> str:
        """
        Resize, convert format, optimize image.

        Returns: Path to optimized image
        """

    def image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string."""

    def save_base64_image(self, base64_string: str, output_path: str) -> str:
        """Save base64 encoded image to file."""

    def generate_public_url(self, image_path: str,
                           request_obj: Optional[Any] = None) -> str:
        """
        Generate public URL for image (Railway or ImgBB fallback).

        Returns: Public URL string
        """

    def _detect_railway_domain(self, request_obj: Any) -> Optional[str]:
        """Detect Railway domain from Flask request."""

    def _upload_to_imgbb(self, image_path: str) -> Optional[str]:
        """Fallback: Upload to ImgBB and return URL."""
```

**Migration from app.py:**
- Lines 430-640: Image utility functions
- Consolidate into single service class
- Clear separation of concerns

---

### 3.2 `services/limit_service.py`

```python
class LimitService:
    """Manages device and user generation limits."""

    def __init__(self, device_repo: DeviceLimitRepository,
                user_repo: UserRepository, free_device_limit: int = 3):
        self.device_repo = device_repo
        self.user_repo = user_repo
        self.free_device_limit = free_device_limit
        self.logger = get_logger(__name__)

    def check_device_limit(self, device_fingerprint: str, ip_address: str,
                          user_agent: str) -> Dict:
        """
        Check anonymous device limit for today.

        Returns: {
            'can_generate': bool,
            'used': int,
            'remaining': int,
            'limit': int
        }
        """

    def check_user_limit(self, user_id: int) -> Dict:
        """
        Check authenticated user limit.

        Returns: Same structure as check_device_limit
        """

    def increment_device_limit(self, device_fingerprint: str, ip_address: str,
                              user_agent: str) -> Dict:
        """Increment device counter and return updated status."""

    def increment_user_limit(self, user_id: int) -> Dict:
        """Increment user counter and return updated status."""

    def can_generate(self, user_id: Optional[int], device_fingerprint: str,
                    ip_address: str, user_agent: str) -> Tuple[bool, Dict]:
        """
        Universal limit check (user or device).

        Returns: (can_generate, limit_status_dict)
        """
```

**Migration from app.py:**
- Lines 294-428: Device limit functions
- Lines 1131-1384: Limit checking in /api/tryon
- Centralize all limit logic

---

### 3.3 `services/notification_service.py`

```python
class NotificationService:
    """Handles Telegram notifications for results and feedback."""

    def __init__(self, telegram_client: TelegramClient,
                feedback_repo: FeedbackRepository):
        self.telegram = telegram_client
        self.feedback_repo = feedback_repo
        self.logger = get_logger(__name__)

    def send_result_notification(self, result_image_path: str,
                                filename: str, ip_address: str) -> bool:
        """
        Send try-on result to Telegram chat.

        Returns: True if sent successfully
        """

    def send_feedback_notification(self, feedback: Dict) -> bool:
        """
        Send feedback rating/comment to Telegram.

        Returns: True if sent successfully
        """

    def retry_failed_feedbacks(self) -> int:
        """
        Retry sending feedback that failed previously.

        Returns: Number of successfully sent
        """

    def auto_configure_chat_id(self) -> Optional[str]:
        """
        Attempt to auto-detect and configure chat ID.

        Returns: Detected chat ID or None
        """
```

**Migration from app.py:**
- Lines 1449-1651: Telegram retry functions
- Lines 1754-1822: Auto-detect logic
- Integrate with TelegramClient

---

### 3.4 `services/tryon_service.py`

```python
class TryonService:
    """Orchestrates virtual try-on workflow."""

    def __init__(self, image_service: ImageService,
                nanobanana_client: NanoBananaClient,
                notification_service: NotificationService,
                limit_service: LimitService,
                generation_repo: GenerationRepository,
                results_folder: str):
        self.image_service = image_service
        self.nanobanana = nanobanana_client
        self.notifications = notification_service
        self.limits = limit_service
        self.generation_repo = generation_repo
        self.results_folder = results_folder
        self.logger = get_logger(__name__)

    def process_tryon(self, person_images: List[str], garment_image: str,
                     category: str, user_id: Optional[int],
                     device_fingerprint: str, ip_address: str,
                     user_agent: str) -> Dict:
        """
        Main virtual try-on workflow.

        Steps:
        1. Check limits (user or device)
        2. Preprocess images
        3. Generate public URLs
        4. Call NanoBanana API
        5. Save results
        6. Send Telegram notification
        7. Increment limits
        8. Record generation

        Returns: {
            'success': bool,
            'results': List[{
                'original': str,
                'result_path': str,
                'result_image': str (base64),
                'result_url': str,
                'result_filename': str
            }],
            'daily_limit': Dict,
            'anonymous_limit': Dict (if not authenticated)
        }

        Raises:
            LimitExceededError: If limits exceeded
            ProcessingError: If NanoBanana fails
        """

    def _process_single_image(self, person_image: str, garment_image: str,
                             category: str, user_id: Optional[int],
                             device_fingerprint: str) -> Dict:
        """Process single person image through pipeline."""

    def _handle_processing_error(self, error: Exception, generation_id: int):
        """Update generation status to failed and log error."""
```

**Migration from app.py:**
- Lines 1131-1384: `/api/tryon` route logic
- Orchestrates all other services
- Clear separation: no HTTP concerns

---

### 3.5 `services/feedback_service.py`

```python
class FeedbackService:
    """Manages feedback collection and Telegram integration."""

    def __init__(self, feedback_repo: FeedbackRepository,
                notification_service: NotificationService):
        self.feedback_repo = feedback_repo
        self.notifications = notification_service
        self.logger = get_logger(__name__)

    def submit_feedback(self, rating: int, comment: str,
                       session_id: Optional[str], ip_address: str) -> Dict:
        """
        Submit user feedback and notify via Telegram.

        Returns: {
            'success': bool,
            'feedback_id': int,
            'telegram_sent': bool
        }
        """

    def list_feedback(self, limit: int = 100) -> Dict:
        """Retrieve feedback list (admin)."""

    def configure_telegram_if_needed(self) -> Optional[str]:
        """Auto-configure Telegram chat ID if not set."""
```

**Migration from app.py:**
- Lines 1651-1977: Feedback endpoints
- Simplify complex feedback submission logic

---

### 3.6 `services/auth_service.py`

```python
class AuthService:
    """Authentication and user management service."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.logger = get_logger(__name__)

    def register(self, email: str, password: str, full_name: str) -> Dict:
        """
        Register new user.

        Returns: {
            'success': bool,
            'user': Dict,
            'token': str
        }

        Raises: ValidationError, UserExistsError
        """

    def login(self, email: str, password: str) -> Dict:
        """
        Authenticate user.

        Returns: Same as register
        Raises: AuthenticationError
        """

    def get_current_user(self, token: str) -> Optional[Dict]:
        """Validate token and return user info."""

    def check_user_limit(self, user_id: int) -> Dict:
        """Check user's daily generation limit."""
```

**Migration from app.py:**
- Lines 2052-2140: Auth endpoints
- Thin wrapper around UserRepository
- Adds validation layer

---

## 4. API ROUTES LAYER

### 4.1 `api/tryon.py`

```python
from flask import Blueprint, request, jsonify

tryon_bp = Blueprint('tryon', __name__, url_prefix='/api')

# Services injected via app context or factory
def init_routes(tryon_service, limit_service, auth_service):

    @tryon_bp.route('/check-device-limit', methods=['POST'])
    def check_device_limit():
        """Check anonymous device generation limit."""
        data = request.get_json()
        # Parse request
        # Call limit_service.check_device_limit()
        # Return JSON

    @tryon_bp.route('/increment-device-limit', methods=['POST'])
    def increment_device_limit():
        """Increment device limit counter."""
        # Similar structure

    @tryon_bp.route('/tryon', methods=['POST'])
    @limiter.limit("10 per hour")
    def virtual_tryon():
        """Main virtual try-on endpoint."""
        # 1. Parse JSON request
        # 2. Extract optional auth token
        # 3. Get user_id from auth_service if authenticated
        # 4. Call tryon_service.process_tryon()
        # 5. Return formatted response
        # 6. Handle errors (400, 429, 500)

    @tryon_bp.route('/result/<filename>', methods=['GET'])
    def get_result(filename):
        """Serve generated result image."""
        # Validate filename
        # Send file with proper headers

    return tryon_bp
```

**Rules**:
- Maximum 30-40 lines per route
- No business logic
- Clear error handling
- Pydantic validation for requests

---

### 4.2 `api/auth.py`

```python
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def init_routes(auth_service, limit_service):

    @auth_bp.route('/register', methods=['POST'])
    @limiter.limit("5 per hour")
    def register():
        """Register new user."""

    @auth_bp.route('/login', methods=['POST'])
    @limiter.limit("10 per hour")
    def login():
        """Login user."""

    @auth_bp.route('/me', methods=['GET'])
    @require_auth
    def get_current_user():
        """Get current user profile."""

    @auth_bp.route('/check-limit', methods=['GET'])
    @require_auth
    def check_limit():
        """Check user's daily limit."""

    return auth_bp
```

---

### 4.3 `api/admin.py`

```python
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def init_routes(user_repo, generation_repo):

    @admin_bp.route('/users', methods=['GET'])
    @require_admin
    def list_users():
        """List all users with stats."""

    @admin_bp.route('/users/<int:user_id>/premium', methods=['POST'])
    @require_admin
    def toggle_premium(user_id):
        """Toggle user premium status."""

    @admin_bp.route('/generations', methods=['GET'])
    @require_admin
    def list_generations():
        """List all generations with filtering."""

    @admin_bp.route('/stats', methods=['GET'])
    @require_admin
    def get_stats():
        """Get system statistics."""

    return admin_bp
```

---

### 4.4 `api/feedback.py`

```python
from flask import Blueprint

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

def init_routes(feedback_service):

    @feedback_bp.route('', methods=['POST'])
    @limiter.limit("20 per hour")
    def submit_feedback():
        """Submit user feedback."""

    @feedback_bp.route('/list', methods=['GET'])
    def list_feedback():
        """List all feedback (admin or public)."""

    return feedback_bp
```

---

### 4.5 `api/static.py`

```python
from flask import Blueprint, send_from_directory, send_file

static_bp = Blueprint('static', __name__)

def init_routes(upload_folder, frontend_folder):

    @static_bp.route('/')
    def serve_frontend():
        """Serve index.html."""

    @static_bp.route('/<path:path>')
    def serve_static(path):
        """Serve static assets."""

    @static_bp.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""

    @static_bp.route('/uploads/<path:filename>', methods=['GET'])
    def serve_upload(filename):
        """Serve uploaded images."""

    @static_bp.route('/api/cleanup', methods=['POST'])
    def cleanup():
        """Manual file cleanup trigger."""

    return static_bp
```

---

## 5. APP FACTORY

### 5.1 `app.py` (Refactored)

```python
"""
Flask application factory for Virtual Try-On service.
"""

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.config import get_settings
from backend.logger import get_logger
from backend.database import db_available, init_database
from backend.auth import AuthManager

# Import repositories
from backend.repositories.device_limit_repository import DeviceLimitRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.generation_repository import GenerationRepository
from backend.repositories.feedback_repository import FeedbackRepository

# Import clients
from backend.clients.nanobanana_client import NanoBananaClient
from backend.clients.telegram_client import TelegramClient

# Import services
from backend.services.image_service import ImageService
from backend.services.limit_service import LimitService
from backend.services.notification_service import NotificationService
from backend.services.tryon_service import TryonService
from backend.services.feedback_service import FeedbackService
from backend.services.auth_service import AuthService

# Import API routes
from backend.api import tryon, auth, admin, feedback, static

logger = get_logger(__name__)


def create_app(config_override=None):
    """
    Application factory function.

    Args:
        config_override: Optional dict to override settings (for testing)

    Returns:
        Flask app instance
    """
    app = Flask(__name__)

    # Load configuration
    settings = get_settings()
    if config_override:
        for key, value in config_override.items():
            setattr(settings, key, value)

    # Configure Flask
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = './uploads'
    app.config['RESULTS_FOLDER'] = './results'
    app.config['FEEDBACK_FOLDER'] = './feedback'

    # Initialize extensions
    CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"])

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per hour", "50 per minute"],
        storage_uri="memory://"
    )

    # Initialize database
    engine, SessionLocal, db_available = init_database()

    # Initialize components (Dependency Injection)

    # 1. Repositories
    device_limit_repo = DeviceLimitRepository(db_connection=engine)
    auth_manager = AuthManager(db_connection=engine) if db_available else None
    user_repo = UserRepository(auth_manager=auth_manager) if auth_manager else None
    generation_repo = GenerationRepository(db_connection=engine)
    feedback_repo = FeedbackRepository(
        db_connection=engine,
        feedback_folder=app.config['FEEDBACK_FOLDER']
    )

    # 2. Clients
    nanobanana_client = NanoBananaClient(api_key=settings.nanobanana_api_key)
    telegram_client = TelegramClient(
        bot_token=settings.telegram_bot_token,
        default_chat_id=settings.telegram_chat_id
    ) if settings.telegram_bot_token else None

    # 3. Services
    image_service = ImageService(
        upload_folder=app.config['UPLOAD_FOLDER'],
        results_folder=app.config['RESULTS_FOLDER']
    )

    limit_service = LimitService(
        device_repo=device_limit_repo,
        user_repo=user_repo,
        free_device_limit=3
    )

    notification_service = NotificationService(
        telegram_client=telegram_client,
        feedback_repo=feedback_repo
    ) if telegram_client else None

    tryon_service = TryonService(
        image_service=image_service,
        nanobanana_client=nanobanana_client,
        notification_service=notification_service,
        limit_service=limit_service,
        generation_repo=generation_repo,
        results_folder=app.config['RESULTS_FOLDER']
    )

    feedback_service = FeedbackService(
        feedback_repo=feedback_repo,
        notification_service=notification_service
    )

    auth_service = AuthService(user_repo=user_repo) if user_repo else None

    # Register blueprints
    app.register_blueprint(
        tryon.init_routes(tryon_service, limit_service, auth_service)
    )
    app.register_blueprint(
        auth.init_routes(auth_service, limit_service)
    )
    app.register_blueprint(
        admin.init_routes(user_repo, generation_repo)
    )
    app.register_blueprint(
        feedback.init_routes(feedback_service)
    )
    app.register_blueprint(
        static.init_routes(
            upload_folder=app.config['UPLOAD_FOLDER'],
            frontend_folder='./frontend'
        )
    )

    # Start background cleanup scheduler
    from backend.utils.file_helpers import start_cleanup_scheduler
    start_cleanup_scheduler(
        upload_folder=app.config['UPLOAD_FOLDER'],
        results_folder=app.config['RESULTS_FOLDER']
    )

    logger.info(f"Flask app initialized successfully")
    logger.info(f"Database available: {db_available}")
    logger.info(f"Telegram configured: {telegram_client is not None}")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Key Benefits**:
- Testable: Can create app with mock dependencies
- Clear initialization order
- All dependencies injected explicitly
- No global state except app factory
- Easy to extend with new services

---

## MIGRATION STRATEGY

### Phase 1: Infrastructure (Low Risk)
1. Create directory structure
2. Move utilities to `utils/`
3. Create base repository classes (no logic changes)
4. **Test**: Import checks, linting

### Phase 2: Data Layer (Medium Risk)
1. Implement `DeviceLimitRepository`
2. Implement `UserRepository` (wrap AuthManager)
3. Implement `GenerationRepository`
4. Implement `FeedbackRepository`
5. **Test**: Each repository with unit tests

### Phase 3: External Integrations (Medium Risk)
1. Implement `NanoBananaClient`
2. Implement `TelegramClient`
3. **Test**: Mock API calls, verify retry logic

### Phase 4: Business Logic (High Risk)
1. Implement `ImageService`
2. Implement `LimitService`
3. Implement `NotificationService`
4. Implement `FeedbackService`
5. Implement `AuthService`
6. Implement `TryonService` (orchestrator)
7. **Test**: Service integration tests

### Phase 5: API Routes (Critical)
1. Implement `api/static.py` (low risk)
2. Implement `api/feedback.py`
3. Implement `api/auth.py`
4. Implement `api/admin.py`
5. Implement `api/tryon.py` (most critical)
6. **Test**: API endpoint tests with Postman/curl

### Phase 6: Factory (Final)
1. Refactor `app.py` to factory pattern
2. Wire all dependencies
3. Remove old code from `app.py`
4. **Test**: Full integration test, smoke tests

### Phase 7: Verification
1. Run full test suite
2. Check CI/CD pipeline
3. Deploy to Railway
4. Monitor logs
5. Verify all features work

---

## SUCCESS CRITERIA

- ✅ All 23 API endpoints work identically to before
- ✅ CI/CD pipeline passes (flake8, black, isort, mypy)
- ✅ No regression in functionality
- ✅ app.py reduced to < 200 lines
- ✅ Each module < 300 lines
- ✅ Clear separation of concerns
- ✅ Testable architecture
- ✅ Railway deployment successful
- ✅ Logs show proper structured logging

---

## RISK MITIGATION

1. **Keep old app.py**: Rename to `app_legacy.py` until fully verified
2. **Feature flags**: Can switch back to old implementation if issues
3. **Incremental deployment**: Test each phase locally before committing
4. **Comprehensive logging**: Add detailed logs during migration
5. **Rollback plan**: Git tags for each migration phase

---

END OF SPECIFICATION
