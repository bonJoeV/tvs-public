# The Vital Stretch Analytics Dashboard

## Overview
A comprehensive, interactive analytics dashboard designed specifically for The Vital Stretch to track business performance, analyze customer lifetime value, monitor practitioner productivity, and identify strategic opportunities through advanced client segmentation.

## Features

### 📊 Core Analytics
- **Revenue Tracking**: Total revenue, memberships, and payment method breakdown
- **Customer Analytics**: LTV analysis, conversion rates, and customer segmentation
- **Practitioner Performance**: Individual VSP metrics, efficiency scores, and payroll tracking
- **Retention Metrics**: Visit frequency, returning clients, and churn analysis
- **Schedule Optimization**: Appointment heatmaps and capacity utilization

### 🎯 Advanced Client Segmentation
Five strategic client segments with downloadable contact lists:
- **👑 VIP Clients** (>$2,500 LTV)
- **💳 Inactive Paid Members** (Active membership, 30+ days absent)
- **⚠️ At-Risk Clients** (45+ days inactive)
- **🌱 New Clients** (<3 visits)
- **⚡ High-Frequency Clients** (Weekly visitors)

### 🔄 Interactive Features
- Dynamic filters (date range, location, VSP, service)
- Clickable charts with drill-down details
- Comparison periods (previous period, last month, last year)
- CSV exports for all segments and reports
- Real-time calculations and visualizations

---

## Prerequisites

### Momence Setup Requirements

Before exporting data, ensure your Momence account is properly configured:

#### 1. Pay Rates Configuration
Navigate to **Studio Set-up → Pay Rates**
- Create pay rate structures for each VSP level (e.g., Level 1, Level 2, Lead)
- Set hourly rates or per-session rates
- Assign rates to different service types (Table Time, Studio Lead, etc.)

#### 2. Practitioner Setup
Navigate to **Studio Set-up → Practitioners**
- Add all VSPs (Vital Stretch Practitioners)
- Assign each practitioner to their appropriate role/level
- Ensure contact information is complete
- Verify active status for current team members

#### 3. Appointment Pay Rates
Navigate to **Appointments → Boards**
- Set the pay rate for each VSP on the appointment board
- Verify rates are correctly applied to different service types
- Check that special rates (introductory sessions, events) are configured

---

## Data Export Instructions

### Required Reports from Momence

You need to export **three specific reports** from your Momence account. These reports are available in your "Favorite Reports" section.

#### Report 1: Membership Sales
**Report Name:** `Membership sales - A report on membership purchases history`

**What it includes:**
- Purchase history for all memberships
- Customer information
- Membership types and pricing
- Purchase dates and renewal information
- Active/expired/frozen status

**How to Export:**
1. Log in to your Momence account
2. Go to **Reports** section
3. Find "Membership sales" in your Favorite Reports
4. Click the report to open
5. Select your desired date range (recommend: All time for complete history)
6. Click **Download Summary**
7. File saved as `momence-membership-sales-export.csv`)

#### Report 2: New Leads & Customers
**Report Name:** `New Leads & Customers by join date - Report that combines your new leads and customers with join dates, LTV, and aggregator source`

**What it includes:**
- All leads and customers
- Join dates
- Lifetime Value (LTV) for each customer
- Customer type (Lead vs Customer)
- Aggregator source (how they found you)
- First purchase information

**How to Export:**
1. Go to **Reports** section in Momence
2. Find "New Leads & Customers by join date" in Favorite Reports
3. Click the report to open
4. Select date range (recommend: All time)
5. Click **Download Summary**
6. File saved as: `momence-new-leads-and-customers.csv`

#### Report 3: Practitioner Payroll - Appointments
**Report Name:** `Practitioner Payroll - Appointments - Appointment payroll for practitioners`

**What it includes:**
- All completed appointments
- Practitioner information
- Customer information
- Appointment dates and times
- Service types and duration
- Revenue and payroll data
- Payment methods
- Hours worked

**How to Export:**
1. Go to **Reports** section in Momence
2. Find "Practitioner Payroll - Appointments" in Favorite Reports
3. Click the report to open
4. Select your date range (recommend: Last 6-12 months for performance analysis)
5. Click **Download Details**
6. Open the zip file `momence-appointments-payroll-report-summary.zip`
7. Extract `momence-appointments-payroll-report-combined.csv`

### Export Tips
- **Date Range**: For the most comprehensive analysis, export "All time" data
- **File Names**: Keep consistent file names for easy re-uploads
- **Regular Updates**: Export fresh data weekly or monthly to track trends
- **Backup**: Keep copies of your CSV files in a secure location

---

## Setup Instructions

### Step 1: Download the Dashboard
1. Save the `vital-stretch-dashboard.html` file to your computer
2. Choose a location you can easily find (e.g., Desktop or Documents folder)

### Step 2: Prepare Your Data Files
1. Export the three required reports from Momence (see instructions above)
2. Ensure all three CSV files are saved to your computer
3. Recommended file names:
   - `momence-appointments-payroll-report-combined.csv`
   - `momence-membership-sales-export.csv`
   - `momence-new-leads-and-customers.csv`

### Step 3: Open the Dashboard
1. Double-click the `vital-stretch-dashboard.html` file
2. It will open in your default web browser (Chrome, Firefox, Safari, or Edge)
3. The dashboard works entirely in your browser - no internet connection required after opening

### Step 4: Upload Your Data
1. Look for the **"📂 Upload Your Data"** section at the top of the dashboard
2. You'll see three upload boxes:
   - **📅 Appointments & Payroll**
   - **💳 Membership Sales**
   - **👥 Leads & Customers**

3. Click **"Choose File"** on each box and select the corresponding CSV file
4. Wait for the green checkmark (✅) to appear for each file
5. The dashboard will automatically process and display your data

### Step 5: Explore Your Analytics
Once all three files are uploaded:
- The dashboard will automatically populate with your data
- Filters will become available
- All tabs will be accessible
- Charts and metrics will display your business insights

---

## How to Use the Dashboard

### Navigation

The dashboard has **nine main tabs** accessible at the top:

1. **📊 Overview** - Executive summary with key metrics and trends
2. **💳 Memberships** - Membership analysis, revenue, and MRR tracking
3. **🚀 Journey** - Customer acquisition funnel and conversion analysis
4. **🔄 Retention** - Client retention, visit frequency, and churn metrics
5. **⏰ Schedule** - Appointment scheduling patterns and optimization
6. **👥 Customers** - Customer analytics, LTV, and **Advanced Segmentation**
7. **⚕️ VSP** - Practitioner performance, payroll, and efficiency metrics
8. **📈 Timeline** - Historical trends and time-series analysis
9. **💡 Insights** - AI-powered recommendations and action items

### Filters

Use the **🔍 Filters** section to refine your analysis:

- **Month**: Filter by specific month
- **Location**: Filter by studio location
- **VSP**: View data for specific practitioners
- **Service**: Analyze specific service types
- **Date Range**: Custom start and end dates
- **Compare To**: Compare against previous periods

**Quick Filters** (one-click presets):
- Last 7 Days
- Last 30 Days
- Last 90 Days
- This Month
- Last Month
- Reset All

### Advanced Client Segmentation

Located in the **👥 Customers** tab:

#### Viewing Segment Details
1. Navigate to the Customers tab
2. Scroll to the **🎯 Advanced Client Segmentation** section
3. Each segment card shows:
   - Total count
   - Key metrics (revenue, days absent, etc.)
   - Two action buttons

#### Using Segment Actions
**👁️ View Button**
- Opens a detailed modal with client list
- Shows up to 100 clients with full details
- Includes segment summary statistics
- Press Escape, click X, or click outside to close

**📥 Export Button**
- Downloads complete segment list as CSV
- Includes all clients (no 100-client limit)
- Contains: name, email, LTV, visits, membership info
- File is timestamped for easy organization

### Interactive Charts

Many charts are **clickable** - look for the 👆 icon:
- Click on chart segments to drill down into details
- View customer lists, revenue breakdowns, and more
- Modal windows show detailed data tables
- Export detailed data to CSV from modal windows

### Exporting Data

Throughout the dashboard, you'll find **📥 Download CSV** buttons:
- Segment lists with contact information
- Detailed appointment data
- Customer lists with LTV information
- Practitioner performance reports

---

## Data Privacy & Security

### Your Data Stays Local
- **All data processing happens in your browser**
- No data is uploaded to external servers
- No internet connection required after opening the dashboard
- Your business data remains completely private

### File Storage
- CSV files remain on your computer
- Dashboard file works offline
- Re-upload data files each time you open the dashboard
- Consider storing CSV files in a secure, backed-up location

---

## Updating Your Data

### Regular Updates
For ongoing analysis, follow this routine:

**Weekly:**
1. Export fresh Appointments report from Momence
2. Open the dashboard
3. Upload the new Appointments CSV
4. Review Inactive Paid Members segment (Customer tab)
5. Export segment lists for outreach

**Monthly:**
1. Export all three reports from Momence
2. Upload to dashboard
3. Review all segments
4. Compare to previous month using comparison filters
5. Export updated segment lists
6. Review Insights tab for recommendations

### Historical Tracking
- Keep previous exports in dated folders
- Compare month-over-month trends
- Track segment changes over time
- Measure campaign effectiveness

---

## Troubleshooting

### Dashboard Won't Load
- **Solution**: Ensure you're using a modern browser (Chrome, Firefox, Safari, Edge)
- Try opening in a different browser
- Clear browser cache and reload

### File Upload Fails
- **Check file format**: Must be CSV (not Excel .xlsx)
- **Check file size**: Very large files (>10MB) may be slow
- **Check file content**: Ensure headers match Momence export format
- **Re-export**: Try exporting the report again from Momence

### Missing Data or Blank Charts
- **Verify all three files uploaded**: Look for green checkmarks (✅)
- **Check date ranges**: Adjust filters to ensure data is in range
- **Check file contents**: Open CSV in Excel to verify data exists
- **Match file names**: Ensure you're uploading the correct report to correct slot

### Segments Show Zero Clients
- **Upload all files**: Segmentation requires all three CSV files
- **Check membership data**: Inactive Paid Members need membership file
- **Adjust time period**: Use broader date range in filters
- **Verify data**: Check that appointments and customers have matching emails

### Modal Won't Close
- **Try pressing Escape key**
- **Click the X button** in top-right corner
- **Click outside the modal** on the dark overlay
- **Refresh the page** if issue persists

### Charts Not Displaying
- **Wait for data processing**: Large files take 5-10 seconds
- **Scroll down**: Some charts appear below the fold
- **Try different tab**: Some tabs load faster than others
- **Check browser console**: Press F12 to see if errors are displayed

---

## Best Practices

### Data Management
1. **Export consistently**: Same date range strategy each time
2. **Name files clearly**: Include date in filename (e.g., `appointments-2025-11.csv`)
3. **Backup regularly**: Keep copies of all CSV exports
4. **Document changes**: Note any Momence setup changes that affect data

### Analysis Workflow
1. **Start with Overview**: Get the big picture
2. **Identify issues**: Look for red flags in metrics
3. **Drill down**: Use filters and segment analysis
4. **Take action**: Export contact lists for outreach
5. **Track results**: Re-run analysis to measure impact

### Segmentation Strategy
1. **Weekly**: Review Inactive Paid Members for immediate retention action
2. **Bi-weekly**: Check At-Risk segment for re-engagement
3. **Monthly**: Review all segments for targeted campaigns
4. **Quarterly**: Analyze segment migration and trends

### Campaign Tracking
1. **Before campaign**: Export segment lists and note counts
2. **During campaign**: Track outreach and responses separately
3. **After campaign**: Re-export segments to measure changes
4. **Calculate ROI**: Compare revenue changes to campaign costs

---

## Key Metrics Explained

### Lifetime Value (LTV)
- Total revenue generated by a customer across all purchases
- Includes memberships, sessions, packages, and add-ons
- Higher LTV indicates more valuable customers
- Track average LTV trends over time

### Monthly Recurring Revenue (MRR)
- Predictable monthly revenue from active memberships
- Calculated from active, non-frozen subscriptions
- Critical metric for financial planning
- Monitor MRR growth rate monthly

### Customer Acquisition Cost (CAC)
- Total marketing spend divided by new customers
- Compare to LTV for profitability analysis
- Track by acquisition channel
- Aim for LTV:CAC ratio of 3:1 or higher

### Churn Rate
- Percentage of customers who stop visiting
- Calculated monthly based on 90-day inactivity
- Lower churn = better retention
- Industry benchmark: <5% monthly is excellent

### Visit Frequency
- Average visits per customer per month
- Higher frequency = stronger engagement
- Compare across segments
- Use for capacity planning

---

## Support & Resources

### Additional Documentation
- **SEGMENTATION_FEATURES.md**: Detailed guide for client segmentation features
- Included with your dashboard files

### Getting Help
If you encounter issues:
1. Review this README thoroughly
2. Check the Troubleshooting section
3. Verify Momence setup and data exports
4. Try re-exporting fresh data from Momence

### Feature Requests
This dashboard is customized for The Vital Stretch. For additional features or modifications, document your requirements clearly including:
- What data you want to see
- How you want it displayed
- What actions you want to take
- Expected outcomes

---

## Version History

### Version 2.1 (Current)
- Added Inactive Paid Members segment (30+ days, active membership)
- Enhanced modal close functionality
- Added membership information to segment exports
- Improved segmentation grid layout for 5 segments
- Updated summary metrics

### Version 2.0
- Introduced Advanced Client Segmentation
- Added four initial client segments (VIP, At-Risk, New Client, High-Frequency)
- Implemented downloadable segment CSV exports
- Added interactive segment detail modals

### Version 1.0
- Initial release with core analytics
- Nine analytical tabs
- Dynamic filtering system
- Interactive charts and drill-downs

---

## Technical Requirements

### Browsers Supported
- Google Chrome (recommended) - Version 90+
- Mozilla Firefox - Version 88+
- Safari - Version 14+
- Microsoft Edge - Version 90+

### File Requirements
- CSV files from Momence (UTF-8 encoding)
- Maximum recommended file size: 50MB per CSV
- No special characters in file names

### System Requirements
- Any computer capable of running a modern web browser
- Minimum 4GB RAM recommended for large datasets
- No internet connection required after initial download

---

## Privacy & Compliance

### Data Handling
- All processing is client-side (in your browser)
- No data is transmitted to external servers
- No cookies or tracking
- No user accounts or authentication required

### HIPAA Compliance
- While this dashboard doesn't collect health information, be mindful:
- Customer names and emails are visible in segments
- Consider data protection when sharing exported CSVs
- Use secure methods to store and transmit segment exports

### Business Continuity
- Keep regular backups of CSV exports
- Store dashboard HTML file in multiple locations
- Document your Momence setup configurations
- Train multiple team members on dashboard usage

---

## Quick Start Checklist

- [ ] Momence pay rates configured
- [ ] Momence practitioners set up with roles
- [ ] Momence appointment pay rates assigned
- [ ] Exported Membership Sales report
- [ ] Exported New Leads & Customers report
- [ ] Exported Practitioner Payroll report
- [ ] Dashboard HTML file downloaded and saved
- [ ] Dashboard opened in browser
- [ ] All three CSV files uploaded
- [ ] Green checkmarks visible for all uploads
- [ ] Reviewed Overview tab
- [ ] Explored Advanced Client Segmentation
- [ ] Exported first segment list
- [ ] Bookmarked dashboard location
- [ ] Scheduled weekly data updates

---

## Contact & Credits

**Dashboard Version:** 2.1  
**Last Updated:** November 2025  
**Designed for:** The Vital Stretch  

This dashboard is a custom analytical tool built specifically for The Vital Stretch's operational needs. All data remains local to your computer for maximum privacy and security.

---

*For questions about Momence reports or data exports, please contact Momence support directly.*
