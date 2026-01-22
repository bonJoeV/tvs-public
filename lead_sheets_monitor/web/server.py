"""
Web server module for Lead Sheets Monitor dashboard.
Contains the HTTP server, dashboard HTML, and API endpoints.
"""

import base64
import hmac
import ipaddress
import json
import os
import time
import secrets
import threading
import urllib.parse
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from config import (
    MOMENCE_HOSTS, SHEETS_CONFIG, CONFIG_FILE,
    DLQ_ENABLED, DLQ_MAX_RETRY_ATTEMPTS, DLQ_RETRY_BACKOFF_HOURS,
    RATE_LIMIT_DELAY, LOG_FORMAT, HEALTH_SERVER_ENABLED, HEALTH_SERVER_PORT,
    DEFAULT_SPREADSHEET_ID, _config,
    get_momence_hosts, get_sheets_config
)
from utils import utc_now, escape_html, logger
import storage
from sheets import get_google_sheets_service, discover_fb_lead_tabs, parse_spreadsheet_url
from momence import create_momence_lead
from notifications import send_test_location_email


# ============================================================================
# Version Information
# ============================================================================

def _get_git_version() -> str:
    """Get the current git commit hash for version display."""
    # First check environment variable (set during Docker build)
    version = os.getenv('APP_VERSION', '')
    if version:
        return version

    # Try to get from git
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        # Git not available or not in a git repo - expected in production
        pass

    return 'dev'


def _get_build_time() -> str:
    """Get the build timestamp (ISO format, set during Docker build)."""
    return os.getenv('BUILD_TIME', '')


APP_VERSION = _get_git_version()
BUILD_TIME = _get_build_time()


# ============================================================================
# Authentication Configuration
# ============================================================================

# Try to load credentials from Secret Manager first (on Cloud Run), then env vars
def _get_dashboard_credentials():
    """Get dashboard credentials from Secret Manager or environment variables."""
    api_key = os.getenv('DASHBOARD_API_KEY', '')
    username = os.getenv('DASHBOARD_USERNAME', '')
    password = os.getenv('DASHBOARD_PASSWORD', '')

    # Try Secret Manager if available
    try:
        from secret_manager import get_dashboard_credentials
        creds = get_dashboard_credentials()
        if creds.get('api_key'):
            api_key = creds['api_key']
        if creds.get('username'):
            username = creds['username']
        if creds.get('password'):
            password = creds['password']
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to get dashboard credentials from Secret Manager: {e}")

    return api_key, username, password

DASHBOARD_API_KEY, DASHBOARD_USERNAME, DASHBOARD_PASSWORD = _get_dashboard_credentials()

# Trusted proxy IPs/networks for X-Forwarded-For header handling
# Format: comma-separated list of IPs or CIDR notation
# Example: "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,127.0.0.1"
_trusted_proxies_str = os.getenv('TRUSTED_PROXY_IPS', '127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16')
TRUSTED_PROXY_NETWORKS: List[ipaddress.IPv4Network] = []
for proxy in _trusted_proxies_str.split(','):
    proxy = proxy.strip()
    if proxy:
        try:
            # Handle single IPs and CIDR notation
            if '/' not in proxy:
                proxy = f"{proxy}/32"
            TRUSTED_PROXY_NETWORKS.append(ipaddress.ip_network(proxy, strict=False))
        except ValueError as e:
            logger.warning(f"Invalid trusted proxy IP/network '{proxy}': {e}")

# Authentication is required if either API key or basic auth is configured
AUTH_ENABLED = bool(DASHBOARD_API_KEY or (DASHBOARD_USERNAME and DASHBOARD_PASSWORD))

# Thread locks for shared state
_csrf_lock = threading.Lock()
_rate_limit_lock = threading.Lock()
_health_state_lock = threading.Lock()
_session_lock = threading.Lock()

# ============================================================================
# Session Management (Database-backed for persistence across restarts)
# ============================================================================

# Session configuration
SESSION_COOKIE_NAME = 'lead_monitor_session'
SESSION_EXPIRY_SECONDS = 86400  # 24 hours (also defined in storage.py)

# In-memory cache for session lookups (optional optimization)
# Falls back to database if not in cache
_session_cache: Dict[str, Dict[str, Any]] = {}
SESSION_CACHE_MAX_SIZE = 100

# Admin activity logging is handled by the storage module (SQLite)


def _generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)


def _create_session(username: str = 'admin', ip_address: str = 'unknown') -> str:
    """
    Create a new session and return the token.

    Uses database-backed storage for persistence across restarts.
    """
    token = _generate_session_token()

    # Store in database (primary storage)
    storage.create_session(token, username, ip_address)

    # Also cache in memory for faster lookups
    with _session_lock:
        _session_cache[token] = {
            'username': username,
            'ip': ip_address,
            'created': time.time()
        }
        # Cleanup cache if over limit - remove expired sessions first
        if len(_session_cache) > SESSION_CACHE_MAX_SIZE:
            now = time.time()
            # Remove sessions older than 24 hours first
            expired = [k for k, v in _session_cache.items()
                       if now - v.get('created', 0) > 86400]
            for k in expired:
                del _session_cache[k]
            # If still over limit, remove oldest
            if len(_session_cache) > SESSION_CACHE_MAX_SIZE:
                # Sort by created time and remove oldest
                sorted_keys = sorted(_session_cache.keys(),
                                     key=lambda k: _session_cache[k].get('created', 0))
                keys_to_remove = sorted_keys[:len(_session_cache) - SESSION_CACHE_MAX_SIZE]
                for key in keys_to_remove:
                    del _session_cache[key]

    return token


def _validate_session(token: str) -> bool:
    """
    Validate a session token and update last accessed time.

    Uses database-backed storage for persistence across restarts.
    """
    if not token:
        return False

    # Try database validation (handles expiry and updates last_accessed)
    session_data = storage.validate_session(token)
    if session_data:
        # Update cache
        with _session_lock:
            _session_cache[token] = {
                'username': session_data.get('username'),
                'ip': session_data.get('ip_address')
            }
        return True

    # Remove from cache if invalid
    with _session_lock:
        if token in _session_cache:
            del _session_cache[token]

    return False


def _invalidate_session(token: str):
    """Invalidate/delete a session."""
    # Remove from database
    storage.invalidate_session(token)

    # Remove from cache
    with _session_lock:
        if token in _session_cache:
            del _session_cache[token]


def _get_session_info(token: str) -> Optional[Dict[str, Any]]:
    """Get session info for a token."""
    if not token:
        return None

    # Check cache first
    with _session_lock:
        if token in _session_cache:
            return _session_cache[token]

    # Fall back to database
    return storage.get_session_info(token)


def _get_session_cookie(handler) -> Optional[str]:
    """Extract session token from cookies."""
    cookie_header = handler.headers.get('Cookie', '')
    if not cookie_header:
        return None

    for cookie in cookie_header.split(';'):
        cookie = cookie.strip()
        if cookie.startswith(f'{SESSION_COOKIE_NAME}='):
            return cookie[len(SESSION_COOKIE_NAME) + 1:]

    return None


# ============================================================================
# Admin Activity Logging (now uses SQLite via storage module)
# ============================================================================

def log_admin_activity(action: str, details: str = '', session_token: str = None, ip_address: str = None, username: str = None, user_agent: str = None):
    """
    Log an admin activity to the database.

    Args:
        action: The action performed (e.g., 'login', 'logout', 'create_tenant', 'delete_sheet')
        details: Additional details about the action
        session_token: The session token (to link activities)
        ip_address: Client IP address
        username: The username (for login events)
        user_agent: Client user agent string
    """
    # Get session info if available
    session_info = None
    resolved_username = username
    resolved_ip = ip_address

    if session_token:
        with _session_lock:
            session_info = _session_cache.get(session_token)
            if session_info:
                if not resolved_username:
                    resolved_username = session_info.get('username')
                if not resolved_ip:
                    resolved_ip = session_info.get('ip')

    # Truncate session token for privacy
    session_id = session_token[:8] + '...' if session_token else None

    # Log to SQLite via storage module
    storage.log_admin_activity(
        action=action,
        details=details,
        username=resolved_username,
        ip_address=resolved_ip,
        session_id=session_id,
        user_agent=user_agent
    )


def get_admin_activity_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Get the most recent admin activity entries from the database."""
    return storage.get_admin_activity_log(limit=limit)


def _build_login_page(error_message: str = '', csrf_token: str = '') -> str:
    """Build the login page HTML."""
    if not csrf_token:
        csrf_token = generate_csrf_token()

    error_html = ''
    if error_message:
        error_html = f'<div class="error-message">{escape_html(error_message)}</div>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" type="image/png" href="/favicon.ico">
        <title>Login - Lead Monitor Dashboard</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .login-container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                width: 100%;
                max-width: 400px;
                overflow: hidden;
            }}
            .login-header {{
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                padding: 32px 24px;
                text-align: center;
            }}
            .login-header h1 {{
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            .login-header p {{
                opacity: 0.9;
                font-size: 14px;
            }}
            .login-icon {{
                width: 64px;
                height: 64px;
                background: rgba(255,255,255,0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 16px;
                font-size: 28px;
            }}
            .login-form {{
                padding: 32px 24px;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            .form-group label {{
                display: block;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                margin-bottom: 8px;
            }}
            .form-group input {{
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.2s, box-shadow 0.2s;
            }}
            .form-group input:focus {{
                outline: none;
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }}
            .form-group input::placeholder {{
                color: #9ca3af;
            }}
            .login-btn {{
                width: 100%;
                padding: 14px 24px;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .login-btn:hover {{
                transform: translateY(-1px);
                box-shadow: 0 10px 20px -10px rgba(99, 102, 241, 0.5);
            }}
            .login-btn:active {{
                transform: translateY(0);
            }}
            .error-message {{
                background: #fef2f2;
                border: 1px solid #fecaca;
                color: #dc2626;
                padding: 12px 16px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
                text-align: center;
            }}
            .login-footer {{
                text-align: center;
                padding: 0 24px 24px;
                color: #6b7280;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <div class="login-icon">&#128274;</div>
                <h1>Lead Monitor</h1>
                <p>Sign in to access the dashboard</p>
            </div>
            <form class="login-form" method="POST" action="/login">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                {error_html}
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" placeholder="Enter your username" required autofocus>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter your password" required>
                </div>
                <button type="submit" class="login-btn">Sign In</button>
            </form>
            <div class="login-footer">
                Lead Sheets Monitor Dashboard
            </div>
        </div>
    </body>
    </html>
    """


# ============================================================================
# CSRF Protection (Database-backed for persistence across restarts)
# ============================================================================

# CSRF configuration
CSRF_TOKEN_EXPIRY_SECONDS = 3600  # 1 hour (also defined in storage.py)

# In-memory cache for CSRF tokens (optional optimization)
_csrf_cache: Dict[str, float] = {}  # token -> timestamp
CSRF_CACHE_MAX_SIZE = 500
CSRF_TOKEN_TTL = 3600  # 1 hour TTL for CSRF tokens


def generate_csrf_token() -> str:
    """
    Generate a new CSRF token and store it.

    Uses database-backed storage for persistence across restarts.
    """
    token = secrets.token_urlsafe(32)
    now = time.time()

    # Store in database (primary storage)
    storage.create_csrf_token(token)

    # Also cache in memory for faster lookups
    with _csrf_lock:
        _csrf_cache[token] = now
        # Cleanup expired tokens first (TTL-based)
        expired = [t for t, ts in _csrf_cache.items() if now - ts > CSRF_TOKEN_TTL]
        for t in expired:
            del _csrf_cache[t]
        # Then cleanup if still over limit
        if len(_csrf_cache) > CSRF_CACHE_MAX_SIZE:
            # Remove oldest entries
            sorted_tokens = sorted(_csrf_cache.items(), key=lambda x: x[1])
            tokens_to_remove = len(_csrf_cache) - CSRF_CACHE_MAX_SIZE
            for t, _ in sorted_tokens[:tokens_to_remove]:
                del _csrf_cache[t]

    return token


def validate_csrf_token(token: str) -> bool:
    """
    Validate a CSRF token.

    Uses database-backed storage for persistence across restarts.
    """
    if not token:
        return False

    # Try database validation (handles expiry)
    if storage.validate_csrf_token(token):
        return True

    # Remove from cache if invalid
    with _csrf_lock:
        if token in _csrf_cache:
            del _csrf_cache[token]

    return False


def consume_csrf_token(token: str) -> bool:
    """
    Validate and consume (delete) a CSRF token after use.

    This is the recommended way to validate CSRF tokens for form submissions
    as it prevents token reuse.
    """
    if not validate_csrf_token(token):
        return False

    # Invalidate the token after successful validation
    storage.invalidate_csrf_token(token)

    # Remove from cache
    with _csrf_lock:
        if token in _csrf_cache:
            del _csrf_cache[token]

    return True


# ============================================================================
# Rate Limiting
# ============================================================================

# Rate limit configuration
RATE_LIMIT_REQUESTS = 60  # Max requests per window
RATE_LIMIT_WINDOW_SECONDS = 60  # Window duration in seconds
RATE_LIMIT_BURST_REQUESTS = 10  # Max burst requests per short window
RATE_LIMIT_BURST_WINDOW_SECONDS = 5  # Burst window duration
RATE_LIMIT_MAX_IPS = 10000  # Maximum IPs to track (memory protection)
RATE_LIMIT_MAX_TIMESTAMPS_PER_IP = 100  # Maximum timestamps to keep per IP (memory protection)

# Rate limit storage: {ip: [timestamp, ...]}
_rate_limit_data: Dict[str, list] = {}
_rate_limit_last_cleanup = time.time()
RATE_LIMIT_CLEANUP_INTERVAL = 60  # Cleanup every 60 seconds

# Health endpoint rate limiting (more permissive for load balancer checks)
# Allows 60 requests per minute per IP (typical LB health check is every 10-30 seconds)
HEALTH_RATE_LIMIT_REQUESTS = 60
HEALTH_RATE_LIMIT_WINDOW_SECONDS = 60
_health_rate_limit_data: Dict[str, List[float]] = {}
_health_rate_limit_lock = threading.Lock()


def _is_ip_in_trusted_networks(ip_str: str) -> bool:
    """Check if an IP address is in the trusted proxy networks."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in TRUSTED_PROXY_NETWORKS:
            if ip in network:
                return True
    except ValueError:
        pass
    return False


def _get_client_ip(handler) -> str:
    """
    Extract client IP from request, handling proxies securely.

    Only trusts X-Forwarded-For from configured trusted proxy IPs.
    Uses rightmost-first approach to prevent spoofing.
    """
    direct_ip = handler.client_address[0]

    # Only trust X-Forwarded-For if request comes from a trusted proxy
    if not _is_ip_in_trusted_networks(direct_ip):
        return direct_ip

    forwarded = handler.headers.get('X-Forwarded-For')
    if not forwarded:
        return direct_ip

    # Parse the X-Forwarded-For header (format: "client, proxy1, proxy2")
    # Use rightmost-first: find the rightmost IP that isn't a trusted proxy
    ips = [ip.strip() for ip in forwarded.split(',')]

    # Walk from right to left, find first non-trusted-proxy IP
    for ip in reversed(ips):
        if ip and not _is_ip_in_trusted_networks(ip):
            return ip

    # If all IPs in chain are trusted proxies, use the leftmost (client) IP
    return ips[0] if ips else direct_ip


def _check_rate_limit(client_ip: str) -> Tuple[bool, Optional[int]]:
    """
    Check if client has exceeded rate limits (thread-safe).

    Returns:
        Tuple of (is_allowed: bool, retry_after: int or None)
    """
    now = time.time()

    with _rate_limit_lock:
        global _rate_limit_last_cleanup

        # Periodic cleanup
        if now - _rate_limit_last_cleanup > RATE_LIMIT_CLEANUP_INTERVAL:
            _cleanup_rate_limit_data_unsafe()
            _rate_limit_last_cleanup = now

        # Initialize or get existing data for this IP
        if client_ip not in _rate_limit_data:
            # Check if we've hit the max IPs limit
            if len(_rate_limit_data) >= RATE_LIMIT_MAX_IPS:
                _cleanup_rate_limit_data_unsafe()
                # If still over limit after cleanup, reject to prevent memory exhaustion
                if len(_rate_limit_data) >= RATE_LIMIT_MAX_IPS:
                    return (False, 60)  # Temporary rejection
            _rate_limit_data[client_ip] = []

        # Clean old entries outside the window
        window_start = now - RATE_LIMIT_WINDOW_SECONDS
        _rate_limit_data[client_ip] = [
            ts for ts in _rate_limit_data[client_ip]
            if ts > window_start
        ]

        # Trim to max timestamps per IP to prevent memory growth
        if len(_rate_limit_data[client_ip]) > RATE_LIMIT_MAX_TIMESTAMPS_PER_IP:
            _rate_limit_data[client_ip] = _rate_limit_data[client_ip][-RATE_LIMIT_MAX_TIMESTAMPS_PER_IP:]

        requests_in_window = len(_rate_limit_data[client_ip])

        # Check burst limit (short window)
        burst_start = now - RATE_LIMIT_BURST_WINDOW_SECONDS
        requests_in_burst = len([ts for ts in _rate_limit_data[client_ip] if ts > burst_start])

        # Check if over burst limit
        if requests_in_burst >= RATE_LIMIT_BURST_REQUESTS:
            burst_requests = sorted([ts for ts in _rate_limit_data[client_ip] if ts > burst_start])
            if burst_requests:
                retry_after = int(RATE_LIMIT_BURST_WINDOW_SECONDS - (now - burst_requests[0])) + 1
                return (False, max(1, retry_after))

        # Check if over window limit
        if requests_in_window >= RATE_LIMIT_REQUESTS:
            oldest = min(_rate_limit_data[client_ip])
            retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - oldest)) + 1
            return (False, max(1, retry_after))

        # Record this request
        _rate_limit_data[client_ip].append(now)

    return (True, None)


def _cleanup_rate_limit_data_unsafe():
    """Remove old rate limit data (NOT thread-safe - caller must hold lock)."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS * 2

    # Remove IPs with no recent requests
    empty_ips = [
        ip for ip, timestamps in _rate_limit_data.items()
        if not timestamps or max(timestamps) < cutoff
    ]
    for ip in empty_ips:
        del _rate_limit_data[ip]


def _check_health_rate_limit(client_ip: str) -> bool:
    """
    Check if health endpoint request should be allowed (thread-safe).

    More permissive than general rate limiting - allows 60 req/min per IP.
    This protects against DoS while allowing legitimate load balancer checks.

    Returns:
        True if request is allowed, False if rate limited
    """
    now = time.time()
    cutoff = now - HEALTH_RATE_LIMIT_WINDOW_SECONDS

    with _health_rate_limit_lock:
        # Initialize or get existing data
        if client_ip not in _health_rate_limit_data:
            # Limit total IPs tracked to prevent memory exhaustion
            if len(_health_rate_limit_data) >= 1000:
                # Clean up old entries
                old_ips = [
                    ip for ip, timestamps in _health_rate_limit_data.items()
                    if not timestamps or max(timestamps) < cutoff
                ]
                for ip in old_ips:
                    del _health_rate_limit_data[ip]
            _health_rate_limit_data[client_ip] = []

        # Filter to recent requests only
        _health_rate_limit_data[client_ip] = [
            ts for ts in _health_rate_limit_data[client_ip] if ts > cutoff
        ]

        # Check limit
        if len(_health_rate_limit_data[client_ip]) >= HEALTH_RATE_LIMIT_REQUESTS:
            return False

        # Record request
        _health_rate_limit_data[client_ip].append(now)
        return True


def cleanup_web_caches():
    """
    Periodic cleanup of in-memory caches.

    This function should be called from the daemon loop to ensure caches
    are cleaned even when there's low traffic to the web dashboard.
    Prevents memory leaks from stale session, CSRF, and rate limit data.
    """
    now = time.time()
    cleaned = {'sessions': 0, 'csrf': 0, 'rate_limit': 0}

    # Cleanup expired sessions from cache
    with _session_lock:
        expired_sessions = [k for k, v in _session_cache.items()
                           if now - v.get('created', 0) > SESSION_EXPIRY_SECONDS]
        for k in expired_sessions:
            del _session_cache[k]
        cleaned['sessions'] = len(expired_sessions)

    # Cleanup expired CSRF tokens from cache
    with _csrf_lock:
        expired_csrf = [t for t, ts in _csrf_cache.items() if now - ts > CSRF_TOKEN_TTL]
        for t in expired_csrf:
            del _csrf_cache[t]
        cleaned['csrf'] = len(expired_csrf)

    # Cleanup stale rate limit data
    with _rate_limit_lock:
        before_count = len(_rate_limit_data)
        _cleanup_rate_limit_data_unsafe()
        cleaned['rate_limit'] = before_count - len(_rate_limit_data)

    # Cleanup health endpoint rate limit data
    cutoff = now - HEALTH_RATE_LIMIT_WINDOW_SECONDS * 2
    with _health_rate_limit_lock:
        old_ips = [
            ip for ip, timestamps in _health_rate_limit_data.items()
            if not timestamps or max(timestamps) < cutoff
        ]
        for ip in old_ips:
            del _health_rate_limit_data[ip]
        cleaned['rate_limit'] += len(old_ips)

    total_cleaned = sum(cleaned.values())
    if total_cleaned > 0:
        logger.debug(f"Web cache cleanup: {cleaned['sessions']} sessions, "
                     f"{cleaned['csrf']} CSRF tokens, {cleaned['rate_limit']} rate limit entries")

    return cleaned


# ============================================================================
# Global State
# ============================================================================

# Global state for health server
_health_state = {
    'start_time': None,
    'last_successful_run': None,
    'leads_processed_today': 0,
    'tracker': None
}


# ============================================================================
# Authentication Helpers
# ============================================================================

def _check_authentication(handler) -> Tuple[bool, Optional[str]]:
    """
    Check if the request is properly authenticated.

    Supports:
    1. Session cookie (from login page)
    2. API Key via X-API-Key header (NOT via query string - security risk)
    3. HTTP Basic Auth (for API access)

    Returns:
        Tuple of (is_authenticated: bool, error_message: str or None)
    """
    if not AUTH_ENABLED:
        return (True, None)

    # Check session cookie first (for browser access)
    session_token = _get_session_cookie(handler)
    if session_token and _validate_session(session_token):
        return (True, None)

    # Check API Key in header ONLY (not query string - can leak in logs/history)
    api_key = handler.headers.get('X-API-Key')

    if api_key and DASHBOARD_API_KEY:
        # Use constant-time comparison to prevent timing attacks
        if hmac.compare_digest(api_key, DASHBOARD_API_KEY):
            return (True, None)

    # Check Basic Auth
    auth_header = handler.headers.get('Authorization')
    if auth_header and auth_header.startswith('Basic ') and DASHBOARD_USERNAME and DASHBOARD_PASSWORD:
        try:
            encoded_credentials = auth_header[6:]  # Remove 'Basic ' prefix
            decoded = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded.split(':', 1)

            # Use constant-time comparison
            username_match = hmac.compare_digest(username, DASHBOARD_USERNAME)
            password_match = hmac.compare_digest(password, DASHBOARD_PASSWORD)

            if username_match and password_match:
                return (True, None)
        except (ValueError, UnicodeDecodeError, base64.binascii.Error):
            # Malformed auth header - log at debug level to avoid log spam from bots
            logger.debug("Malformed Basic auth header")

    # Authentication failed
    if DASHBOARD_API_KEY:
        return (False, "Invalid or missing API key")
    else:
        return (False, "Invalid credentials")


# Lock for config reload operations to prevent race conditions
_config_reload_lock = threading.Lock()


def _reload_config():
    """Reload configuration from database (with config.json fallback).

    Thread-safe: Uses a lock to prevent race conditions when multiple
    threads attempt to reload configuration simultaneously.
    """
    from config import load_config, get_momence_hosts, get_sheets_config
    global _config
    global DLQ_ENABLED, DLQ_MAX_RETRY_ATTEMPTS, RATE_LIMIT_DELAY
    global DEFAULT_SPREADSHEET_ID, LOG_FORMAT

    with _config_reload_lock:
        config_data = load_config()
        _config = config_data  # Update global dict reference

        # Load hosts and sheets from database (with config.json fallback)
        MOMENCE_HOSTS.clear()
        MOMENCE_HOSTS.update(get_momence_hosts())
        SHEETS_CONFIG.clear()
        SHEETS_CONFIG.extend(get_sheets_config())

        # Update settings globals
        settings = config_data.get('settings', {})
        DLQ_ENABLED = settings.get('dlq_enabled', True)
        DLQ_MAX_RETRY_ATTEMPTS = settings.get('dlq_max_retry_attempts', 5)
        RATE_LIMIT_DELAY = settings.get('rate_limit_delay_seconds', 3.0)
        DEFAULT_SPREADSHEET_ID = settings.get('default_spreadsheet_id', '')
        LOG_FORMAT = settings.get('log_format', 'text')


def _save_config():
    """Save current configuration to file (skip on Cloud Run - use database instead)."""
    from config import IS_CLOUD_RUN
    if IS_CLOUD_RUN:
        # On Cloud Run, config is stored in database, not file
        logger.debug("Skipping config file save on Cloud Run - using database")
        return

    config_path = Path(CONFIG_FILE)
    config_to_save = {
        'momence_hosts': MOMENCE_HOSTS,
        'sheets': SHEETS_CONFIG,
        'settings': _config.get('settings', {}),
        'schedule': _config.get('schedule', {})
    }
    try:
        with open(config_path, 'w') as f:
            json.dump(config_to_save, f, indent=2)
        logger.info("Configuration saved")
    except Exception as e:
        logger.warning(f"Could not save config file: {e}")


def _build_dashboard_html() -> str:
    """Build the HTML dashboard page with CSRF token."""
    # Generate CSRF token for this page
    csrf_token = generate_csrf_token()

    tracker = _health_state.get('tracker', {})
    failed_queue = storage.get_failed_queue_entries()
    dead_letters = storage.get_dead_letters()
    start_time = _health_state.get('start_time')

    uptime_seconds = 0
    if start_time:
        uptime_seconds = int((utc_now() - start_time).total_seconds())

    # Format uptime
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    # Gather stats
    sent_count = storage.get_sent_hash_count()
    failed_count = len(failed_queue)
    dead_count = len(dead_letters)
    location_counts = tracker.get('location_counts', {})
    last_check = tracker.get('last_check', 'Never')
    last_error_email = tracker.get('last_error_email_sent')

    # Build Momence host rows (compact table view)
    host_rows = ""
    active_hosts = 0
    total_hosts = len(MOMENCE_HOSTS)
    for host_name, host_cfg in MOMENCE_HOSTS.items():
        enabled = host_cfg.get('enabled', True)
        if enabled:
            active_hosts += 1
        host_id = host_cfg.get('host_id', 'N/A')
        host_sheets = [s for s in SHEETS_CONFIG if s.get('momence_host') == host_name]
        enabled_sheets = sum(1 for s in host_sheets if s.get('enabled', True))
        leads_sent = sum(location_counts.get(s.get('name', ''), 0) for s in host_sheets)

        status_class = 'status-active' if enabled else 'status-disabled'
        status_text = 'Active' if enabled else 'Disabled'

        host_rows += f"""
        <tr class="host-row" data-host="{escape_html(host_name)}" data-enabled="{str(enabled).lower()}">
            <td>
                <strong>{escape_html(host_name)}</strong>
            </td>
            <td><code style="font-size:12px;">{escape_html(host_id)}</code></td>
            <td>{enabled_sheets}/{len(host_sheets)}</td>
            <td>{leads_sent}</td>
            <td><span class="status {status_class}">{status_text}</span></td>
            <td class="host-actions">
                <a href="https://momence.com/dashboard/{escape_html(host_id)}/leads?sortBy=createdAt&sortOrder=DESC" target="_blank" class="btn btn-xs">Leads</a>
                <button class="btn btn-xs btn-secondary" onclick="toggleHost('{escape_html(host_name)}', {str(not enabled).lower()})">
                    {'Enable' if not enabled else 'Disable'}
                </button>
                <button class="btn btn-xs btn-secondary" onclick="editHost('{escape_html(host_name)}')">Edit</button>
                <button class="btn btn-xs btn-danger" onclick="deleteHost('{escape_html(host_name)}')">Delete</button>
            </td>
        </tr>
        """

    # Summary for collapsed view
    host_summary = f"{active_hosts}/{total_hosts} active"

    # Build sheets table
    sheets_rows = ""
    for sheet in SHEETS_CONFIG:
        enabled = sheet.get('enabled', True)
        name = sheet.get('name', 'Unnamed')
        momence_host = sheet.get('momence_host', 'N/A')
        notification_email = sheet.get('notification_email', '')
        lead_count = location_counts.get(name, 0)
        status_class = 'status-active' if enabled else 'status-disabled'
        status_text = 'Active' if enabled else 'Disabled'

        # Show notification email or indicate none configured
        email_display = escape_html(notification_email) if notification_email else '<span class="text-muted">(none)</span>'

        sheets_rows += f"""
        <tr data-sheet-name="{escape_html(name)}">
            <td>{escape_html(name)}</td>
            <td>{escape_html(momence_host)}</td>
            <td>{email_display}</td>
            <td>{lead_count}</td>
            <td><span class="status {status_class}">{status_text}</span></td>
            <td>
                <button class="btn btn-xs btn-secondary" onclick="editSheet('{escape_html(name)}')">Edit</button>
                <button class="btn btn-xs" onclick="toggleSheet('{escape_html(name)}', {str(not enabled).lower()})">
                    {'Enable' if not enabled else 'Disable'}
                </button>
                <button class="btn btn-xs btn-danger" onclick="deleteSheet('{escape_html(name)}')">Delete</button>
            </td>
        </tr>
        """

    # Build failed queue table with expanded error details
    failed_rows = ""
    failed_queue_list = failed_queue
    for idx, entry in enumerate(failed_queue_list):
        lead = entry.get('lead_data', {})
        error_details = entry.get('last_error_details', {})
        error_type = escape_html(entry.get('last_error', 'N/A'))
        status_code = error_details.get('status_code', '')
        cf_ray = error_details.get('cf_ray', '')
        response_body = escape_html(str(error_details.get('response_body', ''))[:200])
        request_url = escape_html(str(error_details.get('request_url', '')))
        request_payload = error_details.get('request_payload', {})
        request_duration = error_details.get('request_duration_ms', '')
        entry_hash = entry.get('entry_hash', '')
        email = lead.get('email', 'N/A')
        momence_host = entry.get('momence_host', 'N/A')
        attempts = entry.get('attempts', 0)
        last_attempted = entry.get('last_attempted_at', '')

        # Build error summary badge
        error_badge_class = 'status-disabled'
        if error_type == 'api_bad_request':
            error_badge_class = 'status-warning'
        elif error_type in ('rate_limited', 'cloudflare_blocked', 'cloudflare_challenge'):
            error_badge_class = 'status-pending'

        # Format payload for display (mask sensitive data)
        payload_display = json.dumps(request_payload, indent=2) if request_payload else 'N/A'

        failed_rows += f"""
        <tr class="failed-row" data-email="{escape_html(email.lower())}" data-attempts="{attempts}" data-timestamp="{escape_html(last_attempted)}" data-hash="{escape_html(entry_hash)}">
            <td onclick="toggleErrorDetails('error-details-{idx}')" style="cursor:pointer;">{escape_html(email)}</td>
            <td>{escape_html(momence_host)}</td>
            <td><span class="utc-time" data-utc="{escape_html(last_attempted or '')}">{escape_html(last_attempted or 'N/A')}</span></td>
            <td>{attempts}</td>
            <td><span class="status {error_badge_class}">{error_type}</span></td>
            <td>{status_code or 'N/A'}</td>
            <td style="text-align:center;">
                <span onclick="toggleErrorDetails('error-details-{idx}')" style="cursor:pointer;color:#6366f1;">▶ Details</span>
            </td>
        </tr>
        <tr id="error-details-{idx}" class="error-details-row" style="display:none;">
            <td colspan="7">
                <div class="error-details-panel">
                    <div class="error-detail-grid">
                        <div class="error-detail-item">
                            <strong>Error Type:</strong> {error_type}
                        </div>
                        <div class="error-detail-item">
                            <strong>HTTP Status:</strong> {status_code or 'N/A'}
                        </div>
                        <div class="error-detail-item">
                            <strong>CF-Ray:</strong> {cf_ray or 'N/A'}
                        </div>
                        <div class="error-detail-item">
                            <strong>Duration:</strong> {request_duration}ms
                        </div>
                        <div class="error-detail-item">
                            <strong>First Failed:</strong> <span class="utc-time" data-utc="{escape_html(entry.get('first_failed_at', 'N/A'))}">{escape_html(entry.get('first_failed_at', 'N/A'))}</span>
                        </div>
                        <div class="error-detail-item">
                            <strong>Last Attempt:</strong> <span class="utc-time" data-utc="{escape_html(last_attempted or 'N/A')}">{escape_html(last_attempted or 'N/A')}</span>
                        </div>
                    </div>
                    <div class="error-detail-section">
                        <strong>Request URL:</strong>
                        <code class="error-code-block">{request_url or 'N/A'}</code>
                    </div>
                    <div class="error-detail-section">
                        <strong>Request Payload:</strong>
                        <pre class="error-code-block">{escape_html(payload_display)}</pre>
                    </div>
                    <div class="error-detail-section">
                        <strong>Response Body:</strong>
                        <pre class="error-code-block">{response_body or '(empty)'}</pre>
                    </div>
                </div>
            </td>
        </tr>
        """

    if not failed_rows:
        failed_rows = '<tr><td colspan="6" class="text-muted">No failed entries</td></tr>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="csrf-token" content="{csrf_token}">
        <link rel="icon" type="image/png" href="/favicon.ico">
        <title>Lead Monitor Dashboard</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
                line-height: 1.5;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            header {{
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                padding: 24px 20px;
                margin-bottom: 24px;
                border-radius: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .header-content h1 {{ font-size: 24px; font-weight: 600; }}
            .header-content p {{ opacity: 0.9; margin-top: 4px; font-size: 14px; }}
            .logout-btn {{
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                text-decoration: none;
                transition: background 0.2s;
            }}
            .logout-btn:hover {{
                background: rgba(255,255,255,0.3);
            }}

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }}
            .stat-card {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .stat-card .value {{
                font-size: 32px;
                font-weight: 700;
                color: #6366f1;
            }}
            .stat-card .label {{
                font-size: 12px;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 4px;
            }}
            .stat-card.warning .value {{ color: #f59e0b; }}
            .stat-card.danger .value {{ color: #dc2626; }}
            .stat-card.success .value {{ color: #10b981; }}

            .section {{ margin-bottom: 24px; }}
            .section-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
            }}

            .card {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .card-header {{
                padding: 16px 20px;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .card-header h3 {{ font-size: 16px; font-weight: 600; }}
            .card-body {{ padding: 16px 20px; }}
            .card-body p {{ margin-bottom: 8px; font-size: 14px; color: #475569; }}
            .card-actions {{
                padding: 12px 20px;
                background: #f8fafc;
                border-top: 1px solid #e2e8f0;
                display: flex;
                gap: 8px;
            }}

            .host-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 16px;
            }}
            .host-card {{ margin-bottom: 0; }}

            /* Collapsible sections */
            .section-collapsible {{
                cursor: pointer;
                user-select: none;
            }}
            .section-collapsible:hover {{
                background: #f8fafc;
            }}
            .section-toggle {{
                display: inline-block;
                width: 20px;
                transition: transform 0.2s;
                color: #64748b;
            }}
            .section-toggle.collapsed {{
                transform: rotate(-90deg);
            }}
            .section-content {{
                overflow: hidden;
                transition: max-height 0.3s ease-out;
            }}
            .section-content.collapsed {{
                max-height: 0 !important;
                padding: 0;
            }}
            .section-summary {{
                display: none;
                font-size: 13px;
                color: #64748b;
                margin-left: 8px;
            }}
            .section-summary.visible {{
                display: inline;
            }}
            .host-actions {{
                white-space: nowrap;
            }}
            .host-row td {{
                padding: 10px 12px;
            }}
            .host-filter {{
                display: flex;
                gap: 8px;
                margin-bottom: 12px;
            }}
            .host-filter-btn {{
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 12px;
                border: 1px solid #e2e8f0;
                background: white;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .host-filter-btn:hover {{
                border-color: #6366f1;
                color: #6366f1;
            }}
            .host-filter-btn.active {{
                background: #6366f1;
                color: white;
                border-color: #6366f1;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px 16px;
                text-align: left;
                border-bottom: 1px solid #e2e8f0;
            }}
            th {{
                background: #f8fafc;
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            td {{ font-size: 14px; }}

            .badge {{
                display: inline-block;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            .badge-success {{ background: #d1fae5; color: #059669; }}
            .badge-warning {{ background: #fef3c7; color: #d97706; }}
            .badge-danger {{ background: #fee2e2; color: #dc2626; }}

            .status {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }}
            .status-active {{ background: #d1fae5; color: #059669; }}
            .status-disabled {{ background: #f1f5f9; color: #64748b; }}
            .status-warning {{ background: #fef3c7; color: #d97706; }}
            .status-pending {{ background: #fce7f3; color: #db2777; }}

            /* Chart styles */
            .chart-container {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 24px;
            }}
            .chart-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
            }}
            .chart-header h3 {{
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
            }}
            .chart-controls {{
                display: flex;
                gap: 8px;
                align-items: center;
            }}
            .chart-controls select {{
                padding: 6px 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                background: white;
            }}
            .chart-wrapper {{
                position: relative;
                height: 300px;
                width: 100%;
            }}
            .chart-legend {{
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #e2e8f0;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 13px;
                color: #475569;
            }}
            .legend-color {{
                width: 12px;
                height: 12px;
                border-radius: 3px;
            }}
            .chart-summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 12px;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #e2e8f0;
            }}
            .summary-item {{
                text-align: center;
                padding: 8px;
                background: #f8fafc;
                border-radius: 6px;
            }}
            .summary-value {{
                font-size: 20px;
                font-weight: 600;
                color: #6366f1;
            }}
            .summary-label {{
                font-size: 11px;
                color: #64748b;
                text-transform: uppercase;
            }}
            .chart-loading {{
                display: flex;
                align-items: center;
                justify-content: center;
                height: 300px;
                color: #64748b;
            }}
            .chart-empty {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 300px;
                color: #94a3b8;
            }}
            .chart-empty svg {{
                width: 48px;
                height: 48px;
                margin-bottom: 12px;
                opacity: 0.5;
            }}

            /* Error details panel styles */
            .failed-row {{ cursor: pointer; }}
            .failed-row:hover {{ background: #f8fafc; }}
            .error-details-row td {{ padding: 0 !important; background: #f8fafc; }}
            .error-details-panel {{
                padding: 16px 20px;
                background: #fff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                margin: 8px 0;
            }}
            .error-detail-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-bottom: 16px;
            }}
            .error-detail-item {{
                padding: 8px;
                background: #f1f5f9;
                border-radius: 4px;
                font-size: 13px;
            }}
            .error-detail-item strong {{
                display: block;
                color: #64748b;
                font-size: 11px;
                text-transform: uppercase;
                margin-bottom: 2px;
            }}
            .error-detail-section {{
                margin-top: 12px;
            }}
            .error-detail-section strong {{
                display: block;
                color: #64748b;
                font-size: 12px;
                margin-bottom: 6px;
            }}
            .error-code-block {{
                display: block;
                background: #1e293b;
                color: #e2e8f0;
                padding: 12px;
                border-radius: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-all;
                max-height: 150px;
                overflow-y: auto;
            }}
            .failed-queue-table th:last-child,
            .failed-queue-table td:last-child {{
                width: 80px;
                text-align: center;
            }}

            .btn {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                cursor: pointer;
                background: #6366f1;
                color: white;
                transition: background 0.2s;
            }}
            .btn:hover {{ background: #4f46e5; }}
            .btn-sm {{ padding: 6px 12px; font-size: 13px; }}
            .btn-xs {{ padding: 4px 8px; font-size: 12px; }}
            .btn-secondary {{ background: #e2e8f0; color: #475569; }}
            .btn-secondary:hover {{ background: #cbd5e1; }}
            .btn-danger {{ background: #dc2626; }}
            .btn-danger:hover {{ background: #b91c1c; }}

            .text-muted {{ color: #94a3b8; font-style: italic; }}
            code {{
                background: #f1f5f9;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 13px;
                font-family: 'SF Mono', Monaco, monospace;
            }}

            .modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                align-items: center;
                justify-content: center;
            }}
            .modal.active {{ display: flex; }}
            .modal-content {{
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 500px;
                max-height: 90vh;
                overflow-y: auto;
            }}
            .modal-header {{
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
            }}
            .modal-header h2 {{ font-size: 18px; }}
            .modal-body {{ padding: 20px; }}
            .modal-footer {{
                padding: 16px 20px;
                border-top: 1px solid #e2e8f0;
                display: flex;
                justify-content: flex-end;
                gap: 8px;
            }}

            .form-group {{ margin-bottom: 16px; }}
            .form-group label {{
                display: block;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 6px;
                color: #475569;
            }}
            .form-group input, .form-group select {{
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 14px;
            }}
            .form-group input:focus, .form-group select:focus {{
                outline: none;
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
            }}

            .alert {{
                padding: 12px 16px;
                border-radius: 8px;
                margin-bottom: 16px;
                font-size: 14px;
            }}
            .alert-success {{ background: #d1fae5; color: #059669; }}
            .alert-error {{ background: #fee2e2; color: #dc2626; }}
            .alert-warning {{ background: #fef3c7; color: #d97706; }}

            .refresh-indicator {{
                display: inline-block;
                margin-left: 8px;
                opacity: 0;
                transition: opacity 0.3s;
            }}
            .refresh-indicator.active {{ opacity: 1; }}

            /* Spinner styles */
            .spinner {{
                display: inline-block;
                width: 14px;
                height: 14px;
                border: 2px solid #e5e7eb;
                border-top-color: #6366f1;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }}
            .spinner-large {{
                width: 40px;
                height: 40px;
                border-width: 3px;
            }}
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}

            /* Retry progress overlay */
            #retry-progress-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.6);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                backdrop-filter: blur(4px);
            }}
            .retry-progress-content {{
                background: white;
                padding: 32px 40px;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                min-width: 400px;
                max-width: 500px;
            }}
            .retry-progress-header {{
                font-size: 18px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 24px;
            }}
            .retry-progress-bar-container {{
                background: #e5e7eb;
                border-radius: 8px;
                height: 12px;
                overflow: hidden;
                margin-bottom: 16px;
            }}
            .retry-progress-bar {{
                background: linear-gradient(90deg, #6366f1, #8b5cf6);
                height: 100%;
                width: 0%;
                border-radius: 8px;
                transition: width 0.3s ease;
            }}
            .retry-progress-count {{
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 20px;
            }}
            .retry-progress-current {{
                background: #f3f4f6;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 16px;
            }}
            .retry-progress-current-label {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #9ca3af;
                margin-bottom: 4px;
            }}
            .retry-progress-current-email {{
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                word-break: break-all;
            }}
            .retry-progress-results {{
                display: flex;
                justify-content: center;
                gap: 24px;
                margin-top: 16px;
            }}
            .retry-result-item {{
                text-align: center;
            }}
            .retry-result-count {{
                font-size: 24px;
                font-weight: 700;
            }}
            .retry-result-count.success {{
                color: #10b981;
            }}
            .retry-result-count.failed {{
                color: #ef4444;
            }}
            .retry-result-label {{
                font-size: 12px;
                color: #6b7280;
                margin-top: 2px;
            }}
            .retry-progress-complete {{
                display: none;
                padding: 16px;
                border-radius: 12px;
                margin-top: 16px;
            }}
            .retry-progress-complete.success {{
                background: #ecfdf5;
                border: 1px solid #a7f3d0;
            }}
            .retry-progress-complete.partial {{
                background: #fffbeb;
                border: 1px solid #fde68a;
            }}
            .retry-progress-complete-icon {{
                font-size: 32px;
                margin-bottom: 8px;
            }}
            .retry-progress-complete-text {{
                font-size: 14px;
                color: #374151;
            }}

            /* Row transition effects */
            .failed-row {{
                transition: background-color 0.3s ease;
            }}

            /* Footer */
            .app-footer {{
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 1rem;
                padding: 1rem;
                font-size: 0.7rem;
                color: #999;
                opacity: 0.6;
                background: transparent;
                user-select: none;
                margin-top: 2rem;
            }}
            .app-footer-copyright {{
                white-space: nowrap;
            }}
            .app-footer-version {{
                white-space: nowrap;
                font-family: 'SF Mono', Monaco, monospace;
                letter-spacing: 0.02em;
            }}
            /* Collapsible panels */
            .collapsible-header {{
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .collapsible-header::after {{
                content: '\u25BC';
                font-size: 0.7em;
                transition: transform 0.2s;
            }}
            .collapsible-header.collapsed::after {{
                transform: rotate(-90deg);
            }}
            .collapsible-content {{
                overflow: hidden;
                max-height: 2000px;
                transition: max-height 0.3s ease-out, opacity 0.2s ease-out;
                opacity: 1;
            }}
            .collapsible-content.collapsed {{
                max-height: 0 !important;
                opacity: 0;
            }}
            /* Logs panel */
            .logs-output {{
                background: #1e293b;
                color: #e2e8f0;
                padding: 16px;
                border-radius: 6px;
                font-family: 'SF Mono', Monaco, 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.5;
                overflow-x: auto;
                white-space: pre;
                max-height: 400px;
                overflow-y: auto;
                margin: 0;
            }}
            /* Status indicator */
            .status-dot {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 6px;
            }}
            .status-dot.healthy {{ background: #10b981; }}
            .status-dot.stale {{ background: #f59e0b; }}
            .status-dot.error {{ background: #dc2626; }}
            .last-updated {{
                font-size: 0.85em;
                color: #e2e8f0;
                margin-left: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="header-content">
                    <h1>Lead Monitor Dashboard</h1>
                    <p>
                        <span class="status-dot healthy" id="status-dot" title="Monitor is running"></span>
                        Last check: <span class="utc-time" data-utc="{escape_html(str(last_check))}">{escape_html(str(last_check))}</span>
                        | Uptime: {uptime_str}
                        <span class="last-updated">(refreshed <span id="last-updated">0s ago</span>)</span>
                    </p>
                </div>
                <div style="display:flex;gap:10px;">
                    <button class="logout-btn" onclick="showSettingsModal()">Settings</button>
                    <a href="/logout" class="logout-btn">Logout</a>
                </div>
            </header>

            <div id="alert-container"></div>

            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card success">
                    <div class="value">{sent_count}</div>
                    <div class="label">Leads Sent</div>
                </div>
                <div class="stat-card{' warning' if failed_count > 0 else ''}">
                    <div class="value">{failed_count}</div>
                    <div class="label">Failed Queue</div>
                </div>
                <div class="stat-card{' danger' if dead_count > 0 else ''}">
                    <div class="value">{dead_count}</div>
                    <div class="label">Dead Letters</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(MOMENCE_HOSTS)}</div>
                    <div class="label">Hosts</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(SHEETS_CONFIG)}</div>
                    <div class="label">Sheets</div>
                </div>
            </div>

            <!-- Leads Chart Section -->
            <div class="chart-container" id="leads-chart-container">
                <div class="chart-header">
                    <h3>Leads by Location (by Lead Created Date)</h3>
                    <div class="chart-controls">
                        <select id="chart-days" onchange="loadLeadsChart()">
                            <option value="24h" selected>Last 24 hours</option>
                            <option value="7">Last 7 days</option>
                            <option value="14">Last 14 days</option>
                            <option value="30">Last 30 days</option>
                            <option value="60">Last 60 days</option>
                            <option value="90">Last 90 days</option>
                        </select>
                    </div>
                </div>
                <div class="chart-wrapper" id="chart-wrapper">
                    <div class="chart-loading">Loading chart data...</div>
                </div>
                <div class="chart-legend" id="chart-legend"></div>
                <div class="chart-summary" id="chart-summary"></div>
            </div>

            <!-- Momence Hosts Section -->
            <div class="section">
                <div class="section-header section-collapsible" onclick="toggleSection('hosts-section')">
                    <h2 class="section-title">
                        <span class="section-toggle" id="hosts-section-toggle">▼</span>
                        Momence Hosts
                        <span class="section-summary" id="hosts-section-summary">{host_summary}</span>
                    </h2>
                    <div style="display:flex;gap:8px;" onclick="event.stopPropagation()">
                        <button class="btn btn-sm" onclick="showAddHostModal()">+ Add Host</button>
                    </div>
                </div>
                <div class="section-content" id="hosts-section-content">
                    <div class="host-filter">
                        <button class="host-filter-btn active" onclick="filterHosts('all')">All ({total_hosts})</button>
                        <button class="host-filter-btn" onclick="filterHosts('active')">Active ({active_hosts})</button>
                        <button class="host-filter-btn" onclick="filterHosts('disabled')">Disabled ({total_hosts - active_hosts})</button>
                    </div>
                    <div class="card" style="margin:0;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Host ID</th>
                                    <th>Sheets</th>
                                    <th>Leads</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="hosts-table-body">
                                {host_rows if host_rows else '<tr><td colspan="6" class="text-muted">No Momence hosts configured</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Locations Section (Collapsible) -->
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title collapsible-header collapsed" id="locations-header"
                        onclick="toggleCollapsible('locations-header', 'locations-content')">Locations ({len(SHEETS_CONFIG)})</h2>
                    <button class="btn btn-sm" onclick="showAddLocationModal()">+ Add Location</button>
                </div>
                <div id="locations-content" class="collapsible-content collapsed">
                    <div class="card">
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Host</th>
                                    <th>Notification Email</th>
                                    <th>Leads</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sheets_rows if sheets_rows else '<tr><td colspan="6" class="text-muted">No locations configured</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Failed Queue Section (Collapsible) -->
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title collapsible-header collapsed" id="failed-queue-header"
                        onclick="toggleCollapsible('failed-queue-header', 'failed-queue-content')">Failed Queue ({failed_count})</h2>
                    <div style="display:flex;gap:8px;align-items:center;">
                        <input type="text" id="failed-search" placeholder="Search email..." onkeyup="filterFailedQueue()" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;">
                        <select id="failed-sort" onchange="sortFailedQueue()" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;">
                            <option value="recent">Most Recent</option>
                            <option value="attempts">Most Attempts</option>
                            <option value="email">Email A-Z</option>
                        </select>
                        {f'<button class="btn btn-sm btn-secondary" onclick="retryAllFailed()">Retry All</button>' if failed_count > 0 else ''}
                    </div>
                </div>
                <div id="failed-queue-content" class="collapsible-content collapsed">
                <div style="background:#fef3c7;border:1px solid #fbbf24;border-radius:6px;padding:10px 14px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#92400e;font-size:13px;">
                        <strong>Error Email:</strong> {f'Last sent <span class="utc-time" data-utc="{escape_html(last_error_email)}">{escape_html(last_error_email)}</span> (1/day limit)' if last_error_email else ('Not sent yet today' if failed_count > 0 else 'No errors')}
                    </span>
                    <button class="btn btn-xs btn-secondary" onclick="clearErrorEmailTracking()" title="Reset tracking to send error email immediately on next error">Reset</button>
                </div>
                <div class="card">
                    <table class="failed-queue-table" id="failed-queue-table">
                        <thead>
                            <tr>
                                <th>Email</th>
                                <th>Host</th>
                                <th>Last Attempt</th>
                                <th>Attempts</th>
                                <th>Error Type</th>
                                <th>HTTP Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="failed-queue-body">
                            {failed_rows}
                        </tbody>
                    </table>
                    <div id="failed-queue-pagination" style="display:flex;justify-content:center;align-items:center;padding:12px;border-top:1px solid #e2e8f0;"></div>
                </div>
                </div>
            </div>

            <!-- Admin Activity Log Section (Collapsible) -->
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title collapsible-header collapsed" id="activity-header"
                        onclick="toggleCollapsible('activity-header', 'activity-content')">Admin Activity</h2>
                    <button class="btn btn-sm btn-secondary" onclick="refreshActivityLog()">Refresh</button>
                </div>
                <div id="activity-content" class="collapsible-content collapsed">
                    <div class="card">
                        <table class="data-table" id="activity-log-table">
                            <thead>
                                <tr>
                                    <th style="width:160px;white-space:nowrap;">Time</th>
                                    <th style="width:130px;">Action</th>
                                    <th>Details</th>
                                    <th style="width:110px;">IP</th>
                                </tr>
                            </thead>
                            <tbody id="activity-log-body">
                                <tr><td colspan="4" class="text-muted">Loading...</td></tr>
                            </tbody>
                        </table>
                        <div id="activity-pagination" style="display:flex;justify-content:center;align-items:center;padding:12px;border-top:1px solid #e2e8f0;"></div>
                    </div>
                </div>
            </div>

            <!-- Application Logs Section (Collapsible) -->
            <div class="section">
                <div class="section-header">
                    <h2 class="section-title collapsible-header collapsed" id="logs-header"
                        onclick="toggleCollapsible('logs-header', 'logs-content')">Application Logs</h2>
                    <button class="btn btn-sm btn-secondary" onclick="refreshLogs()">Refresh</button>
                </div>
                <div id="logs-content" class="collapsible-content collapsed">
                    <div class="card" style="padding:0;">
                        <pre class="logs-output" id="logs-output">Loading...</pre>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <footer class="app-footer">
                <span class="app-footer-copyright">Made with ❤️ by bonJoeV</span>
                <span class="app-footer-version">v{APP_VERSION}{f' · Built <span class="build-time" data-utc="{BUILD_TIME}"></span>' if BUILD_TIME else ''}</span>
            </footer>
        </div>

        <!-- Settings Modal -->
        <div id="settings-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Application Settings</h2>
                </div>
                <div class="modal-body">
                    <form id="settings-form">
                        <div style="font-weight:600;font-size:14px;margin-bottom:12px;color:#6366f1;text-transform:uppercase;letter-spacing:0.5px;">Dead Letter Queue (DLQ)</div>
                        <div class="form-group">
                            <label style="cursor:pointer;display:flex;align-items:center;gap:8px;">
                                <input type="checkbox" id="setting-dlq-enabled" style="width:auto;margin:0;">
                                Enable DLQ (Retry Failed Leads)
                            </label>
                        </div>
                        <div class="form-group">
                            <label for="setting-dlq-max-attempts">Max Retry Attempts</label>
                            <input type="number" id="setting-dlq-max-attempts" min="1" max="100">
                        </div>

                        <div style="font-weight:600;font-size:14px;margin:24px 0 12px;color:#6366f1;text-transform:uppercase;letter-spacing:0.5px;">Performance & Logging</div>
                        <div class="form-group">
                            <label for="setting-rate-limit">Rate Limit Delay (seconds)</label>
                            <input type="number" id="setting-rate-limit" step="0.1" min="0">
                            <small class="text-muted">Delay between outgoing API calls</small>
                        </div>
                        <div class="form-group">
                            <label for="setting-log-retention">Log Retention (days)</label>
                            <input type="number" id="setting-log-retention" min="1" max="365">
                        </div>
                        <div class="form-group">
                            <label for="setting-log-level">Log Level</label>
                            <select id="setting-log-level">
                                <option value="DEBUG">DEBUG</option>
                                <option value="INFO">INFO</option>
                                <option value="WARNING">WARNING</option>
                                <option value="ERROR">ERROR</option>
                            </select>
                        </div>

                        <div style="font-weight:600;font-size:14px;margin:24px 0 12px;color:#6366f1;text-transform:uppercase;letter-spacing:0.5px;">Defaults</div>
                        <div class="form-group">
                            <label for="setting-default-spreadsheet">Default Spreadsheet ID</label>
                            <input type="text" id="setting-default-spreadsheet" placeholder="Google Sheets ID">
                        </div>
                    </form>
                    <div class="alert alert-warning" style="margin-top:20px;margin-bottom:0;font-size:13px;">
                        Note: Some settings may require a container restart to take full effect.
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('settings-modal')">Cancel</button>
                    <button class="btn" onclick="saveSettings()">Save Configuration</button>
                </div>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div id="delete-modal" class="modal">
            <div class="modal-content" style="max-width:450px;">
                <div class="modal-header" style="background:#fef2f2;border-bottom:1px solid #fecaca;">
                    <h2 style="color:#dc2626;" id="delete-modal-title">Confirm Delete</h2>
                </div>
                <div class="modal-body">
                    <p id="delete-modal-message" style="margin-bottom:16px;color:#475569;"></p>
                    <p style="margin-bottom:12px;font-size:13px;color:#64748b;">
                        To confirm, type <strong id="delete-modal-name-display" style="color:#dc2626;"></strong> below:
                    </p>
                    <input type="text" id="delete-confirm-input" placeholder="Type name to confirm" style="width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:6px;font-size:14px;" oninput="validateDeleteInput()">
                    <p id="delete-input-error" style="color:#dc2626;font-size:12px;margin-top:6px;display:none;">Name does not match</p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('delete-modal')">Cancel</button>
                    <button class="btn btn-danger" id="delete-confirm-btn" onclick="confirmDelete()" disabled style="opacity:0.5;">Delete</button>
                </div>
            </div>
        </div>

        <!-- Add/Edit Momence Host Modal -->
        <div id="host-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="host-modal-title">Add Momence Host</h2>
                </div>
                <div class="modal-body">
                    <form id="host-form">
                        <input type="hidden" id="host-original-name">
                        <div class="form-group">
                            <label for="host-name">Host Name</label>
                            <input type="text" id="host-name" required placeholder="e.g., TwinCities">
                        </div>
                        <div class="form-group">
                            <label for="host-host-id">Momence Host ID</label>
                            <input type="text" id="host-host-id" required placeholder="e.g., 49534">
                        </div>
                        <div class="form-group">
                            <label for="host-token">API Token</label>
                            <input type="password" id="host-token" placeholder="Momence API token">
                            <small style="color:#64748b;display:block;margin-top:4px;">Token will be stored securely in Secret Manager</small>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="host-enabled" checked> Enabled
                            </label>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('host-modal')">Cancel</button>
                    <button class="btn" onclick="saveHost()">Save</button>
                </div>
            </div>
        </div>

        <!-- Edit Location Modal -->
        <div id="sheet-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="sheet-modal-title">Edit Location</h2>
                </div>
                <div class="modal-body">
                    <form id="sheet-form">
                        <input type="hidden" id="sheet-original-name">
                        <input type="hidden" id="sheet-spreadsheet-id">
                        <input type="hidden" id="sheet-gid">
                        <div class="form-group">
                            <label for="sheet-name">Location Name</label>
                            <input type="text" id="sheet-name" required placeholder="e.g., Minneapolis Studio">
                        </div>
                        <div class="form-group">
                            <label for="sheet-momence-host">Momence Host</label>
                            <select id="sheet-momence-host" required>
                                <option value="">Select host...</option>
                                {''.join(f'<option value="{escape_html(h)}">{escape_html(h)}</option>' for h in MOMENCE_HOSTS.keys())}
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="sheet-lead-source-id">Lead Source ID (optional)</label>
                            <input type="text" id="sheet-lead-source-id" placeholder="Momence lead source ID">
                        </div>
                        <div class="form-group">
                            <label for="sheet-notification-email">Notification Email (optional)</label>
                            <input type="email" id="sheet-notification-email" placeholder="email@example.com">
                            <small class="text-muted">Leave blank for no location-specific notifications</small>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="sheet-enabled" checked> Enabled
                            </label>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('sheet-modal')">Cancel</button>
                    <button id="test-email-btn" class="btn btn-secondary" onclick="testLocationEmail()" style="display: none;">Test Email</button>
                    <button class="btn" onclick="saveSheet()">Save</button>
                </div>
            </div>
        </div>

        <!-- Add Location Modal (simplified) -->
        <div id="add-location-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Add Location</h2>
                </div>
                <div class="modal-body">
                    <div id="available-tabs-loading" class="text-muted">Loading available tabs...</div>
                    <div id="available-tabs-content" style="display: none;">
                        <form id="add-location-form">
                            <div class="form-group">
                                <label for="location-tab">Location (Tab)</label>
                                <select id="location-tab" required>
                                    <option value="">Select a location...</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="location-momence-host">Momence Host</label>
                                <select id="location-momence-host" required>
                                    <option value="">Select host...</option>
                                    {''.join(f'<option value="{escape_html(h)}">{escape_html(h)}</option>' for h in MOMENCE_HOSTS.keys())}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="location-source-id">Lead Source ID (optional)</label>
                                <input type="text" id="location-source-id" placeholder="Momence lead source ID">
                            </div>
                            <div class="form-group">
                                <label for="location-notification-email">Notification Email (optional)</label>
                                <input type="email" id="location-notification-email" placeholder="email@example.com">
                                <small class="text-muted">Leave blank to use Momence host email</small>
                            </div>
                        </form>
                    </div>
                    <div id="no-tabs-message" style="display: none;" class="text-muted">
                        All available tabs are already configured.
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('add-location-modal')">Cancel</button>
                    <button class="btn" id="add-location-btn" onclick="addLocation()" disabled>Add</button>
                </div>
            </div>
        </div>

        <script>
            // Get CSRF token from meta tag
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            // Helper function to make fetch requests with CSRF token
            function fetchWithCsrf(url, options = {{}}) {{
                options.headers = options.headers || {{}};
                options.headers['X-CSRF-Token'] = csrfToken;
                if (!options.headers['Content-Type'] && options.body) {{
                    options.headers['Content-Type'] = 'application/json';
                }}
                return fetch(url, options);
            }}

            function showAlert(message, type) {{
                const container = document.getElementById('alert-container');
                const alert = document.createElement('div');
                alert.className = 'alert alert-' + type;
                alert.textContent = message;
                container.appendChild(alert);
                setTimeout(() => alert.remove(), 5000);
            }}

            // ============ Collapsible Panels ============
            function toggleCollapsible(headerId, contentId) {{
                const header = document.getElementById(headerId);
                const content = document.getElementById(contentId);
                if (header && content) {{
                    header.classList.toggle('collapsed');
                    content.classList.toggle('collapsed');
                    localStorage.setItem(contentId + '-collapsed', content.classList.contains('collapsed'));
                }}
            }}

            function restoreCollapsibleState(headerId, contentId, defaultCollapsed = false) {{
                const stored = localStorage.getItem(contentId + '-collapsed');
                const isCollapsed = stored !== null ? stored === 'true' : defaultCollapsed;
                const header = document.getElementById(headerId);
                const content = document.getElementById(contentId);
                if (header && content && isCollapsed) {{
                    header.classList.add('collapsed');
                    content.classList.add('collapsed');
                }}
            }}

            // ============ Section Collapse/Expand ============
            function toggleSection(sectionId) {{
                const content = document.getElementById(sectionId + '-content');
                const toggle = document.getElementById(sectionId + '-toggle');
                const summary = document.getElementById(sectionId + '-summary');
                if (content && toggle) {{
                    const isCollapsed = content.classList.toggle('collapsed');
                    toggle.classList.toggle('collapsed', isCollapsed);
                    if (summary) {{
                        summary.classList.toggle('visible', isCollapsed);
                    }}
                    localStorage.setItem(sectionId + '-collapsed', isCollapsed);
                }}
            }}

            function restoreSectionState(sectionId, defaultCollapsed = false) {{
                const stored = localStorage.getItem(sectionId + '-collapsed');
                const isCollapsed = stored !== null ? stored === 'true' : defaultCollapsed;
                if (isCollapsed) {{
                    const content = document.getElementById(sectionId + '-content');
                    const toggle = document.getElementById(sectionId + '-toggle');
                    const summary = document.getElementById(sectionId + '-summary');
                    if (content) content.classList.add('collapsed');
                    if (toggle) toggle.classList.add('collapsed');
                    if (summary) summary.classList.add('visible');
                }}
            }}

            // ============ Host Filtering ============
            function filterHosts(filter) {{
                const rows = document.querySelectorAll('.host-row');
                const buttons = document.querySelectorAll('.host-filter-btn');

                buttons.forEach(btn => btn.classList.remove('active'));
                event.target.classList.add('active');

                rows.forEach(row => {{
                    const enabled = row.dataset.enabled === 'true';
                    if (filter === 'all') {{
                        row.style.display = '';
                    }} else if (filter === 'active') {{
                        row.style.display = enabled ? '' : 'none';
                    }} else if (filter === 'disabled') {{
                        row.style.display = enabled ? 'none' : '';
                    }}
                }});
            }}

            // ============ Admin Activity Log with Pagination ============
            let activityLogData = [];
            let activityLogPage = 0;
            const ACTIVITY_PAGE_SIZE = 10;

            function loadActivityLog() {{
                fetch('/api/admin-activity?limit=100')
                    .then(r => r.json())
                    .then(result => {{
                        if (result.success) {{
                            activityLogData = result.entries || [];
                            activityLogPage = 0;
                            renderActivityLog();
                        }}
                    }})
                    .catch(err => {{
                        console.error('Failed to load activity log:', err);
                    }});
            }}

            function renderActivityLog() {{
                const tbody = document.getElementById('activity-log-body');
                const paginationEl = document.getElementById('activity-pagination');

                if (!activityLogData || activityLogData.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="4" class="text-muted">No activity recorded</td></tr>';
                    if (paginationEl) paginationEl.innerHTML = '';
                    return;
                }}

                const totalPages = Math.ceil(activityLogData.length / ACTIVITY_PAGE_SIZE);
                const start = activityLogPage * ACTIVITY_PAGE_SIZE;
                const pageData = activityLogData.slice(start, start + ACTIVITY_PAGE_SIZE);

                tbody.innerHTML = pageData.map(entry => {{
                    const actionColors = {{
                        'login': '#059669',
                        'logout': '#6366f1',
                        'login_failed': '#dc2626',
                        'create_host': '#059669',
                        'delete_host': '#dc2626',
                        'toggle_host': '#f59e0b',
                        'create_location': '#059669',
                        'delete_location': '#dc2626',
                        'toggle_location': '#f59e0b',
                        'clear_error_tracking': '#8b5cf6'
                    }};
                    const color = actionColors[entry.action] || '#64748b';
                    const formattedTime = formatLocalTime(entry.timestamp);
                    return `<tr>
                        <td title="${{entry.timestamp}} (UTC)" style="white-space:nowrap;">${{formattedTime}}</td>
                        <td><span style="color:${{color}};font-weight:500;">${{entry.action}}</span></td>
                        <td style="font-size:12px;">${{entry.details || '-'}}</td>
                        <td style="font-size:11px;font-family:monospace;">${{entry.ip_address || '-'}}</td>
                    </tr>`;
                }}).join('');

                // Render pagination
                if (paginationEl && totalPages > 1) {{
                    paginationEl.innerHTML = `
                        <button class="btn btn-xs btn-secondary" onclick="activityPagePrev()" ${{activityLogPage === 0 ? 'disabled' : ''}}>&laquo; Prev</button>
                        <span style="margin:0 10px;font-size:12px;color:#64748b;">Page ${{activityLogPage + 1}} of ${{totalPages}} (${{activityLogData.length}} total)</span>
                        <button class="btn btn-xs btn-secondary" onclick="activityPageNext()" ${{activityLogPage >= totalPages - 1 ? 'disabled' : ''}}>Next &raquo;</button>
                    `;
                }} else if (paginationEl) {{
                    paginationEl.innerHTML = `<span style="font-size:12px;color:#64748b;">${{activityLogData.length}} entries</span>`;
                }}
            }}

            function activityPagePrev() {{
                if (activityLogPage > 0) {{
                    activityLogPage--;
                    renderActivityLog();
                }}
            }}

            function activityPageNext() {{
                const totalPages = Math.ceil(activityLogData.length / ACTIVITY_PAGE_SIZE);
                if (activityLogPage < totalPages - 1) {{
                    activityLogPage++;
                    renderActivityLog();
                }}
            }}

            function refreshActivityLog() {{
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = 'Refreshing...';
                loadActivityLog();
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Refresh';
                }}, 500);
            }}

            // ============ Application Logs ============
            function loadLogs() {{
                fetch('/api/logs?lines=50')
                    .then(r => r.json())
                    .then(result => {{
                        const output = document.getElementById('logs-output');
                        if (result.success && result.logs) {{
                            output.textContent = result.logs.join('\\n') || 'No logs available';
                        }} else {{
                            output.textContent = 'Failed to load logs';
                        }}
                    }})
                    .catch(err => {{
                        console.error('Failed to load logs:', err);
                        document.getElementById('logs-output').textContent = 'Error loading logs';
                    }});
            }}

            function refreshLogs() {{
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = 'Refreshing...';
                loadLogs();
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Refresh';
                }}, 500);
            }}

            // ============ Last Updated Tracking ============
            let lastUpdatedTime = Date.now();

            function updateLastUpdated() {{
                const el = document.getElementById('last-updated');
                if (el) {{
                    const seconds = Math.floor((Date.now() - lastUpdatedTime) / 1000);
                    if (seconds < 60) {{
                        el.textContent = seconds + 's ago';
                    }} else {{
                        el.textContent = Math.floor(seconds / 60) + 'm ago';
                    }}
                }}
            }}

            // ============ Dashboard Status Polling ============
            function updateDashboardStatus() {{
                fetch('/api/dashboard-status')
                    .then(r => r.json())
                    .then(result => {{
                        if (result.success) {{
                            // Update last check time
                            const lastCheckEl = document.querySelector('.utc-time[data-utc]');
                            if (lastCheckEl && result.last_check && result.last_check !== 'Never') {{
                                lastCheckEl.setAttribute('data-utc', result.last_check);
                                lastCheckEl.textContent = formatLocalTime(result.last_check);
                                lastCheckEl.title = result.last_check + ' (UTC)';
                            }}
                            // Update uptime
                            const headerP = document.querySelector('header p');
                            if (headerP && result.uptime) {{
                                const uptimeMatch = headerP.innerHTML.match(/Uptime: [^<]+/);
                                if (uptimeMatch) {{
                                    headerP.innerHTML = headerP.innerHTML.replace(/Uptime: [^<]+/, 'Uptime: ' + result.uptime);
                                }}
                            }}
                        }}
                    }})
                    .catch(err => console.error('Failed to update status:', err));
            }}

            // ============ Initialize on Page Load ============
            document.addEventListener('DOMContentLoaded', function() {{
                // Load data
                loadActivityLog();
                loadLeadsChart();
                loadLogs();

                // Restore collapsible states (default to collapsed for both)
                restoreCollapsibleState('activity-header', 'activity-content', true);
                restoreCollapsibleState('logs-header', 'logs-content', true);

                // Restore section collapse states (hosts collapsed by default if > 5 hosts)
                const hostCount = document.querySelectorAll('.host-row').length;
                restoreSectionState('hosts-section', hostCount > 5);

                // Update "last updated" display every second
                setInterval(updateLastUpdated, 1000);

                // Poll for dashboard status every 30 seconds
                setInterval(updateDashboardStatus, 30000);

                // Mark initial load time
                lastUpdatedTime = Date.now();

                // Convert timestamps after a short delay to ensure DOM is ready
                setTimeout(convertAllTimestamps, 100);
            }});

            // ============ Leads Chart ============
            // Distinct colors for chart - first colors are most different to ensure contrast
            const chartColors = [
                '#3b82f6', '#22c55e', '#f97316', '#ec4899', '#8b5cf6',
                '#06b6d4', '#eab308', '#f43f5e', '#14b8a6', '#6366f1'
            ];

            function loadLeadsChart() {{
                const days = document.getElementById('chart-days').value;
                const wrapper = document.getElementById('chart-wrapper');
                const legend = document.getElementById('chart-legend');
                const summary = document.getElementById('chart-summary');

                wrapper.innerHTML = '<div class="chart-loading">Loading chart data...</div>';
                legend.innerHTML = '';
                summary.innerHTML = '';

                fetch('/api/leads-chart?days=' + days)
                    .then(r => r.json())
                    .then(result => {{
                        if (!result.success) {{
                            wrapper.innerHTML = '<div class="chart-empty">Failed to load chart data</div>';
                            return;
                        }}

                        const data = result.data;

                        if (!data.dates || data.dates.length === 0) {{
                            wrapper.innerHTML = `
                                <div class="chart-empty">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                    <div>No lead data available for this period</div>
                                    <div style="font-size:12px;margin-top:4px;">Leads will appear here once processed</div>
                                </div>
                            `;
                            return;
                        }}

                        renderBarChart(data, wrapper);
                        renderChartLegend(data, legend);
                        loadChartSummary(days, summary);
                    }})
                    .catch(err => {{
                        wrapper.innerHTML = '<div class="chart-empty">Error loading chart: ' + err.message + '</div>';
                    }});
            }}

            function renderBarChart(data, container) {{
                const dates = data.dates;
                const locations = data.location_list || [];
                const locationData = data.locations || {{}};

                // Calculate max value for scaling
                let maxValue = Math.max(...data.totals, 1);

                // Build SVG chart
                const width = container.offsetWidth || 800;
                const height = 280;
                const padding = {{ top: 20, right: 20, bottom: 50, left: 50 }};
                const chartWidth = width - padding.left - padding.right;
                const chartHeight = height - padding.top - padding.bottom;

                const barGroupWidth = chartWidth / dates.length;
                const barWidth = Math.min(barGroupWidth * 0.6 / Math.max(locations.length, 1), 30);
                const groupPadding = (barGroupWidth - barWidth * locations.length) / 2;

                let svg = `<svg width="${{width}}" height="${{height}}" style="display:block;">`;

                // Y-axis gridlines and labels
                const yTicks = 5;
                for (let i = 0; i <= yTicks; i++) {{
                    const y = padding.top + (chartHeight / yTicks) * i;
                    const value = Math.round(maxValue - (maxValue / yTicks) * i);
                    svg += `<line x1="${{padding.left}}" y1="${{y}}" x2="${{width - padding.right}}" y2="${{y}}" stroke="#e2e8f0" stroke-width="1"/>`;
                    svg += `<text x="${{padding.left - 10}}" y="${{y + 4}}" text-anchor="end" font-size="11" fill="#64748b">${{value}}</text>`;
                }}

                // Bars for each location stacked by date
                dates.forEach((date, dateIdx) => {{
                    const x = padding.left + dateIdx * barGroupWidth + groupPadding;
                    let stackY = padding.top + chartHeight;

                    // Stack bars for each location
                    locations.forEach((loc, locIdx) => {{
                        const value = locationData[loc] ? locationData[loc][dateIdx] : 0;
                        if (value > 0) {{
                            const barHeight = (value / maxValue) * chartHeight;
                            const barX = x + locIdx * barWidth;
                            const barY = padding.top + chartHeight - barHeight;
                            const color = chartColors[locIdx % chartColors.length];

                            svg += `<rect x="${{barX}}" y="${{barY}}" width="${{barWidth - 1}}" height="${{barHeight}}" fill="${{color}}" rx="2">
                                <title>${{loc}}: ${{value}} leads on ${{date}}</title>
                            </rect>`;
                        }}
                    }});

                    // X-axis date/time label (show every nth label to avoid crowding)
                    const isHourly = date.includes('T') || date.includes(':');
                    const labelInterval = isHourly ? Math.ceil(dates.length / 8) : Math.ceil(dates.length / 10);
                    const showLabel = dates.length <= 14 || dateIdx % labelInterval === 0;
                    if (showLabel) {{
                        const labelX = x + (barWidth * locations.length) / 2;
                        let shortDate;
                        if (isHourly) {{
                            // Format hourly as "1/20 3PM"
                            // Input format: "2026-01-20T15:00" or "2026-01-20 15:00"
                            const datePart = date.substring(0, 10);
                            const hourPart = date.substring(11, 13);
                            const [, month, day] = datePart.split('-');
                            const hour = parseInt(hourPart);
                            const ampm = hour >= 12 ? 'PM' : 'AM';
                            const hour12 = hour % 12 || 12;
                            shortDate = parseInt(month) + '/' + parseInt(day) + ' ' + hour12 + ampm;
                        }} else {{
                            // Format as M/DD (e.g., "1/20" instead of "01-20")
                            const [, month, day] = date.split('-');
                            shortDate = parseInt(month) + '/' + parseInt(day);
                        }}
                        svg += `<text x="${{labelX}}" y="${{height - 10}}" text-anchor="middle" font-size="10" fill="#64748b">${{shortDate}}</text>`;
                    }}
                }});

                // Axes
                svg += `<line x1="${{padding.left}}" y1="${{padding.top}}" x2="${{padding.left}}" y2="${{padding.top + chartHeight}}" stroke="#cbd5e1" stroke-width="1"/>`;
                svg += `<line x1="${{padding.left}}" y1="${{padding.top + chartHeight}}" x2="${{width - padding.right}}" y2="${{padding.top + chartHeight}}" stroke="#cbd5e1" stroke-width="1"/>`;

                svg += '</svg>';
                container.innerHTML = svg;
            }}

            function renderChartLegend(data, container) {{
                const locations = data.location_list || [];
                const locationData = data.locations || {{}};

                let html = '';
                locations.forEach((loc, idx) => {{
                    const color = chartColors[idx % chartColors.length];
                    const total = locationData[loc] ? locationData[loc].reduce((a, b) => a + b, 0) : 0;
                    html += `<div class="legend-item">
                        <span class="legend-color" style="background:${{color}}"></span>
                        <span>${{loc}} (${{total}})</span>
                    </div>`;
                }});

                container.innerHTML = html;
            }}

            function loadChartSummary(days, container) {{
                fetch('/api/leads-summary?days=' + days)
                    .then(r => r.json())
                    .then(result => {{
                        if (!result.success || !result.data) return;

                        const data = result.data;
                        const totalSent = data.by_location.reduce((sum, loc) => sum + loc.total_sent, 0);
                        const totalFailed = data.by_location.reduce((sum, loc) => sum + loc.total_failed, 0);

                        let html = `
                            <div class="summary-item">
                                <div class="summary-value">${{totalSent}}</div>
                                <div class="summary-label">Total Sent</div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-value" style="color:${{totalFailed > 0 ? '#f59e0b' : '#10b981'}}">${{totalFailed}}</div>
                                <div class="summary-label">Total Failed</div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-value">${{data.avg_per_day}}</div>
                                <div class="summary-label">Avg/Day</div>
                            </div>
                        `;

                        if (data.best_day) {{
                            html += `<div class="summary-item">
                                <div class="summary-value" style="color:#10b981">${{data.best_day.count}}</div>
                                <div class="summary-label">Best Day (${{data.best_day.date.substring(5)}})</div>
                            </div>`;
                        }}

                        container.innerHTML = html;
                    }});
            }}

            function closeModal(id) {{
                document.getElementById(id).classList.remove('active');
                // Hide test email button when closing sheet modal
                if (id === 'sheet-modal') {{
                    document.getElementById('test-email-btn').style.display = 'none';
                }}
            }}

            function showAddHostModal() {{
                document.getElementById('host-modal-title').textContent = 'Add Momence Host';
                document.getElementById('host-form').reset();
                document.getElementById('host-original-name').value = '';
                document.getElementById('host-enabled').checked = true;
                document.getElementById('host-modal').classList.add('active');
            }}

            function editHost(name) {{
                fetch('/api/hosts/' + encodeURIComponent(name))
                    .then(r => r.json())
                    .then(data => {{
                        document.getElementById('host-modal-title').textContent = 'Edit Momence Host';
                        document.getElementById('host-original-name').value = name;
                        document.getElementById('host-name').value = name;
                        document.getElementById('host-host-id').value = data.host_id || '';
                        document.getElementById('host-token').value = data.token || '';
                        document.getElementById('host-enabled').checked = data.enabled !== false;
                        document.getElementById('host-modal').classList.add('active');
                    }});
            }}

            function saveHost() {{
                const originalName = document.getElementById('host-original-name').value;
                const name = document.getElementById('host-name').value;
                const data = {{
                    host_id: document.getElementById('host-host-id').value,
                    token: document.getElementById('host-token').value,
                    enabled: document.getElementById('host-enabled').checked
                }};

                const url = originalName ? '/api/hosts/' + encodeURIComponent(originalName) : '/api/hosts';
                const method = originalName ? 'PUT' : 'POST';

                fetchWithCsrf(url, {{
                    method: method,
                    body: JSON.stringify({{name: name, ...data}})
                }})
                .then(r => r.json())
                .then(result => {{
                    if (result.success) {{
                        const msg = result.secret_stored
                            ? 'Host saved (API token stored in Secret Manager)'
                            : 'Host saved successfully';
                        showAlert(msg, 'success');
                        closeModal('host-modal');
                        setTimeout(() => location.reload(), 500);
                    }} else {{
                        showAlert(result.error || 'Failed to save host', 'error');
                    }}
                }});
            }}

            function toggleHost(name, enabled) {{
                fetchWithCsrf('/api/hosts/' + encodeURIComponent(name) + '/toggle', {{
                    method: 'POST',
                    body: JSON.stringify({{enabled: enabled}})
                }})
                .then(r => r.json())
                .then(result => {{
                    if (result.success) {{
                        showAlert('Host ' + (enabled ? 'enabled' : 'disabled'), 'success');
                        setTimeout(() => location.reload(), 500);
                    }} else {{
                        showAlert(result.error || 'Failed to update host', 'error');
                    }}
                }});
            }}

            // ============ Delete Confirmation Modal ============
            let pendingDelete = null;  // {{type: 'host'|'location', name: string}}

            function deleteHost(name) {{
                pendingDelete = {{type: 'host', name: name}};
                document.getElementById('delete-modal-title').textContent = 'Delete Host';
                document.getElementById('delete-modal-message').innerHTML =
                    'You are about to delete the Momence host <strong>"' + escapeHtml(name) + '"</strong>.<br><br>' +
                    '<span style="color:#b91c1c;">This will NOT delete associated locations.</span> You will need to reassign or delete them separately.';
                document.getElementById('delete-modal-name-display').textContent = name;
                document.getElementById('delete-confirm-input').value = '';
                document.getElementById('delete-confirm-btn').disabled = true;
                document.getElementById('delete-confirm-btn').style.opacity = '0.5';
                document.getElementById('delete-input-error').style.display = 'none';
                document.getElementById('delete-modal').classList.add('active');
                document.getElementById('delete-confirm-input').focus();
            }}

            function deleteSheet(name) {{
                pendingDelete = {{type: 'location', name: name}};
                document.getElementById('delete-modal-title').textContent = 'Delete Location';
                document.getElementById('delete-modal-message').innerHTML =
                    'You are about to delete the location <strong>"' + escapeHtml(name) + '"</strong>.<br><br>' +
                    'This will stop monitoring this sheet. Existing leads and tracking data will NOT be affected.';
                document.getElementById('delete-modal-name-display').textContent = name;
                document.getElementById('delete-confirm-input').value = '';
                document.getElementById('delete-confirm-btn').disabled = true;
                document.getElementById('delete-confirm-btn').style.opacity = '0.5';
                document.getElementById('delete-input-error').style.display = 'none';
                document.getElementById('delete-modal').classList.add('active');
                document.getElementById('delete-confirm-input').focus();
            }}

            function validateDeleteInput() {{
                if (!pendingDelete) return;
                const input = document.getElementById('delete-confirm-input').value;
                const btn = document.getElementById('delete-confirm-btn');
                const errorEl = document.getElementById('delete-input-error');

                if (input === pendingDelete.name) {{
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    errorEl.style.display = 'none';
                }} else {{
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                    errorEl.style.display = input.length > 0 ? 'block' : 'none';
                }}
            }}

            function confirmDelete() {{
                if (!pendingDelete) return;
                const input = document.getElementById('delete-confirm-input').value;
                if (input !== pendingDelete.name) {{
                    showAlert('Name does not match', 'error');
                    return;
                }}

                const name = pendingDelete.name;
                const type = pendingDelete.type;

                const endpoint = type === 'host'
                    ? '/api/hosts/' + encodeURIComponent(name)
                    : '/api/sheets/' + encodeURIComponent(name);

                closeModal('delete-modal');

                fetchWithCsrf(endpoint, {{
                    method: 'DELETE'
                }})
                .then(r => r.json())
                .then(result => {{
                    pendingDelete = null;
                    if (result.success) {{
                        showAlert((type === 'host' ? 'Host' : 'Location') + ' deleted successfully', 'success');
                        // Force immediate page reload
                        window.location.reload(true);
                    }} else {{
                        showAlert(result.error || 'Failed to delete ' + type, 'error');
                    }}
                }})
                .catch(err => {{
                    pendingDelete = null;
                    showAlert('Network error: ' + err.message, 'error');
                }});
            }}

            function escapeHtml(text) {{
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }}

            function editSheet(name) {{
                fetch('/api/sheets/' + encodeURIComponent(name))
                    .then(r => r.json())
                    .then(data => {{
                        document.getElementById('sheet-modal-title').textContent = 'Edit Location';
                        document.getElementById('sheet-original-name').value = name;
                        document.getElementById('sheet-name').value = data.name || '';
                        document.getElementById('sheet-momence-host').value = data.momence_host || '';
                        document.getElementById('sheet-spreadsheet-id').value = data.spreadsheet_id || '';
                        document.getElementById('sheet-gid').value = data.gid || '0';
                        document.getElementById('sheet-lead-source-id').value = data.lead_source_id || '';
                        document.getElementById('sheet-notification-email').value = data.notification_email || '';
                        document.getElementById('sheet-enabled').checked = data.enabled !== false;
                        // Show test email button in edit mode (existing location)
                        document.getElementById('test-email-btn').style.display = 'inline-block';
                        document.getElementById('sheet-modal').classList.add('active');
                    }});
            }}

            function saveSheet() {{
                const originalName = document.getElementById('sheet-original-name').value;
                const data = {{
                    name: document.getElementById('sheet-name').value,
                    momence_host: document.getElementById('sheet-momence-host').value,
                    spreadsheet_id: document.getElementById('sheet-spreadsheet-id').value,
                    gid: document.getElementById('sheet-gid').value,
                    lead_source_id: document.getElementById('sheet-lead-source-id').value,
                    notification_email: document.getElementById('sheet-notification-email').value.trim(),
                    enabled: document.getElementById('sheet-enabled').checked
                }};

                const url = originalName ? '/api/sheets/' + encodeURIComponent(originalName) : '/api/sheets';
                const method = originalName ? 'PUT' : 'POST';

                fetchWithCsrf(url, {{
                    method: method,
                    body: JSON.stringify(data)
                }})
                .then(r => r.json())
                .then(result => {{
                    if (result.success) {{
                        showAlert('Location saved successfully', 'success');
                        closeModal('sheet-modal');
                        setTimeout(() => location.reload(), 500);
                    }} else {{
                        showAlert(result.error || 'Failed to save location', 'error');
                    }}
                }});
            }}

            function toggleSheet(name, enabled) {{
                fetchWithCsrf('/api/sheets/' + encodeURIComponent(name) + '/toggle', {{
                    method: 'POST',
                    body: JSON.stringify({{enabled: enabled}})
                }})
                .then(r => r.json())
                .then(result => {{
                    if (result.success) {{
                        showAlert('Sheet ' + (enabled ? 'enabled' : 'disabled'), 'success');
                        setTimeout(() => location.reload(), 500);
                    }} else {{
                        showAlert(result.error || 'Failed to update sheet', 'error');
                    }}
                }});
            }}

            function testLocationEmail() {{
                const name = document.getElementById('sheet-original-name').value;
                if (!name) {{
                    showAlert('Please save the location first', 'error');
                    return;
                }}

                const btn = document.getElementById('test-email-btn');
                const originalText = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Sending...';

                fetchWithCsrf('/api/sheets/' + encodeURIComponent(name) + '/test-email', {{
                    method: 'POST',
                    body: JSON.stringify({{}})
                }})
                .then(r => r.json())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    if (result.success) {{
                        showAlert('Test email sent to: ' + result.recipients.join(', '), 'success');
                    }} else {{
                        showAlert(result.error || 'Failed to send test email', 'error');
                    }}
                }})
                .catch(err => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    showAlert('Failed to send test email: ' + err.message, 'error');
                }});
            }}

            function clearErrorEmailTracking() {{
                if (!confirm('Reset error email tracking?\\n\\nThe next error will immediately trigger an error email to admin.')) {{
                    return;
                }}
                fetchWithCsrf('/api/clear-error-email-tracking', {{
                    method: 'POST',
                    body: JSON.stringify({{}})
                }})
                .then(r => r.json())
                .then(result => {{
                    if (result.success) {{
                        showAlert('Error email tracking cleared', 'success');
                        setTimeout(() => location.reload(), 500);
                    }} else {{
                        showAlert(result.error || 'Failed to clear tracking', 'error');
                    }}
                }});
            }}

            function retryAllFailed() {{
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = 'Retrying...';
                btn.style.opacity = '0.7';

                // Show progress overlay
                showRetryProgress();

                // Use EventSource for SSE streaming
                const eventSource = new EventSource('/api/retry-failed');

                eventSource.onmessage = function(event) {{
                    const data = JSON.parse(event.data);

                    if (data.type === 'start') {{
                        updateRetryProgress(0, data.total, '', 0, 0);
                    }} else if (data.type === 'progress') {{
                        // Update progress bar and current email
                        const progressEl = document.getElementById('retry-progress-bar');
                        const countEl = document.getElementById('retry-progress-count');
                        const emailEl = document.getElementById('retry-progress-email');

                        if (progressEl) {{
                            const pct = (data.current / data.total) * 100;
                            progressEl.style.width = pct + '%';
                        }}
                        if (countEl) {{
                            countEl.textContent = data.current + ' of ' + data.total;
                        }}
                        if (emailEl) {{
                            emailEl.textContent = data.email;
                        }}

                        // Highlight the row being processed
                        const row = document.querySelector(`tr[data-email="${{data.email.toLowerCase()}}"]`);
                        if (row) {{
                            row.style.backgroundColor = '#fef3c7';
                        }}
                    }} else if (data.type === 'result') {{
                        // Update success/failed counts
                        const successEl = document.getElementById('retry-success-count');
                        const failedEl = document.getElementById('retry-failed-count');

                        if (data.success) {{
                            if (successEl) successEl.textContent = parseInt(successEl.textContent || 0) + 1;
                            // Green highlight for success
                            const row = document.querySelector(`tr[data-email="${{data.email.toLowerCase()}}"]`);
                            if (row) row.style.backgroundColor = '#d1fae5';
                        }} else {{
                            if (failedEl) failedEl.textContent = parseInt(failedEl.textContent || 0) + 1;
                            // Red highlight for failure
                            const row = document.querySelector(`tr[data-email="${{data.email.toLowerCase()}}"]`);
                            if (row) row.style.backgroundColor = '#fee2e2';
                        }}
                    }} else if (data.type === 'complete') {{
                        eventSource.close();
                        showRetryComplete(data.successful, data.failed);

                        btn.disabled = false;
                        btn.textContent = 'Retry All';
                        btn.style.opacity = '1';

                        // Reload after showing completion
                        setTimeout(() => location.reload(), 2500);
                    }}
                }};

                eventSource.onerror = function(err) {{
                    eventSource.close();
                    hideRetryProgress();
                    btn.disabled = false;
                    btn.textContent = 'Retry All';
                    btn.style.opacity = '1';
                    showAlert('Connection error during retry', 'error');
                }};
            }}

            function showRetryProgress() {{
                let overlay = document.getElementById('retry-progress-overlay');
                if (!overlay) {{
                    overlay = document.createElement('div');
                    overlay.id = 'retry-progress-overlay';
                    document.body.appendChild(overlay);
                }}
                overlay.innerHTML = `
                    <div class="retry-progress-content">
                        <div class="retry-progress-header">Retrying Failed Leads</div>
                        <div class="retry-progress-bar-container">
                            <div class="retry-progress-bar" id="retry-progress-bar"></div>
                        </div>
                        <div class="retry-progress-count" id="retry-progress-count">Starting...</div>
                        <div class="retry-progress-current">
                            <div class="retry-progress-current-label">Currently processing</div>
                            <div class="retry-progress-current-email" id="retry-progress-email">-</div>
                        </div>
                        <div class="retry-progress-results">
                            <div class="retry-result-item">
                                <div class="retry-result-count success" id="retry-success-count">0</div>
                                <div class="retry-result-label">Succeeded</div>
                            </div>
                            <div class="retry-result-item">
                                <div class="retry-result-count failed" id="retry-failed-count">0</div>
                                <div class="retry-result-label">Failed</div>
                            </div>
                        </div>
                        <div class="retry-progress-complete" id="retry-complete-section">
                            <div class="retry-progress-complete-icon" id="retry-complete-icon"></div>
                            <div class="retry-progress-complete-text" id="retry-complete-text"></div>
                        </div>
                    </div>
                `;
                overlay.style.display = 'flex';
            }}

            function updateRetryProgress(current, total, email, successCount, failedCount) {{
                const progressEl = document.getElementById('retry-progress-bar');
                const countEl = document.getElementById('retry-progress-count');
                const emailEl = document.getElementById('retry-progress-email');
                const successEl = document.getElementById('retry-success-count');
                const failedEl = document.getElementById('retry-failed-count');

                if (progressEl && total > 0) {{
                    const pct = (current / total) * 100;
                    progressEl.style.width = pct + '%';
                }}
                if (countEl) countEl.textContent = current + ' of ' + total;
                if (emailEl) emailEl.textContent = email || '-';
                if (successEl) successEl.textContent = successCount;
                if (failedEl) failedEl.textContent = failedCount;
            }}

            function showRetryComplete(successful, failed) {{
                const completeSection = document.getElementById('retry-complete-section');
                const iconEl = document.getElementById('retry-complete-icon');
                const textEl = document.getElementById('retry-complete-text');
                const progressBar = document.getElementById('retry-progress-bar');

                if (progressBar) progressBar.style.width = '100%';

                if (completeSection) {{
                    completeSection.style.display = 'block';
                    if (failed === 0) {{
                        completeSection.className = 'retry-progress-complete success';
                        if (iconEl) iconEl.textContent = '✓';
                        if (textEl) textEl.textContent = 'All ' + successful + ' leads sent successfully!';
                    }} else {{
                        completeSection.className = 'retry-progress-complete partial';
                        if (iconEl) iconEl.textContent = '⚠';
                        if (textEl) textEl.textContent = successful + ' succeeded, ' + failed + ' still failing';
                    }}
                }}
            }}

            function hideRetryProgress() {{
                const overlay = document.getElementById('retry-progress-overlay');
                if (overlay) overlay.style.display = 'none';
            }}

            // ============ Failed Queue Pagination ============
            let failedQueuePage = 0;
            const FAILED_PAGE_SIZE = 10;
            let allFailedRows = [];  // Store all row pairs (main + details)

            function initFailedQueuePagination() {{
                const tbody = document.getElementById('failed-queue-body');
                const rows = Array.from(tbody.querySelectorAll('tr.failed-row'));
                allFailedRows = rows.map(row => {{
                    const detailsRow = row.nextElementSibling;
                    return {{
                        main: row,
                        details: (detailsRow && detailsRow.classList.contains('error-details-row')) ? detailsRow : null
                    }};
                }});
                failedQueuePage = 0;
                renderFailedQueuePage();
            }}

            function renderFailedQueuePage() {{
                const tbody = document.getElementById('failed-queue-body');
                const paginationEl = document.getElementById('failed-queue-pagination');
                const search = document.getElementById('failed-search').value.toLowerCase();
                const sortBy = document.getElementById('failed-sort').value;

                // Filter
                let filtered = allFailedRows.filter(pair => {{
                    const email = pair.main.getAttribute('data-email') || '';
                    return email.includes(search);
                }});

                // Sort
                filtered.sort((a, b) => {{
                    if (sortBy === 'email') {{
                        return (a.main.getAttribute('data-email') || '').localeCompare(b.main.getAttribute('data-email') || '');
                    }} else if (sortBy === 'attempts') {{
                        return parseInt(b.main.getAttribute('data-attempts') || 0) - parseInt(a.main.getAttribute('data-attempts') || 0);
                    }} else {{ // recent
                        const timeA = a.main.getAttribute('data-timestamp') || '';
                        const timeB = b.main.getAttribute('data-timestamp') || '';
                        return timeB.localeCompare(timeA);
                    }}
                }});

                const totalPages = Math.ceil(filtered.length / FAILED_PAGE_SIZE);
                if (failedQueuePage >= totalPages && totalPages > 0) failedQueuePage = totalPages - 1;
                if (failedQueuePage < 0) failedQueuePage = 0;

                const start = failedQueuePage * FAILED_PAGE_SIZE;
                const pageData = filtered.slice(start, start + FAILED_PAGE_SIZE);

                // Clear and re-render
                tbody.innerHTML = '';
                if (pageData.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="6" class="text-muted">No entries found</td></tr>';
                }} else {{
                    pageData.forEach(pair => {{
                        tbody.appendChild(pair.main);
                        if (pair.details) {{
                            pair.details.style.display = 'none';  // Always hide details on page change
                            tbody.appendChild(pair.details);
                        }}
                    }});
                }}

                // Render pagination
                if (paginationEl) {{
                    if (filtered.length > FAILED_PAGE_SIZE) {{
                        paginationEl.innerHTML = `
                            <button class="btn btn-xs btn-secondary" onclick="failedPagePrev()" ${{failedQueuePage === 0 ? 'disabled' : ''}}>&laquo; Prev</button>
                            <span style="margin:0 10px;font-size:12px;color:#64748b;">Page ${{failedQueuePage + 1}} of ${{totalPages}} (${{filtered.length}} total)</span>
                            <button class="btn btn-xs btn-secondary" onclick="failedPageNext()" ${{failedQueuePage >= totalPages - 1 ? 'disabled' : ''}}>Next &raquo;</button>
                        `;
                    }} else {{
                        paginationEl.innerHTML = filtered.length > 0 ? `<span style="font-size:12px;color:#64748b;">${{filtered.length}} entries</span>` : '';
                    }}
                }}
            }}

            function failedPagePrev() {{
                if (failedQueuePage > 0) {{
                    failedQueuePage--;
                    renderFailedQueuePage();
                }}
            }}

            function failedPageNext() {{
                failedQueuePage++;
                renderFailedQueuePage();
            }}

            function filterFailedQueue() {{
                failedQueuePage = 0;
                renderFailedQueuePage();
            }}

            function sortFailedQueue() {{
                failedQueuePage = 0;
                renderFailedQueuePage();
            }}

            // Initialize pagination on load
            document.addEventListener('DOMContentLoaded', function() {{
                initFailedQueuePagination();
            }});

            function toggleErrorDetails(rowId) {{
                const row = document.getElementById(rowId);
                if (row) {{
                    const isVisible = row.style.display !== 'none';
                    row.style.display = isVisible ? 'none' : 'table-row';
                    // Update the toggle indicator in the previous row
                    const prevRow = row.previousElementSibling;
                    if (prevRow) {{
                        const toggleSpan = prevRow.querySelector('td:last-child span');
                        if (toggleSpan) {{
                            toggleSpan.textContent = isVisible ? '▶ Details' : '▼ Hide';
                        }}
                    }}
                }}
            }}

            // ============ Add Location Functions ============
            let availableTabs = [];
            let spreadsheetId = null;

            function showAddLocationModal() {{
                document.getElementById('available-tabs-loading').style.display = 'block';
                document.getElementById('available-tabs-content').style.display = 'none';
                document.getElementById('no-tabs-message').style.display = 'none';
                document.getElementById('add-location-btn').disabled = true;
                document.getElementById('add-location-form').reset();
                document.getElementById('add-location-modal').classList.add('active');

                // Load available tabs
                fetch('/api/available-tabs')
                    .then(r => r.json())
                    .then(result => {{
                        document.getElementById('available-tabs-loading').style.display = 'none';

                        if (!result.success) {{
                            showAlert(result.error || 'Failed to load tabs', 'error');
                            return;
                        }}

                        spreadsheetId = result.spreadsheet_id;
                        availableTabs = result.tabs || [];

                        if (availableTabs.length === 0) {{
                            document.getElementById('no-tabs-message').style.display = 'block';
                            return;
                        }}

                        // Populate dropdown
                        const select = document.getElementById('location-tab');
                        select.innerHTML = '<option value="">Select a location...</option>';
                        availableTabs.forEach((tab, idx) => {{
                            const option = document.createElement('option');
                            option.value = idx;
                            option.textContent = tab.name;
                            select.appendChild(option);
                        }});

                        document.getElementById('available-tabs-content').style.display = 'block';
                        document.getElementById('add-location-btn').disabled = false;
                    }})
                    .catch(err => {{
                        document.getElementById('available-tabs-loading').style.display = 'none';
                        showAlert('Error loading tabs: ' + err.message, 'error');
                    }});
            }}

            function addLocation() {{
                const tabIdx = document.getElementById('location-tab').value;
                const momenceHost = document.getElementById('location-momence-host').value;
                const sourceId = document.getElementById('location-source-id').value.trim();
                const notificationEmail = document.getElementById('location-notification-email').value.trim();

                if (tabIdx === '') {{
                    showAlert('Please select a location', 'error');
                    return;
                }}
                if (!momenceHost) {{
                    showAlert('Please select a Momence host', 'error');
                    return;
                }}

                const tab = availableTabs[parseInt(tabIdx)];

                fetchWithCsrf('/api/import-sheets', {{
                    method: 'POST',
                    body: JSON.stringify({{
                        spreadsheet_id: spreadsheetId,
                        momence_host: momenceHost,
                        tabs: [{{
                            name: tab.name,
                            gid: tab.gid,
                            lead_source_id: sourceId ? parseInt(sourceId) : null,
                            notification_email: notificationEmail || null
                        }}]
                    }})
                }})
                .then(r => r.json())
                .then(result => {{
                    if (result.success) {{
                        showAlert('Added location: ' + tab.name, 'success');
                        closeModal('add-location-modal');
                        setTimeout(() => location.reload(), 500);
                    }} else {{
                        showAlert(result.error || 'Failed to add location', 'error');
                    }}
                }})
                .catch(err => {{
                    showAlert('Error: ' + err.message, 'error');
                }});
            }}

            // ============ Settings Functions ============
            function showSettingsModal() {{
                fetch('/api/settings')
                    .then(r => r.json())
                    .then(data => {{
                        document.getElementById('setting-dlq-enabled').checked = data.dlq_enabled;
                        document.getElementById('setting-dlq-max-attempts').value = data.dlq_max_retry_attempts;
                        document.getElementById('setting-rate-limit').value = data.rate_limit_delay_seconds;
                        document.getElementById('setting-log-retention').value = data.log_retention_days;
                        document.getElementById('setting-log-level').value = data.log_level;
                        document.getElementById('setting-default-spreadsheet').value = data.default_spreadsheet_id || '';

                        document.getElementById('settings-modal').classList.add('active');
                    }})
                    .catch(err => {{
                        showAlert('Failed to load settings: ' + err.message, 'error');
                    }});
            }}

            function saveSettings() {{
                const data = {{
                    dlq_enabled: document.getElementById('setting-dlq-enabled').checked,
                    dlq_max_retry_attempts: document.getElementById('setting-dlq-max-attempts').value,
                    rate_limit_delay_seconds: document.getElementById('setting-rate-limit').value,
                    log_retention_days: document.getElementById('setting-log-retention').value,
                    log_level: document.getElementById('setting-log-level').value,
                    default_spreadsheet_id: document.getElementById('setting-default-spreadsheet').value
                }};

                fetchWithCsrf('/api/settings', {{
                    method: 'POST',
                    body: JSON.stringify(data)
                }})
                .then(r => r.json())
                .then(result => {{
                    if (result.success) {{
                        showAlert('Settings saved successfully', 'success');
                        closeModal('settings-modal');
                    }} else {{
                        showAlert(result.error || 'Failed to save settings', 'error');
                    }}
                }})
                .catch(err => {{
                    showAlert('Error saving settings: ' + err.message, 'error');
                }});
            }}

            // Modals require explicit Save or Cancel - no click-outside-to-close

            // Convert UTC timestamps to browser local time
            function formatLocalTime(utcString) {{
                if (!utcString || utcString === 'N/A' || utcString === 'None' || utcString === 'Never') {{
                    return utcString;
                }}
                try {{
                    // Normalize the timestamp - replace +00:00 with Z for consistent parsing
                    let normalized = utcString.replace('+00:00', 'Z').replace(' ', 'T');
                    let date = new Date(normalized);

                    // If still invalid, try adding Z for timezone-naive timestamps
                    if (isNaN(date.getTime()) && !normalized.includes('Z') && !normalized.includes('+') && !normalized.includes('-', 10)) {{
                        date = new Date(normalized + 'Z');
                    }}

                    if (isNaN(date.getTime())) {{
                        return utcString;
                    }}
                    // Format: "Jan 19, 2026, 3:45:30 PM"
                    return date.toLocaleString(undefined, {{
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: true
                    }});
                }} catch (e) {{
                    return utcString;
                }}
            }}

            function convertAllTimestamps() {{
                document.querySelectorAll('.utc-time').forEach(el => {{
                    const utc = el.getAttribute('data-utc');
                    if (utc) {{
                        el.textContent = formatLocalTime(utc);
                        el.title = utc + ' (UTC)';  // Show original UTC on hover
                    }}
                }});
                // Convert build time to short local format
                document.querySelectorAll('.build-time').forEach(el => {{
                    const utc = el.getAttribute('data-utc');
                    if (utc) {{
                        try {{
                            const date = new Date(utc);
                            if (!isNaN(date.getTime())) {{
                                // Short format for footer: "Jan 21, 3:45 PM"
                                el.textContent = date.toLocaleString(undefined, {{
                                    month: 'short',
                                    day: 'numeric',
                                    hour: 'numeric',
                                    minute: '2-digit',
                                    hour12: true
                                }});
                                el.title = utc + ' (UTC)';
                            }}
                        }} catch (e) {{
                            el.textContent = utc;
                        }}
                    }}
                }});
            }}

            // Convert timestamps on page load
            convertAllTimestamps();
        </script>
    </body>
    </html>
    """


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health check and dashboard endpoints."""

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass

    def finish(self):
        """
        Clean up after each request.

        This ensures thread-local database connections are closed after each
        request to prevent memory leaks in the ThreadingHTTPServer.
        """
        try:
            # Close thread-local DB connection without cloud upload (too slow per-request)
            storage.close_connection(upload_to_cloud=False)
        except Exception as e:
            # Log but don't let cleanup errors break the response
            logger.debug(f"DB connection cleanup error (non-fatal): {e}")

        # Call parent finish() to complete the request
        super().finish()

    def _is_api_request(self) -> bool:
        """Check if this is an API request (expects JSON response)."""
        path = self.path.split('?')[0]
        accept_header = self.headers.get('Accept', '')
        has_api_key = bool(self.headers.get('X-API-Key'))

        # API requests: /api/* paths, Accept: application/json, or X-API-Key header
        return (
            path.startswith('/api/') or
            'application/json' in accept_header or
            has_api_key
        )

    def _check_auth_and_respond(self, redirect_to_login: bool = True) -> bool:
        """
        Check authentication and send appropriate response if failed.

        Args:
            redirect_to_login: If True, redirect browser requests to login page

        Returns:
            True if authenticated, False if auth failed (response already sent)
        """
        is_authenticated, error_message = _check_authentication(self)

        if not is_authenticated:
            # For API requests, return JSON error
            if self._is_api_request():
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    'success': False,
                    'error': error_message or 'Authentication required'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
            elif redirect_to_login:
                # For browser requests, redirect to login page
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
            else:
                # Return 401 without redirect
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    'success': False,
                    'error': error_message or 'Authentication required'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
            return False

        return True

    def _check_rate_limit_and_respond(self) -> bool:
        """
        Check rate limit and send 429 response if exceeded.

        Returns:
            True if request should proceed, False if rate limited
        """
        client_ip = _get_client_ip(self)
        is_allowed, retry_after = _check_rate_limit(client_ip)

        if not is_allowed:
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Retry-After', str(retry_after))
            self.end_headers()
            response = {
                'success': False,
                'error': 'Too many requests',
                'retry_after': retry_after
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return False

        return True

    def do_GET(self):
        """Handle GET requests with authentication and rate limiting."""
        path = self.path.split('?')[0]

        # Health endpoint is public (for load balancer checks) but rate limited
        if path == '/health':
            client_ip = _get_client_ip(self)
            if not _check_health_rate_limit(client_ip):
                self.send_response(429)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Retry-After', '60')
                self.end_headers()
                self.wfile.write(b'Rate limited')
                return
            self._send_health_response()
            return

        # Favicon is always public
        if path == '/favicon.ico':
            self._send_favicon()
            return

        # Login page is public (but redirects if already authenticated)
        if path == '/login':
            if not self._check_rate_limit_and_respond():
                return
            # If already authenticated, redirect to dashboard
            is_authenticated, _ = _check_authentication(self)
            if is_authenticated:
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
                return
            self._send_login_page()
            return

        # Logout endpoint
        if path == '/logout':
            self._handle_logout()
            return

        # All other endpoints require auth check first, then rate limit
        if not self._check_auth_and_respond():
            return

        if not self._check_rate_limit_and_respond():
            return

        if path == '/' or path == '/dashboard':
            self._send_dashboard()
        elif path == '/metrics':
            self._send_metrics_response()
        elif path == '/status':
            self._send_status_response()
        elif path.startswith('/api/hosts/') and path.count('/') == 3:
            host_name = path.split('/')[3]
            self._get_host(host_name)
        elif path == '/api/hosts':
            self._list_hosts()
        elif path.startswith('/api/sheets/') and path.count('/') == 3:
            sheet_name = path.split('/')[3]
            self._get_sheet(sheet_name)
        elif path == '/api/sheets':
            self._list_sheets()
        elif path == '/api/available-tabs':
            self._list_available_tabs()
        elif path == '/api/retry-failed':
            self._retry_failed()
        elif path == '/api/admin-activity':
            self._get_admin_activity()
        elif path == '/api/logs' or path.startswith('/api/logs?'):
            self._get_logs()
        elif path == '/api/settings':
            self._get_settings()
        elif path == '/api/leads-chart' or path.startswith('/api/leads-chart?'):
            self._get_leads_chart_data()
        elif path == '/api/leads-summary' or path.startswith('/api/leads-summary?'):
            self._get_leads_summary()
        elif path == '/api/dashboard-status':
            self._get_dashboard_status()
        elif path == '/api/database-status':
            self._get_database_status()
        else:
            self._send_404_page()

    def _validate_csrf(self) -> bool:
        """
        Validate CSRF token from request header.

        Returns:
            True if valid, False otherwise
        """
        token = self.headers.get('X-CSRF-Token')
        if not token:
            # Also check in query string for form submissions
            if '?' in self.path:
                query = urllib.parse.parse_qs(self.path.split('?')[1])
                token = query.get('csrf_token', [None])[0]

        if not validate_csrf_token(token):
            self._send_json_response(403, {
                'success': False,
                'error': 'Invalid or missing CSRF token'
            })
            return False
        return True

    def _validate_origin(self) -> bool:
        """
        Validate Origin/Referer header as additional CSRF protection.

        Returns:
            True if valid or no check needed, False if suspicious
        """
        origin = self.headers.get('Origin')
        referer = self.headers.get('Referer')

        # If no origin/referer, allow (could be same-origin or direct tool access)
        if not origin and not referer:
            return True

        # Get the host from the request
        host = self.headers.get('Host', '')
        if not host:
            return True

        # Check origin matches host
        if origin:
            # Origin format: https://hostname:port or http://hostname:port
            try:
                from urllib.parse import urlparse
                parsed = urlparse(origin)
                origin_host = parsed.netloc
                if ':' in host and ':' not in origin_host:
                    # Add default port if needed
                    pass
                if origin_host and origin_host != host:
                    logger.warning(f"CSRF: Origin mismatch - expected {host}, got {origin_host}")
                    return False
            except ValueError as e:
                # Malformed URL in Origin header - log and continue (allow request)
                logger.debug(f"Could not parse Origin header for CSRF check: {e}")

        return True

    def do_POST(self):
        """Handle POST requests with authentication, rate limiting and CSRF validation."""
        path = self.path.split('?')[0]

        # Login endpoint is public (doesn't require existing auth)
        if path == '/login':
            if not self._check_rate_limit_and_respond():
                return
            self._handle_login()
            return

        # Auth check first for all other endpoints
        if not self._check_auth_and_respond():
            return

        # Rate limit check
        if not self._check_rate_limit_and_respond():
            return

        # Validate origin for all POST requests
        if not self._validate_origin():
            self._send_json_response(403, {
                'success': False,
                'error': 'Cross-origin request blocked'
            })
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response(400, {'success': False, 'error': 'Invalid JSON'})
            return

        # Validate CSRF token (check header or body)
        # Special case: skip CSRF for create-database when no database exists (bootstrap)
        skip_csrf = (path == '/api/create-database' and not storage.database_exists())
        if not skip_csrf:
            csrf_token = self.headers.get('X-CSRF-Token') or data.get('csrf_token')
            if not validate_csrf_token(csrf_token):
                self._send_json_response(403, {
                    'success': False,
                    'error': 'Invalid or missing CSRF token'
                })
                return

        if path == '/api/hosts':
            self._create_host(data)
        elif path.startswith('/api/hosts/') and path.endswith('/toggle'):
            host_name = path.split('/')[3]
            self._toggle_host(host_name, data)
        elif path == '/api/sheets':
            self._create_sheet(data)
        elif path.startswith('/api/sheets/') and path.endswith('/toggle'):
            sheet_name = path.split('/')[3]
            self._toggle_sheet(sheet_name, data)
        elif path.startswith('/api/sheets/') and path.endswith('/test-email'):
            sheet_name = path.split('/')[3]
            self._test_location_email(sheet_name)
        elif path == '/api/discover':
            self._discover_sheets(data)
        elif path == '/api/import-sheets':
            self._import_discovered_sheets(data)
        elif path == '/api/clear-error-email-tracking':
            self._clear_error_email_tracking()
        elif path == '/api/settings':
            self._update_settings(data)
        elif path == '/api/create-database':
            self._create_database()
        else:
            self._send_404_page()

    def do_PUT(self):
        """Handle PUT requests with authentication, rate limiting and CSRF validation."""
        # Auth check first
        if not self._check_auth_and_respond():
            return

        # Rate limit check
        if not self._check_rate_limit_and_respond():
            return

        path = self.path.split('?')[0]

        # Validate origin for all PUT requests
        if not self._validate_origin():
            self._send_json_response(403, {
                'success': False,
                'error': 'Cross-origin request blocked'
            })
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response(400, {'success': False, 'error': 'Invalid JSON'})
            return

        # Validate CSRF token (check header or body)
        csrf_token = self.headers.get('X-CSRF-Token') or data.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            self._send_json_response(403, {
                'success': False,
                'error': 'Invalid or missing CSRF token'
            })
            return

        if path.startswith('/api/hosts/'):
            host_name = path.split('/')[3]
            self._update_host(host_name, data)
        elif path.startswith('/api/sheets/'):
            sheet_name = path.split('/')[3]
            self._update_sheet(sheet_name, data)
        else:
            self._send_404_page()

    def do_DELETE(self):
        """Handle DELETE requests with authentication, rate limiting and CSRF validation."""
        # Auth check first
        if not self._check_auth_and_respond():
            return

        # Rate limit check
        if not self._check_rate_limit_and_respond():
            return

        path = self.path.split('?')[0]

        # Validate origin for all DELETE requests
        if not self._validate_origin():
            self._send_json_response(403, {
                'success': False,
                'error': 'Cross-origin request blocked'
            })
            return

        # CSRF token in header for DELETE
        csrf_token = self.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            self._send_json_response(403, {
                'success': False,
                'error': 'Invalid or missing CSRF token'
            })
            return

        if path.startswith('/api/hosts/'):
            host_name = path.split('/')[3]
            self._delete_host(host_name)
        elif path.startswith('/api/sheets/'):
            sheet_name = path.split('/')[3]
            self._delete_sheet(sheet_name)
        else:
            self._send_404_page()

    def _send_dashboard(self):
        """Send the HTML dashboard page."""
        html = _build_dashboard_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _send_login_page(self, error_message: str = ''):
        """Send the login page HTML."""
        html = _build_login_page(error_message=error_message)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _handle_login(self):
        """Handle login form submission."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''

        # Parse form data
        form_data = urllib.parse.parse_qs(body)
        username = form_data.get('username', [''])[0]
        password = form_data.get('password', [''])[0]
        csrf_token = form_data.get('csrf_token', [''])[0]

        # Get client IP
        client_ip = _get_client_ip(self)

        # Validate CSRF token
        if not validate_csrf_token(csrf_token):
            log_admin_activity('login_failed', 'Invalid CSRF token', ip_address=client_ip, username=username)
            self._send_login_page(error_message='Invalid request. Please try again.')
            return

        # Session fixation prevention: invalidate any existing session before creating new one
        existing_session = _get_session_cookie(self)
        if existing_session:
            _invalidate_session(existing_session)

        # Validate credentials
        if not AUTH_ENABLED:
            # No auth configured, just create session
            session_token = _create_session(username='admin', ip_address=client_ip)
            log_admin_activity('login', 'No auth required', session_token=session_token, ip_address=client_ip, username='admin')
            self._redirect_with_session('/', session_token)
            return

        # Check credentials
        username_match = hmac.compare_digest(username, DASHBOARD_USERNAME) if DASHBOARD_USERNAME else False
        password_match = hmac.compare_digest(password, DASHBOARD_PASSWORD) if DASHBOARD_PASSWORD else False

        if username_match and password_match:
            # Create fresh session and redirect to dashboard
            session_token = _create_session(username=username, ip_address=client_ip)
            log_admin_activity('login', 'Successful login', session_token=session_token, ip_address=client_ip, username=username)
            logger.info(f"User '{username}' logged in successfully from {client_ip}")
            self._redirect_with_session('/', session_token)
        else:
            log_admin_activity('login_failed', f'Invalid credentials for user: {username}', ip_address=client_ip, username=username)
            logger.warning(f"Failed login attempt for user '{username}' from {client_ip}")
            self._send_login_page(error_message='Invalid username or password.')

    def _redirect_with_session(self, location: str, session_token: str):
        """Redirect with a session cookie set."""
        self.send_response(302)
        self.send_header('Location', location)
        # Set secure cookie with HttpOnly and SameSite flags
        cookie_value = f"{SESSION_COOKIE_NAME}={session_token}; Path=/; HttpOnly; SameSite=Strict"
        self.send_header('Set-Cookie', cookie_value)
        self.end_headers()

    def _handle_logout(self):
        """Handle logout request."""
        # Invalidate the session
        session_token = _get_session_cookie(self)
        if session_token:
            log_admin_activity('logout', 'User logged out', session_token=session_token, ip_address=_get_client_ip(self))
            _invalidate_session(session_token)
            logger.info("User logged out")

        # Clear the cookie and redirect to login
        self.send_response(302)
        self.send_header('Location', '/login')
        # Set cookie to expire immediately
        cookie_value = f"{SESSION_COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"
        self.send_header('Set-Cookie', cookie_value)
        self.end_headers()

    def _send_favicon(self):
        """Send the favicon (icon.png) as ICO."""
        favicon_path = Path(__file__).parent.parent / 'icon.png'
        if favicon_path.exists():
            try:
                with open(favicon_path, 'rb') as f:
                    icon_data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(icon_data)))
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                self.wfile.write(icon_data)
            except Exception as e:
                logger.error(f"Error sending favicon: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def _send_health_response(self):
        """Send JSON health status."""
        start_time = _health_state.get('start_time')

        uptime_seconds = 0
        if start_time:
            uptime_seconds = int((utc_now() - start_time).total_seconds())

        # Check database status
        db_available = storage.database_exists()

        # Determine overall health status
        if not db_available:
            status = "degraded"
            status_reason = "Database not available"
        else:
            status = "healthy"
            status_reason = None

        health_data = {
            "status": status,
            "database_available": db_available,
            "last_successful_run": _health_state.get('last_successful_run'),
            "leads_processed_today": _health_state.get('leads_processed_today', 0),
            "uptime_seconds": uptime_seconds,
            "timestamp": utc_now().isoformat()
        }

        if status_reason:
            health_data["status_reason"] = status_reason

        # Only include DB-dependent metrics if database is available
        if db_available:
            try:
                health_data["failed_queue_size"] = storage.get_failed_queue_count()
                health_data["dead_letter_size"] = storage.get_dead_letter_count()
            except storage.DatabaseNotAvailableError:
                # Database not ready - metrics not available
                pass
            except Exception as e:
                logger.debug(f"Could not fetch queue metrics for health check: {e}")

        self._send_json_response(200, health_data)

    def _send_metrics_response(self):
        """Send Prometheus-compatible metrics."""
        start_time = _health_state.get('start_time')

        uptime_seconds = 0
        if start_time:
            uptime_seconds = int((utc_now() - start_time).total_seconds())

        metrics = []
        metrics.append("# HELP lead_monitor_up Whether the lead monitor is running")
        metrics.append("# TYPE lead_monitor_up gauge")
        metrics.append("lead_monitor_up 1")

        metrics.append("# HELP lead_monitor_uptime_seconds Time since the monitor started")
        metrics.append("# TYPE lead_monitor_uptime_seconds counter")
        metrics.append(f"lead_monitor_uptime_seconds {uptime_seconds}")

        metrics.append("# HELP lead_monitor_sent_total Total leads sent successfully")
        metrics.append("# TYPE lead_monitor_sent_total counter")
        metrics.append(f"lead_monitor_sent_total {storage.get_sent_hash_count()}")

        metrics.append("# HELP lead_monitor_failed_queue_size Current size of failed queue")
        metrics.append("# TYPE lead_monitor_failed_queue_size gauge")
        metrics.append(f"lead_monitor_failed_queue_size {storage.get_failed_queue_count()}")

        metrics.append("# HELP lead_monitor_dead_letters_size Current size of dead letters")
        metrics.append("# TYPE lead_monitor_dead_letters_size gauge")
        metrics.append(f"lead_monitor_dead_letters_size {storage.get_dead_letter_count()}")

        # Per-location metrics
        metadata = storage.get_tracker_metadata()
        location_counts = metadata.get('location_counts', {})
        if location_counts:
            metrics.append("# HELP lead_monitor_leads_by_location Leads processed by location")
            metrics.append("# TYPE lead_monitor_leads_by_location counter")
            for location, count in location_counts.items():
                safe_location = location.replace('"', '\\"')
                metrics.append(f'lead_monitor_leads_by_location{{location="{safe_location}"}} {count}')

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('\n'.join(metrics).encode('utf-8'))

    def _send_status_response(self):
        """Send detailed status information."""
        metadata = storage.get_tracker_metadata()

        status_data = {
            "momence_hosts": list(MOMENCE_HOSTS.keys()),
            "sheets_configured": len(SHEETS_CONFIG),
            "sent_entries": storage.get_sent_hash_count(),
            "failed_queue": storage.get_failed_queue_count(),
            "dead_letters": storage.get_dead_letter_count(),
            "location_counts": metadata.get('location_counts', {}),
            "last_check": metadata.get('last_check'),
            "cache_built_at": metadata.get('cache_built_at'),
            "config": {
                "dlq_enabled": DLQ_ENABLED,
                "dlq_max_retry_attempts": DLQ_MAX_RETRY_ATTEMPTS,
                "dlq_retry_backoff_hours": DLQ_RETRY_BACKOFF_HOURS,
                "rate_limit_delay": RATE_LIMIT_DELAY,
                "log_format": LOG_FORMAT
            }
        }

        self._send_json_response(200, status_data)

    def _send_json_response(self, status_code: int, data: dict):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))

    def _send_404_page(self):
        """Send a cute 404 error page."""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="icon" type="image/png" href="/favicon.ico">
            <title>404 - Page Not Found</title>
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }
                .container {
                    text-align: center;
                    color: white;
                    max-width: 500px;
                }
                .error-code {
                    font-size: 120px;
                    font-weight: 800;
                    line-height: 1;
                    text-shadow: 4px 4px 0 rgba(0,0,0,0.1);
                    margin-bottom: 10px;
                }
                .lead-icon {
                    font-size: 80px;
                    margin: 20px 0;
                    animation: bounce 2s ease-in-out infinite;
                }
                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-20px); }
                }
                h1 {
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }
                p {
                    font-size: 16px;
                    opacity: 0.9;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }
                .btn {
                    display: inline-block;
                    background: white;
                    color: #6366f1;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    transition: transform 0.2s, box-shadow 0.2s;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                }
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                }
                .breadcrumbs {
                    margin-top: 30px;
                    font-size: 12px;
                    opacity: 0.7;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-code">404</div>
                <div class="lead-icon">📋</div>
                <h1>Oops! You got lost</h1>
                <p>
                    The page you're looking for seems to have wandered off.
                    Maybe it's taking a break, or perhaps it never existed in the first place.
                </p>
                <a href="/" class="btn">Back to Dashboard</a>
                <div class="breadcrumbs">
                    Lead Monitor Dashboard • Page Not Found
                </div>
            </div>
        </body>
        </html>
        """
        self.send_response(404)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    # Host API endpoints
    def _list_hosts(self):
        """List all Momence hosts."""
        hosts = []
        for name, cfg in MOMENCE_HOSTS.items():
            hosts.append({
                'name': name,
                'host_id': cfg.get('host_id'),
                'enabled': cfg.get('enabled', True)
            })
        self._send_json_response(200, {'hosts': hosts})

    def _get_host(self, name: str):
        """Get a single Momence host."""
        name = urllib.parse.unquote(name)
        if name not in MOMENCE_HOSTS:
            self._send_json_response(404, {'success': False, 'error': 'Host not found'})
            return
        cfg = MOMENCE_HOSTS[name]
        self._send_json_response(200, {
            'name': name,
            'host_id': cfg.get('host_id'),
            'token': cfg.get('token', ''),
            'enabled': cfg.get('enabled', True)
        })

    def _create_host(self, data: dict):
        """Create a new Momence host."""
        name = data.get('name')
        if not name:
            self._send_json_response(400, {'success': False, 'error': 'Name required'})
            return

        # Check if host already exists (in database)
        if storage.get_host(name):
            self._send_json_response(400, {'success': False, 'error': 'Host already exists'})
            return

        token = data.get('token', '')

        # Store token in Secret Manager if provided and on Cloud Run
        secret_stored = False
        if token:
            try:
                from secret_manager import set_secret, IS_CLOUD_RUN
                if IS_CLOUD_RUN:
                    secret_name = f"lead-monitor-momence-api-token-{name}"
                    secret_stored = set_secret(secret_name, token)
                    if secret_stored:
                        logger.info(f"Stored API token for host '{name}' in Secret Manager")
                        token = ''  # Don't store in database if in Secret Manager
            except Exception as e:
                logger.warning(f"Failed to store token in Secret Manager: {e}")

        # Create host in database
        try:
            storage.create_host(
                name=name,
                host_id=data.get('host_id', ''),
                token=token,  # Empty if stored in Secret Manager
                enabled=data.get('enabled', True)
            )
            # Update in-memory cache
            MOMENCE_HOSTS[name] = {
                'host_id': data.get('host_id', ''),
                'token': token,
                'enabled': data.get('enabled', True)
            }
            log_admin_activity('create_host', f'Created host: {name}' + (' (token in Secret Manager)' if secret_stored else ''), session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
            self._send_json_response(200, {'success': True, 'secret_stored': secret_stored})
        except ValueError as e:
            self._send_json_response(400, {'success': False, 'error': str(e)})
        except Exception as e:
            logger.error(f"Failed to create host: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    def _update_host(self, name: str, data: dict):
        """Update an existing Momence host."""
        name = urllib.parse.unquote(name)

        # Check if host exists in database
        existing_host = storage.get_host(name)
        if not existing_host:
            self._send_json_response(404, {'success': False, 'error': 'Host not found'})
            return

        new_name = data.get('name', name)
        token = data.get('token')

        # Note: Renaming hosts is not supported with database storage
        # because host name is the primary key and referenced by sheets
        if new_name != name:
            self._send_json_response(400, {'success': False, 'error': 'Renaming hosts is not supported. Delete and recreate instead.'})
            return

        # Handle token update - store in Secret Manager if on Cloud Run
        secret_stored = False
        token_to_store = existing_host.get('token')  # Keep existing token by default
        if token:
            try:
                from secret_manager import set_secret, IS_CLOUD_RUN
                if IS_CLOUD_RUN:
                    secret_name = f"lead-monitor-momence-api-token-{name}"
                    secret_stored = set_secret(secret_name, token)
                    if secret_stored:
                        logger.info(f"Updated API token for host '{name}' in Secret Manager")
                        token_to_store = ''  # Clear from database if in Secret Manager
                    else:
                        token_to_store = token
                else:
                    token_to_store = token
            except Exception as e:
                logger.warning(f"Failed to store token in Secret Manager: {e}")
                token_to_store = token

        # Update host in database
        try:
            storage.update_host(
                name=name,
                host_id=data.get('host_id'),
                token=token_to_store if token else None,  # Only update token if provided
                enabled=data.get('enabled')
            )
            # Update in-memory cache
            if name in MOMENCE_HOSTS:
                if 'host_id' in data:
                    MOMENCE_HOSTS[name]['host_id'] = data['host_id']
                if token:
                    MOMENCE_HOSTS[name]['token'] = token_to_store
                if 'enabled' in data:
                    MOMENCE_HOSTS[name]['enabled'] = data['enabled']
            self._send_json_response(200, {'success': True, 'secret_stored': secret_stored})
        except Exception as e:
            logger.error(f"Failed to update host: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    def _toggle_host(self, name: str, data: dict):
        """Toggle Momence host enabled status."""
        name = urllib.parse.unquote(name)

        # Check if host exists in database
        if not storage.get_host(name):
            self._send_json_response(404, {'success': False, 'error': 'Host not found'})
            return

        enabled = data.get('enabled', True)

        try:
            storage.update_host(name=name, enabled=enabled)
            # Update in-memory cache
            if name in MOMENCE_HOSTS:
                MOMENCE_HOSTS[name]['enabled'] = enabled
            log_admin_activity('toggle_host', f"{'Enabled' if enabled else 'Disabled'} host: {name}", session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
            self._send_json_response(200, {'success': True})
        except Exception as e:
            logger.error(f"Failed to toggle host: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    def _delete_host(self, name: str):
        """Delete a Momence host."""
        name = urllib.parse.unquote(name)

        # Check if host exists in database
        if not storage.get_host(name):
            self._send_json_response(404, {'success': False, 'error': 'Host not found'})
            return

        # Delete the associated secret from Secret Manager
        try:
            from secret_manager import delete_secret, IS_CLOUD_RUN
            if IS_CLOUD_RUN:
                secret_name = f"lead-monitor-momence-api-token-{name}"
                delete_secret(secret_name)
                logger.info(f"Deleted secret '{secret_name}' for host '{name}'")
        except Exception as e:
            logger.warning(f"Failed to delete secret for host '{name}': {e}")

        # Delete from database
        try:
            storage.delete_host(name)
            # Update in-memory cache
            if name in MOMENCE_HOSTS:
                del MOMENCE_HOSTS[name]
            log_admin_activity('delete_host', f'Deleted host: {name}', session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
            self._send_json_response(200, {'success': True})
        except ValueError as e:
            # Host has associated locations
            self._send_json_response(400, {'success': False, 'error': str(e)})
        except Exception as e:
            logger.error(f"Failed to delete host: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    # Sheet API endpoints
    def _list_sheets(self):
        """List all sheets from database."""
        sheets = storage.get_sheets_as_config_list()
        self._send_json_response(200, {'sheets': sheets})

    def _list_available_tabs(self):
        """List FB Lead tabs from default spreadsheet that are not yet configured."""
        if not DEFAULT_SPREADSHEET_ID:
            self._send_json_response(400, {
                'success': False,
                'error': 'No default spreadsheet configured. Add default_spreadsheet_id to settings.'
            })
            return

        try:
            service = get_google_sheets_service()
            all_tabs = discover_fb_lead_tabs(service, DEFAULT_SPREADSHEET_ID)

            # Filter out tabs that are already configured (from database)
            all_sheets = storage.get_all_sheets()
            configured_gids = {sheet.get('gid') for sheet in all_sheets
                              if sheet.get('spreadsheet_id') == DEFAULT_SPREADSHEET_ID}

            available_tabs = [tab for tab in all_tabs if tab['gid'] not in configured_gids]

            self._send_json_response(200, {
                'success': True,
                'spreadsheet_id': DEFAULT_SPREADSHEET_ID,
                'tabs': available_tabs,
                'configured_count': len(configured_gids),
                'available_count': len(available_tabs)
            })

        except Exception as e:
            logger.error(f"Error listing available tabs: {e}")
            self._send_json_response(500, {'success': False, 'error': str(e)})

    def _get_sheet(self, name: str):
        """Get a single sheet by name."""
        name = urllib.parse.unquote(name)
        all_sheets = storage.get_all_sheets()
        for sheet in all_sheets:
            if sheet.get('name') == name:
                self._send_json_response(200, sheet)
                return
        self._send_json_response(404, {'success': False, 'error': 'Sheet not found'})

    def _create_sheet(self, data: dict):
        """Create a new sheet."""
        name = data.get('name')
        if not name:
            self._send_json_response(400, {'success': False, 'error': 'Name required'})
            return

        spreadsheet_id = data.get('spreadsheet_id', '')
        gid = data.get('gid', '0')
        momence_host = data.get('momence_host', '')
        lead_source_id = data.get('lead_source_id', '')

        if not spreadsheet_id:
            self._send_json_response(400, {'success': False, 'error': 'Spreadsheet ID required'})
            return
        if not momence_host:
            self._send_json_response(400, {'success': False, 'error': 'Momence host required'})
            return

        try:
            storage.create_sheet(
                spreadsheet_id=spreadsheet_id,
                gid=gid,
                name=name,
                momence_host=momence_host,
                lead_source_id=lead_source_id,
                enabled=data.get('enabled', True),
                notification_email=data.get('notification_email')
            )
            # Update in-memory cache
            SHEETS_CONFIG.append({
                'name': name,
                'momence_host': momence_host,
                'spreadsheet_id': spreadsheet_id,
                'gid': gid,
                'lead_source_id': lead_source_id,
                'enabled': data.get('enabled', True),
                'notification_email': data.get('notification_email')
            })
            log_admin_activity('create_location', f"Created location: {name} (momence_host: {momence_host})", session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
            self._send_json_response(200, {'success': True})
        except ValueError as e:
            self._send_json_response(400, {'success': False, 'error': str(e)})
        except Exception as e:
            logger.error(f"Failed to create sheet: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    def _update_sheet(self, name: str, data: dict):
        """Update an existing sheet."""
        name = urllib.parse.unquote(name)

        # Find sheet by name in database
        all_sheets = storage.get_all_sheets()
        sheet_to_update = None
        for sheet in all_sheets:
            if sheet.get('name') == name:
                sheet_to_update = sheet
                break

        if not sheet_to_update:
            self._send_json_response(404, {'success': False, 'error': 'Sheet not found'})
            return

        try:
            # Handle notification_email: empty string means removal
            notification_email = data.get('notification_email')
            if notification_email == '':
                notification_email = None

            storage.update_sheet(
                sheet_id=sheet_to_update['id'],
                spreadsheet_id=data.get('spreadsheet_id'),
                gid=data.get('gid'),
                name=data.get('name'),
                momence_host=data.get('momence_host'),
                lead_source_id=data.get('lead_source_id'),
                enabled=data.get('enabled'),
                notification_email=notification_email
            )
            # Update in-memory cache
            for i, sheet in enumerate(SHEETS_CONFIG):
                if sheet.get('name') == name:
                    if 'name' in data:
                        SHEETS_CONFIG[i]['name'] = data['name']
                    if 'momence_host' in data:
                        SHEETS_CONFIG[i]['momence_host'] = data['momence_host']
                    if 'spreadsheet_id' in data:
                        SHEETS_CONFIG[i]['spreadsheet_id'] = data['spreadsheet_id']
                    if 'gid' in data:
                        SHEETS_CONFIG[i]['gid'] = data['gid']
                    if 'lead_source_id' in data:
                        SHEETS_CONFIG[i]['lead_source_id'] = data['lead_source_id']
                    if 'enabled' in data:
                        SHEETS_CONFIG[i]['enabled'] = data['enabled']
                    if notification_email is not None:
                        SHEETS_CONFIG[i]['notification_email'] = notification_email
                    elif 'notification_email' in data and data['notification_email'] == '':
                        SHEETS_CONFIG[i].pop('notification_email', None)
                    break
            self._send_json_response(200, {'success': True})
        except ValueError as e:
            self._send_json_response(400, {'success': False, 'error': str(e)})
        except Exception as e:
            logger.error(f"Failed to update sheet: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    def _toggle_sheet(self, name: str, data: dict):
        """Toggle sheet enabled status."""
        name = urllib.parse.unquote(name)

        # Find sheet by name in database
        all_sheets = storage.get_all_sheets()
        sheet_to_toggle = None
        for sheet in all_sheets:
            if sheet.get('name') == name:
                sheet_to_toggle = sheet
                break

        if not sheet_to_toggle:
            self._send_json_response(404, {'success': False, 'error': 'Sheet not found'})
            return

        enabled = data.get('enabled', True)

        try:
            storage.update_sheet(sheet_id=sheet_to_toggle['id'], enabled=enabled)
            # Update in-memory cache
            for sheet in SHEETS_CONFIG:
                if sheet.get('name') == name:
                    sheet['enabled'] = enabled
                    break
            log_admin_activity('toggle_location', f"{'Enabled' if enabled else 'Disabled'} location: {name}", session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
            self._send_json_response(200, {'success': True})
        except Exception as e:
            logger.error(f"Failed to toggle sheet: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    def _test_location_email(self, name: str):
        """Send a test email for a location to verify email configuration."""
        name = urllib.parse.unquote(name)

        # Verify sheet exists in database
        all_sheets = storage.get_all_sheets()
        sheet_found = any(sheet.get('name') == name for sheet in all_sheets)

        if not sheet_found:
            self._send_json_response(404, {'success': False, 'error': 'Location not found'})
            return

        # Send test email
        result = send_test_location_email(name)
        log_admin_activity(
            'test_email',
            f"Test email for location '{name}': {'success' if result.get('success') else result.get('error', 'failed')}",
            session_token=_get_session_cookie(self),
            ip_address=_get_client_ip(self)
        )

        if result.get('success'):
            self._send_json_response(200, result)
        else:
            self._send_json_response(400, result)

    def _delete_sheet(self, name: str):
        """Delete a sheet."""
        name = urllib.parse.unquote(name)

        # Find sheet by name in database
        all_sheets = storage.get_all_sheets()
        sheet_to_delete = None
        for sheet in all_sheets:
            if sheet.get('name') == name:
                sheet_to_delete = sheet
                break

        if not sheet_to_delete:
            self._send_json_response(404, {'success': False, 'error': 'Sheet not found'})
            return

        try:
            storage.delete_sheet(sheet_to_delete['id'])
            # Update in-memory cache
            for i, sheet in enumerate(SHEETS_CONFIG):
                if sheet.get('name') == name:
                    SHEETS_CONFIG.pop(i)
                    break
            log_admin_activity('delete_location', f'Deleted location: {name}', session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
            self._send_json_response(200, {'success': True})
        except Exception as e:
            logger.error(f"Failed to delete sheet: {e}")
            self._send_json_response(500, {'success': False, 'error': 'Database error'})

    def _get_settings(self):
        """Get application settings."""
        settings = _config.get('settings', {})
        # Ensure defaults are populated for UI
        response = {
            'dlq_enabled': settings.get('dlq_enabled', True),
            'dlq_max_retry_attempts': settings.get('dlq_max_retry_attempts', 5),
            'dlq_retry_backoff_hours': settings.get('dlq_retry_backoff_hours', [1, 2, 4, 8, 24]),
            'rate_limit_delay_seconds': settings.get('rate_limit_delay_seconds', 3.0),
            'default_spreadsheet_id': settings.get('default_spreadsheet_id', ''),
            'log_retention_days': settings.get('log_retention_days', 7),
            'log_format': settings.get('log_format', 'text'),
            'log_level': settings.get('log_level', 'INFO'),
        }
        self._send_json_response(200, response)

    def _update_settings(self, data: dict):
        """Update application settings."""
        current_settings = _config.get('settings', {})

        # Boolean fields
        if 'dlq_enabled' in data:
            current_settings['dlq_enabled'] = bool(data['dlq_enabled'])

        # Integer fields
        try:
            if 'dlq_max_retry_attempts' in data:
                current_settings['dlq_max_retry_attempts'] = int(data['dlq_max_retry_attempts'])
            if 'log_retention_days' in data:
                current_settings['log_retention_days'] = int(data['log_retention_days'])
        except ValueError:
             self._send_json_response(400, {'success': False, 'error': 'Invalid integer value'})
             return

        # Float fields
        try:
            if 'rate_limit_delay_seconds' in data:
                current_settings['rate_limit_delay_seconds'] = float(data['rate_limit_delay_seconds'])
        except ValueError:
             self._send_json_response(400, {'success': False, 'error': 'Invalid number value'})
             return

        # String fields
        if 'default_spreadsheet_id' in data:
            current_settings['default_spreadsheet_id'] = str(data['default_spreadsheet_id']).strip()
        if 'log_format' in data:
            current_settings['log_format'] = str(data['log_format'])
        if 'log_level' in data:
            current_settings['log_level'] = str(data['log_level'])

        # Update config
        _config['settings'] = current_settings
        _save_config()
        _reload_config()

        log_admin_activity('update_settings', 'Updated application settings', session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
        self._send_json_response(200, {'success': True})

    def _retry_failed(self):
        """Retry all failed queue entries with SSE progress streaming."""
        # Get entries directly from storage
        entries = storage.get_failed_queue_entries()

        if not entries:
            self._send_json_response(200, {'success': True, 'successful': 0, 'failed': 0, 'message': 'No entries to retry'})
            return

        # Set up SSE response
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        def send_event(event_type: str, data: dict):
            """Send an SSE event."""
            event_data = json.dumps({**data, 'type': event_type})
            self.wfile.write(f"data: {event_data}\n\n".encode('utf-8'))
            self.wfile.flush()

        total = len(entries)
        send_event('start', {'total': total})

        successful = 0
        failed = 0
        entries_to_remove = []

        for i, entry in enumerate(entries):
            lead_data = entry.get('lead_data', {})
            momence_host = entry.get('momence_host')
            entry_hash = entry.get('entry_hash')
            email = lead_data.get('email', 'unknown')

            send_event('progress', {
                'current': i + 1,
                'total': total,
                'email': email,
                'status': 'retrying'
            })

            # Check if max retries exceeded
            if entry.get('attempts', 0) >= DLQ_MAX_RETRY_ATTEMPTS:
                storage.move_to_dead_letters(entry_hash)
                send_event('result', {'email': email, 'success': False, 'reason': 'max_attempts_exceeded'})
                failed += 1
                continue

            # Add delay between retries
            if i > 0:
                time.sleep(RATE_LIMIT_DELAY)

            result = create_momence_lead(lead_data, momence_host, dry_run=False)

            if result.get('success'):
                successful += 1
                entries_to_remove.append(entry_hash)

                # Mark as sent in storage
                storage.add_sent_hash(entry_hash, lead_data.get('sheetName'))
                storage.increment_location_count(lead_data.get('sheetName', momence_host))

                send_event('result', {'email': email, 'success': True})
            else:
                failed += 1
                error_info = result.get('error', {})

                # Update the entry in storage with new attempt info
                new_attempts = storage.update_failed_entry_attempt(entry_hash, error_info)

                # Check if we should move to dead letters
                if new_attempts and new_attempts >= DLQ_MAX_RETRY_ATTEMPTS:
                    storage.move_to_dead_letters(entry_hash)

                send_event('result', {
                    'email': email,
                    'success': False,
                    'reason': error_info.get('type', 'unknown'),
                    'message': error_info.get('message', '')
                })

        # Remove successful entries from failed queue
        if entries_to_remove:
            storage.remove_from_failed_queue_batch(entries_to_remove)

        send_event('complete', {'successful': successful, 'failed': failed})

    def _clear_error_email_tracking(self):
        """Clear the daily error email tracking, allowing the next error email to be sent immediately."""
        metadata = storage.get_tracker_metadata()
        old_value = metadata.get('last_error_email_sent')

        storage.update_tracker_metadata(last_error_email_sent=None)

        log_admin_activity('clear_error_tracking', f'Reset error email tracking (was: {old_value})', session_token=_get_session_cookie(self), ip_address=_get_client_ip(self))
        logger.info(f"Error email tracking cleared (was: {old_value})")
        self._send_json_response(200, {
            'success': True,
            'message': 'Error email tracking cleared. Next error will trigger an email.',
            'previous_value': old_value
        })

    def _get_database_status(self):
        """Get the current database status."""
        try:
            db_exists = storage.database_exists()
            db_available = storage.is_database_available()

            status = {
                'exists': db_exists,
                'available': db_available,
                'path': storage.get_db_path()
            }

            if db_exists:
                try:
                    status['sent_hash_count'] = storage.get_sent_hash_count()
                    status['failed_queue_count'] = storage.get_failed_queue_count()
                    metadata = storage.get_tracker_metadata()
                    status['last_check'] = metadata.get('last_check')
                    status['cache_built_at'] = metadata.get('cache_built_at')
                except Exception as e:
                    status['error'] = str(e)

            self._send_json_response(200, {
                'success': True,
                'database': status
            })
        except Exception as e:
            self._send_json_response(500, {
                'success': False,
                'error': str(e)
            })

    def _create_database(self):
        """Create a fresh database, deleting any existing one."""
        try:
            # Check if database already exists
            db_existed = storage.database_exists()

            # Create fresh database
            result = storage.create_fresh_database()

            if result:
                action = 'recreate_database' if db_existed else 'create_database'
                log_admin_activity(
                    action,
                    f'{"Recreated" if db_existed else "Created"} fresh database',
                    session_token=_get_session_cookie(self),
                    ip_address=_get_client_ip(self)
                )
                logger.info(f"Database {'recreated' if db_existed else 'created'} via dashboard")
                self._send_json_response(200, {
                    'success': True,
                    'message': f'Database {"recreated" if db_existed else "created"} successfully.',
                    'previous_existed': db_existed
                })
            else:
                self._send_json_response(500, {
                    'success': False,
                    'error': 'Failed to create database'
                })
        except Exception as e:
            logger.exception(f"Error creating database: {e}")
            self._send_json_response(500, {
                'success': False,
                'error': str(e)
            })

    def _get_admin_activity(self):
        """Get recent admin activity log entries."""
        # Parse limit from query string
        limit = 50
        if '?' in self.path:
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            try:
                limit = int(query.get('limit', ['50'])[0])
                limit = min(max(limit, 1), 500)  # Clamp between 1 and 500
            except (ValueError, TypeError):
                pass

        entries = get_admin_activity_log(limit)
        self._send_json_response(200, {
            'success': True,
            'entries': entries,
            'count': len(entries)
        })

    def _get_logs(self):
        """Get recent application log lines."""
        from pathlib import Path
        from config import LOG_DIR

        # Parse lines from query string (default 50)
        lines = 50
        if '?' in self.path:
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            try:
                lines = int(query.get('lines', ['50'])[0])
                lines = min(max(lines, 10), 200)  # Clamp between 10 and 200
            except (ValueError, TypeError):
                pass

        try:
            log_dir = Path(LOG_DIR)
            # Find today's log file (format: YYYYMMDD.log)
            from utils import utc_now
            today = utc_now().strftime('%Y%m%d')
            log_file = log_dir / f'{today}.log'

            log_lines = []
            target_file = None

            if log_file.exists():
                target_file = log_file
            else:
                # Try to find most recent log file
                log_files = sorted(log_dir.glob('*.log'), reverse=True)
                if log_files:
                    target_file = log_files[0]

            if target_file:
                # Efficient tail: read from end of file to avoid loading entire file
                log_lines = self._efficient_tail(target_file, lines)
            else:
                log_lines = ['No log files found']

            self._send_json_response(200, {
                'success': True,
                'logs': log_lines,
                'count': len(log_lines)
            })
        except Exception as e:
            self._send_json_response(200, {
                'success': True,
                'logs': [f'Error reading logs: {str(e)}'],
                'count': 1
            })

    def _efficient_tail(self, file_path: Path, n_lines: int) -> List[str]:
        """
        Efficiently read the last N lines of a file without loading entire file.

        Uses a chunked read from the end of the file to minimize memory usage.
        """
        try:
            with open(file_path, 'rb') as f:
                # For small files (< 64KB), just read the whole thing
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()

                if file_size == 0:
                    return []

                # For small files, read all at once (more efficient than chunked)
                if file_size < 65536:
                    f.seek(0)
                    content = f.read().decode('utf-8', errors='replace')
                    all_lines = content.splitlines()
                    return all_lines[-n_lines:]

                # For larger files, read chunks from the end
                chunk_size = max(8192, n_lines * 200)  # Assume ~200 bytes per line
                lines_found = []
                remaining_size = file_size

                while len(lines_found) < n_lines + 1 and remaining_size > 0:
                    # Calculate chunk position
                    chunk_start = max(0, remaining_size - chunk_size)
                    bytes_to_read = remaining_size - chunk_start

                    f.seek(chunk_start)
                    chunk = f.read(bytes_to_read).decode('utf-8', errors='replace')

                    # Split into lines and prepend to our list
                    chunk_lines = chunk.splitlines()

                    if lines_found:
                        # Merge partial line from previous chunk
                        chunk_lines[-1] += lines_found[0]
                        lines_found = chunk_lines + lines_found[1:]
                    else:
                        lines_found = chunk_lines

                    remaining_size = chunk_start

                    # Increase chunk size for next iteration if needed
                    chunk_size = min(chunk_size * 2, 1048576)  # Max 1MB chunks

                return lines_found[-n_lines:]

        except Exception as e:
            return [f'Error reading file: {str(e)}']

    def _get_leads_chart_data(self):
        """Get leads by location data for charting."""
        # Parse days from query string (default "24h" for hourly)
        days = 7
        hourly = False
        if '?' in self.path:
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            days_param = query.get('days', ['24h'])[0]
            if days_param == '24h':
                hourly = True
            else:
                try:
                    days = int(days_param)
                    days = min(max(days, 1), 365)  # Clamp between 1 and 365
                except (ValueError, TypeError):
                    pass

        chart_data = storage.get_leads_chart_data(days, hourly=hourly)
        self._send_json_response(200, {
            'success': True,
            'data': chart_data,
            'days': days,
            'hourly': hourly
        })

    def _get_leads_summary(self):
        """Get leads summary statistics."""
        # Parse days from query string (default 30)
        days = 30
        if '?' in self.path:
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            try:
                days = int(query.get('days', ['30'])[0])
                days = min(max(days, 1), 365)  # Clamp between 1 and 365
            except (ValueError, TypeError):
                pass

        summary = storage.get_leads_summary_stats(days)
        self._send_json_response(200, {
            'success': True,
            'data': summary
        })

    def _get_dashboard_status(self):
        """Get current dashboard status for header updates."""
        from utils import utc_now

        # Use _health_state which has the actual last_successful_run (not stale DB value)
        last_check = _health_state.get('last_successful_run', 'Never')
        start_time = _health_state.get('tracker', {}).get('start_time')

        # Calculate uptime
        uptime_str = 'N/A'
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                delta = utc_now() - start_dt
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                uptime_str = f'{hours}h {minutes}m'
            except (ValueError, TypeError):
                pass

        self._send_json_response(200, {
            'success': True,
            'last_check': str(last_check) if last_check else 'Never',
            'uptime': uptime_str
        })

    def _discover_sheets(self, data: dict):
        """Discover FB Lead tabs in a spreadsheet."""
        url = data.get('url', '').strip()
        if not url:
            self._send_json_response(400, {'success': False, 'error': 'Spreadsheet URL required'})
            return

        # Parse the URL
        parsed = parse_spreadsheet_url(url)
        if not parsed:
            self._send_json_response(400, {'success': False, 'error': 'Invalid Google Sheets URL'})
            return

        spreadsheet_id, _ = parsed

        try:
            service = get_google_sheets_service()
            tabs = discover_fb_lead_tabs(service, spreadsheet_id)

            if not tabs:
                self._send_json_response(200, {
                    'success': True,
                    'spreadsheet_id': spreadsheet_id,
                    'tabs': [],
                    'message': 'No tabs found with Facebook Lead headers (id, created_time, ad_id, ad_name)'
                })
                return

            self._send_json_response(200, {
                'success': True,
                'spreadsheet_id': spreadsheet_id,
                'tabs': tabs
            })

        except Exception as e:
            logger.error(f"Error discovering sheets: {e}")
            self._send_json_response(500, {'success': False, 'error': str(e)})

    def _import_discovered_sheets(self, data: dict):
        """Import discovered tabs as sheets."""
        spreadsheet_id = data.get('spreadsheet_id', '').strip()
        momence_host = data.get('momence_host', '').strip()
        tabs = data.get('tabs', [])

        if not spreadsheet_id:
            self._send_json_response(400, {'success': False, 'error': 'Spreadsheet ID required'})
            return

        if not momence_host:
            self._send_json_response(400, {'success': False, 'error': 'Momence host required'})
            return

        if momence_host not in MOMENCE_HOSTS:
            self._send_json_response(400, {'success': False, 'error': f'Host "{momence_host}" does not exist. Create it first.'})
            return

        if not tabs:
            self._send_json_response(400, {'success': False, 'error': 'No tabs selected'})
            return

        imported = []
        skipped = []

        for tab in tabs:
            tab_name = tab.get('name', '')
            tab_gid = tab.get('gid', '0')
            lead_source_id = tab.get('lead_source_id')
            notification_email = tab.get('notification_email')

            # Check if sheet already exists
            exists = False
            for sheet in SHEETS_CONFIG:
                if sheet.get('spreadsheet_id') == spreadsheet_id and sheet.get('gid') == tab_gid:
                    exists = True
                    skipped.append(tab_name)
                    break

            if not exists:
                new_sheet = {
                    'spreadsheet_id': spreadsheet_id,
                    'gid': tab_gid,
                    'name': tab_name,
                    'momence_host': momence_host,
                    'enabled': True
                }
                if lead_source_id:
                    new_sheet['lead_source_id'] = lead_source_id
                if notification_email:
                    new_sheet['notification_email'] = notification_email

                SHEETS_CONFIG.append(new_sheet)
                imported.append(tab_name)

        if imported:
            _save_config()

        self._send_json_response(200, {
            'success': True,
            'imported': imported,
            'skipped': skipped
        })


def start_health_server(tracker: dict) -> Optional[ThreadingHTTPServer]:
    """
    Start the health check HTTP server in a background thread.

    Args:
        tracker: The tracker dict to expose via health endpoints

    Returns:
        ThreadingHTTPServer instance if started, None if disabled
    """
    if not HEALTH_SERVER_ENABLED:
        logger.debug("Health server disabled in config")
        return None

    # Reload config from database now that it's been initialized
    # This ensures MOMENCE_HOSTS and SHEETS_CONFIG are populated from DB
    _reload_config()
    logger.info(f"After reload: {len(MOMENCE_HOSTS)} hosts, {len(SHEETS_CONFIG)} sheets")

    with _health_state_lock:
        _health_state['tracker'] = tracker
        _health_state['start_time'] = utc_now()

    # Log authentication status
    if AUTH_ENABLED:
        auth_methods = []
        if DASHBOARD_API_KEY:
            auth_methods.append("API Key")
        if DASHBOARD_USERNAME and DASHBOARD_PASSWORD:
            auth_methods.append("Basic Auth")
        logger.info(f"Dashboard authentication enabled: {', '.join(auth_methods)}")
    else:
        logger.warning("Dashboard authentication is DISABLED - dashboard is publicly accessible!")

    try:
        server = ThreadingHTTPServer(('0.0.0.0', HEALTH_SERVER_PORT), DashboardHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Health server started on port {HEALTH_SERVER_PORT}")
        return server
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        return None


def update_health_state(tracker: dict, success: bool = True):
    """Update health state after a monitor run (thread-safe)."""
    with _health_state_lock:
        _health_state['tracker'] = tracker
        if success:
            _health_state['last_successful_run'] = utc_now().isoformat()


def get_health_state() -> Dict[str, Any]:
    """Get a copy of health state (thread-safe)."""
    with _health_state_lock:
        return dict(_health_state)
