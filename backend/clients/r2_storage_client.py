"""
Cloudflare R2 Storage Client
S3-compatible object storage for permanent image storage
"""
import boto3
from botocore.config import Config
import os
import uuid
import hashlib
from datetime import datetime

from backend.logger import get_logger

logger = get_logger(__name__)


class R2StorageClient:
    """Client for uploading and managing images in Cloudflare R2"""

    def __init__(self):
        self.access_key_id = os.getenv('R2_ACCESS_KEY_ID')
        self.secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY')
        self.endpoint_url = os.getenv('R2_ENDPOINT_URL')
        self.bucket_name = os.getenv('R2_BUCKET_NAME', 'taptolook')
        self.public_url_base = os.getenv('R2_PUBLIC_URL', 'https://pub-ff55d0b20eb2407da9bb491891732a84.r2.dev')

        self.client = None
        self._init_error = None
        if self.access_key_id and self.secret_access_key and self.endpoint_url:
            self._init_client()
            logger.info(f"[R2] Client initialized successfully. Bucket: {self.bucket_name}, Public URL: {self.public_url_base}")
        else:
            logger.warning(f"[R2] Client NOT configured. Missing: access_key={bool(self.access_key_id)}, secret={bool(self.secret_access_key)}, endpoint={bool(self.endpoint_url)}")

    def _init_client(self):
        """Initialize boto3 S3 client for R2"""
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                ),
                region_name='auto'  # R2 uses 'auto' as region
            )
            logger.info("[R2] Client initialized successfully")
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"[R2] CRITICAL: Failed to initialize client: {e}")

    def is_configured(self) -> bool:
        """Check if R2 is properly configured"""
        return self.client is not None

    def upload_image(self, image_data: bytes, user_id: int = None, image_type: str = 'result') -> dict:
        """
        Upload image to R2 storage

        Args:
            image_data: Image bytes
            user_id: Optional user ID for organizing files
            image_type: Type of image (result, person, garment)

        Returns:
            dict with 'key' (object key) and 'url' (public URL)
        """
        if not self.is_configured():
            raise Exception("R2 storage is not configured")

        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]

        # Organize by user and type
        if user_id:
            key = f"users/{user_id}/{image_type}/{timestamp}_{unique_id}.jpg"
        else:
            key = f"anonymous/{image_type}/{timestamp}_{unique_id}.jpg"

        # Upload to R2
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=image_data,
            ContentType='image/jpeg'
        )

        # Generate public URL
        public_url = f"{self.public_url_base.rstrip('/')}/{key}"

        return {
            'key': key,
            'url': public_url
        }

    def upload_tryon_result(self, image_data: bytes, user_id: int, generation_id: int = None) -> dict:
        """
        Upload try-on result image

        Args:
            image_data: Result image bytes
            user_id: User ID
            generation_id: Optional generation ID for reference

        Returns:
            dict with storage info
        """
        if not self.is_configured():
            logger.error(f"[R2] Cannot upload - client not configured (generation_id={generation_id})")
            raise Exception("R2 storage is not configured")

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]

        # Use hash of user_id for privacy (prevents enumeration)
        user_hash = hashlib.sha256(f"{user_id}_{self.access_key_id}".encode()).hexdigest()[:12]

        if generation_id:
            key = f"tryons/{user_hash}/{generation_id}_{timestamp}_{unique_id}.jpg"
        else:
            key = f"tryons/{user_hash}/{timestamp}_{unique_id}.jpg"

        try:
            logger.info(f"[R2] Uploading image for generation_id={generation_id}, size={len(image_data)} bytes")

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_data,
                ContentType='image/jpeg'
            )

            # Verify upload was successful
            head_response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )

            actual_size = head_response.get('ContentLength', 0)
            if actual_size != len(image_data):
                logger.error(f"[R2] Upload verification FAILED: expected {len(image_data)} bytes, got {actual_size}")
                raise Exception(f"Upload verification failed: size mismatch")

            logger.info(f"[R2] Upload verified successfully: {key}")

        except Exception as e:
            logger.error(f"[R2] Upload FAILED for generation_id={generation_id}: {e}")
            raise

        public_url = f"{self.public_url_base.rstrip('/')}/{key}"

        return {
            'key': key,
            'url': public_url,
            'bucket': self.bucket_name,
            'size': len(image_data)
        }

    def delete_image(self, key: str) -> bool:
        """
        Delete image from R2

        Args:
            key: Object key in bucket

        Returns:
            True if deleted successfully
        """
        if not self.is_configured():
            return False

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except Exception as e:
            print(f"[R2] Error deleting {key}: {e}")
            return False

    def get_public_url(self, key: str) -> str:
        """Get public URL for an object key"""
        return f"{self.public_url_base.rstrip('/')}/{key}"

    def list_user_tryons(self, user_id: int, limit: int = 50) -> list:
        """
        List all try-on results for a user

        Args:
            user_id: User ID
            limit: Max number of results

        Returns:
            List of objects with key and url
        """
        if not self.is_configured():
            return []

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"tryons/{user_id}/",
                MaxKeys=limit
            )

            results = []
            for obj in response.get('Contents', []):
                results.append({
                    'key': obj['Key'],
                    'url': self.get_public_url(obj['Key']),
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })

            return results
        except Exception as e:
            print(f"[R2] Error listing user tryons: {e}")
            return []


# Singleton instance
r2_storage = R2StorageClient()
