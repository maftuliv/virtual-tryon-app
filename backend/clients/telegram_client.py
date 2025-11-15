"""Telegram Bot API client with retry logic."""

import os
import time
from typing import Callable, Dict, List, Optional, Tuple

import requests

from backend.logger import get_logger

logger = get_logger(__name__)


class TelegramClient:
    """
    Telegram Bot API client with automatic retry and error handling.

    Features:
    - Exponential backoff retry mechanism
    - Comprehensive error logging
    - Message and photo sending
    - Bot info and updates retrieval
    - Auto-detection of chat ID from messages
    """

    BASE_URL = "https://api.telegram.org"

    def __init__(self, bot_token: str, default_chat_id: Optional[str] = None):
        """
        Initialize Telegram client.

        Args:
            bot_token: Telegram bot API token (from @BotFather)
            default_chat_id: Default chat ID for messages (optional)
        """
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.logger = get_logger(__name__)

    def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        max_retries: int = 3,
    ) -> Tuple[bool, Optional[str]]:
        """
        Send text message with retry.

        Args:
            text: Message text
            chat_id: Chat ID (uses default if not provided)
            parse_mode: Parse mode (HTML or Markdown)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Tuple of (success: bool, error_message: str or None)

        Example:
            >>> client = TelegramClient(bot_token="...", default_chat_id="123")
            >>> success, error = client.send_message("Hello!")
            >>> if success:
            ...     print("Message sent successfully")
        """
        chat_id = chat_id or self.default_chat_id
        if not chat_id:
            return False, "No chat_id provided and no default chat_id set"

        # Parse chat_id to int if possible
        try:
            chat_id_int = int(chat_id)
        except (ValueError, TypeError):
            chat_id_int = chat_id

        url = f"{self.BASE_URL}/bot{self.bot_token}/sendMessage"
        data = {"chat_id": chat_id_int, "text": text, "parse_mode": parse_mode}

        def send_request():
            response = requests.post(url, json=data, timeout=10)
            return self._handle_response(response, "message")

        return self._retry_with_backoff(send_request, max_retries, operation="send_message")

    def send_photo(
        self,
        photo_path: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        max_retries: int = 3,
    ) -> Tuple[bool, Optional[str]]:
        """
        Send photo with optional caption and retry.

        Args:
            photo_path: Path to photo file
            caption: Optional caption text
            chat_id: Chat ID (uses default if not provided)
            parse_mode: Parse mode for caption (HTML or Markdown)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Tuple of (success: bool, error_message: str or None)

        Raises:
            FileNotFoundError: If photo file doesn't exist
        """
        chat_id = chat_id or self.default_chat_id
        if not chat_id:
            return False, "No chat_id provided and no default chat_id set"

        # Check if file exists
        if not os.path.exists(photo_path):
            error_msg = f"Photo file not found: {photo_path}"
            self.logger.error(error_msg)
            return False, error_msg

        # Parse chat_id to int if possible
        try:
            chat_id_int = int(chat_id)
        except (ValueError, TypeError):
            chat_id_int = chat_id

        url = f"{self.BASE_URL}/bot{self.bot_token}/sendPhoto"

        def send_request():
            with open(photo_path, "rb") as photo_file:
                files = {"photo": (os.path.basename(photo_path), photo_file, "image/png")}
                data = {"chat_id": chat_id_int}

                if caption:
                    data["caption"] = caption
                    data["parse_mode"] = parse_mode

                response = requests.post(url, files=files, data=data, timeout=30)

            return self._handle_response(response, "photo")

        return self._retry_with_backoff(send_request, max_retries, operation="send_photo")

    def get_bot_info(self) -> Optional[Dict]:
        """
        Get bot information using /getMe endpoint.

        Returns:
            Bot info dictionary or None if request fails

        Example:
            >>> bot_info = client.get_bot_info()
            >>> if bot_info:
            ...     print(f"Bot username: @{bot_info['username']}")
        """
        url = f"{self.BASE_URL}/bot{self.bot_token}/getMe"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result")

            self.logger.error(f"Failed to get bot info: {response.text}")
            return None

        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}", exc_info=True)
            return None

    def get_updates(self, limit: int = 10) -> List[Dict]:
        """
        Get recent messages using /getUpdates endpoint.

        Args:
            limit: Maximum number of updates to retrieve (default: 10)

        Returns:
            List of update dictionaries

        Example:
            >>> updates = client.get_updates(limit=5)
            >>> for update in updates:
            ...     print(f"Message from: {update['message']['from']['id']}")
        """
        url = f"{self.BASE_URL}/bot{self.bot_token}/getUpdates?limit={limit}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])

            self.logger.error(f"Failed to get updates: {response.text}")
            return []

        except Exception as e:
            self.logger.error(f"Error getting updates: {e}", exc_info=True)
            return []

    def auto_detect_chat_id(self) -> Optional[str]:
        """
        Auto-detect chat ID from recent bot messages.

        Looks through recent updates to find the most recent chat ID.

        Returns:
            Chat ID string or None if not found

        Example:
            >>> chat_id = client.auto_detect_chat_id()
            >>> if chat_id:
            ...     print(f"Detected chat ID: {chat_id}")
            ...     client.default_chat_id = chat_id
        """
        self.logger.info("Attempting to auto-detect Telegram chat ID...")

        # Verify bot token is valid
        bot_info = self.get_bot_info()
        if not bot_info:
            self.logger.error("Invalid bot token - cannot get bot info")
            return None

        self.logger.info(f"Bot verified: @{bot_info.get('username')}")

        # Get recent updates
        updates = self.get_updates(limit=10)

        if not updates:
            self.logger.warning("No recent messages found. Please send a message to the bot first.")
            return None

        # Extract chat ID from most recent message
        for update in reversed(updates):  # Most recent first
            message = update.get("message", {})
            chat = message.get("chat", {})
            chat_id = chat.get("id")

            if chat_id:
                self.logger.info(f"Detected chat ID: {chat_id}")
                return str(chat_id)

        self.logger.warning("No chat ID found in recent updates")
        return None

    def _handle_response(self, response: requests.Response, operation_type: str) -> Tuple[bool, Optional[str]]:
        """
        Handle Telegram API response.

        Args:
            response: requests.Response object
            operation_type: Type of operation ("message" or "photo")

        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                message_id = data.get("result", {}).get("message_id", "N/A")
                self.logger.info(f"Telegram {operation_type} sent successfully (msg_id: {message_id})")
                return True, None
            else:
                error_desc = data.get("description", "Unknown API error")
                self.logger.error(f"Telegram API error: {error_desc}")
                return False, f"Telegram API error: {error_desc}"
        else:
            # Try to parse error details
            try:
                error_data = response.json()
                error_desc = error_data.get("description", "Unknown")
                error_msg = f"HTTP {response.status_code}: {error_desc}"
            except:
                error_msg = f"HTTP {response.status_code}: {response.text[:100]}"

            self.logger.error(f"Telegram request failed: {error_msg}")
            return False, error_msg

    def _retry_with_backoff(
        self, func: Callable, max_retries: int, operation: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Generic retry mechanism with exponential backoff.

        Args:
            func: Function to execute (should return Tuple[bool, Optional[str]])
            max_retries: Maximum number of attempts
            operation: Operation name for logging

        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"[{operation}] Attempt {attempt}/{max_retries}")

                # Execute the function
                success, error = func()

                if success:
                    self.logger.info(f"[{operation}] SUCCESS on attempt {attempt}")
                    return True, None
                else:
                    last_error = error
                    self.logger.warning(f"[{operation}] FAILED on attempt {attempt}: {error}")

            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                self.logger.warning(f"[{operation}] Timeout on attempt {attempt}")

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)[:100]}"
                self.logger.warning(f"[{operation}] Connection error on attempt {attempt}: {e}")

            except Exception as e:
                last_error = f"Unexpected error: {str(e)[:100]}"
                self.logger.error(f"[{operation}] Unexpected error on attempt {attempt}: {e}", exc_info=True)

            # If this wasn't the last attempt, wait before retrying
            if attempt < max_retries:
                delay = 2 ** (attempt - 1)  # Exponential backoff: 1s, 2s, 4s
                self.logger.info(f"[{operation}] Retrying in {delay} seconds...")
                time.sleep(delay)

        # All retries failed
        self.logger.error(f"[{operation}] FAILED after {max_retries} attempts. Last error: {last_error}")
        return False, last_error
