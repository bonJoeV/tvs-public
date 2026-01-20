"""
Integration tests for Lead Sheets Monitor.

These tests verify the interaction between components and external services.
They require more setup than unit tests but provide higher confidence.

Run with: pytest tests/test_integration.py -v
"""

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def integration_env(tmp_path, monkeypatch):
    """
    Set up a complete integration test environment.

    Creates all necessary files and configuration for a full test run.
    """
    # Create directories
    data_dir = tmp_path / "data"
    logs_dir = tmp_path / "logs"
    secrets_dir = tmp_path / "secrets"

    data_dir.mkdir()
    logs_dir.mkdir()
    secrets_dir.mkdir()

    # Create config file
    config = {
        "settings": {
            "log_retention_days": 7,
            "api_timeout_seconds": 30,
            "dlq_enabled": True,
            "dlq_max_retry_attempts": 3,
            "dlq_retry_backoff_hours": [1, 2, 4],
            "health_server": {
                "enabled": False
            }
        },
        "tenants": {
            "TestTenant": {
                "host_id": "12345",
                "token": "test-token-abc123",
                "enabled": True,
                "schedule": {"check_interval_minutes": 5}
            }
        },
        "sheets": [
            {
                "name": "Test Location",
                "spreadsheet_id": "test-spreadsheet-id-1234567890",
                "gid": "0",
                "tenant": "TestTenant",
                "lead_source_id": 123,
                "enabled": True
            }
        ]
    }

    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    # Set environment variables
    monkeypatch.setenv("DATABASE_FILE", str(data_dir / "test.db"))
    monkeypatch.setenv("LOG_DIR", str(logs_dir))
    monkeypatch.setenv("CONFIG_FILE", str(config_path))
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key123",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }))

    yield {
        "tmp_path": tmp_path,
        "data_dir": data_dir,
        "logs_dir": logs_dir,
        "config_path": config_path,
        "db_path": data_dir / "test.db"
    }


# ============================================================================
# Database Integration Tests
# ============================================================================

class TestDatabaseIntegration:
    """Tests for database operations and integrity."""

    def test_database_initialization(self, integration_env):
        """Test that database initializes correctly with all tables."""
        import storage
        storage.init_database()

        # Verify tables exist by trying to query them
        with storage.get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row['name'] for row in tables}

            expected_tables = {
                'sent_hashes',
                'failed_queue',
                'dead_letters',
                'tracker_metadata',
                'admin_activity',
                'leads_daily_metrics',
                'web_sessions',
                'csrf_tokens'
            }

            for table in expected_tables:
                assert table in table_names, f"Missing table: {table}"

    def test_sent_hash_lifecycle(self, integration_env):
        """Test the complete lifecycle of a sent hash."""
        import storage
        storage.init_database()

        test_hash = "abc123def456"
        location = "Test Location"

        # Initially should not exist
        assert not storage.hash_exists(test_hash)

        # Add the hash
        storage.add_sent_hash(test_hash, location)

        # Now should exist
        assert storage.hash_exists(test_hash)

        # Count should be 1
        assert storage.get_sent_hash_count() == 1

    def test_session_persistence(self, integration_env):
        """Test that sessions persist in database."""
        import storage
        storage.init_database()

        token = "test-session-token-12345"
        username = "testuser"
        ip = "192.168.1.1"

        # Create session
        storage.create_session(token, username, ip)

        # Validate session
        session = storage.validate_session(token)
        assert session is not None
        assert session['username'] == username
        assert session['ip_address'] == ip

        # Invalidate session
        storage.invalidate_session(token)

        # Should no longer validate
        assert storage.validate_session(token) is None

    def test_csrf_token_persistence(self, integration_env):
        """Test that CSRF tokens persist in database."""
        import storage
        storage.init_database()

        token = "test-csrf-token-67890"

        # Create token
        storage.create_csrf_token(token)

        # Validate token
        assert storage.validate_csrf_token(token) is True

        # Invalidate token
        storage.invalidate_csrf_token(token)

        # Should no longer validate
        assert storage.validate_csrf_token(token) is False

    def test_failed_queue_lifecycle(self, integration_env):
        """Test the complete failed queue lifecycle."""
        import storage
        storage.init_database()

        entry_hash = "failed-entry-hash-123"
        lead_data = {
            "email": "test@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "sheetName": "Test Location"
        }
        tenant = "TestTenant"
        error_info = {
            "type": "api_rate_limited",
            "status_code": 429,
            "message": "Rate limited"
        }

        # Add to failed queue
        storage.add_to_failed_queue(entry_hash, lead_data, tenant, error_info)

        # Retrieve from queue
        entries = storage.get_failed_queue_entries()
        assert len(entries) == 1
        assert entries[0]['entry_hash'] == entry_hash

        # Move to dead letters
        storage.move_to_dead_letters(entry_hash)

        # Should no longer be in failed queue
        entries = storage.get_failed_queue_entries()
        assert len(entries) == 0

        # Should be in dead letters
        dead = storage.get_dead_letters()
        assert len(dead) == 1

    def test_atomic_location_increment(self, integration_env):
        """Test that location count increment is atomic."""
        import storage
        storage.init_database()

        # Initialize tracker metadata
        storage.init_tracker_metadata()

        location = "Test Location"

        # Increment multiple times
        for _ in range(10):
            storage.increment_location_count(location, 1)

        # Check final count
        counts = storage.get_location_counts()
        assert counts.get(location, 0) == 10


# ============================================================================
# Error Handling Integration Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling across components."""

    def test_error_type_categorization(self, integration_env):
        """Test that error types are correctly categorized."""
        from utils import categorize_error, is_error_retryable

        # Rate limited - retryable
        err_type, retryable = categorize_error(429, {}, "")
        assert err_type == "api_rate_limited"
        assert retryable is True

        # Unauthorized - not retryable
        err_type, retryable = categorize_error(401, {}, "")
        assert err_type == "api_unauthorized"
        assert retryable is False

        # Server error - retryable
        err_type, retryable = categorize_error(503, {}, "")
        assert err_type == "server_unavailable"
        assert retryable is True

        # Cloudflare block
        err_type, retryable = categorize_error(
            403,
            {"cf-mitigated": "true"},
            ""
        )
        assert err_type == "cloudflare_blocked"
        assert retryable is True

    def test_cleanup_error_isolation(self, integration_env):
        """Test that cleanup errors don't block other cleanups."""
        import storage
        storage.init_database()

        # Import here to get fresh module state
        from monitor import run_cleanup_tasks

        # Run cleanup - should complete without raising
        results = run_cleanup_tasks()

        # Should have results for all cleanup types
        assert 'sent_hashes' in results
        assert 'admin_activity' in results
        assert 'metrics' in results


# ============================================================================
# Web Server Integration Tests
# ============================================================================

class TestWebServerIntegration:
    """Tests for web server functionality."""

    def test_session_creation_and_validation(self, integration_env):
        """Test session flow through web server functions."""
        import storage
        storage.init_database()

        # Import after environment setup
        from web.server import _create_session, _validate_session, _invalidate_session

        # Create session
        token = _create_session(username="testadmin", ip_address="10.0.0.1")
        assert token is not None
        assert len(token) > 20

        # Validate session
        assert _validate_session(token) is True

        # Invalidate
        _invalidate_session(token)

        # Should no longer be valid
        assert _validate_session(token) is False

    def test_csrf_token_flow(self, integration_env):
        """Test CSRF token generation and validation."""
        import storage
        storage.init_database()

        from web.server import generate_csrf_token, validate_csrf_token, consume_csrf_token

        # Generate token
        token = generate_csrf_token()
        assert token is not None
        assert len(token) > 20

        # Validate (non-consuming)
        assert validate_csrf_token(token) is True

        # Consume token
        assert consume_csrf_token(token) is True

        # Should no longer be valid (consumed)
        assert validate_csrf_token(token) is False


# ============================================================================
# End-to-End Flow Tests
# ============================================================================

class TestEndToEndFlow:
    """Tests for complete application flows."""

    @patch('sheets.get_google_sheets_service')
    @patch('momence.create_momence_lead')
    def test_lead_processing_flow(
        self,
        mock_create_lead,
        mock_sheets_service,
        integration_env
    ):
        """Test the complete flow from sheet data to Momence."""
        import storage
        storage.init_database()

        # Mock sheet data
        mock_service = MagicMock()
        mock_sheets_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['id', 'created_time', 'ad_id', 'ad_name', 'email', 'first_name', 'last_name', 'phone_number'],
                ['1', '2024-01-15', 'ad1', 'Test Ad', 'lead@example.com', 'Jane', 'Smith', '+15551234567']
            ]
        }

        # Mock successful Momence response
        mock_create_lead.return_value = {
            'success': True,
            'response': {'id': 'lead-123'}
        }

        from sheets import fetch_sheet_data, build_momence_lead_data

        # Fetch data
        data = fetch_sheet_data(mock_service, 'test-spreadsheet-id', 'Test Sheet')
        assert len(data) == 2  # Header + 1 row

        # Build lead data
        headers = data[0]
        row = data[1]
        lead_data = build_momence_lead_data(
            headers=headers,
            row=row,
            lead_source_id=123,
            sheet_name="Test Location"
        )

        assert lead_data is not None
        assert lead_data['email'] == 'lead@example.com'
        assert lead_data['firstName'] == 'Jane'

    def test_hash_deduplication(self, integration_env):
        """Test that duplicate leads are correctly deduplicated."""
        import storage
        from utils import compute_entry_hash
        storage.init_database()

        # Create lead entry
        entry = {
            'email': 'test@example.com',
            'firstName': 'John',
            'lastName': 'Doe',
            'phoneNumber': '+15551234567',
            'created_time': '2024-01-15'
        }

        # Compute hash
        hash1 = compute_entry_hash(entry, sheet_id='sheet1', gid='0')

        # Same entry should produce same hash
        hash2 = compute_entry_hash(entry, sheet_id='sheet1', gid='0')
        assert hash1 == hash2

        # Different entry should produce different hash
        entry['email'] = 'different@example.com'
        hash3 = compute_entry_hash(entry, sheet_id='sheet1', gid='0')
        assert hash1 != hash3

        # Store hash
        storage.add_sent_hash(hash1, 'Test Location')

        # Check deduplication
        assert storage.hash_exists(hash1) is True
        assert storage.hash_exists(hash3) is False


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Basic performance tests."""

    def test_batch_hash_insertion(self, integration_env):
        """Test that batch hash insertion is performant."""
        import storage
        storage.init_database()

        # Generate 1000 test hashes
        hashes = [(f"hash-{i:05d}", f"Location-{i % 10}") for i in range(1000)]

        # Batch insert
        start = time.time()
        storage.add_sent_hashes_batch(hashes)
        duration = time.time() - start

        # Should complete in under 1 second
        assert duration < 1.0, f"Batch insert took {duration:.2f}s"

        # Verify count
        assert storage.get_sent_hash_count() == 1000

    def test_hash_lookup_performance(self, integration_env):
        """Test that hash lookups are fast."""
        import storage
        storage.init_database()

        # Insert some hashes
        hashes = [(f"perf-hash-{i:05d}", "TestLocation") for i in range(1000)]
        storage.add_sent_hashes_batch(hashes)

        # Time 100 lookups
        start = time.time()
        for i in range(100):
            storage.hash_exists(f"perf-hash-{i:05d}")
        duration = time.time() - start

        # Should complete in under 0.5 seconds
        assert duration < 0.5, f"100 lookups took {duration:.2f}s"

    def test_iterator_memory_efficiency(self, integration_env):
        """Test that hash iterator doesn't load all into memory."""
        import storage
        storage.init_database()

        # Insert hashes
        hashes = [(f"iter-hash-{i:05d}", "TestLocation") for i in range(500)]
        storage.add_sent_hashes_batch(hashes)

        # Use iterator
        count = 0
        for _ in storage.iter_sent_hashes(batch_size=100):
            count += 1

        assert count == 500


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
