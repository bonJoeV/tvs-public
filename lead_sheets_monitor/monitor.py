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

import argparse
import json
import signal
import sys
import time
from typing import Dict, Any, List

# Import from modules
from config import (
    MOMENCE_TENANTS, SHEETS_CONFIG, DLQ_ENABLED,
    LOG_DIR, IS_CLOUD_RUN, GRACEFUL_SHUTDOWN_TIMEOUT,
    validate_startup_requirements, log_startup_warnings, StartupValidationError
)
from utils import utc_now, setup_logging, logger
from failed_queue import (
    generate_row_hash, add_to_failed_queue, process_failed_queue, list_dead_letters
)
from sheets import (
    get_google_sheets_service, get_sheet_name_by_gid, fetch_sheet_data,
    build_momence_lead_data
)
from momence import create_momence_lead, close_session
from notifications import send_error_digest, send_location_leads_digest
from web import start_health_server, update_health_state
from config import RATE_LIMIT_DELAY, HEALTH_SERVER_ENABLED, HEALTH_SERVER_PORT
import storage


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

    # Clean up old sent hashes (keep 90 days)
    try:
        hashes_cleaned = storage.cleanup_old_hashes(days=90)
        cleanup_results['sent_hashes'] = hashes_cleaned
        if hashes_cleaned > 0:
            logger.info(f"Cleaned up {hashes_cleaned} old sent hashes")
    except Exception as e:
        logger.error(f"Error cleaning up sent hashes: {type(e).__name__}: {e}")
        cleanup_results['sent_hashes'] = f"error: {e}"

    # Clean up old admin activity logs (keep 90 days)
    try:
        activity_cleaned = storage.cleanup_old_admin_activity(days=90)
        cleanup_results['admin_activity'] = activity_cleaned
        if activity_cleaned > 0:
            logger.info(f"Cleaned up {activity_cleaned} old admin activity entries")
    except Exception as e:
        logger.error(f"Error cleaning up admin activity: {type(e).__name__}: {e}")
        cleanup_results['admin_activity'] = f"error: {e}"

    # Clean up old daily metrics (keep 1 year)
    try:
        metrics_cleaned = storage.cleanup_old_metrics(days=365)
        cleanup_results['metrics'] = metrics_cleaned
        if metrics_cleaned > 0:
            logger.info(f"Cleaned up {metrics_cleaned} old metrics entries")
    except Exception as e:
        logger.error(f"Error cleaning up metrics: {type(e).__name__}: {e}")
        cleanup_results['metrics'] = f"error: {e}"

    # Clean up expired dead letter entries (keep 90 days)
    try:
        from failed_queue import cleanup_expired_dead_letters
        dead_letters_cleaned = cleanup_expired_dead_letters(ttl_days=90)
        cleanup_results['dead_letters'] = dead_letters_cleaned
        if dead_letters_cleaned > 0:
            logger.info(f"Cleaned up {dead_letters_cleaned} expired dead letter entries")
    except Exception as e:
        logger.error(f"Error cleaning up dead letters: {type(e).__name__}: {e}")
        cleanup_results['dead_letters'] = f"error: {e}"

    # Clean up expired web sessions
    try:
        sessions_cleaned = storage.cleanup_expired_sessions()
        cleanup_results['sessions'] = sessions_cleaned
        if sessions_cleaned > 0:
            logger.info(f"Cleaned up {sessions_cleaned} expired web sessions")
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {type(e).__name__}: {e}")
        cleanup_results['sessions'] = f"error: {e}"

    # Clean up expired CSRF tokens
    try:
        csrf_cleaned = storage.cleanup_expired_csrf_tokens()
        cleanup_results['csrf_tokens'] = csrf_cleaned
        if csrf_cleaned > 0:
            logger.info(f"Cleaned up {csrf_cleaned} expired CSRF tokens")
    except Exception as e:
        logger.error(f"Error cleaning up CSRF tokens: {type(e).__name__}: {e}")
        cleanup_results['csrf_tokens'] = f"error: {e}"

    # Log summary if any errors occurred
    errors = [k for k, v in cleanup_results.items() if isinstance(v, str) and v.startswith('error:')]
    if errors:
        logger.warning(f"Cleanup completed with errors in: {', '.join(errors)}")

    return cleanup_results


# ============================================================================
# Support Report Generation
# ============================================================================

def generate_support_report(output_file: str = None) -> str:
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
    for tenant_name, tenant_config in MOMENCE_TENANTS.items():
        lines.append(f"Tenant: {tenant_name}")
        lines.append(f"  Host ID: {tenant_config.get('host_id', 'N/A')}")
        lines.append(f"  Token: {'***' + tenant_config.get('token', '')[-4:] if tenant_config.get('token') else 'N/A'}")
        lines.append(f"  Enabled: {tenant_config.get('enabled', True)}")
    lines.append("")

    # Lead sources
    lines.append("Lead Sources Configured:")
    for sheet in SHEETS_CONFIG:
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
        lines.append(f"Tenant: {entry.get('tenant', 'N/A')}")
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
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report written to: {output_file}")

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

def check_for_new_entries(service, verbose: bool = False) -> list:
    """
    Check all configured sheets for new entries.

    Iterates through all configured sheets, fetches current data, and identifies
    rows that haven't been processed yet based on their hash.

    Args:
        service: Google Sheets API service
        verbose: Enable verbose logging

    Returns:
        List of new entries to process
    """
    new_entries = []

    for sheet_config in SHEETS_CONFIG:
        # Skip disabled sheets
        if not sheet_config.get('enabled', True):
            logger.debug(f"Sheet '{sheet_config.get('name')}' is disabled, skipping")
            continue

        spreadsheet_id = sheet_config['spreadsheet_id']
        gid = sheet_config['gid']
        tenant = sheet_config.get('tenant')

        if not tenant:
            logger.error(f"Sheet '{sheet_config.get('name')}' has no tenant configured, skipping")
            continue

        # Skip if tenant is disabled
        tenant_cfg = MOMENCE_TENANTS.get(tenant, {})
        if not tenant_cfg.get('enabled', True):
            logger.debug(f"Tenant '{tenant}' is disabled, skipping sheet '{sheet_config.get('name')}'")
            continue

        sheet_name = get_sheet_name_by_gid(service, spreadsheet_id, gid)
        if not sheet_name:
            logger.warning(f"Could not find sheet with gid={gid}")
            continue

        logger.info(f"Checking sheet: {sheet_name} (gid={gid}, tenant={tenant})")

        data = fetch_sheet_data(service, spreadsheet_id, sheet_name)
        if not data:
            continue

        headers = data[0] if data else []
        rows = data[1:] if len(data) > 1 else []

        if verbose:
            logger.info(f"  Found {len(rows)} data rows")

        for row_index, row in enumerate(rows, start=2):
            if not any(cell.strip() if isinstance(cell, str) else cell for cell in row):
                continue

            row_hash = generate_row_hash(spreadsheet_id, gid, headers, row)

            if not storage.hash_exists(row_hash):
                new_entries.append({
                    'sheet_config': sheet_config,
                    'sheet_name': sheet_name,
                    'gid': gid,
                    'spreadsheet_id': spreadsheet_id,
                    'row_index': row_index,
                    'headers': headers,
                    'data': row,
                    'hash': row_hash,
                    'tenant': tenant
                })
                logger.info(f"  NEW ENTRY at row {row_index}")

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
        location = entry['sheet_config'].get('name', entry['tenant'])
        tenant = entry['tenant']

        lead_data = build_momence_lead_data(
            entry['headers'],
            entry['data'],
            entry['sheet_config']
        )
        if lead_data:
            # Add delay between POST requests to avoid rate limiting
            if posts_made > 0:
                time.sleep(RATE_LIMIT_DELAY)
            result = create_momence_lead(lead_data, tenant, dry_run=dry_run)
            posts_made += 1

            # Track lead for location email notification (regardless of success/failure)
            sync_success = result.get('success', False)
            lead_record = {**lead_data, 'success': sync_success}
            if location not in leads_by_location:
                leads_by_location[location] = []
            leads_by_location[location].append(lead_record)

            if sync_success:
                # Mark as processed and increment location count
                if not storage.hash_exists(entry['hash']):
                    storage.add_sent_hash(entry['hash'], location)
                    storage.increment_location_count(location)
                # Record daily metric using the lead's created date from spreadsheet
                lead_created_date = lead_data.get('created_time')  # From spreadsheet 'created_time' column
                storage.record_lead_metric(location, tenant, lead_date=lead_created_date, success=True)
            else:
                # Collect error for admin digest with full debugging data
                error_info = result.get('error', {})
                errors.append({
                    'tenant': tenant,
                    'lead_email': lead_data.get('email'),
                    'sheet_name': lead_data.get('sheetName'),
                    'error_type': error_info.get('type', 'unknown'),
                    'exception_type': error_info.get('exception_type'),
                    'status_code': error_info.get('status_code'),
                    'cf_ray': error_info.get('cf_ray', 'N/A'),
                    'response_headers': error_info.get('response_headers', {}),
                    'response_body': error_info.get('response_body', ''),
                    'message': error_info.get('message', ''),
                    'request_url': error_info.get('request_url'),
                    'request_payload': error_info.get('request_payload'),
                    'request_timestamp': error_info.get('request_timestamp'),
                    'request_duration_ms': error_info.get('request_duration_ms'),
                    'timestamp': utc_now().isoformat()
                })
                # Add to failed queue for retry with backoff (if DLQ enabled)
                if DLQ_ENABLED:
                    add_to_failed_queue(lead_data, tenant, error_info, entry['hash'])
                    logger.warning(f"Lead '{lead_data.get('email')}' failed, added to retry queue")
                else:
                    logger.warning(f"Lead '{lead_data.get('email')}' failed (DLQ disabled, will retry on next cycle)")
                # Record failed metric using the lead's created date from spreadsheet
                lead_created_date = lead_data.get('created_time')  # From spreadsheet 'created_time' column
                storage.record_lead_metric(location, tenant, lead_date=lead_created_date, success=False)
        else:
            # No valid lead data (missing email, etc.) - mark as processed to avoid retrying
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


def run_monitor(dry_run: bool = False, verbose: bool = False, reset_tracker: bool = False) -> bool:
    """
    Main monitoring function - single run.

    Connects to Google Sheets, checks for new entries, processes them through
    Momence API, and sends notification emails.

    Args:
        dry_run: If True, log actions without making API calls or saving
        verbose: Enable verbose logging
        reset_tracker: If True, clear the tracker and treat all entries as new

    Returns:
        True if run completed successfully, False on error
    """
    # Re-setup logging to handle date rotation
    setup_logging()

    logger.info("=" * 50)
    logger.info(f"Lead Sheets Monitor (dry_run={dry_run})")
    logger.info(f"Tenants configured: {list(MOMENCE_TENANTS.keys())}")
    logger.info("=" * 50)

    if reset_tracker:
        logger.warning("Resetting tracker - all entries will be treated as new!")
        # Reset by clearing the database tables
        storage.init_database()  # Ensure tables exist
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
            failed_queue = storage.get_failed_queue_entries()
            dead_letters = storage.get_dead_letters()
            if failed_queue:
                logger.info(f"Failed queue has {len(failed_queue)} entries pending retry")
            if dead_letters:
                logger.info(f"Dead letters: {len(dead_letters)} entries")

    try:
        # Process failed queue first (retry previously failed leads)
        if DLQ_ENABLED:
            failed_queue = storage.get_failed_queue_entries()
            if failed_queue:
                logger.info("Processing failed queue...")
                dlq_success, dlq_failed, dlq_errors = process_failed_queue(dry_run=dry_run)
                if dlq_success or dlq_failed:
                    logger.info(f"Failed queue: {dlq_success} retried successfully, {dlq_failed} still failing")

        logger.info("Connecting to Google Sheets API...")
        service = get_google_sheets_service()
        logger.info("Connected")

        new_entries = check_for_new_entries(service, verbose=verbose)
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
    # Use shortest interval among all tenants
    intervals = []
    for tenant in MOMENCE_TENANTS.values():
        schedule = tenant.get('schedule', {})
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
    logger.info(f"Tenants configured: {list(MOMENCE_TENANTS.keys())}")
    if HEALTH_SERVER_ENABLED:
        logger.info(f"Health server: enabled on port {HEALTH_SERVER_PORT}")
    logger.info("=" * 50)

    # Initialize database
    storage.init_database()

    # Start health server if enabled
    metadata = storage.get_tracker_metadata()
    health_server = start_health_server(metadata)

    while not shutdown_handler.should_stop:
        try:
            run_monitor(dry_run=dry_run, verbose=verbose, reset_tracker=False)

            # Run all cleanup tasks periodically (once per monitor run)
            run_cleanup_tasks()

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

    # Graceful shutdown
    logger.info("Shutting down gracefully...")

    # Stop health server
    if health_server:
        try:
            health_server.shutdown()
            logger.info("Health server stopped")
        except Exception as e:
            logger.error(f"Error stopping health server: {e}")

    # Close HTTP session to clean up connections
    try:
        close_session()
        logger.debug("HTTP session closed")
    except Exception as e:
        logger.error(f"Error closing HTTP session: {e}")

    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Lead Sheets Monitor')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Run without sending/saving')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--reset-tracker', '-r', action='store_true', help='Reset tracker')
    parser.add_argument('--daemon', action='store_true', help='Run continuously with dynamic check intervals')

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
        storage.init_database()
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
                print(f"    Tenant: {entry.get('tenant', 'N/A')}")
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
        storage.init_database()
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

    # Initialize database
    storage.init_database()

    if args.daemon:
        run_daemon(dry_run=args.dry_run, verbose=args.verbose)
    else:
        success = run_monitor(
            dry_run=args.dry_run,
            verbose=args.verbose,
            reset_tracker=args.reset_tracker
        )
        exit(0 if success else 1)


if __name__ == '__main__':
    main()
