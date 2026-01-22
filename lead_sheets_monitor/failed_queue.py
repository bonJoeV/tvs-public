"""
Failed queue and dead letter management for Lead Sheets Monitor.
Handles retry logic with exponential backoff.

Now uses SQLite storage backend for atomic, corruption-resistant operations.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from config import (
    DLQ_MAX_RETRY_ATTEMPTS, DLQ_RETRY_BACKOFF_HOURS,
    RATE_LIMIT_DELAY, get_app_settings
)
from utils import utc_now, logger, compute_entry_hash

# Import storage functions
import storage


def generate_row_hash(sheet_id: str, gid: str, headers: list, row_data: list) -> str:
    """
    Generate a unique hash for a row based on key fields only.

    Uses the consolidated compute_entry_hash function from utils.
    This prevents re-submission when non-critical fields (notes, etc.) are edited.

    NOTE: We intentionally do NOT include sheet_id/gid in the hash to maintain
    backwards compatibility with existing sent_hashes entries. Deduplication is
    based on email/name/phone only, which means the same lead won't be submitted
    twice even if they appear in multiple sheets.

    Args:
        sheet_id: Google Sheets spreadsheet ID (unused, kept for API compatibility)
        gid: Sheet tab ID (unused, kept for API compatibility)
        headers: List of column headers
        row_data: List of cell values for the row

    Returns:
        32-character hex hash string
    """
    # Build a dict of the row data for easier access
    row_dict = {}
    for i, value in enumerate(row_data):
        if i < len(headers) and value:
            row_dict[headers[i].lower().strip()] = str(value).strip()

    # Use the consolidated hash function WITHOUT sheet identifiers
    # This maintains backwards compatibility with existing sent_hashes entries
    return compute_entry_hash(row_dict)


# ============================================================================
# Dead-Letter Queue Functions
# ============================================================================

def add_to_failed_queue(lead_data: Dict[str, Any], momence_host: str,
                        error_info: Dict[str, Any], entry_hash: str) -> None:
    """
    Add a failed lead to the retry queue.

    Args:
        lead_data: The lead data that failed to submit
        momence_host: Momence host name
        error_info: Error details from the failed submission
        entry_hash: The hash of the original entry

    Note: The entry_hash should already be in sent_hashes (added before API call
    for idempotency). This ensures the lead won't be picked up as NEW again.
    The failed queue handles retries separately from the main processing loop.
    """
    storage.add_to_failed_queue(entry_hash, lead_data, momence_host, error_info)

    # Ensure hash is in sent_hashes (should already be there from idempotency check,
    # but add defensively in case this function is called from elsewhere)
    if not storage.hash_exists(entry_hash):
        storage.add_sent_hash(entry_hash, lead_data.get('sheetName'))


def should_retry_failed_entry(entry: Dict[str, Any], force: bool = False) -> bool:
    """
    Check if a failed entry should be retried based on backoff timing.

    Args:
        entry: Failed queue entry
        force: If True, ignore backoff timing

    Returns:
        True if the entry should be retried
    """
    if force:
        return True

    attempts = entry.get('attempts', 0)
    if attempts >= DLQ_MAX_RETRY_ATTEMPTS:
        return False  # Should be moved to dead letters

    last_attempted = entry.get('last_attempted_at')
    if not last_attempted:
        return True

    try:
        last_attempted_dt = datetime.fromisoformat(last_attempted.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return True

    # Get backoff hours for this attempt (use last value if attempts exceed list length)
    backoff_index = min(attempts - 1, len(DLQ_RETRY_BACKOFF_HOURS) - 1)
    backoff_hours = DLQ_RETRY_BACKOFF_HOURS[backoff_index] if backoff_index >= 0 else 1

    next_retry_time = last_attempted_dt + timedelta(hours=backoff_hours)
    return utc_now() >= next_retry_time


def move_to_dead_letters(failed_data: dict, entry: Dict[str, Any]) -> None:
    """
    Move a failed entry to the dead letters list.

    Args:
        failed_data: Unused with SQLite backend (kept for compatibility)
        entry: Failed queue entry to move
    """
    entry_hash = entry.get('entry_hash')
    if entry_hash:
        storage.move_to_dead_letters(entry_hash)


def process_failed_queue(dry_run: bool = False,
                         force_retry: bool = False,
                         batch_size: int = 100) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Process entries in the failed queue, retrying those that are due.

    Uses pagination to avoid loading all entries into memory at once.
    Tracks processed hashes to prevent infinite loops when entries aren't due for retry.

    Args:
        dry_run: If True, log actions without making API calls
        force_retry: If True, retry all entries regardless of backoff timing
        batch_size: Number of entries to process per batch (default 100)

    Returns:
        Tuple of (successful_count, failed_count, errors_list)
    """
    # Import here to avoid circular dependency
    from momence import create_momence_lead
    from notifications import send_leads_digest

    total_count = storage.get_failed_queue_count()
    if total_count == 0:
        return 0, 0, []

    logger.info(f"Processing failed queue ({total_count} entries in batches of {batch_size})")

    successful = 0
    failed = 0
    errors: List[Dict[str, Any]] = []

    # Track processed hashes to prevent re-processing in this run
    # This fixes the memory leak where the same entries were loaded repeatedly
    processed_hashes: set = set()
    moved_to_dead_letters: set = set()

    while True:
        # Always fetch from offset 0 since we remove/modify entries
        batch = storage.get_failed_queue_entries_paginated(limit=batch_size, offset=0)
        if not batch:
            break

        # Filter out entries we've already seen this run
        batch = [e for e in batch if e.get('entry_hash') not in processed_hashes
                 and e.get('entry_hash') not in moved_to_dead_letters]
        if not batch:
            # All remaining entries have been processed this run
            break

        entries_to_remove: List[str] = []
        leads_by_host: Dict[str, List[Dict[str, Any]]] = {}

        for entry in batch:
            entry_hash = entry.get('entry_hash')

            # Check if max retries exceeded
            if entry.get('attempts', 0) >= DLQ_MAX_RETRY_ATTEMPTS:
                storage.move_to_dead_letters(entry_hash)
                moved_to_dead_letters.add(entry_hash)
                continue

            # Mark as processed (even if skipped due to backoff)
            processed_hashes.add(entry_hash)

            # Check if it's time to retry
            if not should_retry_failed_entry(entry, force=force_retry):
                logger.debug(f"Skipping {entry.get('lead_data', {}).get('email')} - not due for retry")
                continue

            lead_data = entry.get('lead_data', {})
            momence_host = entry.get('momence_host') or entry.get('tenant')  # Support old 'tenant' key for backwards compat

            logger.info(f"Retrying failed lead: {lead_data.get('email')} (attempt {entry.get('attempts', 0) + 1})")

            if dry_run:
                logger.info(f"[DRY RUN] Would retry lead: {lead_data.get('email')}")
                continue

            # Add delay between ALL API requests (not just successful ones)
            requests_made = successful + failed
            if requests_made > 0:
                time.sleep(RATE_LIMIT_DELAY)

            result = create_momence_lead(lead_data, momence_host, dry_run=False)

            if result.get('success'):
                successful += 1
                entries_to_remove.append(entry_hash)

                # Track for notification (limited memory - clear after sending)
                lead_record = {**lead_data, 'success': True}
                if momence_host not in leads_by_host:
                    leads_by_host[momence_host] = []
                leads_by_host[momence_host].append(lead_record)

                # Update storage
                location = lead_data.get('sheetName', momence_host)
                storage.add_sent_hash(entry_hash, location)
                storage.increment_location_count(location)

                logger.info(f"Successfully retried lead: {lead_data.get('email')}")
            else:
                failed += 1
                error_info = result.get('error', {})

                # Update the entry with new attempt info
                new_attempts = storage.update_failed_entry_attempt(entry_hash, error_info)

                # Check if we should move to dead letters
                if new_attempts and new_attempts >= DLQ_MAX_RETRY_ATTEMPTS:
                    storage.move_to_dead_letters(entry_hash)
                    moved_to_dead_letters.add(entry_hash)

                # Cap error response_body size to avoid memory bloat
                errors.append({
                    'momence_host': momence_host,
                    'lead_email': lead_data.get('email'),
                    'sheet_name': lead_data.get('sheetName'),
                    'error_type': error_info.get('type', 'unknown'),
                    'status_code': error_info.get('status_code'),
                    'message': error_info.get('message', '')[:500],  # Cap at 500 chars
                    'attempts': new_attempts or entry.get('attempts', 0) + 1,
                    'timestamp': utc_now().isoformat()
                })

        # Remove successful entries from failed queue after each batch
        if entries_to_remove:
            storage.remove_from_failed_queue_batch(entries_to_remove)

        # Send notifications for this batch's successfully retried leads (then clear memory)
        if not dry_run:
            for host_name, leads in leads_by_host.items():
                if leads:
                    logger.info(f"Sending leads digest for {len(leads)} retried leads to Momence host '{host_name}'")
                    send_leads_digest(host_name, leads)

        # Clear batch memory
        del batch
        del leads_by_host
        del entries_to_remove

    # Clear tracking sets
    del processed_hashes
    del moved_to_dead_letters

    logger.info(f"Failed queue processing complete: {successful} successful, {failed} failed")
    return successful, failed, errors


def list_dead_letters() -> None:
    """Print summary of dead letter entries with detailed error information."""
    dead_letters = storage.get_dead_letters()

    if not dead_letters:
        print("No dead letter entries")
        return

    print(f"\n{'='*80}")
    print(f"Dead Letters: {len(dead_letters)} entries")
    print(f"{'='*80}\n")

    for i, entry in enumerate(dead_letters, 1):
        lead_data = entry.get('lead_data', {})
        print(f"{i}. {lead_data.get('email', 'N/A')}")
        print(f"   Momence Host: {entry.get('momence_host') or entry.get('tenant')}")
        print(f"   Sheet: {lead_data.get('sheetName', 'N/A')}")
        print(f"   Attempts: {entry.get('attempts', 0)}")
        print(f"   First failed: {entry.get('first_failed_at', 'N/A')}")
        print(f"   Moved to DL: {entry.get('moved_to_dead_letters_at', 'N/A')}")
        print(f"   Last error: {entry.get('last_error', 'N/A')}")
        print(f"   Last error message: {entry.get('last_error_message', 'N/A')}")
        print()


def cleanup_expired_dead_letters(ttl_days: int = None) -> int:
    """
    Remove dead letter entries older than TTL.

    Args:
        ttl_days: Days to keep dead letters (default: from config, typically 90)

    Returns:
        Number of entries removed
    """
    if ttl_days is None:
        settings = get_app_settings()
        ttl_days = settings.dlq_ttl_days

    return storage.cleanup_expired_dead_letters(ttl_days)


def get_dead_letter_stats() -> Dict[str, Any]:
    """
    Get statistics about dead letters for monitoring.

    Returns:
        Dict with count, oldest entry age, error type breakdown
    """
    return storage.get_dead_letter_stats()
