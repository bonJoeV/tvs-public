# Extraction Guide for Remaining Functions

This guide provides specific line numbers and instructions for extracting the remaining functions from `vital-stretch-dashboard.html`.

## Quick Reference Commands

```bash
# View specific lines from the original file:
sed -n 'START,ENDp' /home/user/tvs-public/StudioOps/vital-stretch-dashboard.html

# Example: View lines 2483-2590 (showVisitFrequencyDetails function)
sed -n '2483,2590p' /home/user/tvs-public/StudioOps/vital-stretch-dashboard.html
```

## 1. Completing modals.js

### showVisitFrequencyDetails (lines 2483-2591)
```bash
sed -n '2483,2591p' vital-stretch-dashboard.html
```
- Filters appointments by visit range
- Calculates revenue per client
- Shows modal with client details table

### showPractitionerDetails (lines 2594-2668)
```bash
sed -n '2594,2668p' vital-stretch-dashboard.html
```
- Shows practitioner performance
- Service breakdown table
- Revenue and appointment stats

### showServiceDetails (lines 2671-2741)
```bash
sed -n '2671,2741p' vital-stretch-dashboard.html
```
- Service performance metrics
- Practitioner breakdown for service
- Revenue analysis

### showDayOfWeekDetails (lines 2744-2835)
```bash
sed -n '2744,2835p' vital-stretch-dashboard.html
```
- Day of week performance
- Hour breakdown
- Location filtering

### showHourDetails (lines 2838-2930)
```bash
sed -n '2838,2930p' vital-stretch-dashboard.html
```
- Specific hour performance
- Individual appointments list
- Customer details

### showRetentionDetails (lines 2933-3028)
```bash
sed -n '2933,3028p' vital-stretch-dashboard.html
```
- Retention segment analysis
- One-time vs returning clients
- Revenue breakdown

### showSegmentDetails (lines 6148-6235)
```bash
sed -n '6148,6235p' vital-stretch-dashboard.html
```
- RFM segment details
- Client list for segment
- Behavioral analysis

### showCancellationReasonDetails (lines 11973-12070)
```bash
sed -n '11973,12070p' vital-stretch-dashboard.html
```
- Cancellation reason breakdown
- Member details by reason
- Revenue impact analysis

### showCancellationTypeDetails (lines 12071-12158)
```bash
sed -n '12071,12158p' vital-stretch-dashboard.html
```
- Cancellation by membership type
- Type-specific metrics

### showCancellationLocationDetails (lines 12159-12246)
```bash
sed -n '12159,12246p' vital-stretch-dashboard.html
```
- Location-specific cancellations
- Location performance

### showCancellationMonthDetails (lines 12247-12348)
```bash
sed -n '12247,12348p' vital-stretch-dashboard.html
```
- Monthly cancellation trends
- Seasonal patterns

### showJourneyDetails (lines 12756-12796)
```bash
sed -n '12756,12796p' vital-stretch-dashboard.html
```
- Customer journey stage details
- Stage-specific metrics

### showLeadsTimelineDetails (lines 14260-14308)
```bash
sed -n '14260,14308p' vital-stretch-dashboard.html
```
- Daily lead generation details
- Lead source breakdown

### showLeadsSourceDetails (lines 14309-14371)
```bash
sed -n '14309,14371p' vital-stretch-dashboard.html
```
- Lead source performance
- Conversion rates by source

### Heatmap Details Functions
```bash
# showLocationHeatmapDetails (lines 10305-10357)
sed -n '10305,10357p' vital-stretch-dashboard.html

# showApptHeatmapDetails (lines 10449-10501)
sed -n '10449,10501p' vital-stretch-dashboard.html

# showHeatmapDetails (lines 10502-10560)
sed -n '10502,10560p' vital-stretch-dashboard.html
```

## 2. Completing charts.js

### Core Chart Functions

```bash
# renderMonthlyGoalCharts (lines 7708-7931)
sed -n '7708,7931p' vital-stretch-dashboard.html

# renderRevenueByLocationChart (lines 12840-12882)
sed -n '12840,12882p' vital-stretch-dashboard.html

# renderRevenueByServiceChart (lines 12883-12938)
sed -n '12883,12938p' vital-stretch-dashboard.html

# renderIntroSessionsChart (lines 12939-12971)
sed -n '12939,12971p' vital-stretch-dashboard.html

# renderPaymentMethodsChart (lines 12972-13005)
sed -n '12972,13005p' vital-stretch-dashboard.html

# renderHeatmap (lines 13006-13090)
sed -n '13006,13090p' vital-stretch-dashboard.html

# renderCustomerTypesChart (lines 13157-13182)
sed -n '13157,13182p' vital-stretch-dashboard.html

# renderVisitFrequencyChart (lines 13183-13216)
sed -n '13183,13216p' vital-stretch-dashboard.html

# renderRetentionBreakdownChart (lines 13217-13261)
sed -n '13217,13261p' vital-stretch-dashboard.html

# renderPractitionerCharts (lines 13262-13348)
sed -n '13262,13348p' vital-stretch-dashboard.html

# renderTimelineCharts (lines 13349-13865)
sed -n '13349,13865p' vital-stretch-dashboard.html

# renderMembershipTimelineCharts (lines 13866-14050)
sed -n '13866,14050p' vital-stretch-dashboard.html

# renderLeadsTimelineCharts (lines 14051-14259)
sed -n '14051,14259p' vital-stretch-dashboard.html
```

### Heatmap Chart Functions

```bash
# formatTime (lines 10107-10113)
sed -n '10107,10113p' vital-stretch-dashboard.html

# renderLeadsHeatmap (lines 10115-10213)
sed -n '10115,10213p' vital-stretch-dashboard.html

# renderLocationHeatmap (lines 10214-10304)
sed -n '10214,10304p' vital-stretch-dashboard.html

# renderAppointmentHeatmap (lines 10358-10448)
sed -n '10358,10448p' vital-stretch-dashboard.html
```

## 3. Completing tabs.js

### Core Tab Renderers

```bash
# renderOverviewTab (lines 4589-4998)
sed -n '4589,4998p' vital-stretch-dashboard.html

# renderRetentionTab (lines 4999-5262)
sed -n '4999,5262p' vital-stretch-dashboard.html

# renderStudiosTab (lines 5263-5765)
sed -n '5263,5765p' vital-stretch-dashboard.html

# renderScheduleTab (lines 5766-5978)
sed -n '5766,5978p' vital-stretch-dashboard.html

# renderClientSegmentation (lines 6237-6421)
sed -n '6237,6421p' vital-stretch-dashboard.html

# renderCustomersTab (lines 6422-6737)
sed -n '6422,6737p' vital-stretch-dashboard.html

# renderPractitionersTab (lines 6738-7050)
sed -n '6738,7050p' vital-stretch-dashboard.html

# renderTimelineTab (lines 7051-7331)
sed -n '7051,7331p' vital-stretch-dashboard.html

# renderInsightsTab (lines 7332-7707)
sed -n '7332,7707p' vital-stretch-dashboard.html

# renderMembershipsTab (lines 8037-9228)
sed -n '8037,9228p' vital-stretch-dashboard.html

# renderLeadsTab (lines 9263-9451)
sed -n '9263,9451p' vital-stretch-dashboard.html

# renderJourneyTab (lines 12349-12755)
sed -n '12349,12755p' vital-stretch-dashboard.html
```

### Supporting Functions

```bash
# calculateClientSegments (lines 5979-6147)
sed -n '5979,6147p' vital-stretch-dashboard.html

# calculateComparisonData (lines 8037-8136)
sed -n '8037,8136p' vital-stretch-dashboard.html

# renderLeadsOverview (lines 9452-9520)
sed -n '9452,9520p' vital-stretch-dashboard.html

# renderLeadsSourceAnalysis (lines 9521-9580)
sed -n '9521,9580p' vital-stretch-dashboard.html

# renderLeadsLocationAnalysis (lines 9581-9644)
sed -n '9581,9644p' vital-stretch-dashboard.html

# renderLeadsTimeline (lines 9645-9704)
sed -n '9645,9704p' vital-stretch-dashboard.html

# renderLeadsConversionFunnel (lines 9705-9766)
sed -n '9705,9766p' vital-stretch-dashboard.html

# renderLeadsCharts (lines 9767-10106)
sed -n '9767,10106p' vital-stretch-dashboard.html
```

## 4. Completing upload.js

### Payroll ZIP Handler (lines 3678-3855)
```bash
sed -n '3678,3855p' vital-stretch-dashboard.html
```

This handler:
1. Uses JSZip to extract multiple CSV files
2. Processes appointments, time tracking, and commissions
3. Calculates employee utilization
4. Cleans duration data outliers
5. Stores processed data globally

Key sections:
- ZIP loading and file iteration
- CSV parsing with Papa.parse
- Employee stats calculation
- Duration cleaning algorithm
- Utilization calculation
- Global data storage

### Attendance ZIP Handler (lines 3858-3916)
```bash
sed -n '3858,3916p' vital-stretch-dashboard.html
```

This handler:
1. Extracts attendance report CSV from ZIP
2. Builds email-to-name mapping for VSPs
3. Updates global staffEmailToName object
4. Triggers dashboard re-render with proper names

## Extraction Pattern

For each function:

1. **Extract the function:**
   ```bash
   sed -n 'START,ENDp' vital-stretch-dashboard.html
   ```

2. **Copy to appropriate module file**

3. **Add export statement:**
   ```javascript
   export function functionName() {
       // function body
   }
   ```

4. **Update imports at top of file:**
   ```javascript
   import { dependency1, dependency2 } from './other-module.js';
   ```

5. **Update data access:**
   ```javascript
   // Replace global variables with imports
   // Before: filteredAppointments
   // After:  import { filteredAppointments } from './data.js';
   ```

6. **Update function calls:**
   ```javascript
   // Before: showModal(...)
   // After:  import { showModal } from './modals.js';
   ```

7. **Test the function** in isolation

## Common Patterns to Update

### 1. Data Access
```javascript
// Before (global):
const data = filteredAppointments;

// After (imported):
import { filteredAppointments } from './data.js';
const data = filteredAppointments;
```

### 2. Function Calls
```javascript
// Before (global):
showModal('Title', content);

// After (imported):
import { showModal } from './modals.js';
showModal('Title', content);
```

### 3. Utility Functions
```javascript
// Before (global):
const formatted = formatCurrency(value);

// After (imported):
import { formatCurrency } from './utils.js';
const formatted = formatCurrency(value);
```

### 4. Config Access
```javascript
// Before (global):
const goal = CONFIG.goals.monthlyRevenue;

// After (imported):
import { CONFIG } from './config.js';
const goal = CONFIG.goals.monthlyRevenue;
```

## Testing Each Function

After extracting each function:

1. Check imports are correct
2. Verify no undefined variables
3. Test with actual data
4. Verify modal/chart displays correctly
5. Check browser console for errors

## Tools

Use these bash commands to help with extraction:

```bash
# Count functions in a range
grep -c "^        function" vital-stretch-dashboard.html

# Find all function definitions
grep -n "^        function" vital-stretch-dashboard.html

# Extract a specific function by name
sed -n '/^        function showModal/,/^        }/p' vital-stretch-dashboard.html

# Search for variable usage
grep -n "filteredAppointments" vital-stretch-dashboard.html
```

## Completion Order Recommendation

Extract in this order for best results:

1. **modals.js** - Most detail functions are self-contained
2. **charts.js** - Charts depend on modals for click handlers
3. **tabs.js** - Tabs depend on charts and modals
4. **upload.js** - Independent ZIP handlers

This ensures dependencies are available as you progress.
