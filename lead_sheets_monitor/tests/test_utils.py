"""
Tests for utils.py - validation, hashing, and helper functions.
"""

import pytest
from datetime import datetime, timezone


class TestEmailValidation:
    """Tests for email validation functions."""

    def test_valid_email_simple(self):
        """Test simple valid email addresses."""
        from utils import is_valid_email

        assert is_valid_email('test@example.com') is True
        assert is_valid_email('user@domain.org') is True
        assert is_valid_email('name.surname@company.co.uk') is True

    def test_valid_email_with_plus(self):
        """Test valid email with plus addressing."""
        from utils import is_valid_email

        assert is_valid_email('test+tag@example.com') is True
        assert is_valid_email('user+filter@gmail.com') is True

    def test_invalid_email_no_at(self):
        """Test email without @ symbol."""
        from utils import is_valid_email

        assert is_valid_email('testexample.com') is False

    def test_invalid_email_no_domain(self):
        """Test email without domain."""
        from utils import is_valid_email

        assert is_valid_email('test@') is False
        assert is_valid_email('test@.com') is False

    def test_invalid_email_empty(self):
        """Test empty and None inputs."""
        from utils import is_valid_email

        assert is_valid_email('') is False
        assert is_valid_email(None) is False
        assert is_valid_email('   ') is False

    def test_invalid_email_special_chars(self):
        """Test invalid special characters."""
        from utils import is_valid_email

        assert is_valid_email('test <script>@example.com') is False
        assert is_valid_email('test"quote@example.com') is False

class TestPhoneNormalization:
    """Tests for phone number normalization."""

    def test_normalize_us_phone(self):
        """Test US phone number normalization."""
        from utils import normalize_phone

        # Should normalize to E.164
        result = normalize_phone('(555) 123-4567')
        # May or may not have phonenumbers library
        assert result is not None
        assert len(result) > 0

    def test_normalize_phone_with_country_code(self):
        """Test phone with country code."""
        from utils import normalize_phone

        result = normalize_phone('+1 555 123 4567')
        assert result is not None

    def test_normalize_phone_empty(self):
        """Test empty phone input."""
        from utils import normalize_phone

        assert normalize_phone('') == ''
        assert normalize_phone(None) == ''

    def test_normalize_phone_with_prefix(self):
        """Test phone with p: prefix (from some forms)."""
        from utils import normalize_phone

        result = normalize_phone('p: 555-123-4567')
        assert 'p:' not in result.lower()


class TestEntryHashing:
    """Tests for entry hash computation."""

    def test_compute_hash_basic(self):
        """Test basic hash computation."""
        from utils import compute_entry_hash

        entry = {
            'email': 'test@example.com',
            'firstName': 'John',
            'lastName': 'Doe',
        }

        hash1 = compute_entry_hash(entry)
        assert hash1 is not None
        assert len(hash1) == 32  # SHA256 truncated

    def test_compute_hash_consistency(self):
        """Test that same input produces same hash."""
        from utils import compute_entry_hash

        entry = {
            'email': 'test@example.com',
            'firstName': 'John',
            'lastName': 'Doe',
        }

        hash1 = compute_entry_hash(entry)
        hash2 = compute_entry_hash(entry)

        assert hash1 == hash2

    def test_compute_hash_different_entries(self):
        """Test different entries produce different hashes."""
        from utils import compute_entry_hash

        entry1 = {'email': 'test1@example.com', 'firstName': 'John'}
        entry2 = {'email': 'test2@example.com', 'firstName': 'John'}

        hash1 = compute_entry_hash(entry1)
        hash2 = compute_entry_hash(entry2)

        assert hash1 != hash2

    def test_compute_hash_case_insensitive(self):
        """Test hash is case-insensitive for email."""
        from utils import compute_entry_hash

        entry1 = {'email': 'Test@Example.com', 'firstName': 'John'}
        entry2 = {'email': 'test@example.com', 'firstName': 'john'}

        hash1 = compute_entry_hash(entry1)
        hash2 = compute_entry_hash(entry2)

        # Hashes should be the same (case-insensitive)
        assert hash1 == hash2

    def test_compute_hash_with_sheet_id(self):
        """Test hash includes sheet ID when provided."""
        from utils import compute_entry_hash

        entry = {'email': 'test@example.com'}

        hash1 = compute_entry_hash(entry, sheet_id='sheet1', gid='0')
        hash2 = compute_entry_hash(entry, sheet_id='sheet2', gid='0')

        assert hash1 != hash2

    def test_compute_hash_snake_case_fields(self):
        """Test hash works with snake_case field names."""
        from utils import compute_entry_hash

        entry_camel = {'email': 'test@example.com', 'firstName': 'John', 'lastName': 'Doe'}
        entry_snake = {'email': 'test@example.com', 'first_name': 'John', 'last_name': 'Doe'}

        hash_camel = compute_entry_hash(entry_camel)
        hash_snake = compute_entry_hash(entry_snake)

        # Both naming conventions should produce same hash
        assert hash_camel == hash_snake


class TestHtmlEscaping:
    """Tests for HTML escaping."""

    def test_escape_html_basic(self):
        """Test basic HTML escaping."""
        from utils import escape_html

        assert escape_html('<script>alert("xss")</script>') == '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'

    def test_escape_html_ampersand(self):
        """Test ampersand escaping."""
        from utils import escape_html

        assert '&amp;' in escape_html('A & B')

    def test_escape_html_empty(self):
        """Test empty input."""
        from utils import escape_html

        assert escape_html('') == ''
        assert escape_html(None) == ''


class TestErrorCategorization:
    """Tests for error categorization."""

    def test_categorize_rate_limit(self):
        """Test 429 rate limit categorization."""
        from utils import categorize_error

        error_type, is_retryable = categorize_error(429, {}, '')

        assert error_type == 'api_rate_limited'
        assert is_retryable is True

    def test_categorize_unauthorized(self):
        """Test 401 unauthorized categorization."""
        from utils import categorize_error

        error_type, is_retryable = categorize_error(401, {}, '')

        assert error_type == 'api_unauthorized'
        assert is_retryable is False

    def test_categorize_forbidden(self):
        """Test 403 forbidden categorization."""
        from utils import categorize_error

        error_type, is_retryable = categorize_error(403, {}, '')

        assert error_type == 'api_forbidden'
        assert is_retryable is False

    def test_categorize_not_found(self):
        """Test 404 not found categorization."""
        from utils import categorize_error

        error_type, is_retryable = categorize_error(404, {}, '')

        assert error_type == 'api_not_found'
        assert is_retryable is False

    def test_categorize_server_error(self):
        """Test 500 server error categorization."""
        from utils import categorize_error

        error_type, is_retryable = categorize_error(500, {}, '')

        assert 'server' in error_type
        assert is_retryable is True

    def test_categorize_bad_gateway(self):
        """Test 502 bad gateway categorization."""
        from utils import categorize_error

        error_type, is_retryable = categorize_error(502, {}, '')

        assert error_type == 'server_bad_gateway'
        assert is_retryable is True

    def test_categorize_cloudflare_blocked(self):
        """Test Cloudflare blocked detection."""
        from utils import categorize_error

        headers = {'cf-mitigated': 'challenge'}
        error_type, is_retryable = categorize_error(403, headers, '')

        assert 'cloudflare' in error_type
        assert is_retryable is True

    def test_is_error_retryable(self):
        """Test retryable error helper function."""
        from utils import is_error_retryable

        assert is_error_retryable(500, {}, '') is True
        assert is_error_retryable(429, {}, '') is True
        assert is_error_retryable(401, {}, '') is False
        assert is_error_retryable(400, {}, '') is False


class TestUtcNow:
    """Tests for UTC time helper."""

    def test_utc_now_has_timezone(self):
        """Test utc_now returns timezone-aware datetime."""
        from utils import utc_now

        now = utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_utc_now_is_current(self):
        """Test utc_now returns approximately current time."""
        from utils import utc_now

        now = utc_now()
        system_now = datetime.now(timezone.utc)

        # Should be within 1 second
        diff = abs((system_now - now).total_seconds())
        assert diff < 1
