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
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import TimedRotatingFileHandler

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
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '15'))
CONFIG_FILE = os.getenv('CONFIG_FILE', './config.json')


def load_config():
    """Load tenants and sheets config from JSON file."""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {'tenants': {}, 'sheets': []}


# Load configuration
_config = load_config()
MOMENCE_TENANTS = _config.get('tenants', {})
SHEETS_CONFIG = _config.get('sheets', [])


def setup_logging():
    """Configure logging with daily rotation and 7-day retention."""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / 'monitor.log'

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File handler with daily rotation, keep 7 days
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
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

    return logging.getLogger(__name__)


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

def get_sheet_name_by_gid(service, spreadsheet_id: str, gid: str) -> Optional[str]:
    """Get the actual sheet name from its gid."""
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        for sheet in spreadsheet.get('sheets', []):
            if str(sheet['properties']['sheetId']) == gid:
                return sheet['properties']['title']
        return None
    except HttpError as e:
        logger.error(f"Error getting sheet name: {e}")
        return None


def get_google_sheets_service():
    """Create and return Google Sheets API service."""
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable not set")

    creds_data = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
    return build('sheets', 'v4', credentials=credentials, cache_discovery=False)


def fetch_sheet_data(service, spreadsheet_id: str, sheet_name: str) -> list:
    """Fetch all data from a specific sheet."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A:Z"
        ).execute()
        return result.get('values', [])
    except HttpError as e:
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
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load tracker file: {e}. Starting fresh.")
    return {'sent_hashes': [], 'last_check': None}


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

def check_for_new_entries(service, tracker: dict, verbose: bool = False) -> tuple[list, dict]:
    """Check all configured sheets for new entries."""
    new_entries = []

    for sheet_config in SHEETS_CONFIG:
        spreadsheet_id = sheet_config['spreadsheet_id']
        gid = sheet_config['gid']
        tenant = sheet_config.get('tenant')

        if not tenant:
            logger.warning(f"Sheet '{sheet_config.get('name')}' has no tenant configured, skipping")
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
        lead_data = build_momence_lead_data(
            entry['headers'],
            entry['data'],
            entry['sheet_config']
        )
        if lead_data:
            result = create_momence_lead(lead_data, entry['tenant'], dry_run=dry_run)
            if result:
                # Mark as processed
                if entry['hash'] not in tracker['sent_hashes']:
                    tracker['sent_hashes'].append(entry['hash'])
        else:
            # Still mark as processed to avoid retrying
            if entry['hash'] not in tracker['sent_hashes']:
                tracker['sent_hashes'].append(entry['hash'])

    tracker['last_check'] = datetime.now().isoformat()
    return tracker


def run_monitor(dry_run: bool = False, verbose: bool = False, reset_tracker: bool = False):
    """Main monitoring function - single run."""
    logger.info("=" * 50)
    logger.info(f"Lead Sheets Monitor (dry_run={dry_run})")
    logger.info(f"Tenants configured: {list(MOMENCE_TENANTS.keys())}")
    logger.info("=" * 50)

    if reset_tracker:
        logger.warning("Resetting tracker - all entries will be treated as new!")
        tracker = {'sent_hashes': [], 'last_check': None}
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

        logger.info("Monitor run completed")
        return True

    except Exception as e:
        logger.exception(f"Monitor run failed: {e}")
        return False


def run_daemon(dry_run: bool = False, verbose: bool = False):
    """Run monitor continuously with configured interval."""
    interval_minutes = CHECK_INTERVAL_MINUTES
    interval_seconds = interval_minutes * 60

    logger.info("=" * 50)
    logger.info("Starting Lead Sheets Monitor Daemon")
    logger.info(f"Check interval: {interval_minutes} minutes")
    logger.info(f"Log directory: {LOG_DIR}")
    logger.info(f"Tenants configured: {list(MOMENCE_TENANTS.keys())}")
    logger.info("=" * 50)

    while True:
        try:
            run_monitor(dry_run=dry_run, verbose=verbose, reset_tracker=False)
        except Exception as e:
            logger.exception(f"Error during monitor run: {e}")

        logger.info(f"Next check in {interval_minutes} minutes...")
        time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description='Lead Sheets Monitor')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Run without sending/saving')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--reset-tracker', '-r', action='store_true', help='Reset tracker')
    parser.add_argument('--daemon', action='store_true', help='Run continuously with CHECK_INTERVAL_MINUTES')

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
