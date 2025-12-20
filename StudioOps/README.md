# TVS Franchisee Command Center

A comprehensive financial modeling and operations dashboard for The Vital Stretch franchise owners. Built as a single-file HTML application with no external dependencies (except Chart.js CDN).

## Overview

This dashboard enables franchise operators to:
- Project member growth across multiple studio locations
- Model P&L scenarios with customizable assumptions
- Track VSP (Vital Stretch Practitioner) staffing requirements
- Generate clean reports for SBA loan presentations
- Compare what-if scenarios for business planning

## Features

### 📊 Dashboard Tab
- **Portfolio KPIs**: Total members, projected growth, revenue metrics
- **Studio Status Cards**: Visual health indicators per location
- **Growth Trajectory Chart**: Multi-studio member projections over time
- **Performance Benchmarks**: Compare against industry standards

### 💰 Financials Tab
- **Revenue & Contribution Margin Table**: Monthly or Quarterly view (Q1 CY26 format)
- **P&L Trajectory Chart**: Visualize revenue, costs, and profit trends
- **Studio Break-Even Timeline**: When each location reaches profitability
- **Cash Runway Projections**: Months of runway based on current burn rate
- **Debt Service Tracking**: Per-studio loan payments integrated into P&L

### 👥 Operations Tab
- **VSP Staffing Requirements**: FTE and part-time needs by month
- **Capacity Analysis**: Headroom calculations per studio
- **Utilization Tracking**: Blended hourly rates and efficiency metrics
- **Hiring Alerts**: Advance warnings for staffing needs

### 📈 Leads & Marketing Tab
- **Conversion Funnel**: Lead → Intro → Member pipeline
- **Ad Spend Modeling**: Per-studio marketing budgets
- **Cost Per Lead Analysis**: Track acquisition costs
- **Launch Spend**: Accelerated pre-opening marketing

### 🎯 Scenarios Tab
- **Sensitivity Analysis**: Impact of churn, growth, and delays
- **What-If Modeling**: Test different assumptions
- **Quick Presets**: Conservative, Moderate, Aggressive scenarios

### 🏢 Franchise Tab
- **Multi-Studio Management**: Add, remove, rename locations
- **Per-Studio Configuration**: Rent, capacity, staffing, conversion rates
- **Open Date Planning**: Schedule future studio launches

## Studio Management

### Adding Studios
1. Click **➕ Add New Studio** button
2. Edit the studio name in the header
3. Toggle "New" checkbox for future openings
4. Configure all parameters (sq ft, rent, tables, etc.)

### Configuring Studios
Each studio card includes:
- **Members & Targets**: Current count, Month 9 goal
- **Facility**: Square footage, NNN lease rate, tables
- **Operations**: Hours, days, utilization %
- **Marketing**: Lead→Intro %, Intro→Member %, Ad spend
- **Staffing**: VSP stretch/idle rates
- **Debt Service**: Loan amount, rate, term (set to $0 if no loan)

### Removing Studios
Click the **✕** button in the studio header (minimum 1 studio required)

## Loan Presentation Mode

Click **🏦 Loan View** to enter a clean presentation mode for SBA loan officers:
- Hides all input controls and editing UI
- Shows only projections and financial data
- Automatically switches to Quarterly view
- Select specific studio(s) to focus the presentation
- Click **✕ Exit Loan View** to return to editing

## Multi-Studio Filtering

Use the studio dropdown to:
- **Select All**: View combined portfolio metrics
- **Single Studio**: Focus on one location's projections
- **Multiple Studios**: Compare subset of locations

A banner appears when filtering, showing selected studio(s) details.

## Time Horizon

Adjust the projection period using the dropdown:
- **13 months**: Short-term view
- **24 months** (default): Two-year projection (Jan '26 - Dec '27)
- **36 months**: Extended planning

## Growth Rate Settings

### Ramp Growth (M1-9)
Monthly growth rate during the initial 9-month ramp period.
- Industry benchmark: 8-15%
- Target: 12%+

### Maintenance Growth (M9+)
Monthly growth rate after Month 9.
- Industry benchmark: 3-6%
- Target: 5%+

### Churn Rate
Monthly member attrition rate.
- Industry benchmark: 4-7%
- Target: <4%

### Net Growth Display
Shows both phases:
- **M1-9**: Ramp Growth minus Churn
- **M9+**: Maintenance Growth minus Churn

## Financial Modeling

### Revenue Assumptions
- Average Revenue Per Hour
- Session length (minutes)
- Sessions per member per month
- Retail revenue per member

### Cost Structure
- **Royalty**: Franchise fees (default 6%)
- **Brand Fund**: Marketing fund (default 2%)
- **Credit Card Fees**: Payment processing (default 3%)
- **Momence Fee**: Studio management software (default 1%)
- **VSP Commission**: Practitioner bonuses
- **GM Salary**: General manager compensation
- **Owner Draws**: Owner compensation

### Debt Service
Per-studio loan tracking:
- Enter $0 for locations without loans
- Automatic monthly payment calculation using standard amortization
- Integrated into P&L and cash flow projections

## Data Persistence

Settings are automatically saved to browser localStorage:
- All input values
- Studio configurations
- Time horizon selection

Click **Reset** to clear all saved data and return to defaults.

## Technical Details

### Architecture
- **Single HTML file**: No build process required
- **Vanilla JavaScript**: No framework dependencies
- **Chart.js**: Visualization library (loaded via CDN)
- **CSS Variables**: Consistent theming
- **Responsive Design**: Works on desktop, tablet, and mobile

### Browser Support
- Chrome (recommended)
- Firefox
- Safari
- Edge

### Print Support
- Optimized print styles for PDF generation
- Tables print without scroll constraints
- Charts resize appropriately

## Color Coding

- **Blue** (#013160): Primary brand color, headers
- **Cyan** (#71BED2): Secondary accent, positive trends
- **Gold** (#FBB514): Highlights, warnings, call-to-action
- **Green**: Success states, profitable months
- **Red**: Danger states, losses, alerts
- **Purple**: Debt service indicators

## File Structure

```
FranchiseOps.html    # Complete application (single file)
README.md            # This documentation
```

## Usage

1. Open `FranchiseOps.html` in a web browser
2. Configure your studio parameters in the Franchise tab
3. Adjust growth assumptions in the Dashboard tab
4. Review projections across all tabs
5. Use Loan View for clean presentations
6. Print to PDF as needed

## Support

For questions about The Vital Stretch franchise operations, contact your franchise support team.

---

*Built for The Vital Stretch franchise system*
