"""
Configuration module for Lead Sheets Monitor.
Handles loading settings, constants, and tenant/sheet configuration.

Designed for Google Cloud Run deployment with environment-based configuration.
Supports Google Cloud Secret Manager for secure secret storage.
"""

import os
import json
import re
import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

# Import secret_manager module for Secret Manager integration
try:
    from secret_manager import (
        get_secret, get_google_credentials_json, get_smtp_password,
        get_dashboard_credentials, get_encryption_key, IS_CLOUD_RUN as SECRETS_CLOUD_RUN
    )
    SECRETS_MODULE_AVAILABLE = True
except ImportError:
    SECRETS_MODULE_AVAILABLE = False
    SECRETS_CLOUD_RUN = False

# Optional encryption support
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

# Schema validation - required for secure configuration
try:
    from jsonschema import validate, ValidationError as SchemaValidationError
    SCHEMA_VALIDATION_AVAILABLE = True
except ImportError:
    SCHEMA_VALIDATION_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "jsonschema module not installed - config validation disabled. "
        "Install with: pip install jsonschema"
    )

# Load environment variables
load_dotenv()

# ============================================================================
# Constants
# ============================================================================

# API timeouts and limits
# Note: Keep timeout under Cloud Run's 60s graceful shutdown window
DEFAULT_API_TIMEOUT_SECONDS = 60
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_RATE_LIMIT_DELAY_SECONDS = 3.0
DEFAULT_RETRY_MAX_ATTEMPTS = 3
DEFAULT_RETRY_BASE_DELAY_SECONDS = 2.0

# Log settings
DEFAULT_LOG_RETENTION_DAYS = 7

# Dead-letter queue settings
DEFAULT_DLQ_MAX_RETRY_ATTEMPTS = 5
DEFAULT_DLQ_RETRY_BACKOFF_HOURS = [1, 2, 4, 8, 24]

# Health server settings
DEFAULT_HEALTH_PORT = 8080

# Response truncation limits for logging/emails
RESPONSE_BODY_TRUNCATE_CHARS = 2000
RESPONSE_BODY_LOG_CHARS = 1000
ERROR_BODY_TRUNCATE_CHARS = 500

# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# File paths (configurable via environment)
# These are evaluated at module load time for backward compatibility
# For dynamic access (e.g., in tests), use get_database_file()
DATABASE_FILE = os.getenv('DATABASE_FILE', './data/lead_monitor.db')
LOG_DIR = os.getenv('LOG_DIR', './logs')
CONFIG_FILE = os.getenv('CONFIG_FILE', './config.json')


def get_database_file() -> str:
    """Get database file path dynamically from environment.

    This function reads the environment variable each time, useful for tests
    that change DATABASE_FILE between test cases.
    """
    return os.getenv('DATABASE_FILE', './data/lead_monitor.db')

# Headers relevant for Cloudflare/API debugging
DIAGNOSTIC_HEADERS = [
    'cf-ray',           # Cloudflare request ID (for support tickets)
    'cf-cache-status',  # Cache hit/miss
    'cf-mitigated',     # Cloudflare challenge/block indicator
    'server',           # Usually "cloudflare" if behind CF
    'content-type',     # Response type (html = block page, json = API error)
    'x-request-id',     # API request tracking
    'retry-after',      # Rate limit retry hint
    'x-ratelimit-remaining',  # Rate limit info
    'x-ratelimit-limit',
]

# Encryption key file path
ENCRYPTION_KEY_FILE = os.getenv('ENCRYPTION_KEY_FILE', './.encryption_key')

# Cloud Run specific settings
CLOUD_RUN_SERVICE = os.getenv('K_SERVICE', '')  # Set by Cloud Run
CLOUD_RUN_REVISION = os.getenv('K_REVISION', '')  # Set by Cloud Run
IS_CLOUD_RUN = bool(CLOUD_RUN_SERVICE)

# Graceful shutdown timeout (Cloud Run sends SIGTERM)
GRACEFUL_SHUTDOWN_TIMEOUT = int(os.getenv('GRACEFUL_SHUTDOWN_TIMEOUT', '10'))


# ============================================================================
# Configuration Dataclass (Immutable)
# ============================================================================

@dataclass(frozen=True)
class AppSettings:
    """
    Immutable application settings.

    This class provides a snapshot of configuration that won't change
    during request processing, avoiding race conditions.
    """
    # Timeouts and retries
    api_timeout_seconds: int = DEFAULT_API_TIMEOUT_SECONDS
    request_timeout_seconds: int = DEFAULT_REQUEST_TIMEOUT_SECONDS
    retry_max_attempts: int = DEFAULT_RETRY_MAX_ATTEMPTS
    retry_base_delay_seconds: float = DEFAULT_RETRY_BASE_DELAY_SECONDS
    rate_limit_delay_seconds: float = DEFAULT_RATE_LIMIT_DELAY_SECONDS

    # Logging
    log_retention_days: int = DEFAULT_LOG_RETENTION_DAYS
    log_format: str = 'text'  # 'text' or 'json' (json recommended for Cloud Run)
    log_level: str = 'INFO'

    # Dead-letter queue
    dlq_enabled: bool = True
    dlq_max_retry_attempts: int = DEFAULT_DLQ_MAX_RETRY_ATTEMPTS
    dlq_retry_backoff_hours: tuple = tuple(DEFAULT_DLQ_RETRY_BACKOFF_HOURS)
    dlq_ttl_days: int = 90  # Days to keep dead letters before cleanup

    # Health server
    health_server_enabled: bool = False
    health_server_port: int = DEFAULT_HEALTH_PORT

    # Dashboard rate limiting
    dashboard_rate_limit_requests: int = 60
    dashboard_rate_limit_window_seconds: int = 60
    dashboard_rate_limit_burst: int = 10
    dashboard_rate_limit_burst_window: int = 5

    # Default values
    default_spreadsheet_id: str = ''

    @classmethod
    def from_dict(cls, settings: Dict[str, Any]) -> 'AppSettings':
        """Create AppSettings from a dictionary."""
        # Handle health server from env or config
        health_port_env = os.getenv('HEALTH_PORT')
        health_config = settings.get('health_server', {})
        health_enabled = health_port_env is not None or health_config.get('enabled', False)
        health_port = int(health_port_env or health_config.get('port', DEFAULT_HEALTH_PORT))

        # Log format - default to json on Cloud Run for structured logging
        log_format = settings.get('log_format', 'json' if IS_CLOUD_RUN else 'text')

        # Dashboard rate limiting
        dashboard_rl = settings.get('dashboard_rate_limiting', {})

        return cls(
            api_timeout_seconds=settings.get('api_timeout_seconds', DEFAULT_API_TIMEOUT_SECONDS),
            request_timeout_seconds=settings.get('request_timeout_seconds', DEFAULT_REQUEST_TIMEOUT_SECONDS),
            retry_max_attempts=settings.get('retry_max_attempts', DEFAULT_RETRY_MAX_ATTEMPTS),
            retry_base_delay_seconds=settings.get('retry_base_delay_seconds', DEFAULT_RETRY_BASE_DELAY_SECONDS),
            rate_limit_delay_seconds=settings.get('rate_limit_delay_seconds', DEFAULT_RATE_LIMIT_DELAY_SECONDS),
            log_retention_days=settings.get('log_retention_days', DEFAULT_LOG_RETENTION_DAYS),
            log_format=log_format,
            log_level=settings.get('log_level', os.getenv('LOG_LEVEL', 'INFO')),
            dlq_enabled=settings.get('dlq_enabled', True),
            dlq_max_retry_attempts=settings.get('dlq_max_retry_attempts', DEFAULT_DLQ_MAX_RETRY_ATTEMPTS),
            dlq_retry_backoff_hours=tuple(settings.get('dlq_retry_backoff_hours', DEFAULT_DLQ_RETRY_BACKOFF_HOURS)),
            dlq_ttl_days=settings.get('dlq_ttl_days', 90),
            health_server_enabled=health_enabled,
            health_server_port=health_port,
            dashboard_rate_limit_requests=dashboard_rl.get('requests_per_minute', 60),
            dashboard_rate_limit_window_seconds=dashboard_rl.get('window_seconds', 60),
            dashboard_rate_limit_burst=dashboard_rl.get('burst_requests', 10),
            dashboard_rate_limit_burst_window=dashboard_rl.get('burst_window_seconds', 5),
            default_spreadsheet_id=settings.get('default_spreadsheet_id', ''),
        )


def get_app_settings() -> AppSettings:
    """
    Get current application settings as an immutable object.

    Returns:
        AppSettings instance with current configuration
    """
    return AppSettings.from_dict(_settings)


# Configuration schema for validation
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "momence_hosts": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "host_id": {"type": "string", "minLength": 1},
                    "token": {"type": "string", "minLength": 1},  # Optional if using Secret Manager
                    "enabled": {"type": "boolean"}
                },
                "required": ["host_id"]  # token can come from Secret Manager
            }
        },
        "sheets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "spreadsheet_id": {"type": "string", "minLength": 10},
                    "gid": {"type": "string"},
                    "tab_name": {"type": "string"},
                    "momence_host": {"type": "string", "minLength": 1},
                    "lead_source_id": {"type": ["string", "integer"]},
                    "enabled": {"type": "boolean"},
                    "notification_email": {"type": "string"}
                },
                "required": ["spreadsheet_id", "momence_host", "lead_source_id"]
            }
        },
        "settings": {
            "type": "object",
            "properties": {
                "log_retention_days": {"type": "integer", "minimum": 1, "maximum": 365},
                "log_format": {"type": "string", "enum": ["text", "json"]},
                "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                "api_timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 300},
                "request_timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
                "rate_limit_delay_seconds": {"type": "number", "minimum": 0},
                "retry_max_attempts": {"type": "integer", "minimum": 1, "maximum": 10},
                "retry_base_delay_seconds": {"type": "number", "minimum": 0.5, "maximum": 60},
                "dlq_enabled": {"type": "boolean"},
                "dlq_max_retry_attempts": {"type": "integer", "minimum": 1, "maximum": 100},
                "dlq_ttl_days": {"type": "integer", "minimum": 1, "maximum": 365},
                "health_server": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "port": {"type": "integer", "minimum": 1024, "maximum": 65535}
                    }
                },
                "dashboard_rate_limiting": {
                    "type": "object",
                    "properties": {
                        "requests_per_minute": {"type": "integer", "minimum": 1, "maximum": 1000},
                        "window_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
                        "burst_requests": {"type": "integer", "minimum": 1, "maximum": 100},
                        "burst_window_seconds": {"type": "integer", "minimum": 1, "maximum": 60}
                    }
                }
            }
        }
    }
}


# ============================================================================
# Encryption Functions
# ============================================================================

def _get_or_create_encryption_key() -> Optional[bytes]:
    """
    Get encryption key from Secret Manager, environment, or file.

    Priority order:
    1. Google Cloud Secret Manager (on Cloud Run)
    2. ENCRYPTION_KEY environment variable
    3. Local key file (.encryption_key)
    4. Generate new key (local development only)

    Returns:
        Encryption key bytes, or None if encryption is not available
    """
    if not ENCRYPTION_AVAILABLE:
        logging.getLogger(__name__).debug("Encryption not available - cryptography module not installed")
        return None

    # First try Secret Manager (on Cloud Run)
    if SECRETS_MODULE_AVAILABLE:
        secret_key = get_encryption_key()
        if secret_key:
            logging.getLogger(__name__).debug("Using encryption key from Secret Manager")
            if isinstance(secret_key, str):
                return secret_key.encode('utf-8')
            return secret_key

    # Then try environment variable
    env_key = os.getenv('ENCRYPTION_KEY')
    if env_key:
        # If passed as string in env, convert to bytes
        # Do not decode! Fernet expects the base64-encoded key
        if isinstance(env_key, str):
            return env_key.encode('utf-8')
        return env_key

    # Try loading from key file
    key_path = Path(ENCRYPTION_KEY_FILE)
    if key_path.exists():
        try:
            with open(key_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to read encryption key from {key_path}: {e}")

    # Generate new key and save it
    logging.getLogger(__name__).info(f"Generating new encryption key at {key_path}")
    key = Fernet.generate_key()
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        with open(key_path, 'wb') as f:
            f.write(key)
        # Set restrictive permissions on key file (Unix only)
        try:
            os.chmod(key_path, 0o600)
        except OSError as e:
            # Expected to fail on Windows
            logging.getLogger(__name__).debug(f"Could not set permissions on key file (expected on Windows): {e}")
        logging.getLogger(__name__).info(f"Encryption key saved to {key_path}")
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save encryption key to {key_path}: {e}")
        # Key still works in memory even if not saved

    return key


def get_fernet() -> Optional['Fernet']:
    """Get Fernet instance for encryption/decryption."""
    if not ENCRYPTION_AVAILABLE:
        return None
    key = _get_or_create_encryption_key()
    if key:
        return Fernet(key)
    return None


def encrypt_value(value: str) -> str:
    """
    Encrypt a string value.

    Args:
        value: String to encrypt

    Returns:
        Base64-encoded encrypted string, or original if encryption unavailable
    """
    if not value:
        return value
    fernet = get_fernet()
    if not fernet:
        logging.getLogger(__name__).debug("Encryption unavailable - returning plaintext value")
        return value
    try:
        encrypted = fernet.encrypt(value.encode())
        return f"ENC:{base64.urlsafe_b64encode(encrypted).decode()}"
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to encrypt value: {type(e).__name__}: {e}")
        return value


def decrypt_value(value: str) -> str:
    """
    Decrypt a string value.

    Args:
        value: Encrypted string (prefixed with "ENC:")

    Returns:
        Decrypted string, or original if not encrypted or decryption fails
    """
    if not value or not isinstance(value, str):
        return value
    if not value.startswith("ENC:"):
        return value
    fernet = get_fernet()
    if not fernet:
        logging.getLogger(__name__).warning("Cannot decrypt value - encryption not available")
        return value
    try:
        encrypted = base64.urlsafe_b64decode(value[4:])
        return fernet.decrypt(encrypted).decode()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to decrypt value: {type(e).__name__}: {e}")
        return value


# ============================================================================
# Configuration Loading
# ============================================================================

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration against schema.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigValidationError: If validation fails
    """
    if not SCHEMA_VALIDATION_AVAILABLE:
        # Log at WARNING level - this is a security concern
        logging.getLogger(__name__).warning(
            "Skipping config schema validation (jsonschema not installed). "
            "Configuration errors may not be detected. Install jsonschema for validation."
        )
        return

    try:
        validate(instance=config, schema=CONFIG_SCHEMA)
    except SchemaValidationError as e:
        raise ConfigValidationError(f"Configuration validation failed: {e.message}")

    # Additional validation: check for path traversal in file paths
    for sheet in config.get('sheets', []):
        spreadsheet_id = sheet.get('spreadsheet_id', '')
        if '..' in spreadsheet_id or '/' in spreadsheet_id or '\\' in spreadsheet_id:
            raise ConfigValidationError(
                f"Invalid spreadsheet_id '{spreadsheet_id}': contains path characters"
            )

    # Validate momence_host references exist
    host_names = set(config.get('momence_hosts', {}).keys())
    for sheet in config.get('sheets', []):
        momence_host = sheet.get('momence_host')
        if momence_host and momence_host not in host_names:
            raise ConfigValidationError(
                f"Sheet '{sheet.get('name', 'unnamed')}' references unknown momence_host '{momence_host}'"
            )


def load_config(validate_schema: bool = True) -> Dict[str, Any]:
    """
    Load Momence hosts and sheets config from JSON file.

    Args:
        validate_schema: Whether to validate against schema (default True)

    Returns:
        Configuration dictionary

    Raises:
        ConfigValidationError: If validation fails or JSON is malformed
    """
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Config file is not valid JSON: {e}")
        except OSError as e:
            raise ConfigValidationError(f"Cannot read config file: {e}")
        if validate_schema:
            validate_config(config)
        return config
    return {'momence_hosts': {}, 'sheets': [], 'schedule': {}}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to JSON file."""
    config_path = Path(CONFIG_FILE)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def reload_config() -> Dict[str, Any]:
    """Reload configuration from file and update global state."""
    global _config, MOMENCE_HOSTS, SHEETS_CONFIG, _settings
    global LOG_RETENTION_DAYS, API_TIMEOUT_SECONDS, RETRY_MAX_ATTEMPTS
    global RETRY_BASE_DELAY, RATE_LIMIT_DELAY, DLQ_ENABLED
    global DLQ_MAX_RETRY_ATTEMPTS, DLQ_RETRY_BACKOFF_HOURS
    global HEALTH_SERVER_ENABLED, HEALTH_SERVER_PORT, LOG_FORMAT
    global DEFAULT_SPREADSHEET_ID, _smtp_config, _email_config

    _config = load_config()
    # Note: MOMENCE_HOSTS and SHEETS_CONFIG are now loaded from database
    # via get_momence_hosts() and get_sheets_config() functions
    # The global vars remain as fallback/cache that gets updated by web server

    _settings = _config.get('settings', {})
    LOG_RETENTION_DAYS = _settings.get('log_retention_days', DEFAULT_LOG_RETENTION_DAYS)
    API_TIMEOUT_SECONDS = _settings.get('api_timeout_seconds', DEFAULT_API_TIMEOUT_SECONDS)
    RETRY_MAX_ATTEMPTS = _settings.get('retry_max_attempts', DEFAULT_RETRY_MAX_ATTEMPTS)
    RETRY_BASE_DELAY = _settings.get('retry_base_delay_seconds', DEFAULT_RETRY_BASE_DELAY_SECONDS)
    RATE_LIMIT_DELAY = _settings.get('rate_limit_delay_seconds', DEFAULT_RATE_LIMIT_DELAY_SECONDS)

    DLQ_ENABLED = _settings.get('dlq_enabled', True)
    DLQ_MAX_RETRY_ATTEMPTS = _settings.get('dlq_max_retry_attempts', DEFAULT_DLQ_MAX_RETRY_ATTEMPTS)
    DLQ_RETRY_BACKOFF_HOURS = _settings.get('dlq_retry_backoff_hours', DEFAULT_DLQ_RETRY_BACKOFF_HOURS)

    _health_config = _settings.get('health_server', {})
    _health_port_env = os.getenv('HEALTH_PORT')
    HEALTH_SERVER_ENABLED = _health_port_env is not None or _health_config.get('enabled', False)
    HEALTH_SERVER_PORT = int(_health_port_env or _health_config.get('port', DEFAULT_HEALTH_PORT))

    LOG_FORMAT = _settings.get('log_format', 'text')
    DEFAULT_SPREADSHEET_ID = _settings.get('default_spreadsheet_id', '')

    _smtp_config = _settings.get('smtp', {})
    _email_config = _settings.get('email', {})

    return _config


# Load initial configuration
_config = load_config()
MOMENCE_HOSTS = _config.get('momence_hosts', {})
SHEETS_CONFIG = _config.get('sheets', [])

# Global settings from config
_settings = _config.get('settings', {})
LOG_RETENTION_DAYS = _settings.get('log_retention_days', DEFAULT_LOG_RETENTION_DAYS)
API_TIMEOUT_SECONDS = _settings.get('api_timeout_seconds', DEFAULT_API_TIMEOUT_SECONDS)
RETRY_MAX_ATTEMPTS = _settings.get('retry_max_attempts', DEFAULT_RETRY_MAX_ATTEMPTS)
RETRY_BASE_DELAY = _settings.get('retry_base_delay_seconds', DEFAULT_RETRY_BASE_DELAY_SECONDS)
RATE_LIMIT_DELAY = _settings.get('rate_limit_delay_seconds', DEFAULT_RATE_LIMIT_DELAY_SECONDS)

# Dead-letter queue settings
DLQ_ENABLED = _settings.get('dlq_enabled', True)
DLQ_MAX_RETRY_ATTEMPTS = _settings.get('dlq_max_retry_attempts', DEFAULT_DLQ_MAX_RETRY_ATTEMPTS)
DLQ_RETRY_BACKOFF_HOURS = _settings.get('dlq_retry_backoff_hours', DEFAULT_DLQ_RETRY_BACKOFF_HOURS)

# Health server settings
_health_config = _settings.get('health_server', {})
_health_port_env = os.getenv('HEALTH_PORT')
HEALTH_SERVER_ENABLED = _health_port_env is not None or _health_config.get('enabled', False)
HEALTH_SERVER_PORT = int(_health_port_env or _health_config.get('port', DEFAULT_HEALTH_PORT))

# Logging format setting
LOG_FORMAT = _settings.get('log_format', 'text')

# Default spreadsheet (for simplified add sheet flow)
DEFAULT_SPREADSHEET_ID = _settings.get('default_spreadsheet_id', '')

# Email settings
_smtp_config = _settings.get('smtp', {})
_email_config = _settings.get('email', {})


# ============================================================================
# Momence Host/Sheet Config Helpers (Database-first with config.json fallback)
# ============================================================================

def _get_hosts_from_db() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Try to load hosts from database.

    Returns:
        Dict of hosts if database has data, None otherwise
    """
    try:
        # Lazy import to avoid circular dependency
        import storage
        if not storage.database_exists():
            return None
        hosts = storage.get_hosts_as_config_dict()
        if hosts:
            return hosts
        return None
    except Exception:
        return None


def _get_sheets_from_db() -> Optional[List[Dict[str, Any]]]:
    """
    Try to load sheets from database.

    Returns:
        List of sheets if database has data, None otherwise
    """
    try:
        # Lazy import to avoid circular dependency
        import storage
        if not storage.database_exists():
            return None
        sheets = storage.get_sheets_as_config_list()
        if sheets:
            return sheets
        return None
    except Exception:
        return None


def get_momence_hosts() -> Dict[str, Dict[str, Any]]:
    """
    Get Momence hosts configuration from database.

    Returns:
        Dictionary of host configurations (empty if database not available)
    """
    db_hosts = _get_hosts_from_db()
    return db_hosts if db_hosts else {}


def get_sheets_config() -> List[Dict[str, Any]]:
    """
    Get sheets configuration from database.

    Returns:
        List of sheet configurations (empty if database not available)
    """
    db_sheets = _get_sheets_from_db()
    return db_sheets if db_sheets else []


def get_host_config(host_name: str) -> Optional[Dict[str, Any]]:
    """Get Momence host configuration by name."""
    hosts = get_momence_hosts()
    return hosts.get(host_name)


def get_sheet_config(spreadsheet_id: str, tab_name: str) -> Optional[Dict[str, Any]]:
    """Get sheet configuration by spreadsheet ID and tab name."""
    for sheet in get_sheets_config():
        if sheet.get('spreadsheet_id') == spreadsheet_id and sheet.get('tab_name') == tab_name:
            return sheet
    return None


def get_sheet_config_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get sheet configuration by display name."""
    for sheet in get_sheets_config():
        if sheet.get('name') == name:
            return sheet
    return None


def get_enabled_sheets() -> List[Dict[str, Any]]:
    """Get list of enabled sheet configurations."""
    return [s for s in get_sheets_config() if s.get('enabled', True)]


# Whitelist of allowed environment variables for ENV: prefix resolution
# This prevents config files from reading arbitrary env vars
ALLOWED_ENV_VARS = frozenset({
    'SMTP_PASSWORD',
    'SMTP_USERNAME',
    'SMTP_HOST',
    'SMTP_FROM_ADDRESS',
    'SLACK_WEBHOOK_URL',
    'DASHBOARD_API_KEY',
    'DASHBOARD_USERNAME',
    'DASHBOARD_PASSWORD',
    'GOOGLE_CREDENTIALS_JSON',
    'ENCRYPTION_KEY',
    'ADMIN_EMAIL',
    'NOTIFICATION_EMAIL',
    'DEFAULT_SPREADSHEET_ID',
})


def resolve_env_value(value: str) -> str:
    """
    Resolve ENV: prefixed values from environment variables.

    Only allows whitelisted environment variables to prevent
    config files from reading arbitrary sensitive env vars.
    """
    if isinstance(value, str) and value.startswith('ENV:'):
        env_var = value[4:]
        if env_var not in ALLOWED_ENV_VARS:
            logging.getLogger(__name__).warning(
                f"Env var '{env_var}' not in allowed list - ignoring. "
                f"Allowed: {', '.join(sorted(ALLOWED_ENV_VARS))}"
            )
            return ''
        return os.getenv(env_var, '')
    return value


def get_smtp_config() -> Dict[str, Any]:
    """
    Get SMTP configuration with Secret Manager and environment variable resolution.

    Security: SMTP password must be provided via Secret Manager or environment variable.
    If password is specified directly in config (not ENV: prefix), it will be ignored
    with a warning logged.

    Priority order for password:
    1. Google Cloud Secret Manager (on Cloud Run)
    2. ENV: prefix in config
    3. SMTP_PASSWORD environment variable
    """
    raw_password = _smtp_config.get('password', '')

    # Security check: password must come from secure source
    password = ''

    # First try Secret Manager (on Cloud Run)
    if SECRETS_MODULE_AVAILABLE:
        secret_password = get_smtp_password()
        if secret_password:
            password = secret_password

    # Then try ENV: prefix or direct env var
    if not password and raw_password:
        if isinstance(raw_password, str) and raw_password.startswith('ENV:'):
            password = resolve_env_value(raw_password)
        elif os.getenv('SMTP_PASSWORD'):
            # Allow direct env var as fallback
            password = os.getenv('SMTP_PASSWORD', '')
        else:
            # Plaintext password in config - refuse to use it
            import logging
            logging.getLogger(__name__).warning(
                "SMTP password specified directly in config is not allowed. "
                "Use ENV:VARIABLE_NAME format or set SMTP_PASSWORD environment variable."
            )

    return {
        'host': resolve_env_value(_smtp_config.get('host', '')),
        'port': _smtp_config.get('port', 587),
        'username': resolve_env_value(_smtp_config.get('username', '')),
        'password': password,
        'from_address': resolve_env_value(_smtp_config.get('from_address', '')),
        'from_name': _smtp_config.get('from_name', 'Lead Monitor'),
        'use_tls': _smtp_config.get('use_tls', True),
    }


def get_email_config() -> Dict[str, Any]:
    """Get email notification configuration."""
    return _email_config


def resolve_email_list(recipients: List[str]) -> List[str]:
    """Resolve email list, expanding environment variables."""
    result = []
    for r in recipients:
        resolved = resolve_env_value(r)
        if resolved:
            # Handle comma-separated lists in env vars
            result.extend([e.strip() for e in resolved.split(',') if e.strip()])
    return result


# ============================================================================
# Startup Validation
# ============================================================================

class StartupValidationError(Exception):
    """Raised when required configuration is missing at startup."""
    pass


def validate_startup_requirements(require_google_creds: bool = True) -> List[str]:
    """
    Validate that required configuration is present at startup.

    Checks Secret Manager first (on Cloud Run), then falls back to environment variables.

    Args:
        require_google_creds: Whether to require Google credentials (default True)

    Returns:
        List of warning messages (non-fatal issues)

    Raises:
        StartupValidationError: If critical configuration is missing
    """
    errors = []
    warnings = []

    # Check Google credentials if required
    if require_google_creds:
        # Try Secret Manager first, then env var
        google_creds = None
        if SECRETS_MODULE_AVAILABLE:
            google_creds = get_google_credentials_json()
        if not google_creds:
            google_creds = os.getenv('GOOGLE_CREDENTIALS_JSON')

        if not google_creds:
            errors.append(
                "Google credentials not found. Set 'google-credentials-json' in Secret Manager "
                "or GOOGLE_CREDENTIALS_JSON environment variable"
            )
        else:
            # Validate it's valid JSON
            try:
                creds_data = json.loads(google_creds)
                if not creds_data.get('client_email'):
                    errors.append("Google credentials missing 'client_email' field")
                if not creds_data.get('private_key'):
                    errors.append("Google credentials missing 'private_key' field")
            except json.JSONDecodeError as e:
                errors.append(f"Google credentials is not valid JSON: {e}")

    # Check config file exists
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        warnings.append(f"Config file not found at {CONFIG_FILE} - will create empty config")

    # Check for SMTP configuration if email settings are in config
    smtp_cfg = _smtp_config
    if smtp_cfg:
        if smtp_cfg.get('username') and not smtp_cfg.get('password'):
            if not os.getenv('SMTP_PASSWORD'):
                warnings.append("SMTP username configured but password not set (set SMTP_PASSWORD env var)")

    # Check dashboard authentication (Secret Manager or env vars)
    dashboard_api_key = None
    dashboard_username = None
    dashboard_password = None

    if SECRETS_MODULE_AVAILABLE:
        creds = get_dashboard_credentials()
        dashboard_api_key = creds.get('api_key')
        dashboard_username = creds.get('username')
        dashboard_password = creds.get('password')

    # Fall back to env vars
    if not dashboard_api_key:
        dashboard_api_key = os.getenv('DASHBOARD_API_KEY')
    if not dashboard_username:
        dashboard_username = os.getenv('DASHBOARD_USERNAME')
    if not dashboard_password:
        dashboard_password = os.getenv('DASHBOARD_PASSWORD')

    if not dashboard_api_key and not (dashboard_username and dashboard_password):
        warnings.append(
            "Dashboard authentication not configured! Set secrets in Secret Manager or "
            "DASHBOARD_API_KEY/DASHBOARD_USERNAME/DASHBOARD_PASSWORD environment variables."
        )

    # Check data directory is writable
    data_dir = Path(DATABASE_FILE).parent
    if data_dir.exists():
        test_file = data_dir / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            errors.append(f"Data directory {data_dir} is not writable: {e}")

    if errors:
        raise StartupValidationError(
            "Startup validation failed:\n  - " + "\n  - ".join(errors)
        )

    return warnings


def log_startup_warnings(warnings: List[str], logger_instance=None):
    """Log startup warnings."""
    if not logger_instance:
        logger_instance = logging.getLogger(__name__)

    for warning in warnings:
        logger_instance.warning(f"Startup warning: {warning}")
