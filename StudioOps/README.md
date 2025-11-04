# The Vital Stretch Analytics Dashboard - Complete Documentation

## Version Information
**Current Version:** v2.20251104.07  
**Last Updated:** November 4, 2025  
**Created by:** bonJoeV with ❤️  
**Dashboard Type:** Single-page HTML application (no server required)

---

## Table of Contents
1. [Overview](#overview)
2. [Recent Updates](#recent-updates)
3. [Prerequisites & Momence Setup](#prerequisites--momence-setup)
4. [Data Export Instructions](#data-export-instructions)
5. [Installation & Setup](#installation--setup)
6. [Dashboard Structure & Features](#dashboard-structure--features)
7. [All Dashboard Tabs Explained](#all-dashboard-tabs-explained)
8. [Filtering & Comparison Tools](#filtering--comparison-tools)
9. [Settings & Configuration](#settings--configuration)
10. [Advanced Client Segmentation](#advanced-client-segmentation)
11. [Calculation Methodologies](#calculation-methodologies)
12. [Data Requirements & CSV Structures](#data-requirements--csv-structures)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Best Practices](#best-practices)
15. [Privacy & Compliance](#privacy--compliance)
16. [Version History](#version-history)
17. [Technical Specifications](#technical-specifications)

---

## Overview

The Vital Stretch Analytics Dashboard is a comprehensive, interactive business intelligence tool designed specifically for The Vital Stretch franchise operations. This single-page HTML application runs entirely in your browser with no server or internet connection required after initial download.

### Key Features
- 📊 **8 Interactive Analytical Tabs** - Overview, Timeline, VSP Performance, Customers, Retention, Journey, Memberships, Cancellations
- 💰 **Complete Financial Tracking** - Revenue, labor costs, profitability, MRR, churn analysis
- 👥 **Advanced Client Segmentation** - 5 strategic segments with downloadable contact lists
- 📈 **Goal Tracking** - Monthly revenue, paid appointments, and intro appointments monitoring
- 🔄 **Dynamic Filtering** - Date ranges, locations, practitioners, with period comparisons
- 💼 **Franchise Configuration** - Customizable goals, fees, timezone, and hourly rates
- 📥 **CSV Exports** - Download any segment, report, or filtered data
- 🎨 **Brand Consistent** - The Vital Stretch colors (Primary: #013160, Accent: #71BED2, Highlight: #FBB514)

### What Makes This Dashboard Unique
- **Zero Server Requirements** - All processing happens in your browser
- **Complete Privacy** - Your data never leaves your computer
- **No Login Required** - Open the HTML file and start analyzing
- **Works Offline** - No internet needed after initial file download
- **Automatic ZIP Processing** - Upload payroll ZIP files directly without extraction
- **Real-Time Calculations** - All metrics update instantly as you filter
- **Persistent Settings** - Your preferences save to browser local storage

---

## Recent Updates

### v2.20251104.07 (Current Version) - Critical Fixes
**Release Date:** November 4, 2025

#### 🔴 Major Fixes:

**1. Fixed Lost Value for Cancellations (Monthly Recurring Revenue)**
- **Problem:** Cancellation values were incorrect or showing $0
- **Root Cause:** Matching by Membership ID which doesn't exist in cancellations CSV
- **Solution:** Now matches by Customer Email across all cancellation reports
- **How it works:**
  - Finds all memberships for each cancelled customer by email
  - Uses the most recent membership purchase
  - Takes "Paid Amount" as monthly value (e.g., $107.50/month for "1 Hour/Month")
  - Accurately calculates monthly recurring revenue lost
- **Impact:** Total Lost Revenue now shows accurate MRR impact across all reports
- **Updated in:** Main cancellations calculation + all 4 modal functions

**2. Fixed Monthly Appointments vs Goal (Paid Appointments Only)**
- **Problem:** Chart counted ALL appointments including intro offers
- **Root Cause:** Logic incremented appointments counter for every appointment
- **Solution:** Now counts paid and intro appointments separately
- **Result:**
  - Paid appointments: 300/month goal (non-intro only)
  - Intro appointments: 50/month goal (tracked separately)
  - No double counting
- **Chart renamed:** "Monthly Paid Appointments vs Goal"
- **Impact:** Accurate tracking of paid vs intro performance

### v2.20251104.06 - Default Goals & Data Fixes
**Release Date:** November 4, 2025

**Updates:**
- **Changed default monthly revenue goal:** $50,000 → $20,000 (more realistic for typical franchisees)
- **Changed default intro appointments goal:** 36 → 50
- **Fixed Churn Rate by Location:** Created customer location mapping from cancellations data
- **Made "Compare To" font smaller:** 1pt reduction for better visual hierarchy
- **Enhanced customer name extraction:** Better handling of various CSV field formats

### v2.20251103.05 - Franchise Configuration
**Release Date:** November 3, 2025

**Major Features:**
- Added ⚙️ Franchise Configuration section with persistent settings
- User-configurable base hourly rate for non-appointment work (default: $13.00)
- Comprehensive labor cost tracking (appointment + non-appointment hours)
- New Financial Performance section in Overview tab
- Improved trendline visibility (70% opacity, 3px width) for colorblind accessibility
- Enhanced heatmap interactivity (click days for hourly breakdown, hours for appointments)
- Monthly goal column charts replacing progress bars
- Updated all profitability metrics to use comprehensive labor costs

### v2.20251103.04 - Utilization & Commissions
**Major Features:**
- Added utilization tracking throughout dashboard (average, daily trend, per VSP)
- Added commission tracking (membership & product sales, excludes services)
- Membership charts now show weekly averages with clear notation
- Improved tab order for studio owners/managers
- Enhanced payroll ZIP file processing for time tracking and commissions
- Automatic special character cleaning in product names (®, ™, ©, Â)

---

## Prerequisites & Momence Setup

### Momence Configuration Requirements
Before exporting data, ensure your Momence account is properly configured:

#### 1. Pay Rates Configuration
**Location:** Studio Set-up → Pay Rates
- Create pay rate structures for each VSP level (Level 1, Level 2, Lead, etc.)
- Set hourly rates or per-session rates
- Assign rates to different service types (Table Time, Studio Lead, Admin, etc.)
- Configure special rates for events and intro sessions

#### 2. Practitioner Setup
**Location:** Studio Set-up → Practitioners
- Add all VSPs (Vital Stretch Practitioners)
- Assign each practitioner to appropriate role/level
- Ensure contact information is complete
- Verify active status for current team members
- Set default pay rates for each practitioner

#### 3. Appointment Pay Rates
**Location:** Appointments → Boards
- Set pay rate for each VSP on the appointment board
- Verify rates are correctly applied to different service types
- Check special rates for introductory sessions and events
- Ensure override rates are documented

#### 4. Time Clock Setup (Optional but Recommended)
**Location:** Studio Set-up → Time Clock
- Enable time clock for VSPs
- Set up clocking rules and notifications
- Train VSPs on proper clock in/out procedures
- Used for calculating utilization metrics

---

## Data Export Instructions

### Overview of Required Files
You need **3-4 files** from Momence:

1. ✅ **Required:** Membership Sales CSV
2. ✅ **Required:** Membership Cancellations CSV  
3. ✅ **Required:** New Leads & Customers CSV
4. ⭐ **Strongly Recommended:** Payroll Report ZIP (for appointments, utilization, commissions)

### Detailed Export Instructions

#### Report 1: Membership Sales
**Momence Report Name:** `Membership sales - A report on membership purchases history`

**What it includes:**
- Purchase ID, Membership ID
- Customer name and email
- Membership type and name
- Bought date/time (GMT)
- Paid amount (monthly subscription price)
- Remaining/Expiry/Renewal dates
- Status: Expired, Frozen, Refunded
- Sold by (VSP who sold it)

**Export Steps:**
1. Log in to Momence
2. Go to **Reports** section
3. Find "Membership sales" in Favorite Reports
4. Select date range (recommend: **All time**)
5. Click **Download Summary**
6. Save as: `momence--membership-sales-export.csv`

**Why it's needed:**
- Calculate MRR (Monthly Recurring Revenue)
- Track membership sales trends
- Match cancellations to subscription values
- Analyze which memberships are most popular

---

#### Report 2: Membership Cancellations
**Momence Report Name:** `Membership sales - A report on membership purchases history` (second download)

**What it includes:**
- Customer name and email
- Membership type
- Cancelled at (date and time)
- Cancellation reason
- Possible improvements (feedback)
- Home location

**Export Steps:**
1. In Momence, go to **Reports** → Membership sales
2. Click on the **Cancellations tab** within the report
3. Select date range (recommend: **All time**)
4. Click **Download Summary** (from cancellations tab)
5. Save as: `momence--membership-sales-export__1_.csv`

**Why it's needed:**
- Calculate churn rate
- Analyze cancellation reasons
- Calculate lost monthly recurring revenue
- Identify at-risk locations or membership types
- Sentiment analysis on feedback

---

#### Report 3: New Leads & Customers
**Momence Report Name:** `New Leads & Customers by join date`

**What it includes:**
- First name, last name, email
- Customer type (Lead or Customer)
- Join date
- Aggregator (acquisition source)
- First purchase (what they bought)
- First purchase date
- LTV (Lifetime Value)

**Export Steps:**
1. Go to **Reports** → Favorite Reports
2. Find "New Leads & Customers by join date"
3. Select date range (recommend: **All time**)
4. Click **Download Summary**
5. Save as: `momence-new-leads-and-customers.csv`

**Why it's needed:**
- Track lead conversion rates
- Calculate customer acquisition effectiveness
- Analyze customer LTV
- Build funnel visualizations
- Segment customers by value

---

#### Report 4: Practitioner Payroll ZIP (Strongly Recommended)
**Momence Report Name:** `Practitioner Payroll - Multiple practitioners payroll details`

**What it includes:**
For each VSP, multiple CSV files:
- `momence-payroll-appointments-[name].csv` - All appointments with revenue, payouts
- `momence-payroll-appointments-[name]-aggregate.csv` - Appointment summaries
- `momence-payroll-time-[name].csv` - Clock in/out records (for utilization)
- `momence-payroll-classes-[name].csv` - Classes taught
- `momence-commissions-[name].csv` - Membership & product sales commissions
- `momence-payroll-tips-[name].csv` - Tips received

**Export Steps:**
1. Go to **Reports** → Practitioner Payroll
2. Click **Select Multiple** practitioners
3. Check ALL VSPs you want to analyze
4. Select date range (recommend: **Last 90 days** or **All time**)
5. Click **Download Details** (not Summary!)
6. File downloads as: `momence-payroll-report-summary.zip`
7. **DO NOT UNZIP** - upload the ZIP file directly to dashboard

**Why it's needed:**
- **Primary appointments data source** - Most detailed appointment records
- Calculate utilization (table time vs clocked time)
- Track VSP commissions from membership/product sales
- Analyze individual VSP performance and efficiency
- Calculate accurate labor costs
- Track non-appointment hours for cost analysis

**Important Notes:**
- ZIP file may be 50-100MB depending on date range
- Contains 7 CSV files per practitioner
- Dashboard automatically parses all files
- Cleans special characters (®, ™, ©, Â) automatically
- If you don't have time clock data, utilization metrics won't appear (that's OK)

---

### Export Best Practices

**Date Ranges:**
- **Initial Setup:** Export "All time" for complete history
- **Weekly Updates:** Export last 7-30 days and re-upload
- **Monthly Analysis:** Export full month at month-end

**File Management:**
- Keep consistent file names for easy identification
- Store exports in dedicated folder (e.g., "Vital Stretch Data")
- Create monthly archives of exports
- Document export dates in file names if doing partials

**Update Frequency:**
- **Minimum:** Monthly updates for trend tracking
- **Recommended:** Weekly updates for real-time insights
- **Optimal:** After major events (large membership drives, new VSP starts)

---

## Installation & Setup

### Step 1: Download the Dashboard
1. Download `vital-stretch-dashboard-v7-UPDATED.html` to your computer
2. Save to an easily accessible location (Desktop, Documents, or dedicated folder)
3. **Important:** Keep the file name consistent for bookmarking

### Step 2: Prepare Your Data Files
Export the required files from Momence (see instructions above):
- `momence--membership-sales-export.csv` (memberships)
- `momence--membership-sales-export__1_.csv` (cancellations)
- `momence-new-leads-and-customers.csv` (leads)
- `momence-payroll-report-summary.zip` (payroll - optional but recommended)

### Step 3: Open the Dashboard
1. **Double-click** the HTML file
2. Opens in your default browser (Chrome recommended, but works in Firefox, Safari, Edge)
3. You'll see the header with The Vital Stretch logo
4. Empty state message prompts you to upload data

**No Internet Required:** Dashboard works 100% offline after opening (uses CDN libraries but caches them)

### Step 4: Upload Your Data
**Location:** Click the 📤 Upload button in the top-right corner

**Upload Modal appears with 4 file selection areas:**

1. **📊 Membership Sales**
   - Click "Choose File"
   - Select `momence--membership-sales-export.csv`
   - Wait for processing (green ✅ appears)

2. **❌ Cancellations**
   - Click "Choose File"
   - Select `momence--membership-sales-export__1_.csv`
   - Wait for processing (green ✅ appears)

3. **👥 Leads & Customers**
   - Click "Choose File"
   - Select `momence-new-leads-and-customers.csv`
   - Wait for processing (green ✅ appears)

4. **📦 Payroll ZIP** (optional)
   - Click "Choose File"
   - Select `momence-payroll-report-summary.zip`
   - **Do not unzip first!** Upload the ZIP directly
   - Processing takes 10-30 seconds (contains many files)
   - Green ✅ appears when complete

**Processing Notes:**
- Small files (< 1MB): Instant processing
- Medium files (1-10MB): 2-5 seconds
- Large files (10-50MB): 10-30 seconds
- ZIP files: Longer processing time (extracts and parses all internal files)

### Step 5: Configure Franchise Settings
**Location:** Click ⚙️ Settings icon in top-right corner

**⚙️ Franchise Configuration:**

**Timezone:**
- Select your location's timezone
- Default: America/Chicago (Central Time)
- Used for date/time calculations and reports

**Financial Settings:**
- **Franchise Fee %:** Default 7.0% (of gross revenue)
- **Brand Fund %:** Default 1.5% (of gross revenue)
- **Credit Card Fees %:** Default 2.9% (payment processing)

**Monthly Goals:**
- **Revenue Goal:** Default $20,000/month
- **Paid Appointments Goal:** Default 300/month (excludes intro)
- **Intro Appointments Goal:** Default 50/month

**Labor Costs:**
- **Base Hourly Rate:** Default $13.00/hour
- Used for non-appointment hours (cleaning, admin, training)
- Applied to: (Clocked Hours - Appointment Hours) × Base Rate

**Saving Settings:**
- Click "💾 Save Settings"
- Settings persist in browser local storage
- Survives browser refresh and closing
- Per-device (not synced across computers)

### Step 6: Explore Your Analytics
Once data is uploaded:
- Empty state disappears
- Main content and tabs become visible
- All 8 tabs are accessible
- Filters are populated with your data
- Charts begin rendering
- Click any tab to explore different analytics

---

## Dashboard Structure & Features

### Header Section
**Location:** Top of page

**Elements:**
- **Logo:** The Vital Stretch brand circle logo
- **Title:** "The Vital Stretch - Analytics Dashboard"
- **Tagline:** "Movement is Medicine"
- **Upload Button (📤):** Top-right corner - Upload/update data files
- **Settings Button (⚙️):** Configure franchise settings

### Filter Panel
**Location:** Below header, above tabs

**Date Filters:**
- **Start Date:** Select analysis period start
- **End Date:** Select analysis period end
- **Compare To:** Period-over-period comparison
  - No Comparison
  - Previous Period (equal length)
  - Last Month
  - Last Quarter
  - Same Period Last Year

**Quick Filters (One-click presets):**
- Last 7 Days
- Last 30 Days
- Last 90 Days
- This Month (month-to-date)
- Last Month (complete)
- Reset All (clear all filters)

**Attribute Filters:**
- **Location:** Filter by franchise location
- **Practitioner:** Filter by specific VSP
- Auto-populated from your data

**Refresh Button:**
- 🔄 Refresh Data
- Re-processes all uploaded files
- Use after uploading new data

### Main Navigation Tabs
**8 Primary Tabs:**

1. **Overview** - High-level KPIs and monthly goals
2. **Timeline** - Trends and patterns over time
3. **VSP** - Vital Stretch Practitioner performance
4. **Customers** - Customer analytics and behavior
5. **Retention** - Retention rates and churn analysis
6. **Journey** - Customer journey funnel visualization
7. **Memberships** - Membership sales and performance
8. **Cancellations** - Cancellation analysis (appears when cancellations data loaded)

**Tab Behavior:**
- Click to switch between tabs
- Active tab highlighted
- Content loads on-demand
- Charts render when tab becomes active
- Filters apply to all tabs

### Footer
**Location:** Bottom of page

**Elements:**
- **Version Number:** Current dashboard version
- **Credits:** "Made by bonJoeV with ❤️"
- **Separator:** Visual divider

---

## All Dashboard Tabs Explained

### Tab 1: Overview
**Purpose:** High-level business performance at a glance

#### Key Metrics Cards
Grid of essential KPIs:

**Financial Metrics:**
- **Total Revenue:** Sum of all completed appointments in period
- **Average Revenue per Appointment:** Total revenue ÷ appointment count
- **Monthly Recurring Revenue (MRR):** Active subscriptions × monthly value
- **Total Labor Cost:** Appointment payouts + non-appointment hours
- **Net Profit:** Revenue - Labor - Franchise Fees - Brand Fund - CC Fees

**Volume Metrics:**
- **Total Appointments:** All completed appointments
- **Paid Appointments:** Excludes intro/trial appointments
- **Intro Appointments:** First-time trial appointments
- **Average Utilization:** Table time ÷ clocked time (if time data available)

**Customer Metrics:**
- **Total Customers:** Unique customers with appointments
- **New Customers:** First-time customers in period
- **Returning Customers:** Customers with 2+ appointments
- **Customer Retention Rate:** (Returning ÷ Total) × 100

**Practitioner Metrics:**
- **Active VSPs:** Practitioners with appointments in period
- **Total Commissions:** Membership + product sales commissions (excludes services)

#### Financial Performance Section
Detailed breakdown of profitability:

**Revenue Breakdown:**
- Gross Revenue
- Franchise Fees (7% of revenue)
- Brand Fund (1.5% of revenue)
- Credit Card Fees (2.9% of revenue)

**Labor Cost Breakdown:**
- Appointment Payouts (from payroll data)
- Non-Appointment Hours (clocked - appointment hours)
- Non-Appointment Labor Cost (hours × base rate)
- Total Labor Cost

**Net Profit Calculation:**
- Formula: Revenue - Labor - Franchise Fees - Brand Fund - CC Fees
- Profit Margin percentage
- Explanation of all components

#### Monthly Goals Progress
Three column charts tracking goals:

**1. Monthly Revenue vs Goal**
- Chart Type: Bar + Line overlay
- Blue bars: Actual monthly revenue
- Yellow dashed line: Revenue goal ($20,000 default)
- Shows historical months
- Click bar to see details

**2. Monthly Paid Appointments vs Goal**
- Blue bars: Actual paid appointments (excludes intro)
- Yellow dashed line: Goal (300 default)
- Tracks non-intro appointments only
- Shows performance trends

**3. Monthly Intro Appointments vs Goal**
- Yellow bars: Actual intro appointments
- Blue dashed line: Goal (50 default)
- Tracks trial/intro offers separately

#### Actionable Insights
AI-generated recommendations based on performance:

**Revenue Insights:**
- Goal achievement status and suggestions
- Upselling recommendations when close to goal
- Average revenue per appointment targets

**Appointments Insights:**
- Booking pace recommendations
- Weekly appointment targets to reach goal
- Capacity utilization suggestions

**Customers Insights:**
- Retention improvement strategies
- New customer acquisition recommendations
- Customer reactivation opportunities

**Custom Recommendations:**
- Based on your actual data
- Updates as filters change
- Prioritized by impact

### Tab 2: Timeline
**Purpose:** Visualize trends and patterns over time

#### Revenue Trends Section

**Daily Revenue Chart**
- Line chart with trend line
- X-axis: Date
- Y-axis: Revenue ($)
- Shows daily revenue volatility
- Trendline indicates overall direction
- Hover for exact values

**Weekly Revenue Chart**
- Grouped by week (Week 1, Week 2, etc.)
- Smooths daily volatility
- Better for identifying patterns
- Color-coded bars

**Monthly Revenue by Location**
- Stacked bar chart
- Compare multiple locations
- See location contribution to total
- Filter to specific location for detail

#### Appointment Trends Section

**Daily Appointments Chart**
- Line chart with trend line
- Shows appointment volume over time
- Identify busy/slow periods
- Useful for staffing decisions

**Weekly Appointment Patterns**
- Bar chart by week
- Compare week-over-week performance
- Seasonal trend identification

#### Goal Tracking Charts
(Described in Overview section, but accessible here too)

#### Utilization Trend Chart
(Appears when payroll ZIP uploaded)
- Daily utilization percentage
- Line chart over time
- Shows efficiency trends
- Target: 80%+ utilization
- Formula: (Appointment Hours ÷ Clocked Hours) × 100

#### Peak Hours Heatmap
Interactive appointment timing analysis:

**Features:**
- Grid: Days of week (rows) × Hours of day (columns)
- Color intensity: Darker = more appointments
- Click day name: See hourly breakdown for that day
- Click hour cell: See individual appointments (date, customer, value)
- Clear instructions on chart

**Use Cases:**
- Identify peak booking times
- Optimize staff scheduling
- Plan marketing campaigns around slow times
- Capacity planning

### Tab 3: VSP (Vital Stretch Practitioners)
**Purpose:** Individual practitioner performance tracking

#### VSP Performance Summary Table
Sortable table with columns:

**Practitioner Name:**
- First and Last Name (never email)
- Alphabetically sorted by default

**Revenue:**
- Total revenue generated
- Sortable (click column header)

**Appointments:**
- Number of appointments completed
- Excludes cancelled/no-shows

**Avg Revenue:**
- Average revenue per appointment
- Revenue ÷ Appointments

**Unique Clients:**
- Count of distinct customers served
- Based on unique email addresses

**Utilization %:**
- (Appointment Hours ÷ Clocked Hours) × 100
- Only appears if time tracking data available
- Target: 75-85%
- Red if < 60%, Green if > 80%

**Commissions:**
- Total from membership + product sales
- Excludes service/appointment commissions
- Only appears if commission data available

**Client Retention:**
- % of clients who returned for 2+ appointments
- (Returning Clients ÷ Unique Clients) × 100

**Actions:**
- "View Details" button
- Opens modal with deep dive

#### VSP Detail Modal
Opened by clicking "View Details" for any practitioner:

**Summary Stats:**
- Practitioner name
- Total revenue and appointments
- Average revenue per appointment
- Unique clients served
- Client retention rate
- Utilization (if available)
- Total commissions (if available)

**Appointment List:**
Table showing all appointments:
- Date
- Customer name
- Service/appointment type
- Revenue
- Payment method
- Sortable by any column

**Commission Breakdown:**
(If commission data available)
- Membership commissions
- Product commissions
- Total commissions

**Performance Charts:**
- Revenue over time (line chart)
- Appointments per week (bar chart)

#### Export VSP Data
- 📥 Export to CSV button
- Downloads practitioner performance table
- Includes all columns
- File name: `vital-stretch-vsp-performance-[date].csv`

### Tab 4: Customers
**Purpose:** Customer analytics and behavior patterns

#### Customer Overview Metrics

**Customer Counts:**
- Total Customers (all time)
- New Customers (in selected period)
- Returning Customers
- Active Customers (30-day window)

**Customer Value:**
- Average Customer LTV
- Average Customer Lifetime (days)
- Average Appointments per Customer
- Average Revenue per Customer

**Customer Behavior:**
- Average Days Between Visits
- Visit Frequency Distribution
- Preferred Booking Days/Times

#### Top Customers Table
Ranked list of highest-value customers:

**Columns:**
- Customer Name
- Email
- LTV (Lifetime Total Value)
- Total Appointments
- First Visit Date
- Last Visit Date
- Average Days Between Visits
- Status (Active, At-Risk, Churned)

**Sorting:**
- Default: By LTV (highest first)
- Click any column header to sort
- Helpful for identifying VIP clients

#### Customer Acquisition Analysis

**Acquisition Channels:**
- Pie chart showing customer sources
- From "Aggregator" field in leads data
- Examples: Google, Referral, Walk-in, Social Media
- Click slice for details

**Conversion Funnel:**
- Leads → Customers conversion rate
- Time-to-first-purchase distribution
- Intro → Paid conversion rate

#### Advanced Client Segmentation
(Detailed in separate section below)

### Tab 5: Retention
**Purpose:** Understand customer retention and churn

#### Retention Overview Metrics

**Retention Rates:**
- Overall Retention Rate (%)
- 30-Day Retention
- 60-Day Retention
- 90-Day Retention

**Churn Metrics:**
- Churn Rate (%)
- Churned Customers Count
- Churn by Location
- Churn by Membership Type

**At-Risk Analysis:**
- Customers at Risk Count
- Days Since Last Visit Distribution
- Reactivation Opportunities

#### Retention by Cohort
- Group customers by join date (monthly cohorts)
- Track retention rate over time
- Visualize retention curve
- Compare cohorts

#### Churn Reason Analysis
(Requires cancellation data)
- Top cancellation reasons
- Sentiment analysis on feedback
- Improvement suggestions from customers
- Actionable insights for retention

#### Reactivation Opportunities
List of customers to win back:
- Customers inactive 45-90 days
- Previous high-value customers
- Contact information for outreach
- Last visit date and preferred services

### Tab 6: Journey
**Purpose:** Visualize customer journey from lead to loyal customer

#### Funnel Visualization
Step-by-step conversion funnel:

**Stage 1: Leads**
- Total people in system
- Leads vs Customers split

**Stage 2: First Visit**
- Customers who booked first appointment
- Conversion rate from lead
- Average time to first visit

**Stage 3: Return Visit**
- Customers who came back
- First visit → Return conversion
- Average time between visits

**Stage 4: Membership Purchase**
- Customers who bought memberships
- Return → Member conversion
- Average revenue per member

**Stage 5: Long-Term Retention**
- Customers with 5+ visits
- Member → Loyal conversion
- Average customer lifetime

**Visual Elements:**
- Funnel bars sized by volume
- Percentage labels on each stage
- Drop-off percentages between stages
- Color-coded stages

#### Journey Metrics Cards

**Lead Generation:**
- Total Leads
- Lead Source Breakdown
- Lead-to-Customer Rate
- Average Time to Convert

**First Purchase Behavior:**
- Average First Purchase Value
- Most Popular First Purchase
- Intro Offer Conversion Rate

**Repeat Visit Patterns:**
- Average Days to 2nd Visit
- 2nd Visit Conversion Rate
- Most Common 2nd Purchase

**Membership Adoption:**
- % Customers Who Buy Memberships
- Average Time to Membership
- Most Popular Membership Type

#### Journey Path Analysis
Sankey diagram showing common customer paths:
- Lead Source → First Service → Membership → Retention
- Visualize most successful acquisition paths
- Identify optimization opportunities

### Tab 7: Memberships
**Purpose:** Membership sales and performance analysis

#### Membership Overview Metrics

**Sales Metrics:**
- Total Membership Sales (count)
- Total Membership Revenue
- Average Membership Value
- Active Memberships (current)

**Growth Metrics:**
- New Memberships This Month
- Renewal Rate
- Upgrade/Downgrade Rate
- Net Membership Growth

**Performance Metrics:**
- MRR (Monthly Recurring Revenue)
- MRR Growth Rate
- Average Revenue Per Member (ARPM)
- Membership Lifetime Value

#### Membership Sales Trends

**Monthly Membership Sales Chart**
- Bar chart showing sales count by month
- Trend line overlay
- Compare year-over-year
- Identify seasonal patterns

**Weekly Membership Sales Chart**
- More granular sales tracking
- Weekly averages clearly labeled
- Useful for short-term trends
- Note: Chart subtitle explains these are weekly averages

**Average Sale Value Over Time**
- Line chart of average membership price
- Shows pricing evolution
- Identifies upselling success
- Weekly averages with notation

#### Membership Type Analysis

**Sales by Membership Type**
- Bar chart showing count per type
- Examples: 1 Hour/Month, 2 Hours/Month, 4 Hours/Month
- Most to least popular

**Revenue by Membership Type**
- Stacked bar showing revenue contribution
- Identify highest revenue generators
- May differ from highest volume

**Membership Type Performance Table:**
Columns:
- Membership Type
- Sales Count
- Total Revenue
- Average Price
- Active Count
- Churn Rate
- Avg Customer Lifetime

**Interactive:**
- Click any type to see customer list
- Export customers for targeted marketing

#### Membership Seller Analysis
(From "Sold by" field)
- VSP who sold each membership
- Sales count per VSP
- Revenue generated from memberships
- Commission-eligible sales

### Tab 8: Cancellations
**Purpose:** Deep dive into membership cancellations
**Note:** Tab only appears when cancellations data is uploaded

#### Cancellations Overview Metrics

**Volume Metrics:**
- Total Cancellations (count)
- Cancellation Rate (%)
- Cancellations This Month
- Most Recent Cancellation Date

**Financial Impact:**
- **Total Lost Revenue** (Monthly MRR Lost)
- Calculated by matching customer email to most recent membership
- Shows monthly recurring revenue impact
- Example: 10 cancellations of $107.50/month = $1,075/month lost

**Feedback Metrics:**
- % With Cancellation Reason
- % With Improvement Suggestions
- Feedback Response Rate

#### Cancellation Trends Charts

**Monthly Cancellations Chart**
- Bar chart showing cancellations by month
- **Interactive:** Click any bar to see detailed modal
- Trend line shows if cancellations increasing/decreasing
- Compare to sales trend

**Cumulative Cancellations Chart**
- Line chart showing running total
- Visualize total churn over time
- Compare to cumulative sales

**Cancellation Rate by Month**
- (Cancellations ÷ Sales) × 100 for each month
- More meaningful than raw counts
- Target: < 5% monthly
- Identify problematic months

#### Cancellation Patterns

**By Day of Week:**
- Bar chart showing which days people cancel
- Useful for staffing retention conversations
- May reveal patterns (e.g., Monday cancellations after weekend thinking)

**Daily Cancellation Activity:**
- Line chart showing cancellation timing
- Identify clusters or spikes
- Correlate with events or policy changes

#### Cancellation Reasons Analysis

**Top 10 Cancellation Reasons:**
- Ranked list with counts
- From "Reason" field in cancellations CSV
- Examples:
  - "It's too expensive for me"
  - "Issues with my subscription"
  - "Relocating/moving"
  - "Health/injury issues"
  - "Not seeing results"

**Sentiment Analysis:**
- Automatic categorization:
  - Negative (price, quality concerns)
  - Neutral (moving, schedule)
  - Positive (achieved goals)
- Sentiment distribution pie chart

**Possible Improvements:**
- Word cloud or list
- From "Possible improvements" field
- Customer suggestions for business
- Actionable feedback

**Feedback Response Rate:**
- % of cancellations with reason
- % with improvement suggestions
- Gauge customer engagement

#### Geographic Analysis

**Cancellations by Location:**
- Bar chart showing count per location
- **Interactive:** Click bar to see customers
- Identify problem locations

**Location Distribution (Pie Chart):**
- Visual representation of where cancellations occur
- Compare to sales distribution

**Churn Rate by Location:**
- (Location Cancellations ÷ Location Sales) × 100
- **Now fixed:** Uses customer email matching
- Identifies highest-churn locations
- Target locations for retention efforts

#### Membership Type Analysis

**Cancellations Count by Type:**
- Which memberships cancelled most often
- Compare to sales by type

**Churn Rate by Type:**
- (Type Cancellations ÷ Type Sales) × 100
- Identify problem memberships
- May indicate pricing or value issues
- Examples:
  - High churn on premium memberships: Too expensive?
  - High churn on basic: Not enough value?

#### Comparison Charts

**Monthly Sales vs Cancellations:**
- Dual-line chart comparing trends
- Green line: New membership sales
- Red line: Cancellations
- Identify when churn exceeds sales (danger!)

**Net Growth Chart:**
- Net Growth = Sales - Cancellations
- Positive = healthy growth
- Negative = shrinking member base
- Track month-over-month

#### Cancellation Detail Modals
**Triggered by clicking charts**

**Monthly Cancellations Modal:**
- Click any month bar
- Shows all cancellations for that month
- Table with:
  - Customer name and email
  - Membership type
  - **Monthly value** (matched by email)
  - Location
  - Cancelled date
  - Reason (shortened)
- Sorted by value (highest first)
- Total lost MRR for month

**Location Cancellations Modal:**
- Click location bar
- Shows all cancellations at that location
- Same table structure
- Helps identify location-specific issues

**Membership Type Cancellations Modal:**
- Click membership type bar
- Shows all cancellations of that type
- Helps understand type-specific problems

---

## Filtering & Comparison Tools

### Date Filtering System

#### Custom Date Range
**Controls:**
- Start Date picker
- End Date picker

**Behavior:**
- Sets analysis period for all tabs
- Updates all metrics and charts
- Persists when switching tabs
- Saved to browser session

**Use Cases:**
- Analyze specific month: Jan 1 - Jan 31
- Quarter analysis: Q1, Q2, etc.
- Custom campaign periods
- Week-over-week comparisons

#### Quick Filter Buttons
One-click presets for common periods:

**Last 7 Days:**
- Rolling 7-day window
- Always includes today
- Good for daily monitoring

**Last 30 Days:**
- Rolling 30-day window
- Monthly trends
- Compare to goals

**Last 90 Days:**
- Quarterly view
- Seasonal patterns
- Longer-term trends

**This Month:**
- Current calendar month to date
- Track progress toward monthly goals
- Mid-month performance check

**Last Month:**
- Previous complete calendar month
- Month-end analysis
- Compare to current month

**Reset All:**
- Clears all filters
- Returns to all-time view
- Resets location and practitioner filters too

### Location Filter
**Purpose:** Analyze specific franchise locations

**Options:**
- "All Locations" (default)
- Individual locations from your data
- Auto-populated from appointment records

**Use Cases:**
- Compare location performance
- Location-specific reporting
- Franchise owner multi-location analysis
- Regional trend identification

### Practitioner Filter
**Purpose:** Focus on individual VSP performance

**Options:**
- "All Practitioners" (default)
- Individual VSPs by name (First Last)
- Auto-populated from appointment records

**Use Cases:**
- Individual VSP reviews
- New hire ramp-up tracking
- Performance improvement monitoring
- Commission verification

### Comparison Mode
**Feature:** Compare current period to another period

**Location:** "📊 Compare To" dropdown in filter panel

**Options:**

**1. No Comparison (Default)**
- Shows only current period data
- No comparison bars or percentages
- Simplest view

**2. Previous Period**
- Compares to immediately preceding period of equal length
- Example: Oct 1-15 compares to Sep 16-30
- Best for: Sequential comparison
- Shows: % change, trend indicator (🔺🔻)

**3. Last Month**
- Compares current selection to previous complete calendar month
- Best for: Month-over-month tracking
- Shows comparison metrics in orange

**4. Last Quarter**
- Compares to previous complete quarter
- Best for: Quarterly business reviews
- Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec

**5. Same Period Last Year**
- Year-over-year comparison
- Example: Oct 2024 vs Oct 2023
- Best for: Annual growth tracking, seasonality

#### Comparison Visualization
When comparison mode active:

**Metric Cards:**
- Primary value (current period) - Blue
- Comparison value - Orange
- Percentage change
- Trend indicator:
  - 🔺 = Increase (green text)
  - 🔻 = Decrease (red text)

**Charts:**
- Two bars/lines per data point
- Current period: Primary color (blue)
- Comparison period: Secondary color (orange)
- Legend distinguishes periods

**Example:**
```
Revenue: $25,000 🔺 +15%
(vs Previous Period: $21,739)
```

### Filter Combination
**All filters work together:**
- Date + Location + Practitioner + Comparison
- Example: "Last 30 Days for Eden Prairie location with Emma Kasel compared to Previous Period"
- Filters apply to ALL tabs simultaneously
- Real-time updates as you change filters

### Filter Reset
- Click "Reset All" button
- Or manually clear each filter
- Returns to all-time, all locations, all practitioners view
- Comparison mode stays active until manually changed

---

## Settings & Configuration

### Accessing Settings
**Location:** Click ⚙️ icon in top-right corner

**Modal opens with two main sections:**
1. Franchise Configuration
2. Quick Settings Guide

### Franchise Configuration Settings

#### General Settings

**Timezone:**
- Dropdown with major US timezones
- Default: America/Chicago (Central Time)
- Affects:
  - Date/time display throughout dashboard
  - Report timestamps
  - Appointment scheduling display
- Options include: Pacific, Mountain, Central, Eastern, etc.

**Why it matters:** Ensures times displayed match your local operation hours

---

#### Financial Settings

**Franchise Fee Percentage:**
- Input: 0.0% to 100.0%
- Default: 7.0%
- Applied to: Gross revenue
- Used in: Net profit calculations
- Updates: All profitability metrics

**Brand Fund Percentage:**
- Input: 0.0% to 100.0%
- Default: 1.5%
- Applied to: Gross revenue
- Used in: Net profit calculations
- Purpose: Corporate marketing/brand fund contribution

**Credit Card Fees Percentage:**
- Input: 0.0% to 100.0%
- Default: 2.9%
- Applied to: Revenue from credit card transactions
- Used in: Net profit calculations
- Note: Represents payment processor fees

**Example Calculation:**
```
Gross Revenue: $25,000
Franchise Fee (7%): $1,750
Brand Fund (1.5%): $375
CC Fees (2.9%): $725
Total Fees: $2,850
```

---

#### Monthly Goals

**Monthly Revenue Goal:**
- Input: Dollar amount
- Default: $20,000
- Used in:
  - Overview tab goal progress
  - Monthly Revenue vs Goal chart
  - Actionable insights generation
- Visual indicators: Progress bars and bars change color based on achievement

**Monthly Paid Appointments Goal:**
- Input: Number of appointments
- Default: 300
- **Important:** Counts only paid appointments (excludes intro)
- Used in:
  - Overview tab goal progress
  - Monthly Paid Appointments vs Goal chart
- Chart title clarifies "Paid Appointments"

**Monthly Intro Appointments Goal:**
- Input: Number of intro appointments
- Default: 50
- Counts only intro/trial appointments
- Tracked separately from paid appointments
- Used in:
  - Overview tab
  - Monthly Intro Appointments vs Goal chart

**Goal Setting Tips:**
- Base on historical performance
- Set stretch goals (+10-15% above average)
- Review quarterly and adjust
- Different goals for high/low seasons
- Consider location capacity

---

#### Labor Cost Settings

**Base Hourly Rate:**
- Input: Dollar amount per hour
- Default: $13.00/hour
- Applied to: Non-appointment hours
- Used for: Practitioners not actively with clients

**What counts as "non-appointment hours":**
- Cleaning and studio prep
- Administrative tasks
- Training and meetings
- Marketing activities
- Time clocked in but not with clients
- Calculation: (Total Clocked Hours - Appointment Hours) × Base Rate

**Why this matters:**
- Accurate labor cost calculation
- True profitability understanding
- Budget planning
- Pricing strategy validation

**Example:**
```
VSP worked 40 hours (clocked)
30 hours were appointments (paid at appointment rate)
10 hours were non-appointment (cleaning, admin, etc.)
Non-appointment labor = 10 hours × $13.00 = $130.00
Total Labor = Appointment Payouts + $130.00
```

---

### Settings Persistence

**Storage Method:**
- Browser localStorage
- Per-computer, per-browser
- Survives:
  - Browser refresh
  - Closing and reopening browser
  - Computer restart

**Does NOT sync:**
- Across different computers
- Across different browsers on same computer
- When using Incognito/Private mode

**Updating Settings:**
- Click "💾 Save Settings" button
- Green confirmation message appears
- All calculations immediately update
- No need to re-upload data

**Resetting Settings:**
- Clear browser data/cache
- Or manually change each setting back to default
- Or delete localStorage for the page

---

## Advanced Client Segmentation

### Overview
Strategic client segments with downloadable contact lists for targeted marketing and retention efforts.

**Location:** Customers tab → Advanced Segmentation section

### The 5 Strategic Segments

#### 1. 👑 VIP Clients
**Definition:** Customers with Lifetime Value > $2,500

**Characteristics:**
- Highest value customers
- Frequent visitors
- Typically long-term members
- Loyal and engaged

**Business Value:**
- Top revenue generators
- Lowest churn risk
- Best referral sources
- Premium service candidates

**Marketing Strategy:**
- VIP recognition program
- Exclusive offers
- Early access to new services
- Birthday/anniversary acknowledgment
- Referral incentives

**Contact List Includes:**
- Name and email
- LTV
- Total appointments
- First and last visit dates
- Membership status

---

#### 2. 💳 Inactive Paid Members
**Definition:** Active membership but 30+ days since last appointment

**Characteristics:**
- Paying but not using services
- At high risk of cancellation
- May have forgotten about membership
- Could be having schedule/access issues

**Business Value:**
- Quick win opportunity
- Immediate revenue recovery
- Prevent churn before cancellation
- Re-engagement potential

**Intervention Strategy:**
- Proactive outreach via email/text
- "We miss you" campaigns
- Flexible scheduling offers
- Survey about barriers
- Book appointment on their behalf
- Urgent priority (prevent cancellation)

**Contact List Includes:**
- Name and email
- Membership type
- Days since last visit
- Last appointment date
- Membership value (monthly)

**Action Items:**
- Contact within 24-48 hours of appearing in segment
- Personalized outreach (not generic)
- Make it easy to reschedule
- Address potential barriers proactively

---

#### 3. ⚠️ At-Risk Clients
**Definition:** 45+ days since last visit (no active membership)

**Characteristics:**
- Inactive but not officially churned
- May have forgotten about services
- Life circumstances may have changed
- Still in window for reactivation

**Business Value:**
- Reactivation opportunity
- Previous customers (lower acquisition cost than new)
- Know your service/quality
- Warm leads for win-back campaigns

**Win-Back Strategy:**
- "We miss you" email series
- Special comeback offer
- Survey about why they stopped
- Address previous concerns
- Limited-time incentive
- New service/offering announcements

**Contact List Includes:**
- Name and email
- Days inactive
- Last visit date
- Total past appointments
- Last service type
- Previous LTV

**Timing:**
- Act between days 45-90
- After 90 days, reactivation rate drops significantly
- Multiple touchpoints over 2-3 weeks

---

#### 4. 🌱 New Clients
**Definition:** Customers with fewer than 3 total visits

**Characteristics:**
- Early in customer journey
- Haven't formed habits yet
- High churn risk if not nurtured
- Most moldable for retention

**Business Value:**
- Shape early experience
- Build long-term relationship
- Establish visit patterns
- Convert to members
- Highest lifetime impact potential

**Nurture Strategy:**
- Welcome series automation
- Education about benefits
- Encourage consistent booking
- Membership conversion offers
- Check-in after each visit
- Collect feedback early
- Make them feel special

**Contact List Includes:**
- Name and email
- Total visits (1, 2, or 3)
- First visit date
- Days since last visit
- Services tried
- Intro offer status

**Critical Period:**
- First 30 days is make-or-break
- Goal: Get them to visit 3+ times in first month
- After 3 visits, retention rate jumps significantly

---

#### 5. ⚡ High-Frequency Clients
**Definition:** Weekly visitors (7 days or less between visits)

**Characteristics:**
- Most engaged customers
- Seeing results
- May or may not have memberships
- Value your services highly

**Business Value:**
- Prime membership candidates
- Paying per-visit (higher cost to them)
- Ready for upselling
- Great testimonial sources
- Referral candidates

**Upsell Strategy:**
- Show membership ROI
- "You're already visiting weekly, save with membership"
- Premium membership upgrades
- Add-on services
- Bulk appointment packages
- Loyalty program enrollment

**Contact List Includes:**
- Name and email
- Average days between visits
- Total appointments
- Total spent
- Membership status
- Savings potential with membership

**Pitch:**
```
"You visit every week - that's $430/month!
With our 4 Hour/Month membership at $406.32,
you'd save $23.68 monthly while guaranteeing your spots."
```

---

### Using Segment Data

#### Viewing Segment Details
**In Dashboard:**
- Each segment shows:
  - Count (number of customers)
  - Total revenue from segment
  - Average per customer
- Click "View Details" to see customer list

#### Segment Modal
Opens when clicking "View Details":

**Customer Table:**
- Name
- Email
- Segment-specific metrics
- Last visit date
- Total appointments
- LTV or relevant value

**Sorting:**
- Click column headers
- Default: By value (highest first)

**Actions:**
- Download CSV
- Copy emails for bulk sending

#### Downloading Contact Lists

**Steps:**
1. Click segment "View Details"
2. Click "📥 Export to CSV"
3. File downloads immediately
4. Opens in Excel/Google Sheets

**File Contents:**
- All customers in segment
- Full contact information
- Relevant metrics
- Ready for email marketing tools
- Can import to:
  - Mailchimp
  - Constant Contact
  - Klaviyo
  - Direct email merge

**File Naming:**
- `vital-stretch-[segment-name]-[date].csv`
- Example: `vital-stretch-vip-clients-2024-11-04.csv`

---

### Segment Best Practices

#### Update Frequency
- **Daily:** Check Inactive Paid Members (urgent!)
- **Weekly:** Review New Clients and At-Risk
- **Monthly:** Analyze VIP and High-Frequency for campaigns

#### Priority Order
1. **Inactive Paid Members** - Prevent churn
2. **New Clients** - Build retention
3. **At-Risk** - Win back
4. **High-Frequency** - Upsell to memberships
5. **VIP** - Maintain loyalty

#### Campaign Ideas

**Inactive Paid Members:**
- Subject: "Your appointment is waiting!"
- Offer: Free upgrade to longer session
- Urgency: "Use it before you lose it"

**At-Risk:**
- Subject: "We miss you at The Vital Stretch"
- Offer: 20% off return visit
- Survey: "What can we improve?"

**New Clients:**
- Subject: "Welcome to The Vital Stretch family"
- Education: Benefits of regular stretching
- Offer: Book 3rd visit, get discount

**High-Frequency:**
- Subject: "You're a regular - here's your reward"
- Offer: Membership at discounted rate
- Show: Savings calculation

**VIP:**
- Subject: "Thank you for being a VIP"
- Offer: Refer a friend, both get credit
- Exclusive: Early access to new services

---

## Calculation Methodologies

### Revenue Calculations

#### Total Revenue
```
Sum of all "Paid Amount" from completed appointments
Excludes: Cancelled, No-show, Refunded
Formula: Σ(Paid Amount) where Status = 'Completed'
```

#### Average Revenue per Appointment
```
Total Revenue ÷ Number of Completed Appointments
Formula: Σ(Revenue) / Count(Appointments)
Example: $25,000 / 250 appointments = $100/appt
```

#### Monthly Recurring Revenue (MRR)
```
Sum of all active monthly subscription values
Source: Membership Sales CSV
Filter: Expired = 'No', Frozen = 'No'
Formula: Σ(Paid Amount) for active memberships
```

#### MRR Growth Rate
```
(Current MRR - Previous MRR) / Previous MRR × 100
Example: ($5,000 - $4,500) / $4,500 × 100 = 11.1% growth
```

---

### Labor Cost Calculations

#### Appointment Labor Cost
```
Sum of all appointment payouts
Source: Payroll appointments CSV
Field: "Payout" or "Amount Owed"
Includes: Table time payouts only
```

#### Non-Appointment Labor Cost
```
Formula: (Clocked Hours - Appointment Hours) × Base Hourly Rate
Source: Payroll time tracking CSV + appointments CSV
Example:
  Clocked: 40 hours
  Appointment: 32 hours
  Non-appointment: 8 hours
  Base rate: $13/hour
  Cost: 8 × $13 = $104
```

#### Total Labor Cost
```
Formula: Appointment Labor + Non-Appointment Labor
Used in all profitability calculations
```

---

### Profitability Calculations

#### Net Profit
```
Formula: Revenue - Total Labor - Franchise Fee - Brand Fund - CC Fees

Example:
Revenue:           $25,000
Labor Cost:        $8,500
Franchise Fee (7%): $1,750
Brand Fund (1.5%):   $375
CC Fees (2.9%):      $725
────────────────────────
Net Profit:       $13,650
Profit Margin:     54.6%
```

#### Profit Margin
```
Formula: (Net Profit / Revenue) × 100
Example: ($13,650 / $25,000) × 100 = 54.6%
```

---

### Utilization Calculations

#### Individual Utilization
```
Formula: (Appointment Hours / Clocked Hours) × 100
Source: Time tracking + appointments data

Example:
  Appointment hours: 32
  Clocked hours: 40
  Utilization: (32 / 40) × 100 = 80%
```

#### Average Utilization
```
Formula: Average of all individual utilization rates
Or: Total Appointment Hours / Total Clocked Hours × 100
```

#### Target Utilization
- **Excellent:** 80%+
- **Good:** 70-80%
- **Fair:** 60-70%
- **Poor:** <60%

**Note:** 100% utilization is unrealistic (need breaks, prep, cleanup)

---

### Cancellation Calculations

#### Lost Value (Monthly Recurring Revenue)
**Critical:** This calculates the MONTHLY revenue impact, not one-time loss

```
For each cancellation:
1. Match customer email to Membership Sales CSV
2. Find most recent membership purchase for that customer
3. Take "Paid Amount" as monthly value
4. Sum all monthly values

Example:
Customer A cancelled "1 Hour/Month" at $107.50/month
Customer B cancelled "2 Hours/Month" at $186.15/month
Customer C cancelled "4 Hours/Month" at $406.32/month
────────────────────────────────────────────────────
Total Lost MRR: $699.97/month

This represents ONGOING monthly revenue loss, not a one-time hit.
```

**Why match by email:**
- Cancellations CSV doesn't have Membership ID
- Customer email is reliable identifier
- Gets correct current subscription price
- Handles upgrades/downgrades properly

**Why use most recent membership:**
- Customer may have changed plans
- Most recent = what they were paying when they cancelled
- Accurate representation of loss

#### Churn Rate
```
Formula: (Cancellations / Total Memberships Sold) × 100
Period: Typically monthly
Example: 5 cancellations / 100 members = 5% churn rate
```

#### Churn Rate by Location
```
Formula: (Location Cancellations / Location Sales) × 100

Method:
1. Build customer location map from cancellations CSV
2. Map each membership sale to location via customer email
3. Calculate churn per location

Example:
Eden Prairie: 3 cancellations / 45 sales = 6.7% churn
Maple Grove: 2 cancellations / 35 sales = 5.7% churn
```

**Note:** Uses email mapping because Membership Sales CSV doesn't have location field

#### Churn Rate by Membership Type
```
Formula: (Type Cancellations / Type Sales) × 100

Example:
1 Hour/Month: 5 cancellations / 50 sold = 10% churn
2 Hours/Month: 3 cancellations / 30 sold = 10% churn
4 Hours/Month: 1 cancellation / 20 sold = 5% churn
```

**Insight:** Lower churn on premium memberships suggests good value perception

---

### Customer Metrics

#### Customer Lifetime Value (LTV)
```
Source: Leads & Customers CSV (provided by Momence)
Or calculated: Total Revenue from Customer

Average LTV: Sum(Individual LTVs) / Count(Customers)
```

#### Customer Retention Rate
```
Formula: (Returning Customers / Total Customers) × 100
Returning = customers with 2+ appointments
Example: 150 returning / 200 total = 75% retention
```

#### Average Days Between Visits
```
For each customer with 2+ visits:
  Days = (Last Visit - First Visit) / (Visit Count - 1)
Average: Mean of all customer averages
```

#### Visit Frequency Distribution
```
Segments:
- Weekly: ≤7 days between visits
- Bi-weekly: 8-14 days
- Monthly: 15-30 days
- Occasional: 31-60 days
- Rare: 60+ days
```

---

### Appointment Counting

#### Total Appointments
```
Count of all completed appointments in period
Includes: Paid + Intro
Excludes: Cancelled, No-show
```

#### Paid Appointments
```
Total Appointments - Intro Appointments
Only non-intro, revenue-generating appointments
Used for 300/month goal tracking
```

#### Intro Appointments
```
Appointments matching intro offer criteria:
- Service name contains: "Intro", "Trial", "First", "New"
- Or: Marked as intro in data
- Or: Special intro pricing
Used for 50/month goal tracking
```

**Important:** Paid and Intro are mutually exclusive (no double counting)

---

### Conversion Calculations

#### Lead to Customer Conversion
```
Formula: (Customers / Total Leads) × 100
Source: Leads & Customers CSV
Customer = Type = "Customer"
Lead = Type = "Lead"
```

#### Intro to Paid Conversion
```
Formula: (Customers with Paid Appt after Intro / Total Intro Appts) × 100
Example: 40 converted / 50 intros = 80% conversion
```

#### First Visit to Return Conversion
```
Formula: (Customers with 2+ visits / Total Customers) × 100
Example: 150 returning / 200 customers = 75%
```

---

### Commission Calculations

#### Total Commissions
```
Sum of:
- Membership Sales Commissions (from commissions CSV)
- Product Sales Commissions (from commissions CSV)

Excludes:
- Service/appointment commissions (not in data)
- Tips (separate field)
```

#### Commission per VSP
```
Aggregate from individual commission files
Source: momence-commissions-[vsp-name].csv
```

---

## Data Requirements & CSV Structures

### File 1: Membership Sales
**File Name:** `momence--membership-sales-export.csv`

#### Required Fields:
| Field Name | Type | Example | Notes |
|------------|------|---------|-------|
| Purchase ID | Text | "52217744" | Unique identifier |
| First Name | Text | "John" | Customer first name |
| Last Name | Text | "Smith" | Customer last name |
| Customer Email | Email | "john@example.com" | **KEY FIELD** for matching |
| Membership ID | Text | "423762" | Unique membership ID |
| Membership Name | Text | "4 Hours/Month" | Type of membership |
| Bought Date/Time (GMT) | Datetime | "2025-11-03T23:02:08.717Z" | ISO 8601 format |
| Paid Amount | Decimal | "406.32" | **Monthly subscription price** |
| Membership Type | Text | "subscription" | Usually "subscription" |
| Remaining/ Expiry/ Renewal | Datetime | "2025-12-03T23:02:08.695Z" | Next renewal date |
| Payment Token | Text | "pi_3SPWlE..." | Stripe/payment ID |
| Expired | Text | "No" or "Yes" | Membership status |
| Frozen | Text | "No" or "Yes" | Frozen status |
| Refunded | Decimal | "0.00" | Refund amount |
| Sold by | Email | "vsp@example.com" | VSP who sold it |

#### Data Quality Notes:
- **Customer Email** is critical for cancellation matching
- **Paid Amount** represents monthly subscription cost (not one-time)
- **Expired** = "No" means active membership
- **Frozen** = "Yes" means temporarily suspended
- Sold by may be empty string

#### Sample Row:
```csv
"52217744","Imran","Reasat","ireasat@comcast.net","423762","4 Hours/Month","2025-11-03T23:02:08.717Z","406.32","subscription","2025-12-03T23:02:08.695Z","pi_3SPWlEASxZM6NZHe06MZQN79","No","No","0.00",""
```

---

### File 2: Membership Cancellations
**File Name:** `momence--membership-sales-export__1_.csv`

#### Required Fields:
| Field Name | Type | Example | Notes |
|------------|------|---------|-------|
| Customer Name | Text | "Nick Naumann" | Full name |
| Customer Email | Email | "nick_naumann@yahoo.com" | **KEY FIELD** for matching |
| Membership | Text | "1 Hour/Month" | Cancelled membership type |
| Cancelled at | Text | "2025-10-28, 1:53 PM" | Date and time format |
| Reason | Text | "It's too expensive..." | Cancellation reason |
| Possible improvements | Text | "Better pricing" | Customer feedback |
| Home location | Text | "Eden Prairie" | **Location field** |

#### Data Quality Notes:
- **Customer Email** matches to Membership Sales for value lookup
- **Home location** is the ONLY location field in datasets (used for mapping)
- **Reason** may have multi-level structure: "Category > Subcategory"
- **Possible improvements** often empty
- Date format: "YYYY-MM-DD, HH:MM AM/PM"

#### Sample Row:
```csv
"Nick Naumann","nick_naumann@yahoo.com","1 Hour/Month","2025-10-28, 1:53 PM","","","Eden Prairie"
```

#### Reason Examples:
```
"It's too expensive for me > Perceived value doesn't match cost"
"Issues with my subscription > Plan lacks flexibility"
"Relocating/moving"
"Health/injury issues"
"Not seeing results"
```

---

### File 3: New Leads & Customers
**File Name:** `momence-new-leads-and-customers.csv`

#### Required Fields:
| Field Name | Type | Example | Notes |
|------------|------|---------|-------|
| First name | Text | "Sarah" | Customer first name |
| Last name | Text | "Johnson" | Customer last name |
| E-mail | Email | "sarah@example.com" | Customer email |
| Type | Text | "Customer" or "Lead" | Classification |
| Join date | Date | "2024-03-15" | When added to system |
| Aggregator | Text | "Google" | Acquisition source |
| First purchase | Text | "1 Hour Stretch" | Initial service |
| First purchase date | Date | "2024-03-20" | Date of first appointment |
| LTV | Decimal | "547.82" | Lifetime Total Value |

#### Data Quality Notes:
- **Type** = "Customer" means at least 1 purchase
- **Type** = "Lead" means no purchases yet
- **Aggregator** shows marketing channel effectiveness
- **LTV** is pre-calculated by Momence
- **Join date** vs **First purchase date** shows conversion speed

#### Sample Row:
```csv
"Sarah","Johnson","sarah@example.com","Customer","2024-03-15","Google","1 Hour Stretch","2024-03-20","547.82"
```

#### Common Aggregator Values:
- Google
- Facebook
- Instagram
- Referral
- Walk-in
- Website
- Groupon
- Other

---

### File 4: Payroll ZIP Contents
**File Name:** `momence-payroll-report-summary.zip`

#### Contains (per practitioner):

**A. Appointments File**
`momence-payroll-appointments-[name].csv`

Critical Fields:
- Date/Time
- Customer Email
- Customer First Name, Last Name
- Practitioner First Name, Last Name (your VSP)
- Paid Amount (revenue)
- Payout (what VSP is paid)
- Package/Appointment Name (service type)
- Location
- Status (Completed, Cancelled, etc.)
- Payment Method
- Duration (in minutes)

**B. Appointments Aggregate**
`momence-payroll-appointments-[name]-aggregate.csv`
- Summary statistics per VSP
- Totals by week or month

**C. Time Tracking File**
`momence-payroll-time-[name].csv`

Critical for Utilization:
- Clock In Time
- Clock Out Time
- Duration (hours)
- Date
- Practitioner name

**D. Commissions File**
`momence-commissions-[name].csv`

Commission Details:
- Sale Date
- Commission Amount
- Commission Type (Membership or Product)
- Product Name (cleaned of special characters)
- Customer info

**E. Classes File**
`momence-payroll-classes-[name].csv`
- Group classes taught (if applicable)

**F. Tips File**
`momence-payroll-tips-[name].csv`
- Tips received (usually minimal in stretch business)

#### ZIP Processing:
1. Dashboard extracts all files in-browser (no server)
2. Identifies file type by name pattern
3. Combines all VSP appointment files
4. Combines all time tracking files
5. Combines all commission files
6. Handles special characters automatically
7. Links data by practitioner name and date

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Dashboard shows "No Data Available"
**Symptoms:**
- Empty state message visible
- No tabs or metrics showing

**Solutions:**
1. Click 📤 Upload button and upload your CSV files
2. Ensure files are from Momence (correct format)
3. Check that files aren't corrupted (open in Excel to verify)
4. Try refreshing browser and re-uploading

---

#### Issue: Charts not displaying
**Symptoms:**
- Metrics show but charts are blank
- Empty chart containers
- Console errors (F12 to check)

**Solutions:**
1. Wait for charts to load (large datasets take 5-10 seconds)
2. Refresh the page (F5)
3. Try different browser (Chrome recommended)
4. Check JavaScript is enabled
5. Clear browser cache
6. Ensure Chart.js library loaded (check browser console)

---

#### Issue: "Churn Rate by Location" shows no data
**Symptoms:**
- Chart exists but shows "No data"
- Other location charts work fine

**Solutions:**
1. Ensure BOTH membership sales AND cancellations CSVs are uploaded
2. Verify cancellations CSV has "Home location" field populated
3. Check that customer emails match between files
4. This was a bug in older versions - ensure you have v2.20251104.06+

**How it works now:**
- Matches customers by email between cancellations and sales
- Uses location from cancellations CSV (only place it exists)
- Should work if both files are uploaded

---

#### Issue: Customer names showing as "Unknown" in cancellation modals
**Symptoms:**
- Click monthly cancellations bar
- Modal shows "Unknown" for customer names

**Solutions:**
1. This was fixed in v2.20251104.06
2. Ensure you have latest version (check footer)
3. Cancellations CSV should have "Customer Name" field
4. Dashboard tries multiple field name variations automatically

**Current logic tries:**
- "Customer Name" (primary)
- "First name" + "Last name"
- "First Name" + "Last Name"
- Falls back to "Unknown" only if all missing

---

#### Issue: Practitioner names showing as email addresses
**Symptoms:**
- VSP tab shows emails instead of names

**Solutions:**
1. This should NOT happen in current version
2. Ensure payroll ZIP has "Practitioner First Name" and "Practitioner Last Name"
3. Check appointments CSV has these fields
4. If missing, contact Momence about payroll export format

---

#### Issue: Lost Revenue showing $0 for cancellations
**Symptoms:**
- Total Lost Revenue = $0
- Individual cancellation values = $0

**This was a major bug - FIXED in v2.20251104.07**

**Solutions:**
1. Update to v2.20251104.07 or later
2. Ensure membership sales CSV uploaded
3. Ensure cancellations CSV uploaded
4. Verify customer emails exist in both files

**How it works now:**
- Matches by Customer Email (not Membership ID)
- Finds most recent membership purchase
- Uses "Paid Amount" as monthly value
- Accurately calculates MRR impact

---

#### Issue: Monthly Appointments vs Goal seems too high
**Symptoms:**
- Goal: 300 paid appointments
- Chart shows 350+ appointments
- Doesn't match your records

**This was a bug - FIXED in v2.20251104.07**

**Problem:**
- Old version counted ALL appointments (paid + intro)
- Inflated the paid appointments count

**Solutions:**
1. Update to v2.20251104.07
2. Chart now titled "Monthly Paid Appointments vs Goal"
3. Excludes intro appointments
4. Intro tracked separately (50/month goal)

---

#### Issue: ZIP file upload fails or hangs
**Symptoms:**
- Upload spinner keeps spinning
- No green checkmark appears
- Browser freezes

**Solutions:**
1. **Check file size:** Very large ZIPs (>100MB) may take 30-60 seconds
2. **Don't unzip first:** Upload the .zip file directly
3. **Try smaller date range:** Export just 90 days instead of all-time
4. **Close other tabs:** Free up browser memory
5. **Try different browser:** Chrome handles large files best
6. **Check file integrity:** Re-download from Momence if corrupted

---

#### Issue: Utilization metrics not showing
**Symptoms:**
- No utilization cards or charts
- Other VSP metrics visible

**This is normal if:**
- You haven't uploaded payroll ZIP file
- Payroll ZIP doesn't include time tracking files
- VSPs don't use time clock in Momence

**Solutions:**
1. Upload payroll ZIP file (see data export instructions)
2. Ensure payroll export includes time tracking option
3. Check that VSPs actually clock in/out in Momence
4. If no time clock used, utilization simply won't appear (that's OK)

---

#### Issue: Commission tracking not showing
**Symptoms:**
- No commission metrics in VSP tab
- Expected to see commission data

**This is normal if:**
- No payroll ZIP uploaded
- VSPs haven't sold any memberships/products in period
- Payroll export doesn't include commissions file

**Solutions:**
1. Upload payroll ZIP (commissions are inside)
2. Check date range includes period with sales
3. Verify payroll export selected "Include Commissions"
4. If no commissions earned, field simply won't appear

---

#### Issue: Settings not saving
**Symptoms:**
- Change settings and click Save
- Refresh page, settings revert to defaults

**Solutions:**
1. Check that JavaScript is enabled
2. Check browser allows localStorage (not in Incognito mode)
3. Try different browser
4. Check for browser extensions blocking storage
5. Look for confirmation message after clicking Save

**Note:** Settings are per-browser, per-device (don't sync)

---

#### Issue: Data seems incorrect or outdated
**Symptoms:**
- Numbers don't match your expectations
- Old data visible

**Solutions:**
1. Check date filters at top of page
2. Check location and practitioner filters
3. Click "Reset All" to clear filters
4. Re-export fresh data from Momence
5. Click 🔄 Refresh Data button
6. Re-upload updated CSV files

---

#### Issue: Browser performance slow with large datasets
**Symptoms:**
- Dashboard laggy or unresponsive
- Charts take long to render
- Filter changes slow

**Solutions:**
1. **Use date filters:** Analyze smaller time periods
2. **Close unused tabs:** Free up memory
3. **Increase RAM:** Large datasets (50,000+ rows) need 8GB+ RAM
4. **Use Chrome:** Better JavaScript performance
5. **Split analysis:** Do separate analysis per quarter/location

---

#### Issue: Comparison mode not working
**Symptoms:**
- Select "Previous Period" but no comparison shown
- No orange bars or percentage changes

**Solutions:**
1. Ensure you have enough historical data
2. "Same Period Last Year" needs data from last year
3. Check that date range selected is not the earliest period
4. Some tabs show comparison differently than others
5. Try "Previous Period" first (most reliable)

---

#### Issue: Export CSV downloads not working
**Symptoms:**
- Click "Export to CSV" but nothing downloads

**Solutions:**
1. Check browser download settings
2. Check pop-up blocker (may block downloads)
3. Look in Downloads folder (may download silently)
4. Try different browser
5. Check file permissions (write access to Downloads)

---

#### Issue: Special characters in data (®, ™, ©, Â)
**Symptoms:**
- Product names have weird characters
- Text looks corrupted

**This should be fixed automatically**

**Dashboard automatically cleans:**
- ® (registered trademark)
- ™ (trademark)
- © (copyright)
- Â (encoding artifact)

**If still seeing issues:**
1. Check you have v2.20251103.04 or later
2. May be different character - report to developer
3. Workaround: Manually clean CSV before upload

---

#### Issue: Modal windows won't close
**Symptoms:**
- Click modal background but modal stays open
- Can't access rest of dashboard

**Solutions:**
1. Press ESC key
2. Click the X button in modal corner
3. Refresh page (last resort - will lose filters)

---

#### Issue: Appointment heatmap not clickable
**Symptoms:**
- Instructions say click days/hours
- Nothing happens when clicking

**Solutions:**
1. Ensure payroll data uploaded (heatmap needs appointment data)
2. Check you're clicking actual day names (not empty cells)
3. Check you're clicking hour cells with color (appointments)
4. May need to hover first to ensure chart is active
5. Try clicking different cells

---

#### Issue: Goal charts not updating after changing settings
**Symptoms:**
- Changed monthly goals in settings
- Charts still show old goals

**Solutions:**
1. Refresh the page after saving settings
2. Or switch to different tab and back to Overview
3. Charts should update automatically but may need refresh

---

#### Issue: Can't find upload button
**Symptoms:**
- Dashboard open but can't upload files

**Solutions:**
1. Look for 📤 icon in top-right corner
2. If empty state visible, also has prominent upload section
3. May need to scroll to top of page
4. Try refreshing page

---

### Getting Additional Help

**Before contacting support:**
1. Check dashboard version (footer)
2. Try on different browser
3. Check browser console (F12) for errors
4. Try with smaller dataset
5. Review this troubleshooting guide

**Information to provide:**
- Dashboard version number
- Browser and version
- Operating system
- File sizes of CSVs
- Specific error messages
- Screenshots of issue
- Steps to reproduce

---

## Best Practices

### Data Management Best Practices

#### Regular Export Schedule
- **Weekly:** Export last 7 days for real-time monitoring
- **Monthly:** Export full month at month-end for analysis
- **Quarterly:** Export full quarter for strategic review
- **Annually:** Export all-time for year-end reporting

#### File Organization
```
Vital Stretch Data/
├── 2024/
│   ├── 01-January/
│   │   ├── momence-membership-sales-2024-01.csv
│   │   ├── momence-cancellations-2024-01.csv
│   │   ├── momence-leads-customers-2024-01.csv
│   │   └── momence-payroll-2024-01.zip
│   ├── 02-February/
│   └── ...
├── Dashboard/
│   └── vital-stretch-dashboard-v7-UPDATED.html
└── Exports/
    ├── vip-clients-2024-01-15.csv
    └── ...
```

#### Backup Strategy
- **Local:** Keep copies on your computer
- **Cloud:** Sync to Google Drive, Dropbox, or OneDrive
- **Frequency:** After each export
- **Retention:** Keep at least 2 years of data

#### Data Quality Checks
Before uploading to dashboard:
1. Open CSV in Excel/Google Sheets
2. Check for missing data (empty cells)
3. Verify dates are in correct format
4. Ensure email addresses are valid
5. Check for duplicate rows

---

### Analysis Best Practices

#### Start Broad, Then Drill Down
1. **Month 1:** Review full year "All Time" view
2. **Month 2:** Focus on last 90 days
3. **Ongoing:** Use weekly and monthly views
4. **Deep Dives:** Filter to specific locations/VSPs/issues

#### Use Comparison Mode Strategically
- **Week-over-week:** Use "Previous Period" for short-term trends
- **Month-over-month:** Use "Last Month" for monthly reviews
- **Year-over-year:** Use "Same Period Last Year" for annual growth
- **Seasonal:** Compare same months across years

#### Goal Setting Approach
1. **Baseline:** Run 3 months with default goals
2. **Analyze:** Review actual performance
3. **Adjust:** Set realistic stretch goals (+10-15%)
4. **Review:** Quarterly goal review and adjustment
5. **Seasonal:** Different goals for high/low seasons

#### Filter Strategy
- **Daily monitoring:** No filters (all data)
- **Weekly reviews:** Last 7 days
- **Monthly reviews:** This Month, then Last Month
- **VSP reviews:** Practitioner filter + Last 30 Days
- **Location analysis:** Location filter + appropriate date range

---

### Business Strategy Best Practices

#### Using Segments Effectively

**VIP Clients (>$2,500 LTV):**
- Contact: Monthly
- Purpose: Loyalty appreciation, early access, referrals
- Frequency: 1x per month
- Channel: Personal email or call

**Inactive Paid Members (30+ days):**
- Contact: Immediately (within 24-48 hours)
- Purpose: Prevent churn, re-engage
- Frequency: Every 7 days until resolved
- Channel: Email + text + phone if needed
- Priority: URGENT

**At-Risk Clients (45+ days):**
- Contact: Within 1 week of appearing in segment
- Purpose: Win-back, reactivation
- Frequency: Series of 3-4 touchpoints over 2 weeks
- Channel: Email sequence + special offer

**New Clients (<3 visits):**
- Contact: After each visit
- Purpose: Nurture, educate, habit formation
- Frequency: Every 3-7 days for first 30 days
- Channel: Automated email series + personal touches

**High-Frequency Clients (Weekly visitors):**
- Contact: After 4 weekly visits
- Purpose: Convert to membership, show ROI
- Frequency: One-time targeted offer
- Channel: Email with personalized savings calculation

#### Retention Strategy
1. **Identify at-risk early:** Use segments proactively
2. **Act quickly:** Contact inactive members within 24-48 hours
3. **Personalize:** Reference their history and preferences
4. **Remove friction:** Make it easy to reschedule
5. **Follow up:** Don't give up after one contact
6. **Collect feedback:** Ask why they haven't been in

#### Growth Strategy
1. **Upsell high-frequency:** Convert weekly visitors to members
2. **Nurture new clients:** Focus on first 30 days
3. **Reactivate at-risk:** 45-90 day window is key
4. **Reward VIPs:** Leverage referrals
5. **Address churn reasons:** Fix root causes

#### Pricing Strategy
Use dashboard data to inform pricing:
- **Monitor churn by type:** High churn on a tier = price/value issue
- **Compare to goals:** Revenue below goal = need more sales or higher prices
- **Analyze competitors:** Use market research + your data
- **Test gradually:** Small increases, monitor churn impact

#### Staffing Strategy
Use utilization and appointment patterns:
- **Peak hours heatmap:** Schedule more VSPs during busy times
- **Low utilization:** Reduce hours or reassign tasks
- **High utilization (>90%):** Add VSPs to meet demand
- **Non-appointment time:** Balance cleaning/admin with appointment slots

---

### Dashboard Usage Best Practices

#### Weekly Review Routine
**Every Monday (15 minutes):**
1. Open dashboard
2. Upload last 7 days data (if doing incremental)
3. Check "Last 7 Days" quick filter
4. Review Overview tab KPIs
5. Check Inactive Paid Members segment → Act immediately
6. Check goal progress
7. Note action items

#### Monthly Business Review (1 hour)
**First week of new month:**
1. Export full previous month data
2. Upload to dashboard
3. Set filter to "Last Month"
4. Review all 8 tabs systematically:
   - Overview: Did we hit goals?
   - Timeline: What were the trends?
   - VSP: Any performance issues or wins?
   - Customers: LTV and behavior patterns
   - Retention: Churn analysis
   - Journey: Conversion funnel health
   - Memberships: Sales performance
   - Cancellations: Any alarming patterns?
5. Export segments for marketing campaigns
6. Document learnings and action items
7. Adjust goals if needed
8. Share insights with team

#### Quarterly Strategic Review (3 hours)
**First week of new quarter:**
1. Export full previous quarter
2. Set filter to last 90 days
3. Use comparison mode: "Last Quarter"
4. Deep analysis of each tab
5. Identify 3-5 key opportunities
6. Set quarterly strategic goals
7. Plan marketing campaigns
8. Adjust staffing plans
9. Review and refine processes
10. Present findings to team

#### Ad-Hoc Analysis
**When to do:**
- Major marketing campaign launch
- New VSP onboarding
- Service or pricing changes
- Competitive threats
- Seasonal planning

**How to do:**
1. Define specific question
2. Set appropriate filters
3. Use comparison mode if relevant
4. Export data if needed for further analysis
5. Document findings
6. Make data-driven decision

---

### Communication Best Practices

#### Sharing Dashboard Insights

**With Team:**
- Weekly: High-level KPIs in team meeting
- Monthly: Full review with all VSPs
- Share wins and opportunities
- Make data transparent
- Tie insights to actions

**With Ownership/Corporate:**
- Monthly: Summary report with key metrics
- Quarterly: Strategic review and goals
- Focus on: Revenue, profitability, growth, churn
- Highlight successes and challenges
- Request support where needed

**With Individual VSPs:**
- Monthly: 1-on-1 performance review
- Use VSP tab detail modal
- Show their metrics
- Discuss utilization and commissions
- Set improvement goals
- Celebrate wins

#### Email Campaign Best Practices
Using exported segment lists:

**Subject Lines:**
- Personal: Use recipient name
- Clear: State benefit or urgency
- Short: <50 characters
- Emoji OK: But don't overuse

**Email Content:**
- Personal: Reference their history
- Brief: 2-3 short paragraphs
- Clear CTA: Make it easy to act
- Mobile-friendly: Most read on phone
- Professional: Use branded template

**Frequency:**
- VIP: Monthly touches
- Inactive Members: Weekly until re-engaged
- At-Risk: Every 3-5 days (3-4 total)
- New Clients: Every 3-7 days for first month
- High-Frequency: One targeted offer

**Testing:**
- A/B test subject lines
- Test different offers
- Test sending times
- Measure open and click rates
- Iterate based on results

---

## Privacy & Compliance

### Data Handling

#### Client-Side Processing
- **All processing in browser:** No data sent to external servers
- **No external API calls:** Except for CDN libraries (Chart.js, PapaParse, JSZip)
- **No tracking:** No Google Analytics, cookies, or third-party scripts
- **No accounts:** No login, no user database
- **No cloud storage:** Everything local to your device

#### Data Storage
- **Browser localStorage:** Settings only (goals, timezone, fees)
- **No file storage:** CSVs processed in memory, not saved by dashboard
- **Session-based:** Data clears when you close dashboard
- **Per-device:** Settings don't sync between computers

#### Data Security
- **Keep files secure:** Store CSV exports in encrypted folder
- **Use strong passwords:** For your Momence account
- **Secure downloads:** Only download dashboard from trusted source
- **Update regularly:** Use latest dashboard version for security fixes
- **Antivirus:** Keep your computer protected

---

### HIPAA Considerations

**The dashboard does NOT collect health information, but:**

#### Personal Information Visible
- Customer names
- Customer email addresses  
- Appointment history
- Location data
- No health conditions
- No treatment details
- No payment card data

#### Best Practices
- **Limit access:** Only authorized personnel should use dashboard
- **Secure workstations:** Lock computer when away
- **Private viewing:** Don't view dashboard in public spaces
- **Secure exports:** Encrypt segment CSV files
- **Proper disposal:** Securely delete old CSV files
- **Training:** Train staff on data privacy

#### Exporting Segment Lists
- **Email marketing tools:** Most are HIPAA-compliant if configured
- **Spreadsheets:** Password-protect exported files
- **Sharing:** Use encrypted email or secure file transfer
- **Retention:** Delete customer lists after campaign complete
- **Audit trail:** Document who accesses what data

---

### Business Continuity

#### Disaster Recovery
**What to backup:**
- Dashboard HTML file (latest version)
- All CSV exports (monthly archives)
- Settings documentation
- Analysis reports and findings
- Segment lists (if needed long-term)

**Backup locations:**
- **Primary:** Your computer (working copies)
- **Secondary:** Cloud storage (Google Drive, Dropbox)
- **Tertiary:** External hard drive (quarterly)

**Recovery procedure:**
1. Download latest dashboard version
2. Retrieve CSV files from backup
3. Upload to dashboard
4. Reconfigure settings (or load from backup)
5. Resume analysis

#### Knowledge Transfer
**Document for your team:**
- How to export data from Momence
- How to upload to dashboard
- How to interpret key metrics
- Segment strategies and campaigns
- Monthly review process
- Who has access and responsibilities

**Train multiple people:**
- Primary analyst (you)
- Backup analyst (manager or owner)
- Data exporter (admin staff)
- Don't have single point of failure

---

## Version History

### v2.20251104.07 (November 4, 2025) - CURRENT
**Critical Fixes:**
- ✅ **Fixed Lost Value for Cancellations:** Now matches by Customer Email instead of Membership ID
- ✅ **Accurate MRR calculation:** Uses "Paid Amount" from most recent membership as monthly value
- ✅ **Updated all 4 cancellation modals:** Month, Type, Location detail functions
- ✅ **Fixed Monthly Appointments vs Goal:** Now counts only paid appointments (excludes intro)
- ✅ **Renamed chart:** "Monthly Paid Appointments vs Goal" for clarity
- ✅ **Separate intro tracking:** 50/month goal tracked independently
- ✅ **Eliminated double counting:** Paid and intro appointments mutually exclusive

**Impact:** Financial analysis now accurate, goal tracking now precise

---

### v2.20251104.06 (November 4, 2025)
**Major Updates:**
- Changed default monthly revenue goal: $50,000 → $20,000
- Changed default intro appointments goal: 36 → 50
- Fixed Churn Rate by Location chart (now uses email mapping)
- Made "Compare To" label font 1pt smaller
- Enhanced customer name extraction in cancellations modals
- Improved location matching between datasets
- Updated comprehensive documentation

---

### v2.20251103.05 (November 3, 2025)
**Major Features:**
- ⚙️ Franchise Configuration section with persistent settings
- User-configurable base hourly rate (default: $13.00)
- Comprehensive labor cost tracking (appointment + non-appointment)
- New Financial Performance section in Overview tab
- Detailed labor cost breakdown with explanations
- Improved trendline visibility: 70% opacity, 3px width (colorblind-friendly)
- Enhanced heatmap interactivity: Click days for hourly breakdown, click hours for appointments
- Monthly goal column charts replacing progress bars
- Updated all profitability metrics to use comprehensive labor costs
- Renamed: "Upload Your Data" → "Upload/Set Your Franchise Data"

---

### v2.20251103.04 (November 3, 2025)
**Major Features:**
- Removed: Net Profit metric from Overview tab (added back with comprehensive calculation in v2.20251103.05)
- Added: Utilization tracking throughout dashboard
  - Overview: Average utilization metric
  - Timeline: Daily utilization trend chart
  - VSP tab: Individual utilization percentages
- Added: Commission tracking (membership & product only, excludes services)
  - Total commissions metric card
  - Individual VSP commission tracking
  - Automatic special character cleaning (®, ™, ©, Â)
- Changed: Membership average chart now shows weekly averages with clear notation
- Improved: Tab order prioritized for studio owners/managers
- Improved: Overview metrics reordered by business priority
- Improved: Timeline charts reordered by decision-making importance
- Enhanced: All utilization and commission metrics respect date filters
- Enhanced: Payroll ZIP file processing for time tracking and commissions

---

### v2.20251103.03 (November 3, 2025)
- Enhanced modal interactions
- Improved chart rendering
- Bug fixes

---

### v2.20251102.33 (November 2, 2025)
**Major Updates:**
- Added: 💳 Inactive Paid Members segment (30+ days, active membership)
- Enhanced modal close functionality  
- Added membership information to segment exports
- Improved segmentation grid layout for 5 segments
- Updated summary metrics
- Enhanced segment filtering and display

---

### v2.20251102.11 (November 2, 2025)
**Major Features:**
- Introduced: Advanced Client Segmentation
- Added initial four segments:
  - 👑 VIP Clients (>$2,500 LTV)
  - ⚠️ At-Risk Clients (45+ days inactive)
  - 🌱 New Clients (<3 visits)
  - ⚡ High-Frequency Clients (Weekly visitors)
- Implemented downloadable segment CSV exports
- Added interactive segment detail modals
- Enhanced customer analytics

---

### v2.20251101.16 (November 1, 2025)
**Initial Release:**
- Core analytics dashboard with 9 tabs (later refined to 8 with Cancellations conditional)
- Dynamic filtering system (date, location, practitioner)
- Interactive charts and drill-downs
- Basic client segmentation
- CSV export functionality
- Comparison period features
- Goal tracking
- Responsive design

---

### v1.010 (Original Version - Deprecated)
**Features:**
- API integration to Momence
- Four analytical tabs
- Charts and tables
- Real-time data sync

**Status:** Terminated due to Momence API issues
**Reason:** Switched to CSV-based approach for reliability

---

## Technical Specifications

### Technology Stack

#### Frontend
- **HTML5:** Structure and semantic markup
- **CSS3:** Styling with modern features
  - CSS Grid for layouts
  - Flexbox for components
  - CSS Variables for theming
  - Media queries for responsive design
- **JavaScript ES6+:** Interactivity and data processing
  - Arrow functions
  - Template literals
  - Destructuring
  - Async/await (where needed)
  - Classes (for modular organization)

#### Libraries (from CDN)
- **Chart.js v4.4.0:** Data visualization
  - Bar charts
  - Line charts
  - Pie charts
  - Radar charts
  - Custom plugins
  - Source: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`

- **PapaParse v5.4.1:** CSV parsing
  - Fast CSV parsing
  - Handles large files
  - Auto-detects delimiters
  - Stream parsing for big files
  - Source: `https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js`

- **JSZip v3.10.1:** ZIP file handling
  - Extract ZIP files in browser
  - No server required
  - Process multiple files
  - Source: `https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js`

#### Fonts
- **Yeseva One:** Headers (serif)
  - Source: Google Fonts
  - Gives branded look
- **System Fonts:** Body text (sans-serif)
  - Futura (if available)
  - Falls back to Arial, then sans-serif

---

### Browser Compatibility

#### Fully Supported
- ✅ **Google Chrome** v90+ (Recommended)
- ✅ **Mozilla Firefox** v88+
- ✅ **Apple Safari** v14+
- ✅ **Microsoft Edge** v90+
- ✅ **Opera** v76+

#### Not Supported
- ❌ Internet Explorer (any version)
- ❌ Old Android Browser (<2019)
- ❌ Chrome/Firefox versions older than 2020

#### Required Browser Features
- JavaScript enabled
- localStorage support
- FileReader API
- Blob/ArrayBuffer support
- ES6+ support
- Canvas API (for charts)

---

### Performance Specifications

#### File Size
- **Dashboard HTML:** ~550KB (all code inline)
- **Gzipped:** ~120KB
- **No external dependencies** (except CDN libraries)

#### Processing Capacity
- **Small datasets** (<1,000 rows): Instant processing
- **Medium datasets** (1,000-10,000 rows): 1-3 seconds
- **Large datasets** (10,000-50,000 rows): 5-15 seconds
- **Very large** (50,000-100,000 rows): 30-60 seconds
- **ZIP files** (100+ internal files): 30-60 seconds

#### Memory Requirements
- **Minimum:** 4GB RAM
- **Recommended:** 8GB RAM
- **Large datasets:** 16GB RAM recommended
- **Browser memory:** Clears on page close

#### Rendering Performance
- **Charts:** Render on-demand (lazy loading)
- **Switching tabs:** <500ms
- **Applying filters:** 1-3 seconds
- **Modal opening:** <100ms
- **Smooth scrolling:** 60fps target

---

### Data Storage

#### Browser localStorage
**What's stored:**
- Franchise settings (timezone, fees, rates)
- Monthly goals (revenue, appointments, intro)
- Last used filter preferences (maybe)

**Storage limit:** 5-10MB per domain
**Persistence:** Permanent until cleared
**Scope:** Per browser, per device

#### Session Storage
**Currently not used:** Could be added for temporary data

#### Memory Storage
**What's stored:**
- Uploaded CSV data (during session)
- Processed arrays and objects
- Chart instances
- Current filter state

**Cleared when:**
- Page refresh
- Browser close
- New data uploaded

---

### Security Features

#### No Server Communication
- All processing happens in browser
- No data transmission to external servers
- No external API calls (except CDN for libraries)
- Libraries loaded from trusted CDNs

#### Code Integrity
- All code inline (no external JS files that could be compromised)
- Open HTML file to inspect code
- No obfuscation or minification
- Readable and auditable

#### Data Protection
- No cookies set
- No tracking scripts
- No analytics
- No third-party integrations
- No cross-origin requests

---

### File Compatibility

#### Supported Formats
- **CSV:** UTF-8 encoding
- **ZIP:** Standard ZIP compression
- **Text:** UTF-8 text files

#### CSV Requirements
- Delimiter: Comma (,)
- Quotes: Double quotes for fields with commas
- Encoding: UTF-8
- Line endings: CRLF or LF
- Header row: Required (field names)

#### Unsupported Formats
- Excel files (.xlsx, .xls) - Must export to CSV first
- Databases - Must export to CSV first
- JSON - Not supported
- XML - Not supported

---

### Responsive Design

#### Breakpoints
- **Desktop:** 1920px+ (optimal)
- **Laptop:** 1366px-1919px
- **Tablet:** 768px-1365px
- **Mobile:** <768px (limited support)

**Recommendation:** Use on desktop/laptop for best experience

#### Mobile Considerations
- Charts readable on tablet
- Tables may require horizontal scroll
- Modals responsive
- Touch-friendly buttons
- Not optimized for phone screens

---

### Accessibility

#### Color Contrast
- Meets WCAG AA standards
- Dark text on light backgrounds
- Sufficient contrast ratios
- Colorblind-friendly chart colors

#### Trendline Visibility
- 70% opacity (increased from 30%)
- 3px width (increased from 2px)
- High contrast colors
- Works for colorblind users

#### Keyboard Navigation
- Tab through interface
- Enter to activate buttons
- ESC to close modals
- Arrow keys in some controls

#### Screen Reader Support
- Semantic HTML
- ARIA labels (where needed)
- Alt text on images
- Descriptive button text

---

### Known Limitations

#### Technical Limitations
- **No real-time sync:** Must manually upload new data
- **No cloud storage:** Data doesn't sync across devices
- **No collaboration:** Single user at a time
- **No version control:** Manual backup required
- **Browser dependency:** Requires modern browser
- **File size limits:** Very large files (>100MB) may be slow

#### Functional Limitations
- **No data editing:** Can't modify data in dashboard
- **No custom formulas:** Pre-defined calculations only
- **No API access:** CSV-based only
- **No scheduled reports:** Manual export required
- **No mobile app:** Web-based only

#### Data Limitations
- **Historical data:** Only what you export from Momence
- **Deleted data:** If deleted from Momence, gone from exports
- **Data quality:** Dashboard can't fix bad source data
- **Missing fields:** If Momence doesn't export it, dashboard can't show it

---

## Quick Start Checklist

### Initial Setup (One-Time)
- [ ] Configure pay rates in Momence
- [ ] Set up all practitioners in Momence
- [ ] Assign appointment pay rates
- [ ] Enable time clock (optional but recommended)
- [ ] Download dashboard HTML file
- [ ] Save to easy-to-find location
- [ ] Bookmark in browser

### Required Data Exports
- [ ] Export Membership Sales (all time)
- [ ] Export Membership Cancellations (all time)
- [ ] Export New Leads & Customers (all time)
- [ ] Export Practitioner Payroll ZIP (all time or 90 days)
- [ ] Files saved to consistent location
- [ ] File names kept standard

### First-Time Dashboard Use
- [ ] Open dashboard HTML in browser
- [ ] Click Upload button (📤)
- [ ] Upload Membership Sales CSV
- [ ] Upload Cancellations CSV  
- [ ] Upload Leads & Customers CSV
- [ ] Upload Payroll ZIP (optional)
- [ ] Wait for all green checkmarks (✅)

### Configuration
- [ ] Click Settings button (⚙️)
- [ ] Set timezone
- [ ] Configure franchise fee %
- [ ] Configure brand fund %
- [ ] Configure CC fees %
- [ ] Set monthly revenue goal
- [ ] Set monthly paid appointments goal (300)
- [ ] Set monthly intro appointments goal (50)
- [ ] Set base hourly rate
- [ ] Click Save Settings
- [ ] Verify confirmation message

### Initial Analysis
- [ ] Review Overview tab KPIs
- [ ] Check goal progress
- [ ] Review Financial Performance section
- [ ] Check Timeline trends
- [ ] Review VSP performance
- [ ] Explore Customers tab
- [ ] Check Advanced Segmentation
- [ ] Review Retention metrics
- [ ] Explore Journey funnel
- [ ] Check Memberships performance
- [ ] Analyze Cancellations (if data available)

### Immediate Actions
- [ ] Check Inactive Paid Members segment
- [ ] Export urgent segment lists
- [ ] Send immediate outreach to inactive members
- [ ] Review At-Risk clients
- [ ] Plan New Client nurture sequence
- [ ] Identify VIP clients for appreciation
- [ ] Contact High-Frequency clients about memberships

### Ongoing Routine Setup
- [ ] Schedule weekly data exports
- [ ] Schedule Monday weekly reviews (15 min)
- [ ] Schedule monthly business reviews (1 hour)
- [ ] Schedule quarterly strategic reviews (3 hours)
- [ ] Set up file backup routine
- [ ] Train backup person on dashboard
- [ ] Document your process
- [ ] Create segment campaign calendar

---

## Support & Resources

### Dashboard Support
- **Version:** Check footer for current version (v2.20251104.07)
- **Updates:** Contact your franchise administrator
- **Bug reports:** Document issue and report to developer
- **Feature requests:** Submit through proper channels

### Momence Support
- **Data export questions:** Contact Momence support
- **Account setup:** Momence customer success
- **Pay rate configuration:** Momence documentation
- **API issues:** Escalate to Momence technical team

### Learning Resources
- **This README:** Complete reference guide
- **Dashboard tooltips:** Hover over (?) icons
- **Chart labels:** Descriptive titles and legends
- **Modal instructions:** Read carefully before acting

---

## Contact & Credits

**Dashboard Version:** v2.20251104.07  
**Last Updated:** November 4, 2025  
**Dashboard Type:** Single-page HTML application  
**Designed For:** The Vital Stretch Franchise  
**Created By:** bonJoeV with ❤️

### Purpose
This dashboard is a custom analytical tool built specifically for The Vital Stretch's operational needs. It empowers franchise owners and managers to make data-driven decisions about staffing, marketing, retention, and growth strategy.

### Philosophy
- **Privacy First:** All data stays on your device
- **Simplicity:** One HTML file, no installation
- **Transparency:** Open code, clear calculations
- **Actionable:** Not just reports, but insights for action
- **Continuous Improvement:** Regular updates based on user needs

### Acknowledgments
- **The Vital Stretch:** For the opportunity to build this tool
- **Momence:** For providing comprehensive data exports
- **Chart.js:** For excellent visualization library
- **PapaParse:** For reliable CSV parsing
- **JSZip:** For client-side ZIP extraction
- **Users:** For feedback and feature requests

---

## Final Notes

This dashboard represents hundreds of hours of development, testing, and refinement. It's designed to be:

- **Comprehensive:** Covers all aspects of business analytics
- **User-Friendly:** Intuitive interface for non-technical users
- **Reliable:** Thoroughly tested with real Vital Stretch data
- **Maintainable:** Clear code for future updates
- **Private:** Your data never leaves your computer
- **Actionable:** Every metric designed to drive decisions

The goal is to empower you with data-driven insights to grow your franchise, improve customer satisfaction, increase retention, and maximize profitability.

### Remember:
- Data is only valuable if you act on it
- Segments are opportunities, not just lists
- Trends tell stories - listen to them
- Your customers want you to succeed
- Small improvements compound over time

### Success Formula:
1. **Measure:** Upload data weekly
2. **Analyze:** Review dashboard regularly
3. **Act:** Implement insights promptly
4. **Iterate:** Refine based on results
5. **Repeat:** Make it a habit

---

**Thank you for using The Vital Stretch Analytics Dashboard!**

*For the latest version and updates, contact your franchise administrator.*

---

**Document Version:** 2.0  
**Last Updated:** November 4, 2025  
**Document Type:** Complete Technical & User Documentation  
**Status:** Current and Complete

---

*End of README - Complete Documentation*
