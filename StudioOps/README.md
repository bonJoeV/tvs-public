# The Vital Stretch Analytics Dashboard

**Version:** v2.20251115.11 | **Single-page HTML dashboard for franchise analytics**

---

## 🎯 What Is This?

A powerful analytics dashboard for The Vital Stretch franchises that runs entirely in your browser. No installation, no servers, complete privacy.

### Key Features
- 📊 8 comprehensive analytical tabs
- 💰 Complete financial tracking (revenue, labor, profitability)
- 👥 Advanced client segmentation with downloadable lists
- 📈 Goal tracking & performance monitoring
- 🎯 VSP conversion rates & utilization metrics
- 🗺️ Location-specific appointment heatmaps
- 🎨 Colorblind-friendly performance indicators
- 📥 CSV exports for any data view
- 🔒 Complete privacy - your data never leaves your computer

---

## 🚀 Quick Start

### Step 1: Export Data from Momence

You need **8 data files** from your Momence account:

#### Required Files

1. **Membership Sales** → `momence--membership-sales-export.csv`
   - Report: "Membership sales - A report on membership purchases history"

2. **Membership Cancellations** → `momence--membership-sales-export__1_.csv`
   - Report: "Membership sales" → Cancellations tab

3. **New Leads & Customers** → `momence-new-leads-and-customers.csv`
   - Report: "New Leads & Customers by join date"

4. **Practitioner Payroll ZIP** → `momence-payroll-report-summary.zip`
   - Report: "Practitioner Payroll" (includes appointments, time tracking, commissions)

5. **Leads Converted Report** → `momence-leads-converted-report.csv`
   - Report: "Leads converted" or "Lead Conversion Report"

6. **Appointments Attendance Report** → `momence-appointments-attendance-report-combined.csv`
   - Report: "Appointments attendance report"

7. **Membership Renewals** → `momence-membership-renewals-report.csv`
   - Report: "Membership renewals report"

8. **Frozen Memberships** → `frozen-memberships-report.csv`
   - Report: "Frozen memberships report"

💡 **Tip:** Select **LAST 365 Days** for all exports to get comprehensive historical data.

---

### Step 2: Open & Upload Data

1. **Open** `vital-stretch-dashboard.html` in your browser
2. Click **📤 Upload Data** button
3. Upload your 8 files (drag & drop or click to browse)
4. Wait for green checkmarks (✅) for each file
5. Dashboard automatically processes and displays your data

⚠️ **First Time Users:** If you've used an older version, clear your browser cache:
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

**Verify Version:** Check footer shows `v2.20251115.11`

---

### Step 3: Configure Settings

Click **⚙️ Settings** to configure:

**Business Settings:**
- Timezone (for accurate date/time calculations)
- Franchise Fee (default: 6%)
- Brand Fund (default: 2%)
- Credit Card Fees (default: 3%)

**Monthly Goals:**
- Revenue Goal (default: $20,000)
- Paid Appointments Goal (default: 300)
- Intro Appointments Goal (default: 50)

**Labor Settings:**
- Base Hourly Rate (default: $13.00)

Click **Save Settings** - stored locally in your browser.

---

## 📊 Dashboard Tabs

### 1. Overview
Key metrics at a glance: revenue, appointments, memberships, goals progress, and top-level KPIs.

### 2. Timeline
Historical trends: revenue over time, appointment volume, MRR growth, weekly/monthly comparisons.

### 3. VSP Performance
**Includes Advanced Analytics:**
- **Conversion Rates Table** - Intro stretch → paid member conversion by VSP/month
- **Utilization Rates Table** - Table time efficiency (appointment hours / clocked hours)
- Revenue by VSP, appointments breakdown, unique clients served
- Color-coded performance indicators (Blue = Excellent, Orange = Good, Purple = Needs Improvement)

### 4. Customers
Client demographics, visit patterns, customer lifetime value, and advanced segmentation.

**Advanced Client Segmentation:**
- 💎 VIP Clients (>$2,500 LTV)
- ⚠️ At-Risk Clients (45+ days inactive)
- ❌ Inactive Paid Members
- 🌱 New Clients (<3 visits)
- ⚡ High-Frequency Non-Members

Each segment includes downloadable contact lists for targeted campaigns.

### 5. Retention
Churn analysis, cohort retention tracking, membership lifecycle, and retention rate trends.

### 6. Journey
Customer lifecycle funnel from lead → customer → member, with conversion metrics at each stage.

### 7. Memberships
Subscription tracking, MRR analysis, membership growth trends, and active member counts.

### 8. Cancellations
Churn reasons analysis, lost revenue tracking, cancellation trends, and reactivation opportunities.

### 9. Leads
Lead generation tracking, source effectiveness, conversion rates, and lead value analysis.

### 10. Schedule
Appointment timing analysis with **location-specific heatmaps** showing busiest times by day/hour.

---

## 📈 Key Metrics Explained

**Financial Metrics:**
- **Total Revenue** - All income from appointments and memberships
- **Labor Costs** - VSP pay + non-appointment hours × base rate
- **Gross Profit** - Revenue - Labor Costs
- **Net Profit** - Gross Profit - Franchise Fees - Brand Fund - CC Fees
- **MRR** - Monthly Recurring Revenue from active subscriptions

**Customer Metrics:**
- **Customer LTV** - Lifetime value per customer
- **Churn Rate** - % of members who cancel
- **Retention Rate** - % of customers retained period-over-period
- **Conversion Rate** - % of leads who become customers

**VSP Metrics:**
- **Conversion Rate** - % of intro stretches that become paid members (Target: 50%+)
- **Utilization Rate** - Appointment hours / clocked hours (Target: 60%+)
- **Revenue per Hour** - Efficiency metric
- **Appointments per VSP** - Workload distribution

---

## 🎯 Best Practices

### Weekly Routine (15 minutes)
1. Export fresh data from Momence
2. Upload to dashboard
3. Review goal progress in Overview tab
4. Check VSP Performance Analytics
5. Review At-Risk clients segment
6. Export segments for outreach campaigns

### Monthly Review (1 hour)
1. Analyze full month trends in Timeline
2. Review VSP conversion & utilization rates
3. Check Retention & Cancellations tabs
4. Compare to previous periods
5. Export all client segments for campaigns
6. Adjust next month's goals in Settings

### Quarterly Planning
1. Identify seasonal patterns in Timeline
2. Review location performance in Schedule heatmaps
3. Analyze customer journey funnel
4. Plan marketing campaigns based on lead sources
5. Set strategic goals for next quarter

---

## 🛠️ Troubleshooting

**Dashboard not updating?**
- Force reload: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- Verify footer shows `v2.20251115.11`
- Clear browser cache completely

**No data showing?**
- Verify all 8 required files uploaded successfully
- Look for green checkmarks (✅) on each file
- Check browser console (F12) for error messages
- Try refreshing page and re-uploading

**VSP Analytics showing weird dates?**
- Dashboard automatically filters future dates
- Check that Momence exports don't include test data
- Verify appointment dates are in correct format

**Can't export segments?**
- Disable pop-up blocker for this page
- Check browser's download settings
- Try different browser (Chrome recommended)

**Performance issues?**
- Reduce date range to smaller period
- Filter to single location
- Close other browser tabs
- Use Chrome or Edge for best performance

---

## 🔒 Privacy & Security

✅ **Your data never leaves your computer** - All processing happens in your browser  
✅ **No server connection required** - Works completely offline  
✅ **No login required** - Just open and use  
✅ **No tracking or analytics** - Zero data collection  
✅ **Local storage only** - Settings saved in your browser  

---

## 💻 System Requirements

**Browser:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+  
**Operating System:** Windows, macOS, Linux  
**Internet:** Only needed to download dashboard file (once)  
**Storage:** ~2MB for dashboard file + your CSV files  

**Not Supported:**
- Internet Explorer (any version)
- Very old mobile browsers

---

## 🆕 What's New in v2.20251115.11

### VSP Performance Analytics
- 📊 Moved to prominent position at top of VSP tab
- 📊 Added conversion rate tracking (intro → paid member by month)
- ⏱️ Added utilization rate tracking (table time efficiency by month)
- 🎨 Implemented colorblind-friendly color scheme (Blue-Orange-Purple)
- 💡 Added detailed hover tooltips for all metrics
- 🔮 Automatic filtering of future dates

### Design Improvements
- Color-coded performance levels with maximum distinction
- Professional table layouts with clear legends
- Enhanced mobile responsiveness
- Improved chart readability

### Bug Fixes
- Fixed future date filtering in analytics
- Improved conversion rate calculations
- Enhanced utilization rate accuracy
- Better handling of missing data

---

## 📖 Need More Details?

For comprehensive documentation including:
- Detailed data requirements and field mappings
- In-depth metric calculations and formulas
- Advanced use cases and workflows
- Marketing campaign templates
- Data validation tips

See **README-Detailed.md**

---

## 📞 Support

For questions or support:
- Contact your franchise administrator
- Check README-Detailed.md for technical details
- Review browser console (F12) for error messages

---

**Thank you for using The Vital Stretch Analytics Dashboard!**

*Version v2.20251115.11 | Created with ❤️ by bonJoeV for The Vital Stretch Franchise*
