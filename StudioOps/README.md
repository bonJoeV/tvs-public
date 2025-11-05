# The Vital Stretch Analytics Dashboard

**Version:** v2.20251105.5 | **Updated:** November 5, 2025 | **Created by:** bonJoeV with ❤️

---

## What Is This?

A powerful, single-page analytics dashboard for The Vital Stretch franchises. Run it entirely in your browser—no server, no installation, complete privacy.

### Key Features
- 📊 8 interactive analytical tabs
- 💰 Complete financial tracking (revenue, labor, profitability)
- 👥 Advanced client segmentation with downloadable lists
- 📈 Goal tracking & period comparisons
- 📋 Attendance analytics & booking pipeline tracking
- 🗺️ Location-specific appointment heatmaps
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

You need **4 required files** and **2 optional files** for full functionality:

#### Report 1: Membership Sales (**REQUIRED**)
**Report Name:** "Membership sales - A report on membership purchases history"

**How to Export:**
1. Log in to Momence → **Reports** section
2. Find "Membership sales" in your Favorite Reports
3. Select date range: **LAST 365 Days** (recommended)
4. Click **Download Summary**
5. Save as: `momence--membership-sales-export.csv`

#### Report 2: Membership Cancellations (**REQUIRED**)
**Report Name:** "Membership sales" → **Cancellations tab**

**How to Export:**
1. In Momence, go to **Reports** → Membership sales
2. Click the **Cancellations tab**
3. Select date range: **LAST 365 Days** (recommended)
4. Click **Download Summary**
5. Save as: `momence--membership-sales-export__1_.csv`

#### Report 3: New Leads & Customers (**REQUIRED**)
**Report Name:** "New Leads & Customers by join date"

**How to Export:**
1. Go to **Reports** → Find in Favorite Reports
2. Select date range: **LAST 365 Days** (recommended)
3. Click **Download Summary**
4. Save as: `momence-new-leads-and-customers.csv`

#### Report 4: Practitioner Payroll ZIP (**REQUIRED**)
**Report Name:** "Practitioner Payroll - Multiple practitioners payroll details"

**How to Export:**
1. Go to **Reports** → Find in Favorite Reports
2. Select **ALL practitioners** (or select all individually)
3. Select date range: **LAST 365 Days** (recommended)
4. Click **Download** (creates a ZIP file automatically)
5. Save the ZIP file (e.g., `momence-payroll-report-summary.zip`)

**What it includes:**
- Appointment details & labor costs
- Time tracking (clock in/out) for utilization metrics
- Commission data (memberships & product sales)
- Works/doesn't work summary

#### Report 5: Leads Converted Report (**REQUIRED**)
**Report Name:** "Leads converted" or "Lead Conversion Report"

**How to Export:**
1. Go to **Reports** → Find in Favorite Reports
2. Select date range: **LAST 365 Days** (recommended)
3. Click **Download Summary**
4. Save as: `momence-leads-converted-report.csv`

**What it provides:**
- Tracks which leads converted to customers
- Shows conversion dates and methods
- Calculates lifetime value (LTV) per converted lead
- Analyzes lead source effectiveness

#### Report 6: Appointments Attendance Report ZIP (**REQUIRED**)
**Report Name:** "Appointments attendance report"

**How to Export:**
1. Go to **Reports** → Find in Favorite Reports
2. Select **ALL practitioners**
3. Select date range: **LAST 365 Days** (recommended)
4. Click **Download** (creates a ZIP file automatically)
5. Save the ZIP file (e.g., `momence-appointments-attendance-report-summary.zip`)

**What it provides:**
- Client booking patterns and appointment history
- Upcoming appointments (booking pipeline visibility)
- Payment status tracking (paid vs unpaid reservations)
- VSP name mapping for cleaner reports
- Top client frequency analysis

**Benefits:**
- See your booking pipeline strength
- Identify most frequent/loyal clients
- Track unpaid reservations for follow-up
- Analyze future revenue potential

---

### Step 3: Upload Data to Dashboard

1. **Open** the dashboard HTML file in your browser
2. Click the **📤 Upload Data** button
3. Upload your 4-6 files in any order
4. Wait for green checkmarks (✅) for each file
5. Dashboard automatically processes and displays your data

**⚠️ IMPORTANT: Clear Browser Cache**
If you've used an older version of the dashboard, force-reload to get the latest version:
- **Windows/Linux:** Press `Ctrl + Shift + R`
- **Mac:** Press `Cmd + Shift + R`

**Verify Latest Version:** Check the browser tab title shows the footer shows `v2.20251105.5`

**Supported Files:**
- ✅ CSV files (membership sales, cancellations, leads, leads converted)
- ✅ ZIP files (practitioner payroll, attendance report - no need to extract!)

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

### New in Latest Version

**📋 Attendance Analytics** (Insights tab)
- Booking pipeline visibility with upcoming appointments count
- Top 10 most frequent clients ranked by visit count
- Top VSPs by appointments booked
- Paid vs unpaid reservation tracking
- Identifies VIP clients for special treatment

**🗺️ Location-Specific Appointment Heatmaps** (Schedule tab)
- Separate heatmap for each location
- Shows busiest times by day and hour
- Click any day or hour for detailed breakdown
- Helps optimize scheduling and staffing

### Advanced Features

**Client Segmentation** (in Customers tab)
- 5 strategic segments with downloadable contact lists
- VIP Clients, New Clients, At-Risk, Inactive Paid Members, High-Frequency Non-Members
- Export any segment as CSV for outreach campaigns

**Lead Tracking** (Leads tab - when Leads Converted report uploaded)
- Conversion rate tracking by source
- Lead timeline visualization
- LTV analysis for converted leads
- Source effectiveness comparison

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

**"Dashboard not updating with new version"**
- **Force reload** to clear browser cache
- Windows/Linux: Press `Ctrl + Shift + R`
- Mac: Press `Cmd + Shift + R`
- Check tab title shows latest version `[v5-FIELD-FIX]`
- Check footer shows `v2.20251105.5`

**"No data showing after upload"**
- Verify all 4 required files are uploaded (memberships, cancellations, leads, payroll ZIP)
- Check for green checkmarks (✅) on each file
- Ensure files are exported correctly from Momence
- Try refreshing the page and re-uploading

**"Non-Appt Labor missing or showing zero"**
- Upload the Practitioner Payroll ZIP file (required for time tracking)
- Ensure time clock is enabled in Momence
- Verify practitioners are clocking in/out properly
- Check browser console (F12) for debug messages
- Clear cache and force reload

**"Attendance Analytics not showing"**
- Upload the Attendance Report ZIP file (optional)
- This section only appears when attendance data is loaded
- Check for green checkmark on attendance file upload

**"Missing appointment or commission data"**
- Upload the Practitioner Payroll ZIP file
- Ensure pay rates are configured in Momence
- Verify practitioners are assigned to appointments

**"Settings not saving"**
- Check that browser allows local storage
- Disable private/incognito mode
- Try a different browser (Chrome, Firefox, Edge)

**"Dashboard looks broken or won't load"**
- Use a modern browser (Chrome 90+, Firefox 88+, Edge 90+)
- Disable browser extensions temporarily
- Clear browser cache completely
- Try opening in incognito/private mode
- Check browser console (F12) for error messages

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

### v2.20251105.5 (Current)
- 🔴 **CRITICAL FIX:** Non-Appt Labor calculation with month/location filtering
- 🔴 Fixed time tracking field name bug ("Clocked in" vs "Clock in date")
- ✨ Added Attendance Analytics section with booking pipeline tracking
- ✨ Added location-specific appointment heatmaps
- ✨ Added support for Leads Converted report
- ✨ Added support for Attendance Report ZIP file
- 🎨 Reduced comparison text font size to 8px for better visual hierarchy
- 🐛 Fixed template literal bug in Insights recommendations
- 📊 Added top 10 most frequent clients analysis
- 📊 Added top VSPs by appointments booked
- 📊 Added paid vs unpaid reservation tracking
- 🔧 Added cache-busting meta tags
- 🔧 Added debug console logging for troubleshooting

### v2.20251104.07
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
