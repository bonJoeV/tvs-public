#!/usr/bin/env python3
"""
Google Sheets Monitor - Watches for new entries and pushes leads to Momence CRM.
Tracks sent entries to prevent duplicates. Supports multiple tenants (hosts).
"""

import os
import sys
import json
import time
import hashlib
import argparse
import logging
import random
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SENT_TRACKER_FILE = os.getenv('SENT_TRACKER_FILE', './sent_entries.json')
LOG_DIR = os.getenv('LOG_DIR', './logs')
CONFIG_FILE = os.getenv('CONFIG_FILE', './config.json')


def load_config():
    """Load tenants and sheets config from JSON file."""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {'tenants': {}, 'sheets': [], 'schedule': {}}


# Load configuration
_config = load_config()
MOMENCE_TENANTS = _config.get('tenants', {})
SHEETS_CONFIG = _config.get('sheets', [])

# Global settings from config
_settings = _config.get('settings', {})
LOG_RETENTION_DAYS = _settings.get('log_retention_days', 7)
API_TIMEOUT_SECONDS = _settings.get('api_timeout_seconds', 120)
RETRY_MAX_ATTEMPTS = _settings.get('retry_max_attempts', 3)
RETRY_BASE_DELAY = _settings.get('retry_base_delay_seconds', 2.0)

# Day name to number mapping
DAY_NAME_TO_NUM = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}


def parse_business_hours(biz_hours_config: dict) -> dict:
    """Parse business hours config into day number -> (open, close) tuple."""
    result = {}
    for day_name, hours in biz_hours_config.items():
        day_num = DAY_NAME_TO_NUM.get(day_name.lower())
        if day_num is not None:
            result[day_num] = tuple(hours) if hours else None
    return result


def setup_logging():
    """Configure logging with YYYYMMDD.log format and 7-day retention."""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Use YYYYMMDD.log format
    today = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f'{today}.log'

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File handler - use basic FileHandler since we name by date
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Clean up old log files
    cleanup_old_logs(log_dir, keep_days=LOG_RETENTION_DAYS)

    return logging.getLogger(__name__)


def cleanup_old_logs(log_dir: Path, keep_days: int = 7):
    """Remove log files older than keep_days."""
    cutoff_date = datetime.now() - timedelta(days=keep_days)

    for log_file in log_dir.glob('*.log'):
        # Parse YYYYMMDD from filename
        try:
            date_str = log_file.stem
            file_date = datetime.strptime(date_str, '%Y%m%d')
            if file_date < cutoff_date:
                log_file.unlink()
                print(f"Removed old log file: {log_file.name}")
        except ValueError:
            # Skip files that don't match YYYYMMDD format
            pass


# Initialize logger
logger = setup_logging()


# Browser signatures for rotating user agents
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


def get_browser_headers() -> dict:
    """Get randomized browser headers to avoid detection."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": random.choice(USER_AGENTS),
        "Origin": "https://www.momence.com",
        "Referer": "https://www.momence.com/",
    }


# ============================================================================
# Momence Lead Creation
# ============================================================================

def get_tenant_config(tenant_name: str) -> Optional[Dict[str, str]]:
    """Get tenant configuration by name."""
    return MOMENCE_TENANTS.get(tenant_name)


def create_momence_lead(lead_data: Dict[str, Any], tenant_name: str, dry_run: bool = False) -> Optional[Dict]:
    """
    Create a lead in Momence using the Customer Leads API.

    Endpoint: POST https://api.momence.com/integrations/customer-leads/{hostId}/collect
    """
    tenant = get_tenant_config(tenant_name)
    if not tenant:
        logger.error(f"Tenant '{tenant_name}' not found in MOMENCE_TENANTS config")
        return None

    host_id = tenant.get('host_id')
    token = tenant.get('token')

    if not host_id or not token:
        logger.error(f"Tenant '{tenant_name}' missing host_id or token")
        return None

    if dry_run:
        logger.info(f"[DRY RUN] Would create Momence lead for tenant '{tenant_name}': {json.dumps(lead_data, indent=2)}")
        return {"dry_run": True}

    lead_source_id = lead_data.get('leadSourceId')
    if not lead_source_id:
        logger.error("No leadSourceId in lead data")
        return None

    try:
        url = f"https://api.momence.com/integrations/customer-leads/{host_id}/collect"

        payload = {
            "token": token,
            "email": lead_data.get('email', ''),
            "firstName": lead_data.get('firstName', ''),
            "lastName": lead_data.get('lastName', ''),
            "sourceId": lead_source_id,
        }

        if lead_data.get('phoneNumber'):
            payload["phoneNumber"] = lead_data['phoneNumber']
        if lead_data.get('zipCode'):
            payload["zipCode"] = lead_data['zipCode']
        if lead_data.get('discoveryAnswer'):
            payload["discoveryAnswer"] = lead_data['discoveryAnswer']

        response = requests.post(url, headers=get_browser_headers(), json=payload, timeout=30)
        response.raise_for_status()

        logger.info(f"Created Momence lead for tenant '{tenant_name}': {lead_data.get('email')}")
        return response.json() if response.text else {"success": True}

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create Momence lead for tenant '{tenant_name}': {e}")
        return None


def build_momence_lead_data(headers: list, row: list, sheet_config: dict) -> Optional[Dict[str, Any]]:
    """Build Momence lead data from sheet row."""
    data = {}
    for i, value in enumerate(row):
        if i < len(headers) and value:
            data[headers[i].lower()] = value

    lead_source_id = sheet_config.get('lead_source_id')
    if not lead_source_id:
        logger.warning(f"No lead_source_id configured for sheet: {sheet_config.get('name')}")
        return None

    email = data.get('email')
    if not email:
        logger.warning("Cannot create lead without email")
        return None

    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')

    phone = data.get('phone_number', '')
    if phone.startswith('p:'):
        phone = phone[2:]

    lead_data = {
        "leadSourceId": lead_source_id,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
    }

    if phone:
        lead_data["phoneNumber"] = phone
    if data.get('zip_code') or data.get('zipcode'):
        lead_data["zipCode"] = data.get('zip_code') or data.get('zipcode')
    if data.get('discovery_answer') or data.get('discoveryanswer'):
        lead_data["discoveryAnswer"] = data.get('discovery_answer') or data.get('discoveryanswer')

    return lead_data


# ============================================================================
# Google Sheets Functions
# ============================================================================

def retry_with_backoff(func, max_retries: int = None, base_delay: float = None):
    """Execute a function with exponential backoff retry logic."""
    if max_retries is None:
        max_retries = RETRY_MAX_ATTEMPTS
    if base_delay is None:
        base_delay = RETRY_BASE_DELAY
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except (TimeoutError, ConnectionError, HttpError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed: {e}")
    raise last_exception


def get_sheet_name_by_gid(service, spreadsheet_id: str, gid: str) -> Optional[str]:
    """Get the actual sheet name from its gid."""
    try:
        def fetch():
            return service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

        spreadsheet = retry_with_backoff(fetch)
        for sheet in spreadsheet.get('sheets', []):
            if str(sheet['properties']['sheetId']) == gid:
                return sheet['properties']['title']
        return None
    except (HttpError, TimeoutError) as e:
        logger.error(f"Error getting sheet name: {e}")
        return None


def get_google_sheets_service():
    """Create and return Google Sheets API service with timeout."""
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp

    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable not set")

    creds_data = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)

    # Create http with configurable timeout and authorize it
    http = httplib2.Http(timeout=API_TIMEOUT_SECONDS)
    authed_http = AuthorizedHttp(credentials, http=http)

    return build('sheets', 'v4', http=authed_http, cache_discovery=False)


def fetch_sheet_data(service, spreadsheet_id: str, sheet_name: str) -> list:
    """Fetch all data from a specific sheet."""
    try:
        def fetch():
            return service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_name}'!A:Z"
            ).execute()

        result = retry_with_backoff(fetch)
        return result.get('values', [])
    except (HttpError, TimeoutError) as e:
        logger.error(f"Error fetching sheet data: {e}")
        return []


# ============================================================================
# Tracker Functions
# ============================================================================

def load_sent_tracker() -> dict:
    """Load the tracker of previously sent entries."""
    tracker_path = Path(SENT_TRACKER_FILE)
    if tracker_path.exists():
        try:
            with open(tracker_path, 'r') as f:
                data = json.load(f)
                # Ensure location_counts exists for backwards compatibility
                if 'location_counts' not in data:
                    data['location_counts'] = {}
                if 'cache_built_at' not in data:
                    data['cache_built_at'] = datetime.now().isoformat()
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load tracker file: {e}. Starting fresh.")
    return {'sent_hashes': [], 'last_check': None, 'location_counts': {}, 'cache_built_at': datetime.now().isoformat()}


def save_sent_tracker(tracker: dict):
    """Save the tracker of sent entries."""
    tracker_path = Path(SENT_TRACKER_FILE)
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tracker_path, 'w') as f:
        json.dump(tracker, f, indent=2, default=str)
    logger.info(f"Tracker saved with {len(tracker['sent_hashes'])} entries")


def generate_row_hash(sheet_id: str, gid: str, row_index: int, row_data: list) -> str:
    """Generate a unique hash for a row to track if it's been sent."""
    content = f"{sheet_id}:{gid}:{row_index}:{json.dumps(row_data)}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# Main Processing
# ============================================================================

def check_for_new_entries(service, tracker: dict, verbose: bool = False, check_all_tenants: bool = False) -> tuple[list, dict]:
    """Check all configured sheets for new entries.

    Args:
        service: Google Sheets API service
        tracker: Tracker dict for sent entries
        verbose: Enable verbose logging
        check_all_tenants: If True, check all sheets regardless of business hours.
                          If False (default), only check sheets for tenants in business hours.
    """
    new_entries = []

    for sheet_config in SHEETS_CONFIG:
        spreadsheet_id = sheet_config['spreadsheet_id']
        gid = sheet_config['gid']
        tenant = sheet_config.get('tenant')

        if not tenant:
            logger.warning(f"Sheet '{sheet_config.get('name')}' has no tenant configured, skipping")
            continue

        # Skip sheets for tenants outside business hours (unless check_all_tenants is True)
        if not check_all_tenants and not is_business_hours_for_tenant(tenant):
            if verbose:
                logger.info(f"Skipping sheet '{sheet_config.get('name')}' - tenant '{tenant}' is outside business hours")
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

            row_hash = generate_row_hash(spreadsheet_id, gid, row_index, row)

            if row_hash not in tracker['sent_hashes']:
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

    return new_entries, tracker


def process_new_entries(new_entries: list, tracker: dict, dry_run: bool = False) -> dict:
    """Process new entries: push to Momence."""
    if not new_entries:
        logger.info("No new entries to process")
        return tracker

    logger.info(f"Processing {len(new_entries)} new entries")

    for entry in new_entries:
        location = entry['sheet_config'].get('name', entry['tenant'])

        lead_data = build_momence_lead_data(
            entry['headers'],
            entry['data'],
            entry['sheet_config']
        )
        if lead_data:
            result = create_momence_lead(lead_data, entry['tenant'], dry_run=dry_run)
            if result:
                # Mark as processed and increment location count
                if entry['hash'] not in tracker['sent_hashes']:
                    tracker['sent_hashes'].append(entry['hash'])
                    tracker['location_counts'][location] = tracker['location_counts'].get(location, 0) + 1
        else:
            # Still mark as processed to avoid retrying
            if entry['hash'] not in tracker['sent_hashes']:
                tracker['sent_hashes'].append(entry['hash'])
                tracker['location_counts'][location] = tracker['location_counts'].get(location, 0) + 1

    tracker['last_check'] = datetime.now().isoformat()
    return tracker


def log_location_counts(tracker: dict):
    """Log cumulative location counts since cache was built."""
    location_counts = tracker.get('location_counts', {})
    cache_built_at = tracker.get('cache_built_at', 'unknown')

    if not location_counts:
        logger.info("Location counts: No entries processed yet")
        return

    logger.info(f"Cumulative location counts (since {cache_built_at}):")
    total = 0
    for location, count in sorted(location_counts.items()):
        logger.info(f"  {location}: {count}")
        total += count
    logger.info(f"  TOTAL: {total}")


def run_monitor(dry_run: bool = False, verbose: bool = False, reset_tracker: bool = False):
    """Main monitoring function - single run."""
    logger.info("=" * 50)
    logger.info(f"Lead Sheets Monitor (dry_run={dry_run})")
    logger.info(f"Tenants configured: {list(MOMENCE_TENANTS.keys())}")
    logger.info("=" * 50)

    if reset_tracker:
        logger.warning("Resetting tracker - all entries will be treated as new!")
        tracker = {'sent_hashes': [], 'last_check': None, 'location_counts': {}, 'cache_built_at': datetime.now().isoformat()}
    else:
        tracker = load_sent_tracker()
        logger.info(f"Loaded tracker with {len(tracker['sent_hashes'])} entries")

    try:
        logger.info("Connecting to Google Sheets API...")
        service = get_google_sheets_service()
        logger.info("Connected")

        new_entries, tracker = check_for_new_entries(service, tracker, verbose=verbose)
        tracker = process_new_entries(new_entries, tracker, dry_run=dry_run)

        if not dry_run:
            save_sent_tracker(tracker)
        else:
            logger.info("[DRY RUN] Tracker not saved")

        # Log cumulative location counts
        log_location_counts(tracker)

        logger.info("Monitor run completed")
        return True

    except Exception as e:
        logger.exception(f"Monitor run failed: {e}")
        return False


def is_business_hours_for_tenant(tenant_name: str) -> bool:
    """Check if current time is within business hours for a tenant."""
    tenant = MOMENCE_TENANTS.get(tenant_name, {})
    schedule = tenant.get('schedule', {})
    biz_hours_config = schedule.get('business_hours', {})
    business_hours = parse_business_hours(biz_hours_config)

    if not business_hours:
        return True  # No schedule defined, assume always business hours

    now = datetime.now()
    day_of_week = now.weekday()  # 0=Monday, 6=Sunday
    hours = business_hours.get(day_of_week)

    if hours is None:
        return False  # Closed today

    open_hour, close_hour = hours
    return open_hour <= now.hour < close_hour


def get_check_interval() -> tuple[int, list[str]]:
    """Get the appropriate check interval based on which tenants are in business hours.

    Returns:
        tuple: (interval_minutes, list_of_active_tenant_names)
    """
    active_tenants = []
    active_intervals = []

    for tenant_name, tenant in MOMENCE_TENANTS.items():
        schedule = tenant.get('schedule', {})
        if is_business_hours_for_tenant(tenant_name):
            active_tenants.append(tenant_name)
            active_intervals.append(schedule.get('check_interval_biz_hours', 5))

    if active_tenants:
        # Use shortest interval among active tenants
        return min(active_intervals), active_tenants
    else:
        # All tenants off-hours: use shortest off-hours interval
        off_interval = 30  # default
        for tenant in MOMENCE_TENANTS.values():
            schedule = tenant.get('schedule', {})
            off_interval = min(off_interval, schedule.get('check_interval_off_hours', 30))
        return off_interval, []


def run_daemon(dry_run: bool = False, verbose: bool = False):
    """Run monitor continuously with dynamic interval based on business hours.

    Only checks sheets for tenants that are currently in business hours.
    This saves API calls when some tenants are closed.
    """
    logger.info("=" * 50)
    logger.info("Starting Lead Sheets Monitor Daemon")
    logger.info(f"Log directory: {LOG_DIR}")
    logger.info(f"Tenants configured: {list(MOMENCE_TENANTS.keys())}")
    for tenant_name, tenant in MOMENCE_TENANTS.items():
        schedule = tenant.get('schedule', {})
        logger.info(f"  {tenant_name}: biz={schedule.get('check_interval_biz_hours', 5)}min, off={schedule.get('check_interval_off_hours', 30)}min")
    logger.info("Per-tenant checking enabled: only active tenant sheets will be checked")
    logger.info("=" * 50)

    while True:
        try:
            run_monitor(dry_run=dry_run, verbose=verbose, reset_tracker=False)
        except Exception as e:
            logger.exception(f"Error during monitor run: {e}")

        interval_minutes, active_tenants = get_check_interval()
        if active_tenants:
            biz_status = f"business hours: {', '.join(active_tenants)}"
        else:
            biz_status = "off hours (all tenants)"
        logger.info(f"Next check in {interval_minutes} minutes ({biz_status})...")
        time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description='Lead Sheets Monitor')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Run without sending/saving')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--reset-tracker', '-r', action='store_true', help='Reset tracker')
    parser.add_argument('--daemon', action='store_true', help='Run continuously with dynamic check intervals')

    args = parser.parse_args()

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
