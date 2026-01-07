# The Vital Stretch - Franchise Analytics Dashboard

## Overview

The Vital Stretch Dashboard is a B2B franchise analytics platform for The Vital Stretch franchise network, providing real-time performance insights, financial tracking, and operational intelligence.

**Technical details**: See [Technical README](TECHNICAL_README.md)

---

## Quick Start

1. **Sign in** via Google OAuth at the dashboard URL
2. **Overview Tab** - Start here for a high-level snapshot of franchise and studio performance
3. **Studios Tab** - Compare studio performance side-by-side with rankings and trends
4. **Use Filters** - Filter by date range, franchise, studio, or practitioner across all views
5. **Export Reports** - Download CSV exports or generate PDF executive reports

---

## Uploading Data

### How to Upload

1. Click the **Upload** button in the header
2. **Select Franchise** (Franchisor/Super Admin only)
3. **Select Momence Host** - Choose which studio location the data belongs to
4. **Drag & drop** files or click "Choose Files"
5. Review detected file types and click **Upload**

### Supported File Formats

**ZIP Files** (Recommended)
- `momence-{hostId}-{timestamp}.zip` - Momence export archives containing multiple CSV files

**CSV Files** - Upload individual reports from Momence:

| File Type | Description |
|-----------|-------------|
| **Appointments** | Creates sessions, practitioners, customers |
| **Memberships** | Membership sales and contracts |
| **Membership Cancellations** | Cancelled membership records |
| **Membership Renewals** | Renewal payment records |
| **Frozen Memberships** | Temporarily frozen memberships |
| **New Leads & Customers** | Lead and customer creation |
| **Leads Converted** | Lead conversion tracking |
| **Customer List Report** | Customer email and profile updates |
| **Gift Cards** | Gift card sales and redemptions |
| **Refunds** | Refund transactions |
| **Retail/Product Sales** | Product sales with margins |
| **Momence Payments Report** | Payment transactions |
| **Staff Time Tracking** | Practitioner time entries |
| **Commissions** | Commission payouts |
| **Payroll** | Payroll appointment data |
| **Attendance** | Staff clock-in/out records |
| **Customer Referral Rewards** | Referral tracking |

### Upload Order Or all together (Recommended)

For best results, upload files in this order:
1. **Appointments/Attendance** - Creates sessions, practitioners, customers
2. **Memberships** - Establishes member contracts
3. **Lifecycle Events** - Renewals, Frozen, Cancellations
4. **Payments & Sales** - Refunds, Gift Cards, Retail
5. **Leads & Customers** - Enriches customer profiles

### Tips

- **Batch Mode** (enabled by default) allows rollback if errors occur
- **Magic Upload** auto-detects file types based on headers
- Memberships are identified by having "Hours/Month" in the name
- Renewals are automatically credited to the original seller
- Future bookings are excluded from appointments & VSP stats

---

## User Roles

| Role | Access |
|------|--------|
| Super Admin | Full system access With JIT (just in time) access to franchisor data |
| Franchisor | All franchises visibility |
| Owner | Own franchise only |
| General Manager | Assigned locations |
| Studio Lead | Assigned studios |
| Manager | Limited location access |
| Staff | View-only |

---

## Dashboard Tabs

### Analytics
- **Overview** - KPIs, revenue charts, membership health, network benchmarking
- **Timeline** - Daily trends, appointment heatmaps, utilization, franchise fees
- **Studios** - Cross-studio comparison, rankings, geographic analysis

### Customer Intelligence
- **Customers** - Segmentation (VIP, At-Risk, New), LTV, cohort retention
- **Memberships** - MRR, churn, renewals, at-risk alerts, expiration forecasts
- **Leads** - Scoring, 4-stage conversion funnel, source attribution

### Operations
- **Journey** - Lead-to-member conversion funnel with drop-off tracking
- **Schedule** - Booking heatmaps, gap analysis, capacity planning
- **VSP Performance** - Practitioner utilization, commissions, rebooking rates

### Business
- **Retail** - Product sales, profit margins, category breakdown
- **Gift Cards** - Sales, redemptions, liability reporting
- **Insights** - AI-powered goal tracking and recommendations

### Admin
- **Franchises** - Location management, territory mapping, Momence config
- **Admin** - CSV uploads, franchise settings, goals, timezone setup
- **Monitoring** - Live sync status, today's schedule, check-in boards, audit logs

---

## Reporting

### Exports
- **CSV** - Available on all tabs for filtered data
- **PDF** - Executive reports with YoY comparisons and cash flow projections

### Scheduled Reports
- Daily: 7:00 AM local
- Weekly: Sunday 8:00 AM
- Monthly: 1st of month 9:00 AM

### Filters
- Date range (custom, week, month, quarter, year)
- Franchise / Studio / Practitioner
- Service type
- Compare mode (prior period or YoY)

Save filter presets for quick access.

---

## Demo Mode

Explore the dashboard with sample data using demo franchises:
- **Fort Collins** (Colorado, 3 Studios) - Healthy
- **NW Arkansas** (Arkansas, 2 Studios) - Good
- **Lexington** (Kentucky, 2 Studios) - Moderate
- **New London** (Connecticut, 1 Studio) - Struggling
- **Franchisor Admin** - Multi-franchise oversight view

Demo uses sample data. Your real franchise data is not affected.

---

## Security

- **HTTPS/TLS** encryption on all data
- **Google OAuth 2.0** authentication
- **Role-based access control** with franchise data isolation
- **Audit logging** of all user activity
- **Rate limiting** (300 req/min per user)

---

## Infrastructure

- **Google Cloud Platform** - Cloud Run, Firebase Hosting
- **PostgreSQL** database with automated backups
- **Redis** caching for performance
- **Global CDN** for fast delivery

---

## Glossary

| Term | Definition |
|------|------------|
| **MRR** | Monthly Recurring Revenue from active memberships |
| **LTV** | Lifetime Value - total revenue from a customer |
| **VSP** | Vital Stretch Practitioner - staff providing services |
| **Churn** | Rate of membership cancellations |
| **At-Risk** | Members showing signs of potential cancellation |
| **Intro** | Introductory session for new customers |
| **Momence** | Point-of-sale and booking system used by studios |

---

## Browser Support

- Edge (recommended)
- Chrome
- Firefox
- Safari

Mobile browsers supported for viewing; uploads recommended on desktop.

---

## Support

Contact **Joe Vandermark** for dashboard support and access requests.

---

## Legal

**Proprietary Software** - This software is not open source.

Copyright © 2026 **KJ Vital Holdings Inc.** All rights reserved.

This software and its documentation are the exclusive intellectual property of KJ Vital Holdings Inc. Unauthorized copying, distribution, modification, or use of this software is strictly prohibited. This software is licensed exclusively for use by The Vital Stretch franchise network.

**IP Owner:** KJ Vital Holdings Inc.

---

*The Vital Stretch Dashboard v1.0*
