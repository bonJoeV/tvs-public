"""
Tests for the error_types module.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from error_types import (
    ErrorType,
    ERROR_RETRYABILITY,
    is_retryable,
    get_error_type_for_status
)


class TestErrorType:
    """Tests for ErrorType enum."""

    def test_error_type_values(self):
        """Test that ErrorType enum has expected values."""
        assert ErrorType.CLOUDFLARE_BLOCKED.value == 'cloudflare_blocked'
        assert ErrorType.API_RATE_LIMITED.value == 'api_rate_limited'
        assert ErrorType.SERVER_UNAVAILABLE.value == 'server_unavailable'
        assert ErrorType.API_UNAUTHORIZED.value == 'api_unauthorized'

    def test_error_type_string_conversion(self):
        """Test that ErrorType can be used as string."""
        assert str(ErrorType.CLOUDFLARE_BLOCKED) == 'cloudflare_blocked'
        assert f"{ErrorType.API_RATE_LIMITED}" == 'api_rate_limited'

    def test_error_type_comparison(self):
        """Test that ErrorType can be compared to strings."""
        assert ErrorType.CLOUDFLARE_BLOCKED == 'cloudflare_blocked'
        assert ErrorType.API_RATE_LIMITED == 'api_rate_limited'


class TestErrorRetryability:
    """Tests for error retryability mapping."""

    def test_cloudflare_errors_retryable(self):
        """Test that Cloudflare errors are marked as retryable."""
        assert ERROR_RETRYABILITY[ErrorType.CLOUDFLARE_BLOCKED] is True
        assert ERROR_RETRYABILITY[ErrorType.CLOUDFLARE_CHALLENGE] is True
        assert ERROR_RETRYABILITY[ErrorType.CLOUDFLARE_ERROR] is True

    def test_server_errors_retryable(self):
        """Test that server errors are marked as retryable."""
        assert ERROR_RETRYABILITY[ErrorType.SERVER_ERROR] is True
        assert ERROR_RETRYABILITY[ErrorType.SERVER_BAD_GATEWAY] is True
        assert ERROR_RETRYABILITY[ErrorType.SERVER_UNAVAILABLE] is True
        assert ERROR_RETRYABILITY[ErrorType.SERVER_GATEWAY_TIMEOUT] is True

    def test_client_errors_not_retryable(self):
        """Test that client errors are NOT retryable."""
        assert ERROR_RETRYABILITY[ErrorType.API_BAD_REQUEST] is False
        assert ERROR_RETRYABILITY[ErrorType.API_UNAUTHORIZED] is False
        assert ERROR_RETRYABILITY[ErrorType.API_FORBIDDEN] is False
        assert ERROR_RETRYABILITY[ErrorType.API_NOT_FOUND] is False
        assert ERROR_RETRYABILITY[ErrorType.API_VALIDATION_ERROR] is False

    def test_rate_limit_retryable(self):
        """Test that rate limiting is retryable."""
        assert ERROR_RETRYABILITY[ErrorType.API_RATE_LIMITED] is True

    def test_is_retryable_function(self):
        """Test the is_retryable helper function."""
        assert is_retryable(ErrorType.CLOUDFLARE_BLOCKED) is True
        assert is_retryable(ErrorType.API_UNAUTHORIZED) is False
        assert is_retryable(ErrorType.SERVER_UNAVAILABLE) is True

    def test_is_retryable_unknown_defaults_true(self):
        """Test that unknown error types default to retryable."""
        # Create a mock error type that's not in the mapping
        assert is_retryable(ErrorType.UNKNOWN) is True


class TestGetErrorTypeForStatus:
    """Tests for status code to error type mapping."""

    def test_400_bad_request(self):
        """Test 400 status code."""
        error_type, retryable = get_error_type_for_status(400)
        assert error_type == ErrorType.API_BAD_REQUEST
        assert retryable is False

    def test_401_unauthorized(self):
        """Test 401 status code."""
        error_type, retryable = get_error_type_for_status(401)
        assert error_type == ErrorType.API_UNAUTHORIZED
        assert retryable is False

    def test_403_forbidden(self):
        """Test 403 status code."""
        error_type, retryable = get_error_type_for_status(403)
        assert error_type == ErrorType.API_FORBIDDEN
        assert retryable is False

    def test_404_not_found(self):
        """Test 404 status code."""
        error_type, retryable = get_error_type_for_status(404)
        assert error_type == ErrorType.API_NOT_FOUND
        assert retryable is False

    def test_409_conflict(self):
        """Test 409 status code."""
        error_type, retryable = get_error_type_for_status(409)
        assert error_type == ErrorType.API_CONFLICT
        assert retryable is False

    def test_422_validation_error(self):
        """Test 422 status code."""
        error_type, retryable = get_error_type_for_status(422)
        assert error_type == ErrorType.API_VALIDATION_ERROR
        assert retryable is False

    def test_429_rate_limited(self):
        """Test 429 status code."""
        error_type, retryable = get_error_type_for_status(429)
        assert error_type == ErrorType.API_RATE_LIMITED
        assert retryable is True

    def test_500_server_error(self):
        """Test 500 status code."""
        error_type, retryable = get_error_type_for_status(500)
        assert error_type == ErrorType.SERVER_ERROR
        assert retryable is True

    def test_502_bad_gateway(self):
        """Test 502 status code."""
        error_type, retryable = get_error_type_for_status(502)
        assert error_type == ErrorType.SERVER_BAD_GATEWAY
        assert retryable is True

    def test_503_unavailable(self):
        """Test 503 status code."""
        error_type, retryable = get_error_type_for_status(503)
        assert error_type == ErrorType.SERVER_UNAVAILABLE
        assert retryable is True

    def test_504_gateway_timeout(self):
        """Test 504 status code."""
        error_type, retryable = get_error_type_for_status(504)
        assert error_type == ErrorType.SERVER_GATEWAY_TIMEOUT
        assert retryable is True

    def test_unknown_4xx(self):
        """Test unknown 4xx status code."""
        error_type, retryable = get_error_type_for_status(418)  # I'm a teapot
        assert error_type == ErrorType.UNKNOWN
        assert retryable is False

    def test_unknown_5xx(self):
        """Test unknown 5xx status code."""
        error_type, retryable = get_error_type_for_status(599)
        assert error_type == ErrorType.SERVER_ERROR
        assert retryable is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
