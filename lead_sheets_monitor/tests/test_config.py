"""
Tests for config.py - configuration loading and validation.
"""

import pytest
import json
import os
from pathlib import Path


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, temp_dir, monkeypatch):
        """Test validation passes for valid config."""
        config = {
            'tenants': {
                'TestTenant': {
                    'host_id': '12345',
                    'token': 'test-token',
                    'enabled': True
                }
            },
            'sheets': [
                {
                    'name': 'Test Sheet',
                    'spreadsheet_id': 'valid-spreadsheet-id-1234567890',
                    'tenant': 'TestTenant',
                    'lead_source_id': 123
                }
            ]
        }

        config_path = temp_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        monkeypatch.setenv('CONFIG_FILE', str(config_path))

        # Re-import to pick up new config
        import importlib
        import config as config_module
        importlib.reload(config_module)

        # Should not raise
        config_module.validate_config(config)

    def test_validate_invalid_spreadsheet_id(self, temp_dir):
        """Test validation fails for path traversal in spreadsheet ID."""
        import importlib
        import config as config_module

        config = {
            'tenants': {'Test': {'host_id': '1', 'token': 't'}},
            'sheets': [
                {
                    'spreadsheet_id': '../etc/passwd',
                    'tenant': 'Test',
                    'lead_source_id': 1
                }
            ]
        }

        with pytest.raises(config_module.ConfigValidationError):
            config_module.validate_config(config)

    def test_validate_missing_tenant_reference(self, temp_dir):
        """Test validation fails for missing tenant reference."""
        import importlib
        import config as config_module

        config = {
            'tenants': {'ExistingTenant': {'host_id': '1', 'token': 't'}},
            'sheets': [
                {
                    'spreadsheet_id': 'valid-id-1234567890123456',
                    'tenant': 'NonExistentTenant',
                    'lead_source_id': 1
                }
            ]
        }

        with pytest.raises(config_module.ConfigValidationError):
            config_module.validate_config(config)


class TestAppSettings:
    """Tests for AppSettings dataclass."""

    def test_app_settings_from_dict(self):
        """Test creating AppSettings from dict."""
        from config import AppSettings

        settings_dict = {
            'api_timeout_seconds': 120,
            'retry_max_attempts': 5,
            'dlq_enabled': True,
            'dlq_max_retry_attempts': 10
        }

        settings = AppSettings.from_dict(settings_dict)

        assert settings.api_timeout_seconds == 120
        assert settings.retry_max_attempts == 5
        assert settings.dlq_enabled is True
        assert settings.dlq_max_retry_attempts == 10

    def test_app_settings_defaults(self):
        """Test AppSettings uses defaults for missing values."""
        from config import AppSettings

        settings = AppSettings.from_dict({})

        # Should have default values
        assert settings.api_timeout_seconds > 0
        assert settings.retry_max_attempts > 0
        assert settings.log_retention_days > 0

    def test_app_settings_immutable(self):
        """Test AppSettings is immutable (frozen)."""
        from config import AppSettings

        settings = AppSettings.from_dict({})

        with pytest.raises(Exception):  # FrozenInstanceError
            settings.api_timeout_seconds = 999


class TestEncryption:
    """Tests for encryption functions."""

    def test_encrypt_decrypt_roundtrip(self, temp_dir, monkeypatch):
        """Test encrypting and decrypting a value."""
        monkeypatch.setenv('ENCRYPTION_KEY_FILE', str(temp_dir / '.encryption_key'))

        import importlib
        import config as config_module
        importlib.reload(config_module)

        original = 'my-secret-token'
        encrypted = config_module.encrypt_value(original)

        # Should be prefixed with ENC:
        if encrypted.startswith('ENC:'):
            decrypted = config_module.decrypt_value(encrypted)
            assert decrypted == original
        else:
            # Encryption not available - value returned unchanged
            assert encrypted == original

    def test_decrypt_non_encrypted_value(self):
        """Test decrypting a non-encrypted value returns it unchanged."""
        from config import decrypt_value

        plain = 'not-encrypted'
        result = decrypt_value(plain)

        assert result == plain

    def test_decrypt_empty_value(self):
        """Test decrypting empty/None values."""
        from config import decrypt_value

        assert decrypt_value('') == ''
        assert decrypt_value(None) is None


class TestEnvResolution:
    """Tests for environment variable resolution."""

    def test_resolve_env_value(self, monkeypatch):
        """Test resolving ENV: prefixed values."""
        from config import resolve_env_value

        monkeypatch.setenv('TEST_VAR', 'secret-value')

        result = resolve_env_value('ENV:TEST_VAR')
        assert result == 'secret-value'

    def test_resolve_non_env_value(self):
        """Test non-ENV: values are returned unchanged."""
        from config import resolve_env_value

        result = resolve_env_value('plain-value')
        assert result == 'plain-value'

    def test_resolve_missing_env_var(self, monkeypatch):
        """Test resolving missing env var returns empty string."""
        from config import resolve_env_value

        # Ensure the var doesn't exist
        monkeypatch.delenv('NONEXISTENT_VAR', raising=False)

        result = resolve_env_value('ENV:NONEXISTENT_VAR')
        assert result == ''


class TestSmtpConfig:
    """Tests for SMTP configuration."""

    def test_smtp_password_from_env(self, temp_dir, monkeypatch):
        """Test SMTP password can be loaded from env var."""
        monkeypatch.setenv('SMTP_PASSWORD', 'secret-password')
        monkeypatch.setenv('CONFIG_FILE', str(temp_dir / 'config.json'))

        config = {
            'settings': {
                'smtp': {
                    'host': 'smtp.example.com',
                    'port': 587,
                    'username': 'user@example.com'
                }
            },
            'tenants': {},
            'sheets': []
        }

        config_path = temp_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)

        import importlib
        import config as config_module
        importlib.reload(config_module)

        smtp_config = config_module.get_smtp_config()
        assert smtp_config['password'] == 'secret-password'


class TestStartupValidation:
    """Tests for startup validation."""

    def test_validate_missing_google_creds(self, temp_dir, monkeypatch):
        """Test validation fails without Google credentials."""
        monkeypatch.delenv('GOOGLE_CREDENTIALS_JSON', raising=False)
        monkeypatch.setenv('CONFIG_FILE', str(temp_dir / 'config.json'))

        # Create minimal config
        config_path = temp_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump({'tenants': {}, 'sheets': []}, f)

        import importlib
        import config as config_module
        importlib.reload(config_module)

        with pytest.raises(config_module.StartupValidationError):
            config_module.validate_startup_requirements(require_google_creds=True)

    def test_validate_invalid_google_creds_json(self, temp_dir, monkeypatch):
        """Test validation fails with invalid JSON credentials."""
        monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', 'not-valid-json')
        monkeypatch.setenv('CONFIG_FILE', str(temp_dir / 'config.json'))

        config_path = temp_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump({'tenants': {}, 'sheets': []}, f)

        import importlib
        import config as config_module
        importlib.reload(config_module)

        with pytest.raises(config_module.StartupValidationError):
            config_module.validate_startup_requirements(require_google_creds=True)

    def test_validate_skips_google_creds_when_not_required(self, temp_dir, monkeypatch):
        """Test validation passes without Google creds when not required."""
        monkeypatch.delenv('GOOGLE_CREDENTIALS_JSON', raising=False)
        monkeypatch.setenv('CONFIG_FILE', str(temp_dir / 'config.json'))

        config_path = temp_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump({'tenants': {}, 'sheets': []}, f)

        import importlib
        import config as config_module
        importlib.reload(config_module)

        # Should not raise
        warnings = config_module.validate_startup_requirements(require_google_creds=False)
        assert isinstance(warnings, list)
