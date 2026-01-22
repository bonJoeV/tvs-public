"""
SQLite storage backend for Lead Sheets Monitor.

Provides atomic, corruption-resistant storage for:
- Sent entry hashes (deduplication)
- Failed queue entries (retry with backoff)
- Dead letters (failed after max retries)
- Tracker metadata (last check, location counts, etc.)

Replaces the JSON file-based storage with proper database operations.

On Cloud Run, the database is synced to/from Cloud Storage for persistence
across container restarts.
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

# Track if we've synced from cloud storage
_cloud_sync_done = False

# Track database availability status
_database_available = None  # None = unknown, True = available, False = not available


class DatabaseNotAvailableError(Exception):
    """Raised when database operations are attempted but no database exists."""
    pass


def database_exists() -> bool:
    """Check if the database file exists (without creating it)."""
    return Path(DATABASE_FILE).exists()


def is_database_available() -> bool:
    """
    Check if the database is available for operations.

    Returns True if:
    - Database file exists locally, OR
    - Running on Cloud Run and GCS has a database to download
    """
    global _database_available

    # If we've already determined availability, return cached result
    if _database_available is not None:
        return _database_available

    # Check if local file exists
    if database_exists():
        _database_available = True
        return True

    # On Cloud Run, check if GCS has a database
    from config import IS_CLOUD_RUN
    if IS_CLOUD_RUN:
        try:
            from cloud_storage import _get_client, GCS_BUCKET, GCS_DB_BLOB
            client = _get_client()
            if client:
                bucket = client.bucket(GCS_BUCKET)
                blob = bucket.blob(GCS_DB_BLOB)
                if blob.exists():
                    _database_available = True
                    return True
        except Exception:
            pass

    _database_available = False
    return False


def reset_database_availability():
    """Reset the cached database availability status (call after creating DB)."""
    global _database_available
    _database_available = None


def _safe_json_loads(data: str, default: Any = None, field_name: str = "unknown") -> Any:
    """
    Safely parse JSON with error handling.

    Args:
        data: JSON string to parse
        default: Default value if parsing fails (None, {}, or [])
        field_name: Field name for error logging

    Returns:
        Parsed JSON or default value
    """
    if not data:
        return default if default is not None else {}
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON in {field_name}: {e}")
        return default if default is not None else {}

# Thread-local storage for database connections
_local = threading.local()

# Database connection retry settings
DB_CONNECT_MAX_RETRIES = 3
DB_CONNECT_RETRY_DELAY = 1.0  # seconds


def get_db_path() -> str:
    """Get the database file path."""
    return DATABASE_FILE


def _get_connection(allow_create: bool = False) -> sqlite3.Connection:
    """
    Get a thread-local database connection with retry logic.

    Uses WAL mode for better concurrent access and corruption resistance.
    Retries connection on failure to handle transient filesystem issues.

    Args:
        allow_create: If False (default), raises DatabaseNotAvailableError if DB doesn't exist.
                     If True, creates the database file if it doesn't exist.

    Raises:
        DatabaseNotAvailableError: If database doesn't exist and allow_create is False
        sqlite3.Error: If database connection fails
    """
    if not hasattr(_local, 'connection') or _local.connection is None:
        db_path = get_db_path()

        # Check if database exists before connecting (unless explicitly creating)
        if not allow_create and not Path(db_path).exists():
            raise DatabaseNotAvailableError(
                f"Database not found at {db_path}. "
                "Use the dashboard to create a new database or ensure GCS sync is working."
            )

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


def close_connection(upload_to_cloud: bool = True):
    """
    Close the thread-local database connection.

    Args:
        upload_to_cloud: If True, upload database to Cloud Storage (Cloud Run only)
    """
    if hasattr(_local, 'connection') and _local.connection is not None:
        try:
            _local.connection.close()
        except sqlite3.Error as e:
            logger.warning(f"Error closing database connection: {e}")
        finally:
            _local.connection = None
            logger.debug("Closed database connection")

    # Upload to Cloud Storage on close (Cloud Run only)
    if upload_to_cloud:
        try:
            from cloud_storage import upload_database
            upload_database(DATABASE_FILE)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Cloud Storage upload failed: {e}")


@contextmanager
def get_db(allow_create: bool = False):
    """
    Context manager for database operations with automatic commit/rollback.

    Args:
        allow_create: If True, creates database if it doesn't exist.
                     If False (default), raises DatabaseNotAvailableError if DB missing.
    """
    conn = _get_connection(allow_create=allow_create)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_database(allow_create: bool = True) -> bool:
    """
    Initialize the database schema.

    On Cloud Run, first downloads the database from Cloud Storage if it exists.
    Creates tables if they don't exist. Safe to call multiple times.

    Args:
        allow_create: If True (default), creates a new database if none exists.
                     If False, only initializes if database already exists (from GCS or local).

    Returns:
        True if database was initialized successfully, False if no database available
        and allow_create is False.
    """
    global _cloud_sync_done, _database_available

    # Download from Cloud Storage on first init (Cloud Run only)
    if not _cloud_sync_done:
        # IMPORTANT: Close any existing connection BEFORE downloading
        # This ensures the downloaded file isn't overwritten by WAL checkpoint
        # when the old connection is eventually closed
        if hasattr(_local, 'connection') and _local.connection is not None:
            try:
                _local.connection.close()
            except sqlite3.Error:
                pass
            _local.connection = None

        try:
            from cloud_storage import download_database
            download_database(DATABASE_FILE)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Cloud Storage download failed: {e}")
        _cloud_sync_done = True

    # Check if database exists after GCS download attempt
    if not allow_create and not database_exists():
        logger.warning("No database available and allow_create=False. Running without database.")
        _database_available = False
        return False

    # Mark database as available since we're about to create/use it
    _database_available = True

    with get_db(allow_create=True) as conn:
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
                momence_host TEXT NOT NULL,
                attempts INTEGER DEFAULT 1,
                last_error TEXT,
                last_error_message TEXT,
                last_error_details TEXT,
                error_history TEXT,
                first_failed_at TEXT NOT NULL,
                last_attempted_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_failed_queue_momence_host ON failed_queue(momence_host)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_failed_queue_attempts ON failed_queue(attempts)')

        # Dead letters table - entries that exceeded max retries
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dead_letters (
                entry_hash TEXT PRIMARY KEY,
                lead_data TEXT NOT NULL,
                momence_host TEXT NOT NULL,
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

        # Lead metrics table - stores individual lead records for charting
        # lead_datetime: full ISO datetime from spreadsheet (for hourly charts)
        # lead_date: date portion only (for daily aggregation)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS lead_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_datetime TEXT NOT NULL,
                lead_date TEXT NOT NULL,
                location TEXT NOT NULL,
                momence_host TEXT NOT NULL,
                success INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_lead_metrics_datetime ON lead_metrics(lead_datetime)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_lead_metrics_date ON lead_metrics(lead_date)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_lead_metrics_location ON lead_metrics(location)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_lead_metrics_momence_host ON lead_metrics(momence_host)')

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

        # Sheet progress table - tracks last processed row per sheet for incremental fetching
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sheet_progress (
                sheet_key TEXT PRIMARY KEY,
                last_row_index INTEGER NOT NULL,
                last_check TEXT NOT NULL,
                row_count INTEGER
            )
        ''')

        # Momence hosts table - stores host configurations (replaces config.json momence_hosts)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS momence_hosts (
                name TEXT PRIMARY KEY,
                host_id TEXT NOT NULL,
                token TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_momence_hosts_enabled ON momence_hosts(enabled)')

        # Sheets/locations table - stores sheet configurations (replaces config.json sheets)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spreadsheet_id TEXT NOT NULL,
                gid TEXT NOT NULL,
                name TEXT NOT NULL,
                momence_host TEXT NOT NULL,
                lead_source_id TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                notification_email TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(spreadsheet_id, gid),
                FOREIGN KEY (momence_host) REFERENCES momence_hosts(name)
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sheets_momence_host ON sheets(momence_host)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sheets_enabled ON sheets(enabled)')

        logger.info("Database initialized successfully")

    return True


def create_fresh_database() -> bool:
    """
    Create a fresh database, deleting any existing one.

    This is an explicit action typically triggered from the dashboard.
    It will:
    1. Close any existing connections
    2. Delete existing database files (including WAL)
    3. Create a new empty database with schema
    4. Upload to GCS if on Cloud Run

    Returns:
        True if database was created successfully
    """
    global _cloud_sync_done, _database_available

    logger.warning("Creating fresh database - this will delete all existing data!")

    # Close any existing connection
    close_connection(upload_to_cloud=False)

    # Delete existing database files
    db_path = get_db_path()
    for ext in ['', '-wal', '-shm']:
        file_path = Path(f"{db_path}{ext}")
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted {file_path}")

    # Reset sync state so init_database downloads from GCS if needed
    # But since we're creating fresh, we skip the download
    _cloud_sync_done = True  # Skip GCS download
    _database_available = None  # Reset availability cache

    # Create new database with schema
    result = init_database(allow_create=True)

    if result:
        # Upload to GCS immediately
        try:
            from cloud_storage import upload_database
            upload_database(DATABASE_FILE)
            logger.info("Uploaded fresh database to GCS")
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to upload fresh database to GCS: {e}")

    return result


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
# Sheet Progress Operations (Incremental Fetching)
# ============================================================================

def get_sheet_progress(spreadsheet_id: str, gid: str) -> int:
    """Get last processed row index for a sheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID
        gid: The sheet/tab ID within the spreadsheet

    Returns:
        Last processed row index (1-indexed), or 0 if not tracked yet
    """
    sheet_key = f"{spreadsheet_id}_{gid}"
    with get_db() as conn:
        row = conn.execute(
            'SELECT last_row_index FROM sheet_progress WHERE sheet_key = ?',
            (sheet_key,)
        ).fetchone()
        return row['last_row_index'] if row else 0


def update_sheet_progress(spreadsheet_id: str, gid: str, row_index: int, row_count: int) -> None:
    """Update progress tracking for a sheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID
        gid: The sheet/tab ID within the spreadsheet
        row_index: The last processed row index (1-indexed)
        row_count: Total row count in the sheet (for detecting deletions)
    """
    sheet_key = f"{spreadsheet_id}_{gid}"
    with get_db() as conn:
        conn.execute('''
            INSERT INTO sheet_progress (sheet_key, last_row_index, last_check, row_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(sheet_key) DO UPDATE SET
                last_row_index = excluded.last_row_index,
                last_check = excluded.last_check,
                row_count = excluded.row_count
        ''', (sheet_key, row_index, utc_now().isoformat(), row_count))


def reset_sheet_progress(spreadsheet_id: str = None, gid: str = None) -> int:
    """Reset progress for one sheet or all sheets.

    Args:
        spreadsheet_id: If provided with gid, reset only that sheet
        gid: If provided with spreadsheet_id, reset only that sheet

    Returns:
        Number of rows deleted
    """
    with get_db() as conn:
        if spreadsheet_id and gid:
            sheet_key = f"{spreadsheet_id}_{gid}"
            cursor = conn.execute(
                'DELETE FROM sheet_progress WHERE sheet_key = ?',
                (sheet_key,)
            )
        else:
            cursor = conn.execute('DELETE FROM sheet_progress')
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"Reset sheet progress for {deleted} sheet(s)")
        return deleted


def get_existing_hashes(hashes: List[str]) -> Set[str]:
    """Return set of hashes that already exist in sent_hashes.

    Used for batch deduplication of new rows - prevents duplicate submissions
    if container crashes and restarts mid-process.

    Args:
        hashes: List of hash strings to check

    Returns:
        Set of hashes that already exist in the database
    """
    if not hashes:
        return set()
    with get_db() as conn:
        placeholders = ','.join('?' * len(hashes))
        result = conn.execute(
            f'SELECT hash FROM sent_hashes WHERE hash IN ({placeholders})',
            hashes
        ).fetchall()
        return {row['hash'] for row in result}


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
                'location_counts': _safe_json_loads(row['location_counts'], {}, 'location_counts')
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
    # Build JSON path with proper quoting for keys with spaces/special chars
    # e.g., '$."Eden Prairie"' instead of '$.Eden Prairie'
    json_path = f'$."{location}"'

    with get_db() as conn:
        # First, try atomic update using json_set (SQLite 3.38+)
        # This handles the case where the key already exists
        cursor = conn.execute('''
            UPDATE tracker_metadata
            SET location_counts = json_set(
                COALESCE(location_counts, '{}'),
                ?,
                COALESCE(
                    json_extract(location_counts, ?),
                    0
                ) + ?
            )
            WHERE id = 1
        ''', (json_path, json_path, increment))

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
    momence_host: str,
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
                    entry_hash, lead_data, momence_host, attempts,
                    last_error, last_error_message, last_error_details, error_history,
                    first_failed_at, last_attempted_at
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_hash,
                json.dumps(lead_data),
                momence_host,
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
            SELECT entry_hash, lead_data, momence_host, attempts,
                   last_error, last_error_message, last_error_details, error_history,
                   first_failed_at, last_attempted_at
            FROM failed_queue
        ''').fetchall()

        return [
            {
                'entry_hash': row['entry_hash'],
                'lead_data': _safe_json_loads(row['lead_data'], {}, 'lead_data'),
                'momence_host': row['momence_host'],
                'attempts': row['attempts'],
                'last_error': row['last_error'],
                'last_error_message': row['last_error_message'],
                'last_error_details': _safe_json_loads(row['last_error_details'], {}, 'last_error_details'),
                'error_history': _safe_json_loads(row['error_history'], [], 'error_history'),
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


def get_failed_queue_entries_paginated(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get entries from the failed queue with pagination.

    Use this instead of get_failed_queue_entries() to avoid loading all entries
    into memory at once.

    Args:
        limit: Maximum number of entries to return (default 100)
        offset: Number of entries to skip (default 0)

    Returns:
        List of failed queue entry dictionaries
    """
    with get_db() as conn:
        rows = conn.execute('''
            SELECT entry_hash, lead_data, momence_host, attempts,
                   last_error, last_error_message, last_error_details, error_history,
                   first_failed_at, last_attempted_at
            FROM failed_queue
            ORDER BY last_attempted_at ASC
            LIMIT ? OFFSET ?
        ''', (limit, offset)).fetchall()

        return [
            {
                'entry_hash': row['entry_hash'],
                'lead_data': _safe_json_loads(row['lead_data'], {}, 'lead_data'),
                'momence_host': row['momence_host'],
                'attempts': row['attempts'],
                'last_error': row['last_error'],
                'last_error_message': row['last_error_message'],
                'last_error_details': _safe_json_loads(row['last_error_details'], {}, 'last_error_details'),
                'error_history': _safe_json_loads(row['error_history'], [], 'error_history'),
                'first_failed_at': row['first_failed_at'],
                'last_attempted_at': row['last_attempted_at']
            }
            for row in rows
        ]


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
                    entry_hash, lead_data, momence_host, attempts,
                    last_error, last_error_message, last_error_details, error_history,
                    first_failed_at, last_attempted_at, moved_to_dead_letters_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['entry_hash'],
                row['lead_data'],
                row['momence_host'],
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
            SELECT entry_hash, lead_data, momence_host, attempts,
                   last_error, last_error_message, last_error_details, error_history,
                   first_failed_at, last_attempted_at, moved_to_dead_letters_at
            FROM dead_letters
        ''').fetchall()

        return [
            {
                'entry_hash': row['entry_hash'],
                'lead_data': _safe_json_loads(row['lead_data'], {}, 'lead_data'),
                'momence_host': row['momence_host'],
                'attempts': row['attempts'],
                'last_error': row['last_error'],
                'last_error_message': row['last_error_message'],
                'last_error_details': _safe_json_loads(row['last_error_details'], {}, 'last_error_details'),
                'error_history': _safe_json_loads(row['error_history'], [], 'error_history'),
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
                    entry_hash, lead_data, momence_host, attempts,
                    last_error, last_error_message, last_error_details, error_history,
                    first_failed_at, last_attempted_at
                ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
            ''', (
                row['entry_hash'],
                row['lead_data'],
                row['momence_host'],
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
                'momence_hosts': {}
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

        # Get Momence host counts
        host_rows = conn.execute('''
            SELECT momence_host, COUNT(*) as cnt FROM dead_letters GROUP BY momence_host
        ''').fetchall()
        momence_hosts = {row['momence_host']: row['cnt'] for row in host_rows}

        return {
            'count': count,
            'oldest_days': oldest_days,
            'error_types': error_types,
            'momence_hosts': momence_hosts
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
                'metadata': _safe_json_loads(row['metadata'], None, 'admin_activity_metadata') if row['metadata'] else None
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


def record_lead_metric(location: str, momence_host: str, lead_date: str = None, success: bool = True):
    """
    Record a lead metric with full datetime for hourly tracking.

    Args:
        location: The sheet/location name
        momence_host: The Momence host name
        lead_date: The datetime the lead was created (from spreadsheet).
                   Can be full ISO datetime (2026-01-20T09:26:08-05:00) or just date.
                   If not provided, uses current UTC time.
        success: True if lead was sent successfully, False if failed
    """
    # Store full datetime if provided, otherwise use current time
    if lead_date and 'T' in str(lead_date):
        lead_datetime = str(lead_date)
    else:
        lead_datetime = utc_now().isoformat()

    # Normalize to date only for daily aggregation
    normalized_date = _normalize_date(lead_date)

    with get_db() as conn:
        conn.execute('''
            INSERT INTO lead_metrics (lead_datetime, lead_date, location, momence_host, success, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (lead_datetime, normalized_date, location, momence_host, 1 if success else 0, utc_now().isoformat()))


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
            SELECT lead_date, location, momence_host,
                   SUM(success) as leads_sent,
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as leads_failed
            FROM lead_metrics
            WHERE lead_date >= ?
            GROUP BY lead_date, location
            ORDER BY lead_date ASC, location ASC
        ''', (cutoff,)).fetchall()

        return [
            {
                'date': row['lead_date'],
                'location': row['location'],
                'momence_host': row['momence_host'],
                'leads_sent': row['leads_sent'],
                'leads_failed': row['leads_failed']
            }
            for row in rows
        ]


def get_leads_by_hour(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get hourly lead counts by location for the specified number of hours.

    Uses the spreadsheet's created_time (lead_datetime) for accurate hourly tracking.

    Args:
        hours: Number of hours to retrieve (default 24)

    Returns:
        List of hourly metrics grouped by hour and location
    """
    cutoff = (utc_now() - timedelta(hours=hours)).isoformat()

    with get_db() as conn:
        rows = conn.execute('''
            SELECT
                SUBSTR(lead_datetime, 1, 13) || ':00' as hour,
                location,
                momence_host,
                SUM(success) as leads_sent
            FROM lead_metrics
            WHERE lead_datetime >= ?
            GROUP BY SUBSTR(lead_datetime, 1, 13), location
            ORDER BY hour ASC, location ASC
        ''', (cutoff,)).fetchall()

        return [
            {
                'hour': row['hour'],
                'location': row['location'],
                'momence_host': row['momence_host'],
                'leads_sent': row['leads_sent']
            }
            for row in rows
        ]


def get_leads_chart_data(days: int = 30, hourly: bool = False) -> Dict[str, Any]:
    """
    Get lead data formatted for charting.

    Returns data structured for easy chart rendering with:
    - dates: list of date/hour strings
    - locations: dict of location -> list of counts
    - totals: list of totals

    Args:
        days: Number of days to retrieve (ignored if hourly=True)
        hourly: If True, return hourly data for last 24 hours

    Returns:
        Dict with chart-ready data
    """
    if hourly:
        raw_data = get_leads_by_hour(hours=24)
        time_key = 'hour'
    else:
        raw_data = get_leads_by_location_daily(days)
        time_key = 'date'

    # Build a set of all time slots and locations
    times_set = set()
    locations_set = set()
    data_map = {}  # (time, location) -> leads_sent

    for row in raw_data:
        time_val = row[time_key]
        location = row['location']
        times_set.add(time_val)
        locations_set.add(location)
        data_map[(time_val, location)] = row['leads_sent']

    # Sort times and locations
    times = sorted(times_set)
    locations = sorted(locations_set)

    # Fill in the data matrix (with zeros for missing slots)
    location_data = {}
    for loc in locations:
        location_data[loc] = [data_map.get((t, loc), 0) for t in times]

    # Calculate totals
    totals = [sum(data_map.get((t, loc), 0) for loc in locations) for t in times]

    return {
        'dates': times,
        'locations': location_data,
        'totals': totals,
        'location_list': locations,
        'hourly': hourly
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
            SELECT location, momence_host,
                   SUM(success) as total_sent,
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as total_failed
            FROM lead_metrics
            WHERE lead_date >= ?
            GROUP BY location
            ORDER BY total_sent DESC
        ''', (cutoff,)).fetchall()

        # Daily averages
        daily_avg = conn.execute('''
            SELECT AVG(daily_total) as avg_per_day
            FROM (
                SELECT lead_date, SUM(success) as daily_total
                FROM lead_metrics
                WHERE lead_date >= ?
                GROUP BY lead_date
            )
        ''', (cutoff,)).fetchone()

        # Best and worst days
        best_day = conn.execute('''
            SELECT lead_date, SUM(success) as total
            FROM lead_metrics
            WHERE lead_date >= ?
            GROUP BY lead_date
            ORDER BY total DESC
            LIMIT 1
        ''', (cutoff,)).fetchone()

        worst_day = conn.execute('''
            SELECT lead_date, SUM(success) as total
            FROM lead_metrics
            WHERE lead_date >= ?
            GROUP BY lead_date
            ORDER BY total ASC
            LIMIT 1
        ''', (cutoff,)).fetchone()

        return {
            'by_location': [
                {
                    'location': row['location'],
                    'momence_host': row['momence_host'],
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
            'DELETE FROM lead_metrics WHERE lead_date < ?',
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


# ============================================================================
# Momence Hosts Storage (Database-backed)
# ============================================================================

def get_all_hosts() -> List[Dict[str, Any]]:
    """
    Get all Momence hosts from the database.

    Returns:
        List of host dictionaries
    """
    with get_db() as conn:
        rows = conn.execute('''
            SELECT name, host_id, token, enabled, created_at, updated_at
            FROM momence_hosts
            ORDER BY name ASC
        ''').fetchall()

        return [
            {
                'name': row['name'],
                'host_id': row['host_id'],
                'token': row['token'],
                'enabled': bool(row['enabled']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            for row in rows
        ]


def get_host(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a single Momence host by name.

    Args:
        name: Host name

    Returns:
        Host dictionary or None if not found
    """
    with get_db() as conn:
        row = conn.execute('''
            SELECT name, host_id, token, enabled, created_at, updated_at
            FROM momence_hosts WHERE name = ?
        ''', (name,)).fetchone()

        if not row:
            return None

        return {
            'name': row['name'],
            'host_id': row['host_id'],
            'token': row['token'],
            'enabled': bool(row['enabled']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }


def get_enabled_hosts() -> List[Dict[str, Any]]:
    """
    Get all enabled Momence hosts from the database.

    Returns:
        List of enabled host dictionaries
    """
    with get_db() as conn:
        rows = conn.execute('''
            SELECT name, host_id, token, enabled, created_at, updated_at
            FROM momence_hosts
            WHERE enabled = 1
            ORDER BY name ASC
        ''').fetchall()

        return [
            {
                'name': row['name'],
                'host_id': row['host_id'],
                'token': row['token'],
                'enabled': True,
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            for row in rows
        ]


def create_host(name: str, host_id: str, token: str = None, enabled: bool = True) -> Dict[str, Any]:
    """
    Create a new Momence host.

    Args:
        name: Host display name (used as key)
        host_id: Momence host ID
        token: API token (optional if using Secret Manager)
        enabled: Whether the host is enabled

    Returns:
        Created host dictionary

    Raises:
        ValueError: If host with this name already exists
    """
    now = utc_now().isoformat()

    with get_db() as conn:
        # Check if host exists
        existing = conn.execute('SELECT 1 FROM momence_hosts WHERE name = ?', (name,)).fetchone()
        if existing:
            raise ValueError(f"Host '{name}' already exists")

        conn.execute('''
            INSERT INTO momence_hosts (name, host_id, token, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, host_id, token, 1 if enabled else 0, now, now))

        logger.info(f"Created Momence host: {name}")

    return {
        'name': name,
        'host_id': host_id,
        'token': token,
        'enabled': enabled,
        'created_at': now,
        'updated_at': now
    }


def update_host(name: str, host_id: str = None, token: str = None,
                enabled: bool = None) -> Optional[Dict[str, Any]]:
    """
    Update an existing Momence host.

    Args:
        name: Host name to update
        host_id: New host ID (optional)
        token: New API token (optional)
        enabled: New enabled state (optional)

    Returns:
        Updated host dictionary or None if not found
    """
    now = utc_now().isoformat()

    with get_db() as conn:
        # Check if host exists
        existing = conn.execute('SELECT * FROM momence_hosts WHERE name = ?', (name,)).fetchone()
        if not existing:
            return None

        # Build update query
        updates = ['updated_at = ?']
        params = [now]

        if host_id is not None:
            updates.append('host_id = ?')
            params.append(host_id)
        if token is not None:
            updates.append('token = ?')
            params.append(token)
        if enabled is not None:
            updates.append('enabled = ?')
            params.append(1 if enabled else 0)

        params.append(name)
        conn.execute(f'UPDATE momence_hosts SET {", ".join(updates)} WHERE name = ?', params)

        logger.info(f"Updated Momence host: {name}")

    return get_host(name)


def delete_host(name: str) -> bool:
    """
    Delete a Momence host.

    Args:
        name: Host name to delete

    Returns:
        True if deleted, False if not found
    """
    with get_db() as conn:
        # Check if host has associated sheets
        sheet_count = conn.execute(
            'SELECT COUNT(*) FROM sheets WHERE momence_host = ?', (name,)
        ).fetchone()[0]

        if sheet_count > 0:
            raise ValueError(f"Cannot delete host '{name}' - has {sheet_count} associated location(s)")

        cursor = conn.execute('DELETE FROM momence_hosts WHERE name = ?', (name,))
        deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted Momence host: {name}")

        return deleted


def get_hosts_as_config_dict() -> Dict[str, Dict[str, Any]]:
    """
    Get all hosts in the format expected by config.py (MOMENCE_HOSTS dict).

    Returns:
        Dictionary mapping host names to host config dicts
    """
    hosts = get_all_hosts()
    return {
        host['name']: {
            'host_id': host['host_id'],
            'token': host['token'],
            'enabled': host['enabled']
        }
        for host in hosts
    }


# ============================================================================
# Sheets/Locations Storage (Database-backed)
# ============================================================================

def get_all_sheets() -> List[Dict[str, Any]]:
    """
    Get all sheets/locations from the database.

    Returns:
        List of sheet dictionaries
    """
    with get_db() as conn:
        rows = conn.execute('''
            SELECT id, spreadsheet_id, gid, name, momence_host, lead_source_id,
                   enabled, notification_email, created_at, updated_at
            FROM sheets
            ORDER BY momence_host ASC, name ASC
        ''').fetchall()

        return [
            {
                'id': row['id'],
                'spreadsheet_id': row['spreadsheet_id'],
                'gid': row['gid'],
                'name': row['name'],
                'momence_host': row['momence_host'],
                'lead_source_id': row['lead_source_id'],
                'enabled': bool(row['enabled']),
                'notification_email': row['notification_email'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            for row in rows
        ]


def get_sheet(sheet_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single sheet by ID.

    Args:
        sheet_id: Sheet database ID

    Returns:
        Sheet dictionary or None if not found
    """
    with get_db() as conn:
        row = conn.execute('''
            SELECT id, spreadsheet_id, gid, name, momence_host, lead_source_id,
                   enabled, notification_email, created_at, updated_at
            FROM sheets WHERE id = ?
        ''', (sheet_id,)).fetchone()

        if not row:
            return None

        return {
            'id': row['id'],
            'spreadsheet_id': row['spreadsheet_id'],
            'gid': row['gid'],
            'name': row['name'],
            'momence_host': row['momence_host'],
            'lead_source_id': row['lead_source_id'],
            'enabled': bool(row['enabled']),
            'notification_email': row['notification_email'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }


def get_sheet_by_spreadsheet(spreadsheet_id: str, gid: str) -> Optional[Dict[str, Any]]:
    """
    Get a sheet by spreadsheet ID and gid.

    Args:
        spreadsheet_id: Google Spreadsheet ID
        gid: Sheet tab ID

    Returns:
        Sheet dictionary or None if not found
    """
    with get_db() as conn:
        row = conn.execute('''
            SELECT id, spreadsheet_id, gid, name, momence_host, lead_source_id,
                   enabled, notification_email, created_at, updated_at
            FROM sheets WHERE spreadsheet_id = ? AND gid = ?
        ''', (spreadsheet_id, gid)).fetchone()

        if not row:
            return None

        return {
            'id': row['id'],
            'spreadsheet_id': row['spreadsheet_id'],
            'gid': row['gid'],
            'name': row['name'],
            'momence_host': row['momence_host'],
            'lead_source_id': row['lead_source_id'],
            'enabled': bool(row['enabled']),
            'notification_email': row['notification_email'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }


def get_enabled_sheets_db() -> List[Dict[str, Any]]:
    """
    Get all enabled sheets/locations from the database.

    Returns:
        List of enabled sheet dictionaries
    """
    with get_db() as conn:
        rows = conn.execute('''
            SELECT s.id, s.spreadsheet_id, s.gid, s.name, s.momence_host, s.lead_source_id,
                   s.enabled, s.notification_email, s.created_at, s.updated_at
            FROM sheets s
            JOIN momence_hosts h ON s.momence_host = h.name
            WHERE s.enabled = 1 AND h.enabled = 1
            ORDER BY s.momence_host ASC, s.name ASC
        ''').fetchall()

        return [
            {
                'id': row['id'],
                'spreadsheet_id': row['spreadsheet_id'],
                'gid': row['gid'],
                'name': row['name'],
                'momence_host': row['momence_host'],
                'lead_source_id': row['lead_source_id'],
                'enabled': True,
                'notification_email': row['notification_email'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            for row in rows
        ]


def get_sheets_by_host(momence_host: str) -> List[Dict[str, Any]]:
    """
    Get all sheets for a specific Momence host.

    Args:
        momence_host: Host name

    Returns:
        List of sheet dictionaries
    """
    with get_db() as conn:
        rows = conn.execute('''
            SELECT id, spreadsheet_id, gid, name, momence_host, lead_source_id,
                   enabled, notification_email, created_at, updated_at
            FROM sheets WHERE momence_host = ?
            ORDER BY name ASC
        ''', (momence_host,)).fetchall()

        return [
            {
                'id': row['id'],
                'spreadsheet_id': row['spreadsheet_id'],
                'gid': row['gid'],
                'name': row['name'],
                'momence_host': row['momence_host'],
                'lead_source_id': row['lead_source_id'],
                'enabled': bool(row['enabled']),
                'notification_email': row['notification_email'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            for row in rows
        ]


def create_sheet(spreadsheet_id: str, gid: str, name: str, momence_host: str,
                 lead_source_id: str, enabled: bool = True,
                 notification_email: str = None) -> Dict[str, Any]:
    """
    Create a new sheet/location.

    Args:
        spreadsheet_id: Google Spreadsheet ID
        gid: Sheet tab ID
        name: Display name
        momence_host: Momence host name (must exist)
        lead_source_id: Momence lead source ID
        enabled: Whether the sheet is enabled
        notification_email: Email for lead digests (overrides host setting)

    Returns:
        Created sheet dictionary

    Raises:
        ValueError: If sheet already exists or host doesn't exist
    """
    now = utc_now().isoformat()

    with get_db() as conn:
        # Check if host exists
        host = conn.execute('SELECT 1 FROM momence_hosts WHERE name = ?', (momence_host,)).fetchone()
        if not host:
            raise ValueError(f"Momence host '{momence_host}' does not exist")

        # Check if sheet already exists
        existing = conn.execute(
            'SELECT 1 FROM sheets WHERE spreadsheet_id = ? AND gid = ?',
            (spreadsheet_id, gid)
        ).fetchone()
        if existing:
            raise ValueError(f"Sheet with spreadsheet_id '{spreadsheet_id}' and gid '{gid}' already exists")

        conn.execute('''
            INSERT INTO sheets (spreadsheet_id, gid, name, momence_host, lead_source_id,
                               enabled, notification_email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (spreadsheet_id, gid, name, momence_host, str(lead_source_id),
              1 if enabled else 0, notification_email, now, now))

        sheet_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        logger.info(f"Created sheet: {name} (host: {momence_host})")

    return get_sheet(sheet_id)


def update_sheet(sheet_id: int, spreadsheet_id: str = None, gid: str = None,
                 name: str = None, momence_host: str = None, lead_source_id: str = None,
                 enabled: bool = None, notification_email: str = None) -> Optional[Dict[str, Any]]:
    """
    Update an existing sheet/location.

    Args:
        sheet_id: Sheet database ID
        spreadsheet_id: New spreadsheet ID (optional)
        gid: New tab ID (optional)
        name: New display name (optional)
        momence_host: New host name (optional)
        lead_source_id: New lead source ID (optional)
        enabled: New enabled state (optional)
        notification_email: New notification email (optional)

    Returns:
        Updated sheet dictionary or None if not found
    """
    now = utc_now().isoformat()

    with get_db() as conn:
        # Check if sheet exists
        existing = conn.execute('SELECT * FROM sheets WHERE id = ?', (sheet_id,)).fetchone()
        if not existing:
            return None

        # If changing host, verify new host exists
        if momence_host is not None:
            host = conn.execute('SELECT 1 FROM momence_hosts WHERE name = ?', (momence_host,)).fetchone()
            if not host:
                raise ValueError(f"Momence host '{momence_host}' does not exist")

        # Build update query
        updates = ['updated_at = ?']
        params = [now]

        if spreadsheet_id is not None:
            updates.append('spreadsheet_id = ?')
            params.append(spreadsheet_id)
        if gid is not None:
            updates.append('gid = ?')
            params.append(gid)
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if momence_host is not None:
            updates.append('momence_host = ?')
            params.append(momence_host)
        if lead_source_id is not None:
            updates.append('lead_source_id = ?')
            params.append(str(lead_source_id))
        if enabled is not None:
            updates.append('enabled = ?')
            params.append(1 if enabled else 0)
        if notification_email is not None:
            updates.append('notification_email = ?')
            params.append(notification_email)

        params.append(sheet_id)
        conn.execute(f'UPDATE sheets SET {", ".join(updates)} WHERE id = ?', params)

        logger.info(f"Updated sheet ID {sheet_id}")

    return get_sheet(sheet_id)


def delete_sheet(sheet_id: int) -> bool:
    """
    Delete a sheet/location.

    Args:
        sheet_id: Sheet database ID

    Returns:
        True if deleted, False if not found
    """
    with get_db() as conn:
        cursor = conn.execute('DELETE FROM sheets WHERE id = ?', (sheet_id,))
        deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted sheet ID {sheet_id}")

        return deleted


def get_sheets_as_config_list() -> List[Dict[str, Any]]:
    """
    Get all sheets in the format expected by config.py (SHEETS_CONFIG list).

    Returns:
        List of sheet config dicts (without internal fields like id, created_at)
    """
    sheets = get_all_sheets()
    return [
        {
            'spreadsheet_id': sheet['spreadsheet_id'],
            'gid': sheet['gid'],
            'name': sheet['name'],
            'momence_host': sheet['momence_host'],
            'lead_source_id': sheet['lead_source_id'],
            'enabled': sheet['enabled'],
            'notification_email': sheet['notification_email']
        }
        for sheet in sheets
    ]


def get_host_count() -> int:
    """Get the count of Momence hosts."""
    with get_db() as conn:
        result = conn.execute('SELECT COUNT(*) FROM momence_hosts').fetchone()
        return result[0]


def get_sheet_count() -> int:
    """Get the count of sheets/locations."""
    with get_db() as conn:
        result = conn.execute('SELECT COUNT(*) FROM sheets').fetchone()
        return result[0]
