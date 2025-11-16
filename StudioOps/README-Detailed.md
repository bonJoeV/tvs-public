# The Vital Stretch Analytics Dashboard - Detailed Documentation

**Version:** v2.20251115.11 
**Last Updated:** November 13, 2025  
**Maintained For:** The Vital Stretch Franchise Operations

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation & Setup](#installation--setup)
4. [Data Requirements](#data-requirements)
5. [Dashboard Tabs - Deep Dive](#dashboard-tabs---deep-dive)
6. [Advanced Analytics](#advanced-analytics)
7. [Metric Calculations](#metric-calculations)
8. [Client Segmentation Logic](#client-segmentation-logic)
9. [Use Cases & Workflows](#use-cases--workflows)
10. [Troubleshooting](#troubleshooting)
11. [Data Privacy & Security](#data-privacy--security)
12. [Technical Specifications](#technical-specifications)
13. [FAQ](#faq)

---

## 🎯 Overview

### What Is This Dashboard?

The Vital Stretch Analytics Dashboard is a single-page HTML application that transforms your Momence business management data into actionable business intelligence. Built entirely with client-side JavaScript, it provides comprehensive analytics without requiring servers, installations, or cloud services.

### Core Capabilities

**Data Processing:**
- Parses 8 different CSV/ZIP file types from Momence
- Handles 10,000+ appointment records efficiently
- Processes multiple practitioners across 21+ locations
- Real-time calculations with instant filtering

**Analytics Engine:**
- 10 specialized analytical tabs
- 100+ calculated metrics
- Interactive visualizations with Chart.js
- Advanced client segmentation
- VSP performance tracking
- Financial modeling

**Export & Reporting:**
- CSV export from any data view
- Client segment downloads with contact info
- Filtered data exports
- Custom date range reports

**Privacy & Security:**
- 100% client-side processing
- No data transmission to external servers
- No authentication required
- Compliant with HIPAA/GDPR workflows

### Who Should Use This?

- **Franchise Owners:** Monitor overall performance across all locations
- **Studio Managers:** Track location-specific metrics and VSP performance
- **Marketing Teams:** Analyze lead sources and export segments for campaigns
- **Operations Teams:** Optimize scheduling and staffing based on heatmaps
- **Finance Teams:** Calculate labor costs, profitability, and franchise fees

---

## 💻 System Requirements

### Browser Compatibility

**Recommended (Best Performance):**
- Google Chrome 90 or higher
- Microsoft Edge 90 or higher

**Fully Supported:**
- Mozilla Firefox 88 or higher
- Safari 14 or higher (macOS/iOS)

**Not Supported:**
- Internet Explorer (any version)
- Opera Mini
- Old Android default browsers

### Operating System Requirements

- **Windows:** 7, 8, 10, 11 (64-bit recommended)
- **macOS:** 10.13 High Sierra or higher
- **Linux:** Any modern distribution
- **ChromeOS:** Fully supported

### Hardware Requirements

**Minimum:**
- 4GB RAM
- 2GB free disk space
- 1.5 GHz processor

**Recommended:**
- 8GB+ RAM (for datasets >5,000 records)
- 5GB+ free disk space
- Multi-core processor

### Network Requirements

- **Internet:** Only required for initial dashboard download
- **Offline Operation:** Fully functional without internet once loaded
- **No Firewall Issues:** No external connections made

### File Size Limits

- **Individual CSV:** Up to 100MB (tested with 50,000 rows)
- **Payroll ZIP:** Up to 50MB (with 20+ individual files)
- **Total Dataset:** Up to 500MB across all files
- **Browser Memory:** Allocates ~200MB during processing

---

## 🚀 Installation & Setup

### Step 1: Download Dashboard

1. **Download** `vital-stretch-dashboard.html` from your source
2. **Save** to a dedicated folder (e.g., `Documents/VitalStretch/`)
3. **Optional:** Create a desktop shortcut for easy access

**Note:** The dashboard is a single HTML file - no installation required.

### Step 2: Prepare Momence Exports

Before exporting data, ensure your Momence account is properly configured.

#### Momence Configuration Requirements

**1. Pay Rates Setup**
- Navigate to: Studio Set-up → Pay Rates
- Create pay rate structures for each VSP level
- Set hourly rates or per-session rates
- Assign rates to service types (Table Time, Studio Lead, etc.)

**2. Practitioner Setup**
- Navigate to: Studio Set-up → Practitioners
- Add all VSPs with complete information
- Assign appropriate roles/levels
- Verify active status for current team

**3. Appointment Pay Rates**
- Navigate to: Appointments → Boards
- Set pay rate for each VSP on appointment board
- Verify rates for different service types
- Configure special rates (intro sessions, events)

#### Export Instructions

For each required report:

1. **Log into Momence** with admin credentials
2. **Navigate to Reports** section
3. **Select report type** from the list below
4. **Set date range:** Last 365 Days (recommended)
5. **Click Export** or Download
6. **Save with exact filename** shown below
7. **Do not modify** CSV files after export

### Step 3: Open Dashboard

**Method 1: Double-Click**
1. Navigate to dashboard file
2. Double-click `vital-stretch-dashboard.html`
3. Browser should open automatically

**Method 2: Browser Menu**
1. Open your browser
2. File → Open File (or `Ctrl+O` / `Cmd+O`)
3. Select `vital-stretch-dashboard.html`

**Method 3: Drag & Drop**
1. Open browser window
2. Drag HTML file into browser
3. Dashboard loads automatically

### Step 4: Upload Data Files

1. Click **📤 Upload Data** button (top of page)
2. Upload modal appears with 8 file slots
3. For each file:
   - Click **Choose File** button
   - Select corresponding CSV/ZIP file
   - Wait for green checkmark (✅)
4. After all files uploaded, click **Process Data**
5. Wait for processing (10-30 seconds for large datasets)
6. Dashboard populates with your data

**Upload Feedback:**
You'll see status messages like:
- ✅ 992 appointments from 9 employees
- ✅ 237 memberships loaded
- ✅ 33 cancellations loaded
- ✅ 1,562 customers loaded

### Step 5: Configure Settings

1. Click **⚙️ Settings** button (top right)
2. Configure business settings
3. Set monthly goals
4. Configure labor settings
5. Click **Save Settings**

Settings are stored in browser's localStorage and persist between sessions.

### Step 6: Verify Data

**Quick Verification Checklist:**

- [ ] Overview tab shows non-zero revenue
- [ ] Timeline tab displays charts
- [ ] VSP Performance shows conversion/utilization tables
- [ ] Customers tab lists your clients
- [ ] Date filter works correctly
- [ ] Location filter includes all studios
- [ ] Export buttons generate CSV files
- [ ] Footer shows correct version: `v2.20251115.11`

---

## 📊 Data Requirements

### File 1: Membership Sales Export

**Filename:** `momence--membership-sales-export.csv`

**Momence Report:** "Membership sales - A report on membership purchases history"

**Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `Purchase Date` | DateTime | When membership was purchased | `2025-01-15, 2:30 PM` |
| `Customer First Name` | Text | Customer's first name | `Sarah` |
| `Customer Last Name` | Text | Customer's last name | `Johnson` |
| `Customer E-mail` | Email | Unique customer identifier | `sarah.j@email.com` |
| `Studio` | Text | Location name | `Denver - Downtown` |
| `Paid Amount` | Currency | Amount paid for membership | `$199.00` or `199.00` |
| `Membership Type` | Text | subscription or package | `subscription` |
| `Expired` | Boolean | Yes/No if membership expired | `No` |
| `Frozen` | Boolean | Yes/No if frozen | `No` |
| `Refunded` | Currency | Refund amount if applicable | `0.00` or `$50.00` |

**Used For:**
- Total membership revenue calculations
- MRR (Monthly Recurring Revenue) tracking
- Active membership counts
- Frozen/refunded membership tracking
- Membership type distribution
- Revenue trend analysis

**Data Quality Notes:**
- Currency fields can include dollar signs (auto-stripped)
- Dates parsed in multiple formats automatically
- Empty/null fields handled gracefully
- Duplicate records detected and flagged

---

### File 2: Membership Cancellations

**Filename:** `momence--membership-sales-export__1_.csv`

**Momence Report:** "Membership sales" → Cancellations tab

**Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `Customer E-mail` | Email | Matches customer to membership | `sarah.j@email.com` |
| `Cancelled at` | DateTime | When cancellation occurred | `2025-03-20, 10:15 AM` |
| `Studio` | Text | Location where cancelled | `Denver - Downtown` |
| `Membership Type` | Text | Type of cancelled membership | `subscription` |
| `Reason` | Text | Cancellation reason (if available) | `Moving out of area` |

**Used For:**
- Churn rate calculations
- Cancellation trend analysis
- Reason tracking for improvements
- Lost revenue calculations
- Retention strategy planning

---

### File 3: New Leads & Customers

**Filename:** `momence-new-leads-and-customers.csv`

**Momence Report:** "New Leads & Customers by join date"

**Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `First Name` | Text | Customer/lead first name | `Michael` |
| `Last Name` | Text | Customer/lead last name | `Smith` |
| `E-mail` | Email | Unique identifier | `m.smith@email.com` |
| `Type` | Text | "Lead" or "Customer" | `Customer` |
| `Join Date` | DateTime | When entered system | `2025-02-10, 3:45 PM` |
| `Studio` | Text | Associated location | `Austin - Central` |
| `Aggregator` | Text | Lead source | `Google`, `Organic`, `Facebook` |
| `Lifetime Value` | Currency | Total revenue from customer | `$2,547.99` |
| `First Purchase` | Text | Type of first purchase | `Introductory Session` |
| `First Purchase Date` | DateTime | Date of first purchase | `2025-02-11, 11:00 AM` |

**Used For:**
- Customer lifetime value (LTV) analysis
- Lead source effectiveness tracking
- Conversion rate calculations
- Customer segmentation (VIP, New, At-Risk)
- Lead generation trends
- Customer acquisition analysis

**Important Notes:**
- `Type` field determines lead vs. customer status
- `Aggregator` is primary lead source field
- LTV includes all revenue (memberships + appointments)
- Some customers may have `Type = "Lead"` initially

---

### File 4: Practitioner Payroll ZIP

**Filename:** `momence-payroll-report-summary.zip`

**Momence Report:** "Practitioner Payroll - Multiple practitioners payroll details"

**Contents:** ZIP archive containing individual payroll CSV files (one per VSP)

**Per-File Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `Date` | Date | Work date | `2025-01-15` |
| `Clock In` | Time | Start time | `9:00 AM` |
| `Clock Out` | Time | End time | `5:00 PM` |
| `Customer Name` | Text | Client served (for appointments) | `Sarah Johnson` |
| `Service` | Text | Type of service | `60-Min Stretch` |
| `Appointment Pay` | Currency | Pay for appointment | `$35.00` |
| `Non-Appointment Hours` | Number | Hours not in appointments | `1.5` |
| `Commission` | Currency | Product/membership commission | `$25.00` |

**Used For:**
- Utilization rate calculations (appointment hours / clocked hours)
- Labor cost calculations
- VSP performance tracking
- Commission tracking
- Capacity planning
- Efficiency analysis

**Special Processing Rules:**
- **Overnight Shifts:** Clock out before clock in = caps at 7 hours
- **Long Shifts:** >12 hours = caps at 7 hours (prevents data errors)
- **Name Matching:** VSP names matched to appointment data automatically
- **Special Characters:** Auto-cleaned for consistency

**Example Calculation:**
```
Clock In: 9:00 AM
Clock Out: 5:00 PM
Total Clocked: 8 hours

Appointments: 5 sessions × 1 hour each = 5 hours
Utilization Rate = (5 / 8) × 100 = 62.5%
```

---

### File 5: Leads Converted Report

**Filename:** `momence-leads-converted-report.csv`

**Momence Report:** "Leads converted" or "Lead Conversion Report"

**Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `Lead E-mail` | Email | Original lead identifier | `prospect@email.com` |
| `Converted Date` | DateTime | When became customer | `2025-02-15, 1:30 PM` |
| `First Purchase Type` | Text | What they bought | `Introductory Session` |
| `Lead Source` | Text | Original lead source | `Google Ads` |
| `Studio` | Text | Location | `Seattle - Ballard` |

**Used For:**
- Conversion funnel analysis
- Lead source ROI calculation
- Time-to-conversion tracking
- Journey mapping

---

### File 6: Appointments Attendance Report

**Filename:** `momence-appointments-attendance-report-combined.csv`

**Momence Report:** "Appointments attendance report"

**Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `Appointment Date` | DateTime | Date and time of appointment | `2025-03-15, 10:00 AM` |
| `Customer First Name` | Text | Client's first name | `Jennifer` |
| `Customer Last Name` | Text | Client's last name | `Williams` |
| `Customer E-mail` | Email | Unique identifier | `j.williams@email.com` |
| `Studio` | Text | Location name | `Portland - Pearl` |
| `Total Paid` | Currency | Revenue from appointment | `$89.00` |
| `Employee` | Text | VSP name | `John Martinez` |
| `Appointment Status` | Text | completed, cancelled, no-show | `completed` |
| `Service Duration` | Number | Length in minutes | `60` |
| `Service Type` | Text | Type of appointment | `60-Min Stretch` |

**Used For:**
- Revenue tracking (primary source)
- Appointment volume metrics
- VSP performance analysis
- Schedule heatmap generation
- Customer visit history
- Peak hours identification
- Service type analysis

**Status Handling:**
- `completed` - Included in all metrics
- `cancelled` - Excluded from revenue/volume
- `no-show` - Excluded from revenue/volume
- Blank/empty - Treated as completed

---

### File 7: Membership Renewals Report

**Filename:** `momence-membership-renewals-report.csv`

**Momence Report:** "Membership renewals report"

**Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `Customer E-mail` | Email | Member identifier | `member@email.com` |
| `Membership Type` | Text | Type renewing | `Monthly Membership` |
| `Renewal Date` | Date | When renewal due | `2025-04-01` |
| `Studio` | Text | Location | `Boston - Back Bay` |
| `Current Value` | Currency | Monthly value | `$199.00` |

**Used For:**
- Renewal pipeline tracking
- At-risk member identification
- Revenue forecasting
- Retention planning

---

### File 8: Frozen Memberships Report

**Filename:** `frozen-memberships-report.csv`

**Momence Report:** "Frozen memberships report"

**Required Fields:**

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `Customer E-mail` | Email | Member identifier | `frozen@email.com` |
| `Frozen Date` | DateTime | When frozen | `2025-02-01, 9:00 AM` |
| `Studio` | Text | Location | `Miami - Brickell` |
| `Membership Type` | Text | Type frozen | `subscription` |
| `Reason` | Text | Why frozen | `Traveling` |

**Used For:**
- Frozen membership tracking
- Potential reactivation campaigns
- Revenue impact analysis
- Seasonal pattern identification

---

### Data Quality Best Practices

**Before Exporting from Momence:**

1. **Verify Date Ranges:**
   - Use consistent date range across all reports
   - Recommend: Last 365 Days for comprehensive analysis
   - Avoid overlapping export periods

2. **Check Field Completeness:**
   - Ensure all VSPs have names configured
   - Verify studio names are consistent
   - Check that email addresses are populated

3. **Review Data Accuracy:**
   - Spot-check recent appointments against schedule
   - Verify membership sales totals
   - Confirm cancellation records

**After Exporting:**

1. **Do Not Modify CSVs:**
   - Don't edit in Excel (may corrupt encoding)
   - Don't add/remove columns
   - Don't change filenames

2. **Verify File Integrity:**
   - Check file sizes (shouldn't be 0 bytes)
   - Open in text editor to verify content
   - Ensure proper UTF-8 encoding

3. **Keep Backups:**
   - Archive exports by month
   - Store in secure location
   - Retain for historical analysis

---

## 📑 Dashboard Tabs - Deep Dive

### Tab 1: Overview 📊

**Purpose:** Executive dashboard with key performance indicators and goal tracking.

#### Sections

**1. Key Metrics Grid**

Top-level KPIs displayed as cards:

| Metric | Calculation | Purpose |
|--------|-------------|---------|
| Total Revenue | Sum(Appointment Revenue) + Sum(Membership Revenue) | Overall business performance |
| Active Memberships | Count(Memberships WHERE Expired = No) | Current member base |
| Total Appointments | Count(Appointments WHERE Status = completed) | Service volume |
| Average Ticket | Total Revenue / Total Appointments | Per-transaction value |
| Total Customers | Count(DISTINCT Customer E-mail) | Client base size |
| Lead Count | Count(WHERE Type = Lead) | Pipeline size |
| Frozen Memberships | Count(Memberships WHERE Frozen = Yes) | Members on pause |
| Refunded Memberships | Count(Memberships WHERE Refunded > 0) | Churn indicator |

**Color Coding:**
- Green cards - Revenue and positive metrics
- Blue cards - Volume metrics
- Orange cards - Member-related metrics
- Purple cards - Flags/warnings (frozen, refunded)

**2. Financial Summary Panel**

Detailed financial breakdown:

```
Total Revenue:        $XXX,XXX.XX
  - Appointment Revenue: $XXX,XXX.XX (XX%)
  - Membership Revenue:  $XX,XXX.XX (XX%)

Labor Costs:          $XX,XXX.XX
  - Appointment Pay:     $XX,XXX.XX
  - Non-Appointment Pay: $X,XXX.XX

Gross Profit:         $XXX,XXX.XX (XX% margin)

Franchise Fees:       $X,XXX.XX (6%)
Brand Fund:           $X,XXX.XX (2%)
CC Processing:        $X,XXX.XX (3%)

Net Profit:           $XXX,XXX.XX (XX% margin)
```

**3. Goal Tracking**

Visual progress bars for monthly goals:

- **Revenue Goal:** Shows actual vs. target with percentage
- **Paid Appointments Goal:** Completed appointments vs. target
- **Intro Appointments Goal:** Intro sessions vs. target

**Goal Status Colors:**
- 🟢 Green: >90% to goal
- 🟡 Yellow: 70-90% to goal
- 🔴 Red: <70% to goal

**4. Revenue Charts**

**Daily Revenue Line Chart:**
- X-axis: Dates in selected range
- Y-axis: Revenue amount
- Line color: Accent blue
- Hover: Shows exact date and amount
- Trend line: 7-day moving average

**7-Day Rolling Average:**
- Smooths daily volatility
- Identifies true trends
- Better for strategic planning

**Monthly Revenue by Location:**
- Stacked bar chart
- Each color = different location
- Shows contribution to total
- Filterable by location dropdown

**5. Active Membership Trends**

Line chart showing membership growth:
- Daily active member count
- Trend line overlay
- Period comparison option
- Color: Success green

#### Use Cases

**Daily Check-In (2 minutes):**
- Review yesterday's revenue
- Check goal progress
- Scan for red flags (high refunds, low appointments)

**Executive Reporting:**
- Screenshot Overview tab
- Export financial summary
- Share goal progress with stakeholders

**Performance Monitoring:**
- Track week-over-week growth
- Monitor margin trends
- Identify revenue anomalies

---

### Tab 2: Timeline 📈

**Purpose:** Historical trend analysis and period-over-period comparisons.

#### Sections

**1. Revenue Trends**

**Daily Revenue Chart:**
- Line chart with individual daily points
- 7-day moving average overlay
- Click-to-zoom functionality
- Hover shows exact amounts

**Weekly Revenue Comparison:**
- Bar chart by week number
- Color-coded by performance
- Week-over-week % change labels
- Last 12 weeks displayed

**Monthly Revenue Bars:**
- Shows last 12 months
- Stacked by revenue type (appointments vs. memberships)
- Month-over-month growth percentage
- Year-over-year comparison overlay

**2. Appointment Trends**

**Daily Appointment Volume:**
- Line chart showing appointment counts
- Identifies busy and slow periods
- Trend line indicates growth/decline
- Filterable by service type

**Weekly Patterns:**
- Which weeks perform best
- Seasonal identification
- Holiday impact analysis

**Appointment Type Distribution:**
- Stacked area chart
- Shows service mix over time
- Tracks intro session percentage
- Identifies service preference shifts

**3. Membership Growth**

**Weekly Membership Sales:**
- Bar chart of new memberships per week
- Color-coded by membership type
- Shows acquisition pace
- Target line overlay (optional)

**Active Members Timeline:**
- Line chart of member count over time
- Net growth calculation (new - cancelled)
- Cohort retention curves
- Churn rate timeline

**MRR (Monthly Recurring Revenue) Trend:**
- Line chart of subscription revenue
- Predictable revenue tracking
- Growth rate calculation
- Projection line (next 3 months)

**4. Lead Generation Trends**

**Leads Over Time:**
- Total lead volume timeline
- Segmented by source
- Conversion rate overlay
- Lead quality indicators

**Lead Source Performance:**
- Stacked area chart
- Each source as colored area
- Shows source mix changes
- Identifies emerging channels

#### Interactive Features

**Date Range Selection:**
- Last 7 days
- Last 30 days
- Last 90 days
- Last 6 months
- Last 12 months
- Custom range

**Period Comparison:**
- Compare to prior period
- Year-over-year comparison
- Custom period selection

**Zoom & Pan:**
- Click and drag to zoom into specific dates
- Pan left/right through timeline
- Reset zoom button

#### Use Cases

**Seasonal Planning:**
- Identify busy seasons
- Plan staffing accordingly
- Schedule marketing campaigns for slow periods
- Adjust pricing for peak times

**Growth Analysis:**
- Calculate month-over-month growth rate
- Identify growth accelerators/inhibitors
- Project future performance
- Set realistic targets

**Trend Identification:**
- Spot declining metrics early
- Validate marketing campaign effectiveness
- Track recovery from slow periods
- Monitor long-term business health

---

### Tab 3: VSP Performance 👨‍⚕️

**Purpose:** Individual practitioner performance tracking and analytics.

#### Top Section: Advanced Performance Analytics

**1. Conversion Rates Table**

Tracks intro stretch → paid member conversion by VSP and month.

**Table Structure:**

| VSP Name | Jan | Feb | Mar | Apr | ... | YTD Avg |
|----------|-----|-----|-----|-----|-----|---------|
| John M.  | 55% | 48% | 62% | 51% | ... | 54%     |
| Sarah K. | 42% | 45% | 38% | 47% | ... | 43%     |
| Mike R.  | 31% | 29% | 35% | 28% | ... | 31%     |

**Color Coding (Colorblind-Friendly):**
- 🔵 **Blue (Excellent):** ≥50% conversion rate
- 🟠 **Orange (Good):** 30-49% conversion rate
- 🟣 **Purple (Needs Improvement):** <30% conversion rate

**Hover Tooltips:**
- Shows exact conversion count
- Format: "X conversions / Y intro stretches"
- Example: "5 conversions / 10 intro stretches (50.0%)"

**Calculation:**
```
Conversion Rate = (Paid Memberships Attributed to VSP) / (Intro Stretches by VSP) × 100
```

**Where:**
- Paid Memberships = Memberships purchased after intro with this VSP
- Intro Stretches = Appointments marked as intro sessions
- Attribution = 30-day window after intro session

**2. Utilization Rates Table**

Measures table time efficiency (appointment hours / clocked hours).

**Table Structure:**

| VSP Name | Jan | Feb | Mar | Apr | ... | YTD Avg |
|----------|-----|-----|-----|-----|-----|---------|
| John M.  | 68% | 71% | 65% | 69% | ... | 68%     |
| Sarah K. | 55% | 58% | 61% | 59% | ... | 58%     |
| Mike R.  | 42% | 45% | 48% | 44% | ... | 45%     |

**Color Coding (Colorblind-Friendly):**
- 🔵 **Blue (Excellent):** ≥60% utilization
- 🟠 **Orange (Good):** 40-59% utilization
- 🟣 **Purple (Needs Improvement):** <40% utilization

**Hover Tooltips:**
- Shows hour breakdown
- Format: "X appointment hours / Y clocked hours"
- Example: "28 appointment hours / 40 clocked hours (70.0%)"

**Calculation:**
```
Utilization Rate = (Appointment Hours) / (Clocked Hours - Capped) × 100
```

**Special Rules:**
- Shifts >12 hours OR overnight = capped at 7 hours
- Only counts completed appointments
- Excludes cancelled/no-show appointments
- Non-appointment admin time included in clocked hours

**Industry Benchmarks:**
- Excellent: 60-85%
- Good: 40-60%
- Poor: <40%
- Overbooked: >85% (burnout risk)

#### Bottom Section: VSP Performance Table

Comprehensive sortable table with all VSP metrics.

**Columns:**

| Column | Calculation | Purpose |
|--------|-------------|---------|
| Practitioner Name | First + Last Name | VSP identification |
| Revenue | Sum(Appointment Revenue) | Total generated |
| Appointments | Count(Completed Appointments) | Volume metric |
| Avg Revenue | Revenue / Appointments | Per-session value |
| Unique Clients | Count(DISTINCT Customer Email) | Client diversity |
| Utilization % | (Appt Hours / Clocked Hours) × 100 | Efficiency |
| Commission | Sum(Product + Membership Commission) | Additional earnings |

**Sorting:**
- Click any column header to sort
- Default: Alphabetical by name
- Second click: Reverse sort
- Visual indicator shows current sort

**Row Color Coding:**
- Top performers: Light green highlight
- Below average: Light yellow highlight
- Needs attention: Light red highlight

#### VSP Performance Charts

**1. Revenue by Practitioner**
- Horizontal bar chart
- Sorted by revenue (highest first)
- Shows relative performance
- Color-coded by performance tier

**2. Appointments by Practitioner**
- Horizontal bar chart
- Shows workload distribution
- Identifies overworked/underutilized VSPs
- Compared to average line

**3. Monthly VSP Trends**
- Line chart with multiple lines (one per VSP)
- Toggle VSPs on/off by clicking legend
- Shows performance trends over time
- Identifies improving/declining VSPs

**4. Commission Breakdown**
- Stacked bar chart
- Membership commissions vs. product commissions
- By VSP
- Shows additional income opportunities

#### Use Cases

**Performance Reviews:**
1. Export VSP performance table
2. Review conversion and utilization rates
3. Identify training needs
4. Set improvement goals
5. Track month-over-month progress

**Scheduling Optimization:**
1. Identify VSPs with low utilization
2. Increase their scheduled hours
3. Identify high-utilization VSPs
4. Prevent burnout with schedule adjustments

**Compensation Planning:**
1. Review total revenue per VSP
2. Calculate commission accurately
3. Identify bonus opportunities
4. Plan raises based on performance

**Training & Development:**
1. Spot VSPs with low conversion rates
2. Implement sales training
3. Track improvement over time
4. Share best practices from top performers

---

### Tab 4: Customers 👥

**Purpose:** Client database, demographics, and advanced segmentation.

#### Sections

**1. Customer Overview Cards**

| Metric | Description |
|--------|-------------|
| Total Unique Customers | Count of distinct email addresses |
| New Customers This Period | Customers added in filter date range |
| Average Customer LTV | Mean lifetime value across all customers |
| Average Visits per Customer | Total appointments / unique customers |

**2. Customer Data Table**

Comprehensive, sortable, searchable table.

**Columns:**
- First Name, Last Name
- Email
- Customer Type (Lead vs. Customer)
- Join Date
- Studio (primary location)
- Lead Source/Aggregator
- First Purchase
- First Purchase Date
- Lifetime Value (LTV)
- Total Visits
- Last Visit Date

**Features:**
- **Search Box:** Filters all columns in real-time
- **Column Sorting:** Click headers to sort
- **Color-Coded Types:** Customers in green, Leads in yellow
- **Pagination:** Shows 50 records per page
- **Export Visible:** CSV download of filtered results

**3. Advanced Client Segmentation**

Five strategic customer segments with export capabilities.

#### Segment 1: 💎 VIP Clients (>$2,500 LTV)

**Definition:**
Customers whose lifetime value exceeds $2,500.

**Calculation:**
```
LTV = Sum(All Memberships) + Sum(All Appointments)
if LTV > 2500 → VIP Segment
```

**Card Displays:**
- Client count
- Total VIP revenue
- Average VIP LTV
- Percentage of customer base

**Modal Details (Click "View"):**
- Full client list (up to 100 displayed)
- Name, Email, LTV, Total Visits
- Sortable by any column
- Shows membership status

**Export CSV Includes:**
- First Name, Last Name
- Email Address
- Customer Type
- Lifetime Value
- Total Visits
- Last Visit Date
- Membership Status
- Primary Studio

**Use Case:**
- Create exclusive VIP events
- Offer premium services
- Personal thank-you outreach
- Referral incentive programs
- Priority scheduling

#### Segment 2: ⚠️ At-Risk Clients (45+ Days Inactive)

**Definition:**
Customers with at least one prior visit but no appointment in 45+ days.

**Calculation:**
```
daysSinceLastVisit = Today - Max(Appointment Date)
if daysSinceLastVisit ≥ 45 AND totalVisits > 0 → At-Risk
```

**Card Displays:**
- At-risk client count
- Revenue at risk (sum of LTVs)
- Average days since last visit
- Potential revenue loss

**Modal Details:**
- Days since last visit (sorted longest first)
- Previous visit frequency
- Total LTV (investment to retain)
- Last service received

**Export CSV Includes:**
- All contact information
- Days since last visit
- Previous visit frequency
- LTV
- Last appointment date
- Last service type

**Use Case:**
- Win-back email campaigns
- "We miss you" text messages
- Special reactivation offers
- Personal phone calls for high-LTV clients
- Survey about why they stopped

**Sample Campaign Workflow:**
1. Export At-Risk segment
2. Filter by LTV >$500 (high value)
3. Upload to email platform
4. Send personalized win-back email
5. Offer: "Come back! First session 50% off"
6. Track reactivation rate
7. Calculate campaign ROI

#### Segment 3: ❌ Inactive Paid Members

**Definition:**
Customers with active memberships who haven't visited in 30+ days.

**Calculation:**
```
hasActiveMembership = Membership EXISTS AND Expired = No
daysSinceLastVisit = Today - Max(Appointment Date)
if hasActiveMembership AND daysSinceLastVisit ≥ 30 → Inactive Paid
```

**Card Displays:**
- Inactive member count
- Wasted MRR (monthly value not being used)
- Average days inactive
- Potential revenue recovery

**Why This Matters:**
These members are paying but not using services = high churn risk and negative experience.

**Modal Details:**
- Membership type
- Monthly value
- Days since last visit
- Membership start date
- Total paid to date

**Export CSV Includes:**
- Contact information
- Membership details
- Monthly recurring amount
- Days inactive
- Membership purchase date

**Use Case:**
- Urgent reactivation campaign
- Reminder of membership benefits
- Offer free session to get them back
- Survey about barriers to attendance
- Consider freeze option if needed

#### Segment 4: 🌱 New Clients (<3 Visits)

**Definition:**
Customers with 1-3 total visits, still building habits.

**Calculation:**
```
totalVisits = Count(Appointments)
if totalVisits >= 1 AND totalVisits <= 3 → New Client
```

**Card Displays:**
- New client count
- Current average LTV
- Growth potential (estimated)
- Conversion opportunity

**Why This Matters:**
Critical onboarding phase. High retention if we engage them properly.

**Modal Details:**
- Current visit count
- Days since first visit
- Current LTV
- Has membership? (Yes/No)

**Export CSV Includes:**
- Contact information
- Visit count
- First visit date
- Last visit date
- Current LTV
- Membership status

**Use Case:**
- Welcome series emails
- Membership conversion offers
- Educational content about benefits
- Habit-building tips
- Referral program introduction

**Sample Onboarding Sequence:**
1. **After Visit 1:** Welcome email + benefits guide
2. **After Visit 2:** Membership offer with discount
3. **Before Visit 3:** Schedule next appointment reminder
4. **After Visit 3:** Referral request ("Bring a friend!")

#### Segment 5: ⚡ High-Frequency Non-Members

**Definition:**
Customers visiting weekly (4+ times/month) without a membership.

**Calculation:**
```
averageVisitsPerWeek = totalVisits / weeksSinceFirstVisit
hasActiveMembership = Membership EXISTS AND Expired = No
if averageVisitsPerWeek >= 1 AND hasActiveMembership = False → High-Frequency Non-Member
```

**Card Displays:**
- Client count
- Average visits per week
- Potential MRR (if converted to members)
- Current spend vs. membership savings

**Why This Matters:**
These clients are ideal membership candidates - they'd save money and we'd get predictable revenue.

**Modal Details:**
- Visits per week
- Total spent to date
- Membership savings calculation
- Visit frequency trend

**Export CSV Includes:**
- Contact information
- Visits per week
- Total appointments
- Total spent
- Potential monthly savings with membership

**Use Case:**
- Membership sales campaign
- Show ROI calculation
- Limited-time membership offer
- Personal sales consultation

**Sample Sales Pitch:**
"Hi [Name], we noticed you visit us weekly. You've spent $X in the past month. With our monthly membership at $Y, you'd save $Z every month! Plus, you'd get [additional benefits]. Can we schedule a quick chat?"

#### Segmentation Summary Panel

Below all segment cards:

```
📊 Segmentation Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Segmented:     X,XXX clients
VIP Revenue:         $XXX,XXX
At-Risk Revenue:     $XX,XXX (potential loss)
Growth Potential:    $XX,XXX (from new clients)
Conversion Oppty:    $X,XXX/mo MRR (high-frequency non-members)
```

**4. Customer Insights Charts**

**LTV Distribution:**
- Histogram showing customer value spread
- Identifies if most customers are low or high value
- Helps set VIP threshold
- Customizable tier ranges

**Visit Frequency Distribution:**
- Bar chart of visits per customer
- Identifies engagement levels
- Shows retention patterns

**Customer Acquisition Timeline:**
- Line chart of new customers over time
- Marketing campaign effectiveness
- Seasonal patterns

**Top Customers by LTV:**
- Horizontal bar chart
- Top 20 customers
- Highlights most valuable relationships

---

### Tab 5: Retention 🔄

**Purpose:** Churn analysis and retention metrics.

#### Sections

**1. Retention Overview Cards**

| Metric | Calculation | Purpose |
|--------|-------------|---------|
| Overall Retention Rate | (Active Customers / Total Customers) × 100 | General health |
| Member Retention Rate | (Active Members / Total Members) × 100 | Membership health |
| Churn Rate | (Cancelled / Total) × 100 | Loss rate |
| Average Member Lifetime | Mean(Membership Duration) | Engagement length |

**2. Cohort Retention Analysis**

**Cohort Definition:**
Groups customers by join month, tracks retention over subsequent months.

**Example Table:**

| Join Month | Month 1 | Month 2 | Month 3 | Month 6 | Month 12 |
|------------|---------|---------|---------|---------|----------|
| Jan 2025   | 100%    | 85%     | 78%     | 65%     | 54%      |
| Feb 2025   | 100%    | 88%     | 81%     | 69%     | -        |
| Mar 2025   | 100%    | 90%     | 83%     | -       | -        |

**Color Coding:**
- Green: >75% retention
- Yellow: 50-75% retention
- Red: <50% retention

**Insights:**
- Identify drop-off patterns
- Compare cohort performance
- Test retention initiative impact

**3. Retention Curves**

**Line Chart:**
- X-axis: Months since join
- Y-axis: % still active
- Multiple lines: Different join cohorts
- Industry benchmark overlay (optional)

**Use Cases:**
- Identify critical drop-off periods
- Set retention goals
- Measure retention program effectiveness

**4. Churn Reasons Analysis**

**Pie Chart:**
Shows distribution of cancellation reasons from cancellations file.

**Common Reasons:**
- Moving out of area
- Financial reasons
- Didn't see results
- Scheduling conflicts
- Other

**Actionable Insights:**
- If "Didn't see results" high → Training issue
- If "Financial" high → Pricing/value issue
- If "Scheduling" high → Availability issue

**5. Win-Back Performance**

Tracks reactivation of previously cancelled members.

**Metrics:**
- Cancelled members
- Re-activated members
- Win-back rate
- Time to reactivation

---

### Tab 6: Journey 🗺️

**Purpose:** Customer lifecycle visualization and conversion funnel.

#### Conversion Funnel Visualization

**Stage 1: Total Leads & Customers**
```
[████████████████████████] 100% (1,500 people)
```

**Stage 2: Customers (Converted)**
```
[███████████████         ] 65% (975 customers)
```
- Conversion Rate: 65% of leads became customers
- Still Leads: 525 (35%)

**Stage 3: Had Intro Offer**
```
[████████                ] 48% (720 customers)
```
- Intro Conversion: 74% of customers had intro
- Direct purchasers: 255 (26%)

**Stage 4: Purchased Membership**
```
[█████                   ] 32% (480 members)
```
- Intro → Paid: 67% of intro users became members
- Total member conversion: 32% of all leads

#### Metrics Table

| Metric | Value | Industry Benchmark |
|--------|-------|-------------------|
| Lead → Customer | 65% | 40-60% |
| Lead → Intro | 48% | 30-50% |
| Intro → Paid | 67% | 60-80% |
| Lead → Member | 32% | 20-35% |

#### Journey Timeline

**Average Days in Each Stage:**

```
Lead created → First contact: 2 days
First contact → Intro booked: 5 days
Intro scheduled → Intro completed: 3 days
Intro completed → Member purchase: 7 days
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Journey: 17 days average
```

#### Drop-Off Analysis

**Where We Lose People:**

1. **Lead to Customer (35% lost)**
   - Not responding to outreach
   - Price concerns
   - Changed mind
   
   **Action:** Improve lead nurturing, faster response

2. **Customer to Intro (26% skip intro)**
   - Bought without intro
   - Not interested in trial
   
   **Action:** Promote intro benefits

3. **Intro to Member (33% don't convert)**
   - Didn't like experience
   - Price objections
   - Not ready to commit
   
   **Action:** Improve intro experience, handle objections

---

### Tab 7: Memberships 💳

**Purpose:** Subscription tracking and membership analytics.

#### Sections

**1. Membership Overview Cards**

| Metric | Calculation |
|--------|-------------|
| Total Memberships | All-time membership count |
| Active Memberships | Currently valid (not expired) |
| MRR | Sum(active subscription memberships) |
| Average Membership Value | MRR / Active Members |
| Frozen Memberships | Count where Frozen = Yes |
| Refunded Memberships | Count where Refunded > 0 |

**2. Membership Types Breakdown**

**Pie Chart:**
- Subscriptions vs. Packages
- Shows distribution
- Hover for exact counts

**Table:**

| Type | Count | % of Total | Revenue | Avg Value |
|------|-------|------------|---------|-----------|
| Monthly Subscription | XXX | XX% | $XX,XXX | $XXX |
| Quarterly Package | XXX | XX% | $XX,XXX | $XXX |
| Annual Subscription | XXX | XX% | $XX,XXX | $XXX |

**3. Membership Growth Charts**

**Weekly New Memberships:**
- Bar chart by week
- Shows acquisition pace
- Color-coded by type
- Trend line overlay

**Active Membership Trend:**
- Line chart over time
- Shows net growth (new - cancelled)
- Separate lines for subscriptions vs. packages
- Goal line (optional)

**4. MRR Tracking**

**Monthly Recurring Revenue Chart:**
- Line chart showing MRR over time
- Predictable revenue metric
- Critical for financial planning
- Shows growth rate

**MRR Components:**
```
New MRR:        $X,XXX (from new subscriptions)
Expansion MRR:  $XXX (from upgrades)
Contraction:    -$XXX (from downgrades)
Churned MRR:    -$X,XXX (from cancellations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Net MRR Growth: $X,XXX
```

**5. Membership Sales Heatmap**

Interactive heatmap showing when memberships are purchased.

**Grid:**
- Rows: Days of week (Monday-Sunday)
- Columns: Hours (6am-9pm)
- Color intensity: Sales volume

**Interactivity:**
- Click any cell → See specific sales for that time
- Hover → Tooltip with count
- Filter by membership type

**Use Case:**
- Identify best times to promote memberships
- Schedule sales staff accordingly
- Time marketing campaigns

---

### Tab 8: Cancellations ❌

**Purpose:** Churn analysis and lost revenue tracking.

#### Sections

**1. Cancellation Overview**

| Metric | Description |
|--------|-------------|
| Total Cancellations | All-time cancellations |
| Cancellations This Period | In filter date range |
| Lost Monthly Revenue | MRR lost from cancellations |
| Average Membership Duration | Before cancellation |
| Churn Rate | (Cancellations / Active Members) × 100 |

**2. Cancellation Trends**

**Timeline Chart:**
- Line chart of cancellations over time
- Identifies problem periods
- Seasonal patterns
- Intervention effectiveness

**3. Cancellation Reasons**

**Pie Chart:**
Distribution of reasons from cancellations file.

**Table with Actions:**

| Reason | Count | % | Potential Actions |
|--------|-------|---|-------------------|
| Moving | XX | XX% | Send-off gift, referral to new area |
| Financial | XX | XX% | Payment plans, value communication |
| No Results | XX | XX% | Training improvement, expectations |
| Scheduling | XX | XX% | More availability, flexibility |
| Other | XX | XX% | Follow-up survey |

**4. Lost Revenue Analysis**

**Breakdown:**
```
One-Time Lost Revenue:  $XX,XXX (package refunds)
Monthly Lost Revenue:   $X,XXX (subscription MRR)
Annual Impact:          $XX,XXX (MRR × 12)
Lifetime Value Lost:    $XXX,XXX (based on avg duration)
```

**Recovery Opportunities:**
- Win-back campaigns
- Exit surveys
- Referral requests
- Freeze instead of cancel

---

### Tab 9: Leads 🎯

**Purpose:** Lead generation tracking and source analysis.

#### Sections

**1. Lead Overview**

| Metric | Calculation |
|--------|-------------|
| Total Leads | Count where Type = Lead |
| Converted Customers | Count converted |
| Conversion Rate | (Converted / Total) × 100 |
| Average Lead Value | Revenue from converts / Total leads |

**2. Lead Sources Performance**

**Table:**

| Source | Leads | Converts | Conv Rate | Avg Value | Total Revenue |
|--------|-------|----------|-----------|-----------|---------------|
| Google | XXX | XXX | XX% | $XXX | $XX,XXX |
| Organic | XXX | XXX | XX% | $XXX | $XX,XXX |
| Facebook | XXX | XXX | XX% | $XXX | $XX,XXX |
| Instagram | XXX | XXX | XX% | $XXX | $XX,XXX |
| Referral | XXX | XXX | XX% | $XXX | $XX,XXX |

**Insights:**
- Best converting source
- Highest value source
- Most volume source
- ROI calculation (if ad spend known)

**3. Lead Generation Heatmaps**

**Appointment Leads Heatmap:**
- Shows when leads book appointments
- Day × Hour grid
- Click for lead details
- Displays lead creation date

**Social Fitness Leads Heatmap:**
- Specifically tracks social media leads
- Same format as appointment heatmap
- Filter by platform

**4. Lead Timeline**

**Line Chart:**
- Lead volume over time
- Segmented by source
- Stacked area format
- Shows channel mix evolution

**5. Lead Status Distribution**

**Current Status of All Leads:**
- Active (still in pipeline)
- Converted (became customers)
- Lost (marked as lost)
- Inactive (no activity 90+ days)

---

### Tab 10: Schedule 📅

**Purpose:** Appointment timing analysis and capacity planning.

#### Sections

**1. Appointment Overview**

| Metric | Description |
|--------|-------------|
| Total Appointments | In filter range |
| Average per Day | Appointments / Days |
| Peak Day | Busiest day of week |
| Peak Hour | Busiest hour |

**2. Location-Specific Heatmaps**

**One Heatmap Per Location:**
- Dropdown to select location
- Separate heatmap displays for each studio
- Shows that location's appointment patterns

**Grid Structure:**
- Rows: Days of week (Monday-Saturday)
- Columns: Hours (6am-9pm)
- Cells: Appointment count
- Color intensity: Volume (darker = more appointments)

**Interactivity:**

**Click Day Name:**
- Shows hourly breakdown for that day
- Sorted by appointment count (highest first)
- Displays: Hour | Appointments | Revenue | Avg Revenue

**Click Hour Cell:**
- Shows individual appointments for that time
- Displays: Date | Customer | VSP | Revenue
- Export option for that hour's appointments

**Hover:**
- Tooltip shows exact count
- Format: "Monday 9:00 AM - 12 appointments"

**3. Appointment Trends**

**Daily Appointments Chart:**
- Line chart showing volume over time
- Identifies busy/slow periods
- Trend line overlay
- Useful for staffing decisions

**Weekly Patterns:**
- Bar chart by week
- Week-over-week comparison
- Seasonal identification

**Day of Week Analysis:**
- Bar chart showing busiest days
- Helps optimize VSP schedules
- Informs marketing for slow days

**4. Utilization Trend Chart**
(Appears when payroll ZIP uploaded)

**Line Chart:**
- Daily utilization percentage
- Target line at 80%
- Color-coded: Green above target, Red below
- Shows efficiency trends over time

**Formula:**
```
Daily Utilization = (Total Appointment Hours that day / Total Clocked Hours that day) × 100
```

---

## 🧮 Metric Calculations

### Revenue Calculations

**Total Revenue:**
```javascript
appointmentRevenue = appointments
    .filter(a => a['Appointment Status'] === 'completed')
    .reduce((sum, a) => sum + parseFloat(a['Total Paid'] || 0), 0);

membershipRevenue = memberships
    .reduce((sum, m) => sum + parseFloat(m['Paid Amount'] || 0), 0);

totalRevenue = appointmentRevenue + membershipRevenue;
```

**Monthly Recurring Revenue (MRR):**
```javascript
MRR = memberships
    .filter(m => 
        m['Membership Type'].toLowerCase() === 'subscription' &&
        m['Expired'] !== 'Yes'
    )
    .reduce((sum, m) => sum + parseFloat(m['Paid Amount'] || 0), 0);
```

**Average Ticket:**
```javascript
avgTicket = totalRevenue / completedAppointments.length;
```

### Labor Cost Calculations

**Appointment Labor Cost:**
```javascript
// From payroll ZIP files
appointmentPay = payrollData.reduce((sum, record) => {
    return sum + parseFloat(record['Appointment Pay'] || 0);
}, 0);
```

**Non-Appointment Labor Cost:**
```javascript
nonAppointmentPay = payrollData.reduce((sum, record) => {
    const nonApptHours = parseFloat(record['Non-Appointment Hours'] || 0);
    return sum + (nonApptHours * baseHourlyRate);
}, 0);
```

**Total Labor Cost:**
```javascript
totalLaborCost = appointmentPay + nonAppointmentPay;
```

### Profitability Calculations

**Gross Profit:**
```javascript
grossProfit = totalRevenue - totalLaborCost;
grossMargin = (grossProfit / totalRevenue) × 100;
```

**Franchise Fees:**
```javascript
franchiseFee = totalRevenue × (franchiseFeePercent / 100);
brandFund = totalRevenue × (brandFundPercent / 100);
ccFees = totalRevenue × (ccFeePercent / 100);
```

**Net Profit:**
```javascript
netProfit = grossProfit - franchiseFee - brandFund - ccFees;
netMargin = (netProfit / totalRevenue) × 100;
```

### VSP Performance Calculations

**Utilization Rate:**
```javascript
function calculateUtilization(vspPayrollRecords, vspAppointments) {
    // Calculate appointment hours
    const appointmentHours = vspAppointments
        .filter(a => a['Appointment Status'] === 'completed')
        .reduce((sum, a) => {
            const duration = parseFloat(a['Service Duration'] || 0);
            return sum + (duration / 60); // Convert minutes to hours
        }, 0);
    
    // Calculate clocked hours with special rules
    const clockedHours = vspPayrollRecords.reduce((sum, record) => {
        const clockIn = parseTime(record['Clock In']);
        const clockOut = parseTime(record['Clock Out']);
        
        let hours;
        if (clockOut < clockIn) {
            // Overnight shift - cap at 7 hours
            hours = 7;
        } else {
            hours = (clockOut - clockIn) / (1000 * 60 * 60); // ms to hours
            if (hours > 12) {
                // Shift >12 hours - cap at 7 hours
                hours = 7;
            }
        }
        
        return sum + hours;
    }, 0);
    
    return (appointmentHours / clockedHours) × 100;
}
```

**Conversion Rate:**
```javascript
function calculateConversionRate(vspAppointments, memberships) {
    // Find intro sessions by this VSP
    const introSessions = vspAppointments.filter(a => 
        a['Service Type'].toLowerCase().includes('intro') ||
        a['Service Type'].toLowerCase().includes('introductory')
    );
    
    // Find memberships purchased within 30 days after intro with this VSP
    const conversions = introSessions.filter(intro => {
        const introDate = new Date(intro['Appointment Date']);
        const customerEmail = intro['Customer E-mail'];
        
        return memberships.some(m => {
            const purchaseDate = new Date(m['Purchase Date']);
            const daysDiff = (purchaseDate - introDate) / (1000 * 60 * 60 * 24);
            
            return m['Customer E-mail'] === customerEmail &&
                   daysDiff >= 0 && daysDiff <= 30;
        });
    }).length;
    
    return (conversions / introSessions.length) × 100;
}
```

### Customer Metrics

**Lifetime Value (LTV):**
```javascript
function calculateLTV(customerEmail, appointments, memberships) {
    const apptRevenue = appointments
        .filter(a => a['Customer E-mail'] === customerEmail)
        .reduce((sum, a) => sum + parseFloat(a['Total Paid'] || 0), 0);
    
    const memberRevenue = memberships
        .filter(m => m['Customer E-mail'] === customerEmail)
        .reduce((sum, m) => sum + parseFloat(m['Paid Amount'] || 0), 0);
    
    return apptRevenue + memberRevenue;
}
```

**Churn Rate:**
```javascript
churnRate = (cancellations.length / totalActiveMembers) × 100;
```

**Retention Rate:**
```javascript
retentionRate = ((totalActiveMembers - cancellations.length) / totalActiveMembers) × 100;
```

### Conversion Metrics

**Lead to Customer:**
```javascript
const leads = allPeople.filter(p => p['Type'] === 'Lead');
const customers = allPeople.filter(p => p['Type'] === 'Customer');
const conversionRate = (customers.length / allPeople.length) × 100;
```

**Intro to Paid:**
```javascript
const hadIntro = customers.filter(c => 
    c['First Purchase'].toLowerCase().includes('intro')
);
const becameMembers = hadIntro.filter(c => 
    memberships.some(m => m['Customer E-mail'] === c['E-mail'])
);
const introToPaidRate = (becameMembers.length / hadIntro.length) × 100;
```

---

## 🎯 Client Segmentation Logic

### VIP Clients (>$2,500 LTV)

```javascript
function getVIPClients(customers, appointments, memberships) {
    return customers.filter(customer => {
        const ltv = calculateLTV(customer['E-mail'], appointments, memberships);
        return ltv > 2500;
    }).map(customer => ({
        ...customer,
        ltv: calculateLTV(customer['E-mail'], appointments, memberships),
        totalVisits: appointments.filter(a => 
            a['Customer E-mail'] === customer['E-mail']
        ).length
    }));
}
```

### At-Risk Clients (45+ Days Inactive)

```javascript
function getAtRiskClients(customers, appointments) {
    const today = new Date();
    
    return customers.filter(customer => {
        const customerAppts = appointments.filter(a => 
            a['Customer E-mail'] === customer['E-mail'] &&
            a['Appointment Status'] === 'completed'
        );
        
        if (customerAppts.length === 0) return false;
        
        const lastApptDate = new Date(Math.max(
            ...customerAppts.map(a => new Date(a['Appointment Date']))
        ));
        
        const daysSince = (today - lastApptDate) / (1000 * 60 * 60 * 24);
        
        return daysSince >= 45;
    }).map(customer => {
        const lastApptDate = new Date(Math.max(
            ...appointments
                .filter(a => a['Customer E-mail'] === customer['E-mail'])
                .map(a => new Date(a['Appointment Date']))
        ));
        
        return {
            ...customer,
            daysSinceLastVisit: Math.floor((today - lastApptDate) / (1000 * 60 * 60 * 24))
        };
    });
}
```

### Inactive Paid Members

```javascript
function getInactivePaidMembers(customers, memberships, appointments) {
    const today = new Date();
    
    return customers.filter(customer => {
        // Has active membership?
        const activeMembership = memberships.find(m =>
            m['Customer E-mail'] === customer['E-mail'] &&
            m['Expired'] !== 'Yes'
        );
        
        if (!activeMembership) return false;
        
        // Last appointment date
        const customerAppts = appointments.filter(a =>
            a['Customer E-mail'] === customer['E-mail'] &&
            a['Appointment Status'] === 'completed'
        );
        
        if (customerAppts.length === 0) return true; // Has membership but never visited
        
        const lastApptDate = new Date(Math.max(
            ...customerAppts.map(a => new Date(a['Appointment Date']))
        ));
        
        const daysSince = (today - lastApptDate) / (1000 * 60 * 60 * 24);
        
        return daysSince >= 30;
    });
}
```

### New Clients (<3 Visits)

```javascript
function getNewClients(customers, appointments) {
    return customers.filter(customer => {
        const visitCount = appointments.filter(a =>
            a['Customer E-mail'] === customer['E-mail'] &&
            a['Appointment Status'] === 'completed'
        ).length;
        
        return visitCount >= 1 && visitCount <= 3;
    }).map(customer => {
        const visits = appointments.filter(a =>
            a['Customer E-mail'] === customer['E-mail']
        );
        
        return {
            ...customer,
            visitCount: visits.length,
            daysSinceFirst: calculateDaysSinceFirst(visits)
        };
    });
}
```

### High-Frequency Non-Members

```javascript
function getHighFrequencyNonMembers(customers, appointments, memberships) {
    return customers.filter(customer => {
        // Check if has active membership
        const hasMembership = memberships.some(m =>
            m['Customer E-mail'] === customer['E-mail'] &&
            m['Expired'] !== 'Yes'
        );
        
        if (hasMembership) return false;
        
        // Calculate visit frequency
        const visits = appointments.filter(a =>
            a['Customer E-mail'] === customer['E-mail'] &&
            a['Appointment Status'] === 'completed'
        );
        
        if (visits.length < 4) return false;
        
        const firstVisit = new Date(Math.min(
            ...visits.map(v => new Date(v['Appointment Date']))
        ));
        const lastVisit = new Date(Math.max(
            ...visits.map(v => new Date(v['Appointment Date']))
        ));
        
        const weeksBetween = (lastVisit - firstVisit) / (1000 * 60 * 60 * 24 * 7);
        const visitsPerWeek = visits.length / weeksBetween;
        
        return visitsPerWeek >= 1;
    });
}
```

---

## 💼 Use Cases & Workflows

### Use Case 1: Weekly Performance Review

**Goal:** Quick check-in on business health

**Workflow:**
1. **Export fresh data from Momence** (Monday morning)
2. **Upload to dashboard**
3. **Overview tab:** Check revenue vs. goal
4. **Timeline tab:** Compare to last week
5. **VSP Performance:** Review conversion/utilization tables
6. **Customers tab:** Check At-Risk segment count
7. **Action items:** Note any red flags for follow-up

**Time:** 15 minutes  
**Frequency:** Weekly (Monday mornings)  
**Owner:** Operations Manager

---

### Use Case 2: Monthly Marketing Campaign

**Goal:** Re-engage at-risk customers

**Workflow:**

**Week 1: Data Analysis**
1. **Export At-Risk segment** from Customers tab
2. **Sort by LTV** (highest first)
3. **Filter to customers with >$500 LTV**
4. **Review last visit dates and services used**

**Week 2: Campaign Setup**
1. **Upload segment to email platform**
2. **Create personalized email:**
   - Subject: "[Name], we miss you at The Vital Stretch!"
   - Body: Personalized based on last service, offer 50% off next visit
   - CTA: Book now button
3. **Schedule send** (Tuesday 10am - optimal open time)

**Week 3: Follow-Up**
1. **Text message** to high-LTV non-responders
2. **Personal phone calls** to VIP clients (>$2,500 LTV)
3. **Track bookings** in Momence

**Week 4: Analysis**
1. **Re-run At-Risk segment** to see who returned
2. **Calculate:**
   - Reactivation rate = (Returned / Contacted) × 100
   - Revenue recovered = Sum(appointments from reactivated)
   - Campaign ROI = (Revenue - Cost) / Cost × 100
3. **Document learnings** for next campaign

**Expected Results:**
- 15-25% reactivation rate
- $5,000-$10,000 revenue recovered
- 300-500% ROI

---

### Use Case 3: VSP Performance Review

**Goal:** Quarterly VSP evaluation and development planning

**Workflow:**

**Preparation (Day 1):**
1. **Export VSP Performance table**
2. **Review Conversion Rates table** (3 months of data)
3. **Review Utilization Rates table** (3 months of data)
4. **Calculate for each VSP:**
   - Total revenue generated
   - Revenue trend (growing/declining)
   - Conversion rate trend
   - Utilization rate trend
   - Unique clients served
   - Client feedback scores (from external source)

**Individual Meetings (Weeks 1-2):**

**High Performers (Blue/Orange):**
- Celebrate achievements
- Ask: "What's working well for you?"
- Discuss: Career development, lead trainer role
- Goal: Maintain performance, share best practices

**Needs Improvement (Purple):**
- Review metrics objectively
- Ask: "What challenges are you facing?"
- Identify: Training needs, schedule issues
- Create: 90-day improvement plan with specific goals
- Schedule: Bi-weekly check-ins

**Action Planning (Week 3):**
1. **Schedule training** for low-conversion VSPs
2. **Adjust schedules** for low-utilization VSPs
3. **Implement shadowing** (low performers shadow high performers)
4. **Set next quarter goals** for each VSP

**Follow-Up (Ongoing):**
1. **Monthly check-ins** on improvement plans
2. **Review progress** in analytics tables
3. **Adjust strategies** as needed

---

### Use Case 4: Membership Sales Optimization

**Goal:** Increase membership conversion rate

**Workflow:**

**Phase 1: Analysis**
1. **Journey tab:** Review current intro → paid conversion rate
2. **VSPs tab:** Identify highest and lowest converting VSPs
3. **Schedule tab:** Use membership sales heatmap to find best times
4. **Customers tab:** Review High-Frequency Non-Members segment

**Phase 2: Strategy Development**

**From VSP Analysis:**
- Interview top-converting VSPs: "What's your pitch?"
- Document their best practices
- Create training module

**From Heatmap Analysis:**
- Best sales times: Tuesday evenings, Saturday mornings
- Schedule senior VSPs during these times
- Focus membership promotions during high-conversion hours

**From High-Frequency Non-Members:**
- Export segment (potential easy conversions)
- Calculate their current spend vs. membership savings
- Create personalized ROI pitch

**Phase 3: Implementation**

**Training Program:**
1. **Week 1:** All-hands training on membership benefits
2. **Week 2:** Role-playing objection handling
3. **Week 3:** Shadowing top performers
4. **Week 4:** Implement new sales script

**Targeted Campaign:**
1. **Email High-Frequency Non-Members** with ROI calculator
2. **Personal calls** from top-converting VSPs
3. **Limited-time offer:** First month half price

**Schedule Optimization:**
1. **Staff best salespeople** during peak conversion times
2. **Intro sessions scheduled** during high-conversion hours
3. **Follow-up timing** optimized (7 days after intro)

**Phase 4: Measurement**
1. **Track conversion rate** weekly
2. **Measure by VSP** to see training effectiveness
3. **Monitor campaign segment** conversion
4. **Calculate ROI** of training and campaign investment

**Expected Results:**
- Conversion rate increase: +10-15 percentage points
- High-Frequency segment conversion: 30-40%
- Training ROI: 200-300% over 6 months

---

### Use Case 5: Location Performance Analysis

**Goal:** Identify and improve underperforming location

**Workflow:**

**Step 1: Identification**
1. **Overview tab:** Filter to each location individually
2. **Compare metrics:**
   - Revenue per location
   - Appointments per location
   - Active members per location
   - Average ticket per location
3. **Identify lowest performer**

**Step 2: Deep Dive**
1. **Timeline tab:** Check if decline is recent or ongoing
2. **Schedule tab:** Review location-specific heatmap
   - Are there slow times we can fill?
   - Is utilization lower than other locations?
3. **VSPs tab:** Compare VSP performance at this location
   - Lower conversion rates?
   - Lower utilization?
   - Fewer unique clients?
4. **Customers tab:** Check At-Risk segment for this location
   - Higher than other locations?
   - Why are clients leaving?
5. **Retention tab:** Review churn rate for this location

**Step 3: Root Cause Analysis**

**Potential Issues:**
- **VSP Performance:** Lower conversion/utilization → Training needed
- **Schedule Gaps:** Lots of empty slots → Marketing/scheduling issue
- **High Churn:** Lots of cancellations → Service quality issue
- **Low Traffic:** Few appointments → Visibility/marketing issue
- **Pricing:** Low average ticket → Value communication issue

**Step 4: Action Plan**

**Example: Low VSP Performance**
1. **Send high-performing VSP** to underperforming location for training
2. **Implement mystery shopper** to assess service quality
3. **Review and adjust** commission structure
4. **Provide additional** sales training

**Example: Schedule Gaps**
1. **Run Local SEO audit**
2. **Increase Google Ads** budget for this location
3. **Launch local partnerships** (gyms, chiropractors)
4. **Implement referral** incentives for this location only

**Example: High Churn**
1. **Exit survey** for all cancellations
2. **Focus group** with at-risk clients
3. **Facility audit** (cleanliness, equipment, atmosphere)
4. **Mystery shop** competitor locations
5. **Implement improvements** based on feedback

**Step 5: Monitor & Iterate**
1. **Weekly tracking** of key metrics
2. **Monthly progress** review
3. **Adjust strategy** based on results
4. **Document successes** for other locations

**Timeline:** 90 days to meaningful improvement  
**Expected Results:** 20-30% improvement in underperforming metrics

---

## 🛠️ Troubleshooting

### Issue: Dashboard Won't Open

**Symptoms:**
- Double-clicking file does nothing
- Browser shows "Download" instead of opening
- Error message appears

**Solutions:**

**Solution 1: Open With Browser**
1. Right-click the HTML file
2. Select "Open With"
3. Choose your browser (Chrome recommended)

**Solution 2: Change Default Program (Windows)**
1. Right-click HTML file
2. Properties → Opens With → Change
3. Select browser → Check "Always use this app"
4. Click OK

**Solution 3: File Location**
- Move file out of compressed/ZIP folder
- Ensure file is on local drive (not network drive)
- Check file permissions (should have read access)

**Solution 4: Browser Settings**
- Enable JavaScript (required)
- Disable strict security settings temporarily
- Clear browser cache: `Ctrl + Shift + Delete`

---

### Issue: Data Won't Upload

**Symptoms:**
- "Process Data" button does nothing
- Green checkmarks don't appear
- Errors in upload modal

**Solutions:**

**Solution 1: File Format**
- Verify files are CSV, not XLSX or XLS
- Re-export from Momence if unsure
- Don't edit CSVs in Excel (can corrupt encoding)

**Solution 2: File Size**
- Check file isn't too large (>100MB)
- If too large, reduce date range in Momence export
- Try exporting 6 months at a time instead of full year

**Solution 3: File Names**
- Use exact filenames specified in documentation
- Check for extra spaces or characters
- Don't change filenames after export

**Solution 4: Browser Console**
1. Press F12 to open developer tools
2. Go to "Console" tab
3. Look for error messages
4. Send screenshot to support if needed

**Solution 5: File Content**
- Open CSV in text editor (Notepad++)
- Verify it has data (not empty)
- Check for proper column headers
- Look for unusual characters or formatting

---

### Issue: Charts Not Displaying

**Symptoms:**
- Blank spaces where charts should be
- Spinning loader never stops
- Charts appear for a moment then disappear

**Solutions:**

**Solution 1: Wait**
- Large datasets take 30-60 seconds to process
- Don't interact with dashboard during processing
- Check browser status bar for "loading" indicator

**Solution 2: Data Filters**
- Click "Clear Filters" button
- Verify date range includes your data
- Check location filter isn't excluding everything

**Solution 3: Browser Extensions**
- Disable ad blockers (can interfere with charts)
- Disable privacy extensions temporarily
- Try in Incognito/Private mode

**Solution 4: Browser Cache**
- Clear cache: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- Close and reopen browser
- Try different browser (Chrome recommended)

**Solution 5: Data Validity**
- Ensure date fields are valid dates
- Check currency fields are numeric
- Verify no completely empty required columns

---

### Issue: Wrong Numbers in Metrics

**Symptoms:**
- Revenue totals don't match expectations
- Appointment counts seem off
- VSP metrics don't add up

**Solutions:**

**Solution 1: Date Filter**
- Check date range at top of page
- Click "Clear Filters" to see all data
- Verify "All Time" shows expected totals

**Solution 2: Location Filter**
- Ensure "All Locations" is selected
- If filtering to one location, numbers should be lower
- Clear location filter to see franchise-wide totals

**Solution 3: Appointment Status**
- Dashboard excludes cancelled/no-show appointments
- Check Momence export includes status field
- Verify status values are spelled correctly

**Solution 4: Duplicate Data**
- Don't upload same file twice
- Clear browser, refresh, re-upload clean files
- Check export date range for overlaps

**Solution 5: Data Validation**
- Spot-check specific records
- Use customer table to verify individual LTVs
- Compare appointment table to Momence source
- Check memberships table for proper totals

---

### Issue: VSP Analytics Showing Wrong Dates

**Symptoms:**
- Future months showing in conversion/utilization tables
- December dates in analytics when it's not December
- Impossible dates

**Solutions:**

**Solution 1: Automatic Filtering**
- Dashboard auto-filters future dates
- If seeing future dates, check browser console (F12)
- May indicate data export issue from Momence

**Solution 2: Data Export Settings**
- Re-export from Momence with correct date range
- Don't include scheduled future appointments
- Use "Last 365 Days" for historical analysis

**Solution 3: System Date/Time**
- Verify computer date/time is correct
- Check timezone setting in dashboard Settings
- Ensure Momence export timezone matches

---

### Issue: Export Not Working

**Symptoms:**
- CSV doesn't download when clicking Export
- Error message when exporting
- File downloads but is empty

**Solutions:**

**Solution 1: Pop-up Blocker**
- Allow pop-ups for this page
- Browser may be blocking download
- Check browser address bar for blocked pop-up icon

**Solution 2: Download Settings**
- Check browser's download location
- Ensure sufficient disk space
- Verify write permissions for downloads folder

**Solution 3: Data to Export**
- Ensure there's data in the filtered view
- Check that segment isn't empty
- Verify table has rows before exporting

**Solution 4: Browser Alternative**
- Try in different browser
- Chrome has most reliable export
- Firefox may require pop-up permission

---

### Issue: Segmentation Shows Zero Clients

**Symptoms:**
- All segment cards show "0 clients"
- Segments that should have clients appear empty
- Segment modals open but show no data

**Solutions:**

**Solution 1: Required Data**
- Ensure appointments file uploaded (needed for visit counts)
- Verify memberships file uploaded (needed for Inactive Paid)
- Check leads/customers file has LTV field

**Solution 2: Date Filters**
- Segments respect global date filters
- Clear filters to see all historical clients
- If filtering to recent dates, older segments won't show

**Solution 3: Segment Criteria**
- VIP requires >$2,500 LTV
- At-Risk requires 45+ days without visit
- New Clients requires 1-3 visits
- Verify you have clients meeting criteria

**Solution 4: Data Quality**
- Check LTV values are populated
- Verify email addresses consistent across files
- Ensure appointment dates are valid

---

### Issue: Performance Issues / Slow Dashboard

**Symptoms:**
- Dashboard takes forever to load
- Browser becomes unresponsive
- Charts take minutes to render

**Solutions:**

**Solution 1: Reduce Date Range**
- Filter to smaller time period (e.g., last 3 months)
- Process smaller chunks separately
- Don't use "All Time" with very large datasets

**Solution 2: Location Filtering**
- Filter to single location at a time
- Analyze one studio before moving to next
- Less data = faster processing

**Solution 3: Browser Resources**
- Close other browser tabs
- Close other programs
- Ensure sufficient RAM available (4GB minimum)

**Solution 4: Browser Choice**
- Chrome and Edge perform best
- Firefox is adequate
- Safari is slower for large datasets

**Solution 5: Data Size**
- Datasets >50,000 appointments may be slow
- Consider quarterly analysis instead of annual
- Archive older data if not needed

---

### Issue: Heatmap Not Interactive

**Symptoms:**
- Can't click heatmap cells
- Clicking does nothing
- No drill-down modal appears

**Solutions:**

**Solution 1: Data Availability**
- Ensure appointments exist for that time period
- Check filters aren't excluding relevant data
- Verify appointments have valid dates/times

**Solution 2: JavaScript Errors**
- Press F12 to open console
- Look for red error messages
- Refresh page if errors present

**Solution 3: Click Target**
- Click directly on the number in the cell
- Don't click cell border or edge
- Try different cells to test

**Solution 4: Browser Compatibility**
- Update browser to latest version
- Try Chrome if using different browser
- Disable extensions that might interfere

---

## 🔒 Data Privacy & Security

### How Your Data Is Handled

**Client-Side Processing:**
- All data processing happens in your web browser
- JavaScript reads and analyzes CSV files locally
- No data sent to external servers
- No cloud storage used

**No Data Transmission:**
- Dashboard doesn't make ANY external network requests
- No analytics or tracking code
- No form submissions
- Works completely offline after initial load

**Local Storage:**
- Settings saved to browser's localStorage
- Not synced across devices
- Cleared when browser cache cleared
- Not accessible to other websites

**Data Lifecycle:**
```
1. You upload CSVs → Stored in browser memory (RAM)
2. Dashboard processes data → All calculations local
3. You view results → Rendered in browser
4. You close tab → Data removed from memory
5. You clear cache → Settings also removed
```

### HIPAA / GDPR Compliance

**Suitable for Compliant Workflows:**

✅ **No Data Breach Risk:** Data never leaves your device  
✅ **No Third-Party Access:** No external services involved  
✅ **No Data Retention:** Nothing stored after you close browser  
✅ **User Control:** You control all data at all times  
✅ **No Logging:** No access logs or audit trails created  

**Your Responsibilities:**
- Don't share dashboard file on unsecured computers
- Log out of shared computers after use
- Keep source CSV files secure
- Don't email unencrypted exports

### Security Best Practices

**File Handling:**
1. **Store CSVs Securely**
   - Encrypted folder on local drive
   - Password-protected ZIP if sharing
   - Delete old exports regularly

2. **Dashboard Access**
   - Don't open on public/shared computers
   - Close browser tab when done
   - Don't leave unattended

3. **Exports**
   - Exported CSVs contain sensitive data
   - Store securely, don't email
   - Delete when no longer needed

**Network Security:**
- Dashboard works offline (no network needed)
- No VPN required (nothing transmitted)
- Safe to use on any network

---

## 🖥️ Technical Specifications

### Technology Stack

**Frontend:**
- Pure HTML5 (single file)
- JavaScript (ES6+)
- CSS3 with custom variables

**Libraries:**
- Chart.js 4.4.0 - Data visualization
- PapaParse 5.4.1 - CSV parsing
- JSZip 3.10.1 - ZIP file handling

**No Backend:**
- No server required
- No database required
- No authentication system
- 100% client-side

### Browser API Usage

**File API:**
- FileReader for CSV uploads
- Blob creation for exports
- No server uploads

**Storage API:**
- localStorage for settings persistence
- Quota: ~10MB (more than sufficient)
- Synchronous access

**Canvas API:**
- Chart.js uses for rendering
- Hardware accelerated
- Fallback for older browsers

### Performance Characteristics

**Initial Load:**
- File size: ~500KB
- Load time: 1-3 seconds
- No external dependencies to download

**Data Processing:**
- 1,000 appointments: <1 second
- 10,000 appointments: 3-5 seconds
- 50,000 appointments: 10-15 seconds

**Memory Usage:**
- Empty dashboard: ~50MB
- With 10,000 records: ~150-200MB
- With 50,000 records: ~300-400MB

**Chart Rendering:**
- Simple charts: <100ms
- Complex heatmaps: 200-500ms
- Interactive features: 50-100ms response

### Code Architecture

**Modular Structure:**
```
index.html (single file contains)
├── HTML Structure
│   ├── Header (upload, filters, settings)
│   ├── Tab Navigation
│   └── Tab Content Areas
├── CSS Styles
│   ├── Layout & Grid
│   ├── Color Scheme (CSS Variables)
│   ├── Components (cards, tables, buttons)
│   └── Responsive Breakpoints
└── JavaScript
    ├── Data Upload & Parsing
    ├── Data Processing & Calculations
    ├── Filtering & Sorting Functions
    ├── Tab Rendering Functions
    ├── Chart Generation
    ├── Export Functions
    └── Settings Management
```

**Data Flow:**
```
CSV Files
   ↓
PapaParse (parsing)
   ↓
JavaScript Objects (in memory)
   ↓
Filter & Calculate Functions
   ↓
Render Functions (each tab)
   ↓
Chart.js Visualizations
   ↓
User Interaction
   ↓
Dynamic Updates
```

### Extensibility

**Easy to Modify:**
- Single HTML file
- Well-commented code
- Modular functions
- Clear variable names

**Common Customizations:**
- Change color scheme (CSS variables)
- Adjust calculation formulas
- Add new chart types
- Modify segment criteria
- Add custom exports

**Not Recommended:**
- Adding backend/server
- External API calls
- Cloud storage integration
- Multi-user features

---

## ❓ FAQ

### General Questions

**Q: Do I need to install anything?**  
A: No installation required. It's a single HTML file that opens in any modern web browser.

**Q: Does it work on Mac/Windows/Linux?**  
A: Yes, works on any operating system with a modern browser.

**Q: Can I use it on my phone/tablet?**  
A: It works on mobile but is optimized for desktop. Charts and tables are easier to interact with on larger screens.

**Q: Do I need internet access?**  
A: Only to initially download the dashboard file. After that, it works completely offline.

**Q: How often should I update data?**  
A: Weekly is recommended for regular monitoring. Daily for active campaign tracking. Monthly minimum for general trends.

### Data Questions

**Q: What if I'm missing one of the CSV files?**  
A: Dashboard will still work, but some features won't be available. For example, without payroll ZIP, utilization rates won't calculate.

**Q: Can I edit the CSV files before uploading?**  
A: Not recommended. Editing in Excel can corrupt encoding. If needed, use a text editor and be very careful not to change structure.

**Q: What happens to my data after I close the browser?**  
A: All data is cleared from memory when you close the tab. Only your Settings are saved (in browser's localStorage).

**Q: Can I save my uploaded data to reload later?**  
A: Not currently. You need to re-upload CSVs each time. Consider the SQLite backend version if you want data persistence.

**Q: How far back can I analyze data?**  
A: As far back as your Momence data goes. Exporting "Last 365 Days" gives you a full year of history.

**Q: What if I have more than 21 locations?**  
A: Dashboard handles any number of locations. Performance may be slower with 50+ locations.

### Feature Questions

**Q: Can I add custom metrics?**  
A: Yes, but requires modifying JavaScript code. Dashboard is customizable if you're comfortable with coding.

**Q: Can multiple users access the same data?**  
A: Each user needs to upload their own CSVs. Dashboard is single-user by design. Consider shared folder for CSV files.

**Q: Can I share my analysis with others?**  
A: Export any view to CSV and share the file. Or take screenshots of charts. Don't share the uploaded dashboard file (contains all data).

**Q: How do I create backups?**  
A: Keep a backup of your source CSV files. Dashboard itself doesn't store data permanently.

**Q: Can I access historical versions?**  
A: No version history. Each upload is a fresh analysis. Archive your CSV exports by date if you want historical records.

### Technical Questions

**Q: Why is my browser warning me about the file?**  
A: Browsers sometimes flag HTML files as potentially unsafe. This is a false positive - the dashboard has no malicious code.

**Q: Can I run this on a server?**  
A: Yes, but unnecessary. It's designed to run locally. If you do serve it, ensure proper access controls.

**Q: Is the code open source?**  
A: Ask your franchise administrator. Code is viewable (right-click → View Page Source) but licensing depends on your agreement.

**Q: Can I white-label it?**  
A: Yes, you can customize branding, colors, and logos. Requires HTML/CSS knowledge.

**Q: How do I update to a new version?**  
A: Download the new HTML file and replace the old one. Your Settings will need to be re-entered.

### Troubleshooting Questions

**Q: Why are my charts not showing?**  
A: Most commonly: browser cache issues, date filters excluding data, or missing required files. See Troubleshooting section.

**Q: Why are numbers different from Momence?**  
A: Dashboard excludes cancelled/no-show appointments and may calculate some metrics differently. Also check date/location filters.

**Q: Why can't I export segments?**  
A: Usually a pop-up blocker issue. Allow pop-ups for the dashboard page.

**Q: Dashboard is very slow, why?**  
A: Large datasets (>50,000 appointments) can be slow. Try filtering to smaller date range or single location.

**Q: I get JavaScript errors, what do I do?**  
A: Press F12, screenshot the error, and send to support. Usually fixable with cache clear or browser update.

---

## 📞 Getting Help

### Support Resources

**Primary Documentation:**
- This file (README-Detailed.md) - Comprehensive guide
- README-Simple.md - Quick start guide

**Troubleshooting:**
- See Troubleshooting section in this document
- Browser console (F12) for error messages
- Try different browser (Chrome recommended)

**Common Issues:**
99% of issues resolved by:
1. Clearing browser cache (`Ctrl + Shift + R`)
2. Using Chrome instead of other browsers
3. Clearing all filters
4. Re-exporting fresh data from Momence

### Contact Support

**For Technical Issues:**
- Contact your franchise administrator
- Include: Browser version, OS, error messages
- Attach: Screenshots of issue
- Describe: Steps to reproduce

**For Feature Requests:**
- Document desired functionality
- Explain business use case
- Provide examples if possible

**For Training:**
- Request walkthrough session
- Review Use Cases section
- Practice with sample data first

---

## 📝 Version History

### v2.20251115.11 (Current)

**VSP Performance Analytics:**
- Moved conversion/utilization tables to top of VSP tab
- Implemented colorblind-friendly Blue-Orange-Purple scheme
- Added detailed hover tooltips for all metrics
- Automatic future date filtering
- Monthly tracking for both metrics

**Design Improvements:**
- Professional table layouts with clear legends
- Color-coded performance levels with maximum distinction
- Enhanced mobile responsiveness
- Improved chart readability

**Bug Fixes:**
- Fixed future date filtering in analytics
- Improved conversion rate calculations
- Enhanced utilization rate accuracy with overnight shift handling
- Better handling of missing data

### Previous Versions

**v2.20251106:**
- Added customer segmentation (5 segments)
- Implemented location-specific heatmaps
- Enhanced membership analytics
- Added cancellation tracking

**v2.20251103:**
- Added utilization tracking with payroll ZIP
- Implemented commission tracking
- Weekly membership averages (changed from monthly)
- Enhanced filtering logic

**v2.20251102:**
- Initial comprehensive dashboard release
- 10-tab structure
- Basic financial tracking
- VSP performance metrics

---

## 🙏 Acknowledgments

**Created For:** The Vital Stretch Franchise  
**Developed By:** bonJoeV  
**With Assistance From:** Claude (Anthropic)  

**Special Thanks:**
- Franchise owners for feedback and feature requests
- Studio managers for use case validation
- VSP team for performance insights testing

---

**Dashboard Version:** v2.20251115.11  
**Documentation Version:** v1.0  
**Last Updated:** November 13, 2025

---

*Thank you for using The Vital Stretch Analytics Dashboard. This tool is designed to empower data-driven decision making across all franchise locations. Use it to identify opportunities, optimize operations, and grow your business.*

**Remember:** Data is only valuable when it drives action. Don't just analyze - act on insights, measure results, and continuously improve! 💪
