"""
Google Cloud Storage integration for persistent data storage.

Provides sync functionality to persist SQLite database across Cloud Run
container restarts. Downloads database on startup, uploads on shutdown.

Usage:
    from cloud_storage import download_database, upload_database

    # On startup (before init_database)
    download_database()

    # On shutdown (after close_connection)
    upload_database()
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cloud Storage configuration
GCS_BUCKET = os.getenv('GCS_BUCKET', 'tvs-dashboard-lead-monitor-data')
GCS_DB_BLOB = os.getenv('GCS_DB_BLOB', 'lead_monitor.db')

# Check if running on Cloud Run
IS_CLOUD_RUN = bool(os.getenv('K_SERVICE'))

# Lazy-loaded Cloud Storage client
_storage_client = None


def _get_client():
    """Get or create the Cloud Storage client."""
    global _storage_client
    if _storage_client is None:
        try:
            from google.cloud import storage
            _storage_client = storage.Client()
            logger.info("Cloud Storage client initialized")
        except ImportError:
            logger.warning(
                "google-cloud-storage not installed. "
                "Install with: pip install google-cloud-storage"
            )
            _storage_client = False  # Mark as unavailable
        except Exception as e:
            logger.warning(f"Failed to initialize Cloud Storage client: {e}")
            _storage_client = False
    return _storage_client if _storage_client else None


def download_database(local_path: str) -> bool:
    """
    Download the database from Cloud Storage if it exists.

    IMPORTANT: This function should be called BEFORE any database connections
    are opened, as it replaces the database file. Any existing SQLite connections
    will become invalid after this function runs.

    Args:
        local_path: Local path to save the database file

    Returns:
        True if downloaded successfully, False if not found or error
    """
    if not IS_CLOUD_RUN:
        logger.debug("Not running on Cloud Run, skipping GCS download")
        return False

    client = _get_client()
    if not client:
        logger.warning("Cloud Storage client not available, starting with empty database")
        return False

    try:
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(GCS_DB_BLOB)

        if not blob.exists():
            logger.info(f"No existing database found in gs://{GCS_BUCKET}/{GCS_DB_BLOB}")
            return False

        # Ensure directory exists
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        # Remove any existing database file to ensure clean download
        # This prevents issues with WAL mode where the old file might persist
        for ext in ['', '-wal', '-shm']:
            existing = Path(f"{local_path}{ext}")
            if existing.exists():
                existing.unlink()

        # Download to temp file first, then move (atomic)
        temp_path = f"{local_path}.download"
        blob.download_to_filename(temp_path)
        shutil.move(temp_path, local_path)

        # Get actual file size after download
        actual_size = Path(local_path).stat().st_size
        logger.info(f"Downloaded database from gs://{GCS_BUCKET}/{GCS_DB_BLOB} ({actual_size} bytes)")
        return True

    except Exception as e:
        logger.error(f"Failed to download database from Cloud Storage: {e}")
        return False


def upload_database(local_path: str) -> bool:
    """
    Upload the database to Cloud Storage.

    Includes a safety check to prevent overwriting a larger database with a smaller
    one, which can happen during deployments when a fresh container with an empty
    database races with an existing container that has valid data.

    Args:
        local_path: Local path of the database file

    Returns:
        True if uploaded successfully, False otherwise
    """
    if not IS_CLOUD_RUN:
        logger.debug("Not running on Cloud Run, skipping GCS upload")
        return False

    client = _get_client()
    if not client:
        logger.warning("Cloud Storage client not available, database not persisted")
        return False

    if not Path(local_path).exists():
        logger.warning(f"Database file not found at {local_path}, nothing to upload")
        return False

    try:
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(GCS_DB_BLOB)

        local_size = Path(local_path).stat().st_size

        # Safety check: don't overwrite a larger database with a smaller one
        # This prevents race conditions during deployments where a fresh container
        # might overwrite valid data from an existing container
        # Threshold: 8KB is roughly an empty database with schema only
        MIN_MEANINGFUL_SIZE = 8192
        if local_size < MIN_MEANINGFUL_SIZE:
            # Check if GCS has a larger database
            blob.reload()  # Fetch current metadata
            if blob.exists() and blob.size and blob.size > local_size:
                logger.warning(
                    f"Skipping upload: local database ({local_size} bytes) is smaller than "
                    f"GCS database ({blob.size} bytes). This prevents overwriting valid data."
                )
                return False

        # Upload the database file
        blob.upload_from_filename(local_path)

        logger.info(f"Uploaded database to gs://{GCS_BUCKET}/{GCS_DB_BLOB} ({local_size} bytes)")
        return True

    except Exception as e:
        logger.error(f"Failed to upload database to Cloud Storage: {e}")
        return False
