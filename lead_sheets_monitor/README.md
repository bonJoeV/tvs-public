# Lead Sheets Monitor

Monitors Google Sheets for new Facebook/Instagram lead entries and pushes them to Momence CRM. Supports multiple tenants (Momence accounts) with configurable lead sources per sheet.

## Features

- Multi-tenant support (multiple Momence accounts)
- Monitors multiple sheets/tabs for new leads
- Automatically pushes leads to Momence CRM with location-based lead sources
- Tracks sent entries to prevent duplicates
- **Dynamic check intervals** based on business hours (per tenant)
- **Per-tenant checking** reduces API calls by skipping closed tenants
- **Cumulative location counts** since tracker reset
- Daily log rotation with configurable retention
- Configurable API timeout and retry settings
- Daemon mode for continuous monitoring
- Rotates browser signatures to avoid API detection
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
| `CONFIG_FILE` | No | Path to config.json (default: ./config.json) |
| `SENT_TRACKER_FILE` | No | Path to tracker file (default: ./sent_entries.json) |
| `LOG_DIR` | No | Log directory (default: ./logs) |

### Config File (config.json)

```json
{
  "settings": {
    "log_retention_days": 7,
    "api_timeout_seconds": 60,
    "retry_max_attempts": 3,
    "retry_base_delay_seconds": 1.0
  },
  "tenants": {
    "TwinCities": {
      "host_id": "49534",
      "token": "your-leads-token",
      "schedule": {
        "check_interval_biz_hours": 5,
        "check_interval_off_hours": 30,
        "business_hours": {
          "monday": [8, 16],
          "tuesday": [8, 16],
          "wednesday": [10, 19],
          "thursday": [10, 19],
          "friday": [10, 19],
          "saturday": [9, 14],
          "sunday": null
        }
      }
    }
  },
  "sheets": [
    {
      "spreadsheet_id": "your-google-spreadsheet-id",
      "gid": "0",
      "name": "Eden Prairie",
      "tenant": "TwinCities",
      "lead_source_id": 134089
    }
  ]
}
```

#### Settings

| Field | Default | Description |
|-------|---------|-------------|
| `log_retention_days` | 7 | Days to keep log files |
| `api_timeout_seconds` | 60 | Google Sheets API timeout |
| `retry_max_attempts` | 3 | Number of retry attempts on failure |
| `retry_base_delay_seconds` | 1.0 | Base delay for exponential backoff |

#### Tenants

| Field | Description |
|-------|-------------|
| `host_id` | Momence host ID |
| `token` | Momence Customer Leads API token |
| `schedule.check_interval_biz_hours` | Check interval during business hours (minutes) |
| `schedule.check_interval_off_hours` | Check interval outside business hours (minutes) |
| `schedule.business_hours` | Hours per day as `[open, close]` in 24h format, or `null` if closed |

#### Sheets

| Field | Description |
|-------|-------------|
| `spreadsheet_id` | Google Sheets ID (from URL) |
| `gid` | Sheet tab ID (from URL after `#gid=`) |
| `name` | Display name for logging and location counts |
| `tenant` | Which tenant to push leads to |
| `lead_source_id` | Momence lead source ID |

## CLI Options

```bash
python monitor.py --help
python monitor.py --dry-run       # Test without API calls
python monitor.py --verbose       # Show detailed output
python monitor.py --reset-tracker # Reset tracker, treat all entries as new
python monitor.py --daemon        # Run continuously
```

## How It Works

1. Loads settings, tenant, and sheet configuration from config.json
2. Connects to Google Sheets API with configured timeout
3. For each configured sheet:
   - Checks if the sheet's tenant is in business hours
   - Skips API calls for closed tenants (reduces load)
   - Fetches new rows from open tenant sheets
4. For each new entry:
   - Builds lead data from sheet columns
   - Pushes to Momence CRM using the sheet's configured tenant
   - Increments location count
5. Saves tracker to prevent duplicate processing
6. In daemon mode:
   - Uses the **minimum interval** among active tenants (e.g., if TenantA=5min and TenantB=10min, uses 5min)
   - Falls back to off-hours interval when all tenants are closed
   - Waits, then repeats

## Logging

Logs are written to `./logs/YYYYMMDD.log` with:
- Daily log files (e.g., `20260109.log`)
- Configurable retention (default: 7 days)
- Console output for real-time monitoring
- Cumulative location counts logged after each run

Example output:
```
2026-01-09 10:15:00 - INFO - Cumulative location counts (since 2026-01-08T21:48:07):
2026-01-09 10:15:00 - INFO -   Eden Prairie: 12
2026-01-09 10:15:00 - INFO -   Savage: 8
2026-01-09 10:15:00 - INFO -   TOTAL: 20
2026-01-09 10:15:00 - INFO - Next check in 5 minutes (business hours: TwinCities)...
```

## Momence API

Uses the Customer Leads API:
```
POST https://api.momence.com/integrations/customer-leads/{hostId}/collect
```

Required fields: `token`, `email`, `firstName`, `lastName`, `sourceId`
Optional fields: `phoneNumber`, `zipCode`, `discoveryAnswer`
