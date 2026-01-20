"""
SQLite storage backend for Lead Sheets Monitor.

Provides atomic, corruption-resistant storage for:
- Sent entry hashes (deduplication)
- Failed queue entries (retry with backoff)
- Dead letters (failed after max retries)
- Tracker metadata (last check, location counts, etc.)

Replaces the JSON file-based storage with proper database operations.
"""

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from utils import utc_now, logger

# Import database path from config
from config import DATABASE_FILE

# Thread-local storage for database connections
_local = threading.local()

# Database connection retry settings
DB_CONNECT_MAX_RETRIES = 3
DB_CONNECT_RETRY_DELAY = 1.0  # seconds


def get_db_path() -> str:
    """Get the database file path."""
    return DATABASE_FILE


def _get_connection() -> sqlite3.Connection:
    """
    Get a thread-local database connection with retry logic.

    Uses WAL mode for better concurrent access and corruption resistance.
    Retries connection on failure to handle transient filesystem issues.
    """
    if not hasattr(_local, 'connection') or _local.connection is None:
        db_path = get_db_path()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        last_error = None
        for attempt in range(DB_CONNECT_MAX_RETRIES):
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row  # Allow dict-like access to rows

                # Enable WAL mode for better concurrency and crash recovery
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')  # Good balance of safety and speed
                conn.execute('PRAGMA foreign_keys=ON')

                _local.connection = conn
                logger.debug(f"Opened database connection to {db_path}")
                return _local.connection

            except sqlite3.Error as e:
                last_error = e
                if attempt < DB_CONNECT_MAX_RETRIES - 1:
                    logger.warning(
                        f"Database connection attempt {attempt + 1}/{DB_CONNECT_MAX_RETRIES} failed: {e}. "
                        f"Retrying in {DB_CONNECT_RETRY_DELAY}s..."
                    )
                    time.sleep(DB_CONNECT_RETRY_DELAY)
                else:
                    logger.error(f"Failed to connect to database after {DB_CONNECT_MAX_RETRIES} attempts: {e}")
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error

    return _local.connection


def close_connection():
    """Close the thread-local database connection."""
    if hasattr(_local, 'connection') and _local.connection is not None:
        try:
            _local.connection.close()
        except sqlite3.Error as e:
            logger.warning(f"Error closing database connection: {e}")
        finally:
            _local.connection = None
            logger.debug("Closed database connection")


@contextmanager
def get_db():
    """Context manager for database operations with automatic commit/rollback."""
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_database():
    """
    Initialize the database schema.

    Creates tables if they don't exist. Safe to call multiple times.
    """
    with get_db() as conn:
        # Sent hashes table - tracks processed entries
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sent_hashes (
                hash TEXT PRIMARY KEY,
                location TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sent_hashes_created ON sent_hashes(created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sent_hashes_location ON sent_hashes(location)')

        # Failed queue table - entries pending retry
        conn.execute('''
            CREATE TABLE IF NOT EXISTS failed_queue (
                entry_hash TEXT PRIMARY KEY,
                lead_data TEXT NOT NULL,
                tenant TEXT NOT NULL,
                attempts INTEGER DEFAULT 1,
                last_error TEXT,
                last_error_message TEXT,
                last_error_details TEXT,
                error_history TEXT,
                first_failed_at TEXT NOT NULL,
                last_attempted_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_failed_queue_tenant ON failed_queue(tenant)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_failed_queue_attempts ON failed_queue(attempts)')

        # Dead letters table - entries that exceeded max retries
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dead_letters (
                entry_hash TEXT PRIMARY KEY,
                lead_data TEXT NOT NULL,
                tenant TEXT NOT NULL,
                attempts INTEGER,
                last_error TEXT,
                last_error_message TEXT,
                last_error_details TEXT,
                error_history TEXT,
                first_failed_at TEXT,
                last_attempted_at TEXT,
                moved_to_dead_letters_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_dead_letters_moved_at ON dead_letters(moved_to_dead_letters_at)')

        # Tracker metadata table - single row for global state
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tracker_metadata (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_check TEXT,
                cache_built_at TEXT,
                last_error_email_sent TEXT,
                location_counts TEXT
            )
        ''')

        # Initialize metadata row if not exists
        conn.execute('''
            INSERT OR IGNORE INTO tracker_metadata (id, cache_built_at, location_counts)
            VALUES (1, ?, '{}')
        ''', (utc_now().isoformat(),))

        # Admin activity log table - replaces JSON file
        conn.execute('''
            CREATE TABLE IF NOT EXISTS admin_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                username TEXT,
                ip_address TEXT,
                session_id TEXT,
                user_agent TEXT,
                metadata TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_activity_timestamp ON admin_activity(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_admin_activity_action ON admin_activity(action)')

        # Daily leads metrics table - for historical tracking and charts
        # Uses lead_date (from spreadsheet) not the processing date
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads_daily_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_date TEXT NOT NULL,
                location TEXT NOT NULL,
                tenant TEXT NOT NULL,
                leads_sent INTEGER DEFAULT 0,
                leads_failed INTEGER DEFAULT 0,
                UNIQUE(lead_date, location)
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_leads_daily_date ON leads_daily_metrics(lead_date)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_leads_daily_location ON leads_daily_metrics(location)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_leads_daily_tenant ON leads_daily_metrics(tenant)')

        # Web sessions table - for persistent session storage across restarts
        conn.execute('''
            CREATE TABLE IF NOT EXISTS web_sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                last_accessed_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_web_sessions_expires ON web_sessions(expires_at)')

        # CSRF tokens table - for persistent CSRF protection across restarts
        conn.execute('''
            CREATE TABLE IF NOT EXISTS csrf_tokens (
                token TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_csrf_tokens_expires ON csrf_tokens(expires_at)')

        logger.info("Database initialized successfully")


# ============================================================================
# Sent Hashes Operations
# ============================================================================

def hash_exists(hash_value: str) -> bool:
    """Check if a hash exists in the sent_hashes table."""
    with get_db() as conn:
        result = conn.execute(
            'SELECT 1 FROM sent_hashes WHERE hash = ?',
            (hash_value,)
        ).fetchone()
        return result is not None


def add_sent_hash(hash_value: str, location: str = None):
    """Add a hash to the sent_hashes table."""
    with get_db() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO sent_hashes (hash, location, created_at) VALUES (?, ?, ?)',
            (hash_value, location, utc_now().isoformat())
        )


def add_sent_hashes_batch(hashes: List[tuple]):
    """
    Add multiple hashes in a single transaction.

    Args:
        hashes: List of (hash, location) tuples
    """
    with get_db() as conn:
        now = utc_now().isoformat()
        conn.executemany(
            'INSERT OR IGNORE INTO sent_hashes (hash, location, created_at) VALUES (?, ?, ?)',
            [(h, loc, now) for h, loc in hashes]
        )


def get_all_sent_hashes() -> Set[str]:
    """
    Get all sent hashes as a set.

    WARNING: This loads all hashes into memory. For large datasets (>100k entries),
    consider using hash_exists() for individual checks or iter_sent_hashes() for
    streaming access.

    Returns:
        Set of all hash strings
    """
    count = get_sent_hash_count()
    if count > 100000:
        logger.warning(
            f"Loading {count} hashes into memory. Consider using hash_exists() "
            "for individual checks or iter_sent_hashes() for streaming."
        )

    with get_db() as conn:
        rows = conn.execute('SELECT hash FROM sent_hashes').fetchall()
        return {row['hash'] for row in rows}


def iter_sent_hashes(batch_size: int = 10000):
    """
    Iterate over sent hashes in batches to avoid memory issues.

    This is a generator that yields hashes one at a time while fetching
    from the database in batches.

    Args:
        batch_size: Number of hashes to fetch per database query

    Yields:
        Hash strings one at a time
    """
    offset = 0
    while True:
        with get_db() as conn:
            rows = conn.execute(
                'SELECT hash FROM sent_hashes ORDER BY rowid LIMIT ? OFFSET ?',
                (batch_size, offset)
            ).fetchall()

            if not rows:
                break

            for row in rows:
                yield row['hash']

            offset += batch_size


def get_sent_hashes_batch(offset: int = 0, limit: int = 10000) -> List[str]:
    """
    Get a batch of sent hashes with pagination.

    Args:
        offset: Starting position
        limit: Maximum number of hashes to return

    Returns:
        List of hash strings
    """
    with get_db() as conn:
        rows = conn.execute(
            'SELECT hash FROM sent_hashes ORDER BY rowid LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()
        return [row['hash'] for row in rows]


def get_sent_hash_count() -> int:
    """Get the count of sent hashes."""
    with get_db() as conn:
        result = conn.execute('SELECT COUNT(*) FROM sent_hashes').fetchone()
        return result[0]


def cleanup_old_hashes(days: int = 90) -> int:
    """
    Remove hashes older than specified days.

    Args:
        days: Number of days to keep hashes

    Returns:
        Number of hashes deleted
    """
    cutoff = (utc_now() - timedelta(days=days)).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM sent_hashes WHERE created_at < ?',
            (cutoff,)
        )
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old hashes (older than {days} days)")
        return deleted


# ============================================================================
# Tracker Metadata Operations
# ============================================================================

def get_tracker_metadata() -> Dict[str, Any]:
    """Get tracker metadata."""
    with get_db() as conn:
        row = conn.execute(
            'SELECT last_check, cache_built_at, last_error_email_sent, location_counts FROM tracker_metadata WHERE id = 1'
        ).fetchone()

        if row:
            return {
                'last_check': row['last_check'],
                'cache_built_at': row['cache_built_at'],
                'last_error_email_sent': row['last_error_email_sent'],
                'location_counts': json.loads(row['location_counts'] or '{}')
            }
        return {
            'last_check': None,
            'cache_built_at': utc_now().isoformat(),
            'last_error_email_sent': None,
            'location_counts': {}
        }


def update_tracker_metadata(
    last_check: str = None,
    last_error_email_sent: str = None,
    location_counts: Dict[str, int] = None
):
    """Update tracker metadata fields."""
    with get_db() as conn:
        updates = []
        params = []

        if last_check is not None:
            updates.append('last_check = ?')
            params.append(last_check)

        if last_error_email_sent is not None:
            updates.append('last_error_email_sent = ?')
            params.append(last_error_email_sent)

        if location_counts is not None:
            updates.append('location_counts = ?')
            params.append(json.dumps(location_counts))

        if updates:
            conn.execute(
                f'UPDATE tracker_metadata SET {", ".join(updates)} WHERE id = 1',
                params
            )


def increment_location_count(location: str, increment: int = 1):
    """
    Increment the count for a specific location atomically.

    Uses SQLite's json_set function for atomic read-modify-write to prevent
    race conditions when multiple threads increment simultaneously.
    """
    with get_db() as conn:
        # First, try atomic update using json_set (SQLite 3.38+)
        # This handles the case where the key already exists
        cursor = conn.execute('''
            UPDATE tracker_metadata
            SET location_counts = json_set(
                COALESCE(location_counts, '{}'),
                '$.' || ?,
                COALESCE(
                    json_extract(location_counts, '$.' || ?),
                    0
                ) + ?
            )
            WHERE id = 1
        ''', (location, location, increment))

        # If json_set is not available (older SQLite), fall back to serialized update
        if cursor.rowcount == 0:
            # Ensure row exists
            conn.execute('''
                INSERT OR IGNORE INTO tracker_metadata (id, cache_built_at, location_counts)
                VALUES (1, ?, '{}')
            ''', (utc_now().isoformat(),))

            # Use a transaction with IMMEDIATE to serialize access
            row = conn.execute(
                'SELECT location_counts FROM tracker_metadata WHERE id = 1'
            ).fetchone()

            counts = json.loads(row['location_counts'] or '{}') if row else {}
            counts[location] = counts.get(location, 0) + increment

            conn.execute(
                'UPDATE tracker_metadata SET location_counts = ? WHERE id = 1',
                (json.dumps(counts),)
            )


# ============================================================================
# Failed Queue Operations
# ============================================================================

def add_to_failed_queue(
    entry_hash: str,
    lead_data: Dict[str, Any],
    tenant: str,
    error_info: Dict[str, Any]
):
    """
    Add or update an entry in the failed queue.

    If the entry already exists, increments attempt count and updates error info.
    """
    now = utc_now().isoformat()

    error_details = {
        'type': error_info.get('type', 'unknown'),
        'message': error_info.get('message', ''),
        'status_code': error_info.get('status_code'),
        'cf_ray': error_info.get('cf_ray'),
        'response_body': error_info.get('response_body', ''),
        'response_headers': error_info.get('response_headers', {}),
        'request_url': error_info.get('request_url'),
        'request_payload': error_info.get('request_payload'),
        'request_timestamp': error_info.get('request_timestamp'),
        'request_duration_ms': error_info.get('request_duration_ms'),
        'recorded_at': now
    }

    with get_db() as conn:
        # Check if entry exists
        existing = conn.execute(
            'SELECT attempts, error_history FROM failed_queue WHERE entry_hash = ?',
            (entry_hash,)
        ).fetchone()

        if existing:
            # Update existing entry
            attempts = existing['attempts'] + 1
            error_history = json.loads(existing['error_history'] or '[]')
            error_history.append(error_details)
            error_history = error_history[-5:]  # Keep last 5 errors

            conn.execute('''
                UPDATE failed_queue SET
                    attempts = ?,
                    last_error = ?,
                    last_error_message = ?,
                    last_error_details = ?,
                    error_history = ?,
                    last_attempted_at = ?
                WHERE entry_hash = ?
            ''', (
                attempts,
                error_info.get('type', 'unknown'),
                error_info.get('message', ''),
                json.dumps(error_details),
                json.dumps(error_history),
                now,
                entry_hash
            ))
            logger.info(f"Updated failed queue entry for {lead_data.get('email')} (attempt {attempts})")
        else:
            # Insert new entry
            conn.execute('''
                INSERT INTO failed_queue (
                    entry_hash, lead_data, tenant, attempts,
                    last_error, last_error_message, last_error_details, error_history,
                    first_failed_at, last_attempted_at
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_hash,
                json.dumps(lead_data),
                tenant,
                error_info.get('type', 'unknown'),
                error_info.get('message', ''),
                json.dumps(error_details),
                json.dumps([error_details]),
                now,
                now
            ))
            logger.info(f"Added {lead_data.get('email')} to failed queue")


def get_failed_queue_entries() -> List[Dict[str, Any]]:
    """Get all entries in the failed queue."""
    with get_db() as conn:
        rows = conn.execute('''
            SELECT entry_hash, lead_data, tenant, attempts,
                   last_error, last_error_message, last_error_details, error_history,
                   first_failed_at, last_attempted_at
            FROM failed_queue
        ''').fetchall()

        return [
            {
                'entry_hash': row['entry_hash'],
                'lead_data': json.loads(row['lead_data']),
                'tenant': row['tenant'],
                'attempts': row['attempts'],
                'last_error': row['last_error'],
                'last_error_message': row['last_error_message'],
                'last_error_details': json.loads(row['last_error_details'] or '{}'),
                'error_history': json.loads(row['error_history'] or '[]'),
                'first_failed_at': row['first_failed_at'],
                'last_attempted_at': row['last_attempted_at']
            }
            for row in rows
        ]


def get_failed_queue_count() -> int:
    """Get the count of failed queue entries."""
    with get_db() as conn:
        result = conn.execute('SELECT COUNT(*) FROM failed_queue').fetchone()
        return result[0]


def remove_from_failed_queue(entry_hash: str):
    """Remove an entry from the failed queue."""
    with get_db() as conn:
        conn.execute('DELETE FROM failed_queue WHERE entry_hash = ?', (entry_hash,))


def remove_from_failed_queue_batch(entry_hashes: List[str]):
    """Remove multiple entries from the failed queue."""
    if not entry_hashes:
        return
    with get_db() as conn:
        placeholders = ','.join(['?' for _ in entry_hashes])
        conn.execute(f'DELETE FROM failed_queue WHERE entry_hash IN ({placeholders})', entry_hashes)


def update_failed_entry_attempt(entry_hash: str, error_info: Dict[str, Any]):
    """Update a failed entry with new attempt information."""
    now = utc_now().isoformat()

    with get_db() as conn:
        row = conn.execute(
            'SELECT attempts, error_history FROM failed_queue WHERE entry_hash = ?',
            (entry_hash,)
        ).fetchone()

        if row:
            attempts = row['attempts'] + 1
            error_history = json.loads(row['error_history'] or '[]')

            error_details = {
                'type': error_info.get('type', 'unknown'),
                'message': error_info.get('message', ''),
                'status_code': error_info.get('status_code'),
                'recorded_at': now
            }
            error_history.append(error_details)
            error_history = error_history[-5:]

            conn.execute('''
                UPDATE failed_queue SET
                    attempts = ?,
                    last_error = ?,
                    last_error_message = ?,
                    last_attempted_at = ?,
                    error_history = ?
                WHERE entry_hash = ?
            ''', (
                attempts,
                error_info.get('type', 'unknown'),
                error_info.get('message', ''),
                now,
                json.dumps(error_history),
                entry_hash
            ))
            return attempts
    return None


# ============================================================================
# Dead Letters Operations
# ============================================================================

def move_to_dead_letters(entry_hash: str):
    """Move a failed queue entry to dead letters."""
    now = utc_now().isoformat()

    with get_db() as conn:
        # Get the entry from failed queue
        row = conn.execute(
            'SELECT * FROM failed_queue WHERE entry_hash = ?',
            (entry_hash,)
        ).fetchone()

        if not row:
            logger.warning(f"Entry {entry_hash} not found in failed queue")
            return

        # Check if already in dead letters
        existing = conn.execute(
            'SELECT 1 FROM dead_letters WHERE entry_hash = ?',
            (entry_hash,)
        ).fetchone()

        if existing:
            logger.debug(f"Entry {entry_hash} already in dead letters, skipping duplicate")
        else:
            # Insert into dead letters
            conn.execute('''
                INSERT INTO dead_letters (
                    entry_hash, lead_data, tenant, attempts,
                    last_error, last_error_message, last_error_details, error_history,
                    first_failed_at, last_attempted_at, moved_to_dead_letters_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['entry_hash'],
                row['lead_data'],
                row['tenant'],
                row['attempts'],
                row['last_error'],
                row['last_error_message'],
                row['last_error_details'],
                row['error_history'],
                row['first_failed_at'],
                row['last_attempted_at'],
                now
            ))

            lead_data = json.loads(row['lead_data'])
            logger.warning(
                f"Moved {lead_data.get('email')} to dead letters after {row['attempts']} attempts"
            )

        # Remove from failed queue
        conn.execute('DELETE FROM failed_queue WHERE entry_hash = ?', (entry_hash,))


def get_dead_letters() -> List[Dict[str, Any]]:
    """Get all dead letter entries."""
    with get_db() as conn:
        rows = conn.execute('''
            SELECT entry_hash, lead_data, tenant, attempts,
                   last_error, last_error_message, last_error_details, error_history,
                   first_failed_at, last_attempted_at, moved_to_dead_letters_at
            FROM dead_letters
        ''').fetchall()

        return [
            {
                'entry_hash': row['entry_hash'],
                'lead_data': json.loads(row['lead_data']),
                'tenant': row['tenant'],
                'attempts': row['attempts'],
                'last_error': row['last_error'],
                'last_error_message': row['last_error_message'],
                'last_error_details': json.loads(row['last_error_details'] or '{}'),
                'error_history': json.loads(row['error_history'] or '[]'),
                'first_failed_at': row['first_failed_at'],
                'last_attempted_at': row['last_attempted_at'],
                'moved_to_dead_letters_at': row['moved_to_dead_letters_at']
            }
            for row in rows
        ]


def get_dead_letter_count() -> int:
    """Get the count of dead letter entries."""
    with get_db() as conn:
        result = conn.execute('SELECT COUNT(*) FROM dead_letters').fetchone()
        return result[0]


def requeue_dead_letters() -> int:
    """
    Move all dead letters back to the failed queue for retry.

    Returns:
        Number of entries requeued
    """
    now = utc_now().isoformat()

    with get_db() as conn:
        rows = conn.execute('SELECT * FROM dead_letters').fetchall()

        if not rows:
            logger.info("No dead letters to requeue")
            return 0

        count = 0
        for row in rows:
            # Reset attempts and insert into failed queue
            conn.execute('''
                INSERT OR REPLACE INTO failed_queue (
                    entry_hash, lead_data, tenant, attempts,
                    last_error, last_error_message, last_error_details, error_history,
                    first_failed_at, last_attempted_at
                ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
            ''', (
                row['entry_hash'],
                row['lead_data'],
                row['tenant'],
                row['last_error'],
                row['last_error_message'],
                row['last_error_details'],
                row['error_history'],
                row['first_failed_at'],
                now
            ))
            count += 1

        # Clear dead letters
        conn.execute('DELETE FROM dead_letters')

        logger.info(f"Requeued {count} dead letters to failed queue")
        return count


def cleanup_expired_dead_letters(ttl_days: int = 90) -> int:
    """
    Remove dead letter entries older than TTL.

    Args:
        ttl_days: Days to keep dead letters

    Returns:
        Number of entries removed
    """
    cutoff = (utc_now() - timedelta(days=ttl_days)).isoformat()

    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM dead_letters WHERE moved_to_dead_letters_at < ?',
            (cutoff,)
        )
        deleted = cursor.rowcount

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired dead letter entries (TTL: {ttl_days} days)")

        return deleted


def get_dead_letter_stats() -> Dict[str, Any]:
    """Get statistics about dead letters."""
    with get_db() as conn:
        count = conn.execute('SELECT COUNT(*) FROM dead_letters').fetchone()[0]

        if count == 0:
            return {
                'count': 0,
                'oldest_days': 0,
                'error_types': {},
                'tenants': {}
            }

        # Get oldest entry age
        oldest = conn.execute('''
            SELECT MIN(moved_to_dead_letters_at) FROM dead_letters
        ''').fetchone()[0]

        oldest_days = 0
        if oldest:
            try:
                oldest_dt = datetime.fromisoformat(oldest.replace('Z', '+00:00'))
                oldest_days = (utc_now() - oldest_dt).days
            except (ValueError, AttributeError):
                pass

        # Get error type counts
        error_rows = conn.execute('''
            SELECT last_error, COUNT(*) as cnt FROM dead_letters GROUP BY last_error
        ''').fetchall()
        error_types = {row['last_error'] or 'unknown': row['cnt'] for row in error_rows}

        # Get tenant counts
        tenant_rows = conn.execute('''
            SELECT tenant, COUNT(*) as cnt FROM dead_letters GROUP BY tenant
        ''').fetchall()
        tenants = {row['tenant']: row['cnt'] for row in tenant_rows}

        return {
            'count': count,
            'oldest_days': oldest_days,
            'error_types': error_types,
            'tenants': tenants
        }


# ============================================================================
# Admin Activity Logging
# ============================================================================

def log_admin_activity(
    action: str,
    details: str = '',
    username: str = None,
    ip_address: str = None,
    session_id: str = None,
    user_agent: str = None,
    metadata: Dict[str, Any] = None
):
    """
    Log an admin activity to the database.

    Args:
        action: The action performed (e.g., 'login', 'logout', 'retry_failed')
        details: Human-readable description of the action
        username: The username who performed the action
        ip_address: Client IP address
        session_id: Truncated session identifier for linking activities
        user_agent: Client user agent string
        metadata: Additional JSON-serializable metadata
    """
    # Validate and safely serialize metadata
    metadata_json = None
    if metadata:
        try:
            # Attempt to serialize to validate it's JSON-serializable
            metadata_json = json.dumps(metadata)
        except (TypeError, ValueError) as e:
            # Log the error and store a sanitized version
            logger.warning(f"Admin activity metadata not JSON-serializable: {e}")
            metadata_json = json.dumps({'error': 'metadata_serialization_failed', 'type': str(type(metadata))})

    with get_db() as conn:
        conn.execute('''
            INSERT INTO admin_activity (timestamp, action, details, username, ip_address, session_id, user_agent, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            utc_now().isoformat(),
            action,
            details,
            username or 'unknown',
            ip_address or 'unknown',
            session_id,
            user_agent,
            metadata_json
        ))

    logger.info(f"Admin activity: {action} by {username or 'unknown'} from {ip_address or 'unknown'} - {details}")


def get_admin_activity_log(limit: int = 50, action_filter: str = None) -> List[Dict[str, Any]]:
    """
    Get recent admin activity entries.

    Args:
        limit: Maximum number of entries to return
        action_filter: Optional filter by action type

    Returns:
        List of activity entries, newest first
    """
    with get_db() as conn:
        if action_filter:
            rows = conn.execute('''
                SELECT id, timestamp, action, details, username, ip_address, session_id, user_agent, metadata
                FROM admin_activity
                WHERE action = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (action_filter, limit)).fetchall()
        else:
            rows = conn.execute('''
                SELECT id, timestamp, action, details, username, ip_address, session_id, user_agent, metadata
                FROM admin_activity
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,)).fetchall()

        return [
            {
                'id': row['id'],
                'timestamp': row['timestamp'],
                'action': row['action'],
                'details': row['details'],
                'username': row['username'],
                'ip_address': row['ip_address'],
                'session_id': row['session_id'],
                'user_agent': row['user_agent'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            }
            for row in rows
        ]


def cleanup_old_admin_activity(days: int = 90) -> int:
    """
    Remove admin activity entries older than specified days.

    Args:
        days: Number of days to keep entries

    Returns:
        Number of entries deleted
    """
    cutoff = (utc_now() - timedelta(days=days)).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM admin_activity WHERE timestamp < ?',
            (cutoff,)
        )
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old admin activity entries (older than {days} days)")
        return deleted


# ============================================================================
# Daily Leads Metrics
# ============================================================================

def _normalize_date(date_str: str) -> str:
    """
    Normalize a date string to YYYY-MM-DD format.

    Handles various input formats commonly found in spreadsheets,
    including ISO datetime with timezone (e.g., 2026-01-09T02:57:57-05:00).

    Args:
        date_str: Date string in various formats

    Returns:
        Normalized date string in YYYY-MM-DD format, or today's date if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return utc_now().strftime('%Y-%m-%d')

    date_str = date_str.strip()
    if not date_str:
        return utc_now().strftime('%Y-%m-%d')

    from datetime import datetime

    # First, try to handle ISO datetime with timezone (e.g., 2026-01-09T02:57:57-05:00)
    # Just extract the date part before 'T'
    if 'T' in date_str:
        try:
            date_part = date_str.split('T')[0]
            parsed = datetime.strptime(date_part, '%Y-%m-%d')
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Common date formats in order of likelihood
    formats = [
        '%Y-%m-%d',      # ISO format: 2024-01-15
        '%m/%d/%Y',      # US format: 01/15/2024
        '%m/%d/%y',      # US short: 01/15/24
        '%d/%m/%Y',      # European: 15/01/2024
        '%Y/%m/%d',      # Alternative ISO: 2024/01/15
        '%B %d, %Y',     # Full month: January 15, 2024
        '%b %d, %Y',     # Short month: Jan 15, 2024
        '%d-%m-%Y',      # European with dashes: 15-01-2024
        '%Y%m%d',        # Compact: 20240115
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # If all formats fail, log warning and use today's date
    logger.warning(f"Could not parse date '{date_str}', using today's date")
    return utc_now().strftime('%Y-%m-%d')


def record_lead_metric(location: str, tenant: str, lead_date: str = None, success: bool = True):
    """
    Record a lead metric for a specific date.

    Args:
        location: The sheet/location name
        tenant: The tenant name
        lead_date: The date the lead was created (from spreadsheet), format 'YYYY-MM-DD'.
                   If not provided, uses today's date.
        success: True if lead was sent successfully, False if failed
    """
    # Normalize the date (handles None, empty, and various formats)
    lead_date = _normalize_date(lead_date)

    with get_db() as conn:
        # Try to update existing row
        if success:
            cursor = conn.execute('''
                UPDATE leads_daily_metrics
                SET leads_sent = leads_sent + 1
                WHERE lead_date = ? AND location = ?
            ''', (lead_date, location))
        else:
            cursor = conn.execute('''
                UPDATE leads_daily_metrics
                SET leads_failed = leads_failed + 1
                WHERE lead_date = ? AND location = ?
            ''', (lead_date, location))

        # If no row was updated, insert a new one
        if cursor.rowcount == 0:
            conn.execute('''
                INSERT INTO leads_daily_metrics (lead_date, location, tenant, leads_sent, leads_failed)
                VALUES (?, ?, ?, ?, ?)
            ''', (lead_date, location, tenant, 1 if success else 0, 0 if success else 1))


def get_leads_by_location_daily(days: int = 30) -> List[Dict[str, Any]]:
    """
    Get daily lead counts by location for the specified number of days.

    Args:
        days: Number of days to retrieve (default 30)

    Returns:
        List of daily metrics grouped by lead_date and location
    """
    cutoff = (utc_now() - timedelta(days=days)).strftime('%Y-%m-%d')

    with get_db() as conn:
        rows = conn.execute('''
            SELECT lead_date, location, tenant, leads_sent, leads_failed
            FROM leads_daily_metrics
            WHERE lead_date >= ?
            ORDER BY lead_date ASC, location ASC
        ''', (cutoff,)).fetchall()

        return [
            {
                'date': row['lead_date'],
                'location': row['location'],
                'tenant': row['tenant'],
                'leads_sent': row['leads_sent'],
                'leads_failed': row['leads_failed']
            }
            for row in rows
        ]


def get_leads_chart_data(days: int = 30) -> Dict[str, Any]:
    """
    Get lead data formatted for charting.

    Returns data structured for easy chart rendering with:
    - dates: list of date strings
    - locations: dict of location -> list of daily counts
    - totals: list of daily totals

    Args:
        days: Number of days to retrieve

    Returns:
        Dict with chart-ready data
    """
    raw_data = get_leads_by_location_daily(days)

    # Build a set of all dates and locations
    dates_set = set()
    locations_set = set()
    data_map = {}  # (date, location) -> leads_sent

    for row in raw_data:
        date = row['date']
        location = row['location']
        dates_set.add(date)
        locations_set.add(location)
        data_map[(date, location)] = row['leads_sent']

    # Sort dates and locations
    dates = sorted(dates_set)
    locations = sorted(locations_set)

    # Fill in the data matrix (with zeros for missing days)
    location_data = {}
    for loc in locations:
        location_data[loc] = [data_map.get((d, loc), 0) for d in dates]

    # Calculate daily totals
    totals = [sum(data_map.get((d, loc), 0) for loc in locations) for d in dates]

    return {
        'dates': dates,
        'locations': location_data,
        'totals': totals,
        'location_list': locations
    }


def get_leads_summary_stats(days: int = 30) -> Dict[str, Any]:
    """
    Get summary statistics for leads.

    Args:
        days: Number of days to include in summary

    Returns:
        Dict with summary statistics
    """
    cutoff = (utc_now() - timedelta(days=days)).strftime('%Y-%m-%d')

    with get_db() as conn:
        # Total leads by location
        location_totals = conn.execute('''
            SELECT location, tenant, SUM(leads_sent) as total_sent, SUM(leads_failed) as total_failed
            FROM leads_daily_metrics
            WHERE lead_date >= ?
            GROUP BY location
            ORDER BY total_sent DESC
        ''', (cutoff,)).fetchall()

        # Daily averages
        daily_avg = conn.execute('''
            SELECT AVG(daily_total) as avg_per_day
            FROM (
                SELECT lead_date, SUM(leads_sent) as daily_total
                FROM leads_daily_metrics
                WHERE lead_date >= ?
                GROUP BY lead_date
            )
        ''', (cutoff,)).fetchone()

        # Best and worst days
        best_day = conn.execute('''
            SELECT lead_date, SUM(leads_sent) as total
            FROM leads_daily_metrics
            WHERE lead_date >= ?
            GROUP BY lead_date
            ORDER BY total DESC
            LIMIT 1
        ''', (cutoff,)).fetchone()

        worst_day = conn.execute('''
            SELECT lead_date, SUM(leads_sent) as total
            FROM leads_daily_metrics
            WHERE lead_date >= ?
            GROUP BY lead_date
            ORDER BY total ASC
            LIMIT 1
        ''', (cutoff,)).fetchone()

        return {
            'by_location': [
                {
                    'location': row['location'],
                    'tenant': row['tenant'],
                    'total_sent': row['total_sent'],
                    'total_failed': row['total_failed']
                }
                for row in location_totals
            ],
            'avg_per_day': round(daily_avg['avg_per_day'] or 0, 1) if daily_avg else 0,
            'best_day': {'date': best_day['lead_date'], 'count': best_day['total']} if best_day else None,
            'worst_day': {'date': worst_day['lead_date'], 'count': worst_day['total']} if worst_day else None,
            'days_included': days
        }


def cleanup_old_metrics(days: int = 365) -> int:
    """
    Remove metrics entries older than specified days.

    Args:
        days: Number of days to keep metrics (default 1 year)

    Returns:
        Number of entries deleted
    """
    cutoff = (utc_now() - timedelta(days=days)).strftime('%Y-%m-%d')
    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM leads_daily_metrics WHERE lead_date < ?',
            (cutoff,)
        )
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old metrics entries (older than {days} days)")
        return deleted


# ============================================================================
# Web Session Storage (Database-backed)
# ============================================================================

SESSION_EXPIRY_SECONDS = 86400  # 24 hours


def create_session(token: str, username: str, ip_address: str = None) -> None:
    """
    Create a new session in the database.

    Args:
        token: Session token
        username: Username for the session
        ip_address: Client IP address
    """
    now = utc_now()
    expires_at = now + timedelta(seconds=SESSION_EXPIRY_SECONDS)

    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO web_sessions (token, username, ip_address, created_at, last_accessed_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (token, username, ip_address, now.isoformat(), now.isoformat(), expires_at.isoformat()))


def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a session token and update last accessed time.

    Args:
        token: Session token to validate

    Returns:
        Session data dict if valid, None otherwise
    """
    if not token:
        return None

    now = utc_now()

    with get_db() as conn:
        row = conn.execute('''
            SELECT token, username, ip_address, created_at, last_accessed_at, expires_at
            FROM web_sessions WHERE token = ?
        ''', (token,)).fetchone()

        if not row:
            return None

        # Check if expired
        expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
        if now > expires_at:
            # Delete expired session
            conn.execute('DELETE FROM web_sessions WHERE token = ?', (token,))
            return None

        # Update last accessed time
        conn.execute('''
            UPDATE web_sessions SET last_accessed_at = ? WHERE token = ?
        ''', (now.isoformat(), token))

        return {
            'token': row['token'],
            'username': row['username'],
            'ip_address': row['ip_address'],
            'created_at': row['created_at'],
            'last_accessed_at': now.isoformat(),
            'expires_at': row['expires_at']
        }


def invalidate_session(token: str) -> None:
    """Delete a session from the database."""
    with get_db() as conn:
        conn.execute('DELETE FROM web_sessions WHERE token = ?', (token,))


def get_session_info(token: str) -> Optional[Dict[str, Any]]:
    """Get session info without updating last accessed time."""
    if not token:
        return None

    with get_db() as conn:
        row = conn.execute('''
            SELECT token, username, ip_address, created_at, last_accessed_at, expires_at
            FROM web_sessions WHERE token = ?
        ''', (token,)).fetchone()

        if not row:
            return None

        return {
            'token': row['token'],
            'username': row['username'],
            'ip_address': row['ip_address'],
            'created_at': row['created_at'],
            'last_accessed_at': row['last_accessed_at'],
            'expires_at': row['expires_at']
        }


def cleanup_expired_sessions() -> int:
    """Remove expired sessions from the database."""
    now = utc_now().isoformat()
    with get_db() as conn:
        cursor = conn.execute('DELETE FROM web_sessions WHERE expires_at < ?', (now,))
        return cursor.rowcount


def get_active_session_count() -> int:
    """Get count of active (non-expired) sessions."""
    now = utc_now().isoformat()
    with get_db() as conn:
        result = conn.execute(
            'SELECT COUNT(*) FROM web_sessions WHERE expires_at >= ?',
            (now,)
        ).fetchone()
        return result[0]


# ============================================================================
# CSRF Token Storage (Database-backed)
# ============================================================================

CSRF_TOKEN_EXPIRY_SECONDS = 3600  # 1 hour


def create_csrf_token(token: str) -> None:
    """
    Store a CSRF token in the database.

    Args:
        token: CSRF token to store
    """
    now = utc_now()
    expires_at = now + timedelta(seconds=CSRF_TOKEN_EXPIRY_SECONDS)

    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO csrf_tokens (token, created_at, expires_at)
            VALUES (?, ?, ?)
        ''', (token, now.isoformat(), expires_at.isoformat()))


def validate_csrf_token(token: str) -> bool:
    """
    Validate a CSRF token.

    Args:
        token: Token to validate

    Returns:
        True if valid, False otherwise
    """
    if not token:
        return False

    now = utc_now()

    with get_db() as conn:
        row = conn.execute('''
            SELECT token, expires_at FROM csrf_tokens WHERE token = ?
        ''', (token,)).fetchone()

        if not row:
            return False

        # Check if expired
        expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
        if now > expires_at:
            # Delete expired token
            conn.execute('DELETE FROM csrf_tokens WHERE token = ?', (token,))
            return False

        return True


def invalidate_csrf_token(token: str) -> None:
    """Delete a CSRF token (use after successful form submission)."""
    with get_db() as conn:
        conn.execute('DELETE FROM csrf_tokens WHERE token = ?', (token,))


def cleanup_expired_csrf_tokens() -> int:
    """Remove expired CSRF tokens from the database."""
    now = utc_now().isoformat()
    with get_db() as conn:
        cursor = conn.execute('DELETE FROM csrf_tokens WHERE expires_at < ?', (now,))
        return cursor.rowcount
