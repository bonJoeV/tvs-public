# Lead Sheets Monitor

Monitors Google Sheets for new Facebook/Instagram lead entries and pushes them to Momence CRM. Supports multiple tenants (Momence accounts) with configurable lead sources per sheet.

## Features

- Multi-tenant support (multiple Momence accounts)
- Monitors multiple sheets/tabs for new leads
- Automatically pushes leads to Momence CRM with location-based lead sources
- Tracks sent entries to prevent duplicates
- Daily log rotation with 7-day retention
- Configurable check interval (default: 15 minutes)
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
docker-compose run --rm sheets-monitor-cli
```

## Configuration

### Environment (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CREDENTIALS_JSON` | Yes | Google service account JSON (single line) |
| `CONFIG_FILE` | No | Path to config.json (default: ./config.json) |
| `SENT_TRACKER_FILE` | No | Path to tracker file (default: ./sent_entries.json) |
| `LOG_DIR` | No | Log directory (default: ./logs) |
| `CHECK_INTERVAL_MINUTES` | No | Check interval for daemon mode (default: 15) |

### Tenants & Sheets (config.json)

```json
{
  "tenants": {
    "TwinCities": {
      "host_id": "49534",
      "token": "your-leads-token"
    },
    "AnotherStudio": {
      "host_id": "99999",
      "token": "another-token"
    }
  },
  "sheets": [
    {
      "spreadsheet_id": "your-google-spreadsheet-id",
      "gid": "0",
      "name": "Eden Prairie",
      "tenant": "TwinCities",
      "lead_source_id": 134089
    },
    {
      "spreadsheet_id": "your-google-spreadsheet-id",
      "gid": "22953747",
      "name": "Savage",
      "tenant": "TwinCities",
      "lead_source_id": 134088
    }
  ]
}
```

#### Config Fields

**Tenants:**
- `host_id`: Momence host ID
- `token`: Momence Customer Leads API token

**Sheets:**
- `spreadsheet_id`: Google Sheets ID (from URL)
- `gid`: Sheet tab ID (from URL after `#gid=`)
- `name`: Display name for logging
- `tenant`: Which tenant to push leads to
- `lead_source_id`: Momence lead source ID

## CLI Options

```bash
python monitor.py --help
python monitor.py --dry-run       # Test without API calls
python monitor.py --verbose       # Show detailed output
python monitor.py --reset-tracker # Treat all entries as new
python monitor.py --daemon        # Run continuously
```

## How It Works

1. Loads tenant and sheet configuration from config.json
2. Connects to Google Sheets API
3. Checks configured sheets for new rows
4. For each new entry:
   - Builds lead data from sheet columns
   - Pushes to Momence CRM using the sheet's configured tenant
5. Saves tracker to prevent duplicate processing
6. In daemon mode: waits for configured interval, then repeats

## Logging

Logs are written to `./logs/monitor.log` with:
- Daily rotation at midnight
- 7 days retention
- Console output for real-time monitoring

## Momence API

Uses the Customer Leads API:
```
POST https://api.momence.com/integrations/customer-leads/{hostId}/collect
```

Required fields: `token`, `email`, `firstName`, `lastName`, `sourceId`
Optional fields: `phoneNumber`, `zipCode`, `discoveryAnswer`
