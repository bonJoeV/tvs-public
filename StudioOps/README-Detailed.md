# The Vital Stretch Analytics Dashboard - Detailed Documentation

**Version:** v2.20251105.5 | **Updated:** November 5, 2025

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Files Explained](#data-files-explained)
3. [Dashboard Tabs Deep Dive](#dashboard-tabs-deep-dive)
4. [Advanced Features](#advanced-features)
5. [Filtering & Data Processing](#filtering--data-processing)
6. [Calculations & Formulas](#calculations--formulas)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Performance Optimization](#performance-optimization)
9. [Browser Compatibility](#browser-compatibility)
10. [Version History](#version-history)

---

## System Architecture

### Technology Stack
- **Frontend:** Pure HTML5, CSS3, vanilla JavaScript
- **Charts:** Chart.js v4.4.0
- **CSV Parsing:** PapaParse v5.4.1
- **ZIP Processing:** JSZip v3.10.1
- **No Backend:** All processing happens client-side

### How It Works
1. User uploads CSV/ZIP files
2. Dashboard parses files using PapaParse
3. Data is stored in browser memory
4. Filters are applied dynamically
5. Charts render using Chart.js
6. Settings saved to localStorage

### Data Flow
```
User uploads file
    ↓
File validation
    ↓
CSV parsing / ZIP extraction
    ↓
Data transformation
    ↓
Store in memory (global variables)
    ↓
Apply filters
    ↓
Calculate metrics
    ↓
Render UI
    ↓
Update charts
```

### Security & Privacy
- **Zero server communication** - no data uploaded anywhere
- **Client-side only** - everything happens in your browser
- **Local storage** - only settings stored locally
- **No tracking** - no analytics or telemetry
- **Open file** - you can inspect the code

---

## Data Files Explained

### Required Files (4)

#### 1. Membership Sales Export
**File:** `momence--membership-sales-export.csv`
**Momence Report:** "Membership sales - A report on membership purchases history"

**Key Fields:**
- `Bought Date/Time (GMT)` - When membership was purchased
- `Product name` - Name of membership plan
- `Paid Amount` - Revenue from membership
- `Frequency` - Billing frequency (monthly, annual, etc.)
- `Customer Email` - Primary key for customer matching
- `Customer Name` - Display name
- `Home location` - Location assignment
- `Status` - Active/Cancelled
- `Sold by` - Staff member who sold it

**Used For:**
- MRR (Monthly Recurring Revenue) calculation
- Active membership tracking
- Membership growth trends
- Revenue attribution
- Staff performance on sales

#### 2. Membership Cancellations Export
**File:** `momence--membership-sales-export__1_.csv`
**Momence Report:** "Membership sales" → Cancellations tab

**Key Fields:**
- `Bought Date/Time (GMT)` - Original purchase date
- `Product name` - Membership plan name
- `Customer Email` - For matching to active members
- `Cancellation Date` - When they cancelled
- `Cancellation Reason` - Why they cancelled
- `Paid Amount` - Value of lost MRR

**Used For:**
- Churn rate calculation
- Cancellation reason analysis
- Lost MRR tracking
- Retention insights
- Customer lifecycle analysis

#### 3. New Leads & Customers
**File:** `momence-new-leads-and-customers.csv`
**Momence Report:** "New Leads & Customers by join date"

**Key Fields:**
- `E-mail` - Primary key
- `First name`, `Last name` - Customer info
- `Type` - "Lead" or "Customer"
- `Join date` - When they joined
- `Lead source` - How they found you
- `LTV` - Lifetime value
- `Home location` - Location assignment

**Used For:**
- Lead generation tracking
- Customer acquisition trends
- Lead source effectiveness
- LTV analysis
- Customer segmentation

#### 4. Practitioner Payroll ZIP
**File:** `momence-payroll-report-summary.zip`
**Momence Report:** "Practitioner Payroll - Multiple practitioners payroll details"

**Contains Multiple Files Per Practitioner:**
- `momence-payroll-appointments-[name].csv` - Appointment details
- `momence-payroll-appointments-[name]-aggregate.csv` - Appointment summary
- `momence-payroll-time-[name].csv` - Clock in/out records
- `momence-payroll-commissions-[name].csv` - Commission data

**Appointment File Fields:**
- `Appointment Date` - When appointment occurred
- `Customer Email` - Client identifier
- `Customer Name` - Display name
- `Appointment` - Service name
- `Revenue` - Payment amount
- `Time (h)` - Duration in hours
- `Total Payout` - VSP compensation
- `Practitioner First Name`, `Practitioner Last Name` - VSP info
- `Location` - Where service was performed
- `Late cancellations` - Yes/No flag

**Time Tracking File Fields:**
- `Clocked in` - Clock in timestamp
- `Clocked out` - Clock out timestamp
- `Duration (h)` - Hours worked
- `Hourly Rate` - Pay rate
- `Payout` - Amount earned

**Commission File Fields:**
- `Commission Date` - When commission earned
- `Item name` - Product/membership sold
- `Item type` - "Membership" or "Product"
- `Item price` - Sale amount
- `Commission earned` - VSP commission

**Used For:**
- Appointment revenue tracking
- VSP performance metrics
- Utilization calculation (appointment hours vs clocked hours)
- Non-appointment labor cost tracking
- Commission tracking
- Location-specific metrics
- Schedule optimization

### Optional Files (2)

#### 5. Leads Converted Report
**File:** `momence-leads-converted-report.csv`
**Momence Report:** "Leads converted" or "Lead Conversion Report"

**Key Fields:**
- `First Name`, `Last Name` - Lead info
- `E-mail` - Primary key
- `Lead source` - Acquisition channel
- `Converted` - Conversion date
- `Converted to` - What they converted to (membership, package, etc.)
- `LTV` - Lifetime value post-conversion

**Used For:**
- Lead conversion rate tracking
- Source effectiveness analysis
- Conversion timeline analysis
- LTV by lead source
- Marketing ROI calculation

**Benefits:**
- More accurate conversion tracking than just type changes
- Understand which sources convert best
- Track time-to-conversion
- Optimize marketing spend

#### 6. Appointments Attendance Report ZIP
**File:** `momence-appointments-attendance-report-summary.zip`
**Momence Report:** "Appointments attendance report"

**Contains:**
- `momence-appointments-attendance-report-combined.csv` - Full attendance records
- `momence-appointments-attendance-report-aggregate-combined.csv` - Summary data
- Individual VSP attendance files

**Combined File Fields:**
- `Staff Name` - VSP name (used for mapping)
- `Staff E-mail` - VSP email
- `Time booked (h)` - Hours of appointments
- `Total time (h)` - Total clocked hours
- `First Name`, `Last Name` - Client info
- `E-mail` - Client email
- `Date of reservation` - Appointment date/time
- `Is paid` - Payment status (Yes/No)

**Used For:**
- Booking pipeline visibility (upcoming appointments)
- Most frequent client identification
- VSP workload analysis
- Payment status tracking
- Client loyalty metrics
- Future revenue projection
- VSP name mapping (cleaner reports)

**New Features Unlocked:**
- **Attendance Analytics** section in Insights tab
- Top 10 most frequent clients
- Top VSPs by appointments booked
- Upcoming appointments count
- Paid vs unpaid reservation breakdown
- Booking pipeline strength indicator

---

## Dashboard Tabs Deep Dive

### 1. Overview Tab 📊

**Purpose:** High-level business snapshot

**Key Metrics:**
- **Total Revenue** - Appointment revenue + membership revenue
  - Excludes active member appointment revenue (to avoid double-counting)
- **Total Appointments** - Count of all appointments
- **Unique Clients** - Distinct customer emails
- **Avg Revenue/Appt** - Total revenue ÷ appointment count

**Financial Performance Section:**
- **Net Profit** - Revenue - labor - franchise fees
- **Profit Margin** - (Net profit ÷ revenue) × 100
- **Total Labor Cost** - Appointment payouts + non-appointment labor
- **Appointment Payouts** - Direct VSP compensation from appointments
- **Non-Appt Labor** - (Clocked hours - appointment hours) × base hourly rate

**How Non-Appt Labor is Calculated:**
1. Get all clocked time from payroll ZIP
2. Sum total clocked hours for filtered period/location
3. Sum total appointment hours for same period/location
4. Non-appt hours = Clocked hours - Appointment hours
5. Cost = Non-appt hours × base hourly rate (from settings)

**Franchise Fees Section:**
- Franchise Fee (default 6%)
- Brand Fund (default 2%)
- Credit Card Processing (default 3%)
- Total Fees
- Impact on profit calculation

**Period Comparison:**
- When filtering by specific month, shows comparison to previous month
- Comparison indicators: ↑ (increase), ↓ (decrease)
- Percentage change calculation

**Intro Appointments:**
- Counts appointments with "intro" in service name
- Tracked separately from paid appointments

### 2. Timeline Tab 📈

**Purpose:** Trend analysis over time

**Charts:**
- **Revenue Trend** - Daily revenue with 7-day moving average
- **Appointments Trend** - Daily appointment count
- **MRR Trend** - Monthly recurring revenue over time
- **Avg Ticket Trend** - Average revenue per appointment

**Features:**
- Interactive charts (click for details)
- Date range filtering
- Location filtering
- Export to CSV

**Time Grouping:**
- Less than 60 days: Daily
- 60-180 days: Weekly
- More than 180 days: Monthly

### 3. VSP Performance Tab 👥

**Purpose:** Individual practitioner metrics

**Metrics Per VSP:**
- Total Revenue Generated
- Number of Appointments
- Average Revenue per Appointment
- Total Hours Worked
- Total Payout Earned
- Commission Earned (if data available)
- Utilization Rate (if time tracking available)

**Utilization Calculation:**
```
Utilization = (Appointment Hours ÷ Clocked Hours) × 100
```

**Sorting:**
- By revenue (default)
- By appointments
- By utilization
- By commission

**Filtering:**
- By location
- By date range
- Search by name

### 4. Customers Tab 🧑‍🤝‍🧑

**Purpose:** Client analysis and segmentation

**Demographics:**
- Total Customers
- New Customers (this period)
- Active Members
- Visit distribution (1 visit, 2-3 visits, 4-10, 11+)

**LTV Analysis:**
- LTV Distribution chart (6 tiers)
- Click any tier to see customers in that range
- Export customer lists

**Client Segmentation (5 Segments):**

1. **VIP Clients**
   - Criteria: 10+ visits OR LTV > $1,000
   - Action: Reward loyalty, create VIP program

2. **New Clients**
   - Criteria: 1-3 visits in past 30 days
   - Action: Follow-up campaigns, intro packages

3. **At-Risk Clients**
   - Criteria: No visit in 60+ days, historically active
   - Action: Re-engagement campaigns, special offers

4. **Inactive Paid Members**
   - Criteria: Active membership, no appointments in 30+ days
   - Action: Urgent follow-up, prevent churn

5. **High-Frequency Non-Members**
   - Criteria: 5+ visits, no active membership
   - Action: Membership conversion campaigns

**Export Features:**
- Click any segment to see details
- Export segment as CSV with contact info
- Use for email campaigns, CRM imports

### 5. Retention Tab 🔄

**Purpose:** Analyze customer retention and churn

**Metrics:**
- **Retention Rate** - Percentage of customers who return
- **Churn Rate** - Percentage of members who cancel
- **Avg Customer Lifetime** - Average days as active customer

**Cohort Analysis:**
- Groups customers by join month
- Tracks retention month-over-month
- Color-coded heatmap (green = good, red = bad)

**Churn Analysis:**
- Monthly churn rate trend
- Churn by location
- Churn by membership type

### 6. Journey Tab 🚀

**Purpose:** Customer lifecycle funnel

**Stages:**
1. **Leads** - Prospects in system
2. **Converted Leads** - Leads who became customers
3. **First Appointment** - Completed intro/first visit
4. **Repeat Customer** - 2+ appointments
5. **Member** - Active membership holder

**Conversion Rates:**
- Lead → Customer
- Customer → Repeat
- Repeat → Member

**Drop-off Analysis:**
- Shows where customers are lost
- Helps identify friction points
- Optimization opportunities

### 7. Memberships Tab 💳

**Purpose:** Subscription business tracking

**Key Metrics:**
- **MRR (Monthly Recurring Revenue)** - Sum of active membership values
- **Active Members** - Count of active subscriptions
- **Avg Membership Value** - MRR ÷ active members
- **MRR Growth Rate** - Month-over-month change

**MRR Calculation:**
- Only counts active memberships (Status = "Active")
- Normalizes to monthly value:
  - Annual: Paid Amount ÷ 12
  - Quarterly: Paid Amount ÷ 3
  - Monthly: Paid Amount

**Charts:**
- MRR Trend over time
- Members by Type (pie chart)
- MRR by Location (if multi-location)

**Membership Analysis:**
- Top membership types by revenue
- Top membership types by count
- Growth trends

### 8. Cancellations Tab ❌

**Purpose:** Understand and reduce churn

**Metrics:**
- Total Cancellations
- Cancellation Rate
- Lost MRR
- Avg Time to Cancel

**Cancellation Reasons:**
- Chart showing top reasons
- Click for detailed list
- Export for follow-up

**Patterns:**
- Cancellations by month
- Cancellations by location
- Cancellations by membership type

**Win-Back Opportunities:**
- Recent cancellations (< 30 days)
- High-value cancellations
- Exportable contact lists

### 9. Schedule Tab 📅

**Purpose:** Optimize scheduling and staffing

**Key Features:**

**Appointment Heatmap by Location:**
- Separate heatmap for each location
- Shows busiest times by day (Monday-Saturday) and hour (6am-9pm)
- Color intensity shows appointment volume
- Click any cell for detailed appointment list
- Click day name for hourly breakdown

**How to Use:**
- Identify peak times for staffing
- Find scheduling gaps
- Optimize practitioner schedules
- Plan marketing for slow times

**Schedule Optimization Insights:**
- Average utilization rate
- Total gap hours
- Cost of gaps (lost revenue)
- Potential additional revenue

**Gap Analysis Table:**
- Top 20 days with largest scheduling gaps
- Shows practitioner, date, gaps, utilization
- Opportunity value calculation

### 10. Insights Tab 💡

**Purpose:** Actionable recommendations and goal tracking

**Monthly Goal Tracking:**
- Revenue vs Goal (bar chart)
- Appointments vs Goal (bar chart)
- Intro Appointments vs Goal (bar chart)
- Progress percentages
- Gap calculations

**Key Insights:**
- Profit margin analysis
- Client retention rate
- Top service performance
- Revenue per client
- Client engagement metrics

**Attendance Analytics** (when attendance data loaded):
- Total reservations count
- Upcoming appointments (booking pipeline)
- Paid vs unpaid breakdown
- Top 10 most frequent clients
- Top VSPs by appointments booked
- Booking pipeline health indicator

**AI Recommendations:**
- Priority-ranked action items
- Based on your actual data
- Estimated impact
- Specific action plans
- Categories: High/Medium/Low priority

**Action Items:**
- Weekly recommended actions
- Follow-up campaigns
- Package creation suggestions
- Schedule optimization tips
- Referral program ideas

### 11. Leads Tab 🎯

**Purpose:** Lead tracking and conversion (requires Leads Converted report)

**Key Metrics:**
- Total Leads
- Conversion Rate
- Avg Time to Convert
- Total LTV from Conversions

**Lead Source Analysis:**
- Leads by source (chart)
- Conversion rate by source
- LTV by source
- Click source for detailed lead list

**Lead Timeline:**
- Daily lead generation
- Conversion trend over time
- Click any date for lead details

**Features:**
- Export lead lists by source
- Filter by date range
- Filter by conversion status

---

## Advanced Features

### Filtering System

**Available Filters:**
- **Month** - Select specific month or "All Months"
- **Location** - Select specific location or "All Locations"
- **Practitioner** - Select specific VSP or "All Practitioners"
- **Service** - Select specific service type or "All Services"
- **Date Range** - Custom start and end dates

**How Filtering Works:**
1. User changes filter dropdown
2. `applyFilters()` function runs
3. Creates new filtered datasets:
   - `filteredAppointments` - from `appointmentsData`
   - `filteredMemberships` - from `membershipsData`
   - `filteredLeads` - from `leadsData`
   - `filteredTimeTracking` - from `window.timeTrackingData`
4. Filters respect practitioner-location relationships
5. All tabs re-render with filtered data
6. Charts update automatically

**Critical: Time Tracking Filtering**

The time tracking filter has special logic to respect location filtering:

1. First, filters appointments by all criteria (month, location, practitioner)
2. Builds a set of practitioners who have appointments in filtered data
3. Filters time tracking to ONLY include those practitioners
4. This ensures time tracking respects location (since practitioners work at specific locations)
5. Filters by date range (month/start date/end date)

**Why This Matters:**
- Prevents counting time from practitioners at other locations
- Ensures Non-Appt Labor calculates correctly
- Maintains data accuracy when location filtering

### Period Comparison

**When Enabled:**
- Selecting a specific month activates comparison
- Compares to previous month automatically
- Shows delta (↑ increase, ↓ decrease)
- Percentage change calculated

**Metrics Compared:**
- Total Revenue
- Total Appointments
- Unique Clients
- Net Profit
- And more...

**Comparison Indicator Colors:**
- Green: Positive change
- Red: Negative change
- Gray: No change

### CSV Export

**Any Data Can Be Exported:**
1. Click chart, table, or segment
2. Click "Export to CSV" button
3. Browser downloads CSV file
4. Use in Excel, Google Sheets, CRM, etc.

**Export Formats:**
- Client segments (name, email, phone, etc.)
- Lead lists (with source, conversion status)
- Appointment details
- Revenue reports
- And more...

### Interactive Charts

**Click Functionality:**
- Bar charts → Show details for that bar
- Pie charts → Show breakdown for that slice
- Line charts → Show data point details
- Heatmaps → Show appointments for that time slot

**Hover Tooltips:**
- All charts show values on hover
- Percentages for pie charts
- Trends for line charts

### Client Segmentation Engine

**How It Works:**
1. Aggregates all appointment and membership data per customer
2. Calculates:
   - Total visits
   - Last visit date
   - Total LTV
   - Membership status
   - Visit frequency
3. Applies segment criteria
4. Assigns customers to segments
5. Generates downloadable contact lists

**Segment Priority:**
1. Inactive Paid Members (most urgent)
2. At-Risk (needs attention)
3. VIP (maintain relationship)
4. High-Frequency Non-Members (conversion opportunity)
5. New Clients (nurture)

### Appointment Heatmap Algorithm

**For Each Location:**
1. Initialize grid (Monday-Saturday, 6am-9pm)
2. For each appointment:
   - Extract day of week
   - Extract hour
   - Increment counter for that cell
3. Calculate max value for color scaling
4. Render heatmap with 8 intensity levels (0-7)
5. Add click handlers for interactivity

**Color Scaling:**
- Level 0 (white): No appointments
- Level 1-2 (light blue): Low
- Level 3-4 (medium blue): Medium
- Level 5-6 (dark blue): High
- Level 7 (darkest blue): Maximum

---

## Calculations & Formulas

### Financial Calculations

**Total Revenue:**
```
Appointment Revenue (non-members) +
Appointment Revenue (non-active-members) +
Membership Revenue
```

**Appointment Revenue Calculation:**
- Excludes appointments from active members (to avoid double-counting with MRR)
- Active member check: Email match between appointments and active memberships

**Total Labor Cost:**
```
Appointment Payouts +
Non-Appointment Labor Cost
```

**Non-Appointment Labor Cost:**
```
(Total Clocked Hours - Total Appointment Hours) × Base Hourly Rate
```

**Net Profit:**
```
Total Revenue - 
Total Labor Cost - 
Franchise Fees - 
Brand Fund - 
Credit Card Fees
```

**Profit Margin:**
```
(Net Profit ÷ Total Revenue) × 100
```

### Membership Calculations

**MRR (Monthly Recurring Revenue):**
```
For each active membership:
  If frequency contains "annual": Amount ÷ 12
  Else if frequency contains "quarterly": Amount ÷ 3
  Else: Amount (monthly)
  
MRR = Sum of all normalized amounts
```

**Churn Rate:**
```
(Cancellations This Period ÷ Active Members Start of Period) × 100
```

**Average Membership Value:**
```
Total MRR ÷ Number of Active Members
```

### Customer Metrics

**LTV (Lifetime Value):**
```
Sum of all revenue from this customer
(appointments + memberships + products)
```

**Retention Rate:**
```
(Customers with 2+ Visits ÷ Total Customers) × 100
```

**Avg Visits Per Customer:**
```
Total Appointments ÷ Unique Customers
```

**Customer Acquisition Cost (if known):**
```
Total Marketing Spend ÷ New Customers
```

### VSP Performance

**Utilization Rate:**
```
(Total Appointment Hours ÷ Total Clocked Hours) × 100
```

**Revenue Per Hour:**
```
Total Revenue Generated ÷ Total Hours Worked
```

**Appointments Per Day:**
```
Total Appointments ÷ Number of Days Worked
```

### Goal Progress

**Revenue Progress:**
```
(Actual Revenue ÷ Revenue Goal) × 100
```

**Appointments Needed Per Week:**
```
Math.ceil((Goal - Current) ÷ Weeks Remaining)
```

**On Track Calculation:**
```
Current Progress ≥ (Days Elapsed ÷ Days in Month) × 100
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: Non-Appt Labor Shows Zero or Disappears

**Causes:**
1. Time tracking data not loaded
2. Field name mismatch
3. No practitioners match filtered appointments
4. All time records filtered out by date

**Solutions:**
1. Upload Practitioner Payroll ZIP file
2. Ensure Momence time clock is enabled
3. Clear browser cache (Ctrl+Shift+R)
4. Check console for debug messages (F12)
5. Verify practitioners are clocking in/out properly

**Debug Steps:**
1. Open browser console (F12)
2. Apply month filter
3. Look for debug output:
   ```
   DEBUG: Filtering time tracking... {
     totalTimeRecords: XXX,
     practitionersInFiltered: [...],
     ...
   }
   ```
4. If `filteredCount: 0`, no records match filters
5. If `totalTimeRecords: 0`, data not loaded

#### Issue: Dashboard Won't Update to Latest Version

**Cause:** Browser cache holding old version

**Solution:**
1. Force reload: `Ctrl+Shift+R` (Win) or `Cmd+Shift+R` (Mac)
2. Check tab title shows correct version
3. Check footer shows correct version
4. If still doesn't work:
   - Clear all browser cache
   - Try incognito/private mode
   - Try different browser

#### Issue: Data Not Showing After Upload

**Causes:**
1. Missing required files
2. Incorrect file format
3. File exported incorrectly from Momence
4. Browser blocking file access

**Solutions:**
1. Verify all 4 required files uploaded
2. Check for green checkmarks (✅) on each
3. Ensure files exported correctly:
   - Membership Sales: CSV from report
   - Cancellations: CSV from Cancellations tab
   - Leads: CSV from New Leads & Customers
   - Payroll: ZIP file with all practitioners
4. Try different browser
5. Disable browser extensions
6. Check browser console for errors

#### Issue: Attendance Analytics Not Showing

**Cause:** Attendance report not uploaded

**Solution:**
1. This is an optional feature
2. Only appears when attendance ZIP is uploaded
3. Upload `momence-appointments-attendance-report-summary.zip`
4. Look for green checkmark
5. Refresh to see Attendance Analytics in Insights tab

#### Issue: Settings Not Saving

**Causes:**
1. Browser blocking localStorage
2. Private/incognito mode
3. Browser storage full

**Solutions:**
1. Ensure not in private/incognito mode
2. Check browser settings allow localStorage
3. Try different browser
4. Clear browser storage
5. Check for browser extensions blocking storage

#### Issue: Charts Not Rendering

**Causes:**
1. JavaScript error
2. Browser compatibility
3. Chart.js not loaded
4. Data format issue

**Solutions:**
1. Check browser console for errors (F12)
2. Use modern browser (Chrome 90+, Firefox 88+, Edge 90+)
3. Disable browser extensions
4. Clear cache and reload
5. Try different browser

#### Issue: Export CSV Not Working

**Causes:**
1. Browser blocking downloads
2. Pop-up blocker active
3. No data to export

**Solutions:**
1. Allow downloads in browser settings
2. Disable pop-up blocker for dashboard
3. Check that data is displayed before exporting
4. Try different browser

### Browser Console Debugging

**How to Access:**
- Windows/Linux: Press `F12`
- Mac: Press `Cmd+Option+I`
- Or right-click → Inspect → Console tab

**What to Look For:**
- Red error messages
- `DEBUG:` messages (for time tracking)
- `Uncaught` errors
- Failed network requests (shouldn't be any)

**Common Error Messages:**

**"Cannot read property X of undefined"**
- Data not loaded properly
- Missing required field in CSV
- Re-upload data files

**"Chart is not defined"**
- Chart.js library not loaded
- Check internet connection when first loading dashboard
- Refresh page

**"localStorage is not available"**
- Browser blocking local storage
- Disable private/incognito mode
- Check browser settings

---

## Performance Optimization

### Large Dataset Handling

**Dashboard Can Handle:**
- 100,000+ appointments
- 10,000+ customers
- 1,000+ memberships
- 5+ years of data

**Optimization Techniques:**
1. Lazy rendering - tabs render only when clicked
2. Filtered datasets - work with filtered data, not full dataset
3. Chart decimation - reduce data points for charts
4. Virtual scrolling - for large tables
5. Debouncing - filter changes don't trigger immediate re-render

### Memory Management

**Global Variables:**
- `appointmentsData` - Master appointment dataset
- `membershipsData` - Master membership dataset
- `leadsData` - Master leads dataset
- `filteredAppointments` - Filtered appointments
- `filteredMemberships` - Filtered memberships
- `filteredLeads` - Filtered leads
- `filteredTimeTracking` - Filtered time tracking
- `window.timeTrackingData` - Master time tracking dataset
- `window.employeeUtilization` - Calculated utilization data
- `allCharts` - Object holding all Chart.js instances

**Chart Memory Management:**
- Destroy chart before creating new one
- `destroyChart()` function cleans up properly
- Prevents memory leaks

### Browser Performance Tips

**For Best Performance:**
1. Use Chrome or Edge (best JavaScript performance)
2. Close unnecessary browser tabs
3. Disable unused extensions
4. Restart browser periodically
5. Keep browser updated

**If Dashboard Feels Slow:**
1. Reduce date range (filter to specific period)
2. Filter to specific location
3. Close charts tab when not using
4. Export large datasets rather than viewing in browser
5. Consider splitting data into multiple time periods

---

## Browser Compatibility

### Fully Supported Browsers

**Chrome/Edge 90+**
- ✅ Full compatibility
- ✅ Best performance
- ✅ All features work
- Recommended browser

**Firefox 88+**
- ✅ Full compatibility
- ✅ Good performance
- ✅ All features work

**Safari 14+**
- ✅ Full compatibility
- ⚠️ Slightly slower chart rendering
- ✅ All features work

### Partially Supported

**Internet Explorer 11**
- ❌ Not supported
- ❌ Does not support modern JavaScript
- Solution: Use Chrome, Firefox, or Edge

**Older Browsers**
- ❌ Browsers older than listed versions not supported
- Solution: Update browser to latest version

### Mobile Browsers

**Mobile Chrome/Safari**
- ✅ Works but not optimized for mobile
- ⚠️ Small screen makes some features difficult
- Recommendation: Use on desktop/laptop for best experience

### Operating Systems

**Windows 10/11**
- ✅ Fully supported
- Recommended: Chrome or Edge

**macOS**
- ✅ Fully supported  
- Recommended: Chrome or Safari

**Linux**
- ✅ Fully supported
- Recommended: Chrome or Firefox

**iOS/Android**
- ⚠️ Works but not optimized
- Recommendation: Use desktop for full features

---

## Version History

### v2.20251105.5 (Current - November 5, 2025)

**Critical Fixes:**
- 🔴 **FIXED:** Non-Appt Labor calculation with month/location filtering
  - Root cause: Time tracking field name was wrong ("Clock in date" vs "Clocked in")
  - Now properly filters time tracking to match filtered appointments
  - Respects location filtering through practitioner matching
- 🔴 **FIXED:** Template literal bug in Insights showing raw code instead of calculated value

**New Features:**
- ✨ **Attendance Analytics** - New section in Insights tab
  - Top 10 most frequent clients
  - Top VSPs by appointments booked  
  - Upcoming appointments count (booking pipeline)
  - Paid vs unpaid reservation tracking
  - Future revenue visibility
- ✨ **Location-Specific Heatmaps** - Separate heatmap for each location in Schedule tab
  - Each location shows its own busy times
  - Easier to compare locations
  - Click functionality filters by location
- ✨ **Leads Converted Report Support** - Enhanced lead tracking
- ✨ **Attendance Report ZIP Support** - Unlock attendance analytics features

**Improvements:**
- 🎨 Comparison text reduced to 8px for better visual hierarchy
- 🔧 Added cache-busting meta tags
- 🔧 Added debug console logging for troubleshooting
- 🔧 Improved error handling

### v2.20251104.07 (November 4, 2025)

**Bug Fixes:**
- 🔴 Fixed cancellation value calculations (MRR matching)
- 🔴 Fixed paid appointments vs goal tracking
- Improved email-based matching for cancellations
- Separate tracking for paid vs intro appointments

### v2.20251104.06

**Changes:**
- Changed default revenue goal to $20,000
- Changed default intro goal to 50
- Fixed churn rate by location
- Enhanced customer name extraction

### v2.20251103.05

**Features:**
- Added franchise configuration settings
- Comprehensive labor cost tracking
- New financial performance section
- Monthly goal visualizations

### v2.20251103.04

**Features:**
- Added utilization tracking
- Added commission tracking
- Enhanced ZIP file processing
- Improved tab organization

### v2.20251102 and Earlier

**Initial Features:**
- 8 main analytical tabs
- Client segmentation
- CSV export functionality
- Chart.js integration
- Membership tracking
- Lead management
- Basic filtering
- Goal tracking

---

## Best Practices

### Data Management

**Weekly Routine (15 minutes):**
1. Export fresh data from Momence
2. Upload to dashboard
3. Review goal progress
4. Check VSP performance
5. Export urgent segments (Inactive Paid Members)
6. Plan outreach campaigns

**Monthly Review (1 hour):**
1. Analyze full month trends
2. Compare to previous periods
3. Review all customer segments
4. Deep dive on retention & churn
5. Adjust strategies based on insights
6. Update goals if needed

### File Organization

**Recommended Folder Structure:**
```
The-Vital-Stretch-Analytics/
├── dashboard.html
├── data/
│   ├── 2025-11/
│   │   ├── momence--membership-sales-export.csv
│   │   ├── momence--membership-sales-export__1_.csv
│   │   ├── momence-new-leads-and-customers.csv
│   │   ├── momence-payroll-report-summary.zip
│   │   ├── momence-leads-converted-report.csv
│   │   └── momence-appointments-attendance-report-summary.zip
│   ├── 2025-10/
│   └── 2025-09/
└── exports/
    ├── segments/
    ├── reports/
    └── archives/
```

### Security Best Practices

1. **Store Dashboard Securely**
   - Keep on encrypted drive
   - Backup regularly
   - Don't share via public links

2. **Protect Data Files**
   - Don't upload to cloud storage unless encrypted
   - Delete old files when no longer needed
   - Shred when disposing

3. **Browser Security**
   - Keep browser updated
   - Use strong password for device
   - Lock computer when away
   - Log out of Momence after exporting

### Usage Tips

1. **Start with Overview**
   - Get high-level snapshot
   - Identify areas needing attention
   - Then dive into specific tabs

2. **Use Filters Effectively**
   - Start broad (All Locations, All Time)
   - Then narrow down (Specific Location, Specific Month)
   - Compare periods to identify trends

3. **Act on Segments**
   - Export Inactive Paid Members weekly
   - Follow up with At-Risk clients monthly
   - Reach out to VIPs quarterly
   - Convert High-Frequency Non-Members

4. **Monitor Leading Indicators**
   - Lead generation rate
   - Intro appointment count
   - Retention rate trends
   - Booking pipeline (upcoming appointments)

5. **Track Lagging Indicators**
   - Revenue
   - MRR
   - Churn rate
   - Profit margin

---

## Glossary

**MRR** - Monthly Recurring Revenue from active memberships

**LTV** - Lifetime Value, total revenue from a customer

**VSP** - Vital Stretch Practitioner (staff member)

**Churn** - When a customer cancels their membership

**Retention** - Percentage of customers who return for repeat visits

**Utilization** - Percentage of clocked time spent on appointments

**Non-Appt Labor** - Time clocked but not spent on appointments (admin, cleaning, training)

**Intro Appointment** - Discounted first-time appointment to attract new clients

**Booking Pipeline** - Upcoming scheduled appointments (future revenue)

**Active Member** - Customer with currently active membership subscription

**At-Risk Client** - Previously active customer who hasn't visited recently

**Cohort** - Group of customers who joined in the same time period

**Conversion Rate** - Percentage of leads who become customers

**Gap** - Scheduling gap between appointments (unutilized time)

---

## Support & Contact

### Getting Help

**Documentation:**
- README.md - Quick start guide
- README-Detailed.md - This document (comprehensive technical guide)
- BUG-EXPLANATION.md - Technical bug details
- VERIFICATION-GUIDE.md - How to verify dashboard loaded correctly
- CHANGES.md - Detailed changelog

**Troubleshooting:**
1. Check Troubleshooting Guide (above)
2. Clear browser cache and force reload
3. Check browser console for errors
4. Try different browser
5. Contact franchise administrator

**Feature Requests:**
- Document desired features
- Explain use case
- Provide example data if possible
- Contact via franchise network

### Reporting Issues

**When reporting an issue, include:**
1. Dashboard version (check footer)
2. Browser name and version
3. Operating system
4. Steps to reproduce issue
5. Screenshot if applicable
6. Console errors if any (F12 → Console)
7. Which tab/feature is affected

---

**Thank you for using The Vital Stretch Analytics Dashboard!**

**Created with ❤️ by bonJoeV for The Vital Stretch Franchise**

*This dashboard is designed to help franchise owners make data-driven decisions and grow their business. Use it weekly, act on insights, and watch your business thrive.*

---

**Version:** v2.20251105.5  
**Last Updated:** November 5, 2025  
**License:** Proprietary - For The Vital Stretch franchise use only
