# The Vital Stretch Analytics Dashboard - Complete Documentation

**Version:** v2.20251113.04 | **Updated:** November 13, 2024 | **Created by:** bonJoeV with ❤️

---

## Table of Contents

1. [Introduction](#introduction)
2. [Complete Data File Guide](#complete-data-file-guide)
3. [Momence Configuration](#momence-configuration)
4. [Dashboard Features](#dashboard-features)
5. [VSP Performance Analytics](#vsp-performance-analytics)
6. [Tab-by-Tab Guide](#tab-by-tab-guide)
7. [Settings & Configuration](#settings--configuration)
8. [Advanced Features](#advanced-features)
9. [Technical Specifications](#technical-specifications)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Version History](#version-history)
12. [Best Practices](#best-practices)

---

## Introduction

The Vital Stretch Analytics Dashboard is a comprehensive, browser-based analytics platform designed specifically for The Vital Stretch franchises. It processes your Momence data locally in your browser, ensuring complete privacy while providing powerful insights into your business performance.

### Core Philosophy
- **Privacy First**: Your data never leaves your computer
- **No Dependencies**: No server, no installation, no login
- **Actionable Insights**: Turn data into decisions
- **Franchise-Specific**: Built for The Vital Stretch business model

---

## Complete Data File Guide

### Overview of Data Files

The dashboard supports **9 different data files** from Momence:
- **6 Required** files for core functionality
- **3 Optional** files for enhanced features

### File 1: Membership Sales (REQUIRED)

**Purpose:** Tracks all membership purchases and recurring revenue

**Momence Path:**
1. Reports → "Membership sales - A report on membership purchases history"
2. Select date range: Last 365 days (recommended)
3. Click "Download Summary"

**Filename:** `momence--membership-sales-export.csv`

**What it contains:**
- Customer information (name, email, phone)
- Membership type and pricing
- Purchase date and payment method
- Recurring billing status
- Duration and commitment period

**Used for:**
- MRR (Monthly Recurring Revenue) calculations
- Active member counts
- Revenue projections
- Membership type analysis
- Customer lifetime value

### File 2: Membership Cancellations (REQUIRED)

**Purpose:** Tracks membership cancellations and churn

**Momence Path:**
1. Reports → "Membership sales"
2. Click the **Cancellations** tab
3. Select date range: Last 365 days (recommended)
4. Click "Download Summary"

**Filename:** `momence--membership-sales-export__1_.csv`

**What it contains:**
- Customer information
- Cancellation date
- Membership type canceled
- Monthly value lost
- Cancellation reason (if provided)

**Used for:**
- Churn rate calculations
- Lost MRR tracking
- Cancellation reason analysis
- Customer retention insights
- Win-back campaign targeting

### File 3: New Leads & Customers (REQUIRED)

**Purpose:** Tracks new lead generation and customer acquisition

**Momence Path:**
1. Reports → "New Leads & Customers by join date"
2. Select date range: Last 365 days (recommended)
3. Click "Download Summary"

**Filename:** `momence-new-leads-and-customers.csv`

**What it contains:**
- Customer/lead information
- Join date
- Lead source (if tracked)
- Contact information
- Type (lead vs customer)

**Used for:**
- Lead generation tracking
- Customer acquisition analysis
- Source attribution
- Growth rate calculations
- Marketing ROI

### File 4: Practitioner Payroll ZIP (REQUIRED)

**Purpose:** Comprehensive labor, appointment, and commission tracking

**Momence Path:**
1. Reports → "Practitioner Payroll - Multiple practitioners payroll details"
2. Select **ALL practitioners** (or individually)
3. Select date range: Last 365 days (recommended)
4. Click "Download" (creates ZIP automatically)

**Filename:** `momence-payroll-report-summary.zip`

**Contains multiple CSVs:**
- Appointment details with labor costs
- Time tracking data (clock in/out)
- Commission data (memberships & products)
- Works/doesn't work summary

**What's inside:**
- **Appointments CSV**: Revenue, pay rates, service types, customer info
- **Time Tracking CSV**: Clock in/out times, total hours, date
- **Commissions CSV**: Membership sales, product sales, commission amounts
- **Summary CSV**: Overview by practitioner

**Used for:**
- Labor cost analysis
- VSP performance metrics
- Utilization rate calculations
- Commission tracking
- Revenue per hour calculations
- Appointment-based metrics

**Important Notes:**
- Dashboard automatically extracts and processes all CSVs from ZIP
- No need to manually unzip
- Supports both "Clocked in" and "Clock in date" field variations
- Time tracking enables utilization metrics

### File 5: Leads Converted Report (REQUIRED)

**Purpose:** Tracks lead conversion and lifetime value

**Momence Path:**
1. Reports → "Leads converted" or "Lead Conversion Report"
2. Select date range: Last 365 days (recommended)
3. Click "Download Summary"

**Filename:** `momence-leads-converted-report.csv`

**What it contains:**
- Lead information and source
- Conversion date
- Time to conversion
- Initial service/purchase
- Lifetime value (LTV) per converted lead

**Used for:**
- Conversion rate by source
- LTV analysis
- Marketing effectiveness
- Lead quality scoring
- Source ROI calculations
- Conversion funnel optimization

### File 6: Appointments Attendance Report (REQUIRED)

**Purpose:** Booking pipeline and attendance tracking

**Momence Path:**
1. Reports → "Appointments attendance report"
2. Select **ALL practitioners**
3. Select date range: Last 365 days (recommended)
4. Click "Download" to get combined CSV

**Filename:** `momence-appointments-attendance-report-combined.csv`

**What it contains:**
- Customer appointment history
- Upcoming appointments (booking pipeline)
- Payment status (paid vs unpaid)
- VSP assignments
- Appointment frequency per client

**Used for:**
- Booking pipeline visibility
- Revenue forecasting
- Top client identification
- VIP client recognition
- Unpaid reservation tracking
- VSP workload analysis

### File 7: Membership Renewals (OPTIONAL)

**Purpose:** Tracks upcoming membership renewals

**Momence Path:**
1. Reports → "Membership renewals report"
2. Select date range for upcoming renewals
3. Click "Download Summary"

**Filename:** `momence-membership-renewals-report.csv`

**What it contains:**
- Customer information
- Current membership type
- Renewal date
- Renewal amount
- Auto-renew status

**Used for:**
- Renewal planning
- Revenue forecasting
- Proactive customer outreach
- Retention campaigns
- Cash flow projections

**Benefits when included:**
- Shows upcoming revenue
- Identifies renewal opportunities
- Helps plan retention efforts
- Improves financial forecasting

### File 8: Frozen Memberships (OPTIONAL)

**Purpose:** Tracks paused/frozen memberships

**Momence Path:**
1. Reports → "Frozen memberships report"
2. Click "Download Summary"

**Filename:** `frozen-memberships-report.csv`

**What it contains:**
- Customer information
- Membership type frozen
- Freeze start date
- Expected unfreeze date
- Reason for freeze (if provided)

**Used for:**
- Tracking paused revenue
- Identifying at-risk members
- Reactivation campaigns
- Understanding seasonal patterns
- MRR adjustments

**Benefits when included:**
- Better MRR accuracy
- Win-back campaign targeting
- Understanding member lifecycle
- Seasonal trend analysis

### Data File Summary Table

| # | File Name | Type | Status | Purpose |
|---|-----------|------|--------|---------|
| 1 | momence--membership-sales-export.csv | CSV | Required | Membership sales & MRR |
| 2 | momence--membership-sales-export__1_.csv | CSV | Required | Cancellations & churn |
| 3 | momence-new-leads-and-customers.csv | CSV | Required | Lead generation |
| 4 | momence-payroll-report-summary.zip | ZIP | Required | Labor, appointments, commissions |
| 5 | momence-leads-converted-report.csv | CSV | Required | Conversion tracking & LTV |
| 6 | momence-appointments-attendance-report-combined.csv | CSV | Required | Booking pipeline |
| 7 | momence-membership-renewals-report.csv | CSV | Optional | Upcoming renewals |
| 8 | frozen-memberships-report.csv | CSV | Optional | Frozen memberships |

---

## Momence Configuration

Before exporting data, ensure your Momence account is properly configured:

### Pay Rates Configuration

**Location:** Studio Set-up → Pay Rates

**Steps:**
1. Create pay rate structures for each VSP level:
   - Level 1 Practitioner
   - Level 2 Practitioner
   - Lead Practitioner
   - Studio Manager
   - Any other tiers

2. Set rates for different work types:
   - **Table Time**: Per-session or hourly rate for appointments
   - **Studio Lead**: Hourly rate for lead duties
   - **Training**: Rate for training sessions
   - **Administrative**: Rate for non-appointment work

3. Configure service-specific rates:
   - Introductory stretch sessions
   - Regular stretch sessions
   - Special events or workshops
   - Package deals

**Best Practices:**
- Keep rate structures consistent across locations
- Document rate changes with effective dates
- Review rates quarterly
- Ensure rates align with profitability goals

### Practitioner Setup

**Location:** Studio Set-up → Practitioners

**Required Information:**
- Full name (First and Last)
- Contact information (email, phone)
- Role/Level assignment
- Active status
- Location assignment (for multi-location)
- Start date

**Best Practices:**
- Use consistent naming (avoid nicknames)
- Keep contact info updated
- Assign correct role/level for accurate pay rates
- Mark inactive practitioners properly
- Document certifications and training levels

### Appointment Board Configuration

**Location:** Appointments → Boards

**Configure:**
1. Default pay rates per service type
2. VSP assignments to specific services
3. Booking rules and restrictions
4. Session durations
5. Buffer times between appointments

**Important:**
- Verify pay rates are applied correctly
- Test different service types
- Check that special rates (intros, events) are configured
- Ensure time slots align with actual service durations

### Time Clock Setup

**Location:** Studio Set-up → Settings → Time Clock

**Enable:**
- Time clock functionality for all practitioners
- Automatic clock-out reminders
- Break time tracking (if applicable)
- Location-based clock in/out (for multi-location)

**Best Practices:**
- Train all VSPs on time clock usage
- Set up mobile time clock access
- Establish clock-in/out policies
- Review time entries regularly
- Correct any errors promptly

### Commission Tracking

**Location:** Studio Set-up → Commissions

**Configure:**
- Membership sales commissions
- Product sales commissions
- Commission tiers (if applicable)
- Spiff programs or bonuses

**Important:**
- Clearly communicate commission structure
- Track commission payments separately
- Review commission reports monthly
- Adjust structure based on performance

---

## Dashboard Features

### Core Capabilities

#### 1. Data Upload & Processing
- **Drag & Drop**: Simply drag files onto upload area
- **Multi-File**: Upload all files at once or one at a time
- **Auto-Detection**: Dashboard recognizes file types automatically
- **ZIP Support**: Automatically extracts and processes ZIP files
- **Progress Indicators**: Green checkmarks show successful uploads
- **Error Handling**: Clear messages if files are incorrect

#### 2. Date Filtering
- **Flexible Ranges**: Select any date range for analysis
- **Quick Selects**: Last 7 days, 30 days, 90 days, year-to-date
- **Custom Ranges**: Pick exact start and end dates
- **Future Filtering**: Automatically excludes future dates from analysis
- **Period Comparisons**: Compare current vs previous periods

#### 3. Location Filtering (Multi-Location Support)
- **All Locations**: View consolidated data
- **Single Location**: Filter to specific studio
- **Location Comparison**: Compare performance across locations
- **Location-Specific**: Heatmaps and metrics by location

#### 4. Practitioner Filtering
- **All VSPs**: View team-wide data
- **Individual VSP**: Focus on specific practitioner
- **VSP Comparison**: Compare performance metrics
- **Role Filtering**: Filter by VSP level/role

#### 5. Goal Tracking
- **Monthly Goals**: Set targets for revenue, appointments, intros
- **Visual Progress**: Progress bars show goal achievement
- **Period Comparisons**: Track improvement over time
- **Goal Alerts**: Highlights when exceeding or falling short

#### 6. Export Capabilities
- **CSV Exports**: Export any table or segment
- **Client Lists**: Downloadable contact lists for campaigns
- **Segment Exports**: VIP, At-Risk, New Clients, etc.
- **Custom Exports**: Export filtered data views

---

## VSP Performance Analytics

### Overview

The VSP Performance Analytics section is prominently displayed at the top of the VSP tab, providing critical insights into practitioner performance across two key dimensions: conversion rates and utilization rates.

### Location & Access

**Tab:** VSP Performance (Tab 3)
**Position:** Top of tab, immediately after the alert box
**Visibility:** Always visible when VSP tab is active

### Components

#### 1. Conversion Rates Table

**Purpose:** Measures how effectively each VSP converts introductory stretch clients into paying members

**Table Structure:**
- **Rows**: Each VSP (alphabetically sorted)
- **Columns**: One column per month, plus Total column
- **Grand Total Row**: Overall conversion performance

**Calculation:**
```
Conversion Rate = (Conversions / Intro Stretches) × 100
```

**Data Points:**
- **Intro Stretches**: Number of first-time clients
- **Conversions**: Number who became paying members
- **Rate**: Percentage conversion

**Color Coding:**
- 🔵 **Blue** (Excellent): 50%+ conversion rate
- 🟠 **Orange** (Good): 30-49% conversion rate
- 🟣 **Purple** (Needs Improvement): <30% conversion rate

**Tooltips:**
Hover over any cell to see:
```
Conversions: 12 / Intro Stretches: 25 = 48%
```

**How to Use:**
1. Identify top converters (blue cells) for best practices
2. Coach VSPs with purple cells on sales techniques
3. Track improvement month-over-month
4. Set conversion rate goals per VSP
5. Recognize and reward top performers

**Business Insights:**
- **High Conversion (50%+)**: VSP is excellent at building rapport and demonstrating value
- **Medium Conversion (30-49%)**: Good performance, room for improvement in sales technique
- **Low Conversion (<30%)**: May need coaching on customer experience, sales process, or service quality

#### 2. Utilization Rates Table

**Purpose:** Measures how efficiently VSPs use their clocked time for client appointments (table time efficiency)

**Table Structure:**
- **Rows**: Each VSP (alphabetically sorted)
- **Columns**: One column per month, plus Total column
- **Grand Total Row**: Overall utilization performance

**Calculation:**
```
Utilization Rate = (Appointment Hours / Clocked Hours) × 100
```

**Data Points:**
- **Appointment Hours**: Time spent with clients (table time)
- **Clocked Hours**: Total time clocked in
- **Rate**: Percentage utilization

**Color Coding:**
- 🔵 **Blue** (Excellent): 60%+ utilization
- 🟠 **Orange** (Good): 40-59% utilization
- 🟣 **Purple** (Needs Improvement): <40% utilization

**Tooltips:**
Hover over any cell to see:
```
Appt: 32.5h / Clocked: 68.0h = 48%
```

**How to Use:**
1. Identify scheduling inefficiencies (purple cells)
2. Optimize appointment booking patterns
3. Reduce gaps between appointments
4. Track utilization trends over time
5. Set utilization targets per VSP

**Business Insights:**
- **High Utilization (60%+)**: Excellent scheduling, minimal downtime
- **Medium Utilization (40-59%)**: Good efficiency, opportunities to fill gaps
- **Low Utilization (<40%)**: Significant scheduling gaps, lost revenue opportunity

**Benchmark Utilization Rates:**
- **60-70%**: Optimal for client-facing service businesses
- **40-60%**: Acceptable, room for improvement
- **<40%**: Indicates scheduling problems or overstaffing

#### 3. Performance Analytics Header

**Visual Design:**
- Gradient background (accent to primary colors)
- Large, clear heading: "📊 VSP Performance Analytics"
- Subtitle: "Conversion Rates & Utilization Metrics by Month"
- Professional, easy-to-read layout

#### 4. Explanatory Legends

**Conversion Rates Legend:**
```
Note: Conversion rate calculated as: (customers with first 
appointment who became members) / (total customers with first 
appointments).

This measures how effectively each VSP converts new customers 
into paying members.

• Excellent: 50%+ (Blue shading)
• Good: 30-49% (Orange shading)
• Needs Improvement: Below 30% (Purple shading)
```

**Utilization Rates Legend:**
```
Note: Utilization rate measures the percentage of clocked-in 
time spent with clients (table time). Higher rates indicate 
better efficiency.

• Excellent: 60%+ (Blue shading)
• Good: 40-59% (Orange shading)
• Needs Improvement: Below 40% (Purple shading)
```

### Colorblind-Friendly Design

**Color Scheme: Blue-Orange-Purple**

**Design Rationale:**
The dashboard uses a carefully selected color scheme that provides maximum visual distinction for all users, including those with colorblindness.

**Color Specifications:**

1. **Blue (Excellent)**
   - RGB: `rgba(0, 102, 204, 0.3)`
   - Hex: `#0066CC` at 30% opacity
   - Cool, professional tone
   - Clearly indicates "achievement"

2. **Orange (Good)**
   - RGB: `rgba(255, 140, 0, 0.3)`
   - Hex: `#FF8C00` at 30% opacity
   - Warm, attention-grabbing tone
   - Indicates "watch/improve"

3. **Purple (Needs Improvement)**
   - RGB: `rgba(139, 0, 139, 0.3)`
   - Hex: `#8B008B` at 30% opacity
   - Bold, distinct tone
   - Indicates "action required"

**Accessibility Benefits:**
- ✅ Works for Protanopia (red-blind)
- ✅ Works for Deuteranopia (green-blind)
- ✅ Works for Tritanopia (blue-blind)
- ✅ Works for Achromatopsia (total colorblindness)
- ✅ High contrast for low vision users

**Why This Scheme:**
- **Maximum Distinction**: Colors are as far apart as possible in color space
- **Perceptually Uniform**: Maintains distinction in different lighting
- **Universal Design**: Accessible to all users
- **Professional**: Appropriate for business context

### Data Processing & Filtering

**Automatic Future Date Filtering:**
The dashboard automatically excludes appointments and time tracking data from future dates to ensure accurate historical analysis.

**Month Aggregation:**
Data is grouped by month for clear trend analysis and comparison.

**VSP Name Matching:**
The system intelligently matches VSP names across different data sources (appointments, time tracking, memberships) even with slight variations in formatting.

**Edge Cases Handled:**
- Missing data (shows "-" in cells)
- Zero values (handled gracefully)
- Incomplete months (calculated on available data)
- Name variations (fuzzy matching)

### Using Analytics for Business Decisions

#### Scenario 1: Low Conversion Rate

**Symptoms:**
- VSP consistently shows purple cells in conversion table
- Conversion rate below 30%

**Root Cause Analysis:**
1. Review VSP's intro appointment approach
2. Check customer feedback and satisfaction scores
3. Assess VSP's product knowledge and sales training
4. Evaluate intro appointment follow-up process

**Action Steps:**
1. Provide sales and customer experience training
2. Shadow high-converting VSPs
3. Review intro appointment script and process
4. Set specific conversion improvement goals
5. Track progress weekly

#### Scenario 2: Low Utilization Rate

**Symptoms:**
- VSP consistently shows purple cells in utilization table
- Utilization rate below 40%

**Root Cause Analysis:**
1. Review VSP's schedule and appointment gaps
2. Check booking patterns and availability
3. Assess demand at VSP's typical working hours
4. Evaluate scheduling practices

**Action Steps:**
1. Optimize appointment booking patterns
2. Reduce gaps between appointments
3. Offer fill-in appointments or promotions
4. Adjust VSP's working hours to match demand
5. Consider cross-training for multiple services

#### Scenario 3: Identifying Training Opportunities

**Use Analytics To:**
1. Compare new vs experienced VSP performance
2. Identify best practices from top performers
3. Create training programs based on data
4. Set realistic improvement targets
5. Track training effectiveness

### Monthly Performance Review Process

**Step 1: Review Overall Trends (5 minutes)**
- Look at Grand Total rows
- Identify overall business trends
- Note any seasonal patterns

**Step 2: Identify Top Performers (5 minutes)**
- Sort by Total column
- Recognize blue (excellent) performers
- Document best practices

**Step 3: Identify Improvement Opportunities (10 minutes)**
- Find purple (needs improvement) cells
- Identify patterns (consistent vs one-time issues)
- Prioritize coaching opportunities

**Step 4: One-on-One Conversations (15 minutes per VSP)**
- Review individual performance
- Discuss specific months/metrics
- Set improvement goals
- Provide actionable feedback
- Schedule follow-up

**Step 5: Team Meeting (30 minutes)**
- Share aggregate results (anonymously)
- Celebrate team wins
- Discuss improvement strategies
- Set team goals for next month

---

## Tab-by-Tab Guide

### Tab 1: Overview

**Purpose:** High-level business snapshot and financial performance

**Key Metrics Displayed:**
- Total Revenue (current period)
- Paid Appointments count
- Intro Appointments count
- Active Members
- MRR (Monthly Recurring Revenue)
- Average Ticket

**Financial Performance Section:**
- Revenue breakdown (appointments + memberships)
- Labor costs (appointment pay + non-appointment hours)
- Gross profit (revenue - labor)
- Net profit (after franchise fees, brand fund, CC fees)
- Profit margins

**Goal Tracking:**
- Revenue goal progress bar
- Paid appointments goal progress
- Intro appointments goal progress
- Visual indicators (on track / behind / exceeded)

**Period Comparison:**
- Compare to previous period
- % change indicators
- Trend arrows (up/down)

**What to Look For:**
- Are you meeting your goals?
- Is profit margin healthy (target: 30-40%)?
- Are labor costs under control (target: <50% of revenue)?
- Is MRR growing month-over-month?

### Tab 2: Timeline

**Purpose:** Visualize trends over time

**Charts Included:**

1. **Revenue Over Time**
   - Line chart showing daily/monthly revenue
   - Helps identify trends and patterns
   - Spot seasonal variations

2. **Appointments Over Time**
   - Tracks appointment volume
   - Separates paid vs intro appointments
   - Identifies busy periods

3. **MRR Growth**
   - Monthly recurring revenue trend
   - Shows membership business health
   - Projects future revenue

4. **Customer Acquisition**
   - New customers over time
   - Lead generation effectiveness
   - Growth trajectory

**Interactive Features:**
- Hover for exact values
- Click legend to hide/show series
- Zoom into specific time periods

**What to Look For:**
- Consistent upward trends
- Seasonal patterns to anticipate
- Sudden drops requiring investigation
- Correlation between marketing and results

### Tab 3: VSP Performance

**Purpose:** Individual practitioner analysis and performance tracking

**Main Sections:**

1. **Alert Info Box** - Introduction to VSP metrics

2. **📊 VSP Performance Analytics** (TOP SECTION - NEW!)
   - Conversion Rates Table
   - Utilization Rates Table
   - See [VSP Performance Analytics](#vsp-performance-analytics) section for details

3. **Performance Metrics Grid**
   - Top Performer (by score)
   - Highest Revenue generator
   - Best Efficiency ($/hour)
   - Most Clients served
   - Average Utilization
   - Total Commissions

4. **Revenue & Appointments Charts**
   - Revenue by VSP (bar chart)
   - Appointments by VSP (bar chart)
   - Interactive - click VSP for details

5. **Leaderboard Cards**
   - Each VSP with detailed metrics
   - Ranking (🥇🥈🥉 or numeric)
   - Comprehensive performance data:
     - Revenue & appointments
     - Efficiency ($/hour)
     - Client count
     - Utilization rate
     - Commissions
     - Average ticket
     - Profit margin

6. **Detailed Performance Table**
   - Sortable by any column
   - All VSPs with complete metrics
   - Export capability

**Scoring System:**
VSP score calculated from:
- Revenue (40%)
- Efficiency (30%)
- Client satisfaction proxy (20%)
- Consistency (10%)

**What to Look For:**
- Balanced performance across metrics
- VSPs needing coaching
- Top performers to recognize
- Workload distribution issues
- Commission opportunities

### Tab 4: Customers

**Purpose:** Client analysis and segmentation

**Main Sections:**

1. **Customer Overview Metrics**
   - Total customers
   - Active members
   - Average LTV
   - New customers this period
   - Return customer rate

2. **Client Segmentation**
   
   **Five Strategic Segments:**
   
   a. **VIP Clients** (High LTV)
   - Criteria: LTV above VIP threshold
   - Why: Your most valuable customers
   - Action: White-glove service, exclusive offers, retention focus
   - Export: Contact list for VIP program
   
   b. **New Clients** (Recent Join)
   - Criteria: Joined within last 30 days
   - Why: Critical onboarding period
   - Action: Welcome campaigns, intro offers, check-ins
   - Export: Contact list for new client nurture sequence
   
   c. **At-Risk Clients** (Declining Visits)
   - Criteria: Members with declining visit frequency
   - Why: Early warning of potential churn
   - Action: Re-engagement campaigns, special offers, check-in calls
   - Export: Contact list for win-back campaigns
   
   d. **Inactive Paid Members** (Not Visiting)
   - Criteria: Active membership but no recent visits
   - Why: Paying but not using service
   - Action: Urgent re-engagement, schedule assistance
   - Export: Contact list for immediate outreach
   
   e. **High-Frequency Non-Members** (Potential Converts)
   - Criteria: Frequent visitors without membership
   - Why: Prime candidates for membership conversion
   - Action: Membership pitch, cost savings demo
   - Export: Contact list for membership sales campaign

3. **Segment Details**
   - Count of clients in each segment
   - Total LTV per segment
   - Average visit frequency
   - Export buttons for contact lists

4. **Visit Pattern Analysis**
   - Visit frequency distribution
   - Peak visit times
   - Appointment preferences

**How to Use:**
1. Review segment sizes monthly
2. Export contacts for targeted campaigns
3. Track segment movement (e.g., At-Risk → Active)
4. Set goals for segment optimization
5. Measure campaign effectiveness

### Tab 5: Retention

**Purpose:** Churn analysis and cohort retention tracking

**Main Sections:**

1. **Churn Overview**
   - Current churn rate
   - Members lost this period
   - Lost MRR
   - Churn trend over time

2. **Cohort Retention Analysis**
   - Monthly cohorts (members by join month)
   - Retention rate over time
   - Heatmap visualization
   - Identify retention patterns

3. **Churn by Segment**
   - Churn rate by membership type
   - Churn rate by location
   - Churn rate by VSP
   - Identify problem areas

4. **Win-Back Opportunities**
   - Recently canceled members
   - Reason for cancellation
   - Potential to win back
   - Suggested outreach

**Key Metrics Explained:**

**Churn Rate:**
```
Churn Rate = (Cancellations / Active Members) × 100
```
Target: <5% monthly churn

**Retention Rate:**
```
Retention Rate = 100% - Churn Rate
```
Target: >95% monthly retention

**What to Look For:**
- Increasing churn rates
- Specific segments with high churn
- Patterns in cancellation reasons
- Cohorts with poor retention
- Win-back opportunities

### Tab 6: Journey

**Purpose:** Customer lifecycle and conversion funnel analysis

**Funnel Stages:**

1. **Lead Generation**
   - Total leads captured
   - Lead sources
   - Source effectiveness

2. **Lead Conversion**
   - Leads → Customers conversion rate
   - Time to first appointment
   - Conversion by source

3. **Intro Experience**
   - Intro appointments completed
   - Intro → Paid conversion rate
   - VSP performance on intros

4. **Membership Conversion**
   - Customers → Members conversion rate
   - Time to membership purchase
   - Membership type distribution

5. **Retention & Growth**
   - Member retention rate
   - Upgrades/downgrades
   - Average member lifetime

**Visualizations:**
- Funnel chart showing drop-offs
- Conversion rates at each stage
- Time-to-convert metrics
- Source performance comparison

**What to Look For:**
- Where are leads dropping off?
- Which sources convert best?
- How long does conversion take?
- Are intros converting to paid?
- Are paid customers becoming members?

**Optimization Opportunities:**
- Improve lowest-converting stage
- Reduce time-to-conversion
- Focus on best-performing sources
- Train VSPs on weak conversion points

### Tab 7: Memberships

**Purpose:** Subscription business health and growth

**Main Sections:**

1. **Membership Overview**
   - Total active memberships
   - MRR (Monthly Recurring Revenue)
   - Average membership value
   - Membership growth rate

2. **Membership Types**
   - Distribution by type
   - Revenue by type
   - Churn by type
   - Profitability by type

3. **Membership Trends**
   - New memberships over time
   - Cancellations over time
   - Net membership growth
   - MRR growth trend

4. **Membership Heatmap** (when data available)
   - Busiest membership sale times
   - Day and hour breakdown
   - Identify peak conversion times
   - Optimize staffing for sales

5. **Renewal Tracking** (when renewals data uploaded)
   - Upcoming renewals count
   - Renewal revenue forecast
   - Auto-renew vs manual
   - At-risk renewals

6. **Frozen Memberships** (when frozen data uploaded)
   - Count of frozen memberships
   - Frozen MRR (paused revenue)
   - Average freeze duration
   - Reactivation opportunities

**Key Metrics:**

**MRR Growth Rate:**
```
MRR Growth = ((Current MRR - Previous MRR) / Previous MRR) × 100
```
Target: 5-10% monthly MRR growth

**Membership Penetration:**
```
Penetration = (Active Members / Total Customers) × 100
```
Target: 40-60% of customers should be members

**What to Look For:**
- Consistent MRR growth
- Balanced membership types
- Low churn on memberships
- High renewal rates
- Reactivation opportunities for frozen memberships

### Tab 8: Cancellations

**Purpose:** Understand why customers cancel and how to prevent it

**Main Sections:**

1. **Cancellation Overview**
   - Total cancellations this period
   - Cancellation rate
   - Lost MRR
   - Lost LTV

2. **Cancellation Reasons**
   - Breakdown by stated reason
   - Most common reasons
   - Addressable vs non-addressable
   - Trends over time

3. **Cancellation by Segment**
   - By membership type
   - By location
   - By VSP (if patterns exist)
   - By customer tenure

4. **Financial Impact**
   - Monthly MRR lost
   - Annual revenue impact
   - Customer lifetime value lost
   - Win-back potential

5. **Cancellation Timeline**
   - Cancellations over time
   - Seasonal patterns
   - Event correlation
   - Predict future churn

**Common Cancellation Reasons:**
- **Price/Cost**: Too expensive, financial hardship
- **Moving/Relocation**: Customer moved away
- **Time/Schedule**: Can't fit into schedule
- **Results**: Not seeing desired results
- **Service**: Dissatisfied with service
- **Other Commitment**: Found alternative solution

**What to Look For:**
- Addressable reasons (price, results, service, schedule)
- Patterns in timing (seasonality, after X months)
- Specific locations or VSPs with high churn
- Win-back opportunities

**Action Items by Reason:**

**Price/Cost:**
- Offer payment plans
- Introduce lower-tier options
- Highlight value and ROI
- Create loyalty discounts

**Results:**
- Improve expectation setting
- Enhance VSP training
- Add progress tracking
- Offer complementary services

**Schedule:**
- Expand hours
- Offer flexible booking
- Add online scheduling
- Create standing appointments

**Service:**
- Gather detailed feedback
- VSP coaching and training
- Quality assurance program
- Customer satisfaction surveys

### Tab 9: Leads

**Purpose:** Lead generation and conversion analysis

**Appears when:** Leads Converted Report is uploaded

**Main Sections:**

1. **Lead Overview**
   - Total leads generated
   - Conversion rate
   - Average time to conversion
   - Average LTV of converted leads

2. **Lead Sources**
   - Performance by source
   - Conversion rate by source
   - LTV by source
   - ROI by source (if cost data available)

3. **Lead Timeline**
   - Leads generated over time
   - Conversions over time
   - Time-to-convert trends
   - Seasonal patterns

4. **Conversion Funnel**
   - Lead → Customer → Member journey
   - Drop-off points
   - Optimization opportunities

5. **Source Performance Comparison**
   - Table with all sources
   - Metrics: Leads, Conversions, Rate, LTV
   - Sortable columns
   - Export capability

**Key Metrics:**

**Lead Conversion Rate:**
```
Conversion Rate = (Converted Leads / Total Leads) × 100
```
Target: 30-50% lead conversion rate

**Source ROI:**
```
ROI = (LTV of Converted Leads - Marketing Cost) / Marketing Cost × 100
```

**What to Look For:**
- Best-performing sources
- Sources with high LTV
- Sources with fast conversion
- Underperforming sources to optimize or eliminate
- Opportunities to scale winning sources

### Tab 10: Schedule

**Purpose:** Scheduling optimization and capacity analysis

**Main Sections:**

1. **Schedule Overview Metrics**
   - Overall utilization rate
   - Total scheduling gaps
   - Potential revenue from gaps
   - VSP efficiency scores

2. **Appointment Heatmap by Location**
   - Separate heatmap for each location
   - Shows appointment density by:
     - Day of week (Monday-Saturday)
     - Hour of day (6am-9pm)
   - Color intensity = number of appointments
   - Interactive: Click day or hour for breakdown

3. **Schedule Optimization Insights**
   - Recommendations for filling gaps
   - Busiest times to staff appropriately
   - Slowest times to optimize
   - Revenue opportunity from better scheduling

4. **Top 20 Days with Largest Gaps**
   - Table showing worst scheduling days
   - Columns: Practitioner, Date, Appointments, Gaps, Gap Time, Utilization, Opportunity
   - Identifies specific days to improve
   - Calculates lost revenue per gap

**Using the Heatmap:**

**Click a Day Name:**
- Shows hourly breakdown for that day across all weeks
- Identifies consistent patterns
- Example: Every Monday slow at 2pm

**Click an Hour Cell:**
- Shows specific appointments for that time slot
- Lists customers, VSPs, services
- Helps understand booking patterns

**Color Legend:**
- Light: Few appointments
- Medium: Moderate booking
- Dark: Very busy / fully booked

**What to Look For:**
- Consistent slow periods (opportunities)
- Overbooked times (capacity constraints)
- Day-of-week patterns
- Hour-of-day patterns
- Location-specific differences

**Optimization Strategies:**

**For Slow Periods:**
- Offer discounted fill-in appointments
- Run promotions for off-peak times
- Adjust VSP schedules to match demand
- Cross-train for other services

**For Busy Periods:**
- Ensure adequate staffing
- Minimize cancellations/no-shows
- Optimize appointment duration
- Consider expanding capacity

**For Gaps:**
- Block schedule appointments closer
- Reduce buffer times
- Offer express services for small gaps
- Review practitioner availability patterns

### Tab 11: Insights

**Purpose:** Booking pipeline visibility and attendance analytics

**Appears when:** Attendance Report is uploaded

**Main Sections:**

1. **Booking Pipeline Overview**
   - Total upcoming appointments
   - Revenue forecast from pipeline
   - Paid vs unpaid reservations
   - Pipeline strength indicator

2. **Top 10 Most Frequent Clients**
   - Ranked by visit count
   - Customer name and visit frequency
   - Identifies VIP clients
   - Excellent retention targets

3. **Top VSPs by Appointments Booked**
   - Ranked by appointment count
   - Shows booking popularity
   - Helps with scheduling decisions
   - Identifies high-demand practitioners

4. **Paid vs Unpaid Reservations**
   - Breakdown of payment status
   - Unpaid reservation value
   - Follow-up opportunities
   - Cash flow implications

**Key Metrics:**

**Pipeline Strength:**
```
Strong: 2+ weeks of appointments booked
Medium: 1-2 weeks of appointments
Weak: <1 week of appointments
```

**What to Look For:**
- Strong pipeline (indicates demand)
- Unpaid reservations requiring follow-up
- VIP clients to recognize and reward
- Popular VSPs (capacity planning)

**Action Items:**

**Strong Pipeline:**
- Maintain marketing efforts
- Ensure capacity for demand
- Prepare for growth

**Weak Pipeline:**
- Increase marketing
- Reach out to past clients
- Run booking promotions
- Check for operational issues

**Unpaid Reservations:**
- Send payment reminders
- Offer easy payment options
- Follow up before appointment
- Reduce cancellation risk

---

## Settings & Configuration

### Accessing Settings

**Method 1:** Click the ⚙️ Settings button in top navigation bar
**Method 2:** Keyboard shortcut (if implemented): `Ctrl+,` or `Cmd+,`

### Settings Sections

#### 1. Business Configuration

**Timezone Selection**
- Dropdown with all world timezones
- Ensures correct date/time calculations
- Affects: Appointment times, heatmaps, analytics
- Default: Browser timezone

**Franchise Fee (%)**
- Percentage paid to franchisor
- Default: 6%
- Affects: Net profit calculations
- Range: 0-100%

**Brand Fund (%)**
- Percentage contributed to brand marketing
- Default: 2%
- Affects: Net profit calculations
- Range: 0-100%

**Credit Card Processing Fees (%)**
- Percentage paid for card processing
- Default: 3%
- Affects: Net profit calculations
- Range: 0-100%

#### 2. Monthly Goals

**Revenue Goal**
- Target monthly revenue
- Default: $20,000
- Used for: Goal tracking, progress bars
- Recommended: Set based on historical data + 10-20% growth

**Paid Appointments Goal**
- Target number of paid appointments per month
- Default: 300
- Excludes intro appointments
- Recommended: Based on capacity and VSP count

**Intro Appointments Goal**
- Target number of introductory appointments
- Default: 50
- Critical for lead generation
- Recommended: 10-20% of paid appointments

#### 3. Labor Configuration

**Base Hourly Rate**
- Rate paid for non-appointment work
- Default: $13.00
- Used for: Non-appointment labor cost calculations
- Examples: Studio lead time, training, administrative

#### 4. LTV (Lifetime Value) Tiers

**Purpose:** Defines VIP thresholds for client segmentation

**Tier Options:**
- **Conservative**: $500 minimum for VIP status
- **Moderate**: $1,000 minimum for VIP status
- **Aggressive**: $1,500 minimum for VIP status

**Affects:**
- VIP client segmentation
- Client tier classifications
- Recognition programs

**How to Choose:**
- Review average customer LTV
- Set VIP threshold at top 10-20% of customers
- Adjust based on business goals

#### 5. Date Filtering

**Not Before Date**
- Filter out data before specific date
- Useful for: New ownership, system changes, data quality
- Optional: Leave blank to include all data

**Future Date Filtering**
- Automatically enabled
- Excludes appointments and data after today
- Ensures historical accuracy
- Exception: Membership renewals (future dates are relevant)

### Saving Settings

**Process:**
1. Adjust settings as desired
2. Click "Save Settings" button
3. Settings saved to browser's local storage
4. Page may reload to apply changes

**Persistence:**
- Settings persist across sessions
- Stored locally (private, secure)
- Not shared across devices or browsers
- Export settings (if needed) - feature can be added

### Resetting Settings

**Method 1:** Clear browser cache and reload
**Method 2:** Delete local storage manually (developer tools)
**Method 3:** Re-enter default values manually

**Default Values:**
```javascript
{
  timezone: 'America/New_York',
  franchiseFee: 6,
  brandFund: 2,
  creditCardFees: 3,
  revenueGoal: 20000,
  paidAppointmentsGoal: 300,
  introAppointmentsGoal: 50,
  baseHourlyRate: 13.00,
  ltvTiers: 'moderate',
  notBeforeDate: null
}
```

---

## Advanced Features

### 1. Interactive Charts

**Chart Library:** Chart.js

**Available Interactions:**
- **Hover**: See exact values
- **Click Legend**: Hide/show data series
- **Click Data Points**: Drill into details (where implemented)

**Chart Types:**
- Line charts: Trends over time
- Bar charts: Comparisons
- Doughnut charts: Composition
- Heatmaps: Density visualization

### 2. Data Export Capabilities

**What Can Be Exported:**
- Any table in the dashboard
- Client segment contact lists
- Filtered data views
- Custom report data

**Export Format:** CSV (Comma-Separated Values)

**Export Process:**
1. Navigate to desired data
2. Apply any filters
3. Click "Export" or "Download" button
4. CSV file downloads automatically

**Using Exported Data:**
- Import into Excel/Google Sheets
- Use for email marketing (MailChimp, Constant Contact)
- Create custom reports
- Share with team or franchisor

### 3. Client Segment Exports

**Purpose:** Download contact lists for targeted campaigns

**Segments Available:**
- VIP Clients
- New Clients
- At-Risk Clients
- Inactive Paid Members
- High-Frequency Non-Members

**Export Contains:**
- Customer Name
- Email Address
- Phone Number
- Segment-specific data (LTV, visit count, etc.)

**Use Cases:**

**VIP Clients Export:**
- Create VIP program
- Send exclusive offers
- Personal outreach campaigns
- Loyalty rewards

**At-Risk Clients Export:**
- Win-back campaigns
- Special re-engagement offers
- Personal check-in calls
- Satisfaction surveys

**Inactive Paid Members Export:**
- Urgent retention campaigns
- Scheduling assistance
- Service recovery
- Membership optimization

### 4. Period Comparisons

**Comparison Types:**
- **Previous Period**: Compare to last month, last week, etc.
- **Year-over-Year**: Compare to same period last year
- **Custom**: Compare any two date ranges

**Metrics Compared:**
- Revenue
- Appointments
- MRR
- Customers
- Any other key metrics

**Visual Indicators:**
- ▲ Green arrow: Increase
- ▼ Red arrow: Decrease
- Percentage change
- Actual value change

### 5. Location-Specific Analysis

**Available when:** Multiple locations exist in data

**Features:**
- Filter entire dashboard to single location
- Compare locations side-by-side
- Location-specific heatmaps
- Location-based goals (future enhancement)

**Use Cases:**
- Multi-location franchisees
- Benchmarking performance
- Identifying best practices
- Allocating resources

### 6. VSP-Specific Filtering

**Purpose:** Focus on individual practitioner performance

**Filter Options:**
- Single VSP selection
- Multiple VSP selection
- VSP role/level filtering

**Affects:**
- All dashboard metrics
- Charts and visualizations
- Export data

**Use Cases:**
- Individual performance reviews
- VSP coaching sessions
- Workload analysis
- Commission calculations

### 7. Customizable Goals

**Goal Types:**
- Revenue goals
- Appointment volume goals
- Intro appointment goals
- Custom metric goals (future)

**Goal Features:**
- Monthly targets
- Visual progress tracking
- Goal vs actual comparison
- Historical goal tracking

**Setting Effective Goals:**
- Use historical data as baseline
- Add 10-20% for growth targets
- Review and adjust quarterly
- Celebrate goal achievement

### 8. Real-Time Calculations

**All metrics calculated in real-time:**
- No pre-processing required
- Instant updates with filter changes
- Dynamic aggregations
- Fresh insights always

**Performance:**
- Handles 365+ days of data
- Processes thousands of records
- Minimal lag on modern browsers
- Optimized calculations

---

## Technical Specifications

### Browser Requirements

**Minimum Versions:**
- Google Chrome 90+
- Mozilla Firefox 88+
- Apple Safari 14+
- Microsoft Edge 90+
- Brave Browser (any recent version)
- Opera 76+

**Required Browser Features:**
- JavaScript enabled
- Local Storage enabled
- CSV file handling
- Modern CSS3 support
- ES6 JavaScript support

**Not Supported:**
- Internet Explorer (any version)
- Very old browsers (pre-2020)

### File Size Limits

**Practical Limits:**
- CSV files: Up to 50 MB
- ZIP files: Up to 100 MB
- Total data: Up to 365 days typical

**Performance Considerations:**
- Larger files take longer to process
- Browser may show "page unresponsive" briefly
- Allow processing to complete
- Modern computers handle typical franchise data easily

### Data Processing

**Client-Side Only:**
- All processing in browser
- Zero server communication
- Complete privacy
- Instant processing

**Processing Steps:**
1. File upload
2. File validation
3. CSV parsing
4. Data normalization
5. Calculations
6. Visualization rendering

**Average Processing Time:**
- Small dataset (1-3 months): <5 seconds
- Medium dataset (3-6 months): 5-15 seconds
- Large dataset (6-12 months): 15-30 seconds
- Extra large (12+ months): 30-60 seconds

### Storage Requirements

**Disk Space:**
- Dashboard HTML file: ~2 MB
- Data files: Variable (typically 5-50 MB per export)
- Browser cache: ~10 MB
- Total: ~20-100 MB typical

**Browser Storage:**
- Settings: <1 KB
- No data stored in browser
- Files must be re-uploaded each session

### Security & Privacy

**Data Security:**
- ✅ No server transmission
- ✅ No external API calls
- ✅ No data collection
- ✅ No tracking or analytics
- ✅ All processing local
- ✅ No user accounts or login

**Privacy Guarantees:**
- Your data never leaves your computer
- No telemetry or usage tracking
- No cookies (except essential browser storage for settings)
- No third-party services
- No data retention (reload = fresh start)

**Best Practices:**
- Use secure computer
- Don't share dashboard file with data
- Clear browser cache if using shared computer
- Keep data files in secure location
- Regular backups of data files

### Performance Optimization

**Optimizations Implemented:**
- Lazy loading of charts
- Debounced filtering
- Memoized calculations
- Efficient data structures
- Minimal DOM manipulations

**Performance Tips:**
- Use modern browser
- Close unnecessary tabs
- Ensure adequate RAM (4GB+ recommended)
- Use smaller date ranges if slow
- Filter data before heavy operations

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Dashboard Shows Old Version

**Symptoms:**
- New features missing
- Old version number in footer
- Recent bug fixes not applied

**Solution:**
1. Force reload page:
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`
2. Clear browser cache completely
3. Re-download dashboard HTML file
4. Verify footer shows `v2.20251113.04`

#### Issue: Files Not Uploading

**Symptoms:**
- Upload button not working
- Files don't show checkmarks
- Error messages

**Troubleshooting:**
1. **Check File Format:**
   - Must be CSV or ZIP files from Momence
   - No modifications to files after export
   - No Excel files (.xlsx) - export as CSV

2. **Check File Name:**
   - Should match expected pattern
   - Don't rename Momence exports
   - Original names work best

3. **Check File Size:**
   - Files should be <50 MB (CSV) or <100 MB (ZIP)
   - Large files may timeout
   - Consider smaller date range

4. **Browser Issues:**
   - Try different browser
   - Disable extensions temporarily
   - Check JavaScript is enabled
   - Check local storage enabled

5. **File Corruption:**
   - Re-export from Momence
   - Ensure complete download
   - Check file opens in text editor

#### Issue: No Data Showing After Upload

**Symptoms:**
- Blank dashboard
- Zero values everywhere
- Charts empty

**Troubleshooting:**
1. **Verify All Required Files:**
   - ✅ Membership Sales
   - ✅ Membership Cancellations
   - ✅ New Leads & Customers
   - ✅ Practitioner Payroll ZIP
   - ✅ Leads Converted Report
   - ✅ Attendance Report
   
2. **Check Date Range:**
   - Selected date range may have no data
   - Expand date range to include data
   - Check "Not Before Date" setting

3. **Check Location Filter:**
   - May be filtered to location with no data
   - Set to "All Locations"

4. **Check Browser Console:**
   - Press F12 to open developer tools
   - Check Console tab for errors
   - Look for red error messages
   - Share error with support if needed

#### Issue: Wrong Data or Calculations

**Symptoms:**
- Numbers don't match expectations
- Metrics seem incorrect
- Discrepancies with Momence

**Troubleshooting:**
1. **Verify Export Settings:**
   - Check date range in exports
   - Ensure all practitioners included
   - Verify location coverage

2. **Check Dashboard Settings:**
   - Review franchise fee %
   - Check base hourly rate
   - Verify goals are reasonable

3. **Understand Calculation Methods:**
   - Dashboard may calculate differently
   - See [Key Metrics Explained](#key-metrics-explained)
   - Some metrics are estimates

4. **Check for Filtering:**
   - Date range may exclude data
   - Location filter may be active
   - VSP filter may be applied

#### Issue: VSP Performance Analytics Missing

**Symptoms:**
- Conversion table not showing
- Utilization table not showing
- Section entirely missing

**Troubleshooting:**
1. **Check Required Files:**
   - Payroll ZIP must include appointments
   - Membership sales file required
   - Time tracking data required (for utilization)

2. **Check Data Validity:**
   - Ensure appointments have VSP names
   - Verify memberships have customer emails
   - Check time tracking has clock in/out data

3. **Check Date Range:**
   - Selected range may have no relevant data
   - Expand to include more months

4. **Browser Console:**
   - Press F12
   - Look for debug messages
   - Check for data processing errors

#### Issue: Conversion Rates Show December/Future Dates

**Symptoms:**
- Analytics show months beyond current month
- December showing when it's November

**Solution:**
- Dashboard automatically filters future dates
- Check browser console (F12) for debug messages
- Verify Momence data doesn't include test appointments
- Contact support if persists

#### Issue: Utilization Rates All Zero

**Symptoms:**
- Utilization table shows 0% or "-" everywhere
- No color coding

**Troubleshooting:**
1. **Check Time Tracking Data:**
   - Payroll ZIP must include time tracking CSV
   - VSPs must be clocking in/out properly
   - Verify time clock is enabled in Momence

2. **Check Field Names:**
   - Dashboard handles "Clocked in" and "Clock in date"
   - Check browser console for debug messages

3. **Verify VSP Name Matching:**
   - Names must match across files
   - Check for typos or variations
   - Look at browser console for name matching logs

#### Issue: Colors Hard to Distinguish

**Symptoms:**
- Can't tell difference between colors
- Performance levels unclear

**Current Scheme:**
- Blue = Excellent
- Orange = Good
- Purple = Needs Improvement

**Solutions:**
- Scheme already optimized for colorblindness
- Use tooltips for exact values
- Rely on numeric percentages
- Contact support for alternative options

#### Issue: Dashboard Slow or Unresponsive

**Symptoms:**
- Page loads slowly
- Interactions lag
- Browser warns "page unresponsive"

**Solutions:**
1. **Reduce Data Size:**
   - Use smaller date ranges
   - Filter to single location
   - Process fewer months at once

2. **Browser Optimization:**
   - Close unnecessary tabs
   - Clear browser cache
   - Restart browser
   - Use faster browser (Chrome recommended)

3. **Computer Resources:**
   - Close other applications
   - Ensure adequate RAM available
   - Check CPU usage

4. **File Size:**
   - Very large files (>50MB) may be slow
   - Consider breaking into smaller date ranges
   - Export from Momence in segments

#### Issue: Exports Not Working

**Symptoms:**
- Export buttons don't work
- CSV doesn't download
- Downloaded file is empty

**Solutions:**
1. **Browser Permissions:**
   - Allow file downloads
   - Check browser download settings
   - Disable download blockers

2. **Check Data:**
   - Ensure table has data to export
   - Apply filters to include data
   - Check if segment is empty

3. **File Location:**
   - Check browser's download folder
   - Look for blocked downloads notification
   - Try different browser

#### Issue: Settings Not Saving

**Symptoms:**
- Settings reset after reload
- Changes don't persist

**Solutions:**
1. **Check Local Storage:**
   - Ensure browser allows local storage
   - Disable private/incognito mode
   - Check browser privacy settings

2. **Browser Compatibility:**
   - Try different browser
   - Update to latest browser version
   - Check for browser extensions interfering

3. **Manual Reset:**
   - Clear all browser data
   - Reload dashboard
   - Re-enter settings

### Getting Additional Help

**Before Contacting Support:**
1. Check this troubleshooting guide
2. Try the suggested solutions
3. Note browser version and OS
4. Screenshot any error messages
5. Note specific steps to reproduce issue

**When Contacting Support:**
Provide:
- Dashboard version number (from footer)
- Browser name and version
- Operating system
- Detailed description of issue
- Steps to reproduce
- Any error messages
- Screenshots if applicable

---

## Version History

### v2.20251113.04 (Current - November 13, 2024)

**Major Features:**
- 📊 **VSP Performance Analytics** - Moved to top of VSP tab
- 📊 **Conversion Rate Tracking** - Intro to member conversion by VSP and month
- ⏱️ **Utilization Rate Tracking** - Table time efficiency by VSP and month
- 🎨 **Colorblind-Friendly Colors** - Blue-Orange-Purple scheme for maximum distinction
- 💡 **Detailed Tooltips** - Hover over any cell for detailed breakdowns
- 🔮 **Future Date Filtering** - Automatic exclusion of future dates from analytics

**Design Improvements:**
- Color-coded performance levels (Blue/Orange/Purple)
- Professional legends explaining thresholds
- Clean, accessible visual design
- Maximum distinction for colorblind users

**Bug Fixes:**
- Fixed future date filtering in VSP analytics
- Improved conversion rate calculations
- Enhanced utilization rate accuracy
- Better handling of edge cases in analytics
- Improved name matching across data sources

### v2.20251105.5 (November 5, 2024)

**Critical Fixes:**
- 🔴 **CRITICAL FIX:** Non-Appt Labor calculation with month/location filtering
- 🔴 Fixed time tracking field name bug ("Clocked in" vs "Clock in date")

**New Features:**
- ✨ Added Attendance Analytics section with booking pipeline tracking
- ✨ Added location-specific appointment heatmaps
- ✨ Added support for Leads Converted report
- ✨ Added support for Attendance Report CSV file
- 📊 Added top 10 most frequent clients analysis
- 📊 Added top VSPs by appointments booked
- 📊 Added paid vs unpaid reservation tracking

**Improvements:**
- 🎨 Reduced comparison text font size to 8px for better visual hierarchy
- 🛠 Fixed template literal bug in Insights recommendations
- 🔧 Added cache-busting meta tags
- 🔧 Added debug console logging for troubleshooting

### v2.20251104.07 (November 4, 2024)

**Fixes:**
- 🔴 Fixed cancellation value calculations (MRR matching)
- 🔴 Fixed paid appointments vs goal tracking
- Improved email-based matching for cancellations
- Separate tracking for paid vs intro appointments

### v2.20251104.06 (November 4, 2024)

**Changes:**
- Changed default revenue goal to $20,000
- Changed default intro goal to 50
- Fixed churn rate by location
- Enhanced customer name extraction

### v2.20251103.05 (November 3, 2024)

**Features:**
- Added franchise configuration settings
- Comprehensive labor cost tracking
- New financial performance section
- Monthly goal visualizations

### v2.20251103.04 (November 3, 2024)

**Features:**
- Added utilization tracking
- Added commission tracking
- Enhanced ZIP file processing
- Improved tab organization

### Earlier Versions

Prior versions focused on:
- Core dashboard functionality
- Basic metrics and visualizations
- Client segmentation
- Export capabilities
- Multi-location support

---

## Best Practices

### Data Management

#### Weekly Data Export Routine

**Recommended Schedule:** Every Monday morning

**Process:**
1. Log into Momence (15 minutes)
2. Export all 6 required files (10 minutes)
3. Save files in organized folder structure:
   ```
   /Vital Stretch Data/
     /2024/
       /November/
         /Week-2024-11-11/
           - membership-sales.csv
           - cancellations.csv
           - leads.csv
           - payroll.zip
           - leads-converted.csv
           - attendance.csv
   ```
4. Upload to dashboard (2 minutes)
5. Review key metrics (10 minutes)
6. Export urgent segments if needed (3 minutes)

**Total Time:** 40 minutes per week

#### File Organization Best Practices

**Folder Structure:**
```
/Analytics/
  /Dashboard Versions/
    - dashboard-v2.20251113.04.html
    - dashboard-v2.20251105.5.html (backup)
  /Data Exports/
    /2024/
      /January/
      /February/
      ...
      /November/
        /Week-2024-11-04/
        /Week-2024-11-11/
        /Week-2024-11-18/
  /Export Campaigns/
    /VIP-Clients/
      - vip-export-2024-11-11.csv
    /At-Risk/
      - at-risk-export-2024-11-11.csv
  /Reports/
    /Monthly Reviews/
```

**Naming Conventions:**
- Include date in YYYY-MM-DD format
- Use descriptive names
- Be consistent
- Avoid special characters

#### Backup Strategy

**What to Backup:**
- Dashboard HTML file (each version)
- All data export files
- Exported segments/reports
- Custom settings (if possible)

**Backup Frequency:**
- Dashboard: After each version update
- Data exports: Immediately after download
- Segments: After export

**Backup Locations:**
- Local drive (primary)
- Cloud storage (Google Drive, Dropbox, OneDrive)
- External hard drive (monthly backup)

### Weekly Analysis Routine

**Time Required:** 15-20 minutes

**Steps:**

**1. Upload Fresh Data (2 minutes)**
- Export latest week from Momence
- Upload to dashboard
- Verify all files loaded (checkmarks)

**2. Review Overview Tab (3 minutes)**
- Check progress toward monthly goals
- Note any concerning trends
- Compare to previous week

**3. Check VSP Performance (5 minutes)**
- Review Performance Analytics tables
- Check conversion rates (any purple cells?)
- Check utilization rates (any purple cells?)
- Note top performers and those needing support

**4. Review Client Segments (3 minutes)**
- Check At-Risk client count
- Review Inactive Paid Members
- Note New Clients count

**5. Export Urgent Segments (2 minutes)**
- Export At-Risk clients if high
- Export Inactive Paid Members
- Save for immediate outreach

**6. Note Action Items (2 minutes)**
- VSPs needing coaching
- Segments requiring campaigns
- Follow-up needed
- Schedule reviews

### Monthly Deep Dive

**Time Required:** 60-90 minutes

**Recommended Schedule:** First week of new month

**Agenda:**

**Week 1: Data Preparation (20 minutes)**
- Export full previous month data
- Upload to dashboard
- Set date range to previous month
- Verify all metrics loaded correctly

**Week 2: Financial Review (30 minutes)**
1. **Revenue Analysis (10 min)**
   - Total revenue vs goal
   - Revenue by source (appointments vs memberships)
   - Revenue by location (if multi-location)
   - Revenue trends

2. **Profitability Analysis (10 min)**
   - Labor costs vs revenue
   - Gross profit margin
   - Net profit after fees
   - Identify cost reduction opportunities

3. **MRR Analysis (10 min)**
   - MRR growth rate
   - New memberships
   - Cancellations
   - Net membership growth

**Week 3: Operations Review (30 minutes)**
1. **VSP Performance (15 min)**
   - Review Performance Analytics
   - Top performers to recognize
   - Conversion rates by VSP
   - Utilization rates by VSP
   - VSPs needing coaching
   - Commission performance

2. **Schedule Optimization (15 min)**
   - Review appointment heatmaps
   - Identify scheduling gaps
   - Calculate lost revenue opportunity
   - Plan optimization initiatives

**Week 4: Customer Analysis (30 minutes)**
1. **Segmentation Review (15 min)**
   - Size of each segment
   - Movement between segments
   - Segment trends over time
   - Export segments for campaigns

2. **Retention Analysis (15 min)**
   - Churn rate
   - Cancellation reasons
   - Win-back opportunities
   - Retention initiatives needed

**Monthly Report Creation:**
Create a simple monthly summary:
```
THE VITAL STRETCH - MONTHLY PERFORMANCE REPORT
Month: [Month Year]
Location: [Location Name]

KEY METRICS:
- Revenue: $X (Y% vs goal)
- Appointments: X (Y% vs goal)
- MRR: $X (Y% growth)
- Active Members: X
- Churn Rate: X%

TOP PERFORMERS:
- Revenue Leader: [VSP Name] - $X
- Conversion Leader: [VSP Name] - X%
- Utilization Leader: [VSP Name] - X%

OPPORTUNITIES:
1. [Opportunity 1]
2. [Opportunity 2]
3. [Opportunity 3]

ACTION ITEMS:
1. [Action 1]
2. [Action 2]
3. [Action 3]
```

### Segment Campaign Workflows

#### VIP Client Campaign

**Frequency:** Quarterly

**Process:**
1. Export VIP segment (Customers tab)
2. Review list for accuracy
3. Create exclusive offer:
   - "VIP Appreciation Month"
   - Special pricing on services
   - Free add-ons
   - Priority scheduling
4. Send personalized emails
5. Make personal phone calls to top VIPs
6. Track response and engagement

**Expected Results:**
- Increased loyalty
- Referrals from happy VIPs
- Higher LTV

#### At-Risk Client Campaign

**Frequency:** Monthly

**Process:**
1. Export At-Risk segment (Customers tab)
2. Review decline patterns
3. Create re-engagement offer:
   - "We Miss You" discount
   - Free consultation
   - Complimentary session
   - Personalized check-in
4. Send caring, personalized outreach
5. Offer scheduling assistance
6. Track conversions

**Expected Results:**
- 20-30% reactivation rate
- Prevented churn
- Improved retention

#### Inactive Paid Member Campaign

**Frequency:** Weekly (urgent)

**Process:**
1. Export Inactive Paid Members (Customers tab)
2. Immediate personal outreach (phone call preferred)
3. Understand why not attending:
   - Schedule issues?
   - Service concerns?
   - Forgot about membership?
4. Offer solutions:
   - Flexible scheduling
   - Different VSP
   - Modified service
   - Temporary freeze vs cancellation
5. Schedule appointment immediately
6. Follow up after appointment

**Expected Results:**
- 40-50% reactivation rate
- Saved MRR
- Improved member satisfaction

#### New Client Nurture Campaign

**Frequency:** Continuous (triggered by new joins)

**Process:**
1. Export New Clients segment (Customers tab)
2. Create welcome sequence:
   - Day 0: Welcome email
   - Day 2: Tip #1 (what to expect)
   - Day 5: Tip #2 (how to maximize value)
   - Day 10: Check-in call
   - Day 14: Membership offer
   - Day 21: Referral request
3. Personalize based on intro experience
4. Track conversion to membership

**Expected Results:**
- 40-60% membership conversion
- Higher retention
- Early referrals

#### High-Frequency Non-Member Conversion Campaign

**Frequency:** Monthly

**Process:**
1. Export High-Frequency Non-Members (Customers tab)
2. Calculate potential savings with membership
3. Create personalized pitch:
   - "You could save $X per month"
   - Show specific cost comparison
   - Limited-time joining bonus
4. Have VSP make recommendation
5. Offer trial membership (first month discount)
6. Track conversions

**Expected Results:**
- 50-70% conversion rate
- Increased MRR
- Higher customer LTV

### VSP Coaching Framework

#### Using Analytics for Coaching

**Monthly Performance Review Process:**

**1. Prepare (10 minutes before meeting)**
- Review VSP's Performance Analytics
- Print or screenshot relevant data
- Note specific months/metrics to discuss
- Prepare positive feedback and improvement areas

**2. Review Together (15 minutes)**
- Show VSP their performance data
- Discuss conversion rates month-by-month
- Review utilization rates
- Compare to team averages

**3. Analyze Together (10 minutes)**
- What's going well? (blue cells)
- What needs improvement? (purple cells)
- What changed between months?
- External factors vs controllable factors

**4. Set Goals (5 minutes)**
- Specific conversion rate target
- Specific utilization rate target
- Action items to achieve targets
- Timeline for improvement

**5. Create Action Plan (10 minutes)**
- Training needed
- Best practices to adopt
- Shadowing opportunities
- Check-in schedule

**6. Follow-Up (ongoing)**
- Weekly progress check-ins
- Monthly data review
- Celebrate improvements
- Adjust targets as needed

#### Conversion Rate Coaching

**For Low Conversion Rates (<30%):**

**Assessment Questions:**
- How do you approach intro appointments?
- What's your typical intro appointment flow?
- How do you explain membership benefits?
- When do you discuss membership?
- How do you handle objections?

**Common Issues & Solutions:**

**Issue: Not Discussing Membership**
- Solution: Build into intro appointment flow
- Script: "Many of our clients find that membership saves them money while helping them stay consistent with their wellness goals."

**Issue: Waiting Too Long**
- Solution: Discuss membership during intro
- Timing: After demonstrating value, before end of session

**Issue: Not Confident in Value Proposition**
- Solution: Training on membership benefits
- Practice: Role-play with manager

**Issue: Not Asking for the Sale**
- Solution: Always end with invitation
- Script: "Based on what we discussed, our [membership type] would be perfect for your goals. Can we get you set up today?"

#### Utilization Rate Coaching

**For Low Utilization Rates (<40%):**

**Assessment Questions:**
- What's your typical schedule look like?
- How do you handle gaps between appointments?
- Are clients booking far in advance?
- Do you have a lot of cancellations?
- How much time do you spend on admin tasks?

**Common Issues & Solutions:**

**Issue: Large Gaps Between Appointments**
- Solution: Block schedule appointments closer together
- Target: 15-30 minute buffers maximum
- Encourage back-to-back booking when possible

**Issue: Slow Booking**
- Solution: Optimize booking patterns
- Offer popular time slots
- Encourage regular standing appointments
- Use fill-in appointments for gaps

**Issue: Too Much Non-Appointment Time**
- Solution: Streamline administrative work
- Batch admin tasks
- Use technology effectively
- Delegate when possible

**Issue: Late Starts/Early Ends**
- Solution: Maximize available hours
- Start day fully booked
- End day fully booked
- Consider shift timing adjustment

### Goal Setting Best Practices

#### Setting Effective Goals

**SMART Goals Framework:**
- **Specific**: Exactly what will be achieved
- **Measurable**: Numerical target
- **Achievable**: Challenging but realistic
- **Relevant**: Aligns with business priorities
- **Time-Bound**: Clear deadline

**Examples:**

**Good Goal:**
"Increase monthly revenue from $18,000 to $22,000 (22% growth) by end of Q1 2025 through improved intro conversion rates and increased appointment volume."

**Bad Goal:**
"Make more money."

#### Revenue Goals

**How to Set:**
1. Review last 12 months average
2. Identify highest month
3. Set goal 10-20% above average
4. Ensure capacity exists
5. Account for seasonality

**Example Calculation:**
```
Average Last 12 Months: $20,000
Top Month: $25,000
Target Growth: 15%
New Goal: $23,000

Check Capacity:
- 4 VSPs × 40 hours/week × $60/hour average = $38,400 potential
- Goal of $23,000 = 60% capacity utilization ✓ Achievable
```

#### Appointment Goals

**How to Set:**
1. Calculate average appointments per VSP
2. Multiply by number of VSPs
3. Account for:
   - Vacation/time off
   - Training time
   - Lead responsibilities
   - Desired utilization rate

**Example Calculation:**
```
4 VSPs × 8 appointments/day × 22 working days = 704 appointments
Minus 10% for time off/training = 634 appointments
Minus 10% buffer for realistic scheduling = 570 appointments

Set paid goal: 450
Set intro goal: 50
Total: 500 appointments (leaves room for growth)
```

#### Conversion Rate Goals

**How to Set:**
1. Review current conversion rates from analytics
2. Identify top performers
3. Set team goal between current average and top performer
4. Individual goals based on current performance + improvement

**Example:**
```
Current Team Average: 35%
Top Performer: 52%
Target Team Goal: 42% (halfway improvement)

Individual Goals:
- High performer (48%): Maintain at 48-50%
- Average performer (35%): Improve to 40%
- Low performer (22%): Improve to 30%
```

#### Utilization Rate Goals

**How to Set:**
1. Review current utilization from analytics
2. Industry benchmark: 60-70% for service businesses
3. Account for:
   - Administrative duties
   - Training time
   - Lead responsibilities
   - Break time

**Example:**
```
Current Average: 42%
Target: 55%
Timeline: 3 months

Month 1: Achieve 48% (focus on scheduling gaps)
Month 2: Achieve 52% (optimize booking patterns)
Month 3: Achieve 55% (fill-in appointments, promotions)
```

### Success Metrics & KPIs

#### Dashboard KPIs to Track

**Financial KPIs:**
- Total Revenue (monthly)
- MRR (Monthly Recurring Revenue)
- Revenue Growth Rate (month-over-month)
- Gross Profit Margin (target: 50%+)
- Net Profit Margin (target: 20-30%)
- Labor Cost Percentage (target: <50%)
- Revenue per Appointment (target: $60-$80)
- Revenue per VSP (monthly)

**Operational KPIs:**
- Total Appointments (monthly)
- Paid Appointments (target: 300-400)
- Intro Appointments (target: 50-75)
- Appointment Conversion Rate (intro to paid) (target: 60%+)
- Membership Conversion Rate (intro to member) (target: 40-50%)
- Average Appointments per VSP per Day (target: 6-8)
- VSP Utilization Rate (target: 55-65%)
- Schedule Gap Time (target: minimize)

**Customer KPIs:**
- Active Members (target: growing)
- Membership Penetration Rate (target: 40-60% of customers)
- MRR Growth Rate (target: 5-10% monthly)
- Customer Churn Rate (target: <5% monthly)
- Member Retention Rate (target: >95% monthly)
- Average Customer LTV (target: $1,000+)
- New Customers (monthly)
- VIP Client Count (target: 10-20% of base)

**Marketing KPIs:**
- Lead Generation (monthly)
- Lead Conversion Rate (target: 30-50%)
- Lead Source Effectiveness (conversion rate by source)
- Cost per Acquisition (if cost data available)
- ROI by Marketing Channel

**Team KPIs:**
- VSP Conversion Rate (target: 40%+ team average)
- VSP Utilization Rate (target: 55%+ team average)
- Commission Performance (growing)
- Client Satisfaction (via Net Promoter Score if tracked)

#### Creating a Custom KPI Dashboard

**Recommendation:** Create monthly snapshot

**Format:**
```
THE VITAL STRETCH - KPI DASHBOARD
Month: [Month Year]
Location: [Location Name]

FINANCIAL HEALTH
□ Revenue: $X (Y% vs goal) [↑↓]
□ MRR: $X (Y% growth) [↑↓]
□ Net Profit Margin: X% [↑↓]
□ Labor Cost %: X% [↑↓]

OPERATIONAL PERFORMANCE
□ Total Appointments: X (Y% vs goal) [↑↓]
□ Conversion Rate (Intro→Member): X% [↑↓]
□ Avg VSP Utilization: X% [↑↓]
□ Revenue per Appointment: $X [↑↓]

CUSTOMER SUCCESS
□ Active Members: X (Y% growth) [↑↓]
□ Member Churn Rate: X% [↑↓]
□ New Customers: X [↑↓]
□ VIP Clients: X [↑↓]

TEAM PERFORMANCE
□ Top Converter: [VSP] - X%
□ Highest Revenue: [VSP] - $X
□ Best Utilization: [VSP] - X%

GROWTH INDICATORS
□ MRR Growth: X% month-over-month
□ Customer Growth: X% month-over-month
□ Revenue Growth: X% month-over-month
```

---

## Conclusion

The Vital Stretch Analytics Dashboard is a comprehensive tool designed to transform your Momence data into actionable business insights. By following the practices outlined in this guide, you'll be able to:

✅ Make data-driven decisions
✅ Optimize VSP performance
✅ Improve customer retention
✅ Maximize revenue and profitability
✅ Grow your franchise strategically

**Remember:**
- Data is only valuable if you act on it
- Small improvements compound over time
- Consistency matters more than perfection
- Your customers want you to succeed

**Thank you for using The Vital Stretch Analytics Dashboard!**

For support or feedback, contact your franchise administrator or the dashboard creator.

---

**Created with ❤️ by bonJoeV for The Vital Stretch Franchise**

*Version v2.20251113.04 - November 13, 2024*
