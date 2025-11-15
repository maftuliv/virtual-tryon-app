"""File management utilities."""

import os
import threading
import time
from typing import List

from backend.logger import get_logger

logger = get_logger(__name__)


def cleanup_old_files(folders: List[str], max_age_seconds: int = 3600) -> int:
    """
    Remove files older than specified age from given folders.

    Args:
        folders: List of folder paths to clean
        max_age_seconds: Maximum file age in seconds (default: 1 hour)

    Returns:
        Number of files removed

    Example:
        >>> cleanup_old_files(['./uploads', './results'], max_age_seconds=3600)
        5
    """
    try:
        current_time = time.time()
        cleanup_count = 0

        for folder in folders:
            if not os.path.exists(folder):
                logger.warning(f"Cleanup folder does not exist: {folder}")
                continue

            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)

                if not os.path.isfile(file_path):
                    continue  # Skip directories

                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleanup_count += 1
                        logger.debug(f"Removed old file: {filename} (age: {file_age:.0f}s)")
                except Exception as e:
                    logger.error(f"Failed to remove {filename}: {e}")

        if cleanup_count > 0:
            logger.info(f"Cleanup: Removed {cleanup_count} old files")

        return cleanup_count

    except Exception as e:
        logger.error(f"Cleanup error: {e}", exc_info=True)
        return 0


def start_cleanup_scheduler(
    folders: List[str], interval_seconds: int = 1800, max_age_seconds: int = 3600
):
    """
    Start background thread for automatic file cleanup.

    Args:
        folders: List of folders to clean
        interval_seconds: Cleanup interval in seconds (default: 30 minutes)
        max_age_seconds: Maximum file age before deletion (default: 1 hour)

    Example:
        >>> start_cleanup_scheduler(['./uploads', './results'])
        # Background cleanup scheduler started (runs every 30 minutes)
    """

    def run_cleanup_loop():
        """Background cleanup loop."""
        while True:
            time.sleep(interval_seconds)
            cleanup_old_files(folders, max_age_seconds)

    cleanup_thread = threading.Thread(target=run_cleanup_loop, daemon=True, name="FileCleanup")
    cleanup_thread.start()

    logger.info(
        f"Background cleanup scheduler started "
        f"(interval: {interval_seconds}s, max_age: {max_age_seconds}s)"
    )
