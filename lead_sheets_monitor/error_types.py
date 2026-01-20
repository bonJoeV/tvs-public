"""
Error type constants for Lead Sheets Monitor.

Centralizes all error type strings to prevent typos and enable IDE autocomplete.
"""

from enum import Enum
from typing import Tuple


class ErrorType(str, Enum):
    """
    Enumeration of all error types used in the application.

    Inherits from str to allow direct use as string values.
    """
    # Cloudflare-related errors (generally retryable)
    CLOUDFLARE_BLOCKED = 'cloudflare_blocked'
    CLOUDFLARE_CHALLENGE = 'cloudflare_challenge'
    CLOUDFLARE_ERROR = 'cloudflare_error'

    # API client errors (generally NOT retryable)
    API_BAD_REQUEST = 'api_bad_request'
    API_UNAUTHORIZED = 'api_unauthorized'
    API_FORBIDDEN = 'api_forbidden'
    API_NOT_FOUND = 'api_not_found'
    API_CONFLICT = 'api_conflict'
    API_VALIDATION_ERROR = 'api_validation_error'
    API_RATE_LIMITED = 'api_rate_limited'

    # Server errors (retryable)
    SERVER_ERROR = 'server_error'
    SERVER_BAD_GATEWAY = 'server_bad_gateway'
    SERVER_UNAVAILABLE = 'server_unavailable'
    SERVER_GATEWAY_TIMEOUT = 'server_gateway_timeout'

    # Network/connection errors (retryable)
    REQUEST_EXCEPTION = 'request_exception'
    CONNECTION_ERROR = 'connection_error'
    TIMEOUT_ERROR = 'timeout_error'

    # Application-level errors
    CONFIG_ERROR = 'config_error'
    VALIDATION_ERROR = 'validation_error'
    UNKNOWN = 'unknown'

    def __str__(self) -> str:
        return self.value


# Mapping of error types to their retryability
# True = retryable (transient), False = permanent
ERROR_RETRYABILITY = {
    ErrorType.CLOUDFLARE_BLOCKED: True,
    ErrorType.CLOUDFLARE_CHALLENGE: True,
    ErrorType.CLOUDFLARE_ERROR: True,

    ErrorType.API_BAD_REQUEST: False,
    ErrorType.API_UNAUTHORIZED: False,
    ErrorType.API_FORBIDDEN: False,
    ErrorType.API_NOT_FOUND: False,
    ErrorType.API_CONFLICT: False,
    ErrorType.API_VALIDATION_ERROR: False,
    ErrorType.API_RATE_LIMITED: True,

    ErrorType.SERVER_ERROR: True,
    ErrorType.SERVER_BAD_GATEWAY: True,
    ErrorType.SERVER_UNAVAILABLE: True,
    ErrorType.SERVER_GATEWAY_TIMEOUT: True,

    ErrorType.REQUEST_EXCEPTION: True,
    ErrorType.CONNECTION_ERROR: True,
    ErrorType.TIMEOUT_ERROR: True,

    ErrorType.CONFIG_ERROR: False,
    ErrorType.VALIDATION_ERROR: False,
    ErrorType.UNKNOWN: True,
}


def is_retryable(error_type: ErrorType) -> bool:
    """
    Check if an error type is retryable.

    Args:
        error_type: The error type to check

    Returns:
        True if the error should be retried, False otherwise
    """
    return ERROR_RETRYABILITY.get(error_type, True)


def get_error_type_for_status(status_code: int) -> Tuple[ErrorType, bool]:
    """
    Map an HTTP status code to an error type.

    Args:
        status_code: HTTP status code

    Returns:
        Tuple of (ErrorType, is_retryable)
    """
    if status_code == 400:
        return ErrorType.API_BAD_REQUEST, False
    elif status_code == 401:
        return ErrorType.API_UNAUTHORIZED, False
    elif status_code == 403:
        return ErrorType.API_FORBIDDEN, False
    elif status_code == 404:
        return ErrorType.API_NOT_FOUND, False
    elif status_code == 409:
        return ErrorType.API_CONFLICT, False
    elif status_code == 422:
        return ErrorType.API_VALIDATION_ERROR, False
    elif status_code == 429:
        return ErrorType.API_RATE_LIMITED, True
    elif status_code == 502:
        return ErrorType.SERVER_BAD_GATEWAY, True
    elif status_code == 503:
        return ErrorType.SERVER_UNAVAILABLE, True
    elif status_code == 504:
        return ErrorType.SERVER_GATEWAY_TIMEOUT, True
    elif status_code >= 500:
        return ErrorType.SERVER_ERROR, True
    elif 400 <= status_code < 500:
        return ErrorType.UNKNOWN, False
    else:
        return ErrorType.UNKNOWN, True
