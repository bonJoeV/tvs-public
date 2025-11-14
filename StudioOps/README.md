# The Vital Stretch Analytics Dashboard

**Version:** v2.20251113.04 | **Updated:** November 13, 2025 | **Created by:** bonJoeV with ❤️

---

## What Is This?

A powerful, single-page analytics dashboard for The Vital Stretch franchises. Run it entirely in your browser—no server, no installation, complete privacy.

### Key Features
- 📊 8 interactive analytical tabs + VSP Performance Analytics
- 💰 Complete financial tracking (revenue, labor, profitability)
- 👥 Advanced client segmentation with downloadable lists
- 📈 Goal tracking & period comparisons
- 🎯 VSP conversion rates & utilization metrics by month
- 🗓️ Booking pipeline & attendance analytics
- 🗺️ Location-specific appointment heatmaps
- 🎨 Colorblind-friendly performance indicators
- 📥 CSV exports for any data
- 🔒 Your data never leaves your computer

---

## Quick Start

### Step 1: Export Data from Momence

You need **9 data files** (some required, some optional):

#### Required Files (6)

1. **Membership Sales**
   - Report: "Membership sales - A report on membership purchases history"
   - Download: Summary
   - Save as: `momence--membership-sales-export.csv`

2. **Membership Cancellations**
   - Report: "Membership sales" → Cancellations tab
   - Download: Summary
   - Save as: `momence--membership-sales-export__1_.csv`

3. **New Leads & Customers**
   - Report: "New Leads & Customers by join date"
   - Download: Summary
   - Save as: `momence-new-leads-and-customers.csv`

4. **Practitioner Payroll ZIP**
   - Report: "Practitioner Payroll - Multiple practitioners payroll details"
   - Download: ZIP (includes appointments, time tracking, commissions)
   - Save as: `momence-payroll-report-summary.zip`

5. **Leads Converted Report**
   - Report: "Leads converted" or "Lead Conversion Report"
   - Download: Summary
   - Save as: `momence-leads-converted-report.csv`

6. **Appointments Attendance Report**
   - Report: "Appointments attendance report"
   - Download: CSV (combined/summary export)
   - Save as: `momence-appointments-attendance-report-combined.csv`

7. **Membership Renewals**
   - Report: "Membership renewals report"
   - Download: Summary
   - Save as: `momence-membership-renewals-report.csv`
   - Shows upcoming renewal dates for planning

8. **Frozen Memberships**)
   - Report: "Frozen memberships report"
   - Download: Summary
   - Save as: `frozen-memberships-report.csv`
   - Tracks paused memberships

**💡 Tip:** Select **LAST 365 Days** for all date ranges to get comprehensive historical data.

---

### Step 2: Upload Data to Dashboard

1. **Open** the dashboard HTML file in your browser
2. Click the **📤 Upload Data** button
3. Upload your files in any order (drag & drop or click to browse)
4. Wait for green checkmarks (✅) for each file
5. Dashboard automatically processes and displays your data

**⚠️ IMPORTANT: Clear Browser Cache**
If you've used an older version:
- **Windows/Linux:** Press `Ctrl + Shift + R`
- **Mac:** Press `Cmd + Shift + R`

**Verify Latest Version:** Check footer shows `v2.20251113.04`

---

### Step 3: Configure Settings

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
- **Base Hourly Rate** - Default: $13.00

Click **Save Settings** - stored locally in your browser.

---

## Dashboard Overview

### Main Tabs

1. **📊 Overview** - Key metrics, goals, financial performance
2. **📈 Timeline** - Trends over time (revenue, appointments, MRR)
3. **👥 VSP Performance** - Individual practitioner metrics & analytics
4. **🧑‍🤝‍🧑 Customers** - Client demographics & visit patterns
5. **📄 Retention** - Churn analysis & cohort retention
6. **🚀 Journey** - Customer lifecycle funnel
7. **💳 Memberships** - Subscription tracking & growth
8. **❌ Cancellations** - Churn reasons & lost revenue

### VSP Performance Analytics (NEW!)

Located at the top of the VSP tab, includes:

**📊 Conversion Rates Table**
- Tracks intro stretch → paid member conversion by VSP and month
- Color-coded performance (Blue = Excellent 50%+, Orange = Good 30-49%, Purple = Needs Improvement <30%)
- Hover tooltips show detailed breakdown (conversions/intro stretches)

**⏱️ Utilization Rates Table**
- Measures table time efficiency (appointment hours / clocked hours)
- Color-coded performance (Blue = Excellent 60%+, Orange = Good 40-59%, Purple = Needs Improvement <40%)
- Hover tooltips show hour breakdown

**🎨 Colorblind-Friendly Design**
- Uses Blue-Orange-Purple color scheme
- Maximum distinction for all types of colorblindness
- Clear visual indicators for performance levels

### Advanced Features

**Client Segmentation** (Customers tab)
- 5 strategic segments with downloadable contact lists
- VIP Clients, New Clients, At-Risk, Inactive Paid Members, High-Frequency Non-Members
- Export any segment as CSV for outreach campaigns

**Lead Tracking** (Leads tab)
- Conversion rate tracking by source
- Lead timeline visualization
- LTV analysis for converted leads
- Source effectiveness comparison

**Booking Pipeline** (Insights tab)
- Upcoming appointments count
- Top 10 most frequent clients
- Top VSPs by appointments booked
- Paid vs unpaid reservation tracking

**Location Heatmaps** (Schedule tab)
- Separate heatmap for each location
- Shows busiest times by day and hour
- Click any day or hour for detailed breakdown

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

### VSP Metrics
- **Conversion Rate** - Intro stretches that become paid members
- **Utilization Rate** - Appointment time / total clocked time
- **Revenue per Hour** - Efficiency metric
- **Appointments per VSP** - Workload distribution

---

## Best Practices

### Weekly Routine (15 minutes)
1. Export fresh data from Momence
2. Upload to dashboard
3. Review goal progress
4. Check VSP Performance Analytics
5. Identify at-risk clients
6. Plan outreach campaigns

### Monthly Review (1 hour)
1. Analyze full month trends
2. Review VSP conversion & utilization rates
3. Check retention & churn
4. Compare to previous periods
5. Export segments for campaigns
6. Adjust strategies and goals

---

## Troubleshooting

**"Dashboard not updating"**
- Force reload: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- Check footer shows version `v2.20251113.04`

**"No data showing"**
- Verify at least 6 required files are uploaded
- Check for green checkmarks (✅) on each file
- Refresh page and re-upload if needed

**"VSP Analytics showing December dates"**
- Dashboard filters future dates automatically
- Check browser console (F12) for debug messages
- Ensure Momence data doesn't include test/future appointments

**"Colors hard to distinguish"**
- Current scheme is designed for colorblind accessibility
- Blue = Excellent, Orange = Good, Purple = Needs Improvement
- If still difficult, contact support for alternative schemes

---

## Privacy & Security

✅ **Your data never leaves your computer** - All processing in browser  
✅ **No server connection** - Works completely offline  
✅ **No login required** - Just open and use  
✅ **No tracking** - Zero analytics or data collection  
✅ **Local storage only** - Settings saved in your browser  

---

## System Requirements

- **Browser:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Operating System:** Windows, macOS, Linux
- **Internet:** Only needed to download dashboard (once)
- **Storage:** ~2MB for dashboard, plus your data files

---

## What's New in v2.20251113.04

### VSP Performance Analytics
- 📊 Moved to top of VSP tab for prominence
- 📊 Added conversion rate tracking (intro → member by month)
- ⏱️ Added utilization rate tracking (table time efficiency by month)
- 🎨 Implemented colorblind-friendly Blue-Orange-Purple color scheme
- 💡 Added detailed tooltips on hover for all metrics
- 🔮 Automatic filtering of future dates from analytics

### Design Improvements
- Color coding: Blue (excellent), Orange (good), Purple (needs improvement)
- Maximum visual distinction for colorblind users
- Clean legends explaining thresholds
- Professional appearance

### Bug Fixes
- Fixed future date filtering in VSP analytics
- Improved conversion rate calculations
- Enhanced utilization rate accuracy
- Better handling of edge cases

---

## Getting Help

For complete documentation, see **README-Detailed.md**

For technical support or questions, contact your franchise administrator.

---

**Thank you for using The Vital Stretch Analytics Dashboard!**

*Created with ❤️ by bonJoeV for The Vital Stretch Franchise*
