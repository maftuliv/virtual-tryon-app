"""Virtual try-on orchestration service."""

import os
from typing import Dict, List, Optional

from flask import Request

from backend.clients.nanobanana_client import NanoBananaClient
from backend.clients.r2_storage_client import r2_storage
from backend.logger import get_logger
from backend.repositories.generation_repository import GenerationRepository
from backend.services.image_service import ImageService
from backend.services.limit_service import LimitService
from backend.services.notification_service import NotificationService

logger = get_logger(__name__)


class TryonService:
    """
    Service for orchestrating virtual try-on generation.

    Most complex service - coordinates all aspects of try-on workflow:
    - Limit checking (device or user)
    - Image preprocessing
    - NanoBanana API calls
    - Result processing
    - Limit incrementing
    - Telegram notifications
    - Generation tracking

    Orchestrates: ImageService, LimitService, NanoBananaClient,
                 NotificationService, GenerationRepository
    """

    def __init__(
        self,
        nanobanana_client: NanoBananaClient,
        image_service: ImageService,
        limit_service: LimitService,
        result_folder: str,
        notification_service: Optional[NotificationService] = None,
        generation_repo: Optional[GenerationRepository] = None,
    ):
        """
        Initialize try-on service.

        Args:
            nanobanana_client: NanoBananaClient for AI generation
            image_service: ImageService for image processing
            limit_service: LimitService for limit checking/incrementing
            result_folder: Path to result images folder
            notification_service: Optional NotificationService for alerts
            generation_repo: Optional GenerationRepository for tracking
        """
        self.nanobanana_client = nanobanana_client
        self.image_service = image_service
        self.limit_service = limit_service
        self.notification_service = notification_service
        self.generation_repo = generation_repo
        self.result_folder = result_folder
        self.logger = get_logger(__name__)

    def process_tryon(
        self,
        person_images: List[str],
        garment_image: str,
        garment_category: str = "auto",
        user_id: Optional[int] = None,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_obj: Optional[Request] = None,
    ) -> Dict:
        """
        Process virtual try-on for multiple person images.

        Complete workflow:
        1. Check limits (device or user)
        2. Validate inputs
        3. Process each person image:
           - Preprocess images
           - Generate public URLs
           - Call NanoBanana API
           - Process result
           - Send Telegram notification
        4. Increment limits
        5. Track generation
        6. Return results

        Args:
            person_images: List of person image paths
            garment_image: Garment image path
            garment_category: Category ("auto", "tops", "bottoms", "one-pieces")
            user_id: User ID (authenticated) or None (anonymous)
            device_fingerprint: Browser fingerprint (for anonymous)
            ip_address: Client IP address (for anonymous)
            user_agent: Browser user agent (for anonymous)
            request_obj: Flask request object (for URL generation)

        Returns:
            Dictionary with results:
            {
                'success': bool,
                'results': List[Dict],  # One per person image
                'daily_limit': Dict,    # Updated limit status
                'anonymous_limit': Dict (if anonymous)
            }

        Raises:
            ValueError: If validation fails or limit exceeded
        """
        self.logger.info(
            f"Starting try-on: {len(person_images)} person images, "
            f"category={garment_category}, "
            f"user_id={user_id if user_id else 'anonymous'}"
        )

        # 1. Check limits BEFORE processing
        limit_status = self.limit_service.can_generate(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not limit_status["can_generate"]:
            user_type = "authenticated" if user_id else "anonymous"
            error_msg = (
                f"Вы исчерпали недельный лимит генераций ({limit_status['limit']}/неделю). "
                f"{'Перейдите на Premium для безлимитного доступа!' if user_type == 'authenticated' else 'Зарегистрируйтесь, чтобы продолжить.'}"
            )

            raise ValueError(
                f"LIMIT_EXCEEDED: {error_msg} "
                f"(used={limit_status['used']}, limit={limit_status['limit']})"
            )

        self.logger.info(
            f"Limit check passed: {limit_status['used']}/{limit_status['limit']} used, "
            f"user_type={limit_status.get('user_type', 'unknown')}"
        )

        # 2. Validate inputs
        if not person_images or not garment_image:
            raise ValueError("Person images and garment image are required")

        if not os.path.exists(garment_image):
            raise ValueError(f"Garment image not found: {garment_image}")

        # Filter out non-existent person images
        valid_person_images = [p for p in person_images if os.path.exists(p)]

        if not valid_person_images:
            raise ValueError("No valid person images found")

        self.logger.info(f"Validated inputs: {len(valid_person_images)} person images, garment image OK")

        # 3. Process each person image
        results = []

        for person_image in valid_person_images:
            try:
                result = self._process_single_image(
                    person_image=person_image,
                    garment_image=garment_image,
                    garment_category=garment_category,
                    request_obj=request_obj,
                    ip_address=ip_address,
                )
                results.append(result)

                self.logger.info(f"Successfully processed: {os.path.basename(person_image)}")

            except Exception as e:
                error_result = self._handle_processing_error(person_image, e)
                results.append(error_result)

        # 4. Increment limits (only if at least one success)
        successful_results = [r for r in results if "error" not in r]

        if successful_results:
            try:
                updated_limit = self.limit_service.increment_limit(
                    user_id=user_id,
                    device_fingerprint=device_fingerprint,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    increment=1,  # Increment by 1 regardless of how many person images
                )

                self.logger.info(
                    f"Limit incremented: {updated_limit['used']}/{updated_limit['limit']}, "
                    f"remaining={updated_limit['remaining']}"
                )

            except Exception as e:
                self.logger.warning(f"Failed to increment limit: {e}")
                # Don't fail the request if limit increment fails
                updated_limit = limit_status
        else:
            # No successful results - don't increment
            updated_limit = limit_status

        # 5. Track generation (optional) and upload to R2
        if self.generation_repo and successful_results:
            try:
                for result in successful_results:
                    # Create generation record first
                    generation_record = self.generation_repo.create(
                        user_id=user_id,
                        device_fingerprint=device_fingerprint,
                        category=garment_category,
                        person_image_url=result.get("original", "unknown"),
                        garment_image_url=os.path.basename(garment_image),
                        result_image_url=result.get("result_url"),
                        status="completed",
                    )

                    # Add generation ID to result for frontend
                    result['generation_id'] = generation_record['id']

                    # Upload to R2 if configured and user is logged in
                    self.logger.info(f"[R2-CHECK] user_id={user_id}, r2_configured={r2_storage.is_configured()}")
                    if user_id and r2_storage.is_configured():
                        r2_key_to_cleanup = None
                        try:
                            result_path = result.get("result_path")
                            if result_path and os.path.exists(result_path):
                                with open(result_path, 'rb') as f:
                                    image_data = f.read()

                                r2_result = r2_storage.upload_tryon_result(
                                    image_data=image_data,
                                    user_id=user_id,
                                    generation_id=generation_record['id']
                                )

                                # Save key for cleanup in case DB update fails
                                r2_key_to_cleanup = r2_result['key']

                                # Update generation with R2 info
                                db_updated = self.generation_repo.update_r2_storage(
                                    generation_id=generation_record['id'],
                                    r2_key=r2_result['key'],
                                    r2_url=r2_result['url'],
                                    upload_size=r2_result.get('size')
                                )

                                if not db_updated:
                                    raise Exception("Database update failed after R2 upload")

                                # Clear cleanup flag on success
                                r2_key_to_cleanup = None

                                # Add R2 URL to result
                                result['r2_url'] = r2_result['url']

                                self.logger.info(
                                    f"Uploaded to R2: {r2_result['url']} "
                                    f"({r2_result.get('size', 0)} bytes)"
                                )
                        except Exception as e:
                            self.logger.warning(f"Failed to upload to R2: {e}")
                            # Cleanup orphaned R2 file if upload succeeded but DB failed
                            if r2_key_to_cleanup:
                                try:
                                    r2_storage.delete_image(r2_key_to_cleanup)
                                    self.logger.info(f"Cleaned up orphaned R2 file: {r2_key_to_cleanup}")
                                except Exception as cleanup_error:
                                    self.logger.error(f"Failed to cleanup R2 file {r2_key_to_cleanup}: {cleanup_error}")
                            # Don't fail the request if R2 upload fails

                self.logger.info(f"Tracked {len(successful_results)} generations in database")
            except Exception as e:
                self.logger.error(f"Failed to track generation: {e}")

        # 6. Build response
        response = {
            "success": True,
            "results": results,
            "daily_limit": updated_limit,
        }

        # Add anonymous_limit for backwards compatibility
        if not user_id:
            response["anonymous_limit"] = updated_limit

        self.logger.info(
            f"Try-on complete: {len(successful_results)} successful, "
            f"{len(results) - len(successful_results)} failed"
        )

        return response

    def _process_single_image(
        self,
        person_image: str,
        garment_image: str,
        garment_category: str,
        request_obj: Optional[Request],
        ip_address: Optional[str],
    ) -> Dict:
        """
        Process a single person image with garment.

        Args:
            person_image: Person image path
            garment_image: Garment image path
            garment_category: Garment category
            request_obj: Flask request object (for URL generation)
            ip_address: Client IP address (for Telegram caption)

        Returns:
            Result dictionary:
            {
                'original': str,        # Original filename
                'result_path': str,     # Path to result image
                'result_image': str,    # Base64 data URL
                'result_url': str,      # Public URL
                'result_filename': str  # Result filename
            }

        Raises:
            Exception: If processing fails
        """
        self.logger.info(f"Processing image: {os.path.basename(person_image)}")

        # Preprocess images
        person_optimized = self.image_service.preprocess_image(person_image, max_dimension=2000, quality=95)
        garment_optimized = self.image_service.preprocess_image(garment_image, max_dimension=2000, quality=95)

        # Generate public URLs
        person_url = self.image_service.generate_public_url(person_optimized, request_obj)
        garment_url = self.image_service.generate_public_url(garment_optimized, request_obj)

        self.logger.info(f"Generated URLs: person={person_url}, garment={garment_url}")

        # Generate result filename
        import time

        timestamp = int(time.time())
        result_filename = f"result_{timestamp}_{os.path.basename(person_image)}"
        result_path = os.path.join(self.result_folder, result_filename)

        # Call NanoBanana API
        self.logger.info("Calling NanoBanana API...")

        nanobanana_result = self.nanobanana_client.generate_tryon(
            person_image_url=person_url,
            garment_image_url=garment_url,
            category=garment_category,
            output_path=result_path,
        )

        self.logger.info(
            f"NanoBanana result: task_id={nanobanana_result['task_id']}, "
            f"processing_time={nanobanana_result['processing_time']:.2f}s, "
            f"size={nanobanana_result.get('width')}x{nanobanana_result.get('height')}"
        )

        # Generate result URL
        result_url = self.image_service.generate_public_url(result_path, request_obj)

        # Convert result to base64 for frontend
        result_base64 = self.image_service.image_to_base64(result_path)

        # Send Telegram notification (if configured)
        if self.notification_service and self.notification_service.is_enabled():
            try:
                from datetime import datetime

                caption = f"🎨 <b>Новый результат примерки</b>\n\n"
                caption += f"📸 Оригинал: {os.path.basename(person_image)}\n"
                caption += f"👕 Категория: {garment_category}\n"
                caption += f"🌐 IP: {ip_address or 'Unknown'}\n"
                caption += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                success, error = self.notification_service.send_result_notification(
                    result_image_path=result_path, caption=caption, max_retries=3
                )

                if success:
                    self.logger.info("Telegram result notification sent")
                else:
                    self.logger.warning(f"Telegram notification failed: {error}")

            except Exception as e:
                self.logger.warning(f"Error sending Telegram notification: {e}")
                # Don't fail the request if Telegram send fails

        # Return result
        return {
            "original": os.path.basename(person_image),
            "result_path": result_path,
            "result_image": f"data:image/png;base64,{result_base64}",
            "result_url": result_url,
            "result_filename": result_filename,
        }

    def _handle_processing_error(self, person_image: str, error: Exception) -> Dict:
        """
        Handle processing error for a single image.

        Args:
            person_image: Person image path that failed
            error: Exception that occurred

        Returns:
            Error result dictionary:
            {
                'original': str,
                'error': str
            }
        """
        error_msg = str(error)
        self.logger.error(f"Error processing {person_image}: {error_msg}", exc_info=True)

        return {"original": os.path.basename(person_image), "error": error_msg}
