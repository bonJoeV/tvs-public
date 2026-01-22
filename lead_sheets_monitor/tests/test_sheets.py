"""
Tests for sheets.py - Google Sheets API functions.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestSpreadsheetIdValidation:
    """Tests for spreadsheet ID validation."""

    def test_valid_spreadsheet_id(self):
        """Test valid spreadsheet IDs pass validation."""
        from sheets import validate_spreadsheet_id

        assert validate_spreadsheet_id('1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms') is True
        assert validate_spreadsheet_id('abc123-def456_ghi789') is True
        assert validate_spreadsheet_id('a' * 44) is True

    def test_invalid_spreadsheet_id_too_short(self):
        """Test short spreadsheet IDs fail validation."""
        from sheets import validate_spreadsheet_id

        assert validate_spreadsheet_id('short') is False
        assert validate_spreadsheet_id('a' * 19) is False

    def test_invalid_spreadsheet_id_special_chars(self):
        """Test spreadsheet IDs with invalid chars fail."""
        from sheets import validate_spreadsheet_id

        assert validate_spreadsheet_id('abc/def') is False
        assert validate_spreadsheet_id('abc..def') is False
        assert validate_spreadsheet_id('abc<script>def') is False

    def test_invalid_spreadsheet_id_empty(self):
        """Test empty/None spreadsheet IDs fail validation."""
        from sheets import validate_spreadsheet_id

        assert validate_spreadsheet_id('') is False
        assert validate_spreadsheet_id(None) is False


class TestUrlParsing:
    """Tests for Google Sheets URL parsing."""

    def test_parse_full_url(self):
        """Test parsing full Google Sheets URL."""
        from sheets import parse_spreadsheet_url

        url = 'https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=123'
        result = parse_spreadsheet_url(url)

        assert result is not None
        assert result[0] == '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        assert result[1] == '123'

    def test_parse_url_without_gid(self):
        """Test parsing URL without gid."""
        from sheets import parse_spreadsheet_url

        url = 'https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit'
        result = parse_spreadsheet_url(url)

        assert result is not None
        assert result[0] == '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        assert result[1] is None

    def test_parse_raw_id(self):
        """Test parsing raw spreadsheet ID."""
        from sheets import parse_spreadsheet_url

        raw_id = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
        result = parse_spreadsheet_url(raw_id)

        assert result is not None
        assert result[0] == raw_id
        assert result[1] is None

    def test_parse_invalid_url(self):
        """Test parsing invalid URL returns None."""
        from sheets import parse_spreadsheet_url

        assert parse_spreadsheet_url('https://example.com/not-a-sheet') is None
        assert parse_spreadsheet_url('random-text') is None


class TestRetryLogic:
    """Tests for retry with backoff logic."""

    def test_is_retryable_error_429(self):
        """Test 429 rate limit is retryable."""
        from sheets import is_retryable_error
        from googleapiclient.errors import HttpError
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status = 429
        error = HttpError(resp, b'Rate limited')

        assert is_retryable_error(error) is True

    def test_is_retryable_error_500(self):
        """Test 500 server error is retryable."""
        from sheets import is_retryable_error
        from googleapiclient.errors import HttpError
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status = 500
        error = HttpError(resp, b'Server error')

        assert is_retryable_error(error) is True

    def test_is_retryable_error_401(self):
        """Test 401 unauthorized is not retryable."""
        from sheets import is_retryable_error
        from googleapiclient.errors import HttpError
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status = 401
        error = HttpError(resp, b'Unauthorized')

        assert is_retryable_error(error) is False

    def test_is_retryable_error_403(self):
        """Test 403 forbidden is not retryable."""
        from sheets import is_retryable_error
        from googleapiclient.errors import HttpError
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status = 403
        error = HttpError(resp, b'Forbidden')

        assert is_retryable_error(error) is False

    def test_is_retryable_error_timeout(self):
        """Test timeout errors are retryable."""
        from sheets import is_retryable_error

        assert is_retryable_error(TimeoutError('Connection timed out')) is True
        assert is_retryable_error(ConnectionError('Connection refused')) is True


class TestBuildLeadData:
    """Tests for building Momence lead data from sheet row."""

    def test_build_lead_data_basic(self):
        """Test building basic lead data."""
        from sheets import build_momence_lead_data

        headers = ['email', 'first_name', 'last_name', 'phone_number']
        row = ['test@example.com', 'John', 'Doe', '+15551234567']
        config = {'name': 'Test Sheet', 'lead_source_id': 123}

        result = build_momence_lead_data(headers, row, config)

        assert result is not None
        assert result['email'] == 'test@example.com'
        assert result['firstName'] == 'John'
        assert result['lastName'] == 'Doe'
        assert result['leadSourceId'] == 123

    def test_build_lead_data_missing_email(self):
        """Test building lead data without email returns None."""
        from sheets import build_momence_lead_data

        headers = ['first_name', 'last_name']
        row = ['John', 'Doe']
        config = {'name': 'Test Sheet', 'lead_source_id': 123}

        result = build_momence_lead_data(headers, row, config)

        assert result is None

    def test_build_lead_data_with_extra_fields(self):
        """Test building lead data with extra fields for notifications."""
        from sheets import build_momence_lead_data

        headers = ['email', 'first_name', 'campaign', 'form', 'platform']
        row = ['test@example.com', 'John', 'Summer Sale', 'Contact Form', 'Facebook']
        config = {'name': 'Test Sheet', 'lead_source_id': 123}

        result = build_momence_lead_data(headers, row, config)

        assert result['campaign'] == 'Summer Sale'
        assert result['form'] == 'Contact Form'
        assert result['platform'] == 'Facebook'

    def test_build_lead_data_with_zip_code(self):
        """Test building lead data with zip code variants."""
        from sheets import build_momence_lead_data

        # Test with underscore
        headers = ['email', 'first_name', 'zip_code']
        row = ['test@example.com', 'John', '12345']
        config = {'name': 'Test Sheet', 'lead_source_id': 123}

        result = build_momence_lead_data(headers, row, config)
        assert result.get('zipCode') == '12345'

        # Test without underscore
        headers = ['email', 'first_name', 'zipcode']
        row = ['test@example.com', 'John', '54321']
        config = {'name': 'Test Sheet', 'lead_source_id': 123}

        result = build_momence_lead_data(headers, row, config)
        assert result.get('zipCode') == '54321'
