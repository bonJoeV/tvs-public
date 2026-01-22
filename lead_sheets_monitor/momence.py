"""
Momence API client for Lead Sheets Monitor.
Handles creating leads in Momence CRM.
"""

import json
import logging
import requests
from typing import Optional, Dict, Any

from config import (
    get_host_config, DEFAULT_REQUEST_TIMEOUT_SECONDS,
    RESPONSE_BODY_TRUNCATE_CHARS, RESPONSE_BODY_LOG_CHARS
)
from utils import (
    utc_now, is_valid_email, get_api_headers,
    extract_diagnostic_headers, categorize_error, logger
)
from sheets import retry_with_backoff


# Module-level session for connection pooling
# This improves performance by reusing TCP connections
_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    """Get or create a reusable requests session for connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0  # We handle retries ourselves
        )
        _session.mount('https://', adapter)
        _session.mount('http://', adapter)
    return _session


def close_session():
    """Close the session (call on application shutdown)."""
    global _session
    if _session is not None:
        _session.close()
        _session = None


def create_momence_lead(lead_data: Dict[str, Any], host_name: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Create a lead in Momence using the Customer Leads API.

    Endpoint: POST https://api.momence.com/integrations/customer-leads/{hostId}/collect

    Args:
        lead_data: Dictionary containing lead information (email, firstName, lastName, etc.)
        host_name: Name of the Momence host configuration to use
        dry_run: If True, log the action without making API call

    Returns:
        Dict with 'success' bool and either result data or 'error' details including response headers
    """
    host_config = get_host_config(host_name)
    if not host_config:
        logger.error(f"Momence host '{host_name}' not found in MOMENCE_HOSTS config")
        return {'success': False, 'error': {'type': 'config_error', 'message': f"Momence host '{host_name}' not found"}}

    host_id = host_config.get('host_id')

    # Try to get token from Secret Manager first (on Cloud Run), then fall back to config
    token = None
    try:
        from secret_manager import get_momence_token
        token = get_momence_token(host_name)
    except ImportError:
        pass
    if not token:
        token = host_config.get('token')

    if not host_id or not token:
        logger.error(f"Momence host '{host_name}' missing host_id or token")
        return {'success': False, 'error': {'type': 'config_error', 'message': f"Momence host '{host_name}' missing credentials"}}

    # Validate email format before making API call
    email = lead_data.get('email', '')
    if not is_valid_email(email):
        logger.warning(f"Invalid email format: '{email}' - skipping API call")
        return {'success': False, 'error': {'type': 'validation_error', 'message': f"Invalid email format: '{email}'"}}

    lead_source_id = lead_data.get('leadSourceId')
    if not lead_source_id:
        logger.error("No leadSourceId in lead data")
        return {'success': False, 'error': {'type': 'validation_error', 'message': 'No leadSourceId in lead data'}}

    url = f"https://api.momence.com/integrations/customer-leads/{host_id}/collect"

    # Build payload per Momence API docs:
    # - token: REQUIRED - goes in body, not header
    # - sourceId: optional, integer
    # - email/phoneNumber: at least one required
    # - firstName, lastName: optional
    try:
        source_id_int = int(lead_source_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid leadSourceId '{lead_source_id}' - must be an integer")
        return {
            'success': False,
            'error': {
                'type': 'validation_error',
                'message': f"Invalid leadSourceId '{lead_source_id}' - must be an integer"
            }
        }

    payload = {
        "token": token,  # Required - identifies the account
        "sourceId": source_id_int,
        "email": lead_data.get('email', ''),
        "firstName": lead_data.get('firstName', ''),
        "lastName": lead_data.get('lastName', ''),
    }

    if lead_data.get('phoneNumber'):
        payload["phoneNumber"] = lead_data['phoneNumber']

    if dry_run:
        # Don't log token in dry run output
        safe_payload = {k: v for k, v in payload.items() if k != 'token'}
        safe_payload['token'] = '***'
        logger.info(f"[DRY RUN] Would POST to {url}")
        logger.info(f"[DRY RUN] Payload: {json.dumps(safe_payload, indent=2)}")
        return {'success': True, 'dry_run': True}

    # Store last response and timing for error reporting
    last_response = None
    request_start_time = None
    request_duration_ms = None
    # Simple headers - token is in body per Momence docs
    request_headers = get_api_headers()

    def make_request():
        nonlocal last_response, request_start_time, request_duration_ms
        request_start_time = utc_now()

        # Prepare the request
        req = requests.Request('POST', url, headers=request_headers, json=payload)
        prepared = req.prepare()

        # Log request details at DEBUG level only (verbose)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request: {prepared.method} {prepared.url}")
            # Mask token in headers for debug logging
            safe_headers = {k: ('***' if 'token' in k.lower() else v) for k, v in prepared.headers.items()}
            logger.debug(f"  Headers: {safe_headers}")

        # Send the prepared request using reusable session
        session = get_session()
        response = session.send(prepared, timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS)
        request_duration_ms = int((utc_now() - request_start_time).total_seconds() * 1000)
        last_response = response

        # Log response summary at DEBUG level
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Response: HTTP {response.status_code} in {request_duration_ms}ms")

        # Raise on 5xx for retry (server errors are transient)
        if response.status_code >= 500:
            raise requests.exceptions.HTTPError(f"Server error: HTTP {response.status_code}", response=response)
        return response

    # Build debug context for logging (mask token in payload)
    debug_payload = {k: ('***' if k == 'token' else v) for k, v in payload.items()}

    try:
        response = retry_with_backoff(make_request)

        if response.status_code >= 400:
            all_response_headers = dict(response.headers)
            diag_headers = extract_diagnostic_headers(all_response_headers)
            error_category, is_retryable = categorize_error(response.status_code, all_response_headers, response.text)
            cf_ray = all_response_headers.get('cf-ray', all_response_headers.get('CF-Ray', 'N/A'))

            # Build comprehensive error info for support
            error_info = {
                'type': error_category,
                'is_retryable': is_retryable,
                'status_code': response.status_code,
                'status_text': response.reason,
                'cf_ray': cf_ray,
                'message': f"{error_category}: HTTP {response.status_code}",
                # Request details
                'request_url': url,
                'request_method': 'POST',
                'request_headers': {k: v for k, v in request_headers.items()},
                'request_payload': debug_payload,
                'request_content_type': request_headers.get('Content-Type', 'application/json'),
                'request_timestamp': request_start_time.isoformat() if request_start_time else None,
                'request_duration_ms': request_duration_ms,
                # Response details (ALL headers for support)
                'response_headers': all_response_headers,
                'response_body': response.text[:RESPONSE_BODY_TRUNCATE_CHARS] if response.text else '(empty)',
                'response_content_length': all_response_headers.get('Content-Length', '0'),
                'response_content_type': all_response_headers.get('Content-Type', 'unknown'),
                # Lead context
                'lead_email': lead_data.get('email'),
                'lead_sheet': lead_data.get('sheetName'),
                'momence_host': host_name,
                'host_id': host_id,
                'source_id': lead_source_id,
            }

            retry_hint = " (retryable)" if is_retryable else " (permanent - will not retry)"
            logger.error(f"Momence API error for host '{host_name}': {error_category}{retry_hint}")
            logger.error(f"  Status: HTTP {response.status_code} {response.reason} | CF-Ray: {cf_ray}")
            logger.error(f"  Lead: {lead_data.get('email')} | Sheet: {lead_data.get('sheetName')}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"  Request Headers: {json.dumps(error_info['request_headers'])}")
                logger.debug(f"  Request Payload: {json.dumps(debug_payload)}")
                logger.debug(f"  Response Headers: {json.dumps(all_response_headers)}")
                logger.debug(f"  Response Body: {error_info['response_body']}")
            return {
                'success': False,
                'error': error_info
            }

        logger.info(f"Created Momence lead for host '{host_name}': {lead_data.get('email')} (Studio: {lead_data.get('sheetName')}, sourceId: {lead_source_id}) [{request_duration_ms}ms]")
        return {'success': True, 'data': response.json() if response.text else {}}

    except (requests.exceptions.RequestException, TimeoutError, ConnectionError) as e:
        # All retries exhausted
        error_time = utc_now()
        exception_type = type(e).__name__
        exception_details = str(e)

        diag_headers = {}
        status_code = None
        response_body = ''
        cf_ray = 'N/A'
        error_category = 'request_exception'
        is_retryable = True  # Network errors are generally retryable

        if last_response is not None:
            diag_headers = extract_diagnostic_headers(dict(last_response.headers))
            status_code = last_response.status_code
            response_body = last_response.text[:RESPONSE_BODY_TRUNCATE_CHARS]
            cf_ray = diag_headers.get('cf-ray', diag_headers.get('CF-Ray', 'N/A'))
            error_category, is_retryable = categorize_error(status_code, dict(last_response.headers), last_response.text)

        retry_hint = " (retryable)" if is_retryable else " (permanent)"
        logger.error(f"Failed to create Momence lead for host '{host_name}': {exception_type}{retry_hint}")
        logger.error(f"  Lead: {lead_data.get('email')} | Sheet: {lead_data.get('sheetName')}")
        if last_response is not None:
            logger.error(f"  Last Status: HTTP {status_code} | CF-Ray: {cf_ray}")
        else:
            logger.error(f"  No response received (connection failed or timed out)")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"  Exception: {exception_type}: {exception_details}")
            logger.debug(f"  URL: {url}")
            logger.debug(f"  Request Payload: {json.dumps(debug_payload)}")
            if last_response is not None:
                logger.debug(f"  Response Headers: {json.dumps(diag_headers)}")
                logger.debug(f"  Response Body: {response_body[:RESPONSE_BODY_LOG_CHARS]}")

        return {
            'success': False,
            'error': {
                'type': error_category,
                'is_retryable': is_retryable,
                'exception_type': exception_type,
                'status_code': status_code,
                'cf_ray': cf_ray,
                'response_headers': diag_headers,
                'response_body': response_body,
                'message': f"{exception_type}: {exception_details}",
                'request_url': url,
                'request_payload': debug_payload,
                'request_timestamp': request_start_time.isoformat() if request_start_time else error_time.isoformat(),
                'request_duration_ms': request_duration_ms
            }
        }
