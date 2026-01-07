# The Vital Stretch Dashboard - Technical Architecture Guide

## For Technical Architects & Development Teams

This document provides comprehensive technical documentation for The Vital Stretch Franchise Analytics Dashboard, including architecture decisions, security controls, deployment processes, and operational procedures.

**For non-technical information about features and data security, see the [README](README.md).**

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Architecture Overview](#architecture-overview)
3. [Security Controls](#security-controls)
4. [Development Process](#development-process)
5. [Quality Assurance](#quality-assurance)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Deployment Architecture](#deployment-architecture)
8. [Database Architecture](#database-architecture)
9. [Backup & Disaster Recovery](#backup--disaster-recovery)
10. [High Availability](#high-availability)
11. [Monitoring & Observability](#monitoring--observability)
12. [Data Upload Specifications](#data-upload-specifications)
13. [What's Next (Roadmap)](#whats-next-roadmap)
14. [API Reference](#api-reference)
15. [Environment Variables](#environment-variables)
16. [Error Codes](#error-codes)
17. [Performance Benchmarks](#performance-benchmarks)
18. [Legal](#legal)

---

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Runtime | Node.js | 22+ (Alpine) |
| Framework | NestJS | 11.1.9 |
| HTTP Server | Fastify | High-performance adapter |
| Database ORM | Prisma | 6.9.0 |
| Authentication | Passport JWT + Google OAuth | passport-jwt, google-auth-library |
| API Documentation | Swagger/OpenAPI | Redoc UI |
| Logging | Pino | Structured JSON logging |
| Scheduling | @nestjs/schedule | Cron jobs |
| Email | Nodemailer | SMTP integration |

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 19.1.0 |
| Build Tool | Vite | 6.3.5 |
| Language | TypeScript | Strict mode |
| Routing | React Router | 7.9.6 |
| Charts | Chart.js | 4.5.1 |
| Maps | Leaflet | 1.9.4 |
| CSV Parsing | PapaParse | Client-side processing |
| PDF Generation | html2canvas | Executive reports |

### Database
| Component | Technology | Version |
|-----------|------------|---------|
| Database | PostgreSQL | 17 |
| ORM | Prisma | 6.9.0 |
| Connection Pooling | Prisma Connection Pool | Built-in |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| Cloud Platform | Google Cloud Platform | Primary infrastructure |
| Compute | Cloud Run | Auto-scaling containers |
| Frontend Hosting | Firebase Hosting | Global CDN |
| Message Queue | Cloud Pub/Sub | Async job processing |
| Object Storage | Cloud Storage | File uploads, exports |
| Secrets | Secret Manager | Credential storage |
| IaC | Terraform | Infrastructure as Code |
| Containers | Docker | Containerization |
| CI/CD | Cloud Build | Automated deployments |

---

## Architecture Overview

### System Architecture

```
                              ┌─────────────┐
                              │   USERS     │
                              └──────┬──────┘
                                     │
                                     ▼
                            ┌───────────────┐
                            │  GLOBAL CDN   │
                            │───────────────│
                            │ Firebase CDN  │
                            │ Edge Caching  │
                            │ SSL/TLS       │
                            └───────┬───────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │   FRONTEND    │
                            │───────────────│
                            │ Firebase      │
                            │ Hosting       │
                            │ React SPA     │
                            └───────┬───────┘
                                    │ API calls
                                    ▼
                            ┌───────────────┐
                            │   FIREWALL    │
                            │───────────────│
                            │ Cloud Armor   │
                            │ Rate Limiting │
                            │ DDoS Protect  │
                            └───────┬───────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │    BACKEND    │
                            │───────────────│
                            │ Cloud Run     │
                            │ NestJS API    │
                            │ JWT Auth      │
                            └───────┬───────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
          │   DATABASE    │ │  MESSAGE Q    │ │   STORAGE     │
          │───────────────│ │───────────────│ │───────────────│
          │ Cloud SQL     │ │ Cloud Pub/Sub │ │ Cloud Storage │
          │ PostgreSQL 17 │ │ Async Jobs    │ │ File Uploads  │
          │ VPC Private   │ │ Dead Letter Q │ │ CSV Exports   │
          └───────▲───────┘ └───────┬───────┘ └───────▲───────┘
                  │                 │                 │
                  │                 ▼                 │
                  │          ┌───────────────┐        │
                  │          │    WORKER     │        │
                  │          │───────────────│        │
                  └──────────│ Cloud Run     │────────┘
                             │ Pub/Sub Jobs  │
                             │ VPC Private   │
                             └───────────────┘
```

### Data Flow

```
User → CDN (Firebase) → Frontend → Firewall → Backend API → PostgreSQL
                                                    │
                                                    ├─→ Cloud Storage (file uploads)
                                                    │
                                                    └─→ Pub/Sub → Worker (async jobs)
```

### Multi-Tenant Data Architecture

The system supports multiple isolated databases for different use cases:

| Database | Purpose | Use Case |
|----------|---------|----------|
| `tvsdemo` | Demo data | 4 sample franchises for demonstration |
| `tvsfranchise` | Production | Live franchise data with Google OAuth |
| `tvssessions` | Session tracking | User session and audit data |
| `tvsmega` | Performance testing | 77 franchises, 235 locations |

### Service Architecture

**Backend API Service:**
- RESTful API with OpenAPI documentation
- JWT-based authentication with role-based access control
- Rate limiting (300 req/min global, 10 req/min auth)
- Request validation with class-validator
- Structured logging with request tracing

**Worker Service:**
- Pull-based Pub/Sub message processing
- Batch processing (configurable batch size)
- Graceful shutdown handling (SIGTERM/SIGINT)
- Dead-letter queue for failed messages
- Single-execution mode for scheduled jobs

---

## Security Controls

### Authentication

| Control | Implementation |
|---------|----------------|
| OAuth 2.0 | Google OAuth with ID token verification |
| JWT Tokens | HS256 (configurable to RS256/JWKS) |
| Token Storage | HTTP-only cookies (`__session`) |
| Session Management | Unique session IDs with metadata tracking |
| Token Expiry | Configurable expiration with refresh |

### Authorization (RBAC)

```
SUPER_ADMIN
    └── FRANCHISOR
            └── OWNER
                    └── GENERAL_MANAGER
                            └── STUDIO_LEAD
                                    └── MANAGER
                                            └── STAFF
```

Each role has franchise-scoped permissions enforced at the API layer.

### API Security

| Control | Implementation |
|---------|----------------|
| Rate Limiting | 300 req/min (global), 10 req/min (auth endpoints) |
| Input Validation | class-validator with whitelist mode |
| SQL Injection | Prisma ORM with parameterized queries |
| XSS Protection | Helmet CSP headers |
| CSRF Protection | SameSite cookies |
| Clickjacking | X-Frame-Options: sameorigin |

### Security Headers (Helmet)

```javascript
{
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "cdn.redoc.ly"],
      styleSrc: ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
      fontSrc: ["'self'", "fonts.gstatic.com"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "*.googleapis.com"]
    }
  },
  hsts: { maxAge: 31536000, includeSubDomains: true },
  referrerPolicy: { policy: "strict-origin-when-cross-origin" },
  xssFilter: true,
  frameguard: { action: "sameorigin" }
}
```

### Audit Logging

All user actions are logged with:
- User ID, email, and role
- Franchise and location context
- Action performed
- Session ID and timestamp
- IP address and device information
- Geolocation (when available)

---

## Development Process

### Code Quality Standards

| Tool | Purpose | Configuration |
|------|---------|---------------|
| ESLint | Linting | TypeScript rules, strict mode |
| Prettier | Formatting | Default configuration |
| Husky | Git hooks | Pre-commit validation |
| lint-staged | Staged file linting | ESLint + Prettier on changed files |
| commitlint | Commit messages | Conventional Commits format |

### Commit Message Format

```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
```

Examples:
- `feat(auth): add Google OAuth integration`
- `fix(dashboard): resolve timezone calculation error`
- `perf(api): optimize membership query performance`

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `feature/*` | New features |
| `fix/*` | Bug fixes |
| `release/*` | Release preparation |

### Local Development

```bash
# Start all services
docker-compose up -d

# Services available:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:3000
# - Adminer (DB UI): http://localhost:8080
# - PostgreSQL: localhost:5432
```

---

## Quality Assurance

### Testing Framework

**Backend (Jest):**
```javascript
// jest.config.js
{
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.spec.ts'],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  testTimeout: 30000
}
```

**Frontend (Vitest):**
```javascript
// vitest.config.mts
{
  test: {
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      thresholds: {
        statements: 60,
        branches: 60,
        functions: 60,
        lines: 60
      }
    }
  }
}
```

### Test Commands

```bash
# Backend
npm run test          # Run tests
npm run test:watch    # Watch mode
npm run test:cov      # Coverage report
npm run test:e2e      # End-to-end tests

# Frontend
npm run test          # Run Vitest
npm run test:ui       # Interactive UI
npm run test:coverage # Coverage report
```

### Coverage Requirements

| Metric | Minimum Threshold |
|--------|-------------------|
| Statements | 80% |
| Branches | 80% |
| Functions | 80% |
| Lines | 80% |

---

## CI/CD Pipeline

### Cloud Build Pipeline (`cloudbuild.yaml`)

```yaml
# Pipeline Stages:
1. Build backend Docker image
2. Build worker Docker image
3. Push images to Artifact Registry
4. Deploy backend to Cloud Run
5. Deploy worker to Cloud Run
6. Build frontend (Vite)
7. Deploy frontend to Firebase Hosting
```

### Pipeline Configuration

| Setting | Value |
|---------|-------|
| Machine Type | E2_HIGHCPU_8 |
| Timeout | 30 minutes |
| Logging | CLOUD_LOGGING_ONLY |
| Triggers | Push to main, manual |

### Environment Substitutions

| Variable | Description |
|----------|-------------|
| `_ENVIRONMENT` | dev, staging, prod |
| `_REGION` | GCP region (default: us-central1) |
| `SHORT_SHA` | Git commit short SHA |

### Artifact Registry

Images are tagged with:
- `${SHORT_SHA}` - Commit-specific tag
- `latest` - Most recent build

---

## Deployment Architecture

### Cloud Run Configuration

**Backend Service:**
```yaml
name: tvs-backend-${environment}
scaling:
  minInstances: 1
  maxInstances: 10
resources:
  cpu: 1
  memory: 512Mi
probes:
  startup:
    path: /api/v1/health
    failureThreshold: 3
    periodSeconds: 10
  liveness:
    path: /api/v1/health/live
    periodSeconds: 30
```

**Worker Service:**
```yaml
name: tvs-worker-${environment}
scaling:
  minInstances: 0
  maxInstances: 5
environment:
  WORKER_MODE: pull
  WORKER_BATCH_SIZE: 10
```

### Terraform Modules

| Module | Purpose |
|--------|---------|
| `cloudrun.tf` | Cloud Run services |
| `cloudsql.tf` | PostgreSQL configuration |
| `pubsub.tf` | Message queue setup |
| `storage.tf` | Cloud Storage buckets |
| `secrets.tf` | Secret Manager |
| `iam.tf` | Service accounts & permissions |
| `scheduler.tf` | Cron job definitions |

### Networking

- **VPC Connector**: Private communication with Cloud SQL
- **Egress**: PRIVATE_RANGES_ONLY for backend/worker
- **Ingress**: Allow unauthenticated (API), private (worker)

---

## Database Architecture

### Schema Design

**Core Entities:**
```
Franchise (tenant root)
├── Location (studios)
├── User (authentication)
│   └── UserSession (session tracking)
├── Customer/Member
│   ├── Membership
│   │   ├── MembershipCancellation
│   │   ├── MembershipRenewal
│   │   └── FrozenMembership
│   └── Lead
├── Session/Appointment
├── Practitioner (VSP)
└── PrecomputedDailyMetrics (analytics cache)
```

### PostgreSQL Configuration

```yaml
# Production settings (Terraform)
database_flags:
  max_connections: 200
  shared_buffers: 256MB

# Local development (docker-compose)
shared_buffers: 8GB
effective_cache_size: 24GB
max_connections: 200
work_mem: 64MB
maintenance_work_mem: 512MB
```

### Query Performance

- **Query Insights**: Enabled with 1024-byte query strings
- **Application Tags**: Enabled for query attribution
- **Client IP Recording**: Enabled for debugging
- **Pre-computed Tables**: Aggregated daily metrics for fast dashboard loading

---

## Backup & Disaster Recovery

### Cloud SQL Backups

| Setting | Value |
|---------|-------|
| Automated Backups | Enabled |
| Backup Window | 3:00 AM UTC |
| Retention | 7 backups |
| Point-in-Time Recovery | Enabled |
| Transaction Log Retention | 7 days |
| Maintenance Window | Sunday 4:00 AM UTC |

### Recovery Procedures

**Point-in-Time Recovery:**
```bash
# Restore to specific timestamp
gcloud sql instances restore-backup <instance> \
  --restore-instance=<target> \
  --backup-id=<backup-id>
```

**Cross-Region Recovery:**
- Backups can be restored to different regions
- Database replication available for critical workloads

### Cloud Storage Lifecycle

| Object Type | Retention | Action |
|-------------|-----------|--------|
| Temp files (`temp/`) | 1 day | Delete |
| Exports (`exports/`) | 30 days | Move to NEARLINE |
| Exports (NEARLINE) | 90 days | Delete |

### Deletion Protection

- **Production**: `deletion_protection = true`
- **Non-production**: Configurable via Terraform variable

---

## High Availability

### Cloud Run Auto-Scaling

| Service | Min Instances | Max Instances | Scale Trigger |
|---------|---------------|---------------|---------------|
| Backend | 1 | 10 | CPU utilization, request count |
| Worker | 0 | 5 | Pub/Sub queue depth |

### Health Endpoints

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `/api/v1/health` | Basic health check | Monitoring |
| `/api/v1/health/live` | Liveness probe | Cloud Run |
| `/api/v1/health/ready` | Readiness probe | Cloud Run |
| `/api/v1/health/dependencies` | Full dependency check | Operations |

### Pub/Sub Reliability

| Setting | Value |
|---------|-------|
| Message Retention | 7 days (main), 14 days (DLQ) |
| Ack Deadline | 600 seconds |
| Max Delivery Attempts | 5 |
| Retry Backoff | 10s - 600s |
| Exactly-Once Delivery | Enabled |

### Database High Availability

- **Connection Pooling**: Prisma built-in connection management
- **Automatic Failover**: Cloud SQL HA configuration available
- **Read Replicas**: Configurable for read-heavy workloads

---

## Monitoring & Observability

### Logging

| Component | Logger | Format |
|-----------|--------|--------|
| Backend | Pino | JSON structured |
| Frontend | Console | Development only |
| Nginx | Access logs | Combined format |

### Prometheus Metrics

| Exporter | Port | Metrics |
|----------|------|---------|
| PostgreSQL | 9187 | Connections, transactions, query performance |
| Nginx | 9113 | Requests, connections, response times |

### Cloud Monitoring

| Service | Integration |
|---------|-------------|
| Cloud Run | Built-in metrics and logging |
| Cloud SQL | Query insights, performance metrics |
| Pub/Sub | Message delivery metrics |
| Cloud Build | Build success/failure tracking |

### Alerting (Recommended)

```yaml
# Example Cloud Monitoring alert policies
- name: High Error Rate
  condition: error_rate > 1%
  duration: 5 minutes

- name: Database Connection Saturation
  condition: connection_count > 180
  duration: 2 minutes

- name: Worker Queue Depth
  condition: unacked_messages > 1000
  duration: 10 minutes
```

### API Health Dashboard

Interactive health dashboard at `/api/v1/health/api-checker`:
- Manual endpoint testing
- Category filtering
- Performance visualization
- Slow endpoint highlighting (>50ms)

---

## Data Upload Specifications

### Supported Upload Types

The system supports 18+ file types with automatic detection based on CSV headers.

| File Type | Purpose | Priority | Key Headers |
|-----------|---------|----------|-------------|
| Staff Roster | VSP email mapping | 0 | `First Name`, `Last Name`, `Customer Email` |
| Primary Leads/Customers | Initial customer creation | 1 | `Type`, `Join date`, `Aggregator` |
| Customer List | Email/contact updates | 2 | `Customer ID`, `# of visits`, `LTV` |
| Practitioner Attendance | Relationships | 3 | `Staff Name`, `Clocked In/Out` |
| Appointments | Session data | 6 | `Date`, `Location`, `Customer Email` |
| Memberships | Contracts | 7 | `Bought Date/Time`, `Purchase ID` |
| Cancellations | Churn tracking | 8 | `Cancelled At`, `Reason` |
| Renewals | Forecasting | 10 | `Payment Method`, `Amount`, `Date` |
| Gift Cards | Revenue | 12 | `Code`, `Amount Left`, `Sold At` |
| Momence Payments | Authoritative revenue | 13 | `Category`, `Item`, `Sale Value` |
| Retail | Product sales | 14 | `Product`, `Variant`, `Wholesale Price` |
| Payroll | Compensation | 15 | `Staff Name`, `Base Pay`, `Pay Period` |
| Time Tracking | Hours worked | 16 | `Clocked In/Out`, `Duration` |
| Commissions | Earnings | 17 | `Commissions Earned` |

### Upload Processing Order

Files are processed in dependency order (priority 0 first):

1. **Staff Roster** (0) - Must run first for VSP mapping
2. **Primary Leads/Customers** (1) - Initial customer creation
3. **Customer List** (2) - Updates existing customers
4. **Practitioner Attendance** (3) - Establishes relationships
5. **All other types** (4-17) - Processed in priority order

### File Format Requirements

**General Requirements:**
- File format: CSV (comma-separated)
- Encoding: UTF-8
- Headers: First row must contain column names
- Date formats: `YYYY-MM-DD` or `YYYY-MM-DD, HH:MM AM/PM`
- Currency: Numeric with optional `$` prefix (e.g., `150.00`)
- Booleans: `Yes`/`No`, `True`/`False`, or `1`/`0`

**Example: Memberships CSV**
```csv
Membership,Purchased At,Price,First Name,Last Name,Customer Email,Start Date,Sold By
2 Hours/Month,2025-12-01 2:30 PM,100.00,Jane,Doe,jane@email.com,2025-12-01,John Smith
1 Hour/Month,2025-12-02 10:00 AM,75.00,Bob,Wilson,bob@email.com,2025-12-02,Jane Smith
```

**Example: Appointments CSV**
```csv
Date,Location,First Name,Last Name,Customer Email,Staff member,Service,Duration,Revenue
2025-12-20,Eden Prairie,Jane,Doe,jane@email.com,John Smith,60-Min Massage,60,100.00
```

### ZIP File Uploads

For bulk practitioner files, ZIP archives are supported:

**Supported File Naming:**
```
momence-commissions-{practitioner-name}.csv
momence-payroll-appointments-{practitioner-name}.csv
momence-staff-time-{practitioner-name}.csv
```

The system extracts the ZIP and processes each file with the practitioner name from the filename.

### Batch Processing Features

| Feature | Description |
|---------|-------------|
| Duplicate Detection | SHA-256 file hashing prevents re-importing |
| Rollback | Batches can be superseded to undo imports |
| Audit Trail | All uploads logged with user and timestamp |
| Error Reporting | Row-level error messages with line numbers |
| Validation | Type checking, format validation, required fields |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/ingest/batch/{type}` | POST | Upload CSV file |
| `/api/v1/ingest/batch/status/{id}` | GET | Check batch status |
| `/api/v1/ingest/batch/history` | GET | View upload history |
| `/api/v1/ingest/batch/supersede/{id}` | POST | Rollback a batch |

### Error Handling

Common errors and resolutions:

| Error | Cause | Resolution |
|-------|-------|------------|
| "File has already been imported" | Duplicate file hash | Use different file or supersede previous batch |
| "Missing required columns" | Header mismatch | Verify column names match expected format |
| "Invalid date format" | Unsupported format | Use `YYYY-MM-DD` or `YYYY-MM-DD, HH:MM AM/PM` |
| "Location not found" | Unknown location | Use location names matching your franchise setup |

---

## What's Next (Roadmap)

### Full Momence API Integration (TBD)

**Current State:** Data is imported via manual CSV file uploads from Momence exports.

**Future State:** Full API integration with Momence for real-time, automated data synchronization.

| Feature | Status | Description |
|---------|--------|-------------|
| Real-time Appointments | TBD | Automatic sync of new bookings |
| Member Updates | TBD | Live membership status changes |
| Payment Webhooks | TBD | Instant revenue recording |
| Two-way Sync | TBD | Push data back to Momence |

**Benefits of Full Integration:**
- Eliminate manual CSV uploads
- Real-time dashboard updates
- Reduced data latency (minutes vs. daily)
- Automatic error detection and alerting
- Reduced operational overhead

**Current Workaround:**
Users must export data from Momence and upload CSV files through the Admin panel. The upload system supports:
- Automatic file type detection
- Batch processing with rollback
- Duplicate detection
- Priority-based processing order

### Ads Reporting (TBD)

**Planned Features:**
- Google Ads integration
- Facebook/Meta Ads integration
- Lead attribution tracking
- Cost per acquisition (CPA) metrics
- Return on ad spend (ROAS) calculations
- Campaign performance dashboards
- Multi-touch attribution modeling

**Current State:** Lead source tracking is available through CSV uploads, but automated ad platform integration is not yet implemented.

### Additional Planned Enhancements

| Feature | Priority | Description |
|---------|----------|-------------|
| Mobile App | Medium | Native iOS/Android dashboards |
| Advanced AI Insights | Medium | Predictive analytics, churn prediction |
| Multi-language Support | Low | i18n for international franchises |
| Custom Report Builder | Medium | User-defined report templates |
| SMS Alerts | Low | Critical metric notifications |

---

## API Reference

All API endpoints are prefixed with `/api/v1/` and require JWT authentication unless noted.

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | JWT login (backdoor dev mode) |
| `/auth/google` | GET | Google OAuth redirect |
| `/auth/google/callback` | GET | Google OAuth callback |
| `/auth/me` | GET | Current user info |
| `/auth/logout` | POST | End session |
| `/auth/refresh` | POST | Token refresh |

### KPIs & Financial Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kpi/overview` | GET | Basic KPIs (clients, sessions, revenue) |
| `/kpi/financial-summary` | GET | Revenue metrics with monthly breakdown |
| `/kpi/precomputed` | GET | Pre-computed daily metrics (fast) |

### Timeline & Scheduling

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/timeline/comprehensive-metrics` | GET | Daily revenue, profit, payout, utilization |
| `/timeline/appointment-heatmap` | GET | Day/hour booking patterns |
| `/timeline/franchise-fees` | GET | Fee breakdown over time |
| `/schedule/heatmap` | GET | Booking heatmap with timezone support |
| `/schedule/drill-down` | GET | Cell-level appointment details |
| `/schedule/day-drill-down` | GET | Day-level appointment details |
| `/schedule/gaps` | GET | Scheduling gap analysis |

### Customer Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/customers-analytics/lifecycle` | GET | Customer journey stages |
| `/customers-analytics/cohort-retention` | GET | Retention by signup month |
| `/customers-analytics/segments` | GET | Customer segmentation |
| `/customers` | GET | List customers with filters |
| `/customers/:id` | GET | Customer details |

### Memberships

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/memberships` | GET | List memberships with filters |
| `/memberships/:id` | GET | Single membership details |
| `/memberships/renewal-analytics` | GET | Renewal rates by package |
| `/memberships/cancellation-analytics` | GET | Churn with MRR lost |
| `/memberships/upgrade-downgrade-analytics` | GET | Tier transitions |
| `/memberships/at-risk` | GET | At-risk members with usage metrics |
| `/memberships/expiring-soon` | GET | 30-day expiration forecast |

### Leads

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/leads` | GET | Lead list with follow-up priorities |
| `/leads/:id` | GET | Single lead details |
| `/leads/analytics` | GET | Lifecycle funnel and source attribution |

### Journey (Conversion Funnel)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/journey/funnel` | GET | Lead to member conversion funnel |
| `/journey/conversion-rates` | GET | Stage-by-stage conversion rates |

### Studios

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/studios/comparison` | GET | Cross-location benchmarks |
| `/studios/rankings` | GET | Studio performance rankings |
| `/studios/map-data` | GET | Geographic data for maps |

### VSP (Vital Stretch Practitioners)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vsp/stats` | GET | Summary statistics |
| `/vsp/performance` | GET | Practitioner metrics |
| `/vsp/appointments` | GET | Session list |
| `/vsp/time-tracking` | GET | Clock-in/out records |
| `/vsp/package-metrics` | GET | Package activation/redemption |
| `/vsp/commissions` | GET | Commission by pay period |
| `/vsp/bi-weekly-payroll` | GET | Payroll breakdown |
| `/vsp/service-by-vsp` | GET | Service matrix by practitioner |
| `/vsp/service-by-vsp-drilldown` | GET | Session details by VSP/service |
| `/vsp/utilization-drilldown` | GET | Hours breakdown per VSP |
| `/vsp/combined` | GET | All VSP data in single request |

### Retail Sales

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/retail/summary` | GET | Revenue, profit, transaction counts |
| `/retail/trends` | GET | Daily retail trends |
| `/retail/top-products` | GET | Best-selling products |
| `/retail/top-customers` | GET | Top retail customers |
| `/retail/by-location` | GET | Retail breakdown by studio |
| `/retail/monthly-trends` | GET | Monthly retail trends |
| `/retail/weekly-by-location` | GET | Weekly retail by studio |

### Gift Cards

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/gift-cards/summary` | GET | Sales, redemptions, liability |
| `/gift-cards/trends` | GET | Gift card trends over time |
| `/gift-cards/list` | GET | All gift cards with status |
| `/gift-cards/activity` | GET | Recent gift card activity |
| `/gift-cards/by-location` | GET | Gift cards by studio |

### Insights (AI-Powered)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/insights/goals` | GET | Goal tracking with Claude AI |
| `/insights/recommendations` | GET | AI-generated recommendations |
| `/insights/trends` | GET | Trend analysis |

### Franchises & Locations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/franchises` | GET | List franchises (admin sees all) |
| `/franchises/:id` | GET | Franchise details |
| `/franchises` | POST | Create franchise (admin only) |
| `/franchises/:id` | PUT | Update franchise |
| `/franchises/:id` | DELETE | Delete franchise (super admin) |
| `/franchises/:id/locations` | GET | Franchise locations |
| `/franchises/:id/locations` | POST | Add location |
| `/franchises/locations/:id` | PUT | Update location |
| `/franchises/locations/:id` | DELETE | Delete location |

### Momence Hosts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/momence/hosts` | GET | List Momence hosts |
| `/momence/hosts/:id` | GET | Host details |
| `/momence/hosts` | POST | Create Momence host |
| `/momence/hosts/:id` | PUT | Update Momence host |
| `/momence/hosts/:id` | DELETE | Delete Momence host |

### Momence Monitor (Real-Time Sync)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/momence/monitor/configs` | GET | Get monitor configurations |
| `/momence/monitor/configs` | POST | Create monitor config |
| `/momence/monitor/configs/:id` | PUT | Update monitor config |
| `/momence/monitor/configs/:id/check` | POST | Trigger manual check |
| `/momence/monitor/today-schedule` | GET | Today's combined schedule |
| `/momence/monitor/live-stats` | GET | Live statistics |
| `/momence/monitor/events` | GET | Recent activity events |
| `/momence/monitor/sessions/today` | GET | Today's sessions |
| `/momence/monitor/sales/today-summary` | GET | Today's sales summary |
| `/momence/monitor/check-in-board` | GET | Today's check-in board |
| `/momence/monitor/utilization/summary` | GET | Utilization summary |
| `/momence/monitor/utilization/by-location` | GET | Utilization by location |
| `/momence/monitor/utilization/by-hour` | GET | Utilization by hour |
| `/momence/monitor/utilization/peak-hours` | GET | Peak hours analysis |
| `/momence/monitor/conversion/funnel` | GET | Intro conversion funnel |
| `/momence/monitor/conversion/by-practitioner` | GET | Conversion by VSP |
| `/momence/monitor/teachers` | GET | Teacher/practitioner list |
| `/momence/monitor/teachers/performance` | GET | Teacher performance stats |
| `/momence/monitor/members` | GET | Members with filters |
| `/momence/monitor/members/at-risk` | GET | At-risk members report |
| `/momence/monitor/alerts` | GET | Active alerts |
| `/momence/monitor/alerts/counts` | GET | Alert counts by priority |

### Data Ingestion

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ingest/batch/{type}` | POST | Upload CSV file (batch mode) |
| `/ingest/batch/status/{id}` | GET | Check batch status |
| `/ingest/batch/history` | GET | View upload history |
| `/ingest/batch/supersede/{id}` | POST | Rollback a batch |
| `/ingest/zip` | POST | Upload Momence ZIP archive |

### Reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reports/generate-pdf` | POST | Generate PDF from HTML content |

### Users & Admin

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users` | GET | List users |
| `/users` | POST | Create user |
| `/users/:id` | PUT | Update user |
| `/users/:id` | DELETE | Delete user |
| `/franchisee-settings` | GET | Franchise configuration |
| `/franchisee-settings` | PUT | Update settings |

### Filter Options

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/filter-options/locations` | GET | Available locations |
| `/filter-options/practitioners` | GET | Available VSPs |
| `/filter-options/services` | GET | Available service types |

### Audit & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/audit-log` | GET | Activity history |
| `/audit-log/security-events` | GET | Security monitoring |

### Health Checks

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Basic health check | No |
| `/health/live` | GET | Liveness probe | No |
| `/health/ready` | GET | Readiness probe | No |
| `/health/dependencies` | GET | Full dependency check | No |
| `/health/api-checker` | GET | Interactive API tester | No |

### Common Query Parameters

Most analytics endpoints support these filters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `startDate` | string | Start date (YYYY-MM-DD) |
| `endDate` | string | End date (YYYY-MM-DD) |
| `franchiseId` | string | Franchise UUID (admin/franchisor only) |
| `locationIds` | string[] | Filter by location UUIDs |
| `practitionerId` | string | Filter by practitioner UUID |
| `compareMode` | string | `prior_period` or `prior_year` |

### Response Format

All API responses follow this structure:

```json
{
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 25
  }
}
```

Error responses:

```json
{
  "statusCode": 400,
  "message": "Validation failed",
  "error": "Bad Request"
}
```

### Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| General API | 300 req/min |
| Auth endpoints | 10 req/min |

---

## Support & Resources

### Documentation

| Document | Audience | Content |
|----------|----------|---------|
| [README](README.md) | Franchisors | Features, security overview, upload guide |
| Technical README (this document) | Architects, DevOps | Full technical specifications |
| API Documentation | Developers | `/api/docs` (Redoc UI) |

### Contact

For technical support, contact your development team or system administrator.

---

## Environment Variables

### Backend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `DATABASE_URL_FRANCHISE` | Franchise database connection | `postgresql://user:pass@host:5432/franchise` |
| `JWT_SECRET` | Secret for JWT signing | `your-256-bit-secret` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | `xxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | `GOCSPX-xxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3000` |
| `NODE_ENV` | Environment mode | `development` |
| `ANTHROPIC_API_KEY` | Claude AI API key | - |
| `SMTP_HOST` | Email server host | - |
| `SMTP_PORT` | Email server port | `587` |
| `SMTP_USER` | Email username | - |
| `SMTP_PASS` | Email password | - |
| `REDIS_URL` | Redis connection URL | - |
| `GCP_PROJECT_ID` | Google Cloud project | - |
| `PUBSUB_TOPIC` | Pub/Sub topic name | - |

---

## Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| `AUTH_001` | Invalid or expired token | Re-authenticate |
| `AUTH_002` | Insufficient permissions | Contact admin for role upgrade |
| `FRAN_001` | Franchise not found | Verify franchise ID |
| `FRAN_002` | Location not found | Verify location ID |
| `ING_001` | Duplicate file detected | Use supersede to replace |
| `ING_002` | Invalid CSV format | Check column headers |
| `ING_003` | Missing required columns | See upload documentation |
| `RATE_001` | Rate limit exceeded | Wait and retry |

---

## Performance Benchmarks

| Operation | Target | P95 |
|-----------|--------|-----|
| Dashboard load | < 2s | 1.5s |
| KPI overview | < 500ms | 400ms |
| CSV upload (10k rows) | < 30s | 25s |
| PDF generation | < 10s | 8s |
| Heatmap render | < 1s | 800ms |

---

## Legal

**Proprietary Software** - This software is not open source.

Copyright © 2026 KJ Vital Holdings Inc. All rights reserved.

This software, including all source code, documentation, and associated materials, is the exclusive intellectual property of KJ Vital Holdings Inc. This software is confidential and proprietary.

**Restrictions:**
- No unauthorized copying, distribution, or modification
- No reverse engineering or decompilation
- No sublicensing or transfer of rights
- Licensed exclusively for The Vital Stretch franchise network

All contributions to this codebase become the property of KJ Vital Holdings Inc.

For licensing inquiries, contact KJ Vital Holdings Inc.

---

**Document Version:** 1.1
**Last Updated:** January 2026
**Platform Version:** The Vital Stretch Dashboard v1.0
**IP Owner:** KJ Vital Holdings Inc.
