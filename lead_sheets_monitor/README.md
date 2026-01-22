# Lead Sheets Monitor

## Executive Summary

This service automates lead capture from Facebook/Instagram ads to Momence CRM. When someone fills out a lead form on social media, the data flows through Zapier to Google Sheets, then this monitor automatically pushes new leads to Momence within minutes.

**Key Value:**
- **Zero manual data entry** - Leads appear in Momence automatically
- **Multi-location support** - Handle multiple studios/franchises from one service
- **Reliable delivery** - Automatic retries with exponential backoff, dead letter queue for failures
- **Real-time visibility** - Web dashboard shows leads by location, processing status, and errors
- **Cloud-native** - Runs on Google Cloud Run with automatic scaling and persistence

**Data Flow:**
```
                              
Facebook/Instagram Lead Ad → Zapier → Google Sheet → [This Monitor] → Momence CRM
                              
```

---

## Why This Approach (vs. Zapier Direct Integration)

### The Problem

```
                              ┌→ Google Sheet
Facebook/Instagram Lead Ad → Zapier
                              └→ Momence API
```

However, this approach consistently fails due to **Cloudflare protection on the Momence API or some bug/misconfiguration in Zapier or a Momence configuration or bug**. When Zapier makes requests to Momence's Customer Leads API, it frequently receives:

- **HTTP 400 errors** - Generic bad request responses
- **Cloudflare challenge pages** - Bot detection blocking automated requests
- **Intermittent failures** - Works sometimes, fails unpredictably

Zapier's infrastructure uses shared IP ranges that Cloudflare flags as suspicious, triggering bot protection. This results in **lost leads** with no reliable way to retry or monitor failures.

### Why This Solution Works

This monitor runs on Google Cloud Run with:

1. **Dedicated IP addresses** - Cloud Run egress uses Google's infrastructure, which Cloudflare trusts more than Zapier's shared IPs
2. **Retry logic with backoff** - When Cloudflare does block a request, the lead goes into a retry queue with exponential backoff (1hr → 4hr → 24hr)
3. **Dead letter queue** - Leads that fail after multiple retries are preserved for manual intervention—no leads are ever lost
4. **Rate limiting** - 3-second delays between API calls avoid triggering rate limits
5. **Visibility** - Dashboard shows exactly which leads succeeded, failed, or are pending retry

### The Trade-off

This adds complexity (Google Sheets as intermediate storage, this monitor service) but provides:
- **100% lead delivery** vs. ~70-80% with direct Zapier integration
- **Full audit trail** of every lead attempt
- **Self-healing** through automatic retries
- **Observability** through the web dashboard

The Google Sheets intermediate step also provides a human-readable backup of all leads, useful for reconciliation and debugging.

---

## Features

- **Multi-host support** - Multiple Momence accounts with independent configuration
- **Web Dashboard** - Real-time monitoring UI with host/location management
- **Dead Letter Queue** - Failed leads are automatically retried with exponential backoff
- **Memory Optimized** - Cached API connections, periodic cleanup, GC between cycles
- **Cloud Run Ready** - GCS persistence, Secret Manager integration, health checks
- Monitors multiple sheets/tabs for new leads
- Tracks sent entries (SQLite) to prevent duplicates
- Daily email digests per location
- Configurable check interval
- Dry-run mode for testing

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
cp config.example.json config.json
# Edit both files with your values
```

### 2. Run

```bash
# Install dependencies
pip install -r requirements.txt

# Dry run (no API calls)
python monitor.py --dry-run --verbose

# Single run
python monitor.py --verbose

# Daemon mode (runs continuously)
python monitor.py --daemon --verbose
```

### 3. Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# One-off dry run
docker-compose run --rm sheets-monitor python monitor.py --dry-run --verbose

# Reset tracker (treat all entries as new)
docker-compose run --rm sheets-monitor python monitor.py --reset-tracker --verbose
```

## Configuration

### Environment (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CREDENTIALS_JSON` | Yes | Google service account JSON (single line) |
| `CONFIG_FILE` | No | Path to config.json for settings (default: ./config.json) |
| `DATABASE_FILE` | No | SQLite database path (default: ./lead_monitor.db) |
| `LOG_DIR` | No | Log directory (default: ./logs) |

### Config File (config.json)

The config file contains application **settings only**. Momence hosts and sheet locations are stored in the SQLite database and managed via the web dashboard.

```json
{
  "settings": {
    "log_retention_days": 7,
    "api_timeout_seconds": 60,
    "retry_max_attempts": 3,
    "retry_base_delay_seconds": 1.0,
    "rate_limit_delay_seconds": 3.0,
    "default_spreadsheet_id": "your-google-spreadsheet-id"
  }
}
```

### Database Storage

Momence hosts and sheet/location configurations are stored in the SQLite database (not config.json). This allows:
- **Persistence across deployments** - Config changes via dashboard survive container restarts
- **GCS sync on Cloud Run** - Database is automatically synced to Google Cloud Storage
- **Atomic updates** - No risk of config file corruption

Use the web dashboard to add/edit/delete hosts and locations.

#### Settings

| Field | Default | Description |
|-------|---------|-------------|
| `log_retention_days` | 7 | Days to keep log files |
| `api_timeout_seconds` | 60 | Google Sheets API timeout |
| `retry_max_attempts` | 3 | Number of retry attempts on failure |
| `retry_base_delay_seconds` | 1.0 | Base delay for exponential backoff |
| `rate_limit_delay_seconds` | 3.0 | Delay between Momence API calls |
| `check_interval_minutes` | 5 | How often to check for new leads (daemon mode) |

#### Momence Hosts (Database)

Hosts are stored in the SQLite database and managed via the web dashboard. Each host represents a Momence account:

| Field | Description |
|-------|-------------|
| `name` | Display name (used as identifier) |
| `host_id` | Momence host ID (from dashboard URL) |
| `token` | Momence Customer Leads API token (stored in Secret Manager on Cloud Run) |
| `enabled` | Enable/disable this host |

#### Sheets/Locations (Database)

Locations are stored in the SQLite database and managed via the web dashboard. Each location represents a Google Sheet tab:

| Field | Description |
|-------|-------------|
| `spreadsheet_id` | Google Sheets ID (from URL) |
| `gid` | Sheet tab ID (from URL after `#gid=`) |
| `name` | Display name for logging and location counts |
| `momence_host` | Which Momence host to push leads to |
| `lead_source_id` | Momence lead source ID |
| `enabled` | Enable/disable this sheet |
| `notification_email` | Email for location-specific lead notifications (optional) |

## CLI Options

```bash
python monitor.py --help
python monitor.py --dry-run        # Test without API calls
python monitor.py --verbose        # Show detailed output
python monitor.py --reset-tracker  # Reset tracker, treat all entries as new
python monitor.py --daemon         # Run continuously
python monitor.py --queue-status   # Show failed queue status
python monitor.py --retry-failed   # Force retry all failed entries
```

## Web Dashboard

The monitor includes a web dashboard at `http://localhost:8080` (or Cloud Run URL).

### Dashboard Features

| Section | Description |
|---------|-------------|
| **Status Bar** | Shows last check time, leads processed today, uptime, service health |
| **Leads Chart** | Interactive chart showing leads by location over last 7/14/30 days |
| **Momence Hosts** | Collapsible table of all hosts with quick filters (All/Active/Disabled) |
| **Locations** | Table of all sheet configurations with lead counts |
| **Failed Queue** | Leads that failed to send, with detailed error info and retry buttons |
| **Dead Letters** | Leads that exceeded max retries, requires manual intervention |
| **Activity Log** | Audit trail of admin actions (logins, config changes) |
| **Logs** | Live tail of application logs |

### Host Management

The Hosts section shows all configured Momence accounts in a compact table:
- Click the header to collapse/expand (state is remembered)
- Filter by All / Active / Disabled
- Quick actions: View Leads (opens Momence), Enable/Disable, Edit, Delete

### Adding a New Host

1. Click **+ Add Host** button
2. Enter host name (e.g., "Scarsdale")
3. Enter Host ID from Momence dashboard URL
4. Enter API token from Momence Integrations settings
5. Optionally add notification email for lead digests
6. Click Save

### Adding a New Location

1. Click **+ Add Location** button
2. Paste the Google Sheet URL (extracts spreadsheet ID and tab automatically)
3. Enter a display name (e.g., "Eden Prairie")
4. Select which Momence host this location belongs to
5. Enter the Lead Source ID from Momence
6. Click Save

### Dashboard Authentication

Set credentials via environment or Secret Manager:

```bash
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=secure-password
# Or use API key
DASHBOARD_API_KEY=your-api-key
```

## How It Works

### Overview

This system bridges Facebook/Instagram Lead Ads with Momence CRM. When someone fills out a lead form on Facebook, the data flows through Zapier into a Google Sheet. This monitor watches those sheets and pushes new leads to Momence automatically.

```
Facebook Lead Ad → Zapier → Google Sheet → [This Monitor] → Momence CRM
```

### The Lead Flow (Step by Step)

1. **Lead Captured**: Someone fills out a Facebook Lead Ad form
2. **Zapier Trigger**: Zapier detects the new lead and appends a row to a Google Sheet
3. **Monitor Detects**: Every 5 minutes (configurable), this monitor:
   - Connects to Google Sheets API
   - Fetches rows from each configured sheet (incremental - only new rows)
   - Computes a hash of each row (email + name + phone) to detect duplicates
4. **Duplicate Check**: Compares row hashes against SQLite database of previously sent leads
5. **Push to Momence**: For each new lead:
   - Extracts fields: email, firstName, lastName, phone, zipCode
   - Calls Momence Customer Leads API with the configured `lead_source_id`
   - Waits 3 seconds between API calls (rate limiting)
6. **Track Success**: Stores the row hash in database to prevent re-sending
7. **Handle Failures**: If Momence API fails:
   - Lead is added to the Failed Queue
   - Automatic retry with exponential backoff (1hr, 4hr, 24hr)
   - After 5 failures, moved to Dead Letters for manual review
8. **Notifications**: Sends daily email digest per location with new lead count

### Key Concepts

#### Momence Hosts
A "host" is a Momence account (studio/franchise). Each host has:
- **Host ID**: Found in your Momence dashboard URL (`momence.com/dashboard/49534/...`)
- **API Token**: Generated in Momence under Integrations → Customer Leads API
- **Notification Email**: Where lead digests are sent

#### Locations (Sheets)
A "location" is a single Google Sheet tab representing one studio location. Each location:
- Belongs to one Momence host
- Has a unique `lead_source_id` (created in Momence under Lead Sources)
- Can be enabled/disabled independently

#### Deduplication
Leads are deduplicated by hashing: `email + first_name + last_name + phone`. This means:
- Same person submitting twice = only sent once
- Same person at different locations = sent to each location once
- Editing non-key fields (notes, etc.) won't trigger re-send

### Processing Timing

- **Check Interval**: Default 5 minutes, configurable per deployment
- **Rate Limiting**: 3 second delay between Momence API calls
- **No Overlap**: If a run takes longer than the interval, next run starts immediately after (no parallel runs)

**Example**: 20 new leads across 5 locations:
- Fetch time: ~2-3 seconds per sheet = ~15 seconds
- API calls: 20 leads × 3 sec = 60 seconds
- Total: ~75 seconds, well under 5 minute interval

**Scaling**: With 50 locations × 100 new leads = 5000 leads:
- Would take ~4+ hours for API calls alone
- Consider reducing `rate_limit_delay_seconds` if Momence allows

## Architecture

### Memory Management

The daemon is optimized for long-running operation:

- **Cached Google Sheets service** - Single connection reused across cycles, refreshed hourly
- **Periodic cache cleanup** - Session, CSRF, and rate-limit caches cleaned each cycle
- **Garbage collection** - Explicit `gc.collect()` after each monitoring cycle
- **Paginated queries** - Failed queue processed in batches to limit memory
- **Count-only checks** - Uses `COUNT(*)` queries instead of loading full result sets

### Dead Letter Queue (DLQ)

Failed leads are automatically retried with exponential backoff:

1. First retry: 1 hour after failure
2. Second retry: 4 hours after first retry
3. Third retry: 24 hours after second retry
4. After 5 failures: Moved to dead letters

View dead letters in the dashboard or via CLI:
```bash
python monitor.py --queue-status
```

### Data Flow

1. Daemon loop starts, checks for new leads every N minutes
2. For each configured sheet:
   - Fetches new rows since last check (incremental)
   - Hashes each row to detect duplicates
   - Pushes new leads to Momence API
3. Failed leads added to retry queue
4. Email digests sent per location
5. Database synced to GCS (Cloud Run)
6. Memory cleanup, wait for next cycle

## Google Cloud Run Deployment

### Prerequisites

1. Google Cloud Project with Secret Manager and Cloud Run enabled
2. Service account with necessary permissions
3. GCS bucket for database persistence

### Required Secrets in Secret Manager

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `google-credentials-json` | Google Service Account JSON for Sheets API | Yes |
| `momence-api-tokens` | JSON object mapping host names to API tokens | Yes |
| `smtp-password` | SMTP password for email notifications | If using email |
| `dashboard-password` | Dashboard authentication password | Recommended |
| `dashboard-username` | Dashboard authentication username | Recommended |

### Deploy to Cloud Run

```bash
# Build with Cloud Build
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=SHORT_SHA=$(git rev-parse --short HEAD),_BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Deploy
gcloud run deploy lead-sheets-monitor \
  --image gcr.io/YOUR_PROJECT/lead-sheets-monitor:latest \
  --region us-central1 \
  --set-env-vars "GCP_PROJECT_ID=YOUR_PROJECT,GCS_BUCKET=your-bucket-name"
```

### Environment Variables for Cloud Run

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GCS_BUCKET` | GCS bucket for database persistence |
| `HEALTH_PORT` | Health check port (default: 8080) |
| `GRACEFUL_SHUTDOWN_TIMEOUT` | Seconds for graceful shutdown (default: 10) |

## Momence API

Uses the Customer Leads API:
```
POST https://api.momence.com/integrations/customer-leads/{hostId}/collect
```

Required fields: `token`, `email`, `firstName`, `lastName`, `sourceId`
Optional fields: `phoneNumber`, `zipCode`, `discoveryAnswer`

## Troubleshooting

### Memory Issues

If container memory grows over time:
- Check Cloud Run memory metrics
- Memory should plateau at ~20-30%, not grow continuously
- If growing: check for new memory leaks, review recent changes

### Failed Leads

1. Check dashboard Failed Queue section for error details
2. Common errors:
   - `rate_limited` (429): Reduce `rate_limit_delay_seconds`
   - `api_bad_request` (400): Check lead data format
   - `cloudflare_blocked`: Temporary, will auto-retry

### Logs

```bash
# View recent logs
docker-compose logs -f --tail 100

# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=lead-sheets-monitor" --limit 50
```
