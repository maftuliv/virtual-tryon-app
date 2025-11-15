"""Validation utilities for files and images."""

from typing import Set

# Allowed image extensions
ALLOWED_EXTENSIONS: Set[str] = {"png", "jpg", "jpeg"}


def is_allowed_file(filename: str, allowed_extensions: Set[str] = ALLOWED_EXTENSIONS) -> bool:
    """
    Check if filename has an allowed extension.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (default: png, jpg, jpeg)

    Returns:
        True if extension is allowed, False otherwise

    Examples:
        >>> is_allowed_file("photo.jpg")
        True
        >>> is_allowed_file("document.pdf")
        False
        >>> is_allowed_file("noextension")
        False
    """
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in allowed_extensions
