"""
Tests for storage.py - SQLite database operations.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_init_database_creates_tables(self, temp_dir, monkeypatch):
        """Test that init_database creates all required tables."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        # Re-import to pick up new env
        import importlib
        import storage
        importlib.reload(storage)

        storage.init_database()

        # Verify tables exist by querying them
        with storage.get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {t['name'] for t in tables}

            assert 'sent_hashes' in table_names
            assert 'failed_queue' in table_names
            assert 'dead_letters' in table_names
            assert 'tracker_metadata' in table_names
            assert 'admin_activity' in table_names
            assert 'lead_metrics' in table_names
            assert 'momence_hosts' in table_names
            assert 'sheets' in table_names

    def test_init_database_idempotent(self, temp_dir, monkeypatch):
        """Test that init_database can be called multiple times."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)

        # Call multiple times - should not raise
        storage.init_database()
        storage.init_database()
        storage.init_database()


class TestSentHashes:
    """Tests for sent hash operations."""

    def test_add_and_check_hash(self, temp_dir, monkeypatch):
        """Test adding and checking hashes."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        test_hash = 'abc123def456'

        # Should not exist initially
        assert storage.hash_exists(test_hash) is False

        # Add the hash
        storage.add_sent_hash(test_hash, 'Test Location')

        # Should exist now
        assert storage.hash_exists(test_hash) is True

    def test_add_hash_batch(self, temp_dir, monkeypatch):
        """Test batch adding hashes."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        hashes = [('hash1', 'Location1'), ('hash2', 'Location2'), ('hash3', 'Location3')]

        storage.add_sent_hashes_batch(hashes)

        assert storage.hash_exists('hash1') is True
        assert storage.hash_exists('hash2') is True
        assert storage.hash_exists('hash3') is True
        assert storage.get_sent_hash_count() == 3

    def test_get_all_sent_hashes(self, temp_dir, monkeypatch):
        """Test retrieving all hashes."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.add_sent_hash('hash1', 'Location1')
        storage.add_sent_hash('hash2', 'Location2')

        all_hashes = storage.get_all_sent_hashes()

        assert isinstance(all_hashes, set)
        assert 'hash1' in all_hashes
        assert 'hash2' in all_hashes

    def test_duplicate_hash_ignored(self, temp_dir, monkeypatch):
        """Test that duplicate hashes are ignored."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.add_sent_hash('same_hash', 'Location1')
        storage.add_sent_hash('same_hash', 'Location2')  # Should be ignored

        assert storage.get_sent_hash_count() == 1


class TestFailedQueue:
    """Tests for failed queue operations."""

    def test_add_to_failed_queue(self, temp_dir, monkeypatch):
        """Test adding entry to failed queue."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        lead_data = {'email': 'test@example.com', 'firstName': 'John'}
        error_info = {'type': 'api_error', 'status_code': 500, 'message': 'Server error'}

        storage.add_to_failed_queue('entry_hash_123', lead_data, 'TestHost', error_info)

        entries = storage.get_failed_queue_entries()
        assert len(entries) == 1
        assert entries[0]['entry_hash'] == 'entry_hash_123'
        assert entries[0]['momence_host'] == 'TestHost'
        assert entries[0]['attempts'] == 1

    def test_update_failed_entry_increments_attempts(self, temp_dir, monkeypatch):
        """Test that retrying increments attempt count."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        lead_data = {'email': 'test@example.com'}
        error_info = {'type': 'api_error', 'status_code': 500}

        storage.add_to_failed_queue('entry_hash_123', lead_data, 'TestHost', error_info)

        # Update with another error
        new_attempts = storage.update_failed_entry_attempt('entry_hash_123', {'type': 'api_error', 'status_code': 502})

        assert new_attempts == 2

    def test_remove_from_failed_queue(self, temp_dir, monkeypatch):
        """Test removing entry from failed queue."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        lead_data = {'email': 'test@example.com'}
        error_info = {'type': 'api_error'}

        storage.add_to_failed_queue('entry_hash_123', lead_data, 'TestHost', error_info)
        assert storage.get_failed_queue_count() == 1

        storage.remove_from_failed_queue('entry_hash_123')
        assert storage.get_failed_queue_count() == 0


class TestDeadLetters:
    """Tests for dead letter operations."""

    def test_move_to_dead_letters(self, temp_dir, monkeypatch):
        """Test moving entry to dead letters."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        lead_data = {'email': 'test@example.com'}
        error_info = {'type': 'api_error'}

        storage.add_to_failed_queue('entry_hash_123', lead_data, 'TestHost', error_info)
        assert storage.get_failed_queue_count() == 1

        storage.move_to_dead_letters('entry_hash_123')

        assert storage.get_failed_queue_count() == 0
        assert storage.get_dead_letter_count() == 1

    def test_requeue_dead_letters(self, temp_dir, monkeypatch):
        """Test moving dead letters back to queue."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        lead_data = {'email': 'test@example.com'}
        error_info = {'type': 'api_error'}

        storage.add_to_failed_queue('entry_hash_123', lead_data, 'TestHost', error_info)
        storage.move_to_dead_letters('entry_hash_123')

        assert storage.get_dead_letter_count() == 1
        assert storage.get_failed_queue_count() == 0

        count = storage.requeue_dead_letters()

        assert count == 1
        assert storage.get_dead_letter_count() == 0
        assert storage.get_failed_queue_count() == 1

    def test_dead_letter_stats(self, temp_dir, monkeypatch):
        """Test dead letter statistics."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        lead_data = {'email': 'test@example.com'}
        error_info = {'type': 'api_rate_limited'}

        storage.add_to_failed_queue('hash1', lead_data, 'Host1', error_info)
        storage.move_to_dead_letters('hash1')

        stats = storage.get_dead_letter_stats()

        assert stats['count'] == 1
        assert 'Host1' in stats['momence_hosts']


class TestTrackerMetadata:
    """Tests for tracker metadata operations."""

    def test_get_tracker_metadata(self, temp_dir, monkeypatch):
        """Test getting tracker metadata."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        metadata = storage.get_tracker_metadata()

        assert 'last_check' in metadata
        assert 'cache_built_at' in metadata
        assert 'location_counts' in metadata

    def test_update_tracker_metadata(self, temp_dir, monkeypatch):
        """Test updating tracker metadata."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.update_tracker_metadata(
            last_check='2024-01-15T12:00:00Z',
            location_counts={'Location1': 5, 'Location2': 3}
        )

        metadata = storage.get_tracker_metadata()

        assert metadata['last_check'] == '2024-01-15T12:00:00Z'
        assert metadata['location_counts']['Location1'] == 5

    def test_increment_location_count(self, temp_dir, monkeypatch):
        """Test incrementing location count."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.increment_location_count('TestLocation', 1)
        storage.increment_location_count('TestLocation', 1)
        storage.increment_location_count('TestLocation', 1)

        metadata = storage.get_tracker_metadata()
        assert metadata['location_counts'].get('TestLocation') == 3


class TestAdminActivity:
    """Tests for admin activity logging."""

    def test_log_admin_activity(self, temp_dir, monkeypatch):
        """Test logging admin activity."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.log_admin_activity(
            action='login',
            details='User logged in',
            username='admin',
            ip_address='127.0.0.1'
        )

        logs = storage.get_admin_activity_log(limit=10)

        assert len(logs) == 1
        assert logs[0]['action'] == 'login'
        assert logs[0]['username'] == 'admin'

    def test_get_admin_activity_with_filter(self, temp_dir, monkeypatch):
        """Test filtering admin activity logs."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.log_admin_activity(action='login', username='admin')
        storage.log_admin_activity(action='logout', username='admin')
        storage.log_admin_activity(action='login', username='user2')

        login_logs = storage.get_admin_activity_log(limit=10, action_filter='login')

        assert len(login_logs) == 2
        assert all(log['action'] == 'login' for log in login_logs)


class TestDailyMetrics:
    """Tests for daily lead metrics."""

    def test_record_lead_metric(self, temp_dir, monkeypatch):
        """Test recording lead metrics."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.record_lead_metric('TestLocation', 'TestTenant', '2024-01-15', success=True)
        storage.record_lead_metric('TestLocation', 'TestTenant', '2024-01-15', success=True)
        storage.record_lead_metric('TestLocation', 'TestTenant', '2024-01-15', success=False)

        data = storage.get_leads_by_location_daily(days=30)

        assert len(data) == 1
        assert data[0]['location'] == 'TestLocation'
        assert data[0]['leads_sent'] == 2
        assert data[0]['leads_failed'] == 1

    def test_get_leads_chart_data(self, temp_dir, monkeypatch):
        """Test chart data retrieval."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.record_lead_metric('Location1', 'Host1', '2024-01-15', success=True)
        storage.record_lead_metric('Location2', 'Host1', '2024-01-15', success=True)

        chart_data = storage.get_leads_chart_data(days=30)

        assert 'dates' in chart_data
        assert 'locations' in chart_data
        assert 'totals' in chart_data


class TestMomenceHosts:
    """Tests for Momence hosts storage operations."""

    def test_create_and_get_host(self, temp_dir, monkeypatch):
        """Test creating and retrieving a host."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        host = storage.create_host(
            name='TestHost',
            host_id='12345',
            token='test-token',
            enabled=True
        )

        assert host['name'] == 'TestHost'
        assert host['host_id'] == '12345'
        assert host['enabled'] is True

        retrieved = storage.get_host('TestHost')
        assert retrieved['name'] == 'TestHost'
        assert retrieved['host_id'] == '12345'

    def test_get_all_hosts(self, temp_dir, monkeypatch):
        """Test retrieving all hosts."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='Host1', host_id='111')
        storage.create_host(name='Host2', host_id='222')

        hosts = storage.get_all_hosts()
        assert len(hosts) == 2
        host_names = [h['name'] for h in hosts]
        assert 'Host1' in host_names
        assert 'Host2' in host_names

    def test_update_host(self, temp_dir, monkeypatch):
        """Test updating a host."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='TestHost', host_id='12345', enabled=True)

        updated = storage.update_host('TestHost', host_id='67890', enabled=False)

        assert updated['host_id'] == '67890'
        assert updated['enabled'] is False

    def test_delete_host(self, temp_dir, monkeypatch):
        """Test deleting a host."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='TestHost', host_id='12345')
        assert storage.get_host_count() == 1

        deleted = storage.delete_host('TestHost')
        assert deleted is True
        assert storage.get_host_count() == 0

    def test_create_duplicate_host_fails(self, temp_dir, monkeypatch):
        """Test that creating duplicate host raises error."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='TestHost', host_id='12345')

        with pytest.raises(ValueError):
            storage.create_host(name='TestHost', host_id='67890')

    def test_get_enabled_hosts(self, temp_dir, monkeypatch):
        """Test getting only enabled hosts."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='EnabledHost', host_id='111', enabled=True)
        storage.create_host(name='DisabledHost', host_id='222', enabled=False)

        enabled = storage.get_enabled_hosts()
        assert len(enabled) == 1
        assert enabled[0]['name'] == 'EnabledHost'


class TestSheets:
    """Tests for sheets/locations storage operations."""

    def test_create_and_get_sheet(self, temp_dir, monkeypatch):
        """Test creating and retrieving a sheet."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        # Create host first (required by foreign key)
        storage.create_host(name='TestHost', host_id='12345')

        sheet = storage.create_sheet(
            spreadsheet_id='abc123def456ghi789jkl012',
            gid='0',
            name='TestLocation',
            momence_host='TestHost',
            lead_source_id='99999',
            enabled=True
        )

        assert sheet['name'] == 'TestLocation'
        assert sheet['momence_host'] == 'TestHost'

        retrieved = storage.get_sheet(sheet['id'])
        assert retrieved['name'] == 'TestLocation'

    def test_get_all_sheets(self, temp_dir, monkeypatch):
        """Test retrieving all sheets."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='TestHost', host_id='12345')
        storage.create_sheet(spreadsheet_id='sheet1_id_abcdefghijklmn', gid='0', name='Location1', momence_host='TestHost', lead_source_id='111')
        storage.create_sheet(spreadsheet_id='sheet2_id_abcdefghijklmn', gid='0', name='Location2', momence_host='TestHost', lead_source_id='222')

        sheets = storage.get_all_sheets()
        assert len(sheets) == 2

    def test_update_sheet(self, temp_dir, monkeypatch):
        """Test updating a sheet."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='TestHost', host_id='12345')
        sheet = storage.create_sheet(
            spreadsheet_id='abc123def456ghi789jkl012',
            gid='0',
            name='OldName',
            momence_host='TestHost',
            lead_source_id='99999'
        )

        updated = storage.update_sheet(sheet['id'], name='NewName', enabled=False)

        assert updated['name'] == 'NewName'
        assert updated['enabled'] is False

    def test_delete_sheet(self, temp_dir, monkeypatch):
        """Test deleting a sheet."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='TestHost', host_id='12345')
        sheet = storage.create_sheet(
            spreadsheet_id='abc123def456ghi789jkl012',
            gid='0',
            name='TestLocation',
            momence_host='TestHost',
            lead_source_id='99999'
        )
        assert storage.get_sheet_count() == 1

        deleted = storage.delete_sheet(sheet['id'])
        assert deleted is True
        assert storage.get_sheet_count() == 0

    def test_create_sheet_without_host_fails(self, temp_dir, monkeypatch):
        """Test that creating sheet without valid host raises error."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        with pytest.raises(ValueError):
            storage.create_sheet(
                spreadsheet_id='abc123def456ghi789jkl012',
                gid='0',
                name='TestLocation',
                momence_host='NonExistentHost',
                lead_source_id='99999'
            )

    def test_delete_host_with_sheets_fails(self, temp_dir, monkeypatch):
        """Test that deleting host with associated sheets raises error."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='TestHost', host_id='12345')
        storage.create_sheet(
            spreadsheet_id='abc123def456ghi789jkl012',
            gid='0',
            name='TestLocation',
            momence_host='TestHost',
            lead_source_id='99999'
        )

        with pytest.raises(ValueError):
            storage.delete_host('TestHost')

    def test_get_sheets_by_host(self, temp_dir, monkeypatch):
        """Test getting sheets for a specific host."""
        monkeypatch.setenv('DATABASE_FILE', str(temp_dir / 'test.db'))

        import importlib
        import storage
        importlib.reload(storage)
        storage.init_database()

        storage.create_host(name='Host1', host_id='111')
        storage.create_host(name='Host2', host_id='222')

        storage.create_sheet(spreadsheet_id='sheet1_id_abcdefghijklmn', gid='0', name='Location1', momence_host='Host1', lead_source_id='1')
        storage.create_sheet(spreadsheet_id='sheet2_id_abcdefghijklmn', gid='0', name='Location2', momence_host='Host1', lead_source_id='2')
        storage.create_sheet(spreadsheet_id='sheet3_id_abcdefghijklmn', gid='0', name='Location3', momence_host='Host2', lead_source_id='3')

        host1_sheets = storage.get_sheets_by_host('Host1')
        assert len(host1_sheets) == 2

        host2_sheets = storage.get_sheets_by_host('Host2')
        assert len(host2_sheets) == 1


