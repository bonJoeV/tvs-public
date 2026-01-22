#!/usr/bin/env python3
"""
Lead Sheets Monitor - Main Entry Point

Monitors Google Sheets for new Facebook Lead Ads entries and
pushes them to Momence CRM via their Customer Leads API.

Usage:
    python monitor.py                    # Single run
    python monitor.py --daemon           # Continuous daemon mode
    python monitor.py --dry-run          # Test without making changes
    python monitor.py --queue-status     # Show failed queue status
    python monitor.py --retry-failed     # Force retry all failed entries
"""

# Standard library
import argparse
import gc
import json
import signal
import sys
import time
from typing import Dict, Any, List, Optional

# Local application
import storage
from config import (
    DLQ_ENABLED, LOG_DIR, IS_CLOUD_RUN, GRACEFUL_SHUTDOWN_TIMEOUT,
    RATE_LIMIT_DELAY, HEALTH_SERVER_ENABLED, HEALTH_SERVER_PORT, DATABASE_FILE,
    validate_startup_requirements, log_startup_warnings, StartupValidationError,
    get_momence_hosts, get_sheets_config
)
from failed_queue import (
    generate_row_hash, add_to_failed_queue, process_failed_queue, list_dead_letters
)
from momence import create_momence_lead, close_session
from notifications import send_error_digest, send_location_leads_digest
from sheets import (
    get_google_sheets_service, get_sheet_name_by_gid, fetch_sheet_data,
    build_momence_lead_data
)
from utils import utc_now, setup_logging, logger
from web import start_health_server, update_health_state, cleanup_web_caches


def run_cleanup_tasks():
    """
    Run all database cleanup tasks.

    This removes old/expired data to prevent unbounded database growth:
    - Old sent hashes (default: 90 days)
    - Old admin activity logs (default: 90 days)
    - Old daily lead metrics (default: 365 days)
    - Expired dead letter entries (default: 90 days)
    - Expired web sessions
    - Expired CSRF tokens

    Called once per monitor run in daemon mode.
    Each cleanup task is run independently so one failure doesn't block others.
    """
    cleanup_results = {}

    import sqlite3

    # Clean up old sent hashes (keep 90 days)
    try:
        hashes_cleaned = storage.cleanup_old_hashes(days=90)
        cleanup_results['sent_hashes'] = hashes_cleaned
        if hashes_cleaned > 0:
            logger.info(f"Cleaned up {hashes_cleaned} old sent hashes")
    except sqlite3.Error as e:
        logger.error(f"Database error cleaning up sent hashes: {type(e).__name__}: {e}")
        cleanup_results['sent_hashes'] = f"error: {e}"

    # Clean up old admin activity logs (keep 90 days)
    try:
        activity_cleaned = storage.cleanup_old_admin_activity(days=90)
        cleanup_results['admin_activity'] = activity_cleaned
        if activity_cleaned > 0:
            logger.info(f"Cleaned up {activity_cleaned} old admin activity entries")
    except sqlite3.Error as e:
        logger.error(f"Database error cleaning up admin activity: {type(e).__name__}: {e}")
        cleanup_results['admin_activity'] = f"error: {e}"

    # Clean up old daily metrics (keep 1 year)
    try:
        metrics_cleaned = storage.cleanup_old_metrics(days=365)
        cleanup_results['metrics'] = metrics_cleaned
        if metrics_cleaned > 0:
            logger.info(f"Cleaned up {metrics_cleaned} old metrics entries")
    except sqlite3.Error as e:
        logger.error(f"Database error cleaning up metrics: {type(e).__name__}: {e}")
        cleanup_results['metrics'] = f"error: {e}"

    # Clean up expired dead letter entries (keep 90 days)
    try:
        from failed_queue import cleanup_expired_dead_letters
        dead_letters_cleaned = cleanup_expired_dead_letters(ttl_days=90)
        cleanup_results['dead_letters'] = dead_letters_cleaned
        if dead_letters_cleaned > 0:
            logger.info(f"Cleaned up {dead_letters_cleaned} expired dead letter entries")
    except sqlite3.Error as e:
        logger.error(f"Database error cleaning up dead letters: {type(e).__name__}: {e}")
        cleanup_results['dead_letters'] = f"error: {e}"

    # Clean up expired web sessions
    try:
        sessions_cleaned = storage.cleanup_expired_sessions()
        cleanup_results['sessions'] = sessions_cleaned
        if sessions_cleaned > 0:
            logger.info(f"Cleaned up {sessions_cleaned} expired web sessions")
    except sqlite3.Error as e:
        logger.error(f"Database error cleaning up sessions: {type(e).__name__}: {e}")
        cleanup_results['sessions'] = f"error: {e}"

    # Clean up expired CSRF tokens
    try:
        csrf_cleaned = storage.cleanup_expired_csrf_tokens()
        cleanup_results['csrf_tokens'] = csrf_cleaned
        if csrf_cleaned > 0:
            logger.info(f"Cleaned up {csrf_cleaned} expired CSRF tokens")
    except sqlite3.Error as e:
        logger.error(f"Database error cleaning up CSRF tokens: {type(e).__name__}: {e}")
        cleanup_results['csrf_tokens'] = f"error: {e}"

    # Clean up stale database connections from dead threads
    try:
        connections_cleaned = storage.cleanup_stale_connections()
        cleanup_results['db_connections'] = connections_cleaned
        if connections_cleaned > 0:
            logger.info(f"Cleaned up {connections_cleaned} stale database connections")
    except Exception as e:
        logger.error(f"Error cleaning up stale connections: {type(e).__name__}: {e}")
        cleanup_results['db_connections'] = f"error: {e}"

    # Log summary if any errors occurred
    errors = [k for k, v in cleanup_results.items() if isinstance(v, str) and v.startswith('error:')]
    if errors:
        logger.warning(f"Cleanup completed with errors in: {', '.join(errors)}")

    return cleanup_results


# ============================================================================
# Support Report Generation
# ============================================================================

def generate_support_report(output_file: Optional[str] = None) -> str:
    """
    Generate a comprehensive support report for Momence API issues.

    Args:
        output_file: Optional file path to write the report to

    Returns:
        The report as a string
    """
    failed_queue = storage.get_failed_queue_entries()
    dead_letters = storage.get_dead_letters()

    all_errors = failed_queue + dead_letters

    if not all_errors:
        return "No errors recorded. Run the monitor to capture error details."

    # Build the report
    lines = []
    lines.append("=" * 80)
    lines.append("MOMENCE API SUPPORT REPORT")
    lines.append(f"Generated: {utc_now().isoformat()}")
    lines.append("=" * 80)
    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Failed Queue Entries: {len(failed_queue)}")
    lines.append(f"Dead Letter Entries: {len(dead_letters)}")
    lines.append(f"Total Errors: {len(all_errors)}")
    lines.append("")

    # Unique error types
    error_types = {}
    for entry in all_errors:
        err_type = entry.get('last_error', 'unknown')
        error_types[err_type] = error_types.get(err_type, 0) + 1
    lines.append("Error Types:")
    for err_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
        lines.append(f"  {err_type}: {count}")
    lines.append("")

    # Configuration info (sanitized)
    lines.append("CONFIGURATION")
    lines.append("-" * 40)
    for host_name, host_config in get_momence_hosts().items():
        lines.append(f"Momence Host: {host_name}")
        lines.append(f"  Host ID: {host_config.get('host_id', 'N/A')}")
        lines.append(f"  Token: {'***' + host_config.get('token', '')[-4:] if host_config.get('token') else 'N/A'}")
        lines.append(f"  Enabled: {host_config.get('enabled', True)}")
    lines.append("")

    # Lead sources
    lines.append("Lead Sources Configured:")
    for sheet in get_sheets_config():
        lines.append(f"  {sheet.get('name')}: sourceId={sheet.get('lead_source_id')}")
    lines.append("")

    # Detailed error samples (first 5)
    lines.append("DETAILED ERROR SAMPLES (up to 5)")
    lines.append("-" * 40)

    for i, entry in enumerate(all_errors[:5], 1):
        error_details = entry.get('last_error_details', {})
        lead_data = entry.get('lead_data', {})

        lines.append(f"\n[ERROR {i}]")
        lines.append(f"Email: {lead_data.get('email', 'N/A')}")
        lines.append(f"Sheet: {lead_data.get('sheetName', 'N/A')}")
        lines.append(f"Momence Host: {entry.get('momence_host', 'N/A')}")
        lines.append(f"Attempts: {entry.get('attempts', 0)}")
        lines.append(f"First Failed: {entry.get('first_failed_at', 'N/A')}")
        lines.append(f"Last Attempt: {entry.get('last_attempted_at', 'N/A')}")
        lines.append("")

        if error_details:
            lines.append("Request Details:")
            lines.append(f"  URL: {error_details.get('request_url', 'N/A')}")
            lines.append(f"  Method: {error_details.get('request_method', 'POST')}")
            lines.append(f"  Timestamp: {error_details.get('request_timestamp', 'N/A')}")
            lines.append(f"  Duration: {error_details.get('request_duration_ms', 'N/A')}ms")
            lines.append("")

            # Request headers
            req_headers = error_details.get('request_headers', {})
            if req_headers:
                lines.append("  Request Headers:")
                for k, v in req_headers.items():
                    lines.append(f"    {k}: {v}")
            lines.append("")

            # Request payload (with token masked)
            payload = error_details.get('request_payload', {})
            if payload:
                lines.append("  Request Payload:")
                for k, v in payload.items():
                    display_val = '***' if k == 'token' else v
                    lines.append(f"    {k}: {display_val}")
            lines.append("")

            lines.append("Response Details:")
            lines.append(f"  HTTP Status: {error_details.get('status_code', 'N/A')} {error_details.get('status_text', '')}")
            lines.append(f"  CF-Ray: {error_details.get('cf_ray', 'N/A')}")
            lines.append(f"  Content-Type: {error_details.get('response_content_type', 'N/A')}")
            lines.append(f"  Content-Length: {error_details.get('response_content_length', 'N/A')}")
            lines.append("")

            # Response headers
            resp_headers = error_details.get('response_headers', {})
            if resp_headers:
                lines.append("  Response Headers:")
                for k, v in resp_headers.items():
                    lines.append(f"    {k}: {v}")
            lines.append("")

            lines.append(f"  Response Body: {error_details.get('response_body', '(empty)')}")
        else:
            lines.append("  (No detailed error information available)")

        lines.append("")
        lines.append("-" * 40)

    # Curl command for reproduction
    if all_errors:
        first_error = all_errors[0]
        error_details = first_error.get('last_error_details', {})
        if error_details:
            lines.append("")
            lines.append("CURL COMMAND FOR REPRODUCTION")
            lines.append("-" * 40)
            lines.append("# Replace YOUR_TOKEN with your actual token")
            url = error_details.get('request_url', 'https://api.momence.com/integrations/customer-leads/HOST_ID/collect')
            payload = error_details.get('request_payload', {})
            # Build curl-friendly payload with masked token
            curl_payload = {k: ('YOUR_TOKEN' if k == 'token' else v) for k, v in payload.items()}
            lines.append(f'curl -v "{url}" \\')
            lines.append('  -H "Content-Type: application/json" \\')
            lines.append('  -H "Accept: application/json" \\')
            lines.append(f"  -d '{json.dumps(curl_payload)}'")

    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    report = "\n".join(lines)

    # Write to file if specified
    if output_file:
        # Validate output file path to prevent path traversal attacks
        from pathlib import Path
        output_path = Path(output_file).resolve()
        cwd = Path.cwd().resolve()

        # Ensure the output file is within current directory or a subdirectory
        # Also allow absolute paths that don't traverse upward
        try:
            output_path.relative_to(cwd)
        except ValueError:
            # Path is not relative to cwd - check it's not trying to traverse
            if '..' in str(output_file):
                raise ValueError(f"Invalid output path: path traversal not allowed: {output_file}")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(report)
        print(f"Report written to: {output_path}")

    return report


def requeue_dead_letters() -> int:
    """
    Move all dead letters back to the failed queue for retry.

    Returns:
        Number of entries requeued
    """
    return storage.requeue_dead_letters()


# ============================================================================
# Main Processing
# ============================================================================

def check_for_new_entries(
    service,
    verbose: bool = False,
    full_scan: bool = False
) -> List[Dict[str, Any]]:
    """
    Check all configured sheets for new entries using incremental fetching.

    Uses row progress tracking to fetch only new rows since last check.
    Falls back to full scan on first run or when --full-scan is specified.

    Args:
        service: Google Sheets API service
        verbose: Enable verbose logging
        full_scan: If True, ignore progress and fetch entire sheet

    Returns:
        List of new entries to process
    """
    new_entries: List[Dict[str, Any]] = []

    for sheet_config in get_sheets_config():
        # Skip disabled sheets
        if not sheet_config.get('enabled', True):
            logger.debug(f"Sheet '{sheet_config.get('name')}' is disabled, skipping")
            continue

        spreadsheet_id = sheet_config['spreadsheet_id']
        gid = sheet_config['gid']
        momence_host = sheet_config.get('momence_host')

        if not momence_host:
            logger.error(f"Sheet '{sheet_config.get('name')}' has no momence_host configured, skipping")
            continue

        # Skip if momence_host is disabled
        host_cfg = get_momence_hosts().get(momence_host, {})
        if not host_cfg.get('enabled', True):
            logger.debug(f"Momence host '{momence_host}' is disabled, skipping sheet '{sheet_config.get('name')}'")
            continue

        sheet_name = get_sheet_name_by_gid(service, spreadsheet_id, gid)
        if not sheet_name:
            logger.warning(f"Could not find sheet with gid={gid}")
            continue

        # Determine start row for incremental fetching
        if full_scan:
            start_row = 1
            logger.info(f"Checking sheet: {sheet_name} (FULL SCAN)")
        else:
            last_row = storage.get_sheet_progress(spreadsheet_id, gid)
            # start_row is the first data row to fetch (row 2 = first data row after headers)
            # If last_row is 0 (never processed), fetch from row 2 (all data)
            # If last_row is N, fetch from row N+1 (new rows only)
            start_row = max(last_row + 1, 2) if last_row > 0 else 1
            if last_row > 0:
                logger.info(f"Checking sheet: {sheet_name} (incremental from row {start_row})")
            else:
                logger.info(f"Checking sheet: {sheet_name} (first scan)")

        data = fetch_sheet_data(service, spreadsheet_id, sheet_name, start_row=start_row if start_row > 1 else 1)
        if not data:
            continue

        headers = data[0] if data else []
        rows = data[1:] if len(data) > 1 else []

        if not rows:
            if verbose:
                logger.info(f"  No new rows found")
            continue

        # Calculate actual row indices
        # If incremental (start_row > 1), first data row is at start_row
        # If full scan (start_row = 1), first data row is at row 2
        first_data_row = start_row if start_row > 1 else 2

        logger.info(f"  Fetched {len(rows)} rows (starting at row {first_data_row})")

        # Filter out empty rows and build row data with indices
        valid_rows = []
        for idx, row in enumerate(rows):
            if any(cell.strip() if isinstance(cell, str) else cell for cell in row):
                row_index = first_data_row + idx
                valid_rows.append((row_index, row))

        if not valid_rows:
            if verbose:
                logger.info(f"  No non-empty rows found")
            continue

        # Batch hash generation for all valid rows
        row_hashes = [
            generate_row_hash(spreadsheet_id, gid, headers, row)
            for _, row in valid_rows
        ]

        # Batch hash lookup (single DB query instead of N queries)
        existing_hashes = storage.get_existing_hashes(row_hashes)

        # Process only truly new rows (handles crash recovery case)
        for (row_index, row), row_hash in zip(valid_rows, row_hashes):
            if row_hash in existing_hashes:
                if verbose:
                    logger.debug(f"  Row {row_index} already processed (hash exists)")
                continue

            new_entries.append({
                'sheet_config': sheet_config,
                'sheet_name': sheet_name,
                'gid': gid,
                'spreadsheet_id': spreadsheet_id,
                'row_index': row_index,
                'headers': headers,
                'data': row,
                'hash': row_hash,
                'momence_host': momence_host
            })
            logger.info(f"  NEW ENTRY at row {row_index}")

        # Update progress tracking (last row we've seen)
        if valid_rows:
            last_processed_row = valid_rows[-1][0]  # Last row index
            total_rows = last_processed_row  # Approximate total (actual row count)
            storage.update_sheet_progress(spreadsheet_id, gid, last_processed_row, total_rows)

    return new_entries


def process_new_entries(new_entries: list, dry_run: bool = False) -> tuple[List[Dict], Dict[str, List[Dict]]]:
    """
    Process new entries by pushing them to Momence CRM.

    For each entry, builds the lead data and attempts to create it in Momence.
    Successful entries are marked in the database. Failed entries are collected
    for error reporting and will be retried on the next cycle.

    Args:
        new_entries: List of entry dicts from check_for_new_entries
        dry_run: If True, log actions without making API calls

    Returns:
        Tuple of (errors list, leads_by_location dict)
    """
    errors: List[Dict[str, Any]] = []
    leads_by_location: Dict[str, List[Dict[str, Any]]] = {}

    if not new_entries:
        logger.info("No new entries to process")
        return errors, leads_by_location

    logger.info(f"Processing {len(new_entries)} new entries")

    posts_made = 0
    for entry in new_entries:
        location = entry['sheet_config'].get('name', entry['momence_host'])
        momence_host = entry['momence_host']

        lead_data = build_momence_lead_data(
            entry['headers'],
            entry['data'],
            entry['sheet_config']
        )
        if lead_data:
            # Idempotency protection: Mark as in-progress BEFORE making API call
            # This prevents duplicate submissions if process crashes mid-request
            # and restarts before the response is processed
            if not dry_run and not storage.hash_exists(entry['hash']):
                storage.add_sent_hash(entry['hash'], location)

            # Add delay between POST requests to avoid rate limiting
            if posts_made > 0:
                time.sleep(RATE_LIMIT_DELAY)
            result = create_momence_lead(lead_data, momence_host, dry_run=dry_run)
            posts_made += 1

            # Track lead for location email notification (regardless of success/failure)
            sync_success = result.get('success', False)
            lead_record = {**lead_data, 'success': sync_success}
            if location not in leads_by_location:
                leads_by_location[location] = []
            leads_by_location[location].append(lead_record)

            if sync_success:
                # Hash already added before API call for idempotency
                # Just increment the location count
                storage.increment_location_count(location)
                # Record daily metric using the lead's created date from spreadsheet
                lead_created_date = lead_data.get('created_time')  # From spreadsheet 'created_time' column
                storage.record_lead_metric(location, momence_host, lead_date=lead_created_date, success=True)
            else:
                # Collect error for admin digest with capped sizes to limit memory usage
                error_info = result.get('error', {})
                response_body = error_info.get('response_body', '')
                errors.append({
                    'momence_host': momence_host,
                    'lead_email': lead_data.get('email'),
                    'sheet_name': lead_data.get('sheetName'),
                    'error_type': error_info.get('type', 'unknown'),
                    'exception_type': error_info.get('exception_type'),
                    'status_code': error_info.get('status_code'),
                    'cf_ray': error_info.get('cf_ray', 'N/A'),
                    'response_headers': error_info.get('response_headers', {}),
                    'response_body': response_body[:500] if response_body else '',  # Cap at 500 chars
                    'message': error_info.get('message', '')[:500],  # Cap at 500 chars
                    'request_url': error_info.get('request_url'),
                    'request_payload': error_info.get('request_payload'),
                    'request_timestamp': error_info.get('request_timestamp'),
                    'request_duration_ms': error_info.get('request_duration_ms'),
                    'timestamp': utc_now().isoformat()
                })
                # Add to failed queue for retry with backoff (if DLQ enabled)
                # Note: Hash already added before API call for idempotency, so lead won't be
                # picked up as NEW again. Failed queue handles the retry separately.
                if DLQ_ENABLED:
                    add_to_failed_queue(lead_data, momence_host, error_info, entry['hash'])
                    logger.warning(f"Lead '{lead_data.get('email')}' failed, added to retry queue")
                else:
                    logger.warning(f"Lead '{lead_data.get('email')}' failed (DLQ disabled, will not be retried)")
                # Record failed metric using the lead's created date from spreadsheet
                lead_created_date = lead_data.get('created_time')  # From spreadsheet 'created_time' column
                storage.record_lead_metric(location, momence_host, lead_date=lead_created_date, success=False)
        else:
            # No valid lead data (missing email, etc.) - mark as processed to avoid retrying
            # The hash was already added for idempotency if lead_data existed, so only
            # add it here if there was no lead_data at all
            if not storage.hash_exists(entry['hash']):
                storage.add_sent_hash(entry['hash'], location)
            storage.increment_location_count(location)

    storage.update_tracker_metadata(last_check=utc_now().isoformat())
    return errors, leads_by_location


def log_location_counts():
    """Log cumulative location counts since cache was built."""
    metadata = storage.get_tracker_metadata()
    location_counts = metadata.get('location_counts', {})
    cache_built_at = metadata.get('cache_built_at', 'unknown')

    if not location_counts:
        logger.info("Location counts: No entries processed yet")
        return

    logger.info(f"Cumulative location counts (since {cache_built_at}):")
    total = 0
    for location, count in sorted(location_counts.items()):
        logger.info(f"  {location}: {count}")
        total += count
    logger.info(f"  TOTAL: {total}")


def run_monitor(
    dry_run: bool = False,
    verbose: bool = False,
    reset_tracker: bool = False,
    full_scan: bool = False
) -> bool:
    """
    Main monitoring function - single run.

    Connects to Google Sheets, checks for new entries, processes them through
    Momence API, and sends notification emails.

    Args:
        dry_run: If True, log actions without making API calls or saving
        verbose: Enable verbose logging
        reset_tracker: If True, clear the tracker and treat all entries as new
        full_scan: If True, ignore row progress and fetch entire sheets

    Returns:
        True if run completed successfully, False on error
    """
    # Re-setup logging to handle date rotation
    setup_logging()

    logger.info("=" * 50)
    logger.info(f"Lead Sheets Monitor (dry_run={dry_run})")
    logger.info(f"Momence hosts configured: {list(get_momence_hosts().keys())}")
    logger.info("=" * 50)

    if reset_tracker:
        logger.warning("Resetting tracker - all entries will be treated as new!")
        # Reset by clearing the database tables
        storage.init_database(allow_create=True)  # Ensure tables exist (create if needed)
        # Note: For a full reset, you would need to clear the tables
        # For now, just update metadata to indicate fresh start
        storage.update_tracker_metadata(
            last_check=None,
            cache_built_at=utc_now().isoformat(),
            location_counts={}
        )
    else:
        hash_count = storage.get_sent_hash_count()
        logger.info(f"Loaded tracker with {hash_count} entries")
        if DLQ_ENABLED:
            # Use count-only queries to avoid loading all entries into memory
            failed_count = storage.get_failed_queue_count()
            dead_count = storage.get_dead_letter_count()
            if failed_count:
                logger.info(f"Failed queue has {failed_count} entries pending retry")
            if dead_count:
                logger.info(f"Dead letters: {dead_count} entries")

    try:
        # Process failed queue first (retry previously failed leads)
        if DLQ_ENABLED:
            # Use count-only check to avoid loading all entries into memory
            failed_count = storage.get_failed_queue_count()
            if failed_count > 0:
                logger.info("Processing failed queue...")
                dlq_success, dlq_failed, dlq_errors = process_failed_queue(dry_run=dry_run)
                if dlq_success or dlq_failed:
                    logger.info(f"Failed queue: {dlq_success} retried successfully, {dlq_failed} still failing")

        logger.info("Connecting to Google Sheets API...")
        service = get_google_sheets_service()
        logger.info("Connected")

        new_entries = check_for_new_entries(service, verbose=verbose, full_scan=full_scan)
        errors, leads_by_location = process_new_entries(new_entries, dry_run=dry_run)

        if not dry_run:
            # Send error digest to admin if there were errors (only once per day)
            if errors:
                metadata = storage.get_tracker_metadata()
                last_error_email = metadata.get('last_error_email_sent')
                today = utc_now().strftime('%Y-%m-%d')

                if last_error_email and last_error_email.startswith(today):
                    logger.info(f"Skipping error digest - already sent today at {last_error_email} ({len(errors)} errors queued)")
                else:
                    logger.info(f"Sending error digest email ({len(errors)} errors)...")
                    if send_error_digest(errors):
                        storage.update_tracker_metadata(last_error_email_sent=utc_now().isoformat())

            # Send leads digest for each location
            for location_name, leads in leads_by_location.items():
                if leads:
                    logger.info(f"Sending leads digest for location '{location_name}' ({len(leads)} leads)...")
                    send_location_leads_digest(location_name, leads)
        else:
            logger.info("[DRY RUN] Tracker not saved, emails not sent")

        # Log cumulative location counts
        log_location_counts()

        # Update health state
        metadata = storage.get_tracker_metadata()
        update_health_state(metadata, success=True)

        logger.info("Monitor run completed")
        return True

    except Exception as e:
        logger.exception(f"Monitor run failed: {e}")
        metadata = storage.get_tracker_metadata()
        update_health_state(metadata, success=False)
        return False


def get_check_interval() -> int:
    """Get the check interval from config.

    Returns:
        int: interval in minutes
    """
    # Use shortest interval among all Momence hosts
    intervals = []
    for host in get_momence_hosts().values():
        schedule = host.get('schedule', {})
        intervals.append(schedule.get('check_interval_minutes', 5))

    return min(intervals) if intervals else 5


class GracefulShutdown:
    """Handler for graceful shutdown signals (SIGTERM, SIGINT)."""

    def __init__(self):
        self.should_stop = False
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signal."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self.should_stop = True


def run_daemon(dry_run: bool = False, verbose: bool = False):
    """
    Run monitor continuously in daemon mode.

    Executes run_monitor() at regular intervals based on tenant configuration.
    Handles graceful shutdown via SIGTERM (sent by Cloud Run).

    Args:
        dry_run: If True, log actions without making API calls
        verbose: Enable verbose logging
    """
    interval_minutes = get_check_interval()
    shutdown_handler = GracefulShutdown()

    logger.info("=" * 50)
    logger.info("Starting Lead Sheets Monitor Daemon")
    if IS_CLOUD_RUN:
        logger.info(f"Running on Cloud Run (graceful shutdown: {GRACEFUL_SHUTDOWN_TIMEOUT}s)")
    logger.info(f"Log directory: {LOG_DIR}")
    logger.info(f"Check interval: {interval_minutes} minutes")
    logger.info(f"Momence hosts configured: {list(get_momence_hosts().keys())}")
    if HEALTH_SERVER_ENABLED:
        logger.info(f"Health server: enabled on port {HEALTH_SERVER_PORT}")
    logger.info("=" * 50)

    # Initialize database - don't auto-create to prevent race conditions
    # On Cloud Run, this will download from GCS if available
    # If no database exists, the monitor will wait for one to be created via dashboard
    db_initialized = storage.init_database(allow_create=False)

    if not db_initialized:
        logger.warning(
            "No database available. Monitor will wait for database to be created. "
            "Use the dashboard to create a new database, or upload one to GCS."
        )
        # Start health server even without DB (will report degraded status)
        health_server = start_health_server(None)

        # Wait for database to appear with timeout
        max_wait_seconds = 300  # 5 minutes max wait
        wait_start = time.time()
        last_warning_time = wait_start

        while not shutdown_handler.should_stop:
            elapsed = time.time() - wait_start

            # Check timeout
            if elapsed >= max_wait_seconds:
                logger.error(
                    f"Database wait timeout after {max_wait_seconds}s. "
                    "No database was created or downloaded from GCS. Exiting."
                )
                if health_server:
                    health_server.shutdown()
                sys.exit(1)

            # Log warning every 30 seconds
            if time.time() - last_warning_time >= 30:
                remaining = max_wait_seconds - elapsed
                logger.warning(
                    f"Still waiting for database... ({elapsed:.0f}s elapsed, {remaining:.0f}s until timeout)"
                )
                last_warning_time = time.time()

            if storage.database_exists():
                logger.info("Database detected! Initializing...")
                db_initialized = storage.init_database(allow_create=False)
                if db_initialized:
                    break
            time.sleep(10)  # Check every 10 seconds

        if not db_initialized:
            logger.error("Shutdown requested before database was available")
            if health_server:
                health_server.shutdown()
            return

    # Start health server if enabled
    metadata = storage.get_tracker_metadata()
    health_server = start_health_server(metadata)

    while not shutdown_handler.should_stop:
        try:
            run_monitor(dry_run=dry_run, verbose=verbose, reset_tracker=False)

            # Sync database to GCS after every run for crash protection
            # This ensures data loss is limited to one check interval if container crashes
            if IS_CLOUD_RUN and not dry_run:
                from cloud_storage import upload_database
                upload_database(DATABASE_FILE)

            # Run all cleanup tasks periodically (once per monitor run)
            run_cleanup_tasks()

            # Cleanup web server in-memory caches (sessions, CSRF, rate limits)
            # This prevents memory leaks when dashboard traffic is low
            cleanup_web_caches()

            # Force garbage collection to reclaim memory from processed data structures
            # This helps prevent gradual memory growth from fragmentation
            gc.collect()

        except Exception as e:
            logger.exception(f"Error during monitor run: {e}")

        if shutdown_handler.should_stop:
            break

        # Sleep in smaller increments to respond to shutdown faster
        logger.info(f"Next check in {interval_minutes} minutes...")
        sleep_seconds = interval_minutes * 60
        while sleep_seconds > 0 and not shutdown_handler.should_stop:
            time.sleep(min(5, sleep_seconds))  # Check every 5 seconds
            sleep_seconds -= 5

    # Graceful shutdown with timeout enforcement
    # Cloud Run sends SIGTERM with 60s hard timeout, so we must complete within GRACEFUL_SHUTDOWN_TIMEOUT
    logger.info(f"Shutting down gracefully (timeout: {GRACEFUL_SHUTDOWN_TIMEOUT}s)...")
    shutdown_start = time.time()

    def _check_shutdown_timeout(operation: str) -> bool:
        """Check if we're approaching the shutdown timeout."""
        elapsed = time.time() - shutdown_start
        remaining = GRACEFUL_SHUTDOWN_TIMEOUT - elapsed
        if remaining < 2:  # Less than 2 seconds remaining
            logger.warning(f"Shutdown timeout approaching during {operation}, forcing exit")
            return True
        return False

    # Stop health server first (fast operation)
    if health_server:
        try:
            if not _check_shutdown_timeout("health_server_shutdown"):
                health_server.shutdown()
                logger.info("Health server stopped")
        except Exception as e:
            logger.error(f"Error stopping health server: {e}")

    # Close HTTP session to clean up connections
    try:
        if not _check_shutdown_timeout("session_close"):
            close_session()
            logger.debug("HTTP session closed")
    except Exception as e:
        logger.error(f"Error closing HTTP session: {e}")

    # Close Google Sheets service to release httplib2 connections
    try:
        if not _check_shutdown_timeout("google_service_close"):
            from sheets import close_google_service
            close_google_service()
            logger.debug("Google Sheets service closed")
    except Exception as e:
        logger.error(f"Error closing Google Sheets service: {e}")

    # Close database connections
    try:
        if not _check_shutdown_timeout("db_close"):
            storage.close_connection()
            logger.debug("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")

    elapsed = time.time() - shutdown_start
    logger.info(f"Shutdown complete in {elapsed:.1f}s")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Lead Sheets Monitor')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Run without sending/saving')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--reset-tracker', '-r', action='store_true', help='Reset tracker')
    parser.add_argument('--daemon', action='store_true', help='Run continuously with dynamic check intervals')
    parser.add_argument('--full-scan', action='store_true',
                        help='Force full sheet rescan (ignore row progress tracking)')

    # Dead-letter queue management
    parser.add_argument('--retry-failed', action='store_true',
                        help='Force retry all entries in failed queue (ignoring backoff)')
    parser.add_argument('--list-dead-letters', action='store_true',
                        help='List all entries in dead letters')
    parser.add_argument('--requeue-dead-letters', action='store_true',
                        help='Move all dead letters back to failed queue for retry')
    parser.add_argument('--queue-status', action='store_true',
                        help='Show failed queue and dead letters status')
    parser.add_argument('--support-report', nargs='?', const='momence_support_report.txt',
                        metavar='FILE',
                        help='Generate detailed support report for Momence (optionally specify output file)')

    args = parser.parse_args()

    # Handle dead-letter queue management commands
    if args.list_dead_letters:
        list_dead_letters()
        return

    if args.support_report:
        report = generate_support_report(args.support_report)
        print(report)
        return

    if args.requeue_dead_letters:
        count = requeue_dead_letters()
        if count > 0:
            print(f"Requeued {count} dead letters to failed queue")
        return

    if args.queue_status:
        storage.init_database(allow_create=False)
        failed_queue = storage.get_failed_queue_entries()
        dead_letters = storage.get_dead_letters()
        failed_count = len(failed_queue)
        dead_count = len(dead_letters)
        sent_count = storage.get_sent_hash_count()
        print(f"\nQueue Status:")
        print(f"  Failed queue: {failed_count} entries")
        print(f"  Dead letters: {dead_count} entries")
        print(f"  Total sent: {sent_count} entries")
        if failed_count > 0:
            print(f"\nFailed Queue Entries:")
            print("-" * 80)
            for i, entry in enumerate(failed_queue, 1):
                lead = entry.get('lead_data', {})
                error_details = entry.get('last_error_details', {})

                print(f"\n[{i}] {lead.get('email', 'N/A')}")
                print(f"    Momence Host: {entry.get('momence_host', 'N/A')}")
                print(f"    Attempts: {entry.get('attempts', 0)}")
                print(f"    First Failed: {entry.get('first_failed_at', 'N/A')}")
                print(f"    Last Attempt: {entry.get('last_attempted_at', 'N/A')}")
                print(f"    Error Type: {entry.get('last_error', 'N/A')}")

                if error_details:
                    print(f"    HTTP Status: {error_details.get('status_code', 'N/A')}")
                    print(f"    CF-Ray: {error_details.get('cf_ray', 'N/A')}")
                    print(f"    Request URL: {error_details.get('request_url', 'N/A')}")
                    print(f"    Duration: {error_details.get('request_duration_ms', 'N/A')}ms")

                    # Show request payload (with sensitive data masked)
                    payload = error_details.get('request_payload', {})
                    if payload:
                        print(f"    Request Payload:")
                        for key, value in payload.items():
                            # Mask email partially for privacy
                            if key == 'email' and value and '@' in str(value):
                                parts = str(value).split('@')
                                masked = parts[0][:2] + '***@' + parts[1]
                                print(f"      {key}: {masked}")
                            else:
                                print(f"      {key}: {value}")

                    # Show response body if present
                    response_body = error_details.get('response_body', '')
                    if response_body:
                        print(f"    Response Body: {response_body[:200]}")
                    else:
                        print(f"    Response Body: (empty)")

                    # Show response headers if present
                    resp_headers = error_details.get('response_headers', {})
                    if resp_headers:
                        print(f"    Response Headers: {json.dumps(resp_headers, indent=6)}")
                else:
                    print(f"    (No detailed error info available)")

            print("-" * 80)
        return

    if args.retry_failed:
        storage.init_database(allow_create=False)
        failed_queue = storage.get_failed_queue_entries()
        if not failed_queue:
            print("No entries in failed queue")
            return
        print(f"Force retrying {len(failed_queue)} entries...")
        success, failed, errors = process_failed_queue(
            dry_run=args.dry_run, force_retry=True
        )
        print(f"Results: {success} successful, {failed} failed")
        return

    # Validate startup requirements (skip for dry-run which doesn't need credentials)
    try:
        warnings = validate_startup_requirements(require_google_creds=not args.dry_run)
        log_startup_warnings(warnings, logger)
    except StartupValidationError as e:
        logger.error(str(e))
        print(f"ERROR: {e}", file=sys.stderr)
        exit(1)

    # Daemon mode handles its own database initialization (with waiting logic)
    if args.daemon:
        run_daemon(dry_run=args.dry_run, verbose=args.verbose)
    else:
        # For single-run mode, require database to exist (no waiting)
        if not storage.init_database(allow_create=False):
            logger.error("No database available. Use --reset-tracker to create a new database.")
            print("ERROR: No database available. Use --reset-tracker to create a new database.", file=sys.stderr)
            exit(1)

        success = run_monitor(
            dry_run=args.dry_run,
            verbose=args.verbose,
            reset_tracker=args.reset_tracker,
            full_scan=args.full_scan
        )
        exit(0 if success else 1)


if __name__ == '__main__':
    main()
