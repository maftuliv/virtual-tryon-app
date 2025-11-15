"""Security and privacy utilities."""


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive value for safe logging.

    Shows first and last N characters, masks the middle.

    Args:
        value: Sensitive string to mask
        visible_chars: Number of characters to show at start/end

    Returns:
        Masked string like "abcd...wxyz"

    Examples:
        >>> mask_sensitive_value("my_secret_api_key_12345", 4)
        'my_s...2345'
        >>> mask_sensitive_value("short", 4)
        's...t'
    """
    if not value:
        return "[EMPTY]"

    if len(value) <= visible_chars * 2:
        # Too short to mask meaningfully
        return f"{value[0]}...{value[-1]}" if len(value) > 2 else "***"

    return f"{value[:visible_chars]}...{value[-visible_chars:]}"
