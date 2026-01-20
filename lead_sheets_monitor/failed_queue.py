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

    Args:
        sheet_id: Google Sheets spreadsheet ID
        gid: Sheet tab ID
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

    # Use the consolidated hash function with sheet identifiers
    return compute_entry_hash(row_dict, sheet_id=sheet_id, gid=gid)


# ============================================================================
# Dead-Letter Queue Functions
# ============================================================================

def add_to_failed_queue(lead_data: Dict[str, Any], tenant: str,
                        error_info: Dict[str, Any], entry_hash: str) -> None:
    """
    Add a failed lead to the retry queue.

    Args:
        lead_data: The lead data that failed to submit
        tenant: Tenant name
        error_info: Error details from the failed submission
        entry_hash: The hash of the original entry
    """
    storage.add_to_failed_queue(entry_hash, lead_data, tenant, error_info)

    # Also add to sent_hashes so it won't be re-detected as NEW
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
                         force_retry: bool = False) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Process entries in the failed queue, retrying those that are due.

    Args:
        dry_run: If True, log actions without making API calls
        force_retry: If True, retry all entries regardless of backoff timing

    Returns:
        Tuple of (successful_count, failed_count, errors_list)
    """
    # Import here to avoid circular dependency
    from momence import create_momence_lead
    from notifications import send_leads_digest

    failed_entries = storage.get_failed_queue_entries()

    if not failed_entries:
        return 0, 0, []

    successful = 0
    failed = 0
    errors: List[Dict[str, Any]] = []
    entries_to_remove: List[str] = []
    leads_by_tenant: Dict[str, List[Dict[str, Any]]] = {}

    logger.info(f"Processing failed queue ({len(failed_entries)} entries)")

    for entry in failed_entries:
        # Check if max retries exceeded
        if entry.get('attempts', 0) >= DLQ_MAX_RETRY_ATTEMPTS:
            storage.move_to_dead_letters(entry.get('entry_hash'))
            continue

        # Check if it's time to retry
        if not should_retry_failed_entry(entry, force=force_retry):
            logger.debug(f"Skipping {entry.get('lead_data', {}).get('email')} - not due for retry")
            continue

        lead_data = entry.get('lead_data', {})
        tenant = entry.get('tenant')
        entry_hash = entry.get('entry_hash')

        logger.info(f"Retrying failed lead: {lead_data.get('email')} (attempt {entry.get('attempts', 0) + 1})")

        if dry_run:
            logger.info(f"[DRY RUN] Would retry lead: {lead_data.get('email')}")
            continue

        # Add delay between ALL API requests (not just successful ones)
        requests_made = successful + failed
        if requests_made > 0:
            time.sleep(RATE_LIMIT_DELAY)

        result = create_momence_lead(lead_data, tenant, dry_run=False)

        if result.get('success'):
            successful += 1
            entries_to_remove.append(entry_hash)

            # Track for notification
            lead_record = {**lead_data, 'success': True}
            if tenant not in leads_by_tenant:
                leads_by_tenant[tenant] = []
            leads_by_tenant[tenant].append(lead_record)

            # Update storage
            location = lead_data.get('sheetName', tenant)
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

            errors.append({
                'tenant': tenant,
                'lead_email': lead_data.get('email'),
                'sheet_name': lead_data.get('sheetName'),
                'error_type': error_info.get('type', 'unknown'),
                'status_code': error_info.get('status_code'),
                'message': error_info.get('message', ''),
                'attempts': new_attempts or entry.get('attempts', 0) + 1,
                'timestamp': utc_now().isoformat()
            })

    # Remove successful entries from failed queue
    if entries_to_remove:
        storage.remove_from_failed_queue_batch(entries_to_remove)

    # Send notifications for successfully retried leads
    if not dry_run:
        for tenant_name, leads in leads_by_tenant.items():
            if leads:
                logger.info(f"Sending leads digest for retried leads to tenant '{tenant_name}'")
                send_leads_digest(tenant_name, leads)

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
        print(f"   Tenant: {entry.get('tenant')}")
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
