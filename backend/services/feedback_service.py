"""Feedback collection and notification service."""

from typing import Dict, List, Optional

from backend.logger import get_logger
from backend.repositories.feedback_repository import FeedbackRepository
from backend.services.notification_service import NotificationService

logger = get_logger(__name__)


class FeedbackService:
    """
    Service for managing user feedback collection.

    Responsibilities:
    - Validate and save feedback (rating + comment)
    - Send Telegram notifications for new feedback
    - Retrieve feedback list
    - Auto-configure Telegram if needed

    Orchestrates FeedbackRepository and NotificationService.
    """

    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        notification_service: Optional[NotificationService] = None,
    ):
        """
        Initialize feedback service.

        Args:
            feedback_repo: FeedbackRepository for persistence
            notification_service: Optional NotificationService for alerts
        """
        self.feedback_repo = feedback_repo
        self.notification_service = notification_service
        self.logger = get_logger(__name__)

    def submit_feedback(
        self, rating: int, comment: str, session_id: Optional[str], ip_address: str
    ) -> Dict[str, any]:
        """
        Submit and save user feedback.

        Workflow:
        1. Validate rating (1-5)
        2. Save to database/file (via FeedbackRepository)
        3. Send Telegram notification (if configured)
        4. Update database with Telegram status

        Args:
            rating: Rating (1-5)
            comment: User comment text
            session_id: Session identifier (optional)
            ip_address: Client IP address

        Returns:
            Dictionary with submission result:
            {
                'success': bool,
                'message': str,
                'feedback_id': int or None,
                'saved_to': 'database' or 'files',
                'db_saved': bool,
                'telegram_sent': bool (if configured),
                'telegram_error': str (if failed)
            }

        Raises:
            ValueError: If rating is invalid
        """
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValueError(f"Invalid rating. Must be integer 1-5, got: {rating}")

        # Normalize empty comments
        if not comment or not comment.strip():
            comment = "[Без комментария]"

        self.logger.info(f"Submitting feedback: rating={rating}/5, comment_length={len(comment)}")

        # Save feedback (with telegram_sent=False initially)
        feedback_record = self.feedback_repo.save(
            rating=rating, comment=comment, session_id=session_id, ip_address=ip_address, telegram_sent=False
        )

        feedback_id = feedback_record.get("id")
        db_saved = feedback_record.get("db_saved", False)

        self.logger.info(
            f"Feedback saved: id={feedback_id}, db_saved={db_saved}, file_path={feedback_record.get('file_path')}"
        )

        # Try to send Telegram notification
        telegram_sent = False
        telegram_error = None

        if self.notification_service and self.notification_service.is_enabled():
            self.logger.info("Sending Telegram notification for feedback...")

            success, error = self.notification_service.send_feedback_notification(
                rating=rating, comment=comment, session_id=session_id, max_retries=3
            )

            telegram_sent = success
            telegram_error = error

            # Update database with Telegram status
            if feedback_id:
                try:
                    self.feedback_repo.mark_telegram_sent(feedback_id, success, error)
                    self.logger.info(f"Updated Telegram status for feedback {feedback_id}: sent={success}")
                except Exception as e:
                    self.logger.error(f"Failed to update Telegram status: {e}")

            if success:
                self.logger.info("Telegram notification sent successfully")
            else:
                self.logger.warning(f"Telegram notification failed: {error}")
        else:
            self.logger.info("Telegram notifications not configured - skipping")

        # Build response
        response = {
            "success": True,
            "message": "Feedback saved successfully",
            "feedback_id": feedback_id,
            "saved_to": "database" if db_saved else "files",
            "db_saved": db_saved,
        }

        # Add Telegram status if attempted
        if self.notification_service and self.notification_service.is_enabled():
            response["telegram_sent"] = telegram_sent
            if not telegram_sent:
                response["telegram_error"] = telegram_error

        return response

    def list_feedback(self, limit: int = 100) -> Dict[str, any]:
        """
        Retrieve all feedback.

        Args:
            limit: Maximum number of records (default: 100)

        Returns:
            Dictionary with feedback list:
            {
                'source': 'database' or 'files',
                'count': int,
                'feedback': List[Dict]
            }
        """
        self.logger.info(f"Retrieving feedback list (limit={limit})...")

        result = self.feedback_repo.list_all(limit)

        self.logger.info(f"Retrieved {result['count']} feedback records from {result['source']}")

        return result

    def configure_telegram_if_needed(self) -> Optional[str]:
        """
        Auto-configure Telegram chat ID if not already set.

        Only runs if NotificationService is available but chat ID is missing.

        Returns:
            Detected chat ID or None
        """
        if not self.notification_service:
            self.logger.warning("Notification service not available - cannot configure Telegram")
            return None

        if not self.notification_service.is_enabled():
            self.logger.warning("Telegram client not configured - cannot auto-configure")
            return None

        # Check if chat ID is already set
        if self.notification_service.telegram_client.default_chat_id:
            self.logger.info("Telegram chat ID already configured")
            return self.notification_service.telegram_client.default_chat_id

        # Try to auto-detect
        self.logger.info("Attempting to auto-configure Telegram chat ID...")
        chat_id = self.notification_service.auto_configure_chat_id()

        if chat_id:
            self.logger.info(f"Successfully configured Telegram chat ID: {chat_id}")
        else:
            self.logger.warning("Could not auto-configure Telegram chat ID")

        return chat_id

    def parse_rating(self, rating_value: any) -> int:
        """
        Parse rating value from various input formats.

        Handles:
        - Integer: 1-5
        - String: "1" - "5"
        - List: [1] or ["1"]

        Args:
            rating_value: Rating in any format

        Returns:
            Validated rating integer (1-5)

        Raises:
            ValueError: If rating cannot be parsed or is out of range
        """
        try:
            # If rating is a list, take first element
            if isinstance(rating_value, list) and len(rating_value) > 0:
                rating_value = rating_value[0]

            # If rating is a string, convert to int
            if isinstance(rating_value, str):
                rating_value = int(rating_value.strip())

            # Ensure it's an int
            if not isinstance(rating_value, int):
                rating_value = int(rating_value)

            # Validate range
            if rating_value < 1 or rating_value > 5:
                raise ValueError(f"Rating must be 1-5, got: {rating_value}")

            return rating_value

        except (ValueError, TypeError, IndexError) as e:
            self.logger.error(f"Failed to parse rating: {e}, received: {rating_value}, type: {type(rating_value)}")
            raise ValueError(f"Invalid rating format: {rating_value}")

    def get_unsent_telegram_count(self) -> int:
        """
        Get count of feedback not yet sent to Telegram.

        Returns:
            Number of unsent feedback records
        """
        try:
            unsent = self.feedback_repo.get_unsent_telegram()
            count = len(unsent)
            self.logger.info(f"Found {count} unsent Telegram feedback notifications")
            return count
        except Exception as e:
            self.logger.error(f"Failed to count unsent Telegram feedback: {e}")
            return 0

    def retry_failed_telegram_notifications(self) -> Dict[str, any]:
        """
        Retry sending Telegram notifications for failed feedback.

        Delegates to NotificationService.

        Returns:
            Dictionary with retry results:
            {
                'attempted': int,
                'succeeded': int,
                'failed': int,
                'errors': List[str]
            }
        """
        if not self.notification_service:
            self.logger.warning("Notification service not available - cannot retry failed notifications")
            return {"attempted": 0, "succeeded": 0, "failed": 0, "errors": ["Notification service not available"]}

        self.logger.info("Retrying failed Telegram notifications...")

        result = self.notification_service.retry_failed_feedbacks(max_retries=3)

        self.logger.info(
            f"Retry complete: {result['succeeded']} succeeded, {result['failed']} failed "
            f"out of {result['attempted']} attempted"
        )

        return result
