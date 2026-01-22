"""
Google Cloud Secret Manager integration for Lead Sheets Monitor.

Provides secure secret retrieval for Cloud Run deployments.
Falls back to environment variables for local development.

Required secrets in Secret Manager (project: tvs-dash):
- google-credentials-json: Google Service Account JSON for Sheets API
- momence-api-token: Momence API token for lead submission
- smtp-password: SMTP password for email notifications
- dashboard-password: Dashboard authentication password
- encryption-key: Fernet encryption key for sensitive data

Usage:
    from secret_manager import get_secret

    # Get a secret (tries Secret Manager first, then env var)
    api_token = get_secret('momence-api-token', env_fallback='MOMENCE_API_TOKEN')
"""

import os
import logging
from typing import Optional, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Check if running on Cloud Run
IS_CLOUD_RUN = bool(os.getenv('K_SERVICE'))

# Google Cloud Project ID for Secret Manager
# Required on Cloud Run - no default to prevent accidental cross-project access
_gcp_project_env = os.getenv('GCP_PROJECT_ID')
if IS_CLOUD_RUN and not _gcp_project_env:
    logger.error(
        "GCP_PROJECT_ID environment variable is required on Cloud Run. "
        "Set it in your Cloud Run configuration."
    )
    # Don't fail immediately - let the secret access fail with a clear error
GCP_PROJECT_ID = _gcp_project_env or 'tvs-dashboard'  # Fallback for local dev only

# Secret Manager client (lazy loaded)
_client = None
_secrets_cache: Dict[str, tuple] = {}  # {cache_key: (value, timestamp)}
SECRET_CACHE_TTL = 3600  # 1 hour TTL for cached secrets

# Mapping of secret names to environment variable fallbacks
# Secret names use "lead-monitor-" prefix in Secret Manager
SECRET_ENV_MAPPING = {
    'lead-monitor-google-credentials': 'GOOGLE_CREDENTIALS_JSON',
    'lead-monitor-momence-api-token': 'MOMENCE_API_TOKEN',
    'lead-monitor-smtp-password': 'SMTP_PASSWORD',
    'lead-monitor-dashboard-password': 'DASHBOARD_PASSWORD',
    'lead-monitor-dashboard-username': 'DASHBOARD_USERNAME',
    'lead-monitor-dashboard-api-key': 'DASHBOARD_API_KEY',
    'lead-monitor-encryption-key': 'ENCRYPTION_KEY',
    'lead-monitor-slack-webhook-url': 'SLACK_WEBHOOK_URL',
}


def _get_client():
    """Get or create the Secret Manager client."""
    global _client
    if _client is None:
        try:
            from google.cloud import secretmanager
            _client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager client initialized")
        except ImportError:
            logger.warning(
                "google-cloud-secret-manager not installed. "
                "Install with: pip install google-cloud-secret-manager"
            )
            _client = False  # Mark as unavailable
        except Exception as e:
            logger.warning(f"Failed to initialize Secret Manager client: {e}")
            _client = False
    return _client if _client else None


def get_secret(
    secret_name: str,
    env_fallback: str = None,
    version: str = "latest",
    required: bool = False
) -> Optional[str]:
    """
    Retrieve a secret from Google Cloud Secret Manager.

    On Cloud Run, tries Secret Manager first, then falls back to env var.
    Locally (not Cloud Run), only uses environment variables.

    Args:
        secret_name: Name of the secret in Secret Manager (e.g., 'momence-api-token')
        env_fallback: Environment variable name to use as fallback
        version: Secret version (default: 'latest')
        required: If True, raises ValueError when secret is not found

    Returns:
        Secret value as string, or None if not found

    Raises:
        ValueError: If required=True and secret is not found
    """
    import time

    # Check cache first (with TTL)
    cache_key = f"{secret_name}:{version}"
    if cache_key in _secrets_cache:
        cached_value, cached_time = _secrets_cache[cache_key]
        if time.time() - cached_time < SECRET_CACHE_TTL:
            return cached_value
        # Cache expired, remove it
        del _secrets_cache[cache_key]

    # Determine env var fallback
    if env_fallback is None:
        env_fallback = SECRET_ENV_MAPPING.get(secret_name)

    secret_value = None

    # On Cloud Run, try Secret Manager first
    if IS_CLOUD_RUN:
        client = _get_client()
        if client:
            try:
                # Build the resource name
                name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}/versions/{version}"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                logger.debug(f"Retrieved secret '{secret_name}' from Secret Manager")
            except Exception as e:
                # Debug level - expected when secrets are in env vars instead of Secret Manager
                logger.debug(f"Secret '{secret_name}' not in Secret Manager, will try env var: {e}")

    # Fall back to environment variable
    if secret_value is None and env_fallback:
        secret_value = os.getenv(env_fallback)
        if secret_value:
            logger.debug(f"Using environment variable '{env_fallback}' for secret '{secret_name}'")

    # Cache the result with timestamp (even if None, to avoid repeated lookups)
    if secret_value:
        _secrets_cache[cache_key] = (secret_value, time.time())

    # Handle required secrets
    if required and not secret_value:
        raise ValueError(
            f"Required secret '{secret_name}' not found. "
            f"Set it in Secret Manager or as env var '{env_fallback}'"
        )

    return secret_value


def get_google_credentials_json() -> Optional[str]:
    """Get Google Service Account credentials JSON."""
    return get_secret('lead-monitor-google-credentials', 'GOOGLE_CREDENTIALS_JSON')


def get_momence_token(tenant_name: str = None) -> Optional[str]:
    """
    Get Momence API token.

    Args:
        tenant_name: Optional tenant name for multi-tenant setups

    Returns:
        API token string
    """
    if tenant_name:
        # Try tenant-specific secret first
        secret_name = f"lead-monitor-momence-api-token-{tenant_name}"
        env_fallback = f"MOMENCE_API_TOKEN_{tenant_name.upper()}"
        token = get_secret(secret_name, env_fallback)
        if token:
            return token

    # Fall back to default token
    return get_secret('lead-monitor-momence-api-token', 'MOMENCE_API_TOKEN')


def get_smtp_password() -> Optional[str]:
    """Get SMTP password for email notifications."""
    return get_secret('lead-monitor-smtp-password', 'SMTP_PASSWORD')


def get_dashboard_credentials() -> Dict[str, Optional[str]]:
    """
    Get dashboard authentication credentials.

    Returns:
        Dict with 'api_key', 'username', and 'password' keys
    """
    return {
        'api_key': get_secret('lead-monitor-dashboard-api-key', 'DASHBOARD_API_KEY'),
        'username': get_secret('lead-monitor-dashboard-username', 'DASHBOARD_USERNAME'),
        'password': get_secret('lead-monitor-dashboard-password', 'DASHBOARD_PASSWORD'),
    }


def get_encryption_key() -> Optional[str]:
    """Get Fernet encryption key."""
    return get_secret('lead-monitor-encryption-key', 'ENCRYPTION_KEY')


def clear_cache():
    """Clear the secrets cache (useful for testing or key rotation)."""
    global _secrets_cache
    _secrets_cache = {}
    logger.info("Secrets cache cleared")


def set_secret(secret_name: str, secret_value: str) -> bool:
    """
    Create or update a secret in Google Cloud Secret Manager.

    Args:
        secret_name: Name of the secret (e.g., 'lead-monitor-momence-api-token-TwinCities')
        secret_value: The secret value to store

    Returns:
        True if successful, False otherwise
    """
    if not IS_CLOUD_RUN:
        logger.warning(f"Not on Cloud Run - cannot create secret '{secret_name}' in Secret Manager")
        return False

    client = _get_client()
    if not client:
        logger.error("Secret Manager client not available")
        return False

    try:
        from google.cloud import secretmanager

        parent = f"projects/{GCP_PROJECT_ID}"
        secret_path = f"{parent}/secrets/{secret_name}"

        # Try to get the secret first to see if it exists
        try:
            client.get_secret(request={"name": secret_path})
            secret_exists = True
        except Exception:
            secret_exists = False

        # Create the secret if it doesn't exist
        if not secret_exists:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            logger.info(f"Created new secret '{secret_name}'")

        # Add a new version with the secret value
        client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        logger.info(f"Added new version to secret '{secret_name}'")

        # Clear cache so next get_secret call fetches the new value
        cache_key = f"{secret_name}:latest"
        if cache_key in _secrets_cache:
            del _secrets_cache[cache_key]

        return True

    except Exception as e:
        logger.error(f"Failed to set secret '{secret_name}': {e}")
        return False


def delete_secret(secret_name: str) -> bool:
    """
    Delete a secret from Google Cloud Secret Manager.

    Args:
        secret_name: Name of the secret to delete

    Returns:
        True if successful or secret didn't exist, False on error
    """
    if not IS_CLOUD_RUN:
        logger.warning(f"Not on Cloud Run - cannot delete secret '{secret_name}' from Secret Manager")
        return False

    client = _get_client()
    if not client:
        logger.error("Secret Manager client not available")
        return False

    try:
        secret_path = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}"
        client.delete_secret(request={"name": secret_path})
        logger.info(f"Deleted secret '{secret_name}'")

        # Clear from cache
        cache_key = f"{secret_name}:latest"
        if cache_key in _secrets_cache:
            del _secrets_cache[cache_key]

        return True

    except Exception as e:
        # If secret doesn't exist, that's fine
        if "NOT_FOUND" in str(e):
            logger.debug(f"Secret '{secret_name}' not found (already deleted or never existed)")
            return True
        logger.error(f"Failed to delete secret '{secret_name}': {e}")
        return False


def list_required_secrets() -> Dict[str, str]:
    """
    List all required secrets and their environment variable fallbacks.

    Returns:
        Dict mapping secret names to env var names
    """
    return SECRET_ENV_MAPPING.copy()
