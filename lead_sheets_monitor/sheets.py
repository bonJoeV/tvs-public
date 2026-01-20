"""
Google Sheets API functions for Lead Sheets Monitor.
Handles fetching data, parsing entries, and discovering tabs.
"""

import os
import re
import json
import time
import random
from typing import Optional, Dict, Any, List, Tuple

import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    SCOPES, API_TIMEOUT_SECONDS, RETRY_MAX_ATTEMPTS, RETRY_BASE_DELAY,
    get_enabled_sheets
)
from utils import normalize_phone, logger, compute_entry_hash

# Facebook Lead Ads expected headers
FB_LEAD_HEADERS = {'id', 'created_time', 'ad_id', 'ad_name'}

# Valid spreadsheet ID pattern: alphanumeric, hyphens, and underscores (typically 44 chars but can vary)
SPREADSHEET_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{20,100}$')


def validate_spreadsheet_id(spreadsheet_id: str) -> bool:
    """
    Validate that a spreadsheet ID is properly formatted.

    Google Sheets IDs are typically 44 alphanumeric characters with hyphens/underscores.
    This prevents injection of invalid IDs that could cause API errors.

    Args:
        spreadsheet_id: The ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not spreadsheet_id or not isinstance(spreadsheet_id, str):
        return False
    return bool(SPREADSHEET_ID_PATTERN.match(spreadsheet_id))


class NonRetryableError(Exception):
    """Exception for errors that should not be retried (e.g., 401, 403, 404)."""
    def __init__(self, message: str, status_code: int = None, original_error: Exception = None):
        super().__init__(message)
        self.status_code = status_code
        self.original_error = original_error


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable (transient) or permanent.

    Retryable errors: timeouts, connection issues, rate limits (429), server errors (5xx)
    Non-retryable errors: auth errors (401), forbidden (403), not found (404), bad request (400)

    Args:
        error: The exception to check

    Returns:
        True if the error should be retried, False otherwise
    """
    # HttpError from Google API
    if isinstance(error, HttpError):
        status = error.resp.status if hasattr(error, 'resp') else None
        if status:
            # Don't retry client errors (except 429)
            if status == 429:
                return True  # Rate limited - retry with backoff
            if 400 <= status < 500:
                return False  # Client errors are permanent
            if status >= 500:
                return True  # Server errors are transient
        return True  # Default to retry for unknown status

    # requests library errors
    if isinstance(error, requests.exceptions.RequestException):
        if isinstance(error, requests.exceptions.HTTPError):
            response = getattr(error, 'response', None)
            if response is not None:
                status = response.status_code
                if status == 429:
                    return True  # Rate limited
                if 400 <= status < 500:
                    return False  # Client errors are permanent
                if status >= 500:
                    return True  # Server errors are transient
        # Connection/timeout errors are transient
        return True

    # Timeouts and connection errors are transient
    if isinstance(error, (TimeoutError, ConnectionError)):
        return True

    # Default to retry for unknown errors
    return True


def get_retry_after(error: Exception) -> Optional[float]:
    """
    Extract Retry-After header value from error response if available.

    Args:
        error: The exception to check

    Returns:
        Number of seconds to wait, or None if not available
    """
    response = None

    if isinstance(error, HttpError) and hasattr(error, 'resp'):
        response = error.resp
    elif isinstance(error, requests.exceptions.RequestException):
        response = getattr(error, 'response', None)

    if response:
        retry_after = None
        if hasattr(response, 'headers'):
            retry_after = response.headers.get('Retry-After') or response.headers.get('retry-after')
        elif hasattr(response, 'get'):
            retry_after = response.get('retry-after')

        if retry_after:
            try:
                return float(retry_after)
            except (ValueError, TypeError):
                pass

    return None


def retry_with_backoff(func, max_retries: int = None, base_delay: float = None):
    """
    Execute a function with exponential backoff retry logic.

    Distinguishes between retryable (transient) and non-retryable (permanent) errors.
    Respects Retry-After headers when available.

    Args:
        func: Callable to execute
        max_retries: Maximum number of retry attempts (default: RETRY_MAX_ATTEMPTS)
        base_delay: Base delay in seconds for backoff calculation (default: RETRY_BASE_DELAY)

    Returns:
        Result from successful function call

    Raises:
        NonRetryableError: For permanent errors (401, 403, 404, etc.)
        Last exception: If all retries exhausted for transient errors
    """
    if max_retries is None:
        max_retries = RETRY_MAX_ATTEMPTS
    if base_delay is None:
        base_delay = RETRY_BASE_DELAY

    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except (TimeoutError, ConnectionError, HttpError, requests.exceptions.RequestException) as e:
            last_exception = e

            # Check if this is a permanent error
            if not is_retryable_error(e):
                status_code = None
                if isinstance(e, HttpError) and hasattr(e, 'resp'):
                    status_code = e.resp.status
                elif isinstance(e, requests.exceptions.HTTPError):
                    response = getattr(e, 'response', None)
                    if response is not None:
                        status_code = response.status_code

                logger.error(f"Non-retryable error (HTTP {status_code}): {e}")
                raise NonRetryableError(str(e), status_code=status_code, original_error=e)

            # For retryable errors, continue with backoff
            if attempt < max_retries - 1:
                # Check for Retry-After header
                retry_after = get_retry_after(e)
                if retry_after and retry_after < 300:  # Cap at 5 minutes
                    delay = retry_after
                else:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)

                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed: {e}")

    raise last_exception


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


def get_sheet_name_by_gid(service, spreadsheet_id: str, gid: str) -> Optional[str]:
    """Get the actual sheet name from its gid."""
    # Validate spreadsheet ID before API call
    if not validate_spreadsheet_id(spreadsheet_id):
        logger.error(f"Invalid spreadsheet ID format: {spreadsheet_id[:20]}...")
        return None

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


def fetch_sheet_data(service, spreadsheet_id: str, sheet_name: str) -> list:
    """
    Fetch all data from a specific sheet.

    Uses the entire sheet range without column limits to avoid data loss
    for sheets with more than 26 columns.

    Args:
        service: Google Sheets API service
        spreadsheet_id: Google Sheets spreadsheet ID
        sheet_name: Name of the sheet tab

    Returns:
        List of rows (each row is a list of cell values)
    """
    # Validate spreadsheet ID before API call
    if not validate_spreadsheet_id(spreadsheet_id):
        logger.error(f"Invalid spreadsheet ID format: {spreadsheet_id[:20]}...")
        return []

    try:
        def fetch():
            # Use sheet name only (no column range) to fetch all data
            # This handles sheets with more than 26 columns (beyond column Z)
            return service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_name}'"
            ).execute()

        result = retry_with_backoff(fetch)
        return result.get('values', [])
    except (HttpError, TimeoutError) as e:
        logger.error(f"Error fetching sheet data: {e}")
        return []


def parse_spreadsheet_url(url: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Parse a Google Sheets URL to extract spreadsheet_id and optional gid.

    Supports formats:
    - https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=GID
    - https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
    - Just the spreadsheet ID

    Returns:
        Tuple of (spreadsheet_id, gid) or None if invalid
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # If it's just an ID (no slashes), validate and return it
    if '/' not in url and len(url) > 20:
        # Validate the ID format before returning
        if validate_spreadsheet_id(url):
            return (url, None)
        else:
            logger.warning(f"Invalid spreadsheet ID format: {url[:30]}...")
            return None

    # Match Google Sheets URL pattern
    pattern = r'spreadsheets/d/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    if not match:
        return None

    spreadsheet_id = match.group(1)

    # Validate the extracted ID
    if not validate_spreadsheet_id(spreadsheet_id):
        logger.warning(f"Invalid spreadsheet ID extracted from URL: {spreadsheet_id[:30]}...")
        return None

    # Try to extract gid
    gid = None
    gid_match = re.search(r'[#&]gid=(\d+)', url)
    if gid_match:
        gid = gid_match.group(1)

    return (spreadsheet_id, gid)


def discover_fb_lead_tabs(service, spreadsheet_id: str) -> List[Dict[str, Any]]:
    """
    Discover all tabs in a spreadsheet that have Facebook Lead Ads headers.

    Looks for tabs with headers: id, created_time, ad_id, ad_name

    Args:
        service: Google Sheets API service
        spreadsheet_id: Google Sheets spreadsheet ID

    Returns:
        List of dicts with 'name', 'gid', 'row_count' for each matching tab
    """
    # Validate spreadsheet ID before API call
    if not validate_spreadsheet_id(spreadsheet_id):
        logger.error(f"Invalid spreadsheet ID format: {spreadsheet_id[:20]}...")
        return []

    discovered = []

    try:
        # Get spreadsheet metadata (all sheet names and IDs)
        def fetch_metadata():
            return service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

        spreadsheet = retry_with_backoff(fetch_metadata)
        sheets_metadata = spreadsheet.get('sheets', [])

        for sheet_meta in sheets_metadata:
            props = sheet_meta.get('properties', {})
            sheet_name = props.get('title', '')
            sheet_id = str(props.get('sheetId', 0))

            # Fetch first row to check headers
            try:
                def fetch_headers():
                    return service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range=f"'{sheet_name}'!1:1"
                    ).execute()

                result = retry_with_backoff(fetch_headers)
                rows = result.get('values', [])

                if rows:
                    # Normalize headers (lowercase, strip whitespace)
                    headers = {str(h).lower().strip() for h in rows[0]}

                    # Check if this tab has FB Lead headers
                    if FB_LEAD_HEADERS.issubset(headers):
                        # Get row count
                        grid_props = sheet_meta.get('properties', {}).get('gridProperties', {})
                        row_count = grid_props.get('rowCount', 0)

                        discovered.append({
                            'name': sheet_name,
                            'gid': sheet_id,
                            'row_count': row_count,
                            'headers': list(headers)
                        })
                        logger.info(f"Discovered FB Lead tab: {sheet_name} (gid={sheet_id})")

            except (HttpError, TimeoutError) as e:
                logger.warning(f"Could not check headers for sheet '{sheet_name}': {e}")
                continue

    except (HttpError, TimeoutError) as e:
        logger.error(f"Error discovering tabs in spreadsheet: {e}")

    return discovered


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

    phone = normalize_phone(data.get('phone_number', ''))

    sheet_name = sheet_config.get('name', '')

    lead_data = {
        "leadSourceId": lead_source_id,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "sheetName": sheet_name,
    }

    if phone:
        lead_data["phoneNumber"] = phone
    if data.get('zip_code') or data.get('zipcode'):
        lead_data["zipCode"] = data.get('zip_code') or data.get('zipcode')
    if data.get('discovery_answer') or data.get('discoveryanswer'):
        lead_data["discoveryAnswer"] = data.get('discovery_answer') or data.get('discoveryanswer')

    # Extra fields for email notification (not sent to Momence API)
    if data.get('campaign'):
        lead_data["campaign"] = data['campaign']
    if data.get('form'):
        lead_data["form"] = data['form']
    if data.get('created'):
        lead_data["created"] = data['created']
    if data.get('platform'):
        lead_data["platform"] = data['platform']

    return lead_data


def check_for_new_entries(service, tracker: dict, verbose: bool = False) -> Tuple[List[Dict], dict]:
    """
    Check all configured sheets for new entries.

    Args:
        service: Google Sheets API service
        tracker: Tracker dict containing sent_hashes and metadata
        verbose: Enable verbose logging

    Returns:
        Tuple of (new_entries_list, updated_tracker)
    """
    new_entries = []
    enabled_sheets = get_enabled_sheets()

    if not enabled_sheets:
        logger.warning("No sheets configured or all sheets disabled")
        return new_entries, tracker

    for sheet_cfg in enabled_sheets:
        spreadsheet_id = sheet_cfg.get('spreadsheet_id')
        tab_name = sheet_cfg.get('tab_name') or sheet_cfg.get('name')
        gid = sheet_cfg.get('gid')

        if not spreadsheet_id:
            logger.warning(f"Sheet config missing spreadsheet_id: {sheet_cfg}")
            continue

        # Get actual tab name if we have gid but no tab_name
        if gid and not tab_name:
            tab_name = get_sheet_name_by_gid(service, spreadsheet_id, gid)
            if not tab_name:
                logger.warning(f"Could not resolve tab name for gid={gid}")
                continue

        if not tab_name:
            logger.warning(f"Sheet config missing tab_name: {sheet_cfg}")
            continue

        logger.info(f"Checking sheet: {sheet_cfg.get('name', tab_name)}")

        # Fetch sheet data
        rows = fetch_sheet_data(service, spreadsheet_id, tab_name)
        if not rows:
            logger.info(f"  No data in sheet")
            continue

        # First row is headers
        headers = [str(h).lower().strip() for h in rows[0]]
        data_rows = rows[1:]

        logger.info(f"  Found {len(data_rows)} rows")

        # Check each row for new entries
        for row in data_rows:
            if not row:  # Skip empty rows
                continue

            # Build lead data to compute hash
            lead_data = build_momence_lead_data(headers, row, sheet_cfg)
            if not lead_data:
                continue

            # Add created_time for hash computation if available
            created_time_idx = headers.index('created_time') if 'created_time' in headers else -1
            if created_time_idx >= 0 and created_time_idx < len(row):
                lead_data['created_time'] = row[created_time_idx]

            entry_hash = compute_entry_hash(lead_data)

            # Check if we've already processed this entry
            if entry_hash in tracker.get('sent_hashes', set()):
                if verbose:
                    logger.debug(f"  Skipping already processed: {lead_data.get('email')}")
                continue

            # New entry found
            new_entries.append({
                'lead_data': lead_data,
                'tenant': sheet_cfg.get('tenant'),
                'location': sheet_cfg.get('name', tab_name),
                'hash': entry_hash,
                'sheet_config': sheet_cfg
            })
            logger.info(f"  New entry: {lead_data.get('email')}")

    logger.info(f"Total new entries found: {len(new_entries)}")
    return new_entries, tracker
