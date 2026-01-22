"""
Email notification functions for Lead Sheets Monitor.
Handles sending digest emails for leads and errors.
"""

import json
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional

from config import (
    get_host_config, get_sheet_config_by_name, get_smtp_config,
    resolve_email_list, get_email_config, ERROR_BODY_TRUNCATE_CHARS
)
from utils import utc_now, escape_html, logger


# SMTP timeout in seconds
SMTP_TIMEOUT_SECONDS = 30


def send_email(to_addresses: List[str], subject: str, html_body: str) -> bool:
    """Send an HTML email via SMTP."""
    smtp_cfg = get_smtp_config()

    if not smtp_cfg['username'] or not smtp_cfg['password']:
        logger.warning("SMTP credentials not configured, skipping email")
        return False

    if not to_addresses:
        logger.warning("No recipients specified, skipping email")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_cfg['from_address'] or smtp_cfg['username']
        msg['To'] = ', '.join(to_addresses)

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Use timeout to prevent hanging indefinitely
        with smtplib.SMTP(smtp_cfg['host'], smtp_cfg['port'], timeout=SMTP_TIMEOUT_SECONDS) as server:
            if smtp_cfg.get('use_tls', True):
                # Create SSL context for starttls - ensures TLS negotiation respects timeout
                import ssl
                context = ssl.create_default_context()
                server.starttls(context=context)
            server.login(smtp_cfg['username'], smtp_cfg['password'])
            server.sendmail(msg['From'], to_addresses, msg.as_string())

        logger.info(f"Email sent successfully to {to_addresses}")
        return True

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {type(e).__name__}: {e}")
        return False
    except TimeoutError as e:
        logger.error(f"SMTP connection timed out after {SMTP_TIMEOUT_SECONDS}s: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {type(e).__name__}: {e}")
        return False


def build_error_digest_html(errors: List[Dict[str, Any]]) -> str:
    """
    Build a pretty HTML email for error digest (sent to admin).

    Args:
        errors: List of error dictionaries with details

    Returns:
        HTML string for the email body
    """
    timestamp = utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')

    # Group errors by type for summary
    error_types: Dict[str, int] = {}
    error_hosts: Dict[str, int] = {}
    for err in errors:
        err_type = err.get('error_type', 'unknown')
        error_types[err_type] = error_types.get(err_type, 0) + 1
        momence_host = err.get('momence_host', 'Unknown')
        error_hosts[momence_host] = error_hosts.get(momence_host, 0) + 1

    # Build summary stats using list + join (more memory efficient than string concat)
    summary_items_list = []
    for err_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
        badge_color = "#dc2626" if count > 2 else "#f59e0b"
        summary_items_list.append(f"""
        <div style="display: inline-block; margin: 4px;">
            <span style="background: {badge_color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 500;">
                {escape_html(err_type)}: {count}
            </span>
        </div>
        """)
    summary_items = ''.join(summary_items_list)

    # Build error cards using list + join (more memory efficient than string concat)
    error_cards_list = []
    for i, err in enumerate(errors, 1):
        headers_display = escape_html(json.dumps(dict(err.get('response_headers', {})), indent=2)) if err.get('response_headers') else 'N/A'
        payload_display = escape_html(json.dumps(err.get('request_payload', {}), indent=2)) if err.get('request_payload') else 'N/A'
        response_body = escape_html(err.get('response_body', 'N/A')[:ERROR_BODY_TRUNCATE_CHARS])

        # Escape all user-provided data
        lead_email = escape_html(err.get('lead_email', 'N/A'))
        sheet_name = escape_html(err.get('sheet_name', 'N/A'))
        momence_host = escape_html(err.get('momence_host', 'N/A'))
        error_type = escape_html(err.get('error_type', 'N/A'))
        cf_ray = escape_html(err.get('cf_ray', 'N/A'))
        request_url = escape_html(err.get('request_url', 'N/A'))
        status_code = err.get('status_code', 'N/A')
        attempts = err.get('attempts', 1)

        # Color code by error severity
        if status_code and isinstance(status_code, int):
            if status_code >= 500:
                border_color = "#dc2626"
                status_bg = "#fee2e2"
            elif status_code == 429:
                border_color = "#f59e0b"
                status_bg = "#fef3c7"
            elif status_code >= 400:
                border_color = "#ea580c"
                status_bg = "#ffedd5"
            else:
                border_color = "#6366f1"
                status_bg = "#e0e7ff"
        else:
            border_color = "#dc2626"
            status_bg = "#fee2e2"

        error_cards_list.append(f"""
        <div style="background: #fef2f2; border-radius: 8px; padding: 16px; margin-bottom: 16px; border-left: 4px solid {border_color};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span style="color: #64748b; font-size: 11px; font-weight: 600;">#{i}</span>
                    <strong style="color: #1e293b; font-size: 16px; margin-left: 8px;">{lead_email}</strong>
                    <div style="color: #64748b; font-size: 13px; margin-top: 4px;">{sheet_name}</div>
                </div>
                <div style="text-align: right;">
                    <span style="background: {status_bg}; color: {border_color}; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 13px; display: inline-block;">
                        HTTP {status_code}
                    </span>
                    {f'<div style="color: #64748b; font-size: 11px; margin-top: 4px;">Attempt {attempts}</div>' if attempts > 1 else ''}
                </div>
            </div>

            <table style="width: 100%; font-size: 13px; color: #475569; border-collapse: collapse;">
                <tr>
                    <td style="padding: 6px 0; width: 120px; vertical-align: top;"><strong>Momence Host:</strong></td>
                    <td style="padding: 6px 0;">{momence_host}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; vertical-align: top;"><strong>Error Type:</strong></td>
                    <td style="padding: 6px 0;"><code style="background: #e2e8f0; padding: 2px 6px; border-radius: 3px; color: #be185d;">{error_type}</code></td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; vertical-align: top;"><strong>Timestamp:</strong></td>
                    <td style="padding: 6px 0;">{err.get('request_timestamp', err.get('timestamp', 'N/A'))}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; vertical-align: top;"><strong>Duration:</strong></td>
                    <td style="padding: 6px 0;">{err.get('request_duration_ms', 'N/A')}ms</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; vertical-align: top;"><strong>CF-Ray:</strong></td>
                    <td style="padding: 6px 0;"><code style="background: #e2e8f0; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{cf_ray}</code></td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; vertical-align: top;"><strong>URL:</strong></td>
                    <td style="padding: 6px 0; word-break: break-all;"><code style="background: #e2e8f0; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{request_url}</code></td>
                </tr>
            </table>

            <details style="cursor: pointer; margin-top: 12px;">
                <summary style="color: #6366f1; font-weight: 500; font-size: 13px;">Request Payload</summary>
                <pre style="background: #f1f5f9; padding: 10px; border-radius: 6px; font-size: 11px; overflow-x: auto; margin-top: 8px; white-space: pre-wrap;">{payload_display}</pre>
            </details>

            <details style="cursor: pointer; margin-top: 8px;">
                <summary style="color: #6366f1; font-weight: 500; font-size: 13px;">Response Headers</summary>
                <pre style="background: #f1f5f9; padding: 10px; border-radius: 6px; font-size: 11px; overflow-x: auto; margin-top: 8px; white-space: pre-wrap;">{headers_display}</pre>
            </details>

            <details style="cursor: pointer; margin-top: 8px;">
                <summary style="color: #6366f1; font-weight: 500; font-size: 13px;">Response Body (first {ERROR_BODY_TRUNCATE_CHARS} chars)</summary>
                <pre style="background: #f1f5f9; padding: 10px; border-radius: 6px; font-size: 11px; overflow-x: auto; margin-top: 8px; white-space: pre-wrap;">{response_body}</pre>
            </details>
        </div>
        """)
    error_cards = ''.join(error_cards_list)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f8fafc;">
        <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); border-radius: 12px 12px 0 0; padding: 24px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">
                    Lead Monitor Error Report
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">
                    {len(errors)} error(s) detected during processing
                </p>
            </div>

            <!-- Summary Section -->
            <div style="background: #fef2f2; padding: 16px 24px; border-bottom: 1px solid #fecaca;">
                <div style="font-size: 13px; font-weight: 600; color: #991b1b; margin-bottom: 8px;">ERROR SUMMARY</div>
                <div style="margin-bottom: 8px;">{summary_items}</div>
                <div style="font-size: 12px; color: #64748b;">
                    Affected Momence hosts: {', '.join(error_hosts.keys())}
                </div>
            </div>

            <!-- Content -->
            <div style="background: white; padding: 24px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                {error_cards}

                <!-- Quick Actions -->
                <div style="background: #f1f5f9; border-radius: 8px; padding: 16px; margin-top: 16px;">
                    <div style="font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">TROUBLESHOOTING</div>
                    <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #64748b; line-height: 1.8;">
                        <li><strong>429 Rate Limited:</strong> Increase RATE_LIMIT_DELAY in config</li>
                        <li><strong>401/403:</strong> Check API token validity in Momence host config</li>
                        <li><strong>5xx Server Error:</strong> Momence API may be temporarily unavailable</li>
                        <li><strong>Cloudflare Block:</strong> May need to adjust request headers/timing</li>
                    </ul>
                </div>

                <!-- Footer -->
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; text-align: center;">
                    <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                        Generated by Lead Sheets Monitor | {timestamp}
                    </p>
                    <p style="color: #94a3b8; font-size: 11px; margin: 4px 0 0 0;">
                        Failed leads are automatically queued for retry with exponential backoff
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def build_leads_digest_html(host_name: str, leads: List[Dict[str, Any]], host_id: Optional[str] = None) -> str:
    """
    Build a pretty HTML email for new leads digest.

    Args:
        host_name: Name of the Momence host or location
        leads: List of lead dictionaries
        host_id: Optional Momence host ID for dashboard links

    Returns:
        HTML string for the email body
    """
    timestamp = utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')

    # Group leads by source/sheet
    leads_by_source: Dict[str, List] = {}
    successful_count = sum(1 for lead in leads if lead.get('success'))
    pending_count = len(leads) - successful_count

    for lead in leads:
        source = lead.get('sheetName', 'Unknown')
        if source not in leads_by_source:
            leads_by_source[source] = []
        leads_by_source[source].append(lead)

    # Build source summary badges using list + join (more memory efficient)
    source_badges_list = []
    for source, source_leads in sorted(leads_by_source.items(), key=lambda x: -len(x[1])):
        source_badges_list.append(f"""
        <span style="display: inline-block; background: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 12px; font-size: 12px; margin: 4px;">
            {escape_html(source)}: {len(source_leads)}
        </span>
        """)
    source_badges = ''.join(source_badges_list)

    # Build lead cards using list + join (more memory efficient)
    lead_cards_list = []
    for lead in leads:
        status_bg = '#d1fae5' if lead.get('success') else '#fef3c7'
        status_color = '#059669' if lead.get('success') else '#d97706'
        status_text = 'Synced to Momence' if lead.get('success') else 'Pending Retry'

        # Escape all user-provided data
        email = lead.get('email', '')
        email_escaped = escape_html(email)
        email_encoded = urllib.parse.quote(email)
        first_name = escape_html(lead.get('firstName', ''))
        last_name = escape_html(lead.get('lastName', ''))
        phone_number = escape_html(lead.get('phoneNumber', ''))
        sheet_name = escape_html(lead.get('sheetName', '-'))

        momence_link = f"https://momence.com/dashboard/{escape_html(host_id)}/search?query={email_encoded}" if host_id else ""

        # Build name display
        full_name = f"{first_name} {last_name}".strip() or "Unknown"

        # Build optional fields as a clean list
        extra_fields_html = ""
        extra_items = []
        if lead.get('campaign'):
            extra_items.append(f"<strong>Campaign:</strong> {escape_html(lead.get('campaign'))}")
        if lead.get('form'):
            extra_items.append(f"<strong>Form:</strong> {escape_html(lead.get('form'))}")
        if lead.get('created'):
            extra_items.append(f"<strong>Captured:</strong> {escape_html(lead.get('created'))}")
        if lead.get('platform'):
            extra_items.append(f"<strong>Platform:</strong> {escape_html(lead.get('platform'))}")
        if lead.get('discoveryAnswer'):
            extra_items.append(f"<strong>How they heard:</strong> {escape_html(lead.get('discoveryAnswer'))}")
        if lead.get('zipCode'):
            extra_items.append(f"<strong>Zip:</strong> {escape_html(lead.get('zipCode'))}")

        if extra_items:
            extra_fields_html = f"""
            <div style="background: #f1f5f9; border-radius: 6px; padding: 10px; margin-top: 12px; font-size: 12px; color: #64748b;">
                {' &bull; '.join(extra_items)}
            </div>
            """

        momence_link_html = ""
        if momence_link and lead.get('success'):
            momence_link_html = f"""
            <a href="{momence_link}" style="display: inline-block; background: #6366f1; color: white; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500; text-decoration: none; margin-top: 12px;">
                View in Momence
            </a>
            """

        lead_cards_list.append(f"""
            <div style="background: #ffffff; border-radius: 12px; padding: 20px; margin-bottom: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <div style="font-size: 17px; font-weight: 600; color: #1e293b;">{full_name}</div>
                        <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">{sheet_name}</div>
                    </div>
                    <span style="background: {status_bg}; color: {status_color}; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">
                        {status_text}
                    </span>
                </div>

                <table style="width: 100%; font-size: 14px; color: #475569;">
                    <tr>
                        <td style="padding: 4px 0; width: 30px; vertical-align: middle;">
                            <span style="color: #6366f1;">@</span>
                        </td>
                        <td style="padding: 4px 0;">
                            <a href="mailto:{email_escaped}" style="color: #1e293b; text-decoration: none;">{email_escaped}</a>
                        </td>
                    </tr>
                    {f'''<tr>
                        <td style="padding: 4px 0; vertical-align: middle;">
                            <span style="color: #6366f1;">#</span>
                        </td>
                        <td style="padding: 4px 0; color: #1e293b;">{phone_number}</td>
                    </tr>''' if phone_number else ''}
                </table>

                {extra_fields_html}
                {momence_link_html}
            </div>
        """)
    lead_cards = ''.join(lead_cards_list)

    # Status summary section
    status_summary = ""
    if pending_count > 0:
        status_summary = f"""
        <div style="background: #fef3c7; border-radius: 6px; padding: 12px; margin-bottom: 16px; font-size: 13px; color: #92400e;">
            <strong>{pending_count} lead(s)</strong> pending retry due to temporary API issues. These will be automatically retried.
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f1f5f9;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); border-radius: 12px 12px 0 0; padding: 28px 24px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">
                    New Leads Received
                </h1>
                <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0 0; font-size: 15px;">
                    {escape_html(host_name)}
                </p>
            </div>

            <!-- Stats Bar -->
            <div style="background: white; padding: 20px 24px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: center; gap: 48px;">
                <div style="text-align: center; min-width: 70px;">
                    <div style="font-size: 32px; font-weight: 700; color: #6366f1;">{len(leads)}</div>
                    <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Total</div>
                </div>
                <div style="text-align: center; min-width: 70px;">
                    <div style="font-size: 32px; font-weight: 700; color: #059669;">{successful_count}</div>
                    <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Synced</div>
                </div>
                {f'''<div style="text-align: center; min-width: 70px;">
                    <div style="font-size: 32px; font-weight: 700; color: #d97706;">{pending_count}</div>
                    <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Pending</div>
                </div>''' if pending_count > 0 else ''}
            </div>

            <!-- Source Summary -->
            <div style="background: white; padding: 12px 24px; border-bottom: 1px solid #e2e8f0;">
                <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">By Source</div>
                {source_badges}
            </div>

            <!-- Lead Cards -->
            <div style="background: #f8fafc; padding: 24px; border-radius: 0 0 12px 12px;">
                {status_summary}
                {lead_cards}

                <!-- Momence Dashboard Link -->
                {f'''<div style="text-align: center; margin-top: 16px;">
                    <a href="https://momence.com/dashboard/{escape_html(host_id)}/leads?sortBy=createdAt&sortOrder=DESC" style="display: inline-block; background: #1e293b; color: white; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 500; text-decoration: none;">
                        Open Momence Dashboard
                    </a>
                </div>''' if host_id else ''}

                <!-- Footer -->
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; text-align: center;">
                    <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                        Lead Sheets Monitor | {timestamp}
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_error_digest(errors: List[Dict[str, Any]]) -> bool:
    """Send error digest email to admin."""
    email_config = get_email_config()
    admin_emails = resolve_email_list(email_config.get('admin_recipients', []))
    if not admin_emails:
        logger.debug("No admin email recipients configured")
        return False

    if not errors:
        return True

    html = build_error_digest_html(errors)
    subject = f"Lead Monitor: {len(errors)} Error(s) Detected"
    return send_email(admin_emails, subject, html)


def send_location_leads_digest(location_name: str, leads: List[Dict[str, Any]]) -> bool:
    """
    Send new leads digest email for a specific location.
    Only sends if location has notification_email configured.
    """
    sheet_cfg = get_sheet_config_by_name(location_name)
    if not sheet_cfg:
        logger.warning(f"No sheet config found for location '{location_name}'")
        return False

    momence_host_name = sheet_cfg.get('momence_host', '')
    host_cfg = get_host_config(momence_host_name) if momence_host_name else None

    # Only send if location has email configured
    location_email = sheet_cfg.get('notification_email', '').strip()
    if not location_email:
        logger.debug(f"No notification_email configured for location '{location_name}'")
        return False

    recipients = resolve_email_list([location_email])
    if not recipients:
        logger.debug(f"No valid email recipients for location '{location_name}'")
        return False

    if not leads:
        return True

    host_id = host_cfg.get('host_id') if host_cfg else None
    html = build_leads_digest_html(location_name, leads, host_id=host_id)
    subject = f"{len(leads)} New Lead(s) - {location_name}"
    logger.info(f"Sending location email for '{location_name}' to {recipients}")
    return send_email(recipients, subject, html)


def send_test_location_email(location_name: str) -> Dict[str, Any]:
    """
    Send a test email for a specific location to verify email configuration.

    Args:
        location_name: Name of the location/sheet

    Returns:
        Dict with 'success', 'recipients' (if success), or 'error' (if failed)
    """
    sheet_cfg = get_sheet_config_by_name(location_name)
    if not sheet_cfg:
        return {'success': False, 'error': f"Location '{location_name}' not found"}

    momence_host_name = sheet_cfg.get('momence_host', '')
    host_cfg = get_host_config(momence_host_name) if momence_host_name else None

    # Only use location-specific email
    location_email = sheet_cfg.get('notification_email', '').strip()
    if not location_email:
        return {'success': False, 'error': 'No notification_email configured for this location'}

    recipients = resolve_email_list([location_email])
    if not recipients:
        return {'success': False, 'error': 'Invalid email address configured for this location'}

    # Build test email with sample lead data
    timestamp = utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')
    sample_leads = [{
        'firstName': 'Test',
        'lastName': 'Lead',
        'email': 'test@example.com',
        'phoneNumber': '555-123-4567',
        'sheetName': location_name,
        'success': True,
        'created': timestamp,
    }]

    host_id = host_cfg.get('host_id') if host_cfg else None
    html = build_leads_digest_html(location_name, sample_leads, host_id=host_id)
    subject = f"[TEST] Email Notification Test - {location_name}"

    success = send_email(recipients, subject, html)
    if success:
        logger.info(f"Test email sent for location '{location_name}' to {recipients}")
        return {'success': True, 'recipients': recipients}
    else:
        return {'success': False, 'error': 'Failed to send email - check SMTP configuration'}
