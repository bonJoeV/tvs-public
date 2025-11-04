# The Vital Stretch Analytics Dashboard

## Overview
A comprehensive, interactive analytics dashboard designed specifically for The Vital Stretch to track business performance, analyze customer lifetime value, monitor practitioner productivity, and identify strategic opportunities through advanced client segmentation. Features configurable franchise settings for accurate labor cost and profitability tracking.

## Features

### 📊 Core Analytics
- **Revenue Tracking**: Total revenue, memberships, and payment method breakdown
- **Financial Performance**: Net profit with comprehensive labor cost tracking (appointment + non-appointment)
- **Labor Cost Management**: Configurable base hourly rate for accurate profitability calculations
- **Customer Analytics**: LTV analysis, conversion rates, and customer segmentation
- **Practitioner Performance**: Individual VSP metrics, efficiency scores, payroll tracking, and commission tracking
- **Retention Metrics**: Visit frequency, returning clients, and churn analysis
- **Schedule Optimization**: Appointment heatmaps with detailed drill-down and capacity utilization
- **Utilization Tracking**: Real-time efficiency metrics showing table time vs clocked time

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
- **Enhanced heatmap interactions**: Click days for hourly breakdown, click hours for appointment details
- **Visible trendlines**: High-contrast trendlines on all time-series charts (colorblind-friendly)
- **Monthly goal tracking**: Visual column charts showing monthly progress vs goals
- **Configurable franchise settings**: Persistent settings for accurate cost calculations

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

### Required Data from Momence

You need to export **three specific reports** from your Momence account, plus **one optional payroll zip file** for advanced metrics.

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
7. File saved as `momence-membership-sales-export.csv`

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

#### Report 3: Payroll Zip File with Time Tracking & Commissions
**Report Name:** `Practitioner Payroll - Multiple practitioners payroll details`

**What it includes:**
- **Time tracking data**: Clocked in/out times and durations for each VSP
- **Commission data**: Membership and product sales commissions per VSP
- **Appointments data**: Detailed appointment records per VSP
- Individual CSV files for each practitioner
- All completed appointments
- Practitioner information
- Customer information
- Appointment dates and times
- Service types and duration
- Revenue and payroll data
- Payment methods
- Hours worked

**What this enables:**
- **Utilization metrics**: See efficiency of table time vs clocked time
- **Commission tracking**: Track VSP earnings from memberships and products
- **Advanced analytics**: Deeper insights into team productivity

**How to Export:**
1. Go to **Reports** section in Momence
2. Find "Practitioner Payroll"
3. Select **multiple practitioners** (select all VSPs)
4. Select your date range
5. Click **Download Details**
6. File saved as: `momence-payroll-report-summary.zip`
7. **Upload the entire ZIP file** to the dashboard (do not extract)

**Important Notes:**
- This zip file contains individual CSV files for each practitioner
- Includes time tracking files (clocked hours)
- Includes commission files (membership & product sales)
- The dashboard will automatically parse all files
- Special characters in product names (®, ™, ©, Â) are automatically cleaned

### Export Tips
- **Date Range**: For the most comprehensive analysis, export "All time" data
- **File Names**: Keep consistent file names for easy re-uploads
- **Regular Updates**: Export fresh data weekly or monthly to track trends
- **Backup**: Keep copies of your CSV files in a secure location
- **Payroll Zip**: Upload weekly for most accurate utilization tracking

---

## Setup Instructions

### Step 1: Download the Dashboard
1. Save the `vital-stretch-dashboard.html` file to your computer
2. Choose a location you can easily find (e.g., Desktop or Documents folder)

### Step 2: Prepare Your Data Files
1. Export the three required reports from Momence (see instructions above)
2. Optionally export the payroll zip file for advanced metrics
3. Ensure all files are saved to your computer
4. Recommended file names:
   - `momence-membership-sales-export.csv`
   - `momence-new-leads-and-customers.csv`
   - `momence-payroll-report-summary.zip`

### Step 3: Open the Dashboard
1. Double-click the `vital-stretch-dashboard.html` file
2. It will open in your default web browser (Chrome, Firefox, Safari, or Edge)
3. The dashboard works entirely in your browser - no internet connection required after opening

### Step 4: Upload Your Data
1. Look for the **"📂 Upload/Set Your Franchise Data"** section at the top of the dashboard
2. You'll see three upload boxes:
   - **💳 Membership Sales**
   - **👥 Leads & Customers**
   - **📦 Payroll Zip** - For utilization & commission tracking

3. Click **"Choose File"** on each box and select the corresponding file
4. Wait for the green checkmark (✅) to appear for each file
5. The dashboard will automatically process and display your data

### Step 5: Configure Your Franchise Settings
Once files are uploaded, a new section appears:
1. Look for the **"⚙️ Franchise Configuration"** section
2. Set your **Base Hourly Rate** for non-appointment work (default: $13.00/hour)
   - This is the rate paid for cleaning, admin, training, and other non-appointment tasks
   - Used to calculate total labor costs accurately
3. Click **"💾 Save Configuration"**
4. Your setting is saved and will persist across sessions
5. Update this rate anytime your pay structure changes

### Step 6: Explore Your Analytics
Once files are uploaded:
- The dashboard will automatically populate with your data
- Filters will become available
- All tabs will be accessible
- Charts and metrics will display your business insights
- Utilization and commission metrics appear when zip file is uploaded

---

## How to Use the Dashboard

### Navigation

The dashboard has **nine main tabs** accessible at the top (optimized order for studio owners):

1. **📊 Overview** - Executive summary with key metrics, comprehensive financial performance tracking, and labor cost breakdown
2. **📈 Timeline** - Historical trends and time-series analysis
3. **⚕️ VSP** - Practitioner performance, payroll, efficiency, utilization, and commissions
4. **👥 Customers** - Customer analytics, LTV, and **Advanced Segmentation**
5. **🔄 Retention** - Client retention, visit frequency, and churn metrics
6. **🚀 Journey** - Customer acquisition funnel and conversion analysis
7. **💳 Memberships** - Membership analysis, revenue, and MRR tracking
8. **⏰ Schedule** - Appointment scheduling patterns and optimization
9. **💡 Insights** - AI-powered recommendations, action items, and monthly goal tracking with visual column charts

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

**Important:** All metrics respect filters, including:
- Utilization calculations update based on date range
- Commission totals filter by date
- Timeline charts adjust to filtered data

### Overview Tab

**Key Metrics (Prioritized Order):**
1. **Total Revenue** - Your bottom line
2. **Appointments** - Volume indicator
3. **Unique Clients** - Customer base size
4. **Utilization** - Team efficiency (appears when zip uploaded)
5. **Revenue/Hour** - Operational efficiency
6. **Avg Ticket Size** - Transaction value
7. **Client Frequency** - Loyalty indicator
8. **Revenue per VSP** - Team productivity
9. **Busiest Day** - Scheduling insights
10. **Top Paid Service** - Product mix
11. **Membership Metrics** - Recurring revenue (when available)

### Timeline Tab

**Charts (Business Priority Order):**
1. **Daily Revenue Trend** - Financial health
2. **Daily Appointments** - Business volume
3. **Daily Utilization Trend** - Team efficiency (when available)
4. **Cumulative Revenue** - Growth tracking
5. **Daily Profit Trend** - Profitability
6. **Daily Revenue per Appointment** - Efficiency
7. **New vs Returning Clients** - Customer mix
8. **Daily Hours Worked** - Operations
9. **Weekly Membership Sales Trend** - Recurring revenue
10. **Weekly Average Membership Sale Value** - Membership performance

**Note:** The membership average chart now shows **weekly averages** instead of monthly for better granularity.

### VSP Tab - Practitioner Performance

**Leaderboard System:**
- Comprehensive scoring based on revenue, efficiency, utilization, and commissions
- Ranked cards showing top performers
- Detailed metrics for each VSP

**Key Metrics:**
- Revenue and appointments
- Efficiency (revenue per hour)
- Client count and satisfaction
- **Utilization percentage** (table time vs clocked time)
- **Commission earnings** (memberships & products only)
- Profit margins

**Commission Tracking:**
- Shows total commissions from membership and product sales
- Individual VSP commission breakdowns
- Filters by date range
- Excludes other commission types automatically

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

- **Revenue by Service**: Click to see practitioner breakdown
- **LTV Distribution**: Click bars to see customer lists
- **Retention Segments**: Click to view customers in each tier
- **Schedule Heatmap**: 
  - Click **day names** (row headers) to see hourly breakdown for that day
  - Click **hour cells** to see individual appointments with dates, customer names, and revenue

---

## New Features Explained

### Utilization Tracking

**What it is:**
- Measures efficiency of table time vs clocked-in time
- Shows how much of a VSP's shift is spent with clients
- Calculated as: (Appointment Hours / Clocked Hours) × 100

**Where it appears:**
- **Overview Tab**: Average utilization across all VSPs
- **Timeline Tab**: Daily utilization trend chart
- **VSP Tab**: Individual VSP utilization percentages

**How to enable:**
- Upload the payroll zip file (Report 4)
- Must include time tracking data
- Automatically calculates and updates with filters

**Typical benchmarks:**
- 70-85%: Excellent utilization
- 60-70%: Good utilization
- Below 60%: May indicate scheduling inefficiencies

### Commission Tracking

**What it includes:**
- Membership sales commissions
- Product sales commissions (e.g., Stretch Out Strap)
- Excludes appointment/service commissions

**Where it appears:**
- **Overview Tab**: Total commissions metric (when available)
- **VSP Tab**: Individual VSP commission earnings
- **VSP Leaderboard**: Commission amounts in VSP cards
- **Detailed Performance Table**: Commission column

**Features:**
- Product names automatically cleaned (removes ®, ™, ©, Â)
- Filters by date range
- Includes in VSP performance scoring
- CSV export available

**How to enable:**
- Upload the payroll zip file (Report 4)
- Must include commission CSV files
- Only Membership and Product types tracked

### Labor Cost Tracking

**What it is:**
- Comprehensive labor cost calculation including non-appointment work
- Tracks both commission-based pay (appointments) and hourly base pay (admin/cleaning)
- Provides accurate profitability metrics for business decisions

**Components:**
- **Appointment-Based Labor**: Commission payouts for client time
- **Non-Appointment Labor**: Base rate × (Clocked Hours - Appointment Hours)
- **Total Labor Cost**: Sum of both components

**Configuration:**
1. Navigate to **⚙️ Franchise Configuration** (appears after uploading data)
2. Set your **Base Hourly Rate** (default: $13.00/hour)
3. This is the rate paid for:
   - Cleaning and maintenance
   - Administrative work
   - Training and meetings
   - Any clocked time without appointments
4. Click **"💾 Save Configuration"**
5. Setting is saved to your browser (persists across sessions)

**Where it appears:**
- **Overview Tab**: Financial Performance section with detailed breakdown
- **Insights Tab**: Updated profit calculations
- **Net Profit**: Now reflects true total labor costs
- **Labor as % of Revenue**: Key metric for margin management

**Key insights:**
- See how much non-appointment work costs your business
- Identify opportunities to reduce admin time
- Make informed decisions about staffing levels
- Track profitability trends more accurately

**Best practices:**
- Update base rate when pay structure changes
- Monitor labor percentage (target: <50% of revenue)
- Compare appointment vs non-appointment hours
- Use insights to optimize scheduling

---

## Troubleshooting

### Dashboard Won't Load
- **Solution**: Ensure you're using a modern browser (Chrome, Firefox, Safari, Edge)
- Try opening in a different browser
- Clear browser cache and reload

### File Upload Fails
- **Check file format**: Must be CSV (or ZIP for payroll)
- **Check file size**: Very large files (>10MB) may be slow
- **Check file content**: Ensure headers match Momence export format
- **Re-export**: Try exporting the report again from Momence

### Zip File Not Processing
- **Verify it's a ZIP**: Should be `momence-payroll-report-summary.zip`
- **Don't extract**: Upload the ZIP file directly
- **Check contents**: Should contain individual practitioner CSV files
- **Wait**: Processing multiple files takes 5-10 seconds

### Missing Utilization Metrics
- **Upload payroll zip**: Utilization requires time tracking data
- **Check date range**: Ensure clocked hours exist in filtered period
- **Verify time data**: Open zip to confirm time tracking CSVs exist
- **Re-upload**: Try uploading the zip file again

### Missing Commission Data
- **Upload payroll zip**: Commissions are in individual practitioner files
- **Check commission files**: Look for "commissions-" files in zip
- **Verify date range**: Filter to period where commissions exist
- **Product names**: Special characters are automatically cleaned

### Missing Data or Blank Charts
- **Verify all files uploaded**: Look for green checkmarks (✅)
- **Check date ranges**: Adjust filters to ensure data is in range
- **Check file contents**: Open CSV in Excel to verify data exists
- **Match file names**: Ensure you're uploading the correct report to correct slot

### Segments Show Zero Clients
- **Upload all files**: Segmentation requires all three CSV files
- **Check membership data**: Inactive Paid Members need membership file
- **Adjust time period**: Use broader date range in filters
- **Verify data**: Check that appointments and customers have matching emails

### Configuration Not Saving
- **Check browser storage**: Ensure cookies/local storage is enabled
- **Re-enter rate**: Click "Save Configuration" again
- **Verify confirmation**: Look for green success message
- **Browser compatibility**: Try Chrome or Firefox if issues persist
- **Clear cache**: If rate seems incorrect, clear browser cache and reconfigure

### Labor Costs Not Showing
- **Upload payroll zip**: Non-appointment labor requires time tracking data
- **Set base rate**: Configure your base hourly rate in ⚙️ Franchise Configuration
- **Check time data**: Ensure time tracking CSVs are in the payroll zip
- **Verify calculations**: Non-appt hours = Clocked hours - Appointment hours

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
5. **Weekly zip uploads**: Update payroll zip weekly for accurate utilization

### Analysis Workflow
1. **Start with Overview**: Get the big picture
2. **Check Timeline**: Identify trends and patterns
3. **Review VSP Performance**: Monitor team productivity and efficiency
4. **Analyze Customers**: Understand client behavior and segments
5. **Take action**: Export contact lists for outreach
6. **Track results**: Re-run analysis to measure impact

### Utilization Monitoring
1. **Daily**: Check if utilization drops below 60%
2. **Weekly**: Review VSP utilization trends
3. **Monthly**: Analyze scheduling efficiency opportunities
4. **Quarterly**: Set utilization targets and track progress

### Commission Tracking
1. **Weekly**: Review individual VSP commission performance
2. **Monthly**: Track commission trends and incentives
3. **Quarterly**: Analyze product vs membership commission mix

### Segmentation Strategy
1. **Weekly**: Review Inactive Paid Members for immediate retention action
2. **Bi-weekly**: Check At-Risk segment for re-engagement
3. **Monthly**: Review all segments for targeted campaigns
4. **Quarterly**: Analyze segment migration and trends

---

## Key Metrics Explained

### Labor Costs
- **Appointment-Based Labor**: Commission payouts for time spent with clients
- **Non-Appointment Labor**: Base hourly rate × (Clocked Hours - Appointment Hours)
- **Total Labor Cost**: Sum of both appointment and non-appointment labor
- **Labor as % of Revenue**: Total Labor Cost ÷ Total Revenue × 100
- **Target Range**: Keep total labor below 50% of revenue for healthy margins
- **Configure**: Set your base hourly rate in ⚙️ Franchise Configuration

### Net Profit
- **Definition**: Total Revenue - Total Labor Costs
- **Includes**: All labor costs (appointment commissions + non-appointment base pay)
- **Enhanced Calculation**: Now accounts for cleaning, admin, and training hours
- **Target Margin**: Aim for 25-35% profit margin after all labor costs
- **Use Cases**: Financial planning, pricing strategy, cost optimization

### Utilization
- **Definition**: Percentage of clocked hours spent with clients on the table
- **Formula**: (Appointment Hours / Clocked Hours) × 100
- **Good Range**: 70-85%
- **Use Cases**: Scheduling optimization, staffing decisions, VSP performance

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

### Commissions
- **Membership Commissions**: Earnings from membership sales
- **Product Commissions**: Earnings from retail product sales
- **Excludes**: Service/appointment commissions
- **Used For**: VSP incentive tracking, performance bonuses

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

## Version History

### Version 2.20251103.05 (Current)
**Major Updates:**
- **Added**: ⚙️ Franchise Configuration section
  - User-configurable base hourly rate for non-appointment work
  - Default: $13.00/hour (adjustable)
  - Persistent settings saved to browser
  - Form-based input with validation and confirmation
- **Enhanced**: Comprehensive labor cost tracking
  - Total Labor Cost = Appointment Payouts + Non-Appointment Labor
  - Non-appointment hours calculated automatically (clocked - appointment hours)
  - New Financial Performance section in Overview tab
  - Detailed labor cost breakdown with explanations
  - Updated profit calculations across all tabs
- **Improved**: Trendline visibility for colorblind accessibility
  - Increased opacity from 30% to 70%
  - Increased line width from 2px to 3px
  - Applied to all 7 time-series charts
- **Enhanced**: Heatmap interactivity
  - Click day names to see hourly breakdown
  - Click hour cells to see individual appointments with dates, names, and values
  - Clear instructions for different click behaviors
- **Added**: Monthly goal column charts
  - Replaced progress bars with visual column charts
  - Shows monthly revenue vs goal by month
  - Shows monthly appointments vs goal by month
  - Historical trend tracking
- **Improved**: Weekly average notation on membership charts
  - Clear labeling showing data represents weekly averages
  - Subtitle explanation added
- **Renamed**: "Upload Your Data" → "Upload/Set Your Franchise Data"
- **Updated**: All profitability metrics use comprehensive labor costs

### Version 2.20251103.04
**Major Updates:**
- **Removed**: Net Profit metric from Overview tab
- **Added**: Utilization tracking throughout dashboard
  - Overview tab: Average utilization metric
  - Timeline tab: Daily utilization trend chart
  - VSP tab: Individual utilization percentages
- **Added**: Commission tracking to VSP tab
  - Total commissions metric card
  - Individual VSP commission tracking
  - Membership & Product commissions only
  - Automatic special character cleaning in product names
- **Changed**: Membership average chart now shows weekly averages
- **Improved**: Tab order prioritized for studio owners/managers
- **Improved**: Overview metrics reordered by business priority
- **Improved**: Timeline charts reordered by decision-making importance
- **Enhanced**: All utilization and commission metrics respect date filters
- **Enhanced**: Payroll zip file processing for time tracking and commissions

### Version 2.20251103.03
- Enhanced modal interactions
- Improved chart rendering

### Version 2.20251102.33
- Added Inactive Paid Members segment (30+ days, active membership)
- Enhanced modal close functionality
- Added membership information to segment exports
- Improved segmentation grid layout for 5 segments
- Updated summary metrics

### Version 2.20251102.11
- Introduced Advanced Client Segmentation
- Added four initial client segments (VIP, At-Risk, New Client, High-Frequency)
- Implemented downloadable segment CSV exports
- Added interactive segment detail modals

### Version 2.20251101.16
- Initial release with core analytics
- Nine analytical tabs
- Dynamic filtering system
- Interactive charts and drill-downs

### Version 1.010
- Initial release with API integration to Momence
- Four analytical tabs
- Charts and tables
- Terminated due to Momence API issues

---

## Technical Requirements

### Browsers Supported
- Google Chrome (recommended) - Version 90+
- Mozilla Firefox - Version 88+
- Safari - Version 14+
- Microsoft Edge - Version 90+

### File Requirements
- CSV files from Momence (UTF-8 encoding)
- ZIP file for payroll data (optional, but recommended)
- Maximum recommended file size: 50MB per CSV, 100MB for ZIP
- No special characters in file names

### System Requirements
- Any computer capable of running a modern web browser
- Minimum 4GB RAM recommended for large datasets
- No internet connection required after initial download
- Additional RAM helpful when processing large ZIP files

---

## Privacy & Compliance

### Data Handling
- All processing is client-side (in your browser)
- No data is transmitted to external servers
- No cookies or tracking
- No user accounts or authentication required
- ZIP file processing happens entirely in browser

### HIPAA Compliance
- While this dashboard doesn't collect health information, be mindful:
- Customer names and emails are visible in segments
- Consider data protection when sharing exported CSVs
- Use secure methods to store and transmit segment exports
- Time tracking and commission data is sensitive

### Business Continuity
- Keep regular backups of CSV exports
- Store dashboard HTML file in multiple locations
- Document your Momence setup configurations
- Train multiple team members on dashboard usage

---

## Quick Start Checklist

**Initial Setup:**
- [ ] Momence pay rates configured
- [ ] Momence practitioners set up with roles
- [ ] Momence appointment pay rates assigned
- [ ] Dashboard HTML file downloaded and saved
- [ ] Dashboard opened in browser

**Required Data Exports:**
- [ ] Exported Membership Sales report
- [ ] Exported New Leads & Customers report
- [ ] Exported Practitioner Payroll report
- [ ] All three CSV files uploaded
- [ ] Green checkmarks visible for all uploads

**Configuration:**
- [ ] Set base hourly rate in ⚙️ Franchise Configuration
- [ ] Verified labor cost calculations appear correctly
- [ ] Confirmed Financial Performance section shows in Overview

**Optional Advanced Features:**
- [ ] Exported Payroll Zip file (for utilization & commissions)
- [ ] Uploaded ZIP file to dashboard
- [ ] Verified utilization metrics appear
- [ ] Verified commission tracking appears

**Getting Started:**
- [ ] Reviewed Overview tab
- [ ] Checked Timeline for trends
- [ ] Explored VSP performance and commissions
- [ ] Explored Advanced Client Segmentation
- [ ] Exported first segment list
- [ ] Bookmarked dashboard location
- [ ] Scheduled weekly data updates

---

## Contact & Credits

**Dashboard Version:** 2.5  
**Last Updated:** November 2025  
**Designed for:** The Vital Stretch  
**Created by:** bonJoeV with ❤️

This dashboard is a custom analytical tool built specifically for The Vital Stretch's operational needs. All data remains local to your computer for maximum privacy and security.

---

*For questions about Momence reports or data exports, please contact Momence support directly.*
