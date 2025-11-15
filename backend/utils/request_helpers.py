"""Request handling utilities."""

from typing import Optional

from flask import Request


def get_client_ip(request_obj: Request) -> str:
    """
    Extract client IP address from Flask request.

    Checks X-Forwarded-For header first (for proxies/load balancers),
    then falls back to remote_addr.

    Args:
        request_obj: Flask Request object

    Returns:
        Client IP address as string
    """
    if request_obj.headers.getlist("X-Forwarded-For"):
        # Get first IP if multiple (client, proxy1, proxy2, ...)
        ip = request_obj.headers.getlist("X-Forwarded-For")[0].split(",")[0].strip()
    else:
        ip = request_obj.remote_addr or "unknown"

    return ip
