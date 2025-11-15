"""Notification service for Telegram alerts."""

from typing import List, Optional, Tuple

from backend.clients.telegram_client import TelegramClient
from backend.logger import get_logger
from backend.repositories.feedback_repository import FeedbackRepository

logger = get_logger(__name__)


class NotificationService:
    """
    Service for sending notifications via Telegram.

    Responsibilities:
    - Send result notifications (virtual try-on completed)
    - Send feedback notifications (new user feedback)
    - Retry failed notifications
    - Auto-configure chat ID

    Uses TelegramClient for API communication.
    Uses FeedbackRepository for tracking notification status.
    """

    def __init__(
        self,
        telegram_client: Optional[TelegramClient] = None,
        feedback_repo: Optional[FeedbackRepository] = None,
    ):
        """
        Initialize notification service.

        Args:
            telegram_client: TelegramClient instance (optional)
            feedback_repo: FeedbackRepository for tracking sent status (optional)
        """
        self.telegram_client = telegram_client
        self.feedback_repo = feedback_repo
        self.logger = get_logger(__name__)

    def is_enabled(self) -> bool:
        """
        Check if Telegram notifications are enabled.

        Returns:
            True if TelegramClient is configured, False otherwise
        """
        return self.telegram_client is not None

    def send_result_notification(
        self, result_image_path: str, caption: Optional[str] = None, max_retries: int = 3
    ) -> Tuple[bool, Optional[str]]:
        """
        Send virtual try-on result photo to Telegram.

        Args:
            result_image_path: Path to result image file
            caption: Optional caption text (HTML format supported)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not self.telegram_client:
            self.logger.warning("Telegram client not configured - skipping notification")
            return False, "Telegram client not configured"

        self.logger.info(f"Sending result notification with photo: {result_image_path}")

        success, error = self.telegram_client.send_photo(
            photo_path=result_image_path, caption=caption, max_retries=max_retries
        )

        if success:
            self.logger.info("Result notification sent successfully")
        else:
            self.logger.error(f"Result notification failed: {error}")

        return success, error

    def send_feedback_notification(
        self, rating: int, comment: str, session_id: Optional[str] = None, max_retries: int = 3
    ) -> Tuple[bool, Optional[str]]:
        """
        Send feedback notification to Telegram.

        Args:
            rating: Rating (1-5)
            comment: User comment text
            session_id: Session identifier (optional)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not self.telegram_client:
            self.logger.warning("Telegram client not configured - skipping feedback notification")
            return False, "Telegram client not configured"

        # Build feedback message
        stars = "⭐" * rating
        message = f"<b>Новый отзыв!</b>\n\n"
        message += f"Оценка: {stars} ({rating}/5)\n\n"
        message += f"Комментарий:\n{comment}\n\n"
        if session_id:
            message += f"Session ID: {session_id}"

        self.logger.info(f"Sending feedback notification: {rating}/5 stars")

        success, error = self.telegram_client.send_message(text=message, max_retries=max_retries)

        if success:
            self.logger.info("Feedback notification sent successfully")
        else:
            self.logger.error(f"Feedback notification failed: {error}")

        return success, error

    def retry_failed_feedbacks(self, max_retries: int = 3) -> dict:
        """
        Retry sending notifications for feedback that failed to send.

        Only works if FeedbackRepository is available.

        Args:
            max_retries: Maximum retry attempts per feedback (default: 3)

        Returns:
            Dictionary with retry results:
            {
                'attempted': int,
                'succeeded': int,
                'failed': int,
                'errors': List[str]
            }
        """
        if not self.feedback_repo:
            self.logger.warning("Feedback repository not available - cannot retry failed notifications")
            return {"attempted": 0, "succeeded": 0, "failed": 0, "errors": ["Feedback repository not available"]}

        if not self.telegram_client:
            self.logger.warning("Telegram client not configured - cannot retry notifications")
            return {"attempted": 0, "succeeded": 0, "failed": 0, "errors": ["Telegram client not configured"]}

        # Get unsent feedback
        unsent_feedbacks = self.feedback_repo.get_unsent_telegram()

        if not unsent_feedbacks:
            self.logger.info("No failed feedback notifications to retry")
            return {"attempted": 0, "succeeded": 0, "failed": 0, "errors": []}

        self.logger.info(f"Retrying {len(unsent_feedbacks)} failed feedback notifications...")

        attempted = 0
        succeeded = 0
        failed = 0
        errors = []

        for feedback in unsent_feedbacks:
            attempted += 1
            feedback_id = feedback["id"]
            rating = feedback["rating"]
            comment = feedback["comment"]
            session_id = feedback.get("session_id")

            # Try to send
            success, error = self.send_feedback_notification(
                rating=rating, comment=comment, session_id=session_id, max_retries=max_retries
            )

            # Update database
            try:
                self.feedback_repo.mark_telegram_sent(feedback_id, success, error)

                if success:
                    succeeded += 1
                else:
                    failed += 1
                    errors.append(f"Feedback {feedback_id}: {error}")
            except Exception as e:
                failed += 1
                error_msg = f"Feedback {feedback_id}: Failed to update database: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        self.logger.info(f"Retry complete: {succeeded} succeeded, {failed} failed out of {attempted} attempted")

        return {"attempted": attempted, "succeeded": succeeded, "failed": failed, "errors": errors}

    def auto_configure_chat_id(self) -> Optional[str]:
        """
        Auto-detect Telegram chat ID from recent bot messages.

        Requires that a user has sent at least one message to the bot.

        Returns:
            Detected chat ID or None if detection failed
        """
        if not self.telegram_client:
            self.logger.warning("Telegram client not configured - cannot auto-configure chat ID")
            return None

        self.logger.info("Attempting to auto-configure Telegram chat ID...")

        chat_id = self.telegram_client.auto_detect_chat_id()

        if chat_id:
            self.logger.info(f"Successfully detected chat ID: {chat_id}")
            # Update default chat ID in client
            self.telegram_client.default_chat_id = chat_id
        else:
            self.logger.warning("Could not auto-detect chat ID")

        return chat_id

    def send_test_notification(self) -> Tuple[bool, Optional[str]]:
        """
        Send test notification to verify configuration.

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not self.telegram_client:
            return False, "Telegram client not configured"

        test_message = "<b>Test Notification</b>\n\nTelegram notifications are working correctly!"

        self.logger.info("Sending test notification...")

        success, error = self.telegram_client.send_message(text=test_message, max_retries=1)

        if success:
            self.logger.info("Test notification sent successfully")
        else:
            self.logger.error(f"Test notification failed: {error}")

        return success, error
