"""
Pytest configuration and shared fixtures for Lead Sheets Monitor tests.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def reset_storage_state():
    """
    Reset storage module state before and after each test for proper isolation.

    This fixture runs automatically before each test to ensure clean state.
    """
    import storage
    # Reset state before test
    storage.reset_for_testing()
    yield
    # Reset state after test - critical for releasing file handles before temp cleanup
    storage.reset_for_testing()
    # Extra cleanup to ensure WAL checkpoint happens
    import gc
    gc.collect()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    # Use ignore_cleanup_errors=True on Windows to handle file locking issues
    # Windows may hold onto SQLite files briefly after they're closed
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env(temp_dir, monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', json.dumps({
        'type': 'service_account',
        'project_id': 'test-project',
        'private_key_id': 'key123',
        'private_key': '-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n',
        'client_email': 'test@test-project.iam.gserviceaccount.com',
        'client_id': '123456789',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }))
    monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))
    monkeypatch.setenv('SENT_TRACKER_FILE', str(temp_dir / 'sent_entries.json'))
    monkeypatch.setenv('FAILED_QUEUE_FILE', str(temp_dir / 'failed_queue.json'))
    monkeypatch.setenv('LOG_DIR', str(temp_dir / 'logs'))
    monkeypatch.setenv('CONFIG_FILE', str(temp_dir / 'config.json'))

    # Create minimal config file
    config = {
        'momence_hosts': {
            'TestTenant': {
                'host_id': '12345',
                'token': 'test-token-abc123',
                'enabled': True
            }
        },
        'sheets': [
            {
                'name': 'Test Sheet',
                'spreadsheet_id': 'test-spreadsheet-id-1234567890',
                'gid': '0',
                'momence_host': 'TestTenant',
                'lead_source_id': 123,
                'enabled': True
            }
        ],
        'settings': {
            'log_retention_days': 7,
            'api_timeout_seconds': 30,
            'dlq_enabled': True
        }
    }
    config_path = temp_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f)

    yield


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        'email': 'test@example.com',
        'firstName': 'John',
        'lastName': 'Doe',
        'phoneNumber': '+15551234567',
        'leadSourceId': 123,
        'sheetName': 'Test Sheet',
        'zipCode': '12345',
    }


@pytest.fixture
def sample_sheet_row():
    """Sample sheet row data for testing."""
    return [
        'lead123',           # id
        '2024-01-15',        # created_time
        'ad456',             # ad_id
        'Test Ad',           # ad_name
        'test@example.com',  # email
        'John',              # first_name
        'Doe',               # last_name
        '+15551234567',      # phone_number
        '12345',             # zip_code
    ]


@pytest.fixture
def sample_sheet_headers():
    """Sample sheet headers for testing."""
    return [
        'id', 'created_time', 'ad_id', 'ad_name',
        'email', 'first_name', 'last_name', 'phone_number', 'zip_code'
    ]


@pytest.fixture
def mock_sheets_service():
    """Mock Google Sheets API service."""
    service = MagicMock()

    # Mock spreadsheets().get() for metadata
    service.spreadsheets().get().execute.return_value = {
        'sheets': [
            {
                'properties': {
                    'sheetId': 0,
                    'title': 'Test Sheet',
                    'gridProperties': {'rowCount': 100}
                }
            }
        ]
    }

    # Mock spreadsheets().values().get() for data
    service.spreadsheets().values().get().execute.return_value = {
        'values': [
            ['id', 'created_time', 'ad_id', 'ad_name', 'email', 'first_name', 'last_name', 'phone_number'],
            ['1', '2024-01-15', 'ad1', 'Test Ad', 'test@example.com', 'John', 'Doe', '+15551234567']
        ]
    }

    return service


@pytest.fixture
def mock_momence_success():
    """Mock successful Momence API response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {'success': True, 'id': 'lead123'}
    response.text = '{"success": true}'
    response.headers = {'Content-Type': 'application/json'}
    return response


@pytest.fixture
def mock_momence_error():
    """Mock failed Momence API response."""
    response = MagicMock()
    response.status_code = 400
    response.json.return_value = {'error': 'Invalid email'}
    response.text = '{"error": "Invalid email"}'
    response.headers = {'Content-Type': 'application/json', 'cf-ray': 'abc123'}
    response.reason = 'Bad Request'
    return response
