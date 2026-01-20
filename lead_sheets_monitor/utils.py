"""
Utility functions for Lead Sheets Monitor.
Includes logging, date/time helpers, validation, and hashing.
"""

import sys
import time
import json
import html
import hashlib
import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

from config import (
    LOG_DIR, LOG_RETENTION_DAYS, LOG_FORMAT, EMAIL_REGEX,
    DIAGNOSTIC_HEADERS
)

# Optional phone validation
try:
    import phonenumbers
    PHONE_VALIDATION_AVAILABLE = True
except ImportError:
    PHONE_VALIDATION_AVAILABLE = False


# ============================================================================
# Date/Time Helpers
# ============================================================================

def utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


# ============================================================================
# Logging
# ============================================================================

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": utc_now().isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Add extra fields if present
        for key in ['tenant', 'lead_email', 'sheet_name', 'duration_ms', 'error_type', 'location']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class DailyRotatingFileHandler(logging.FileHandler):
    """
    A file handler that rotates to a new file at midnight UTC.
    Uses YYYYMMDD.log naming format.
    """

    def __init__(self, log_dir: Path, encoding: str = 'utf-8'):
        self.log_dir = log_dir
        self._current_date = utc_now().strftime('%Y%m%d')
        log_file = log_dir / f'{self._current_date}.log'
        super().__init__(log_file, encoding=encoding)

    def emit(self, record):
        """Emit a record, rotating file if date has changed."""
        today = utc_now().strftime('%Y%m%d')
        if today != self._current_date:
            self._rotate_to_new_day(today)
        super().emit(record)

    def _rotate_to_new_day(self, new_date: str):
        """Close current file and open new one for the new date."""
        self._current_date = new_date
        # Close current stream
        if self.stream:
            self.stream.close()
            self.stream = None
        # Update base filename
        self.baseFilename = str(self.log_dir / f'{new_date}.log')
        # Open new stream (will be done lazily by parent on next emit)
        self.stream = self._open()


def setup_logging() -> logging.Logger:
    """Configure logging with YYYYMMDD.log format and retention."""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatter based on config (text or json)
    if LOG_FORMAT == 'json':
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s UTC - %(levelname)s - %(message)s')
        formatter.converter = time.gmtime  # Use UTC for log timestamps

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Check if we already have our rotating handler
    has_rotating_handler = any(
        isinstance(h, DailyRotatingFileHandler)
        for h in root_logger.handlers
    )

    # Remove any old-style FileHandlers and add our rotating handler
    if not has_rotating_handler:
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler) and not isinstance(handler, DailyRotatingFileHandler):
                handler.close()
                root_logger.removeHandler(handler)

        file_handler = DailyRotatingFileHandler(log_dir, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)

    # Add console handler only if not already present
    has_console_handler = any(
        isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
        for h in root_logger.handlers
    )
    if not has_console_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

    # Clean up old log files
    cleanup_old_logs(log_dir, keep_days=LOG_RETENTION_DAYS)

    return logging.getLogger(__name__)


def cleanup_old_logs(log_dir: Path, keep_days: int = 7):
    """Remove log files older than keep_days."""
    cutoff_date = utc_now() - timedelta(days=keep_days)

    for log_file in log_dir.glob('*.log'):
        # Parse YYYYMMDD from filename
        try:
            date_str = log_file.stem
            # Parse as UTC datetime for comparison
            file_date = datetime.strptime(date_str, '%Y%m%d').replace(tzinfo=timezone.utc)
            if file_date < cutoff_date:
                log_file.unlink()
                print(f"Removed old log file: {log_file.name}")
        except ValueError:
            # Skip files that don't match YYYYMMDD format
            pass


# Initialize logger
logger = setup_logging()


# ============================================================================
# Validation Functions
# ============================================================================

# Optional email validation with email-validator library
try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.

    Uses email-validator library if available for more accurate validation,
    falls back to regex otherwise.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()
    if not email:
        return False

    if EMAIL_VALIDATOR_AVAILABLE:
        try:
            # check_deliverability=False for faster validation without DNS lookup
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
    else:
        # Fallback to regex
        return EMAIL_REGEX.match(email) is not None


def normalize_email(email: str) -> Optional[str]:
    """
    Normalize and validate an email address.

    Uses email-validator library if available for proper normalization
    (lowercase domain, handle unicode, etc.).

    Args:
        email: Email address to normalize

    Returns:
        Normalized email address if valid, None otherwise
    """
    if not email or not isinstance(email, str):
        return None

    email = email.strip()
    if not email:
        return None

    if EMAIL_VALIDATOR_AVAILABLE:
        try:
            result = validate_email(email, check_deliverability=False)
            return result.normalized
        except EmailNotValidError:
            return None
    else:
        # Basic normalization without library
        if EMAIL_REGEX.match(email):
            return email.lower()
        return None


def normalize_phone(phone: str, default_region: str = "US") -> str:
    """
    Normalize phone number to E.164 format if possible.

    Args:
        phone: Phone number string to normalize
        default_region: Default region code for parsing (default: US)

    Returns:
        E.164 formatted phone number if valid, or cleaned original if not
    """
    if not phone:
        return ''

    # Strip common prefixes (e.g., "p:" from some forms)
    cleaned = phone.strip()
    if cleaned.lower().startswith('p:'):
        cleaned = cleaned[2:].strip()

    if not PHONE_VALIDATION_AVAILABLE:
        return cleaned

    try:
        parsed = phonenumbers.parse(cleaned, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        else:
            logger.debug(f"Phone number '{cleaned}' is not valid for region {default_region}")
    except phonenumbers.NumberParseException as e:
        logger.debug(f"Could not parse phone number '{cleaned}': {e}")
    except Exception as e:
        logger.warning(f"Unexpected error normalizing phone '{cleaned}': {type(e).__name__}: {e}")

    return cleaned  # Return cleaned original if can't normalize


def escape_html(text: str) -> str:
    """
    Escape HTML special characters to prevent injection.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped string
    """
    if not text:
        return ''
    return html.escape(str(text))


# ============================================================================
# Hashing
# ============================================================================

def compute_entry_hash(entry: dict, sheet_id: str = '', gid: str = '') -> str:
    """
    Compute a stable hash for a lead entry to detect duplicates.

    Handles both camelCase (from Momence API) and snake_case (from sheets) field names.
    Uses SHA256 for better collision resistance.

    Args:
        entry: Dictionary containing lead data
        sheet_id: Optional spreadsheet ID for additional uniqueness
        gid: Optional sheet tab ID for additional uniqueness

    Returns:
        32-character hex string hash of the entry
    """
    # Normalize field access - check both camelCase and snake_case variants
    def get_field(camel: str, snake: str) -> str:
        return str(entry.get(camel, entry.get(snake, ''))).strip().lower()

    # Use key fields that identify a unique lead (normalized to lowercase)
    email = get_field('email', 'email')
    first_name = get_field('firstName', 'first_name')
    last_name = get_field('lastName', 'last_name')
    phone = get_field('phoneNumber', 'phone_number')
    created_time = get_field('created_time', 'created_time')

    # Build hash input with consistent ordering
    parts = [email, first_name, last_name, phone, created_time]

    # Include sheet identifiers if provided (for row-level uniqueness across sheets)
    if sheet_id or gid:
        parts = [sheet_id, gid] + parts

    hash_input = '|'.join(parts)
    return hashlib.sha256(hash_input.encode()).hexdigest()[:32]


# ============================================================================
# API Helpers
# ============================================================================

# Browser signatures for rotating user agents (updated 2024)
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def get_random_user_agent() -> str:
    """Get a random user agent for each request to avoid fingerprinting."""
    return random.choice(USER_AGENTS)


def get_api_headers(include_user_agent: bool = False) -> dict:
    """
    Get minimal headers for API requests.

    Note: Content-Type is NOT set here because requests.post(json=...)
    automatically sets 'Content-Type: application/json; charset=utf-8'.

    Args:
        include_user_agent: If True, include a randomized User-Agent header

    Returns:
        Dict of HTTP headers
    """
    headers = {
        "Accept": "application/json",
    }
    if include_user_agent:
        headers["User-Agent"] = get_random_user_agent()
    return headers


def extract_diagnostic_headers(headers: dict) -> dict:
    """Extract only relevant headers for debugging Cloudflare/API issues."""
    lower_diag = [h.lower() for h in DIAGNOSTIC_HEADERS]
    return {k: v for k, v in headers.items() if k.lower() in lower_diag}


def categorize_error(status_code: int, headers: dict, body: str) -> Tuple[str, bool]:
    """
    Categorize error type for better diagnosis and determine retryability.

    Uses ErrorType enum constants for consistent error type strings.

    Error type naming convention:
    - cloudflare_*: Cloudflare-related errors
    - api_*: API client errors (4xx)
    - server_*: Server errors (5xx)
    - network_*: Network/connection errors

    Args:
        status_code: HTTP status code
        headers: Response headers dict
        body: Response body string

    Returns:
        Tuple of (error_type: str, is_retryable: bool)
    """
    # Import here to avoid circular dependency at module load time
    from error_types import ErrorType, ERROR_RETRYABILITY

    content_type = headers.get('content-type', headers.get('Content-Type', '')).lower()
    server = headers.get('server', headers.get('Server', '')).lower()

    # Check for cf-mitigated header (case-insensitive)
    has_cf_mitigated = any(k.lower() == 'cf-mitigated' for k in headers.keys())

    # Cloudflare block/challenge - may be temporary, retry with backoff
    if has_cf_mitigated:
        return (ErrorType.CLOUDFLARE_BLOCKED.value, ERROR_RETRYABILITY[ErrorType.CLOUDFLARE_BLOCKED])
    if 'text/html' in content_type and 'cloudflare' in server:
        body_lower = body.lower()
        if 'challenge' in body_lower or 'captcha' in body_lower:
            return (ErrorType.CLOUDFLARE_CHALLENGE.value, ERROR_RETRYABILITY[ErrorType.CLOUDFLARE_CHALLENGE])
        if 'blocked' in body_lower or 'banned' in body_lower:
            return (ErrorType.CLOUDFLARE_BLOCKED.value, ERROR_RETRYABILITY[ErrorType.CLOUDFLARE_BLOCKED])
        return (ErrorType.CLOUDFLARE_ERROR.value, ERROR_RETRYABILITY[ErrorType.CLOUDFLARE_ERROR])

    # Rate limiting - always retry with backoff
    if status_code == 429:
        return (ErrorType.API_RATE_LIMITED.value, ERROR_RETRYABILITY[ErrorType.API_RATE_LIMITED])
    has_ratelimit = any(k.lower() in ['retry-after', 'x-ratelimit-remaining'] for k in headers.keys())
    if has_ratelimit and status_code >= 400:
        return (ErrorType.API_RATE_LIMITED.value, ERROR_RETRYABILITY[ErrorType.API_RATE_LIMITED])

    # Client errors - generally NOT retryable
    if status_code == 400:
        return (ErrorType.API_BAD_REQUEST.value, ERROR_RETRYABILITY[ErrorType.API_BAD_REQUEST])
    if status_code == 401:
        return (ErrorType.API_UNAUTHORIZED.value, ERROR_RETRYABILITY[ErrorType.API_UNAUTHORIZED])
    if status_code == 403:
        return (ErrorType.API_FORBIDDEN.value, ERROR_RETRYABILITY[ErrorType.API_FORBIDDEN])
    if status_code == 404:
        return (ErrorType.API_NOT_FOUND.value, ERROR_RETRYABILITY[ErrorType.API_NOT_FOUND])
    if status_code == 409:
        return (ErrorType.API_CONFLICT.value, ERROR_RETRYABILITY[ErrorType.API_CONFLICT])
    if status_code == 422:
        return (ErrorType.API_VALIDATION_ERROR.value, ERROR_RETRYABILITY[ErrorType.API_VALIDATION_ERROR])

    # Server errors - retryable
    if status_code >= 500:
        if status_code == 502:
            return (ErrorType.SERVER_BAD_GATEWAY.value, ERROR_RETRYABILITY[ErrorType.SERVER_BAD_GATEWAY])
        if status_code == 503:
            return (ErrorType.SERVER_UNAVAILABLE.value, ERROR_RETRYABILITY[ErrorType.SERVER_UNAVAILABLE])
        if status_code == 504:
            return (ErrorType.SERVER_GATEWAY_TIMEOUT.value, ERROR_RETRYABILITY[ErrorType.SERVER_GATEWAY_TIMEOUT])
        return (ErrorType.SERVER_ERROR.value, ERROR_RETRYABILITY[ErrorType.SERVER_ERROR])

    # Other 4xx - not retryable
    if 400 <= status_code < 500:
        return (f'api_error_{status_code}', False)

    return (f'http_error_{status_code}', True)


def categorize_error_simple(status_code: int, headers: dict, body: str) -> str:
    """
    Backwards-compatible wrapper that returns only the error type string.

    Args:
        status_code: HTTP status code
        headers: Response headers dict
        body: Response body string

    Returns:
        Error type string
    """
    error_type, _ = categorize_error(status_code, headers, body)
    return error_type


def is_error_retryable(status_code: int, headers: dict, body: str) -> bool:
    """
    Check if an error should be retried based on status code and response.

    Args:
        status_code: HTTP status code
        headers: Response headers dict
        body: Response body string

    Returns:
        True if the error should be retried
    """
    _, is_retryable = categorize_error(status_code, headers, body)
    return is_retryable
