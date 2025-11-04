# The Vital Stretch Analytics Dashboard

**Version:** v2.20251104.07 | **Updated:** November 4, 2025 | **Created by:** bonJoeV with ❤️

---

## What Is This?

A powerful, single-page analytics dashboard for The Vital Stretch franchises. Run it entirely in your browser—no server, no installation, complete privacy.

### Key Features
- 📊 8 interactive analytical tabs
- 💰 Complete financial tracking (revenue, labor, profitability)
- 👥 Advanced client segmentation with downloadable lists
- 📈 Goal tracking & period comparisons
- 📥 CSV exports for any data
- 🔒 Your data never leaves your computer

---

## Quick Start

### Step 1: Configure Momence (One-Time Setup)

Before exporting data, configure your Momence account:

#### Pay Rates Configuration
**Location:** Studio Set-up → Pay Rates
- Create pay rate structures for each VSP level (Level 1, Level 2, Lead, etc.)
- Set hourly rates or per-session rates
- Assign rates to different service types (Table Time, Studio Lead, etc.)

#### Practitioner Setup
**Location:** Studio Set-up → Practitioners
- Add all VSPs (Vital Stretch Practitioners)
- Assign each practitioner to their appropriate role/level
- Ensure contact information is complete
- Verify active status for current team members

#### Appointment Pay Rates
**Location:** Appointments → Boards
- Set the pay rate for each VSP on the appointment board
- Verify rates are correctly applied to different service types
- Check that special rates (introductory sessions, events) are configured

---

### Step 2: Export Data from Momence

You need **3 required files** (plus 1 optional ZIP file):

#### Report 1: Membership Sales
**Report Name:** "Membership sales - A report on membership purchases history"

**How to Export:**
1. Log in to Momence → **Reports** section
2. Find "Membership sales" in your Favorite Reports
3. Select date range: **All time** (recommended)
4. Click **Download Summary**
5. Save as: `momence--membership-sales-export.csv`

#### Report 2: Membership Cancellations
**Report Name:** "Membership sales" → **Cancellations tab**

**How to Export:**
1. In Momence, go to **Reports** → Membership sales
2. Click the **Cancellations tab**
3. Select date range: **All time** (recommended)
4. Click **Download Summary**
5. Save as: `momence--membership-sales-export__1_.csv`

#### Report 3: New Leads & Customers
**Report Name:** "New Leads & Customers by join date"

**How to Export:**
1. Go to **Reports** → Find in Favorite Reports
2. Select date range: **All time** (recommended)
3. Click **Download Summary**
4. Save as: `momence--new-leads-and-customers.csv`

#### Report 4: Practitioner Payroll ZIP (Optional but Recommended)
**Report Name:** "Practitioner Payroll - Multiple practitioners payroll details"

**How to Export:**
1. Go to **Reports** → Find in Favorite Reports
2. Select **ALL practitioners** (or select all individually)
3. Choose date range (recommend: last 90 days or All time)
4. Click **Download** (creates a ZIP file automatically)
5. Save the ZIP file (e.g., `payroll-2025-11-04.zip`)

**What it includes:**
- Appointment details & labor costs
- Time tracking (clock in/out) for utilization metrics
- Commission data (memberships & product sales)
- Works/doesn't work summary

---

### Step 3: Upload Data to Dashboard

1. **Open** the dashboard HTML file in your browser
2. Click the **📤 Upload Data** button
3. Upload your 3-4 files in any order
4. Wait for green checkmarks (✅) for each file
5. Dashboard automatically processes and displays your data

**Supported Files:**
- ✅ CSV files (membership sales, cancellations, leads)
- ✅ ZIP files (practitioner payroll - no need to extract!)

---

### Step 4: Configure Settings

Click the **⚙️ Settings** button to configure:

#### Business Settings
- **Timezone** - Select your local timezone
- **Franchise Fee** - Default: 6%
- **Brand Fund** - Default: 2%
- **Credit Card Fees** - Default: 3%

#### Monthly Goals
- **Revenue Goal** - Default: $20,000
- **Paid Appointments Goal** - Default: 300
- **Intro Appointments Goal** - Default: 50

#### Labor Settings
- **Base Hourly Rate** - Default: $13.00 (for non-appointment work)

Click **Save Settings** and your preferences are stored locally.

---

## Dashboard Overview

### 8 Main Tabs

1. **📊 Overview** - Key metrics, goals, financial performance
2. **📈 Timeline** - Trends over time (revenue, appointments, MRR)
3. **👥 VSP Performance** - Individual practitioner metrics
4. **🧑‍🤝‍🧑 Customers** - Client demographics & visit patterns
5. **🔄 Retention** - Churn analysis & cohort retention
6. **🚀 Journey** - Customer lifecycle funnel
7. **💳 Memberships** - Subscription tracking & growth
8. **❌ Cancellations** - Churn reasons & lost revenue

### Advanced Features

**Client Segmentation** (in Customers tab)
- 5 strategic segments with downloadable contact lists
- VIP Clients, New Clients, At-Risk, Inactive Paid Members, High-Frequency Non-Members
- Export any segment as CSV for outreach campaigns

**Filtering & Comparisons**
- Date range selection
- Location filtering (multi-location franchises)
- Practitioner filtering
- Period-over-period comparisons

---

## Key Metrics Explained

### Financial Metrics
- **Total Revenue** - All income from appointments and memberships
- **Labor Costs** - Appointment pay + non-appointment hours × base rate
- **Gross Profit** - Revenue minus labor costs
- **Net Profit** - Gross profit minus franchise fees, brand fund, CC fees

### Customer Metrics
- **MRR (Monthly Recurring Revenue)** - Active membership subscriptions
- **Churn Rate** - Percentage of members who cancel
- **Customer LTV** - Lifetime value per customer
- **Retention Rate** - Percentage of customers retained period-over-period

### Operational Metrics
- **Utilization Rate** - Hours worked / Hours paid (from time clock data)
- **Average Ticket** - Average revenue per appointment
- **Appointments per VSP** - Workload distribution
- **Intro Conversion Rate** - Intros that become regular customers

---

## Best Practices

### Data Management
- ✅ Export data weekly from Momence
- ✅ Keep consistent file naming
- ✅ Store files in organized folders by date
- ✅ Backup dashboard HTML file regularly

### Weekly Routine (15 minutes)
1. Export fresh data from Momence
2. Upload to dashboard
3. Review goal progress
4. Check VSP performance
5. Export any urgent segments (e.g., Inactive Paid Members)
6. Plan outreach campaigns

### Monthly Review (1 hour)
1. Analyze full month trends
2. Compare to previous periods
3. Review all segments
4. Check retention & churn
5. Adjust strategies based on data
6. Update goals if needed

---

## Troubleshooting

### Common Issues

**"No data showing after upload"**
- Verify all 3 required CSV files are uploaded
- Check for green checkmarks (✅) on each file
- Ensure files are exported correctly from Momence

**"Missing appointment or commission data"**
- Upload the optional Payroll ZIP file
- Ensure time clock is enabled in Momence
- Verify pay rates are configured in Momence

**"Settings not saving"**
- Check that browser allows local storage
- Disable private/incognito mode
- Try a different browser (Chrome, Firefox, Edge)

**"Dashboard looks broken"**
- Use a modern browser (Chrome 90+, Firefox 88+, Edge 90+)
- Disable browser extensions temporarily
- Clear browser cache and reload

---

## Privacy & Security

✅ **Your data never leaves your computer** - All processing happens in your browser  
✅ **No server connection** - Works completely offline  
✅ **No login required** - Just open and use  
✅ **No tracking** - Zero analytics or data collection  
✅ **Local storage only** - Settings saved in your browser  

---

## System Requirements

- **Browser:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Operating System:** Windows, macOS, Linux (any modern OS)
- **Internet:** Only needed to download dashboard file (once)
- **Storage:** ~2MB for dashboard, plus your CSV/ZIP files
- **RAM:** Minimal (runs in browser)

---

## Getting Help

### Support Resources
- **Complete Documentation** - See README-Detailed.md
- **Version Info** - Check footer of dashboard
- **Tooltips** - Hover over (?) icons in dashboard
- **Momence Support** - For data export questions

### Report Issues
- Document the issue clearly
- Note which tab/feature is affected
- Include browser version
- Contact your franchise administrator

---

## Version History Highlights

### v2.20251104.07 (Current)
- 🔴 Fixed cancellation value calculations (MRR matching)
- 🔴 Fixed paid appointments vs goal tracking
- Improved email-based matching for cancellations
- Separate tracking for paid vs intro appointments

### v2.20251104.06
- Changed default revenue goal to $20,000
- Changed default intro goal to 50
- Fixed churn rate by location
- Enhanced customer name extraction

### v2.20251103.05
- Added franchise configuration settings
- Comprehensive labor cost tracking
- New financial performance section
- Monthly goal visualizations

### v2.20251103.04
- Added utilization tracking
- Added commission tracking
- Enhanced ZIP file processing
- Improved tab organization

---

## Success Formula

1. **Measure** - Upload data weekly
2. **Analyze** - Review dashboard regularly
3. **Act** - Implement insights promptly
4. **Iterate** - Refine based on results
5. **Repeat** - Make it a habit

### Remember:
- Data is only valuable if you act on it
- Segments are opportunities, not just lists
- Small improvements compound over time
- Your customers want you to succeed

---

**Thank you for using The Vital Stretch Analytics Dashboard!**

*For complete technical documentation, see README-Detailed.md*

---

**Created with ❤️ by bonJoeV for The Vital Stretch Franchise**
