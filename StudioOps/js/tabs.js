/**
 * Tabs Module
 *
 * This module manages all dashboard tabs and their rendering logic
 */

import { formatCurrency, formatNumber, parseLTV, parseDate, isIntroOffer, formatStaffName } from './utils.js';
import {
    filteredAppointments, filteredLeads, filteredMemberships, filteredCancellations,
    appointmentsData, leadsData, membershipsData, membershipCancellationsData,
    filteredTimeTracking, staffEmailToName
} from './data.js';
import { CONFIG } from './config.js';
import * as charts from './charts.js';
import * as modals from './modals.js';

// Tab state tracking
let renderedTabs = new Set();
let currentActiveTab = 'overview';

// Helper function - Get Active Member Emails
function getActiveMemberEmails() {
    const activeMemberEmails = new Set();
    if (membershipsData && membershipsData.length > 0) {
        membershipsData.forEach(m => {
            // Only include active (non-expired) memberships
            if (m.Expired !== 'Yes' && m['Customer Email']) {
                activeMemberEmails.add(m['Customer Email'].toLowerCase().trim());
            }
        });
    }
    return activeMemberEmails;
}

// Helper function - Calculate Appointment Revenue (excludes active members)
function calculateAppointmentRevenue(appointments) {
    const activeMemberEmails = getActiveMemberEmails();
    return appointments.reduce((sum, row) => {
        const customerEmail = (row['Customer Email'] || '').toLowerCase().trim();
        // Exclude revenue from active members
        if (activeMemberEmails.has(customerEmail)) {
            return sum;
        }
        return sum + parseFloat(row.Revenue || 0);
    }, 0);
}

// Tab Switching
export function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');

    // Add active class to clicked button
    const activeBtn = Array.from(document.querySelectorAll('.tab-btn'))
        .find(btn => btn.textContent.toLowerCase().includes(tabName.replace('Tab', '').replace(/([A-Z])/g, ' $1').trim().toLowerCase()));
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Render tab if not already rendered (lazy loading)
    if (!renderedTabs.has(tabName)) {
        renderTab(tabName);
    }

    currentActiveTab = tabName;
}

// Render a specific tab (lazy loading)
export function renderTab(tabName) {
    switch (tabName) {
        case 'overview':
            renderOverviewTab();
            break;
        case 'retention':
            renderRetentionTab();
            break;
        case 'studios':
            renderStudiosTab();
            break;
        case 'schedule':
            renderScheduleTab();
            break;
        case 'clientSegmentation':
            renderClientSegmentation();
            break;
        case 'customers':
            renderCustomersTab();
            break;
        case 'practitioners':
            renderPractitionersTab();
            break;
        case 'timeline':
            renderTimelineTab();
            break;
        case 'insights':
            renderInsightsTab();
            break;
        case 'memberships':
            renderMembershipsTab();
            break;
        case 'leads':
            renderLeadsTab();
            break;
        case 'journey':
            renderJourneyTab();
            break;
        default:
            console.warn(\`Unknown tab: \${tabName}\`);
    }

    renderedTabs.add(tabName);
}

// Render all tabs (called after filter changes)
export function renderAllTabs() {
    // Only re-render tabs that have been viewed at least once
    renderedTabs.forEach(tabName => {
        renderTab(tabName);
    });

    // Always render the current active tab
    if (!renderedTabs.has(currentActiveTab)) {
        renderTab(currentActiveTab);
    }
}

// Get current period info (helper for calculations)
export function getCurrentPeriod() {
    const month = document.getElementById('monthFilter').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (startDate && endDate) {
        return {
            type: 'custom',
            start: new Date(startDate),
            end: new Date(endDate),
            label: \`\${startDate} to \${endDate}\`
        };
    } else if (month !== 'all') {
        const [year, monthNum] = month.split('-');
        const start = new Date(year, parseInt(monthNum) - 1, 1);
        const end = new Date(year, parseInt(monthNum), 0);
        return {
            type: 'month',
            start: start,
            end: end,
            label: start.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
        };
    }
    return null;
}


// ============================================================================
// TAB RENDERING FUNCTIONS
// ============================================================================

export function renderOverviewTab() {
    const data = filteredAppointments;
    
    // Calculate appointment revenue EXCLUDING active members
    const apptRevenue = calculateAppointmentRevenue(data);
    
    // Calculate membership revenue if data is available
    let membershipRevenue = 0;
    if (filteredMemberships && filteredMemberships.length > 0) {
        membershipRevenue = filteredMemberships.reduce((sum, m) => sum + parseFloat(m['Paid Amount'] || 0), 0);
    }
    
    const totalRevenue = apptRevenue + membershipRevenue;
    const totalPayout = data.reduce((sum, row) => sum + parseFloat(row['Total Payout'] || 0), 0);
    const totalHours = data.reduce((sum, row) => sum + parseFloat(row['Time (h)'] || 0), 0);
    const avgRevenue = data.length > 0 ? apptRevenue / data.length : 0;
    
    // Calculate total labor costs including non-appointment work
    let totalLaborCost = totalPayout;
    let nonApptHours = 0;
    let nonApptLaborCost = 0;
    
    if (filteredTimeTracking && filteredTimeTracking.length > 0) {
        // Get the list of practitioners who have appointments in the filtered data
        const practitionersInFiltered = new Set();
        data.forEach(row => {
            const empName = row['Employee Name'];
            if (empName) {
                practitionersInFiltered.add(empName);
            }
        });
        
        // Only count time tracking for practitioners who have appointments in the filtered data
        const relevantTimeTracking = filteredTimeTracking.filter(t => 
            practitionersInFiltered.has(t['Employee Name'])
        );
        
        const totalClockedHours = relevantTimeTracking.reduce((sum, t) => {
            const hours = parseFloat(t['Duration (h)'] || 0);
            return sum + hours;
        }, 0);
        
        // Non-appointment hours = clocked hours - appointment hours
        nonApptHours = Math.max(0, totalClockedHours - totalHours);
        nonApptLaborCost = nonApptHours * CONFIG.baseHourlyRate;
        totalLaborCost = totalPayout + nonApptLaborCost;
    }
    
    // Calculate salary costs for the filtered period
    let salaryCosts = { total: 0, details: [] };
    if (data.length > 0) {
        const dates = data.map(row => parseDate(row['Appointment Date']));
        const minDate = new Date(Math.min(...dates));
        const maxDate = new Date(Math.max(...dates));
        salaryCosts = calculateSalaryCosts(minDate, maxDate);
        totalLaborCost += salaryCosts.total;
    }
    
    const profit = totalRevenue - totalLaborCost;
    const profitMargin = totalRevenue > 0 ? (profit / totalRevenue * 100) : 0;
    
    // Count intro sessions and late cancellations
    const introSessions = data.filter(row => isIntroOffer(row['Appointment'])).length;
    const lateCancellations = data.filter(row => 
        row['Late cancellations'] && row['Late cancellations'].toLowerCase() === 'yes'
    ).length;
    
    // Unique clients
    const uniqueClients = new Set(
        data.map(row => (row['Customer Email'] || '').toLowerCase().trim())
            .filter(email => email)
    ).size;
    
    // Revenue per hour
    const revenuePerHour = totalHours > 0 ? totalRevenue / totalHours : 0;
    
    // Average ticket size
    const avgTicketSize = data.length > 0 ? totalRevenue / data.length : 0;
    
    // Calculate utilization if data available
    let avgUtilization = null;
    if (window.employeeUtilization) {
        const utilizationValues = Object.values(window.employeeUtilization)
            .map(e => e.utilization)
            .filter(u => u > 0);
        if (utilizationValues.length > 0) {
            avgUtilization = utilizationValues.reduce((sum, u) => sum + u, 0) / utilizationValues.length;
        }
    }
    
    // Client visit frequency
    const clientVisits = {};
    data.forEach(row => {
        const email = row['Customer Email'];
        if (email) {
            clientVisits[email] = (clientVisits[email] || 0) + 1;
        }
    });
    const newClients = Object.values(clientVisits).filter(v => v === 1).length;
    const returningClients = uniqueClients - newClients;
    const avgVisitsPerClient = uniqueClients > 0 ? data.length / uniqueClients : 0;
    
    // Busiest day
    const dayCount = {};
    data.forEach(row => {
        const date = parseDate(row['Appointment Date']);
        if (date) {
            const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const day = days[date.getDay()];
            dayCount[day] = (dayCount[day] || 0) + 1;
        }
    });
    const busiestDay = Object.entries(dayCount).sort((a, b) => b[1] - a[1])[0];
    
    // Top paid service by appointments (excluding demo and intro)
    const serviceCount = {};
    data.forEach(row => {
        const service = row.Appointment;
        if (service && !isIntroOffer(service)) {
            serviceCount[service] = (serviceCount[service] || 0) + 1;
        }
    });
    const topService = Object.entries(serviceCount).sort((a, b) => b[1] - a[1])[0];
    
    // Number of practitioners
    const uniquePractitioners = new Set(
        data.map(row => `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`)
            .filter(name => name.trim() !== '')
    ).size;
    const revenuePerPractitioner = uniquePractitioners > 0 ? totalRevenue / uniquePractitioners : 0;
    
    // Calculate comparison data if enabled
    if (document.getElementById('comparisonPeriod').value !== 'none') {
        calculateComparisonData();
    }
    
    let html = `
        ${comparisonData ? `<div class="alert info"><h4>📊 Period Comparison Active</h4><p>Comparing current period to: <strong>${comparisonData.period}</strong></p></div>` : ''}
        
        <div class="metrics-grid">
            <div class="metric-card compact">
                <div class="metric-label">Total Revenue</div>
                <div class="metric-value">
                    ${formatCurrency(totalRevenue)}
                    ${comparisonData ? getComparisonIndicator(totalRevenue, comparisonData.revenue, 'currency') : ''}
                </div>
                <div class="metric-subtext">
                    ${membershipRevenue > 0 
                        ? `Appointments: ${formatCurrency(apptRevenue)} | Memberships: ${formatCurrency(membershipRevenue)}`
                        : `From ${formatNumber(data.length)} appointments`
                    }
                </div>
                ${comparisonData ? `<div class="comparison-details">vs ${formatCurrency(comparisonData.revenue)} last period</div>` : ''}
            </div>
            <div class="metric-card compact">
                <div class="metric-label">Appointments</div>
                <div class="metric-value">
                    ${formatNumber(data.length)}
                    ${comparisonData ? getComparisonIndicator(data.length, comparisonData.appointments) : ''}
                </div>
                <div class="metric-subtext">Total bookings</div>
                ${comparisonData ? `<div class="comparison-details">vs ${formatNumber(comparisonData.appointments)} last period</div>` : ''}
            </div>
            <div class="metric-card compact">
                <div class="metric-label">Unique Clients</div>
                <div class="metric-value">
                    ${formatNumber(uniqueClients)}
                    ${comparisonData ? getComparisonIndicator(uniqueClients, comparisonData.clients) : ''}
                </div>
                <div class="metric-subtext">${formatNumber(newClients)} new, ${formatNumber(returningClients)} returning</div>
                ${comparisonData ? `<div class="comparison-details">vs ${formatNumber(comparisonData.clients)} last period</div>` : ''}
            </div>
            ${avgUtilization !== null ? `
            <div class="metric-card compact success">
                <div class="metric-label">Utilization</div>
                <div class="metric-value">${avgUtilization.toFixed(1)}%</div>
                <div class="metric-subtext">Table time efficiency</div>
            </div>
            ` : ''}
            <div class="metric-card compact">
                <div class="metric-label">Revenue/Hour</div>
                <div class="metric-value">${formatCurrency(revenuePerHour)}</div>
                <div class="metric-subtext">${formatNumber(totalHours)} total hours</div>
            </div>
            <div class="metric-card compact">
                <div class="metric-label">Avg Ticket Size</div>
                <div class="metric-value">${formatCurrency(avgTicketSize)}</div>
                <div class="metric-subtext">Per appointment</div>
            </div>
            <div class="metric-card compact">
                <div class="metric-label">Client Frequency</div>
                <div class="metric-value">${avgVisitsPerClient.toFixed(1)}</div>
                <div class="metric-subtext">Avg visits per client</div>
            </div>
            <div class="metric-card compact">
                <div class="metric-label">Revenue per VSP</div>
                <div class="metric-value">${formatCurrency(revenuePerPractitioner)}</div>
                <div class="metric-subtext">${formatNumber(uniquePractitioners)} VSPs</div>
            </div>

            ${membershipRevenue > 0 ? `
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(123, 31, 162, 0.05)); border-left: 4px solid #9c27b0;">
                <div class="metric-label">💳 Total Memberships</div>
                <div class="metric-value">${formatNumber(membershipsData.filter(m => m.Expired !== 'Yes').length)}</div>
                <div class="metric-subtext">${formatNumber(membershipsData.length)} customers</div>
            </div>
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(32, 201, 151, 0.05)); border-left: 4px solid #28a745;">
                <div class="metric-label">💵 Membership Revenue</div>
                <div class="metric-value">${formatCurrency(membershipRevenue)}</div>
                <div class="metric-subtext">Avg ${formatCurrency(membershipRevenue / membershipsData.length)} per membership</div>
            </div>
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(0, 123, 255, 0.1), rgba(0, 86, 179, 0.05)); border-left: 4px solid #007bff;">
                <div class="metric-label">🔄 Monthly Recurring Revenue</div>
                <div class="metric-value">${formatCurrency(membershipsData.filter(m => m['Membership Type'] === 'subscription' && m.Expired !== 'Yes').reduce((sum, m) => sum + (parseFloat(m['Paid Amount']) || 0), 0))}</div>
                <div class="metric-subtext">From ${formatNumber(membershipsData.filter(m => m['Membership Type'] === 'subscription' && m.Expired !== 'Yes').length)} active subscriptions</div>
            </div>
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(33, 150, 243, 0.1), rgba(13, 71, 161, 0.05)); border-left: 4px solid #2196f3;">
                <div class="metric-label">❄️ Frozen Memberships</div>
                <div class="metric-value">${formatNumber(membershipsData.filter(m => m.Frozen === 'Yes').length)}</div>
                <div class="metric-subtext">${((membershipsData.filter(m => m.Frozen === 'Yes').length / membershipsData.length) * 100).toFixed(1)}% of total memberships</div>
            </div>
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(244, 67, 54, 0.1), rgba(211, 47, 47, 0.05)); border-left: 4px solid #f44336;">
                <div class="metric-label">💸 Refunded Memberships</div>
                <div class="metric-value">${formatNumber(membershipsData.filter(m => parseFloat(m.Refunded) > 0).length)}</div>
                <div class="metric-subtext">${formatCurrency(membershipsData.reduce((sum, m) => sum + (parseFloat(m.Refunded) || 0), 0))} total refunded</div>
            </div>
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 152, 0, 0.05)); border-left: 4px solid #ffc107;">
                <div class="metric-label">📊 Retention Rate</div>
                <div class="metric-value">${((membershipsData.filter(m => m.Expired !== 'Yes').length / membershipsData.length) * 100).toFixed(1)}%</div>
                <div class="metric-subtext">${formatNumber(membershipsData.filter(m => m.Expired !== 'Yes').length)} active of ${formatNumber(membershipsData.length)} total</div>
            </div>
            ${membershipCancellationsData && membershipCancellationsData.length > 0 ? `
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(244, 67, 54, 0.15), rgba(211, 47, 47, 0.08)); border-left: 4px solid #f44336;">
                <div class="metric-label">🚫 Total Cancellations</div>
                <div class="metric-value">${formatNumber(membershipCancellationsData.length)}</div>
                <div class="metric-subtext">${((membershipCancellationsData.length / membershipsData.length) * 100).toFixed(1)}% of total sales</div>
            </div>
            <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(255, 152, 0, 0.15), rgba(230, 81, 0, 0.08)); border-left: 4px solid #ff9800;">
                <div class="metric-label">📊 Churn Rate</div>
                <div class="metric-value">${((membershipCancellationsData.length / membershipsData.length) * 100).toFixed(1)}%</div>
                <div class="metric-subtext">Cancellations vs sales</div>
            </div>
            ` : ''}
            ` : ''}
        </div>
        
        <div class="table-container" style="background: linear-gradient(135deg, rgba(251, 181, 20, 0.05), rgba(251, 181, 20, 0.02)); border-left: 5px solid var(--highlight);">
            <h2>Financial Performance</h2>
            <div class="metrics-grid" style="grid-template-columns: repeat(${3 + (nonApptHours > 0 ? 1 : 0) + (salaryCosts.total > 0 ? 1 : 0)}, 1fr);">
                <div class="metric-card ${profit > 0 ? 'success' : 'danger'}">
                    <div class="metric-label">Net Profit</div>
                    <div class="metric-value">
                        ${formatCurrency(profit)}
                        ${comparisonData ? getComparisonIndicator(profit, comparisonData.profit, 'currency') : ''}
                    </div>
                    <div class="metric-subtext">${profitMargin.toFixed(1)}% margin</div>
                    ${comparisonData ? `<div class="comparison-details">vs ${formatCurrency(comparisonData.profit)} last period</div>` : ''}
                </div>
                <div class="metric-card warning">
                    <div class="metric-label">Total Labor Cost</div>
                    <div class="metric-value">${formatCurrency(totalLaborCost)}</div>
                    <div class="metric-subtext">${((totalLaborCost / totalRevenue) * 100).toFixed(1)}% of revenue</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Appointment Payouts</div>
                    <div class="metric-value">${formatCurrency(totalPayout)}</div>
                    <div class="metric-subtext">${formatNumber(totalHours)} appt hours</div>
                </div>
                ${nonApptHours > 0 ? `
                <div class="metric-card">
                    <div class="metric-label">Non-Appt Labor</div>
                    <div class="metric-value">${formatCurrency(nonApptLaborCost)}</div>
                    <div class="metric-subtext">${formatNumber(nonApptHours)} hrs @ ${formatCurrency(CONFIG.baseHourlyRate)}/hr</div>
                </div>
                ` : ''}
                ${salaryCosts.total > 0 ? `
                <div class="metric-card">
                    <div class="metric-label">Salaried Employees</div>
                    <div class="metric-value">${formatCurrency(salaryCosts.total)}</div>
                    <div class="metric-subtext">${salaryCosts.details.length} employee(s)</div>
                </div>
                ` : ''}
            </div>
            ${(nonApptHours > 0 || salaryCosts.total > 0) ? `
            <div class="alert info" style="margin-top: 15px;">
                <h4>💡 Labor Cost Breakdown</h4>
                <p style="margin: 8px 0;">
                    <strong>Appointment-Based Labor:</strong> ${formatCurrency(totalPayout)} 
                    (${formatNumber(totalHours)} hours at commission rates)<br>
                    ${nonApptHours > 0 ? `<strong>Non-Appointment Labor:</strong> ${formatCurrency(nonApptLaborCost)} 
                    (${formatNumber(nonApptHours)} hours at base rate of ${formatCurrency(CONFIG.baseHourlyRate)}/hr)<br>` : ''}
                    ${salaryCosts.total > 0 ? `<strong>Salaried Employees:</strong> ${formatCurrency(salaryCosts.total)}<br>
                    ${salaryCosts.details.map(emp => 
                        `&nbsp;&nbsp;• ${emp.name}: ${formatCurrency(emp.proratedCost)} (${emp.daysWorked} days @ ${formatCurrency(emp.annualSalary)}/year)`
                    ).join('<br>')}<br>` : ''}
                    <strong>Total Labor Cost:</strong> ${formatCurrency(totalLaborCost)} 
                    (${((totalLaborCost / totalRevenue) * 100).toFixed(1)}% of revenue)
                </p>
                <p style="margin-top: 10px; font-size: 12px; color: #666;">
                    ${nonApptHours > 0 ? 'Non-appointment hours include cleaning, admin work, training, and other clocked time without appointments. ' : ''}
                    ${salaryCosts.total > 0 ? 'Salaried employee costs are prorated based on their start dates. ' : ''}
                    Adjust settings in <strong>⚙️ Franchise Configuration</strong> for accurate profitability tracking.
                </p>
            </div>
            ` : ''}
        </div>
        
        <div class="table-container" style="background: linear-gradient(135deg, rgba(220, 53, 69, 0.05), rgba(220, 53, 69, 0.02)); border-left: 5px solid var(--danger);">
            <h2>Franchise Fees</h2>
            <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr);">
                <div class="metric-card danger">
                    <div class="metric-label">🏢 Franchise Fee</div>
                    <div class="metric-value">${formatCurrency(totalRevenue * CONFIG.franchiseFeePercent / 100)}</div>
                    <div class="metric-subtext">${CONFIG.franchiseFeePercent}% of revenue</div>
                </div>
                <div class="metric-card danger">
                    <div class="metric-label">🎯 Brand Fund</div>
                    <div class="metric-value">${formatCurrency(totalRevenue * CONFIG.brandFundPercent / 100)}</div>
                    <div class="metric-subtext">${CONFIG.brandFundPercent}% of revenue</div>
                </div>
                <div class="metric-card danger">
                    <div class="metric-label">💳 CC Processing</div>
                    <div class="metric-value">${formatCurrency(totalRevenue * CONFIG.ccFeesPercent / 100)}</div>
                    <div class="metric-subtext">${CONFIG.ccFeesPercent}% of revenue</div>
                </div>
                <div class="metric-card danger" style="background: linear-gradient(135deg, rgba(220, 53, 69, 0.15), rgba(220, 53, 69, 0.05));">
                    <div class="metric-label">💸 Total Fees</div>
                    <div class="metric-value">${formatCurrency(totalRevenue * (CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent) / 100)}</div>
                    <div class="metric-subtext">${((CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent)).toFixed(1)}% of revenue</div>
                </div>
            </div>
            <div class="alert info" style="margin-top: 15px;">
                <h4>💡 Fee Impact on Net Profit</h4>
                <p style="margin: 8px 0;">
                    <strong>Gross Revenue:</strong> ${formatCurrency(totalRevenue)}<br>
                    <strong>Less: Franchise Fees:</strong> -${formatCurrency(totalRevenue * (CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent) / 100)} 
                    (${((CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent)).toFixed(1)}% total)<br>
                    <strong>Less: Labor Costs:</strong> -${formatCurrency(totalLaborCost)}<br>
                    <strong>Net Profit After Fees & Labor:</strong> ${formatCurrency(totalRevenue - totalLaborCost - (totalRevenue * (CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent) / 100))} 
                    (${((totalRevenue - totalLaborCost - (totalRevenue * (CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent) / 100)) / totalRevenue * 100).toFixed(1)}% margin)
                </p>
                <p style="margin-top: 10px; font-size: 12px; color: #666;">
                    Configure fee percentages in <strong>⚙️ Franchise Configuration</strong> to match your franchise agreement.
                </p>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h3>Revenue by Location</h3>
                <div class="chart-wrapper">
                    <canvas id="revenueByLocationChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="interactive-badge" title="Click on any service to see practitioner breakdown"></div>
                <h3>Revenue by Service</h3>
                <div class="chart-wrapper">
                    <canvas id="revenueByServiceChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Introductory Offers</h3>
                <div class="chart-wrapper">
                    <canvas id="introSessionsChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="table-container">
            <h2>AI-Powered Recommendations</h2>
            <p style="margin-bottom: 20px; color: #666;">Smart insights based on your data patterns and industry best practices.</p>
            ${(() => {
                const recommendations = generateSmartRecommendations();
                if (recommendations.length === 0) {
                    return '<div class="alert success"><h4>🎉 Excellent Performance!</h4><p>Your metrics are strong across the board. Keep up the great work!</p></div>';
                }
                return recommendations.slice(0, 3).map(rec => `
                    <div class="recommendation-card">
                        <span class="recommendation-priority ${rec.priority}">${rec.priority.toUpperCase()} PRIORITY</span>
                        <div class="recommendation-title">${rec.title}</div>
                        <p style="margin: 10px 0; color: #666;">${rec.description}</p>
                        <p style="margin: 10px 0;"><strong>Recommended Action:</strong> ${rec.action}</p>
                        <div class="recommendation-impact">
                            <strong>💰 Potential Impact:</strong> ${rec.impact}
                        </div>
                    </div>
                `).join('');
            })()}
            <p style="margin-top: 15px; text-align: center; color: #666; font-style: italic;">
                View more recommendations in the <strong>💡 Insights</strong> tab
            </p>
        </div>
    `;
    
    document.getElementById('overview').innerHTML = html;
    
    // Render charts
    setTimeout(() => {
        renderRevenueByLocationChart();
        renderRevenueByServiceChart();
        renderIntroSessionsChart();
    }, 100);
}

// FUNNEL TAB

// RETENTION TAB

export function renderRetentionTab() {
    const data = filteredAppointments;
    const activeMemberEmails = getActiveMemberEmails();
    
    // Analyze client visits
    const clientVisits = {};
    const clientFirstVisit = {};
    const clientLastVisit = {};
    const clientRevenue = {};
    
    data.forEach(row => {
        const email = (row['Customer Email'] || '').toLowerCase().trim();
        if (!email) return;
        
        const date = parseDate(row['Appointment Date']);
        const revenue = parseFloat(row.Revenue || 0);
        // Only count revenue if customer is NOT an active member
        const revenueToAdd = activeMemberEmails.has(email) ? 0 : revenue;
        
        if (!clientVisits[email]) {
            clientVisits[email] = 0;
            clientFirstVisit[email] = date;
            clientLastVisit[email] = date;
            clientRevenue[email] = 0;
        }
        
        clientVisits[email]++;
        clientRevenue[email] += revenueToAdd;
        
        if (date < clientFirstVisit[email]) clientFirstVisit[email] = date;
        if (date > clientLastVisit[email]) clientLastVisit[email] = date;
    });
    
    // Calculate metrics
    const uniqueClients = Object.keys(clientVisits).length;
    const returningClients = Object.values(clientVisits).filter(count => count > 1).length;
    const retentionRate = uniqueClients > 0 ? (returningClients / uniqueClients * 100) : 0;
    const avgVisitsPerClient = uniqueClients > 0 ? data.length / uniqueClients : 0;
    
    // Visit frequency distribution
    const visitDist = { '1 visit': 0, '2-3 visits': 0, '4-6 visits': 0, '7-10 visits': 0, '11+ visits': 0 };
    Object.values(clientVisits).forEach(count => {
        if (count === 1) visitDist['1 visit']++;
        else if (count <= 3) visitDist['2-3 visits']++;
        else if (count <= 6) visitDist['4-6 visits']++;
        else if (count <= 10) visitDist['7-10 visits']++;
        else visitDist['11+ visits']++;
    });
    
    // Calculate average days between visits
    let totalDaysBetween = 0;
    let visitPairs = 0;
    
    Object.keys(clientVisits).forEach(email => {
        if (clientVisits[email] > 1) {
            const daysBetween = (clientLastVisit[email] - clientFirstVisit[email]) / (1000 * 60 * 60 * 24);
            const avgDaysForClient = daysBetween / (clientVisits[email] - 1);
            totalDaysBetween += avgDaysForClient;
            visitPairs++;
        }
    });
    
    const avgDaysBetweenVisits = visitPairs > 0 ? totalDaysBetween / visitPairs : 0;
    
    // Top clients by visits
    const topClientsByVisits = Object.entries(clientVisits)
        .map(([email, visits]) => ({
            email,
            visits,
            revenue: clientRevenue[email],
            firstVisit: clientFirstVisit[email],
            lastVisit: clientLastVisit[email]
        }))
        .sort((a, b) => b.visits - a.visits)
        .slice(0, 10);
    
    // Find client names from data
    const clientNames = {};
    data.forEach(row => {
        const email = (row['Customer Email'] || '').toLowerCase().trim();
        if (email && !clientNames[email]) {
            clientNames[email] = row['Customer Name'] || email;
        }
    });
    
    let html = `
        <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Total Clients</div>
                <div class="metric-value">${formatNumber(uniqueClients)}</div>
                <div class="metric-subtext">Unique individuals</div>
            </div>
            <div class="metric-card ${retentionRate >= 50 ? 'success' : retentionRate >= 30 ? 'warning' : 'danger'}">
                <div class="metric-label">Retention Rate</div>
                <div class="metric-value">${retentionRate.toFixed(1)}%</div>
                <div class="metric-subtext">${formatNumber(returningClients)} returning clients</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Visits</div>
                <div class="metric-value">${avgVisitsPerClient.toFixed(1)}</div>
                <div class="metric-subtext">Per client</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Days Between</div>
                <div class="metric-value">${avgDaysBetweenVisits.toFixed(0)}</div>
                <div class="metric-subtext">Days between visits</div>
            </div>
        </div>
        
        <div class="alert ${retentionRate >= 50 ? 'success' : 'warning'}">
            <h4>🔄 Retention Analysis</h4>
            <p><strong>Current Status:</strong> ${retentionRate.toFixed(0)}% of clients return for additional appointments.</p>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                <li>${visitDist['1 visit']} clients (${((visitDist['1 visit']/uniqueClients)*100).toFixed(0)}%) visited only once</li>
                <li>Average ${avgDaysBetweenVisits.toFixed(0)} days between visits for returning clients</li>
                <li>${returningClients} loyal clients generating repeat business</li>
            </ul>
            <p style="margin-top: 15px;"><strong>💡 Recommendations:</strong></p>
            <ul style="margin: 5px 0 0 20px; line-height: 1.8;">
                <li>Follow up with one-time visitors within ${Math.ceil(avgDaysBetweenVisits/2)} days</li>
                <li>Create membership packages for ${visitDist['4-6 visits'] + visitDist['7-10 visits'] + visitDist['11+ visits']} frequent visitors</li>
                <li>Send rebooking reminders every ${Math.floor(avgDaysBetweenVisits * 0.8)} days</li>
            </ul>
        </div>
        
        <div class="table-container">
            <h2>Visit Frequency Distribution</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0;">
                ${Object.entries(visitDist).map(([range, count]) => `
                    <div style="background: var(--gray-light); padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid var(--accent);">
                        <div style="font-size: 2.5em; font-weight: bold; color: var(--primary);">${formatNumber(count)}</div>
                        <div style="color: #666; font-size: 14px; margin-top: 5px;">${range} visit${range === '1' ? '' : 's'}</div>
                        <div style="color: var(--accent); font-size: 12px; margin-top: 3px;">${((count/uniqueClients)*100).toFixed(1)}%</div>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="table-container">
            <h2>Top 10 Clients by Visit Frequency</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Client</th>
                        <th>Total Visits</th>
                        <th>Total Revenue</th>
                        <th>Avg/Visit</th>
                        <th>First Visit</th>
                        <th>Last Visit</th>
                        <th>Days Between</th>
                    </tr>
                </thead>
                <tbody>
                    ${topClientsByVisits.map((client, i) => {
                        const avgPerVisit = client.revenue / client.visits;
                        const daysBetween = client.visits > 1 
                            ? Math.round((client.lastVisit - client.firstVisit) / (1000 * 60 * 60 * 24) / (client.visits - 1))
                            : 'N/A';
                        return `
                            <tr>
                                <td><strong>${i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}</strong></td>
                                <td>${clientNames[client.email] || client.email}</td>
                                <td><strong>${client.visits}</strong></td>
                                <td>${formatCurrency(client.revenue)}</td>
                                <td>${formatCurrency(avgPerVisit)}</td>
                                <td>${client.firstVisit.toLocaleDateString()}</td>
                                <td>${client.lastVisit.toLocaleDateString()}</td>
                                <td>${daysBetween}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
        
        <div class="table-container">
            <h2>At-Risk Clients</h2>
            <p style="margin-bottom: 15px; color: #666;">Returning clients who haven't visited in over ${Math.floor(avgDaysBetweenVisits * 1.5)} days (1.5x average gap)</p>
            ${(() => {
                const today = new Date();
                const atRiskClients = topClientsByVisits
                    .filter(client => client.visits > 1)
                    .map(client => {
                        const daysSinceLastVisit = Math.floor((today - client.lastVisit) / (1000 * 60 * 60 * 24));
                        return { ...client, daysSinceLastVisit };
                    })
                    .filter(client => client.daysSinceLastVisit > avgDaysBetweenVisits * 1.5)
                    .sort((a, b) => b.revenue - a.revenue)
                    .slice(0, 20);
                
                if (atRiskClients.length === 0) {
                    return '<div class="alert success"><h4>🎉 Great News!</h4><p>No at-risk clients identified. All returning clients are visiting regularly!</p></div>';
                }
                
                const totalAtRiskRevenue = atRiskClients.reduce((sum, c) => sum + c.revenue, 0);
                
                return `
                    <div class="alert warning">
                        <h4>📊 At-Risk Analysis</h4>
                        <p><strong>${atRiskClients.length} returning clients</strong> haven't visited recently. They represent <strong>${formatCurrency(totalAtRiskRevenue)}</strong> in historical revenue.</p>
                        <p style="margin-top: 10px;"><strong>Action:</strong> Reach out with a "We miss you" message and a special comeback offer.</p>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Client</th>
                                <th>Total Visits</th>
                                <th>Revenue</th>
                                <th>Last Visit</th>
                                <th>Days Ago</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${atRiskClients.map(client => {
                                const urgency = client.daysSinceLastVisit > avgDaysBetweenVisits * 2 ? 'HIGH' : 'MEDIUM';
                                const urgencyColor = urgency === 'HIGH' ? '#dc3545' : '#ffc107';
                                return `
                                    <tr>
                                        <td>${clientNames[client.email] || client.email}</td>
                                        <td>${client.visits}</td>
                                        <td>${formatCurrency(client.revenue)}</td>
                                        <td>${client.lastVisit.toLocaleDateString()}</td>
                                        <td><strong>${client.daysSinceLastVisit}</strong> days</td>
                                        <td><span style="background: ${urgencyColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">${urgency}</span></td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                `;
            })()}
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="interactive-badge" title="Click on any bar to see detailed client list"></div>
                <h3>Visit Frequency Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="visitFrequencyChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="interactive-badge" title="Click on any segment to see client details"></div>
                <h3>Retention Breakdown</h3>
                <div class="chart-wrapper">
                    <canvas id="retentionBreakdownChart"></canvas>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('retention').innerHTML = html;
    
    // Render charts
    setTimeout(() => {
        renderVisitFrequencyChart(visitDist);
        renderRetentionBreakdownChart(uniqueClients - returningClients, returningClients);
    }, 100);
}

// STUDIOS TAB

export function renderStudiosTab() {
    const data = filteredAppointments;
    const activeMemberEmails = getActiveMemberEmails();
    
    // Get all unique locations
    const locations = [...new Set(data.map(row => row.Location).filter(l => l))].sort();
    
    if (locations.length === 0) {
        document.getElementById('studios').innerHTML = `
            <div class="alert info">
                <h4>📍 Studio Analytics</h4>
                <p>No location data available. Upload appointment data with location information to see studio-specific metrics.</p>
            </div>
        `;
        return;
    }
    
    // Calculate metrics for each studio
    const studioMetrics = {};
    
    locations.forEach(location => {
        const locationData = data.filter(row => row.Location === location);
        
        // Group by month for trends
        const monthlyData = {};
        
        locationData.forEach(row => {
            const date = parseDate(row['Appointment Date']);
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            
            if (!monthlyData[monthKey]) {
                monthlyData[monthKey] = {
                    appointments: 0,
                    revenue: 0,
                    hours: 0,
                    clockedHours: 0,
                    clients: new Set()
                };
            }
            
            const email = (row['Customer Email'] || '').toLowerCase().trim();
            const revenue = parseFloat(row.Revenue || 0);
            const revenueToAdd = activeMemberEmails.has(email) ? 0 : revenue;
            
            monthlyData[monthKey].appointments++;
            monthlyData[monthKey].revenue += revenueToAdd;
            monthlyData[monthKey].hours += parseFloat(row['Time (h)'] || 0);
            if (email) monthlyData[monthKey].clients.add(email);
        });
        
        // Add clocked hours if available
        if (window.timeTrackingData && window.timeTrackingData.length > 0) {
            window.timeTrackingData.forEach(row => {
                if (row.Location === location) {
                    const clockedIn = row['Clocked in'] ? new Date(row['Clocked in']) : null;
                    if (clockedIn) {
                        const monthKey = `${clockedIn.getFullYear()}-${String(clockedIn.getMonth() + 1).padStart(2, '0')}`;
                        if (monthlyData[monthKey]) {
                            monthlyData[monthKey].clockedHours += parseFloat(row['Duration (h)'] || 0);
                        }
                    }
                }
            });
        }
        
        // Calculate totals and averages
        const totalRevenue = locationData.reduce((sum, row) => {
            const email = (row['Customer Email'] || '').toLowerCase().trim();
            const revenue = parseFloat(row.Revenue || 0);
            return sum + (activeMemberEmails.has(email) ? 0 : revenue);
        }, 0);
        
        const totalAppointments = locationData.length;
        const uniqueClients = new Set(locationData.map(row => (row['Customer Email'] || '').toLowerCase().trim()).filter(e => e)).size;
        const avgRevenuePerAppt = totalAppointments > 0 ? totalRevenue / totalAppointments : 0;
        
        // Calculate lead conversion for this location
        let locationLeads = [];
        let locationIntros = 0;
        let locationPaid = 0;
        
        // Try filteredLeadsConverted first (converted leads report)
        if (filteredLeadsConverted && filteredLeadsConverted.length > 0) {
            locationLeads = filteredLeadsConverted.filter(lead => lead['Home location'] === location);
            const convertedLeads = locationLeads.filter(l => {
                const convertedTo = (l['Converted to'] || '').trim();
                return convertedTo && convertedTo !== 'N/A' && convertedTo !== '';
            });
            locationIntros = convertedLeads.length;
            locationPaid = convertedLeads.filter(l => (l['Converted to'] || '').toLowerCase().includes('paid')).length;
        } 
        // Fall back to filteredLeads (new leads & customers report)
        else if (filteredLeads && filteredLeads.length > 0) {
            locationLeads = filteredLeads.filter(lead => (lead['Home location'] || lead['Location']) === location);
            const customers = locationLeads.filter(l => l.Type === 'Customer');
            locationIntros = customers.length;
            locationPaid = customers.filter(l => parseLTV(l.LTV) > 0).length;
        }
        
        const leadToIntroRate = locationLeads.length > 0 ? (locationIntros / locationLeads.length * 100) : 0;
        const introToPaidRate = locationIntros > 0 ? (locationPaid / locationIntros * 100) : 0;
        
        studioMetrics[location] = {
            totalRevenue,
            totalAppointments,
            uniqueClients,
            avgRevenuePerAppt,
            monthlyData,
            leads: locationLeads.length,
            intros: locationIntros,
            paid: locationPaid,
            leadToIntroRate,
            introToPaidRate
        };
    });
    
    // Build HTML with comparison table first
    let html = `
        <h2 style="margin-bottom: 20px;">📍 Studio Performance Overview</h2>
        
        <!-- Studio Comparison Table -->
        <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 30px; overflow-x: auto;">
            <h3 style="margin-bottom: 15px; color: var(--primary);">📊 Studio Comparison</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background: var(--gray-light); border-bottom: 2px solid var(--accent);">
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Studio</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600;">Total Revenue</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600;">Appointments</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600;">Unique Clients</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600;">Avg $/Appt</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600;">Total Leads</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600;">Lead→Intro</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600;">Intro→Paid</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Sort studios by total revenue for comparison
    const sortedLocations = [...locations].sort((a, b) => 
        studioMetrics[b].totalRevenue - studioMetrics[a].totalRevenue
    );
    
    sortedLocations.forEach((location, idx) => {
        const metrics = studioMetrics[location];
        const rowStyle = idx % 2 === 0 ? 'background: #f9f9f9;' : '';
        html += `
            <tr style="${rowStyle} border-bottom: 1px solid var(--gray);">
                <td style="padding: 12px; font-weight: 600; color: var(--primary);">${location}</td>
                <td style="padding: 12px; text-align: right;">${formatCurrency(metrics.totalRevenue)}</td>
                <td style="padding: 12px; text-align: right;">${formatNumber(metrics.totalAppointments)}</td>
                <td style="padding: 12px; text-align: right;">${formatNumber(metrics.uniqueClients)}</td>
                <td style="padding: 12px; text-align: right;">${formatCurrency(metrics.avgRevenuePerAppt)}</td>
                <td style="padding: 12px; text-align: right;">${metrics.leads > 0 ? formatNumber(metrics.leads) : 'N/A'}</td>
                <td style="padding: 12px; text-align: right; ${metrics.leadToIntroRate > 50 ? 'color: var(--success); font-weight: 600;' : ''}">${metrics.leads > 0 ? metrics.leadToIntroRate.toFixed(1) + '%' : 'N/A'}</td>
                <td style="padding: 12px; text-align: right; ${metrics.introToPaidRate > 50 ? 'color: var(--success); font-weight: 600;' : ''}">${metrics.intros > 0 ? metrics.introToPaidRate.toFixed(1) + '%' : 'N/A'}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        
        <!-- Quick Stats Cards -->
        <div class="metrics-grid" style="grid-template-columns: repeat(${Math.min(locations.length, 4)}, 1fr); margin-bottom: 30px;">
    `;
    
    sortedLocations.forEach(location => {
        const metrics = studioMetrics[location];
        html += `
            <div class="metric-card">
                <div class="metric-label">${location}</div>
                <div class="metric-value">${formatCurrency(metrics.totalRevenue)}</div>
                <div class="metric-subtext">${formatNumber(metrics.totalAppointments)} appointments • ${formatNumber(metrics.uniqueClients)} clients</div>
            </div>
        `;
    });
    
    html += `</div>`;
    
    // Add customer distribution by Home Location if available
    if (filteredLeads && filteredLeads.length > 0) {
        const homeLocationCounts = {};
        let totalWithHomeLocation = 0;
        
        filteredLeads.forEach(lead => {
            const homeLocation = lead['Home location'] || 'Unknown';
            if (homeLocation !== 'Unknown') {
                homeLocationCounts[homeLocation] = (homeLocationCounts[homeLocation] || 0) + 1;
                totalWithHomeLocation++;
            }
        });
        
        if (totalWithHomeLocation > 0) {
            html += `
                <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 30px;">
                    <h3 style="margin-bottom: 15px; color: var(--primary);">🏠 Customer Home Location Distribution</h3>
                    <p style="color: #666; margin-bottom: 15px;">Based on ${totalWithHomeLocation.toLocaleString()} customers with recorded home location</p>
                    <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
            `;
            
            Object.entries(homeLocationCounts)
                .sort((a, b) => b[1] - a[1])
                .forEach(([location, count]) => {
                    const percentage = ((count / totalWithHomeLocation) * 100).toFixed(1);
                    html += `
                        <div class="metric-card compact">
                            <div class="metric-label">${location}</div>
                            <div class="metric-value">${count.toLocaleString()}</div>
                            <div class="metric-subtext">${percentage}% of customers</div>
                        </div>
                    `;
                });
            
            html += `
                    </div>
                </div>
            `;
        }
    }
    
    // Continue with detailed studio sections
    
    // Add detailed studio sections (sorted by revenue)
    sortedLocations.forEach(location => {
        const metrics = studioMetrics[location];
        const months = Object.keys(metrics.monthlyData).sort();
        
        // Calculate utilization for each month
        const monthlyUtilization = months.map(month => {
            const data = metrics.monthlyData[month];
            return data.clockedHours > 0 ? (data.hours / data.clockedHours * 100) : null;
        });
        
        const avgUtilization = monthlyUtilization.filter(u => u !== null).length > 0
            ? monthlyUtilization.filter(u => u !== null).reduce((sum, u) => sum + u, 0) / monthlyUtilization.filter(u => u !== null).length
            : null;
        
        html += `
            <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 30px; border-top: 4px solid var(--primary);">
                <h2 style="margin-bottom: 20px;">📍 ${location}</h2>
                
                <div class="metrics-grid" style="grid-template-columns: repeat(5, 1fr); margin-bottom: 20px;">
                    <div class="metric-card compact">
                        <div class="metric-label">Total Revenue</div>
                        <div class="metric-value">${formatCurrency(metrics.totalRevenue)}</div>
                        <div class="metric-subtext">All time</div>
                    </div>
                    <div class="metric-card compact">
                        <div class="metric-label">Appointments</div>
                        <div class="metric-value">${formatNumber(metrics.totalAppointments)}</div>
                        <div class="metric-subtext">${formatNumber(metrics.uniqueClients)} clients</div>
                    </div>
                    <div class="metric-card compact">
                        <div class="metric-label">Avg Revenue/Appt</div>
                        <div class="metric-value">${formatCurrency(metrics.avgRevenuePerAppt)}</div>
                        <div class="metric-subtext">Per appointment</div>
                    </div>
                    ${avgUtilization !== null ? `
                    <div class="metric-card compact success">
                        <div class="metric-label">Avg Utilization</div>
                        <div class="metric-value">${avgUtilization.toFixed(1)}%</div>
                        <div class="metric-subtext">Table time</div>
                    </div>
                    ` : '<div class="metric-card compact"><div class="metric-label">Utilization</div><div class="metric-value">N/A</div></div>'}
                    ${metrics.leads > 0 ? `
                    <div class="metric-card compact">
                        <div class="metric-label">Total Leads</div>
                        <div class="metric-value">${formatNumber(metrics.leads)}</div>
                        <div class="metric-subtext">${metrics.intros} intros</div>
                    </div>
                    ` : '<div class="metric-card compact"><div class="metric-label">Leads</div><div class="metric-value">N/A</div></div>'}
                </div>
                
                ${metrics.leads > 0 ? `
                <div class="metrics-grid" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 20px;">
                    <div class="metric-card">
                        <div class="metric-label">Lead → Intro Conversion</div>
                        <div class="metric-value">${metrics.leadToIntroRate.toFixed(1)}%</div>
                        <div class="metric-subtext">${metrics.intros} of ${metrics.leads} leads</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Intro → Paid Conversion</div>
                        <div class="metric-value">${metrics.introToPaidRate.toFixed(1)}%</div>
                        <div class="metric-subtext">${metrics.paid} of ${metrics.intros} intros</div>
                    </div>
                </div>
                ` : ''}
                
                <div class="charts-grid">
                    ${avgUtilization !== null ? `
                    <div class="chart-container">
                        <h3>Monthly Utilization Trend</h3>
                        <div class="chart-wrapper">
                            <canvas id="studioUtilization${location.replace(/\s+/g, '')}Chart"></canvas>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${metrics.leads > 0 ? `
                    <div class="chart-container">
                        <h3>Monthly Conversion Rates</h3>
                        <div class="chart-wrapper">
                            <canvas id="studioConversion${location.replace(/\s+/g, '')}Chart"></canvas>
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="chart-container">
                        <h3>Monthly Revenue</h3>
                        <div class="chart-wrapper">
                            <canvas id="studioRevenue${location.replace(/\s+/g, '')}Chart"></canvas>
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Monthly Appointments</h3>
                        <div class="chart-wrapper">
                            <canvas id="studioAppointments${location.replace(/\s+/g, '')}Chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    document.getElementById('studios').innerHTML = html;
    
    // Render charts
    setTimeout(() => {
        sortedLocations.forEach(location => {
            const metrics = studioMetrics[location];
            const months = Object.keys(metrics.monthlyData).sort();
            const locationId = location.replace(/\s+/g, '');
            
            // Format month labels
            const monthLabels = months.map(m => {
                const [year, month] = m.split('-');
                const date = new Date(year, parseInt(month) - 1);
                return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
            });
            
            // Utilization chart
            const utilizationCanvas = document.getElementById(`studioUtilization${locationId}Chart`);
            if (utilizationCanvas) {
                const utilizationData = months.map(month => {
                    const data = metrics.monthlyData[month];
                    return data.clockedHours > 0 ? ((data.hours / data.clockedHours) * 100).toFixed(1) : null;
                });
                
                destroyChart(`studioUtilization${locationId}`);
                const ctx = utilizationCanvas.getContext('2d');
                allCharts[`studioUtilization${locationId}`] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: monthLabels,
                        datasets: [{
                            label: 'Utilization %',
                            data: utilizationData,
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                ticks: {
                                    callback: function(value) { return value + '%'; }
                                }
                            }
                        }
                    }
                });
            }
            
            // Conversion rates chart
            const conversionCanvas = document.getElementById(`studioConversion${locationId}Chart`);
            if (conversionCanvas && metrics.leads > 0) {
                destroyChart(`studioConversion${locationId}`);
                const ctx = conversionCanvas.getContext('2d');
                allCharts[`studioConversion${locationId}`] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Lead → Intro', 'Intro → Paid'],
                        datasets: [{
                            label: 'Conversion Rate %',
                            data: [metrics.leadToIntroRate, metrics.introToPaidRate],
                            backgroundColor: ['#71BED2', '#FBB514'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                ticks: {
                                    callback: function(value) { return value + '%'; }
                                }
                            }
                        }
                    }
                });
            }
            
            // Revenue chart
            const revenueCanvas = document.getElementById(`studioRevenue${locationId}Chart`);
            if (revenueCanvas) {
                const revenueData = months.map(month => metrics.monthlyData[month].revenue);
                
                destroyChart(`studioRevenue${locationId}`);
                const ctx = revenueCanvas.getContext('2d');
                allCharts[`studioRevenue${locationId}`] = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: monthLabels,
                        datasets: [{
                            label: 'Revenue',
                            data: revenueData,
                            backgroundColor: '#71BED2',
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return formatCurrency(context.parsed.y);
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return formatCurrency(value);
                                    }
                                }
                            }
                        }
                    }
                });
            }
            
            // Appointments chart
            const appointmentsCanvas = document.getElementById(`studioAppointments${locationId}Chart`);
            if (appointmentsCanvas) {
                const appointmentsData = months.map(month => metrics.monthlyData[month].appointments);
                
                destroyChart(`studioAppointments${locationId}`);
                const ctx = appointmentsCanvas.getContext('2d');
                allCharts[`studioAppointments${locationId}`] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: monthLabels,
                        datasets: [{
                            label: 'Appointments',
                            data: appointmentsData,
                            borderColor: '#013160',
                            backgroundColor: 'rgba(1, 49, 96, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { stepSize: 1 }
                            }
                        }
                    }
                });
            }
        });
    }, 100);
}

// SCHEDULE OPTIMIZATION TAB

export function renderScheduleTab() {
    const data = filteredAppointments;
    
    // Group appointments by practitioner and date
    const scheduleByPractitioner = {};
    
    data.forEach(row => {
        const practitioner = `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`;
        const date = parseDate(row['Appointment Date']);
        const dateKey = date.toLocaleDateString();
        
        if (!scheduleByPractitioner[practitioner]) {
            scheduleByPractitioner[practitioner] = {};
        }
        
        if (!scheduleByPractitioner[practitioner][dateKey]) {
            scheduleByPractitioner[practitioner][dateKey] = [];
        }
        
        scheduleByPractitioner[practitioner][dateKey].push({
            time: date,
            duration: parseFloat(row['Time (h)'] || 0),
            revenue: parseFloat(row.Revenue || 0),
            service: row['Appointment'] || 'Unknown'
        });
    });
    
    // Calculate gaps and efficiency
    const gapAnalysis = [];
    let totalGaps = 0;
    let totalGapMinutes = 0;
    let totalWorkingHours = 0;
    let totalPayout = 0;
    let totalRevenueForPayout = 0;
    
    Object.entries(scheduleByPractitioner).forEach(([practitioner, dates]) => {
        Object.entries(dates).forEach(([date, appointments]) => {
            // Sort by time
            appointments.sort((a, b) => a.time - b.time);
            
            if (appointments.length < 2) return;
            
            let dayGaps = 0;
            let dayGapMinutes = 0;
            let dayWorkingHours = 0;
            
            // Calculate gaps between appointments
            for (let i = 0; i < appointments.length - 1; i++) {
                const current = appointments[i];
                const next = appointments[i + 1];
                
                const currentEnd = new Date(current.time.getTime() + current.duration * 60 * 60 * 1000);
                const gapMinutes = (next.time - currentEnd) / (1000 * 60);
                
                if (gapMinutes > 15) { // Consider gaps over 15 minutes
                    dayGaps++;
                    dayGapMinutes += gapMinutes;
                    totalGaps++;
                    totalGapMinutes += gapMinutes;
                }
                
                dayWorkingHours += current.duration;
            }
            
            if (appointments.length > 0) {
                dayWorkingHours += appointments[appointments.length - 1].duration;
            }
            
            totalWorkingHours += dayWorkingHours;
            
            const utilizationRate = dayWorkingHours > 0 
                ? ((dayWorkingHours - (dayGapMinutes / 60)) / dayWorkingHours * 100) 
                : 0;
            
            if (dayGaps > 0) {
                gapAnalysis.push({
                    practitioner,
                    date,
                    appointments: appointments.length,
                    gaps: dayGaps,
                    gapMinutes: dayGapMinutes,
                    workingHours: dayWorkingHours,
                    utilizationRate,
                    potentialRevenue: (dayGapMinutes / 60) * 150
                });
            }
        });
    });
    
    // Calculate average hourly payout for lost wages calculation
    data.forEach(row => {
        totalPayout += parseFloat(row['Total Payout'] || 0);
        totalRevenueForPayout += parseFloat(row.Revenue || 0);
    });
    
    const avgPayoutRate = totalRevenueForPayout > 0 ? (totalPayout / totalRevenueForPayout) : 0.5;
    const avgHourlyRevenue = 150; // Assumed from potential revenue calc
    const avgHourlyPayout = avgHourlyRevenue * avgPayoutRate;
    const lostWages = (totalGapMinutes / 60) * avgHourlyPayout;
    
    // Sort by largest gaps
    gapAnalysis.sort((a, b) => b.gapMinutes - a.gapMinutes);
    
    // Calculate overall metrics
    const avgGapMinutes = totalGaps > 0 ? totalGapMinutes / totalGaps : 0;
    const overallUtilization = totalWorkingHours > 0 
        ? ((totalWorkingHours - (totalGapMinutes / 60)) / totalWorkingHours * 100) 
        : 0;
    const potentialRevenue = (totalGapMinutes / 60) * 150;
    const costOfGap = potentialRevenue - lostWages; // Business lost profit (revenue that would have stayed with business)
    
    let html = `
        <div class="metrics-grid" style="grid-template-columns: repeat(6, 1fr);">
            <div class="metric-card ${overallUtilization >= 80 ? 'success' : overallUtilization >= 60 ? 'warning' : 'danger'}">
                <div class="metric-label">Schedule Efficiency</div>
                <div class="metric-value">${overallUtilization.toFixed(1)}%</div>
                <div class="metric-subtext">Overall utilization</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Gaps</div>
                <div class="metric-value">${formatNumber(totalGaps)}</div>
                <div class="metric-subtext">${(totalGapMinutes / 60).toFixed(1)} hours</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Gap Duration</div>
                <div class="metric-value">${avgGapMinutes.toFixed(0)} min</div>
                <div class="metric-subtext">Per gap</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-label">Cost of Gap</div>
                <div class="metric-value">${formatCurrency(costOfGap)}</div>
                <div class="metric-subtext">Lost business profit</div>
            </div>
            <div class="metric-card danger">
                <div class="metric-label">Lost Wages</div>
                <div class="metric-value">${formatCurrency(lostWages)}</div>
                <div class="metric-subtext">VSP opportunity cost</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">Potential Revenue</div>
                <div class="metric-value">${formatCurrency(potentialRevenue)}</div>
                <div class="metric-subtext">From filling gaps</div>
            </div>
        </div>
        
        <div class="table-container" style="position: relative;">
            <div class="interactive-badge" title="Click any day to see detailed breakdown" style="position: absolute; top: 15px; right: 15px; display: flex;"></div>
            <h2>Appointment Heatmap by Location</h2>
            <p style="margin-bottom: 15px; color: #666;">Busiest appointment times by day and hour (Monday-Saturday). Click any day to see detailed breakdown.</p>
            <div id="heatmapContainer"></div>
        </div>
        
        <div class="alert ${overallUtilization >= 80 ? 'success' : overallUtilization >= 60 ? 'warning' : 'info'}">
            <h4>⏰ Schedule Optimization Insights</h4>
            <p>
                ${overallUtilization >= 80 
                    ? '✅ Excellent scheduling efficiency! Your practitioners have minimal gaps.' 
                    : overallUtilization >= 60
                    ? '⚠️ Good scheduling, but there are opportunities to fill gaps and increase revenue.'
                    : '📈 Significant scheduling gaps detected. Optimizing could substantially increase revenue.'}
            </p>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                <li>Offer discounted "fill-in" appointments for last-minute bookings</li>
                <li>Block schedule appointments closer together when possible</li>
                <li>Consider adding express services (30-45 min) to fill small gaps</li>
                <li>Review practitioner availability patterns to match demand</li>
                <li><strong>Cost to business:</strong> ${formatCurrency(costOfGap)} in lost profit from scheduling gaps</li>
                <li><strong>Lost wages for VSPs:</strong> ${formatCurrency(lostWages)} in opportunity cost</li>
                <li><strong>Potential additional revenue:</strong> ${formatCurrency(potentialRevenue)} by filling all gaps</li>
            </ul>
        </div>
        
        <div class="table-container">
            <h2>Top 20 Days with Largest Scheduling Gaps</h2>
            <p style="margin-bottom: 15px; color: #666;">Opportunities to optimize scheduling and increase revenue</p>
            <table>
                <thead>
                    <tr>
                        <th>Practitioner</th>
                        <th>Date</th>
                        <th>Appointments</th>
                        <th>Gaps</th>
                        <th>Gap Time</th>
                        <th>Utilization</th>
                        <th>Opportunity</th>
                    </tr>
                </thead>
                <tbody>
                    ${gapAnalysis.slice(0, 20).map(day => `
                        <tr>
                            <td>${day.practitioner}</td>
                            <td>${day.date}</td>
                            <td>${day.appointments}</td>
                            <td>${day.gaps}</td>
                            <td>${day.gapMinutes.toFixed(0)} min</td>
                            <td><span style="color: ${day.utilizationRate >= 80 ? 'var(--success)' : day.utilizationRate >= 60 ? 'var(--warning)' : 'var(--danger)'}">${day.utilizationRate.toFixed(1)}%</span></td>
                            <td>${formatCurrency(day.potentialRevenue)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('schedule').innerHTML = html;
    
    // Render heatmap after setting innerHTML
    setTimeout(() => {
        renderHeatmap();
    }, 100);
}

// CLIENT SEGMENTATION FUNCTIONS

export function calculateClientSegments() {
    const today = new Date();
    const segments = {
        vip: [],
        atRisk: [],
        newClient: [],
        highFrequency: [],
        inactivePaidMember: []
    };
    
    // Get current VIP threshold from LTV tier configuration
    const currentTierConfig = LTV_TIERS[CONFIG.ltvTiers];
    const vipMin = currentTierConfig.vipMin;
    
    // Create a map of customer data with visit information
    const customerMap = {};
    
    // Aggregate data from leadsData
    filteredLeads.forEach(lead => {
        const email = lead['E-mail'];
        if (email && !customerMap[email]) {
            customerMap[email] = {
                firstName: lead['First name'],
                lastName: lead['Last name'],
                email: email,
                type: lead.Type,
                ltv: parseLTV(lead.LTV),
                joinDate: lead['Join date'],
                visits: [],
                totalVisits: 0,
                lastVisitDate: null,
                hasActiveMembership: false,
                membershipName: null,
                membershipAmount: 0
            };
        }
    });
    
    // Add membership information
    filteredMemberships.forEach(membership => {
        const email = membership['Customer Email'];
        const expired = membership.Expired === 'Yes';
        const frozen = membership.Frozen === 'Yes';
        
        if (email && customerMap[email] && !expired && !frozen) {
            customerMap[email].hasActiveMembership = true;
            customerMap[email].membershipName = membership['Membership Name'];
            customerMap[email].membershipAmount = parseFloat(membership['Paid Amount'] || 0);
        }
    });
    
    // Add appointment visit data
    filteredAppointments.forEach(appt => {
        const email = appt['Customer Email'];
        const apptDate = new Date(appt['Appointment Date']);
        
        if (email && customerMap[email]) {
            customerMap[email].visits.push(apptDate);
            customerMap[email].totalVisits++;
            
            if (!customerMap[email].lastVisitDate || apptDate > customerMap[email].lastVisitDate) {
                customerMap[email].lastVisitDate = apptDate;
            }
        }
    });
    
    // Categorize customers into segments
    Object.values(customerMap).forEach(customer => {
        // VIP tier (use dynamic vipMin from tier configuration)
        if (customer.ltv > vipMin) {
            segments.vip.push({...customer, segment: 'VIP'});
        }
        
        // Inactive Paid Member (has active membership but no visit in 30+ days)
        if (customer.hasActiveMembership) {
            const daysSinceLastVisit = customer.lastVisitDate 
                ? Math.floor((today - customer.lastVisitDate) / (1000 * 60 * 60 * 24))
                : 999; // Large number if no visit ever
            
            if (daysSinceLastVisit >= 30) {
                segments.inactivePaidMember.push({
                    ...customer, 
                    daysSinceLastVisit, 
                    segment: 'Inactive Paid Member'
                });
            }
        }
        
        // At-risk tier (haven't visited in 45+ days, with at least $50 revenue)
        if (customer.lastVisitDate) {
            const daysSinceLastVisit = Math.floor((today - customer.lastVisitDate) / (1000 * 60 * 60 * 24));
            if (daysSinceLastVisit >= 45 && customer.totalVisits > 0 && customer.ltv >= 50) {
                segments.atRisk.push({...customer, daysSinceLastVisit, segment: 'At-Risk'});
            }
        }
        
        // New client tier (<3 visits, with at least $50 revenue)
        if (customer.totalVisits > 0 && customer.totalVisits < 3 && customer.ltv >= 50) {
            segments.newClient.push({...customer, segment: 'New Client'});
        }
        
        // High-frequency tier (weekly visitors - 4+ visits per month)
        if (customer.visits.length >= 4) {
            // Calculate visit frequency
            const sortedVisits = customer.visits.sort((a, b) => a - b);
            const firstVisit = sortedVisits[0];
            const lastVisit = sortedVisits[sortedVisits.length - 1];
            const daysBetween = Math.floor((lastVisit - firstVisit) / (1000 * 60 * 60 * 24)) || 1;
            const visitsPerWeek = (customer.visits.length / daysBetween) * 7;
            
            if (visitsPerWeek >= 1) {
                segments.highFrequency.push({...customer, visitsPerWeek, segment: 'High-Frequency'});
            }
        }
    });
    
    return segments;
}

export function downloadSegmentCSV(segmentName, segmentData) {
    if (segmentData.length === 0) {
        alert('No clients in this segment to download.');
        return;
    }
    
    // Prepare CSV data
    const headers = ['First Name', 'Last Name', 'Email', 'Type', 'LTV', 'Total Visits', 'Last Visit Date', 'Membership', 'Membership Amount', 'Segment Info'];
    const rows = segmentData.map(client => {
        let segmentInfo = '';
        if (client.daysSinceLastVisit !== undefined) {
            segmentInfo = `${client.daysSinceLastVisit} days since last visit`;
        } else if (client.visitsPerWeek !== undefined) {
            segmentInfo = `${client.visitsPerWeek.toFixed(1)} visits/week`;
        } else {
            segmentInfo = client.segment;
        }
        
        return [
            client.firstName || '',
            client.lastName || '',
            client.email || '',
            client.type || '',
            client.ltv.toFixed(2),
            client.totalVisits,
            client.lastVisitDate ? client.lastVisitDate.toLocaleDateString() : 'N/A',
            client.membershipName || 'None',
            client.membershipAmount ? client.membershipAmount.toFixed(2) : '0.00',
            segmentInfo
        ];
    });
    
    // Create CSV content
    let csvContent = headers.join(',') + '\\n';
    csvContent += rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\\n');
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `${segmentName.replace(/\\s+/g, '_')}_Segment_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


export function renderClientSegmentation() {
    const segments = calculateClientSegments();
    
    // Get current VIP threshold from LTV tier configuration
    const currentTierConfig = LTV_TIERS[CONFIG.ltvTiers];
    const vipMin = currentTierConfig.vipMin;
    
    // Calculate summary stats
    const totalSegmented = segments.vip.length + segments.atRisk.length + 
                           segments.newClient.length + segments.highFrequency.length +
                           segments.inactivePaidMember.length;
    const vipRevenue = segments.vip.reduce((sum, c) => sum + c.ltv, 0);
    const atRiskRevenue = segments.atRisk.reduce((sum, c) => sum + c.ltv, 0);
    const inactiveMemberRevenue = segments.inactivePaidMember.reduce((sum, c) => sum + c.membershipAmount, 0);
    const newClientPotential = segments.newClient.length * (filteredLeads.reduce((sum, l) => sum + parseLTV(l.LTV), 0) / filteredLeads.length);
    
    return `
        <div class="segmentation-container">
            <div class="segmentation-header">
                <h2>Advanced Client Segmentation</h2>
                <p style="color: #666; font-size: 14px;">Strategic client groups for targeted engagement and retention</p>
            </div>
            
            <div class="segmentation-grid">
                <!-- VIP Tier -->
                <div class="segment-card vip">
                    <div class="segment-icon">👑</div>
                    <div class="segment-title">VIP Clients</div>
                    <div class="segment-description">High-value clients with >${formatCurrency(vipMin)} lifetime value</div>
                    <div class="segment-count">${formatNumber(segments.vip.length)}</div>
                    <div class="segment-stats">
                        <div class="segment-stats-row">
                            <span>Total Revenue:</span>
                            <strong>${formatCurrency(vipRevenue)}</strong>
                        </div>
                        <div class="segment-stats-row">
                            <span>Avg LTV:</span>
                            <strong>${segments.vip.length > 0 ? formatCurrency(vipRevenue / segments.vip.length) : '$0'}</strong>
                        </div>
                    </div>
                    <div class="segment-actions">
                        <button class="segment-btn view" onclick="showSegmentDetails('VIP Clients', currentSegments.vip)">
                            👁️ View
                        </button>
                        <button class="segment-btn download" onclick="downloadSegmentCSV('VIP_Clients', currentSegments.vip)">
                            📥 Export
                        </button>
                    </div>
                </div>
                
                <!-- Inactive Paid Member Tier -->
                <div class="segment-card inactive-paid">
                    <div class="segment-icon">💳</div>
                    <div class="segment-title">Inactive Paid Members</div>
                    <div class="segment-description">Active membership, no visit in 30+ days</div>
                    <div class="segment-count">${formatNumber(segments.inactivePaidMember.length)}</div>
                    <div class="segment-stats">
                        <div class="segment-stats-row">
                            <span>Monthly Revenue:</span>
                            <strong>${formatCurrency(inactiveMemberRevenue)}</strong>
                        </div>
                        <div class="segment-stats-row">
                            <span>Avg Days Absent:</span>
                            <strong>${segments.inactivePaidMember.length > 0 ? Math.round(segments.inactivePaidMember.reduce((sum, c) => sum + c.daysSinceLastVisit, 0) / segments.inactivePaidMember.length) : 0}</strong>
                        </div>
                    </div>
                    <div class="segment-actions">
                        <button class="segment-btn view" onclick="showSegmentDetails('Inactive Paid Members', currentSegments.inactivePaidMember)">
                            👁️ View
                        </button>
                        <button class="segment-btn download" onclick="downloadSegmentCSV('Inactive_Paid_Members', currentSegments.inactivePaidMember)">
                            📥 Export
                        </button>
                    </div>
                </div>
                
                <!-- At-Risk Tier -->
                <div class="segment-card at-risk">
                    <div class="segment-icon">⚠️</div>
                    <div class="segment-title">At-Risk Clients</div>
                    <div class="segment-description">No visit in 45+ days, needs re-engagement</div>
                    <div class="segment-count">${formatNumber(segments.atRisk.length)}</div>
                    <div class="segment-stats">
                        <div class="segment-stats-row">
                            <span>Revenue at Risk:</span>
                            <strong>${formatCurrency(atRiskRevenue)}</strong>
                        </div>
                        <div class="segment-stats-row">
                            <span>Avg Days Absent:</span>
                            <strong>${segments.atRisk.length > 0 ? Math.round(segments.atRisk.reduce((sum, c) => sum + c.daysSinceLastVisit, 0) / segments.atRisk.length) : 0}</strong>
                        </div>
                    </div>
                    <div class="segment-actions">
                        <button class="segment-btn view" onclick="showSegmentDetails('At-Risk Clients', currentSegments.atRisk)">
                            👁️ View
                        </button>
                        <button class="segment-btn download" onclick="downloadSegmentCSV('At_Risk_Clients', currentSegments.atRisk)">
                            📥 Export
                        </button>
                    </div>
                </div>
                
                <!-- New Client Tier -->
                <div class="segment-card new-client">
                    <div class="segment-icon">🌱</div>
                    <div class="segment-title">New Clients</div>
                    <div class="segment-description">Less than 3 visits, high growth potential</div>
                    <div class="segment-count">${formatNumber(segments.newClient.length)}</div>
                    <div class="segment-stats">
                        <div class="segment-stats-row">
                            <span>Current LTV:</span>
                            <strong>${formatCurrency(segments.newClient.reduce((sum, c) => sum + c.ltv, 0))}</strong>
                        </div>
                        <div class="segment-stats-row">
                            <span>Growth Potential:</span>
                            <strong>${formatCurrency(newClientPotential)}</strong>
                        </div>
                    </div>
                    <div class="segment-actions">
                        <button class="segment-btn view" onclick="showSegmentDetails('New Clients', currentSegments.newClient)">
                            👁️ View
                        </button>
                        <button class="segment-btn download" onclick="downloadSegmentCSV('New_Clients', currentSegments.newClient)">
                            📥 Export
                        </button>
                    </div>
                </div>
                
                <!-- High-Frequency Tier -->
                <div class="segment-card high-frequency">
                    <div class="segment-icon">⚡</div>
                    <div class="segment-title">High-Frequency</div>
                    <div class="segment-description">Weekly visitors, highly engaged clients</div>
                    <div class="segment-count">${formatNumber(segments.highFrequency.length)}</div>
                    <div class="segment-stats">
                        <div class="segment-stats-row">
                            <span>Total Revenue:</span>
                            <strong>${formatCurrency(segments.highFrequency.reduce((sum, c) => sum + c.ltv, 0))}</strong>
                        </div>
                        <div class="segment-stats-row">
                            <span>Total Visits:</span>
                            <strong>${formatNumber(segments.highFrequency.reduce((sum, c) => sum + c.totalVisits, 0))}</strong>
                        </div>
                    </div>
                    <div class="segment-actions">
                        <button class="segment-btn view" onclick="showSegmentDetails('High-Frequency Clients', currentSegments.highFrequency)">
                            👁️ View
                        </button>
                        <button class="segment-btn download" onclick="downloadSegmentCSV('High_Frequency_Clients', currentSegments.highFrequency)">
                            📥 Export
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="segment-summary">
                <h3>📊 Segmentation Summary</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <div class="summary-label">Total Segmented</div>
                        <div class="summary-value">${formatNumber(totalSegmented)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">VIP Revenue</div>
                        <div class="summary-value">${formatCurrency(vipRevenue)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Unused Memberships</div>
                        <div class="summary-value" style="color: #ff9800;">${formatCurrency(inactiveMemberRevenue)}/mo</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">At-Risk Revenue</div>
                        <div class="summary-value" style="color: #dc3545;">${formatCurrency(atRiskRevenue)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Growth Potential</div>
                        <div class="summary-value" style="color: #28a745;">${formatCurrency(newClientPotential)}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// CUSTOMERS TAB
export function renderCustomersTab() {
    if (filteredLeads.length === 0) {
        document.getElementById('customers').innerHTML = `
            <div class="alert info">
                <h4>📊 Customer Analytics</h4>
                <p>Upload the Leads & Customers CSV file to unlock customer lifetime value analysis, conversion tracking, and segmentation insights.</p>
            </div>
        `;
        return;
    }
    
    // Store segments globally for access in button clicks
    window.currentSegments = calculateClientSegments();
    
    // Calculate LTV metrics
    const ltvs = filteredLeads.map(row => parseLTV(row.LTV));
    const totalLTV = ltvs.reduce((sum, ltv) => sum + ltv, 0);
    const avgLTV = totalLTV / ltvs.length;
    const maxLTV = Math.max(...ltvs);
    
    const customers = filteredLeads.filter(row => row.Type === 'Customer').length;
    const leads = filteredLeads.filter(row => row.Type === 'Lead').length;
    const conversionRate = ((customers / (customers + leads)) * 100).toFixed(1);
    
    // Get current LTV tier configuration
    const currentTierConfig = LTV_TIERS[CONFIG.ltvTiers];
    const ranges = currentTierConfig.ranges;
    const vipMin = currentTierConfig.vipMin;
    
    const zeroLTV = ltvs.filter(ltv => ltv === 0).length;
    const tier1 = ltvs.filter(ltv => ltv > 0 && ltv <= ranges[0]).length;
    const tier2 = ltvs.filter(ltv => ltv > ranges[0] && ltv <= ranges[1]).length;
    const tier3 = ltvs.filter(ltv => ltv > ranges[1] && ltv <= ranges[2]).length;
    const tier4 = ltvs.filter(ltv => ltv > ranges[2] && ltv <= ranges[3]).length;
    const tier5 = ltvs.filter(ltv => ltv > ranges[3] && ltv <= ranges[4]).length;
    const tier6 = ltvs.filter(ltv => ltv > ranges[4]).length;
    
    // 🐛 DEBUG: Log detailed LTV information















    // Find Chris Dahl specifically
    const chrisDahl = filteredLeads.find(lead => 
        lead['E-mail'] && lead['E-mail'].toLowerCase().includes('cdahl@aquali.com')
    );

    if (chrisDahl) {
        const chrisLTV = parseLTV(chrisDahl.LTV);








    } else {

    }
    
    // Show top 10 LTV values

    const top10 = [...filteredLeads]
        .map(lead => ({
            name: `${lead['First name']} ${lead['Last name']}`,
            email: lead['E-mail'],
            rawLTV: lead.LTV,
            parsedLTV: parseLTV(lead.LTV)
        }))
        .sort((a, b) => b.parsedLTV - a.parsedLTV)
        .slice(0, 10);
    top10.forEach((lead, i) => {

    });
    
    // Show tier 6 members (VIP)
    const tier6Members = filteredLeads.filter(lead => parseLTV(lead.LTV) > ranges[4]);

    tier6Members.slice(0, 20).forEach(lead => {

    });

    // Top customers
    const sortedByLTV = [...filteredLeads]
        .sort((a, b) => parseLTV(b.LTV) - parseLTV(a.LTV))
        .slice(0, 10);
    
    let html = `
        <div class="alert ${zeroLTV > filteredLeads.length * 0.3 ? 'warning' : 'info'}">
            <h3>💰 Revenue Opportunity</h3>
            <p><strong>${formatNumber(zeroLTV)}</strong> customers have $0 lifetime value (${((zeroLTV/filteredLeads.length)*100).toFixed(1)}% of total).</p>
            <p style="margin-top: 10px;"><strong>Potential Revenue:</strong> ${formatCurrency(zeroLTV * avgLTV)} if converted at average LTV</p>
        </div>
        
        ${renderClientSegmentation()}
        
        <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Total LTV</div>
                <div class="metric-value">${formatCurrency(totalLTV)}</div>
                <div class="metric-subtext">All customers</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Average LTV</div>
                <div class="metric-value">${formatCurrency(avgLTV)}</div>
                <div class="metric-subtext">Per customer</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Conversion Rate</div>
                <div class="metric-value">${conversionRate}%</div>
                <div class="metric-subtext">${customers} customers | ${leads} leads</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">VIP Customers</div>
                <div class="metric-value">${formatNumber(tier6)}</div>
                <div class="metric-subtext">>${formatCurrency(vipMin)} LTV</div>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 30px; border-left: 4px solid #dc3545;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0 0 5px 0; color: #dc3545;">⚠️ ${formatNumber(zeroLTV)} Customers at $0 LTV</h3>
                    <p style="margin: 0; color: #666;">These customers represent untapped revenue potential</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 12px; color: #666;">Percentage of Total</div>
                    <div style="font-size: 32px; font-weight: bold; color: #dc3545;">${((zeroLTV/filteredLeads.length)*100).toFixed(1)}%</div>
                </div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="interactive-badge" title="Click on any bar to see customer list"></div>
                <h3>LTV Distribution (Customers with Revenue)</h3>
                <div class="chart-wrapper">
                    <canvas id="ltvDistributionChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Customer Types</h3>
                <div class="chart-wrapper">
                    <canvas id="customerTypesChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Retention Analysis Section -->
        ${(() => {
            // Analyze client visits for retention metrics
            const data = filteredAppointments;
            const activeMemberEmails = getActiveMemberEmails();
            const clientVisits = {};
            const clientFirstVisit = {};
            const clientLastVisit = {};
            const clientRevenue = {};
            
            data.forEach(row => {
                const email = (row['Customer Email'] || '').toLowerCase().trim();
                if (!email) return;
                
                const date = parseDate(row['Appointment Date']);
                const revenue = parseFloat(row.Revenue || 0);
                const revenueToAdd = activeMemberEmails.has(email) ? 0 : revenue;
                
                if (!clientVisits[email]) {
                    clientVisits[email] = 0;
                    clientFirstVisit[email] = date;
                    clientLastVisit[email] = date;
                    clientRevenue[email] = 0;
                }
                
                clientVisits[email]++;
                clientRevenue[email] += revenueToAdd;
                
                if (date < clientFirstVisit[email]) clientFirstVisit[email] = date;
                if (date > clientLastVisit[email]) clientLastVisit[email] = date;
            });
            
            const uniqueClients = Object.keys(clientVisits).length;
            const returningClients = Object.values(clientVisits).filter(count => count > 1).length;
            const retentionRate = uniqueClients > 0 ? (returningClients / uniqueClients * 100) : 0;
            const avgVisitsPerClient = uniqueClients > 0 ? data.length / uniqueClients : 0;
            
            const visitDist = { '1 visit': 0, '2-3 visits': 0, '4-6 visits': 0, '7-10 visits': 0, '11+ visits': 0 };
            Object.values(clientVisits).forEach(count => {
                if (count === 1) visitDist['1 visit']++;
                else if (count <= 3) visitDist['2-3 visits']++;
                else if (count <= 6) visitDist['4-6 visits']++;
                else if (count <= 10) visitDist['7-10 visits']++;
                else visitDist['11+ visits']++;
            });
            
            let totalDaysBetween = 0;
            let visitPairs = 0;
            Object.keys(clientVisits).forEach(email => {
                if (clientVisits[email] > 1) {
                    const daysBetween = (clientLastVisit[email] - clientFirstVisit[email]) / (1000 * 60 * 60 * 24);
                    const avgDaysForClient = daysBetween / (clientVisits[email] - 1);
                    totalDaysBetween += avgDaysForClient;
                    visitPairs++;
                }
            });
            const avgDaysBetweenVisits = visitPairs > 0 ? totalDaysBetween / visitPairs : 0;
            
            return `
                <div style="margin: 30px 0;">
                    <h2 style="margin-bottom: 20px;">🔄 Retention Analysis</h2>
                    <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 20px;">
                        <div class="metric-card">
                            <div class="metric-label">Total Clients</div>
                            <div class="metric-value">${formatNumber(uniqueClients)}</div>
                            <div class="metric-subtext">Unique individuals</div>
                        </div>
                        <div class="metric-card ${retentionRate >= 50 ? 'success' : retentionRate >= 30 ? 'warning' : 'danger'}">
                            <div class="metric-label">Retention Rate</div>
                            <div class="metric-value">${retentionRate.toFixed(1)}%</div>
                            <div class="metric-subtext">${formatNumber(returningClients)} returning clients</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Avg Visits</div>
                            <div class="metric-value">${avgVisitsPerClient.toFixed(1)}</div>
                            <div class="metric-subtext">Per client</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Avg Days Between</div>
                            <div class="metric-value">${avgDaysBetweenVisits.toFixed(0)}</div>
                            <div class="metric-subtext">Days between visits</div>
                        </div>
                    </div>
                    
                    <div class="alert ${retentionRate >= 50 ? 'success' : 'warning'}">
                        <h4>🔄 Retention Status</h4>
                        <p><strong>Current Status:</strong> ${retentionRate.toFixed(0)}% of clients return for additional appointments.</p>
                        <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                            <li>${visitDist['1 visit']} clients (${((visitDist['1 visit']/uniqueClients)*100).toFixed(0)}%) visited only once</li>
                            <li>Average ${avgDaysBetweenVisits.toFixed(0)} days between visits for returning clients</li>
                            <li>${returningClients} loyal clients generating repeat business</li>
                        </ul>
                        <p style="margin-top: 15px;"><strong>💡 Recommendations:</strong></p>
                        <ul style="margin: 5px 0 0 20px; line-height: 1.8;">
                            <li>Follow up with one-time visitors within ${Math.ceil(avgDaysBetweenVisits/2)} days</li>
                            <li>Create membership packages for ${visitDist['4-6 visits'] + visitDist['7-10 visits'] + visitDist['11+ visits']} frequent visitors</li>
                            <li>Send rebooking reminders every ${Math.floor(avgDaysBetweenVisits * 0.8)} days</li>
                        </ul>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <h3>Visit Frequency Distribution</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                            ${Object.entries(visitDist).map(([range, count]) => `
                                <div style="background: var(--gray-light); padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid var(--accent);">
                                    <div style="font-size: 2.5em; font-weight: bold; color: var(--primary);">${formatNumber(count)}</div>
                                    <div style="color: #666; font-size: 14px; margin-top: 5px;">${range}</div>
                                    <div style="color: var(--accent); font-size: 12px; margin-top: 3px;">${((count/uniqueClients)*100).toFixed(1)}%</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        })()}
        
        <div class="table-container">
            <h2>Top 10 Customers by Lifetime Value</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Type</th>
                        <th>First Purchase</th>
                        <th>LTV</th>
                    </tr>
                </thead>
                <tbody>
                    ${sortedByLTV.map((c, i) => `
                        <tr>
                            <td><strong>${i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}</strong></td>
                            <td>${c['First name']} ${c['Last name']}</td>
                            <td>${c['E-mail']}</td>
                            <td>${c.Type}</td>
                            <td>${c['First purchase'] || 'N/A'}</td>
                            <td><strong>${formatCurrency(parseLTV(c.LTV))}</strong></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('customers').innerHTML = html;
    
    // Render charts
    setTimeout(() => {
        renderLTVDistributionChart(tier1, tier2, tier3, tier4, tier5, tier6);
        renderCustomerTypesChart(customers, leads);
    }, 100);
}

// PRACTITIONERS TAB

export function renderPractitionersTab() {
    const data = filteredAppointments;
    const activeMemberEmails = getActiveMemberEmails();
    
    // Calculate comprehensive metrics for each practitioner (from leaderboard)
    const practitionerStats = {};
    
    data.forEach(row => {
        const name = `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`.trim();
        if (!name) return;
        
        if (!practitionerStats[name]) {
            practitionerStats[name] = {
                revenue: 0,
                appointments: 0,
                clients: new Set(),
                hours: 0,
                payout: 0,
                lateCancel: 0,
                services: new Set()
            };
        }
        
        const email = (row['Customer Email'] || '').toLowerCase().trim();
        const revenue = parseFloat(row.Revenue || 0);
        // Only count revenue if customer is NOT an active member
        const revenueToAdd = activeMemberEmails.has(email) ? 0 : revenue;
        
        practitionerStats[name].revenue += revenueToAdd;
        practitionerStats[name].appointments++;
        practitionerStats[name].clients.add(email);
        practitionerStats[name].hours += parseFloat(row['Time (h)'] || 0);
        practitionerStats[name].payout += parseFloat(row['Total Payout'] || 0);
        if (row['Late cancellations'] && row['Late cancellations'].toLowerCase() === 'yes') {
            practitionerStats[name].lateCancel++;
        }
        practitionerStats[name].services.add(row.Appointment);
    });
    
    // Calculate scores and rankings
    const practitioners = Object.entries(practitionerStats).map(([name, stats]) => {
        const clientCount = stats.clients.size;
        const revenuePerHour = stats.hours > 0 ? stats.revenue / stats.hours : 0;
        const revenuePerAppt = stats.appointments > 0 ? stats.revenue / stats.appointments : 0;
        const lateCancelRate = stats.appointments > 0 ? (stats.lateCancel / stats.appointments) * 100 : 0;
        const profit = stats.revenue - stats.payout;
        const profitMargin = stats.revenue > 0 ? (profit / stats.revenue) * 100 : 0;
        
        // Get utilization data if available from zip file
        const employeeName = name.toLowerCase().replace(/\s+/g, ' ');
        let utilization = null;
        let clockedHours = 0;
        let shiftCount = 0;
        
        if (window.employeeUtilization) {
            for (const [empName, empData] of Object.entries(window.employeeUtilization)) {
                if (empName.toLowerCase().replace(/\s+/g, ' ') === employeeName) {
                    utilization = empData.utilization;
                    clockedHours = empData.totalClockedHours;
                    shiftCount = empData.shiftCount;
                    break;
                }
            }
        }
        
        // Get commission data if available (Membership & Product only)
        let commissions = 0;
        let commissionCount = 0;
        if (window.filteredCommissions && window.filteredCommissions.length > 0) {
            const employeeCommissions = window.filteredCommissions.filter(c => {
                const commEmpName = (c['Employee Name'] || '').toLowerCase().replace(/\s+/g, ' ');
                return commEmpName === employeeName;
            });
            
            commissions = employeeCommissions.reduce((sum, c) => {
                return sum + (parseFloat(c['Commissions earned']) || 0);
            }, 0);
            commissionCount = employeeCommissions.length;
        }
        
        // Calculate overall score (weighted)
        const revenueScore = stats.revenue / 100; // $100 = 1 point
        const efficiencyScore = revenuePerHour * 2; // $1/hr = 2 points
        const clientScore = clientCount * 5; // 1 client = 5 points
        const consistencyScore = stats.appointments * 2; // 1 appt = 2 points
        const qualityScore = (100 - lateCancelRate) * 0.5; // Low cancellations = high score
        const utilizationScore = utilization !== null ? utilization * 0.5 : 0; // 1% utilization = 0.5 points
        const commissionScore = commissions / 10; // $10 commission = 1 point
        
        const totalScore = revenueScore + efficiencyScore + clientScore + consistencyScore + qualityScore + utilizationScore + commissionScore;
        
        return {
            name,
            revenue: stats.revenue,
            appointments: stats.appointments,
            clients: clientCount,
            hours: stats.hours,
            revenuePerHour,
            revenuePerAppt,
            lateCancelRate,
            profit,
            profitMargin,
            services: stats.services.size,
            score: totalScore,
            payout: stats.payout,
            utilization,
            clockedHours,
            shiftCount,
            commissions,
            commissionCount
        };
    });
    
    // Filter out Sauna
    const filteredPractitioners = practitioners.filter(p => !p.name.toLowerCase().includes('sauna'));
    
    // Sort by score for leaderboard
    filteredPractitioners.sort((a, b) => b.score - a.score);
    
    // Create simplified practitionerData for existing charts
    const practitionerData = {};
    filteredPractitioners.forEach(p => {
        practitionerData[p.name] = {
            appointments: p.appointments,
            revenue: p.revenue,
            payout: p.payout,
            hours: p.hours
        };
    });
    
    let html = `
        <div class="alert info">
            <h3>⚕️ VSP Performance & Leaderboard</h3>
            <p>Comprehensive performance metrics and rankings based on revenue, efficiency, client satisfaction, and consistency.</p>
        </div>
        
        <div class="metrics-grid" style="grid-template-columns: repeat(${filteredPractitioners.some(p => p.utilization !== null) ? (filteredPractitioners.some(p => p.commissions > 0) ? '6' : '5') : (filteredPractitioners.some(p => p.commissions > 0) ? '5' : '4')}, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Top Performer</div>
                <div class="metric-value" style="font-size: 1.5em;">${filteredPractitioners[0]?.name || 'N/A'}</div>
                <div class="metric-subtext">${filteredPractitioners[0] ? formatNumber(filteredPractitioners[0].score) + ' points' : ''}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Highest Revenue</div>
                <div class="metric-value">${formatCurrency(Math.max(...filteredPractitioners.map(p => p.revenue)))}</div>
                <div class="metric-subtext">${filteredPractitioners.sort((a,b) => b.revenue - a.revenue)[0]?.name || 'N/A'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Best Efficiency</div>
                <div class="metric-value">${formatCurrency(Math.max(...filteredPractitioners.map(p => p.revenuePerHour)))}/hr</div>
                <div class="metric-subtext">${filteredPractitioners.sort((a,b) => b.revenuePerHour - a.revenuePerHour)[0]?.name || 'N/A'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Most Clients</div>
                <div class="metric-value">${Math.max(...filteredPractitioners.map(p => p.clients))}</div>
                <div class="metric-subtext">${filteredPractitioners.sort((a,b) => b.clients - a.clients)[0]?.name || 'N/A'}</div>
            </div>
            ${filteredPractitioners.some(p => p.utilization !== null) ? `
            <div class="metric-card success">
                <div class="metric-label">Avg Utilization</div>
                <div class="metric-value">${(filteredPractitioners.filter(p => p.utilization !== null).reduce((sum, p) => sum + p.utilization, 0) / filteredPractitioners.filter(p => p.utilization !== null).length).toFixed(1)}%</div>
                <div class="metric-subtext">Table time efficiency</div>
            </div>
            ` : ''}
            ${filteredPractitioners.some(p => p.commissions > 0) ? `
            <div class="metric-card" style="background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(32, 201, 151, 0.05)); border-left: 4px solid #28a745;">
                <div class="metric-label">Total Commissions</div>
                <div class="metric-value">${formatCurrency(filteredPractitioners.reduce((sum, p) => sum + p.commissions, 0))}</div>
                <div class="metric-subtext">Memberships & Products</div>
            </div>
            ` : ''}
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="interactive-badge" title="Click on any VSP to see full details"></div>
                <h3>Revenue by VSP</h3>
                <div class="chart-wrapper">
                    <canvas id="practitionerRevenueChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="interactive-badge" title="Click on any VSP to see full details"></div>
                <h3>Appointments by VSP</h3>
                <div class="chart-wrapper">
                    <canvas id="practitionerApptsChart"></canvas>
                </div>
            </div>
        </div>
    `;
    
    // Re-sort by score for leaderboard display
    filteredPractitioners.sort((a, b) => b.score - a.score);
    
    // Add leaderboard cards
    filteredPractitioners.forEach((p, index) => {
        const rank = index + 1;
        const rankClass = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : 'other';
        const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank;
        
        html += `
            <div class="leaderboard-card">
                <div class="leaderboard-content">
                    <div style="display: flex; align-items: center;">
                        <div class="leaderboard-rank ${rankClass}">${medal}</div>
                        <div class="leaderboard-info">
                            <div class="leaderboard-name">${p.name}</div>
                            <div class="leaderboard-stats">
                                <div class="leaderboard-stat">
                                    <strong>${formatCurrency(p.revenue)}</strong> Revenue
                                </div>
                                <div class="leaderboard-stat">
                                    <strong>${formatNumber(p.appointments)}</strong> Appointments
                                </div>
                                <div class="leaderboard-stat">
                                    <strong>${formatNumber(p.clients)}</strong> Clients
                                </div>
                                <div class="leaderboard-stat">
                                    <strong>${formatCurrency(p.revenuePerHour)}/hr</strong> Efficiency
                                </div>
                                ${p.clockedHours > 0 ? `
                                <div class="leaderboard-stat">
                                    <strong>${formatNumber(p.clockedHours)} hrs</strong> Hours Worked
                                </div>
                                ` : ''}
                                ${p.utilization !== null ? `
                                <div class="leaderboard-stat">
                                    <strong>${p.utilization.toFixed(1)}%</strong> Utilization
                                </div>
                                ` : ''}
                                ${p.commissions > 0 ? `
                                <div class="leaderboard-stat">
                                    <strong>${formatCurrency(p.commissions)}</strong> Commissions
                                </div>
                                ` : ''}
                                <div class="leaderboard-stat">
                                    <strong>${p.profitMargin.toFixed(0)}%</strong> Margin
                                </div>
                                <div class="leaderboard-stat">
                                    <strong>${p.lateCancelRate.toFixed(1)}%</strong> Late Cancel
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="leaderboard-score">
                        <div class="leaderboard-score-label">Score</div>
                        <div class="leaderboard-score-value">${formatNumber(p.score)}</div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
        <div class="table-container">
            <h2>Detailed Performance Metrics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>VSP</th>
                        <th>Score</th>
                        <th>Revenue</th>
                        <th>Appts</th>
                        <th>$/Hour</th>
                        <th>$/Appt</th>
                        <th>Clients</th>
                        ${filteredPractitioners.some(p => p.utilization !== null) ? '<th>Utilization</th>' : ''}
                        ${filteredPractitioners.some(p => p.commissions > 0) ? '<th>Commissions</th>' : ''}
                        <th>Profit %</th>
                    </tr>
                </thead>
                <tbody>
                    ${filteredPractitioners.map((p, i) => `
                        <tr>
                            <td><strong>${i + 1}</strong></td>
                            <td>${p.name}</td>
                            <td><strong>${formatNumber(p.score)}</strong></td>
                            <td>${formatCurrency(p.revenue)}</td>
                            <td>${formatNumber(p.appointments)}</td>
                            <td>${formatCurrency(p.revenuePerHour)}</td>
                            <td>${formatCurrency(p.revenuePerAppt)}</td>
                            <td>${formatNumber(p.clients)}</td>
                            ${p.utilization !== null ? `<td>${p.utilization.toFixed(1)}%</td>` : (filteredPractitioners.some(pr => pr.utilization !== null) ? '<td>-</td>' : '')}
                            ${p.commissions > 0 ? `<td>${formatCurrency(p.commissions)}</td>` : (filteredPractitioners.some(pr => pr.commissions > 0) ? '<td>-</td>' : '')}
                            <td>${p.profitMargin.toFixed(1)}%</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        
        <div class="alert success">
            <h4>🎯 Performance Insights</h4>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                <li><strong>Top Performer:</strong> ${filteredPractitioners[0]?.name} leads with ${formatNumber(filteredPractitioners[0]?.score)} points, excelling in overall performance.</li>
                <li><strong>Revenue Leader:</strong> ${filteredPractitioners.sort((a,b) => b.revenue - a.revenue)[0]?.name} generated ${formatCurrency(filteredPractitioners.sort((a,b) => b.revenue - a.revenue)[0]?.revenue)} in revenue.</li>
                <li><strong>Efficiency Champion:</strong> ${filteredPractitioners.sort((a,b) => b.revenuePerHour - a.revenuePerHour)[0]?.name} achieves ${formatCurrency(filteredPractitioners.sort((a,b) => b.revenuePerHour - a.revenuePerHour)[0]?.revenuePerHour)}/hour.</li>
                <li><strong>Client Favorite:</strong> ${filteredPractitioners.sort((a,b) => b.clients - a.clients)[0]?.name} serves ${filteredPractitioners.sort((a,b) => b.clients - a.clients)[0]?.clients} unique clients.</li>
            </ul>
        </div>
    `;
    
    document.getElementById('practitioners').innerHTML = html;
    
    // Render charts
    setTimeout(() => {
        renderPractitionerCharts(practitionerData);
    }, 100);
}

// TIMELINE TAB

export function renderTimelineTab() {
    const data = filteredAppointments;
    const activeMemberEmails = getActiveMemberEmails();
    
    // Group by date with comprehensive metrics
    const dailyData = {};
    const clientsByDate = {};
    
    data.forEach(row => {
        const date = parseDate(row['Appointment Date']).toLocaleDateString();
        if (!dailyData[date]) {
            dailyData[date] = { 
                revenue: 0, 
                appointments: 0, 
                hours: 0,
                payout: 0,
                profit: 0,
                newClients: new Set(),
                returningClients: new Set(),
                apptHours: 0,  // For utilization calculation
                clockedHours: 0  // For utilization calculation
            };
            clientsByDate[date] = new Set();
        }
        
        const revenue = parseFloat(row.Revenue || 0);
        const payout = parseFloat(row['Total Payout'] || 0);
        const email = (row['Customer Email'] || '').toLowerCase().trim();
        
        // Only count revenue if customer is NOT an active member
        const revenueToAdd = activeMemberEmails.has(email) ? 0 : revenue;
        
        dailyData[date].revenue += revenueToAdd;
        dailyData[date].appointments++;
        dailyData[date].hours += parseFloat(row['Time (h)'] || 0);
        dailyData[date].apptHours += parseFloat(row['Time (h)'] || 0);  // Track appointment hours
        dailyData[date].payout += payout;
        dailyData[date].profit += (revenueToAdd - payout);
        
        // Track new vs returning clients
        if (email) {
            clientsByDate[date].add(email);
            // Check if this client had appointments before this date
            const priorAppointments = data.filter(r => {
                const rDate = parseDate(r['Appointment Date']).toLocaleDateString();
                const rEmail = (r['Customer Email'] || '').toLowerCase().trim();
                return rEmail === email && new Date(rDate) < new Date(date);
            });
            
            if (priorAppointments.length === 0) {
                dailyData[date].newClients.add(email);
            } else {
                dailyData[date].returningClients.add(email);
            }
        }
    });
    
    // Add clocked hours to daily data if time tracking is available
    if (window.timeTrackingData && window.timeTrackingData.length > 0) {
        window.timeTrackingData.forEach(row => {
            const clockedIn = row['Clocked in'] ? new Date(row['Clocked in']) : null;
            if (clockedIn) {
                const date = clockedIn.toLocaleDateString();
                if (dailyData[date]) {
                    dailyData[date].clockedHours += parseFloat(row['Duration (h)'] || 0);
                }
            }
        });
        
        // Calculate utilization for each day
        Object.keys(dailyData).forEach(date => {
            if (dailyData[date].clockedHours > 0) {
                dailyData[date].utilization = (dailyData[date].apptHours / dailyData[date].clockedHours) * 100;
            } else {
                dailyData[date].utilization = null;
            }
        });
    }
    
    const dates = Object.keys(dailyData).sort((a, b) => new Date(a) - new Date(b));
    const avgDailyRevenue = dates.length > 0 
        ? Object.values(dailyData).reduce((sum, d) => sum + d.revenue, 0) / dates.length 
        : 0;
    const avgDailyAppointments = dates.length > 0
        ? Object.values(dailyData).reduce((sum, d) => sum + d.appointments, 0) / dates.length
        : 0;
    const avgDailyProfit = dates.length > 0
        ? Object.values(dailyData).reduce((sum, d) => sum + d.profit, 0) / dates.length
        : 0;
    
    // Calculate average daily utilization
    const daysWithUtilization = Object.values(dailyData).filter(d => d.utilization !== null && d.utilization !== undefined);
    const avgDailyUtilization = daysWithUtilization.length > 0
        ? daysWithUtilization.reduce((sum, d) => sum + d.utilization, 0) / daysWithUtilization.length
        : null;
    
    const bestDay = dates.reduce((best, date) => {
        return dailyData[date].revenue > (dailyData[best]?.revenue || 0) ? date : best;
    }, dates[0]);
    
    const totalRevenue = Object.values(dailyData).reduce((sum, d) => sum + d.revenue, 0);
    
    let html = `
        <div class="metrics-grid" style="grid-template-columns: repeat(${avgDailyUtilization !== null ? '5' : '4'}, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Avg Daily Revenue</div>
                <div class="metric-value">${formatCurrency(avgDailyRevenue)}</div>
                <div class="metric-subtext">Per business day</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Daily Appointments</div>
                <div class="metric-value">${avgDailyAppointments.toFixed(1)}</div>
                <div class="metric-subtext">Per business day</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Daily Profit</div>
                <div class="metric-value">${formatCurrency(avgDailyProfit)}</div>
                <div class="metric-subtext">After payouts</div>
            </div>
            ${avgDailyUtilization !== null ? `
            <div class="metric-card success">
                <div class="metric-label">Avg Daily Utilization</div>
                <div class="metric-value">${avgDailyUtilization.toFixed(1)}%</div>
                <div class="metric-subtext">Table time efficiency</div>
            </div>
            ` : ''}
            <div class="metric-card">
                <div class="metric-label">Best Day</div>
                <div class="metric-value">${formatCurrency(dailyData[bestDay]?.revenue || 0)}</div>
                <div class="metric-subtext">${bestDay}</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container full-width">
                <h3>Daily Revenue Trend</h3>
                <div class="chart-wrapper">
                    <canvas id="dailyRevenueChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h3>Daily Appointments</h3>
                <div class="chart-wrapper">
                    <canvas id="dailyAppointmentsChart"></canvas>
                </div>
            </div>
            
            ${avgDailyUtilization !== null ? `
            <div class="chart-container full-width">
                <h3>Daily Utilization Trend</h3>
                <div class="chart-wrapper">
                    <canvas id="dailyUtilizationChart"></canvas>
                </div>
            </div>
            ` : ''}
            
            <div class="chart-container full-width">
                <h3>Cumulative Revenue Over Time</h3>
                <div class="chart-wrapper">
                    <canvas id="cumulativeRevenueChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h3>Daily Profit Trend</h3>
                <div class="chart-wrapper">
                    <canvas id="dailyProfitChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h3>Daily Revenue per Appointment (Efficiency)</h3>
                <div class="chart-wrapper">
                    <canvas id="dailyRevenuePerApptChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h3>New vs Returning Clients Per Day</h3>
                <div class="chart-wrapper">
                    <canvas id="dailyClientTypeChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h3>Daily Hours Worked</h3>
                <div class="chart-wrapper">
                    <canvas id="dailyHoursChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h3>Weekly Membership Sales Trend</h3>
                <div class="chart-wrapper">
                    <canvas id="membershipWeeklyChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <h3>Weekly Average Membership Sale Value</h3>
                <div class="chart-wrapper">
                    <canvas id="membershipAvgValueChart"></canvas>
                </div>
            </div>
            
            ${filteredLeadsConverted.length > 0 ? `
            <div class="chart-container full-width">
                <div class="interactive-badge" title="Click on any bar to see lead details"></div>
                <h3>Daily Leads by All Locations</h3>
                <div class="chart-wrapper">
                    <canvas id="leadsTimelineAllChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container full-width">
                <div class="interactive-badge" title="Click on any bar to see lead details"></div>
                <h3>Daily Leads by Location (Stacked)</h3>
                <div class="chart-wrapper">
                    <canvas id="leadsTimelineLocationStackedChart"></canvas>
                </div>
            </div>
            ` : ''}
            
            <div class="chart-container full-width">
                <h3>💸 Franchise Fees Timeline (Stacked)</h3>
                <div class="chart-wrapper">
                    <canvas id="feesTimelineChart"></canvas>
                </div>
                <div style="margin-top: 15px; padding: 15px; background: var(--gray-light); border-radius: 8px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Franchise Fee</div>
                            <div style="font-size: 16px; font-weight: bold; color: var(--primary);">${formatCurrency(totalRevenue * CONFIG.franchiseFeePercent / 100)}</div>
                            <div style="font-size: 11px; color: #999;">${CONFIG.franchiseFeePercent}% of revenue</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Brand Fund</div>
                            <div style="font-size: 16px; font-weight: bold; color: var(--accent);">${formatCurrency(totalRevenue * CONFIG.brandFundPercent / 100)}</div>
                            <div style="font-size: 11px; color: #999;">${CONFIG.brandFundPercent}% of revenue</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">CC Processing</div>
                            <div style="font-size: 16px; font-weight: bold; color: var(--highlight);">${formatCurrency(totalRevenue * CONFIG.ccFeesPercent / 100)}</div>
                            <div style="font-size: 11px; color: #999;">${CONFIG.ccFeesPercent}% of revenue</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #666;">Total Fees</div>
                            <div style="font-size: 18px; font-weight: bold; color: var(--danger);">${formatCurrency(totalRevenue * (CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent) / 100)}</div>
                            <div style="font-size: 11px; color: #999;">${((CONFIG.franchiseFeePercent + CONFIG.brandFundPercent + CONFIG.ccFeesPercent)).toFixed(1)}% of revenue</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('timeline').innerHTML = html;
    
    // Render charts
    setTimeout(() => {
        renderTimelineCharts(dailyData, dates);
        renderMembershipTimelineCharts();
        if (leadsConvertedData.length > 0) {
            renderLeadsTimelineCharts();
        }
        
        // Render appointment heatmaps by location
        const locations = [...new Set(data.map(row => row.Location).filter(l => l))].sort();
        locations.forEach(location => {
            const locationAppts = data.filter(row => row.Location === location);
            const containerId = `apptHeatmap-${location.replace(/\s+/g, '-')}`;
            const container = document.getElementById(containerId);
            if (container) {
                renderAppointmentHeatmap(locationAppts, containerId, location);
            }
        });
    }, 100);
}

// INSIGHTS TAB (with monthly goal tracking)

export function renderInsightsTab() {
    const data = filteredAppointments;
    
    // Calculate various insights - exclude active member revenue
    const totalRevenue = calculateAppointmentRevenue(data);
    const totalPayout = data.reduce((sum, row) => sum + parseFloat(row['Total Payout'] || 0), 0);
    const totalHours = data.reduce((sum, row) => sum + parseFloat(row['Time (h)'] || 0), 0);
    
    // Calculate total labor costs including non-appointment work
    let totalLaborCost = totalPayout;
    let nonApptHours = 0;
    let nonApptLaborCost = 0;
    
    if (filteredTimeTracking && filteredTimeTracking.length > 0) {
        // Get the list of practitioners who have appointments in the filtered data
        const practitionersInFiltered = new Set();
        data.forEach(row => {
            const empName = row['Employee Name'];
            if (empName) {
                practitionersInFiltered.add(empName);
            }
        });
        
        // Only count time tracking for practitioners who have appointments in the filtered data
        const relevantTimeTracking = filteredTimeTracking.filter(t => 
            practitionersInFiltered.has(t['Employee Name'])
        );
        
        const totalClockedHours = relevantTimeTracking.reduce((sum, t) => {
            const hours = parseFloat(t['Duration (h)'] || 0);
            return sum + hours;
        }, 0);
        
        // Non-appointment hours = clocked hours - appointment hours
        nonApptHours = Math.max(0, totalClockedHours - totalHours);
        nonApptLaborCost = nonApptHours * CONFIG.baseHourlyRate;
        totalLaborCost = totalPayout + nonApptLaborCost;
    }
    
    // Calculate salary costs for the filtered period
    let salaryCosts = { total: 0, details: [] };
    if (data.length > 0) {
        const dates = data.map(row => parseDate(row['Appointment Date']));
        const minDate = new Date(Math.min(...dates));
        const maxDate = new Date(Math.max(...dates));
        salaryCosts = calculateSalaryCosts(minDate, maxDate);
        totalLaborCost += salaryCosts.total;
    }
    
    const profit = totalRevenue - totalLaborCost;
    const profitMargin = totalRevenue > 0 ? (profit / totalRevenue * 100) : 0;
    
    // Client retention
    const clientVisits = {};
    data.forEach(row => {
        const email = (row['Customer Email'] || '').toLowerCase().trim();
        if (email) {
            clientVisits[email] = (clientVisits[email] || 0) + 1;
        }
    });
    
    const uniqueClients = Object.keys(clientVisits).length;
    const returningClients = Object.values(clientVisits).filter(count => count > 1).length;
    const retentionRate = uniqueClients > 0 ? (returningClients / uniqueClients * 100) : 0;
    
    // Service analysis
    const serviceRevenue = {};
    const serviceCount = {};
    data.forEach(row => {
        const service = row['Appointment'] || 'Unknown';
        serviceRevenue[service] = (serviceRevenue[service] || 0) + parseFloat(row.Revenue || 0);
        serviceCount[service] = (serviceCount[service] || 0) + 1;
    });
    
    const topService = Object.entries(serviceRevenue)
        .sort((a, b) => b[1] - a[1])[0];
    
    // Goals tracking - Monthly basis
    const revenueGoal = CONFIG.goals.monthlyRevenue;
    const appointmentsGoal = CONFIG.goals.monthlyAppointments;
    const revenueProgress = (totalRevenue / revenueGoal) * 100;
    const appointmentsProgress = (data.length / appointmentsGoal) * 100;
    
    const currentPeriod = getCurrentPeriod();
    
    // Calculate intro appointments
    const introAppointments = data.filter(row => isIntroOffer(row['Appointment'])).length;
    const introGoal = CONFIG.goals.monthlyIntroAppointments;
    const introProgress = (introAppointments / introGoal) * 100;
    
    let html = `
        <div class="table-container">
            <h2>Goal Tracking - ${currentPeriod}</h2>
            <p style="margin-bottom: 20px; color: #666;">Monthly goals: ${formatCurrency(revenueGoal)} revenue | ${formatNumber(appointmentsGoal)} appointments | ${formatNumber(introGoal)} intro appointments</p>
            
            <div class="charts-grid" style="grid-template-columns: 1fr 1fr 1fr;">
                <div class="chart-container">
                    <h3>📊 Monthly Revenue vs Goal</h3>
                    <div class="chart-wrapper" style="height: 300px;">
                        <canvas id="monthlyRevenueGoalChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <h3>📊 Monthly Paid Appointments vs Goal</h3>
                    <div class="chart-wrapper" style="height: 300px;">
                        <canvas id="monthlyAppointmentsGoalChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <h3>🆕 Monthly Intro Appointments vs Goal</h3>
                    <div class="chart-wrapper" style="height: 300px;">
                        <canvas id="monthlyIntroGoalChart"></canvas>
                    </div>
                </div>
            </div>
            
            ${revenueProgress < 100 || introProgress < 100 ? `
                <div class="alert ${revenueProgress >= 70 && introProgress >= 70 ? 'warning' : 'danger'}" style="margin-top: 20px;">
                    <h4>📊 Progress Update</h4>
                    ${revenueProgress < 100 ? `<p><strong>Revenue Gap:</strong> ${formatCurrency(revenueGoal - totalRevenue)} remaining to reach goal</p>` : ''}
                    ${appointmentsProgress < 100 ? `<p><strong>Appointments Gap:</strong> ${formatNumber(appointmentsGoal - data.length)} more appointments needed</p>` : ''}
                    ${introProgress < 100 ? `<p><strong>Intro Appointments Gap:</strong> ${formatNumber(introGoal - introAppointments)} more intro appointments needed</p>` : ''}
                    ${revenueProgress < 100 ? `<p style="margin-top: 10px;"><strong>To reach goal:</strong> Need ${formatCurrency((revenueGoal - totalRevenue)/(appointmentsGoal - data.length || 1))} per appointment</p>` : ''}
                </div>
            ` : `
                <div class="alert success" style="margin-top: 20px;">
                    <h4>🎉 Goals Achieved!</h4>
                    <p>Congratulations! You've met your monthly targets. Keep up the excellent work!</p>
                </div>
            `}
        </div>
        
        <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Profit Margin</div>
                <div class="metric-value">${profitMargin.toFixed(1)}%</div>
                <div class="metric-subtext">${formatCurrency(profit)} profit</div>
            </div>
            <div class="metric-card ${retentionRate >= 50 ? 'success' : retentionRate >= 30 ? 'warning' : 'danger'}">
                <div class="metric-label">Client Retention</div>
                <div class="metric-value">${retentionRate.toFixed(1)}%</div>
                <div class="metric-subtext">${returningClients} returning clients</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Top Service</div>
                <div class="metric-value">${formatCurrency(topService ? topService[1] : 0)}</div>
                <div class="metric-subtext">${topService ? topService[0].substring(0, 30) : 'N/A'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Unique Clients</div>
                <div class="metric-value">${formatNumber(uniqueClients)}</div>
                <div class="metric-subtext">${(data.length/uniqueClients).toFixed(1)} avg visits</div>
            </div>
        </div>
        
        <div class="alert ${retentionRate >= 50 ? 'success' : 'warning'}">
            <h4>💡 Key Insights & Recommendations</h4>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                <li><strong>Revenue:</strong> You're at ${revenueProgress.toFixed(0)}% of your monthly goal. ${revenueProgress >= 80 ? 'Great progress! Consider upselling premium services to exceed your target.' : `To reach goal faster, focus on booking ${Math.ceil((CONFIG.monthlyAppointmentGoal - data.length)/7)} more appointments per week.`}</li>
                <li><strong>Retention:</strong> ${retentionRate.toFixed(0)}% of clients return for multiple visits. ${retentionRate >= 50 ? 'Excellent retention! Consider launching a VIP membership program for your most loyal clients.' : 'Create a 3-visit intro package and follow up within 48 hours of first appointments to boost retention.'}</li>
                <li><strong>Profitability:</strong> Your profit margin is ${profitMargin.toFixed(1)}%. ${profitMargin >= 30 ? 'Healthy margins! Consider reinvesting 10-15% into marketing to scale growth.' : 'Review practitioner payout structure and optimize scheduling to reduce idle time and improve margins.'}</li>
                <li><strong>Service Mix:</strong> "${topService ? topService[0] : 'N/A'}" generates the most revenue. Create package deals combining your top service with complementary services to increase average transaction value.</li>
                <li><strong>Client Engagement:</strong> ${uniqueClients > 0 ? `With ${(data.length/uniqueClients).toFixed(1)} average visits per client, there's opportunity to increase visit frequency. Implement a rebooking incentive (e.g., "Book your next session today and save 10%").` : 'Focus on building your client base through referral programs and local partnerships.'}</li>
                <li><strong>Revenue Per Client:</strong> ${uniqueClients > 0 ? `Current average is ${formatCurrency(totalRevenue/uniqueClients)} per client. Aim to increase this by 20% through package deals and membership options.` : 'Track this metric as your client base grows to optimize pricing strategy.'}</li>
            </ul>
        </div>
        
        <div class="table-container">
            <h2>Action Items</h2>
            <div style="background: var(--gray-light); padding: 20px; border-radius: 10px; border-left: 4px solid var(--accent);">
                <h4 style="margin-bottom: 15px; color: var(--primary);">Recommended Actions This Week:</h4>
                <ol style="margin: 0 0 0 20px; line-height: 2;">
                    <li><strong>Follow-up Campaign:</strong> Contact all one-time visitors from the past 30 days with a special "We miss you" discount offer.</li>
                    <li><strong>Package Creation:</strong> Bundle your top 3 services into an attractive package deal priced 15% below individual session rates.</li>
                    <li><strong>Schedule Optimization:</strong> Review your Schedule tab to identify gaps and opportunities to add 2-3 more appointments per week.</li>
                    <li><strong>Client Feedback:</strong> Send a quick survey to your top 10 clients asking what they love and what could be improved.</li>
                    <li><strong>Referral Program:</strong> Launch a "Bring a Friend" promotion where both the referrer and new client get a discount.</li>
                    ${retentionRate < 50 ? '<li><strong>Retention Focus:</strong> Create an automated email sequence that goes out 7, 14, and 30 days after first visit to encourage rebooking.</li>' : ''}
                    ${profitMargin < 30 ? '<li><strong>Cost Analysis:</strong> Review your top expenses and identify 1-2 areas where you can reduce costs without impacting quality.</li>' : ''}
                </ol>
            </div>
        </div>
        
        ${window.attendanceData && window.attendanceData.length > 0 ? `
        <div class="table-container" style="background: linear-gradient(135deg, rgba(113, 190, 210, 0.05), rgba(113, 190, 210, 0.02)); border-left: 5px solid var(--accent);">
            <h2>📋 Attendance Analytics</h2>
            <p style="margin-bottom: 15px; color: #666;">Client booking patterns and upcoming appointments</p>
            
            ${(() => {
                // Filter attendance data by current date filters if applicable
                let attendanceRecords = window.attendanceData;
                
                // Count appointments per client
                const clientAppointments = {};
                const staffAppointments = {};
                let upcomingCount = 0;
                let paidCount = 0;
                let unpaidCount = 0;
                const now = new Date();
                
                attendanceRecords.forEach(row => {
                    const clientEmail = (row['E-mail'] || '').toLowerCase().trim();
                    const clientName = `${row['First Name'] || ''} ${row['Last Name'] || ''}`.trim();
                    const staffName = row['Staff Name'] || 'Unknown';
                    const reservationDate = row['Date of reservation'];
                    const isPaid = (row['Is paid'] || '').toLowerCase();
                    
                    if (clientEmail && clientName) {
                        if (!clientAppointments[clientEmail]) {
                            clientAppointments[clientEmail] = {
                                name: clientName,
                                count: 0,
                                upcoming: 0,
                                paid: 0
                            };
                        }
                        clientAppointments[clientEmail].count++;
                        
                        // Parse reservation date
                        if (reservationDate) {
                            const resDate = new Date(reservationDate);
                            if (resDate > now) {
                                clientAppointments[clientEmail].upcoming++;
                                upcomingCount++;
                            }
                        }
                        
                        if (isPaid === 'yes') {
                            clientAppointments[clientEmail].paid++;
                            paidCount++;
                        } else {
                            unpaidCount++;
                        }
                    }
                    
                    // Count by staff
                    if (staffName) {
                        staffAppointments[staffName] = (staffAppointments[staffName] || 0) + 1;
                    }
                });
                
                // Top 10 most frequent clients
                const topClients = Object.entries(clientAppointments)
                    .sort((a, b) => b[1].count - a[1].count)
                    .slice(0, 10);
                
                // Top VSPs by appointment count
                const topStaff = Object.entries(staffAppointments)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5);
                
                return `
                    <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 20px;">
                        <div class="metric-card">
                            <div class="metric-label">📅 Total Reservations</div>
                            <div class="metric-value">${formatNumber(attendanceRecords.length)}</div>
                            <div class="metric-subtext">From attendance data</div>
                        </div>
                        <div class="metric-card ${upcomingCount > 50 ? 'success' : upcomingCount > 20 ? 'warning' : ''}">
                            <div class="metric-label">🔮 Upcoming Appointments</div>
                            <div class="metric-value">${formatNumber(upcomingCount)}</div>
                            <div class="metric-subtext">Future bookings</div>
                        </div>
                        <div class="metric-card success">
                            <div class="metric-label">✅ Paid</div>
                            <div class="metric-value">${formatNumber(paidCount)}</div>
                            <div class="metric-subtext">${((paidCount/(paidCount + unpaidCount))*100).toFixed(1)}% of total</div>
                        </div>
                        <div class="metric-card warning">
                            <div class="metric-label">⏳ Unpaid</div>
                            <div class="metric-value">${formatNumber(unpaidCount)}</div>
                            <div class="metric-subtext">${((unpaidCount/(paidCount + unpaidCount))*100).toFixed(1)}% of total</div>
                        </div>
                    </div>
                    
                    <div class="charts-grid" style="grid-template-columns: 1fr 1fr;">
                        <div>
                            <h3>👥 Top 10 Most Frequent Clients</h3>
                            <p style="font-size: 12px; color: #666; margin: -5px 0 10px 0;">Clients with most appointments booked</p>
                            <table style="width: 100%;">
                                <thead>
                                    <tr>
                                        <th style="text-align: left;">Client</th>
                                        <th style="text-align: center;">Total</th>
                                        <th style="text-align: center;">Upcoming</th>
                                        <th style="text-align: center;">Paid</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${topClients.map(([email, data], index) => `
                                        <tr>
                                            <td style="font-weight: ${index < 3 ? 'bold' : 'normal'};">
                                                ${index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`} ${data.name}
                                            </td>
                                            <td style="text-align: center; font-weight: bold;">${data.count}</td>
                                            <td style="text-align: center;">${data.upcoming}</td>
                                            <td style="text-align: center;">${data.paid}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        
                        <div>
                            <h3>⭐ Top VSPs by Appointments Booked</h3>
                            <p style="font-size: 12px; color: #666; margin: -5px 0 10px 0;">VSPs with most appointments in attendance data</p>
                            <table style="width: 100%;">
                                <thead>
                                    <tr>
                                        <th style="text-align: left;">VSP</th>
                                        <th style="text-align: center;">Appointments</th>
                                        <th style="text-align: center;">% of Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${topStaff.map(([name, count], index) => `
                                        <tr>
                                            <td style="font-weight: ${index < 3 ? 'bold' : 'normal'};">
                                                ${index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`} ${name}
                                            </td>
                                            <td style="text-align: center; font-weight: bold;">${formatNumber(count)}</td>
                                            <td style="text-align: center;">${((count/attendanceRecords.length)*100).toFixed(1)}%</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    ${upcomingCount > 0 ? `
                    <div class="alert info" style="margin-top: 15px;">
                        <h4>📅 Booking Pipeline</h4>
                        <p>You have <strong>${formatNumber(upcomingCount)}</strong> appointments scheduled. ${upcomingCount > 50 ? 'Strong booking pipeline! ' : upcomingCount > 20 ? 'Moderate booking pipeline. ' : 'Limited upcoming bookings. '}${unpaidCount > 10 ? `Consider sending payment reminders to the <strong>${formatNumber(unpaidCount)}</strong> clients with unpaid reservations.` : ''}</p>
                    </div>
                    ` : ''}
                `;
            })()}
        </div>
        ` : ''}
        
        <div class="table-container">
            <h2>Complete AI Recommendations Report</h2>
            <p style="margin-bottom: 20px; color: #666;">All personalized recommendations ranked by potential impact.</p>
            ${(() => {
                const recommendations = generateSmartRecommendations();
                if (recommendations.length === 0) {
                    return '<div class="alert success"><h4>🎉 Outstanding Performance!</h4><p>Your business is operating at peak efficiency across all metrics. Continue your current strategies!</p></div>';
                }
                return recommendations.map((rec, index) => `
                    <div class="recommendation-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <span class="recommendation-priority ${rec.priority}">#${index + 1} ${rec.priority.toUpperCase()} PRIORITY</span>
                                <div class="recommendation-title">${rec.title}</div>
                                <p style="margin: 10px 0; color: #666; line-height: 1.6;">${rec.description}</p>
                                <p style="margin: 10px 0; padding: 12px; background: rgba(113, 190, 210, 0.1); border-radius: 8px; border-left: 3px solid var(--accent);">
                                    <strong>📋 Action Plan:</strong> ${rec.action}
                                </p>
                                <div class="recommendation-impact">
                                    <strong>💰 Estimated Impact:</strong> ${rec.impact}
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            })()}
        </div>
    `;
    
    document.getElementById('insights').innerHTML = html;
    
    // Render monthly goal charts
    renderMonthlyGoalCharts(data, revenueGoal, appointmentsGoal);
}

// Render monthly goal charts

export function renderMembershipsTab() {
    if (!membershipsData || membershipsData.length === 0) {
        document.getElementById('memberships').innerHTML = `
            <div class="alert info">
                <h4>💳 Membership Analytics</h4>
                <p>Upload the <strong>Membership Sales CSV</strong> file to unlock comprehensive membership analytics including revenue tracking, retention analysis, and sales performance.</p>
            </div>
        `;
        return;
    }
    
    // Parse membership data
    const now = new Date();
    const activeMemberships = [];
    const expiredMemberships = [];
    membershipTypes = {}; // Using global variable
    const dailyRevenue = {};
    const monthlyRevenue = {};
    salesByStaff = {}; // Using global variable
    const frozenCount = filteredMemberships.filter(m => m.Frozen === 'Yes').length;
    const refundedCount = filteredMemberships.filter(m => parseFloat(m.Refunded) > 0).length;
    
    let totalRevenue = 0;
    let avgMembershipValue = 0;
    let newSalesCount = 0;
    let renewalsCount = 0;
    let newSalesRevenue = 0;
    let renewalsRevenue = 0;
    
    // First pass: Group memberships by customer to find first VSP and identify new vs renewal
    const customerFirstVSP = {};
    const customerPurchaseCount = {};
    
    // Sort memberships by date to properly identify first purchase
    const sortedMemberships = [...filteredMemberships].sort((a, b) => {
        const dateA = a['Bought Date/Time (GMT)'] ? new Date(a['Bought Date/Time (GMT)']) : new Date(0);
        const dateB = b['Bought Date/Time (GMT)'] ? new Date(b['Bought Date/Time (GMT)']) : new Date(0);
        return dateA - dateB;
    });
    
    sortedMemberships.forEach(membership => {
        const email = (membership['Customer Email'] || '').toLowerCase().trim();
        if (!email) return;
        
        const boughtDate = membership['Bought Date/Time (GMT)'] ? new Date(membership['Bought Date/Time (GMT)']) : null;
        const soldBy = membership['Sold by'] || '';
        
        // Track customer purchase count
        if (!customerPurchaseCount[email]) {
            customerPurchaseCount[email] = 0;
        }
        customerPurchaseCount[email]++;
        
        // Track first VSP
        if (!customerFirstVSP[email]) {
            customerFirstVSP[email] = {
                vsp: soldBy,
                date: boughtDate,
                purchaseId: membership['Purchase ID']
            };
        }
    });
    
    // Second pass: Process all memberships
    filteredMemberships.forEach(membership => {
        const paidAmount = parseFloat(membership['Paid Amount']) || 0;
        totalRevenue += paidAmount;
        
        // Determine if new sale or renewal
        const email = (membership['Customer Email'] || '').toLowerCase().trim();
        const purchaseId = membership['Purchase ID'];
        const isFirstPurchase = email && customerFirstVSP[email] && customerFirstVSP[email].purchaseId === purchaseId;
        
        if (isFirstPurchase) {
            newSalesCount++;
            newSalesRevenue += paidAmount;
            membership._isNewSale = true;
        } else if (email && customerFirstVSP[email]) {
            renewalsCount++;
            renewalsRevenue += paidAmount;
            membership._isRenewal = true;
        }
        
        // Parse dates
        const boughtDate = membership['Bought Date/Time (GMT)'] ? new Date(membership['Bought Date/Time (GMT)']) : null;
        const expiryDate = membership['Remaining/ Expiry/ Renewal'] ? new Date(membership['Remaining/ Expiry/ Renewal']) : null;
        const isExpired = membership.Expired === 'Yes';
        
        // Categorize active vs expired
        if (isExpired || (expiryDate && expiryDate < now)) {
            expiredMemberships.push(membership);
        } else {
            activeMemberships.push(membership);
        }
        
        // Track membership types
        const type = membership['Membership Name'] || 'Unknown';
        if (!membershipTypes[type]) {
            membershipTypes[type] = { count: 0, revenue: 0, active: 0, newSales: 0, renewals: 0 };
        }
        membershipTypes[type].count++;
        membershipTypes[type].revenue += paidAmount;
        if (!isExpired && (!expiryDate || expiryDate >= now)) {
            membershipTypes[type].active++;
        }
        if (membership._isNewSale) {
            membershipTypes[type].newSales++;
        } else if (membership._isRenewal) {
            membershipTypes[type].renewals++;
        }
        
        // Track daily revenue
        if (boughtDate) {
            const dateKey = boughtDate.toISOString().split('T')[0];
            if (!dailyRevenue[dateKey]) {
                dailyRevenue[dateKey] = 0;
            }
            dailyRevenue[dateKey] += paidAmount;
            
            // Track monthly revenue
            const monthKey = `${boughtDate.getFullYear()}-${String(boughtDate.getMonth() + 1).padStart(2, '0')}`;
            if (!monthlyRevenue[monthKey]) {
                monthlyRevenue[monthKey] = 0;
            }
            monthlyRevenue[monthKey] += paidAmount;
        }
        
        // Track sales by staff - credit to FIRST VSP for this customer
        let soldBy = membership['Sold by'] || '';
        
        // If customer has a first VSP recorded and this sale has no VSP, credit the first VSP
        if (email && customerFirstVSP[email]) {
            soldBy = customerFirstVSP[email].vsp || soldBy;
        }
        
        // If still empty, mark as Direct/Online
        if (!soldBy) {
            soldBy = 'Direct/Online';
        }
        
        if (!salesByStaff[soldBy]) {
            salesByStaff[soldBy] = { count: 0, revenue: 0, newSales: 0, renewals: 0 };
        }
        salesByStaff[soldBy].count++;
        salesByStaff[soldBy].revenue += paidAmount;
        if (membership._isNewSale) {
            salesByStaff[soldBy].newSales++;
        } else if (membership._isRenewal) {
            salesByStaff[soldBy].renewals++;
        }
    });
    
    avgMembershipValue = totalRevenue / membershipsData.length;
    
    // Calculate MRR (Monthly Recurring Revenue) from active subscriptions
    let mrr = 0;
    activeMemberships.forEach(m => {
        if (m['Membership Type'] === 'subscription') {
            const amount = parseFloat(m['Paid Amount']) || 0;
            mrr += amount;
        }
    });
    
    // Sort data for charts
    const sortedDates = Object.keys(dailyRevenue).sort();
    const sortedMonths = Object.keys(monthlyRevenue).sort();
    
    // Calculate cumulative revenue
    const cumulativeRevenue = [];
    let cumSum = 0;
    sortedDates.forEach(date => {
        cumSum += dailyRevenue[date];
        cumulativeRevenue.push({ date, value: cumSum });
    });
    
    // Calculate retention rate
    const totalMemberships = membershipsData.length;
    const retentionRate = ((activeMemberships.length / totalMemberships) * 100).toFixed(1);
    const churnRate = ((expiredMemberships.length / totalMemberships) * 100).toFixed(1);
    
    // Sort membership types by revenue
    const sortedTypes = Object.entries(membershipTypes)
        .sort((a, b) => b[1].revenue - a[1].revenue)
        .slice(0, 10);
    
    // Sort sales staff by count
    const sortedStaff = Object.entries(salesByStaff)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 10);
    
    // Calculate cancellations (expired memberships that were previously active)
    const canceledCount = expiredMemberships.length;
    const canceledRevenueLost = expiredMemberships.reduce((sum, m) => sum + (parseFloat(m['Paid Amount']) || 0), 0);
    
    // Advanced client segmentation
    const highValueClients = filteredMemberships.filter(m => parseFloat(m['Paid Amount']) >= 300).length;
    const subscriptionClients = filteredMemberships.filter(m => m['Membership Type'] === 'subscription').length;
    const packageClients = filteredMemberships.filter(m => m['Membership Type'] === 'package-events').length;
    const avgRevPerMember = totalRevenue / new Set(filteredMemberships.map(m => (m['Customer Email'] || '').toLowerCase())).size;
    const uniqueCustomers = new Set(filteredMemberships.map(m => (m['Customer Email'] || '').toLowerCase())).size;
    
    let html = `
        <div class="section">
            <h2>Membership Analytics Overview</h2>
            
            <!-- Compact Metrics Grid -->
            <div class="metrics-grid" style="grid-template-columns: repeat(6, 1fr); margin-bottom: 40px;">

                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(32, 201, 151, 0.05)); border-left: 4px solid #28a745;">
                    <div class="metric-label">💳 Active Members</div>
                    <div class="metric-value">${formatNumber(membershipsData.filter(m => m.Expired !== 'Yes').length)}</div>
                    <div class="metric-subtext">${formatCurrency(newSalesRevenue)} revenue<br>Avg: ${formatCurrency(newSalesRevenue/newSalesCount)}</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(0, 123, 255, 0.1), rgba(0, 86, 179, 0.05)); border-left: 4px solid #007bff;">
                    <div class="metric-label">🔄 Total Renewals</div>
                    <div class="metric-value">${formatNumber(renewalsCount)}</div>
                    <div class="metric-subtext">${formatCurrency(renewalsRevenue)} revenue<br>Avg: ${formatCurrency(renewalsRevenue/renewalsCount)}</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(123, 31, 162, 0.05)); border-left: 4px solid #9c27b0;">
                    <div class="metric-label">💰 Total Revenue</div>
                    <div class="metric-value" style="font-size: 1.4em;">${formatCurrency(totalRevenue)}</div>
                    <div class="metric-subtext">${formatNumber(totalMemberships)} total memberships<br>Avg: ${formatCurrency(avgMembershipValue)}</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(255, 99, 132, 0.1), rgba(255, 56, 96, 0.05)); border-left: 4px solid #ff6384;">
                    <div class="metric-label">📊 Renewal Rate</div>
                    <div class="metric-value">${((renewalsCount / totalMemberships) * 100).toFixed(1)}%</div>
                    <div class="metric-subtext">${formatNumber(activeMemberships.length)} active<br>${retentionRate}% retention</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), rgba(245, 124, 0, 0.05)); border-left: 4px solid #ff9800;">
                    <div class="metric-label">❌ Cancellations</div>
                    <div class="metric-value">${formatNumber(canceledCount)}</div>
                    <div class="metric-subtext">${churnRate}% churn rate<br>${formatCurrency(canceledRevenueLost)} revenue lost</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(33, 150, 243, 0.1), rgba(13, 71, 161, 0.05)); border-left: 4px solid #2196f3;">
                    <div class="metric-label">❄️ Frozen</div>
                    <div class="metric-value">${formatNumber(frozenCount)}</div>
                    <div class="metric-subtext">${((frozenCount / totalMemberships) * 100).toFixed(1)}% of total<br>memberships frozen</div>
                </div>
            </div>
            
            <!-- Advanced Client Segmentation -->
            <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 20px;">
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(56, 142, 60, 0.05)); border-left: 4px solid #4caf50;">
                    <div class="metric-label">💎 High-Value Clients</div>
                    <div class="metric-value">${formatNumber(highValueClients)}</div>
                    <div class="metric-subtext">${((highValueClients / totalMemberships) * 100).toFixed(1)}% of memberships<br>$300+ purchases</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(103, 58, 183, 0.1), rgba(81, 45, 168, 0.05)); border-left: 4px solid #673ab7;">
                    <div class="metric-label">🔁 Subscription Members</div>
                    <div class="metric-value">${formatNumber(subscriptionClients)}</div>
                    <div class="metric-subtext">${((subscriptionClients / totalMemberships) * 100).toFixed(1)}% recurring<br>MRR: ${formatCurrency(mrr)}</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(0, 151, 167, 0.05)); border-left: 4px solid #00bcd4;">
                    <div class="metric-label">📦 Package Clients</div>
                    <div class="metric-value">${formatNumber(packageClients)}</div>
                    <div class="metric-subtext">${((packageClients / totalMemberships) * 100).toFixed(1)}% packages<br>One-time purchases</div>
                </div>
                
                <div class="metric-card compact" style="background: linear-gradient(135deg, rgba(255, 87, 34, 0.1), rgba(230, 74, 25, 0.05)); border-left: 4px solid #ff5722;">
                    <div class="metric-label">👤 Unique Customers</div>
                    <div class="metric-value">${formatNumber(uniqueCustomers)}</div>
                    <div class="metric-subtext">Avg Revenue: ${formatCurrency(avgRevPerMember)}<br>${(totalMemberships / uniqueCustomers).toFixed(1)} purchases/customer</div>
                </div>
            </div>
        </div>
        
        <!-- Membership Type Breakdown -->
        <div class="section">
            <h2>Membership Type Analysis</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <h3>Memberships by Type</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipTypeCountChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Revenue by Membership Type</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipTypeRevenueChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Membership Type Table -->
            <div class="table-container">
                <h3>Membership Type Details</h3>
                <button onclick="exportMembershipTypeData()" style="float: right; padding: 8px 16px; background: var(--accent); color: white; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 10px;">📥 Export to CSV</button>
                <table>
                    <thead>
                        <tr>
                            <th>Membership Type</th>
                            <th>Total</th>
                            <th>New Sales</th>
                            <th>Renewals</th>
                            <th>Active</th>
                            <th>Expired</th>
                            <th>Revenue</th>
                            <th>Avg Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sortedTypes.map(([type, data]) => `
                            <tr>
                                <td><strong>${type}</strong></td>
                                <td>${formatNumber(data.count)}</td>
                                <td style="color: #28a745;">${formatNumber(data.newSales || 0)}</td>
                                <td style="color: #007bff;">${formatNumber(data.renewals || 0)}</td>
                                <td style="color: var(--success);">${formatNumber(data.active)}</td>
                                <td style="color: var(--danger);">${formatNumber(data.count - data.active)}</td>
                                <td><strong>${formatCurrency(data.revenue)}</strong></td>
                                <td>${formatCurrency(data.revenue / data.count)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Sales Performance -->
        <div class="section">
            <h2>Sales Performance by VSP</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <h3>Memberships Sold/Renewed by VSP</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipStaffCountChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Revenue by VSP</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipStaffRevenueChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Staff Performance Table -->
            <div class="table-container">
                <h3>VSP Sales Details</h3>
                <button onclick="exportStaffSalesData()" style="float: right; padding: 8px 16px; background: var(--accent); color: white; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 10px;">📥 Export to CSV</button>
                <table>
                    <thead>
                        <tr>
                            <th>VSP</th>
                            <th>Total Sales</th>
                            <th>New Sales</th>
                            <th>Renewals</th>
                            <th>Revenue Generated</th>
                            <th>Avg Sale Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sortedStaff.map(([staff, data]) => `
                            <tr>
                                <td><strong>${formatStaffName(staff)}</strong></td>
                                <td>${formatNumber(data.count)}</td>
                                <td style="color: #28a745;">${formatNumber(data.newSales || 0)}</td>
                                <td style="color: #007bff;">${formatNumber(data.renewals || 0)}</td>
                                <td><strong>${formatCurrency(data.revenue)}</strong></td>
                                <td>${formatCurrency(data.revenue / data.count)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Active vs Expired -->
        <div class="section">
            <h2>Membership Status Analysis</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <h3>Active vs Expired Memberships</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipStatusChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>MRR Growth Over Time</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipMRRChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Timeline Analysis -->
        <div class="section">
            <h2>Timeline &amp; Trends</h2>
            <div class="chart-grid">
                <div class="chart-container full-width">
                    <h3>Daily New Memberships: New Sales vs Renewals</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipTimelineChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Sales by Day of Week</h3>
                    <div class="chart-wrapper">
                        <canvas id="membershipDayOfWeekChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('memberships').innerHTML = html;
    
    // Render charts
    setTimeout(() => {



        // Sales Mix Chart - REMOVED
        // Revenue Mix Chart - REMOVED
        // Cumulative Revenue Chart - REMOVED
        // Monthly Revenue Chart - REMOVED
        
        // Membership type count chart
        const typeCountCanvas = document.getElementById('membershipTypeCountChart');
        if (typeCountCanvas) {

            destroyChart('membershipTypeCount');
            const ctx = typeCountCanvas.getContext('2d');
            allCharts.membershipTypeCount = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: sortedTypes.map(([type]) => type),
                    datasets: [{
                        data: sortedTypes.map(([, data]) => data.count),
                        backgroundColor: [
                            '#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d',
                            '#17a2b8', '#fd7e14', '#6610f2', '#e83e8c', '#20c997'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const [typeName, typeData] = sortedTypes[index];
                            const typeMembers = filteredMemberships.filter(m => m['Membership Name'] === typeName);
                            
                            let modalContent = `
                                <h4>${typeName}</h4>
                                <p><strong>Total:</strong> ${typeData.count} memberships | <strong>Revenue:</strong> ${formatCurrency(typeData.revenue)}</p>
                                <p><strong>Active:</strong> ${typeData.active} | <strong>Expired:</strong> ${typeData.count - typeData.active}</p>
                                <p><strong>Average Value:</strong> ${formatCurrency(typeData.revenue / typeData.count)}</p>
                                <hr>
                                <h5>Recent Members:</h5>
                                <table style="width: 100%; font-size: 0.9em;">
                                    <thead>
                                        <tr>
                                            <th>Customer</th>
                                            <th>Purchased</th>
                                            <th>Amount</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${typeMembers.slice(0, 10).map(m => `
                                            <tr>
                                                <td>${m['First Name']} ${m['Last Name']}</td>
                                                <td>${new Date(m['Bought Date/Time (GMT)']).toLocaleDateString()}</td>
                                                <td>${formatCurrency(parseFloat(m['Paid Amount']))}</td>
                                                <td style="color: ${m.Expired === 'Yes' ? '#dc3545' : '#28a745'}">${m.Expired === 'Yes' ? 'Expired' : 'Active'}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            `;
                            
                            // Prepare export data
                            const exportData = typeMembers.map(m => ({
                                'Customer Name': `${m['First Name']} ${m['Last Name']}`,
                                'Email': m['Customer Email'],
                                'Membership Type': m['Membership Name'],
                                'Purchase Date': new Date(m['Bought Date/Time (GMT)']).toLocaleDateString(),
                                'Amount Paid': parseFloat(m['Paid Amount']).toFixed(2),
                                'Status': m.Expired === 'Yes' ? 'Expired' : 'Active',
                                'Type': m._isNewSale ? 'New Sale' : (m._isRenewal ? 'Renewal' : 'Unknown')
                            }));
                            
                            showModal(`Membership Type: ${typeName}`, modalContent, exportData);
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });

        } else {
            console.error('membershipTypeCountChart canvas not found!');
        }
        
        // Membership type revenue chart (DOUGHNUT with drilldown)
        const typeRevenueCanvas = document.getElementById('membershipTypeRevenueChart');
        if (typeRevenueCanvas) {

            destroyChart('membershipTypeRevenue');
            const ctx = typeRevenueCanvas.getContext('2d');
            allCharts.membershipTypeRevenue = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: sortedTypes.map(([type]) => type),
                    datasets: [{
                        data: sortedTypes.map(([, data]) => data.revenue),
                        backgroundColor: [
                            '#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d',
                            '#17a2b8', '#fd7e14', '#6610f2', '#e83e8c', '#20c997'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const [typeName, typeData] = sortedTypes[index];
                            const typeMembers = filteredMemberships.filter(m => m['Membership Name'] === typeName);
                            
                            let modalContent = `
                                <h4>${typeName}</h4>
                                <p><strong>Total:</strong> ${typeData.count} memberships | <strong>Revenue:</strong> ${formatCurrency(typeData.revenue)}</p>
                                <p><strong>Active:</strong> ${typeData.active} | <strong>Expired:</strong> ${typeData.count - typeData.active}</p>
                                <p><strong>Average Value:</strong> ${formatCurrency(typeData.revenue / typeData.count)}</p>
                                <hr>
                                <h5>Recent Members:</h5>
                                <table style="width: 100%; font-size: 0.9em;">
                                    <thead>
                                        <tr>
                                            <th>Customer</th>
                                            <th>Purchased</th>
                                            <th>Amount</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${typeMembers.slice(0, 10).map(m => `
                                            <tr>
                                                <td>${m['First Name']} ${m['Last Name']}</td>
                                                <td>${new Date(m['Bought Date/Time (GMT)']).toLocaleDateString()}</td>
                                                <td>${formatCurrency(parseFloat(m['Paid Amount']))}</td>
                                                <td style="color: ${m.Expired === 'Yes' ? '#dc3545' : '#28a745'}">${m.Expired === 'Yes' ? 'Expired' : 'Active'}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            `;
                            
                            // Prepare export data
                            const exportData = typeMembers.map(m => ({
                                'Customer Name': `${m['First Name']} ${m['Last Name']}`,
                                'Email': m['Customer Email'],
                                'Membership Type': m['Membership Name'],
                                'Purchase Date': new Date(m['Bought Date/Time (GMT)']).toLocaleDateString(),
                                'Amount Paid': parseFloat(m['Paid Amount']).toFixed(2),
                                'Status': m.Expired === 'Yes' ? 'Expired' : 'Active',
                                'Type': m._isNewSale ? 'New Sale' : (m._isRenewal ? 'Renewal' : 'Unknown')
                            }));
                            
                            showModal(`Membership Type Revenue: ${typeName}`, modalContent, exportData);
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': ' + formatCurrency(context.parsed);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Staff count chart
        const staffCountCanvas = document.getElementById('membershipStaffCountChart');
        if (staffCountCanvas) {
            destroyChart('membershipStaffCount');
            const ctx = staffCountCanvas.getContext('2d');
            allCharts.membershipStaffCount = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sortedStaff.map(([staff]) => formatStaffName(staff)),
                    datasets: [{
                        label: 'Memberships Sold',
                        data: sortedStaff.map(([, data]) => data.count),
                        backgroundColor: '#9c27b0',
                        borderColor: '#7b1fa2',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const [staffName, staffData] = sortedStaff[index];
                            const staffMembers = filteredMemberships.filter(m => {
                                const email = (m['Customer Email'] || '').toLowerCase().trim();
                                if (email && customerFirstVSP[email]) {
                                    return customerFirstVSP[email].vsp === staffName;
                                }
                                return (m['Sold by'] || 'Direct/Online') === staffName;
                            });
                            
                            let modalContent = `
                                <h4>Sales Performance: ${formatStaffName(staffName)}</h4>
                                <p><strong>Memberships Sold:</strong> ${staffData.count}</p>
                                <p><strong>New Sales:</strong> ${staffData.newSales || 0} | <strong>Renewals:</strong> ${staffData.renewals || 0}</p>
                                <p><strong>Revenue Generated:</strong> ${formatCurrency(staffData.revenue)}</p>
                                <p><strong>Average Sale:</strong> ${formatCurrency(staffData.revenue / staffData.count)}</p>
                                <hr>
                                <h5>Recent Sales:</h5>
                                <table style="width: 100%; font-size: 0.9em;">
                                    <thead>
                                        <tr>
                                            <th>Customer</th>
                                            <th>Membership</th>
                                            <th>Date</th>
                                            <th>Amount</th>
                                            <th>Type</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${staffMembers.slice(0, 15).map(m => `
                                            <tr>
                                                <td>${m['First Name']} ${m['Last Name']}</td>
                                                <td>${m['Membership Name']}</td>
                                                <td>${new Date(m['Bought Date/Time (GMT)']).toLocaleDateString()}</td>
                                                <td>${formatCurrency(parseFloat(m['Paid Amount']))}</td>
                                                <td><span style="padding: 4px 8px; border-radius: 4px; background: ${m._isNewSale ? '#d4edda' : '#cfe2ff'}; color: ${m._isNewSale ? '#155724' : '#084298'};">${m._isNewSale ? 'New Sale' : (m._isRenewal ? 'Renewal' : 'Unknown')}</span></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            `;
                            
                            // Prepare export data
                            const exportData = staffMembers.map(m => ({
                                'Staff Member': staffName,
                                'Customer Name': `${m['First Name']} ${m['Last Name']}`,
                                'Email': m['Customer Email'],
                                'Membership Type': m['Membership Name'],
                                'Purchase Date': new Date(m['Bought Date/Time (GMT)']).toLocaleDateString(),
                                'Amount Paid': parseFloat(m['Paid Amount']).toFixed(2),
                                'Sale Type': m._isNewSale ? 'New Sale' : (m._isRenewal ? 'Renewal' : 'Unknown')
                            }));
                            
                            showModal(`Staff Member: ${staffName}`, modalContent, exportData);
                        }
                    },
                    plugins: { legend: { display: false } },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }
        
        // Staff revenue chart
        const staffRevenueCanvas = document.getElementById('membershipStaffRevenueChart');
        if (staffRevenueCanvas) {
            destroyChart('membershipStaffRevenue');
            const ctx = staffRevenueCanvas.getContext('2d');
            allCharts.membershipStaffRevenue = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sortedStaff.map(([staff]) => formatStaffName(staff)),
                    datasets: [{
                        label: 'Revenue',
                        data: sortedStaff.map(([, data]) => data.revenue),
                        backgroundColor: '#ff6384',
                        borderColor: '#ff3860',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const [staffName, staffData] = sortedStaff[index];
                            const staffMembers = filteredMemberships.filter(m => {
                                const email = (m['Customer Email'] || '').toLowerCase().trim();
                                if (email && customerFirstVSP[email]) {
                                    return customerFirstVSP[email].vsp === staffName;
                                }
                                return (m['Sold by'] || 'Direct/Online') === staffName;
                            });
                            
                            let modalContent = `
                                <h4>Revenue Performance: ${formatStaffName(staffName)}</h4>
                                <p><strong>Total Revenue:</strong> ${formatCurrency(staffData.revenue)}</p>
                                <p><strong>Memberships Sold:</strong> ${staffData.count}</p>
                                <p><strong>New Sales:</strong> ${staffData.newSales || 0} | <strong>Renewals:</strong> ${staffData.renewals || 0}</p>
                                <p><strong>Average Sale:</strong> ${formatCurrency(staffData.revenue / staffData.count)}</p>
                                <hr>
                                <h5>Top Sales:</h5>
                                <table style="width: 100%; font-size: 0.9em;">
                                    <thead>
                                        <tr>
                                            <th>Customer</th>
                                            <th>Membership</th>
                                            <th>Date</th>
                                            <th>Amount</th>
                                            <th>Type</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${staffMembers.sort((a, b) => parseFloat(b['Paid Amount']) - parseFloat(a['Paid Amount'])).slice(0, 15).map(m => `
                                            <tr>
                                                <td>${m['First Name']} ${m['Last Name']}</td>
                                                <td>${m['Membership Name']}</td>
                                                <td>${new Date(m['Bought Date/Time (GMT)']).toLocaleDateString()}</td>
                                                <td><strong>${formatCurrency(parseFloat(m['Paid Amount']))}</strong></td>
                                                <td><span style="padding: 4px 8px; border-radius: 4px; background: ${m._isNewSale ? '#d4edda' : '#cfe2ff'}; color: ${m._isNewSale ? '#155724' : '#084298'};">${m._isNewSale ? 'New Sale' : (m._isRenewal ? 'Renewal' : 'Unknown')}</span></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            `;
                            
                            // Prepare export data (sorted by amount)
                            const sortedStaffMembers = staffMembers.sort((a, b) => parseFloat(b['Paid Amount']) - parseFloat(a['Paid Amount']));
                            const exportData = sortedStaffMembers.map(m => ({
                                'Staff Member': staffName,
                                'Customer Name': `${m['First Name']} ${m['Last Name']}`,
                                'Email': m['Customer Email'],
                                'Membership Type': m['Membership Name'],
                                'Purchase Date': new Date(m['Bought Date/Time (GMT)']).toLocaleDateString(),
                                'Amount Paid': parseFloat(m['Paid Amount']).toFixed(2),
                                'Sale Type': m._isNewSale ? 'New Sale' : (m._isRenewal ? 'Renewal' : 'Unknown')
                            }));
                            
                            showModal(`Staff Member: ${staffName}`, modalContent, exportData);
                        }
                    },
                    plugins: { legend: { display: false } },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Status chart
        const statusCanvas = document.getElementById('membershipStatusChart');
        if (statusCanvas) {
            destroyChart('membershipStatus');
            const ctx = statusCanvas.getContext('2d');
            allCharts.membershipStatus = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Active', 'Expired'],
                    datasets: [{
                        data: [activeMemberships.length, expiredMemberships.length],
                        backgroundColor: ['#28a745', '#dc3545']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const isActive = index === 0;
                            const statusMembers = isActive ? activeMemberships : expiredMemberships;
                            const status = isActive ? 'Active' : 'Expired';
                            
                            let modalContent = `
                                <h4>${status} Memberships</h4>
                                <p><strong>Count:</strong> ${statusMembers.length}</p>
                                <p><strong>Total Revenue:</strong> ${formatCurrency(statusMembers.reduce((sum, m) => sum + parseFloat(m['Paid Amount'] || 0), 0))}</p>
                                <hr>
                                <h5>Recent ${status} Memberships:</h5>
                                <table style="width: 100%; font-size: 0.9em;">
                                    <thead>
                                        <tr>
                                            <th>Customer</th>
                                            <th>Type</th>
                                            <th>Purchased</th>
                                            <th>Amount</th>
                                            ${!isActive ? '<th>Expired</th>' : ''}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${statusMembers.slice(0, 15).map(m => `
                                            <tr>
                                                <td>${m['First Name']} ${m['Last Name']}</td>
                                                <td>${m['Membership Name']}</td>
                                                <td>${new Date(m['Bought Date/Time (GMT)']).toLocaleDateString()}</td>
                                                <td>${formatCurrency(parseFloat(m['Paid Amount']))}</td>
                                                ${!isActive ? `<td>${m['Remaining/ Expiry/ Renewal'] ? new Date(m['Remaining/ Expiry/ Renewal']).toLocaleDateString() : 'N/A'}</td>` : ''}
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            `;
                            
                            // Prepare export data
                            const exportData = statusMembers.map(m => ({
                                'Status': status,
                                'Customer Name': `${m['First Name']} ${m['Last Name']}`,
                                'Email': m['Customer Email'],
                                'Membership Type': m['Membership Name'],
                                'Purchase Date': new Date(m['Bought Date/Time (GMT)']).toLocaleDateString(),
                                'Amount Paid': parseFloat(m['Paid Amount']).toFixed(2),
                                'Expiry Date': m['Remaining/ Expiry/ Renewal'] ? new Date(m['Remaining/ Expiry/ Renewal']).toLocaleDateString() : 'N/A',
                                'Sale Type': m._isNewSale ? 'New Sale' : (m._isRenewal ? 'Renewal' : 'Unknown'),
                                'Frozen': m.Frozen || 'No',
                                'Refunded': parseFloat(m.Refunded) > 0 ? 'Yes' : 'No'
                            }));
                            
                            showModal(`${status} Memberships`, modalContent, exportData);
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        // MRR Growth Chart
        const mrrCanvas = document.getElementById('membershipMRRChart');
        if (mrrCanvas) {
            destroyChart('membershipMRR');
            const ctx = mrrCanvas.getContext('2d');
            
            // Calculate MRR by month
            const monthlyMRR = {};
            sortedMonths.forEach(month => {
                const monthStart = new Date(month + '-01');
                const monthEnd = new Date(monthStart.getFullYear(), monthStart.getMonth() + 1, 0);
                
                let mrrValue = 0;
                membershipsData.forEach(m => {
                    if (m['Membership Type'] === 'subscription') {
                        const boughtDate = m['Bought Date/Time (GMT)'] ? new Date(m['Bought Date/Time (GMT)']) : null;
                        const expiryDate = m['Remaining/ Expiry/ Renewal'] ? new Date(m['Remaining/ Expiry/ Renewal']) : null;
                        const isExpired = m.Expired === 'Yes';
                        
                        // If subscription was active during this month
                        if (boughtDate && boughtDate <= monthEnd && (!isExpired || (expiryDate && expiryDate >= monthStart))) {
                            mrrValue += parseFloat(m['Paid Amount']) || 0;
                        }
                    }
                });
                monthlyMRR[month] = mrrValue;
            });
            
            allCharts.membershipMRR = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: sortedMonths.map(m => {
                        const [year, month] = m.split('-');
                        const date = new Date(year, month - 1);
                        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                    }),
                    datasets: [{
                        label: 'MRR',
                        data: sortedMonths.map(m => monthlyMRR[m]),
                        borderColor: '#9c27b0',
                        backgroundColor: 'rgba(156, 39, 176, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Timeline chart (daily new memberships - split by new vs renewal)
        const dailyNewSales = {};
        const dailyRenewals = {};
        membershipsData.forEach(m => {
            const boughtDate = m['Bought Date/Time (GMT)'] ? new Date(m['Bought Date/Time (GMT)']) : null;
            if (boughtDate) {
                const dateKey = boughtDate.toISOString().split('T')[0];
                if (m._isNewSale) {
                    dailyNewSales[dateKey] = (dailyNewSales[dateKey] || 0) + 1;
                } else if (m._isRenewal) {
                    dailyRenewals[dateKey] = (dailyRenewals[dateKey] || 0) + 1;
                }
            }
        });
        const sortedDailyDates = [...new Set([...Object.keys(dailyNewSales), ...Object.keys(dailyRenewals)])].sort();
        
        const timelineCanvas = document.getElementById('membershipTimelineChart');
        if (timelineCanvas) {
            destroyChart('membershipTimeline');
            const ctx = timelineCanvas.getContext('2d');
            allCharts.membershipTimeline = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sortedDailyDates,
                    datasets: [
                        {
                            label: 'New Sales',
                            data: sortedDailyDates.map(d => dailyNewSales[d] || 0),
                            backgroundColor: '#28a745',
                            borderColor: '#218838',
                            borderWidth: 1
                        },
                        {
                            label: 'Renewals',
                            data: sortedDailyDates.map(d => dailyRenewals[d] || 0),
                            backgroundColor: '#007bff',
                            borderColor: '#0056b3',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { 
                        legend: { 
                            display: true,
                            position: 'top'
                        } 
                    },
                    scales: {
                        x: { stacked: true },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }
        
        // Weekly Sales Trend
        const weeklyCanvas = document.getElementById('membershipWeeklyChart');
        if (weeklyCanvas) {
            destroyChart('membershipWeekly');
            const ctx = weeklyCanvas.getContext('2d');
            
            // Group by week
            const weeklyData = {};
            filteredMemberships.forEach(m => {
                const boughtDate = m['Bought Date/Time (GMT)'] ? new Date(m['Bought Date/Time (GMT)']) : null;
                if (boughtDate) {
                    const year = boughtDate.getFullYear();
                    const week = Math.ceil((boughtDate - new Date(year, 0, 1)) / (7 * 24 * 60 * 60 * 1000));
                    const weekKey = `${year}-W${String(week).padStart(2, '0')}`;
                    if (!weeklyData[weekKey]) {
                        weeklyData[weekKey] = { count: 0, revenue: 0 };
                    }
                    weeklyData[weekKey].count++;
                    weeklyData[weekKey].revenue += parseFloat(m['Paid Amount']) || 0;
                }
            });
            
            const sortedWeeks = Object.keys(weeklyData).sort();
            
            allCharts.membershipWeekly = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: sortedWeeks,
                    datasets: [
                        {
                            label: 'Weekly Sales Count',
                            data: sortedWeeks.map(w => weeklyData[w].count),
                            borderColor: '#007bff',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Weekly Revenue',
                            data: sortedWeeks.map(w => weeklyData[w].revenue),
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            beginAtZero: true,
                            grid: {
                                drawOnChartArea: false
                            },
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Day of Week Chart
        const dayOfWeekCanvas = document.getElementById('membershipDayOfWeekChart');
        if (dayOfWeekCanvas) {
            destroyChart('membershipDayOfWeek');
            const ctx = dayOfWeekCanvas.getContext('2d');
            
            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const dayData = {};
            dayNames.forEach(day => dayData[day] = 0);
            
            membershipsData.forEach(m => {
                const boughtDate = m['Bought Date/Time (GMT)'] ? new Date(m['Bought Date/Time (GMT)']) : null;
                if (boughtDate) {
                    const dayName = dayNames[boughtDate.getDay()];
                    dayData[dayName]++;
                }
            });
            
            allCharts.membershipDayOfWeek = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: dayNames,
                    datasets: [{
                        label: 'Memberships Sold',
                        data: dayNames.map(d => dayData[d]),
                        backgroundColor: '#ffc107',
                        borderColor: '#ff9800',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }
        
        // Average Sale Value Over Time
        const avgValueCanvas = document.getElementById('membershipAvgValueChart');
        if (avgValueCanvas) {
            destroyChart('membershipAvgValue');
            const ctx = avgValueCanvas.getContext('2d');
            
            // Calculate average value per month
            const monthlyAvg = {};
            sortedMonths.forEach(month => {
                const monthMemberships = filteredMemberships.filter(m => {
                    const boughtDate = m['Bought Date/Time (GMT)'] ? new Date(m['Bought Date/Time (GMT)']) : null;
                    if (boughtDate) {
                        const memberMonth = `${boughtDate.getFullYear()}-${String(boughtDate.getMonth() + 1).padStart(2, '0')}`;
                        return memberMonth === month;
                    }
                    return false;
                });
                
                if (monthMemberships.length > 0) {
                    const totalValue = monthMemberships.reduce((sum, m) => sum + (parseFloat(m['Paid Amount']) || 0), 0);
                    monthlyAvg[month] = totalValue / monthMemberships.length;
                } else {
                    monthlyAvg[month] = 0;
                }
            });
            
            allCharts.membershipAvgValue = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: sortedMonths.map(m => {
                        const [year, month] = m.split('-');
                        const date = new Date(year, month - 1);
                        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                    }),
                    datasets: [{
                        label: 'Average Sale Value',
                        data: sortedMonths.map(m => monthlyAvg[m]),
                        borderColor: '#ff6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        }
    }, 100);
    
    // Add cancellations data to memberships tab if available
    if (membershipCancellationsData && membershipCancellationsData.length > 0) {
        setTimeout(() => {
            appendCancellationsToMemberships();
        }, 150);
    }
}

// Export functions for membership data

export function renderLeadsTab() {
    // Check if we have the enhanced leads converted data
    const hasConvertedData = leadsConvertedData && leadsConvertedData.length > 0;
    
    if (!hasConvertedData && (!leadsData || leadsData.length === 0)) {
        document.getElementById('leads').innerHTML = `
            <div class="alert info">
                <h4>📊 Leads Analytics</h4>
                <p>Upload the <strong>Leads Converted Report CSV</strong> file to unlock comprehensive lead analytics including:</p>
                <ul style="margin: 10px 0 0 20px;">
                    <li>Detailed lead source tracking</li>
                    <li>Conversion funnel analysis</li>
                    <li>Location-based performance</li>
                    <li>Timeline of lead generation and conversions</li>
                    <li>LTV by source and location</li>
                </ul>
            </div>
        `;
        return;
    }
    
    // Use enhanced data if available, otherwise fallback to basic leads data
    const leadsToAnalyze = hasConvertedData ? leadsConvertedData : leadsData;
    
    // Filter by date range
    const filtered = leadsToAnalyze.filter(row => {
        let dateField = null;
        if (hasConvertedData) {
            dateField = parseDate(row['Converted']);
        } else {
            dateField = parseDate(row['Join date']);
        }
        
        if (!dateField) return false;
        
        const month = document.getElementById('monthFilter').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (month !== 'all') {
            const rowMonth = `${dateField.getFullYear()}-${String(dateField.getMonth() + 1).padStart(2, '0')}`;
            if (rowMonth !== month) return false;
        }
        
        if (startDate && dateField < new Date(startDate)) return false;
        if (endDate && dateField > new Date(endDate + 'T23:59:59')) return false;
        
        return true;
    });
    
    // Analyze data
    const analysis = analyzeLeadsData(filtered, hasConvertedData);
    
    // Render the comprehensive dashboard
    let html = renderLeadsOverview(analysis, hasConvertedData);
    html += renderLeadsSourceAnalysis(analysis, filtered, hasConvertedData);
    html += renderLeadsLocationAnalysis(analysis, filtered, hasConvertedData);
    html += renderLeadsTimeline(filtered, hasConvertedData);
    html += renderLeadsConversionFunnel(analysis, hasConvertedData);
    
    document.getElementById('leads').innerHTML = html;
    
    // Render all charts
    setTimeout(() => {
        renderLeadsCharts(analysis, filtered, hasConvertedData);
    }, 100);
}

export function analyzeLeadsData(leads, hasConvertedData) {
    const analysis = {
        totalLeads: leads.length,
        sources: {},
        locations: {},
        convertedTo: {},
        byDate: {},
        byDayOfWeek: { 'Sunday': 0, 'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0, 'Saturday': 0 },
        byHour: {},
        converted: 0,
        notConverted: 0,
        totalLTV: 0,
        ltvBySource: {},
        ltvByLocation: {},
        conversionsByMonth: {},
        sourcesByLocation: {}
    };
    
    // Initialize hours
    for (let i = 0; i < 24; i++) {
        analysis.byHour[i] = 0;
    }
    
    leads.forEach(lead => {
        let dateField = null;
        let source = 'Unknown';
        let location = 'Unknown';
        let ltv = 0;
        let isConverted = false;
        let convertedTo = 'N/A';
        
        if (hasConvertedData) {
            dateField = parseDate(lead['Converted']);
            source = lead['Lead source'] || 'Unknown';
            // Filter out N/A sources
            if (source === 'N/A' || source === 'n/a') {
                source = 'Unknown';
            }
            location = lead['Home location'] || 'Unknown';
            ltv = parseLTV(lead['LTV']);
            convertedTo = (lead['Converted to'] || '').trim();
            isConverted = convertedTo && convertedTo !== 'N/A' && convertedTo !== '';
        } else {
            dateField = parseDate(lead['Join date']);
            source = lead['Aggregator'] || 'Unknown';
            // Filter out N/A sources
            if (source === 'N/A' || source === 'n/a') {
                source = 'Unknown';
            }
            const type = (lead['Type'] || '').toLowerCase();
            isConverted = type === 'customer';
            ltv = parseLTV(lead['LTV']);
        }
        
        // Count by source
        if (!analysis.sources[source]) {
            analysis.sources[source] = { count: 0, converted: 0, ltv: 0 };
        }
        analysis.sources[source].count++;
        analysis.sources[source].ltv += ltv;
        if (isConverted) analysis.sources[source].converted++;
        
        // Count by location
        if (!analysis.locations[location]) {
            analysis.locations[location] = { count: 0, converted: 0, ltv: 0 };
        }
        analysis.locations[location].count++;
        analysis.locations[location].ltv += ltv;
        if (isConverted) analysis.locations[location].converted++;
        
        // Source by location matrix
        const key = `${source}|${location}`;
        if (!analysis.sourcesByLocation[key]) {
            analysis.sourcesByLocation[key] = { source, location, count: 0, converted: 0, ltv: 0 };
        }
        analysis.sourcesByLocation[key].count++;
        analysis.sourcesByLocation[key].ltv += ltv;
        if (isConverted) analysis.sourcesByLocation[key].converted++;
        
        // Conversion tracking
        if (isConverted) {
            analysis.converted++;
            if (hasConvertedData && convertedTo !== 'N/A') {
                if (!analysis.convertedTo[convertedTo]) {
                    analysis.convertedTo[convertedTo] = { count: 0, ltv: 0 };
                }
                analysis.convertedTo[convertedTo].count++;
                analysis.convertedTo[convertedTo].ltv += ltv;
            }
        } else {
            analysis.notConverted++;
        }
        
        analysis.totalLTV += ltv;
        
        // Time-based analysis
        if (dateField) {
            // By date
            const dateKey = dateField.toISOString().split('T')[0];
            analysis.byDate[dateKey] = (analysis.byDate[dateKey] || 0) + 1;
            
            // By day of week
            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const dayOfWeek = dayNames[dateField.getDay()];
            analysis.byDayOfWeek[dayOfWeek]++;
            
            // By hour
            const hour = dateField.getHours();
            analysis.byHour[hour]++;
            
            // Conversions by month
            if (isConverted) {
                const monthKey = `${dateField.getFullYear()}-${String(dateField.getMonth() + 1).padStart(2, '0')}`;
                analysis.conversionsByMonth[monthKey] = (analysis.conversionsByMonth[monthKey] || 0) + 1;
            }
        }
    });
    
    return analysis;
}


export function renderJourneyTab() {
    // Check if leads data is available
    if (!leadsData || leadsData.length === 0) {
        document.getElementById('journey').innerHTML = `
            <div class="alert info">
                <h4>🚀 Client Journey Visualization</h4>
                <p>Upload the <strong>Leads & Customers CSV</strong> file to unlock the journey visualization showing how clients progress from leads to loyal customers.</p>
            </div>
        `;
        return;
    }
    
    const data = filteredAppointments;
    // Use global filteredLeads
    
    // Calculate journey stages (using same logic as Funnel tab)
    const totalPeople = filteredLeads.length;
    const customers = filteredLeads.filter(row => row.Type === 'Customer').length;
    const leads = totalPeople - customers;
    
    // Intro offers (same logic as Funnel tab)
    const hadIntroOffer = filteredLeads.filter(row => {
        const firstPurchase = row['First purchase'] || '';
        return firstPurchase && firstPurchase !== 'N/A' && isIntroOffer(firstPurchase);
    }).length;
    
    // Made first paid purchase
    const madePurchase = filteredLeads.filter(row => {
        const firstPurchase = row['First purchase'] || '';
        return firstPurchase && firstPurchase !== 'N/A' && !isIntroOffer(firstPurchase);
    }).length;
    
    // Repeat customers (2+ visits)
    const clientVisits = {};
    data.forEach(row => {
        const email = (row['Customer Email'] || '').toLowerCase().trim();
        if (email) {
            clientVisits[email] = (clientVisits[email] || 0) + 1;
        }
    });
    const repeatCustomers = Object.values(clientVisits).filter(count => count >= 2).length;
    
    // Loyal customers (5+ visits)
    const loyalCustomers = Object.values(clientVisits).filter(count => count >= 5).length;
    
    // Calculate conversion rates (with safety checks for division by zero)
    const leadToCustomer = totalPeople > 0 ? (customers / totalPeople * 100) : 0;
    const customerToIntro = customers > 0 ? (hadIntroOffer / customers * 100) : 0;
    const introToPurchase = hadIntroOffer > 0 ? (madePurchase / hadIntroOffer * 100) : 0;
    const purchaseToRepeat = madePurchase > 0 ? (repeatCustomers / madePurchase * 100) : 0;
    const repeatToLoyal = repeatCustomers > 0 ? (loyalCustomers / repeatCustomers * 100) : 0;
    
    // Calculate drop-offs (with safety checks)
    const dropLeadToCustomer = totalPeople > 0 ? ((totalPeople - customers) / totalPeople * 100).toFixed(0) : '0';
    const dropCustomerToIntro = customers > 0 ? ((customers - hadIntroOffer) / customers * 100).toFixed(0) : '0';
    const dropIntroToPurchase = hadIntroOffer > 0 ? ((hadIntroOffer - madePurchase) / hadIntroOffer * 100).toFixed(0) : '0';
    const dropPurchaseToRepeat = madePurchase > 0 ? ((madePurchase - repeatCustomers) / madePurchase * 100).toFixed(0) : '0';
    const dropRepeatToLoyal = repeatCustomers > 0 ? ((repeatCustomers - loyalCustomers) / repeatCustomers * 100).toFixed(0) : '0';
    
    let html = `
        <div class="alert info">
            <h3>🚀 Client Journey Visualization</h3>
            <p>Track how clients progress through your sales funnel, from first contact to loyal customer. Click any stage for details.</p>
        </div>
        
        <div class="journey-flow">
            <div class="journey-stage" onclick="showJourneyDetails('leads', ${totalPeople})">
                <div class="journey-stage-icon">👥</div>
                <div class="journey-stage-title">TOTAL CONTACTS</div>
                <div class="journey-stage-count">${formatNumber(totalPeople)}<br><span class="journey-stage-percent">100%</span></div>
            </div>
            
            <div class="journey-arrow">→</div>
            
            <div class="journey-stage" onclick="showJourneyDetails('customers', ${customers})" style="position: relative;">
                ${dropLeadToCustomer > 0 ? `<div class="journey-dropoff">-${dropLeadToCustomer}% drop</div>` : ''}
                <div class="journey-stage-icon">✅</div>
                <div class="journey-stage-title">CUSTOMERS</div>
                <div class="journey-stage-count">${formatNumber(customers)}<br><span class="journey-stage-percent">${isFinite(leadToCustomer) ? leadToCustomer.toFixed(0) : '0'}%</span></div>
            </div>
            
            <div class="journey-arrow">→</div>
            
            <div class="journey-stage" onclick="showJourneyDetails('intro', ${hadIntroOffer})" style="position: relative;">
                ${dropCustomerToIntro > 0 ? `<div class="journey-dropoff">-${dropCustomerToIntro}% drop</div>` : ''}
                <div class="journey-stage-icon">🎫</div>
                <div class="journey-stage-title">TRIED INTRO</div>
                <div class="journey-stage-count">${formatNumber(hadIntroOffer)}<br><span class="journey-stage-percent">${isFinite(customerToIntro) ? customerToIntro.toFixed(0) : '0'}%</span></div>
            </div>
            
            <div class="journey-arrow">→</div>
            
            <div class="journey-stage" onclick="showJourneyDetails('purchase', ${madePurchase})" style="position: relative;">
                ${dropIntroToPurchase > 0 ? `<div class="journey-dropoff">-${dropIntroToPurchase}% drop</div>` : ''}
                <div class="journey-stage-icon">💳</div>
                <div class="journey-stage-title">FIRST PURCHASE</div>
                <div class="journey-stage-count">${formatNumber(madePurchase)}<br><span class="journey-stage-percent">${isFinite(introToPurchase) ? introToPurchase.toFixed(0) : '0'}%</span></div>
            </div>
            
            <div class="journey-arrow">→</div>
            
            <div class="journey-stage" onclick="showJourneyDetails('repeat', ${repeatCustomers})" style="position: relative;">
                ${dropPurchaseToRepeat > 0 ? `<div class="journey-dropoff">-${dropPurchaseToRepeat}% drop</div>` : ''}
                <div class="journey-stage-icon">🔄</div>
                <div class="journey-stage-title">REPEAT (2+)</div>
                <div class="journey-stage-count">${formatNumber(repeatCustomers)}<br><span class="journey-stage-percent">${isFinite(purchaseToRepeat) ? purchaseToRepeat.toFixed(0) : '0'}%</span></div>
            </div>
            
            <div class="journey-arrow">→</div>
            
            <div class="journey-stage" onclick="showJourneyDetails('loyal', ${loyalCustomers})" style="position: relative;">
                ${dropRepeatToLoyal > 0 ? `<div class="journey-dropoff">-${dropRepeatToLoyal}% drop</div>` : ''}
                <div class="journey-stage-icon">👑</div>
                <div class="journey-stage-title">LOYAL (5+)</div>
                <div class="journey-stage-count">${formatNumber(loyalCustomers)}<br><span class="journey-stage-percent">${isFinite(repeatToLoyal) ? repeatToLoyal.toFixed(0) : '0'}%</span></div>
            </div>
        </div>
        
        <div class="table-container">
            <h2>Journey Conversion Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Stage Transition</th>
                        <th>Count</th>
                        <th>Conversion Rate</th>
                        <th>Drop-off</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Contacts → Customers</td>
                        <td>${formatNumber(customers)} / ${formatNumber(totalPeople)}</td>
                        <td><strong>${totalPeople > 0 ? leadToCustomer.toFixed(1) : '0.0'}%</strong></td>
                        <td>${dropLeadToCustomer}%</td>
                        <td>${leadToCustomer >= 40 ? '✅ Good' : leadToCustomer > 0 ? '⚠️ Needs Work' : '➖ N/A'}</td>
                    </tr>
                    <tr>
                        <td>Customers → Intro Offer</td>
                        <td>${formatNumber(hadIntroOffer)} / ${formatNumber(customers)}</td>
                        <td><strong>${customers > 0 ? customerToIntro.toFixed(1) : '0.0'}%</strong></td>
                        <td>${dropCustomerToIntro}%</td>
                        <td>${customerToIntro >= 50 ? '✅ Good' : customerToIntro > 0 ? '⚠️ Needs Work' : '➖ N/A'}</td>
                    </tr>
                    <tr>
                        <td>Intro → First Purchase</td>
                        <td>${formatNumber(madePurchase)} / ${formatNumber(hadIntroOffer)}</td>
                        <td><strong>${hadIntroOffer > 0 ? introToPurchase.toFixed(1) : '0.0'}%</strong></td>
                        <td>${dropIntroToPurchase}%</td>
                        <td>${introToPurchase >= 30 ? '✅ Good' : introToPurchase > 0 ? '⚠️ Needs Work' : '➖ N/A'}</td>
                    </tr>
                    <tr>
                        <td>Purchase → Repeat</td>
                        <td>${formatNumber(repeatCustomers)} / ${formatNumber(madePurchase)}</td>
                        <td><strong>${madePurchase > 0 ? purchaseToRepeat.toFixed(1) : '0.0'}%</strong></td>
                        <td>${dropPurchaseToRepeat}%</td>
                        <td>${purchaseToRepeat >= 40 ? '✅ Good' : purchaseToRepeat > 0 ? '⚠️ Needs Work' : '➖ N/A'}</td>
                    </tr>
                    <tr>
                        <td>Repeat → Loyal</td>
                        <td>${formatNumber(loyalCustomers)} / ${formatNumber(repeatCustomers)}</td>
                        <td><strong>${repeatCustomers > 0 ? repeatToLoyal.toFixed(1) : '0.0'}%</strong></td>
                        <td>${dropRepeatToLoyal}%</td>
                        <td>${repeatToLoyal >= 30 ? '✅ Good' : repeatToLoyal > 0 ? '⚠️ Needs Work' : '➖ N/A'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="alert ${introToPurchase >= 30 ? 'success' : 'warning'}">
            <h4>💡 Journey Optimization Recommendations</h4>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                ${leadToCustomer < 40 ? '<li><strong>Lead Conversion:</strong> Focus on improving your lead nurturing process. Consider adding more touchpoints and personalized follow-ups.</li>' : ''}
                ${customerToIntro < 50 ? '<li><strong>Intro Offer Adoption:</strong> Make your intro offer more visible and compelling. Consider a time-limited promotion to create urgency.</li>' : ''}
                ${introToPurchase < 30 ? '<li><strong>Intro-to-Purchase:</strong> Your intro offer conversion needs improvement. Follow up within 24 hours of intro sessions and highlight package benefits.</li>' : ''}
                ${purchaseToRepeat < 40 ? '<li><strong>First-to-Second Visit:</strong> This is critical! Implement immediate rebooking at checkout and send reminders within 48 hours.</li>' : ''}
                ${repeatToLoyal < 30 ? '<li><strong>Building Loyalty:</strong> Create a loyalty program or membership for clients with 3-4 visits to incentivize reaching 5+.</li>' : ''}
                <li><strong>Biggest Opportunity:</strong> ${Math.max(dropLeadToCustomer, dropCustomerToIntro, dropIntroToPurchase, dropPurchaseToRepeat, dropRepeatToLoyal) == dropLeadToCustomer ? 'Convert more leads to customers' : Math.max(dropCustomerToIntro, dropIntroToPurchase, dropPurchaseToRepeat, dropRepeatToLoyal) == dropCustomerToIntro ? 'Get more customers to try intro offers' : Math.max(dropIntroToPurchase, dropPurchaseToRepeat, dropRepeatToLoyal) == dropIntroToPurchase ? 'Convert intro offers to purchases' : Math.max(dropPurchaseToRepeat, dropRepeatToLoyal) == dropPurchaseToRepeat ? 'Get first-time buyers to return' : 'Build loyalty with repeat customers'}</li>
            </ul>
        </div>
        
        <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Conversion Rate</div>
                <div class="metric-value">${(customers / totalPeople * 100).toFixed(1)}%</div>
                <div class="metric-subtext">Lead → Customer</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Intro Offer Rate</div>
                <div class="metric-value">${(hadIntroOffer / totalPeople * 100).toFixed(1)}%</div>
                <div class="metric-subtext">Tried introductory offer</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Purchase Rate</div>
                <div class="metric-value">${(madePurchase / totalPeople * 100).toFixed(1)}%</div>
                <div class="metric-subtext">Made actual purchase</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Revenue Rate</div>
                <div class="metric-value">${(() => {
                    const ltvs = leadsData.map(row => parseLTV(row.LTV));
                    const hasRevenue = ltvs.filter(ltv => ltv > 0).length;
                    return (hasRevenue / totalPeople * 100).toFixed(1);
                })()}%</div>
                <div class="metric-subtext">Generating LTV</div>
            </div>
        </div>
    `;
    
    document.getElementById('journey').innerHTML = html;
}


// AI RECOMMENDATIONS ENGINE
export function generateSmartRecommendations() {
    const data = filteredAppointments;
    // Use global leadsData directly
    const recommendations = [];
    
    // Calculate key metrics
    const totalRevenue = data.reduce((sum, row) => sum + parseFloat(row.Revenue || 0), 0);
    const totalPayout = data.reduce((sum, row) => sum + parseFloat(row['Total Payout'] || 0), 0);
    const profit = totalRevenue - totalPayout;
    const profitMargin = totalRevenue > 0 ? (profit / totalRevenue * 100) : 0;
    
    const clientVisits = {};
    data.forEach(row => {
        const email = (row['Customer Email'] || '').toLowerCase().trim();
        if (email) {
            clientVisits[email] = (clientVisits[email] || 0) + 1;
        }
    });
    
    const uniqueClients = Object.keys(clientVisits).length;
    const returningClients = Object.values(clientVisits).filter(count => count > 1).length;
    const retentionRate = uniqueClients > 0 ? (returningClients / uniqueClients * 100) : 0;
    const avgRevPerClient = uniqueClients > 0 ? totalRevenue / uniqueClients : 0;
    
    // RECOMMENDATION 1: Low Retention Rate
    if (retentionRate < 40) {
        recommendations.push({
            priority: 'high',
            title: 'Critical: Improve Client Retention',
            description: `Your retention rate is ${retentionRate.toFixed(0)}%, which is below the industry target of 50%+. You're losing ${100 - retentionRate.toFixed(0)}% of clients after their first visit.`,
            action: 'Implement an automated follow-up sequence: 24 hours (thank you), 7 days (check-in), 14 days (special offer). Set up rebooking incentives at checkout.',
            impact: `Increasing retention to 50% could add ${formatCurrency(avgRevPerClient * uniqueClients * 0.5)} in revenue`,
            impactValue: avgRevPerClient * uniqueClients * 0.5
        });
    }
    
    // RECOMMENDATION 2: Low Profit Margin
    if (profitMargin < 25) {
        recommendations.push({
            priority: 'high',
            title: 'Optimize Profit Margins',
            description: `Your profit margin of ${profitMargin.toFixed(1)}% is below optimal (30%+). This limits growth and reinvestment capacity.`,
            action: 'Review practitioner payout structure, optimize scheduling to reduce idle time, and consider 5-10% price increase for premium services.',
            impact: `Improving margin to 30% would add ${formatCurrency(totalRevenue * 0.3 - profit)} to profit`,
            impactValue: totalRevenue * 0.3 - profit
        });
    }
    
    // RECOMMENDATION 3: At-Risk Clients
    const today = new Date();
    const avgDaysBetween = 30; // Simplified
    const atRiskCount = Object.entries(clientVisits).filter(([email, visits]) => {
        if (visits <= 1) return false;
        const lastVisit = data.filter(r => r['Customer Email']?.toLowerCase().trim() === email)
            .map(r => parseDate(r['Appointment Date']))
            .sort((a, b) => b - a)[0];
        if (!lastVisit) return false;
        const daysSince = (today - lastVisit) / (1000 * 60 * 60 * 24);
        return daysSince > avgDaysBetween * 1.5;
    }).length;
    
    if (atRiskCount > 0) {
        const atRiskRevenue = atRiskCount * avgRevPerClient;
        recommendations.push({
            priority: 'high',
            title: `Re-engage ${atRiskCount} At-Risk Clients`,
            description: `${atRiskCount} returning clients haven't visited recently. They represent ${formatCurrency(atRiskRevenue)} in historical revenue.`,
            action: `Launch a "We miss you" campaign with a special 20% comeback offer. Personalize messages referencing their last service.`,
            impact: `Recovering 30% could bring back ${formatCurrency(atRiskRevenue * 0.3)}`,
            impactValue: atRiskRevenue * 0.3
        });
    }
    
    // RECOMMENDATION 4: Package Opportunities
    const avgVisitsPerClient = uniqueClients > 0 ? data.length / uniqueClients : 0;
    if (avgVisitsPerClient < 3) {
        recommendations.push({
            priority: 'medium',
            title: 'Create Package Deals to Increase Visit Frequency',
            description: `Average client visits only ${avgVisitsPerClient.toFixed(1)} times. Package deals encourage commitment and increase CLV.`,
            action: 'Create 3-pack (10% off), 5-pack (15% off), and 10-pack (20% off) bundles. Promote as "best value" at checkout.',
            impact: `Increasing avg visits to 4 could add ${formatCurrency((4 - avgVisitsPerClient) * uniqueClients * (totalRevenue / data.length))}`,
            impactValue: (4 - avgVisitsPerClient) * uniqueClients * (totalRevenue / data.length)
        });
    }
    
    // RECOMMENDATION 5: Intro Offer Conversion
    if (leadsData && leadsData.length > 0) {
        const hadIntro = leadsData.filter(row => isIntroOffer(row['First purchase'] || '')).length;
        const madePurchase = leadsData.filter(row => {
            const fp = row['First purchase'] || '';
            return fp && fp !== 'N/A' && !isIntroOffer(fp);
        }).length;
        const introConversion = hadIntro > 0 ? (madePurchase / hadIntro * 100) : 0;
        
        if (introConversion < 30 && hadIntro > 0) {
            recommendations.push({
                priority: 'high',
                title: 'Boost Intro Offer to Purchase Conversion',
                description: `Only ${introConversion.toFixed(0)}% of intro offers convert to paid purchases. Industry best practice is 35-40%.`,
                action: 'Follow up within 24 hours of intro sessions. Offer limited-time package deal. Train staff on conversion techniques.',
                impact: `Improving to 35% would add ${formatNumber(hadIntro * 0.35 - madePurchase)} new paying clients`,
                impactValue: (hadIntro * 0.35 - madePurchase) * avgRevPerClient
            });
        }
    }
    
    // RECOMMENDATION 6: Revenue per Client
    if (avgRevPerClient < 200) {
        recommendations.push({
            priority: 'medium',
            title: 'Increase Average Client Value',
            description: `Your average revenue per client is ${formatCurrency(avgRevPerClient)}. Strategic upselling could significantly boost this.`,
            action: 'Train team on consultative selling. Recommend add-ons (extended sessions, complementary services). Create premium service tier.',
            impact: `Increasing to ${formatCurrency(avgRevPerClient * 1.25)} would add ${formatCurrency((avgRevPerClient * 1.25 - avgRevPerClient) * uniqueClients)}`,
            impactValue: (avgRevPerClient * 1.25 - avgRevPerClient) * uniqueClients
        });
    }
    
    // RECOMMENDATION 7: Referral Program
    const newClientsNeeded = Math.max(0, uniqueClients * 0.2); // 20% growth target
    if (newClientsNeeded > 0) {
        recommendations.push({
            priority: 'medium',
            title: 'Launch Referral Program for Growth',
            description: `To achieve 20% client growth, you need ${Math.ceil(newClientsNeeded)} new clients. Referrals are the most cost-effective acquisition channel.`,
            action: 'Offer referring client $20 credit + new client 20% off first visit. Promote via email, in-office signage, and social media.',
            impact: `${Math.ceil(newClientsNeeded)} new clients could add ${formatCurrency(newClientsNeeded * avgRevPerClient)}`,
            impactValue: newClientsNeeded * avgRevPerClient
        });
    }
    
    // RECOMMENDATION 8: Frozen Memberships
    if (membershipsData && membershipsData.length > 0) {
        const frozenCount = membershipsData.filter(m => m.Frozen === 'Yes').length;
        const frozenRate = (frozenCount / membershipsData.length) * 100;
        
        if (frozenRate > 10) {
            recommendations.push({
                priority: 'high',
                title: 'Address High Frozen Membership Rate',
                description: `${frozenRate.toFixed(1)}% of memberships are frozen. This indicates potential dissatisfaction or life changes that might lead to cancellations.`,
                action: 'Reach out personally to frozen members. Offer flexible restart options, pause benefits, or alternative services. Create a "comeback" special offer.',
                impact: `Reactivating 50% of frozen members could recover ${formatCurrency((frozenCount * 0.5) * avgRevPerClient)}`,
                impactValue: (frozenCount * 0.5) * avgRevPerClient
            });
        } else if (frozenCount > 0) {
            recommendations.push({
                priority: 'medium',
                title: 'Monitor Frozen Memberships',
                description: `You have ${frozenCount} frozen membership${frozenCount > 1 ? 's' : ''}. Proactive outreach can prevent cancellations.`,
                action: 'Schedule check-ins with frozen members. Understand their concerns and offer solutions to help them resume their wellness journey.',
                impact: `Preventing cancellations protects ${formatCurrency(frozenCount * avgRevPerClient)} in potential revenue`,
                impactValue: frozenCount * avgRevPerClient
            });
        }
    }
    
    // RECOMMENDATION 9: Refunded Memberships
    if (membershipsData && membershipsData.length > 0) {
        const refundedCount = membershipsData.filter(m => parseFloat(m.Refunded) > 0).length;
        const totalRefunded = membershipsData.reduce((sum, m) => sum + (parseFloat(m.Refunded) || 0), 0);
        const refundRate = (refundedCount / membershipsData.length) * 100;
        
        if (refundRate > 5) {
            recommendations.push({
                priority: 'high',
                title: 'Reduce Membership Refund Rate',
                description: `${refundRate.toFixed(1)}% of memberships have been refunded (${formatCurrency(totalRefunded)} total). This suggests issues with value delivery or expectations.`,
                action: 'Analyze refund reasons. Improve onboarding process. Set clear expectations. Consider satisfaction check-ins after first 2-3 sessions.',
                impact: `Reducing refunds by 50% would save ${formatCurrency(totalRefunded * 0.5)}`,
                impactValue: totalRefunded * 0.5
            });
        } else if (refundedCount > 0) {
            recommendations.push({
                priority: 'low',
                title: 'Low Refund Rate - Maintain Quality',
                description: `Your refund rate is ${refundRate.toFixed(1)}%, which is excellent. This indicates strong value delivery and customer satisfaction.`,
                action: 'Continue current quality standards. Document what\'s working and train all team members on best practices.',
                impact: 'Maintaining low refund rates protects revenue and reputation',
                impactValue: 0
            });
        }
    }
    
    // Sort by impact value
    recommendations.sort((a, b) => b.impactValue - a.impactValue);
    
    return recommendations;
}

// Show journey stage details

// ============================================================================
// SUPPORTING FUNCTIONS FOR LEADS TAB
// ============================================================================

export function renderLeadsOverview(analysis, hasConvertedData) {
    const conversionRate = analysis.totalLeads > 0 ? (analysis.converted / analysis.totalLeads * 100) : 0;
    const avgLTV = analysis.converted > 0 ? (analysis.totalLTV / analysis.converted) : 0;
    
    // Find top source and location
    const sortedSources = Object.entries(analysis.sources).sort((a, b) => b[1].count - a[1].count);
    const topSource = sortedSources[0];
    
    const sortedLocations = Object.entries(analysis.locations).sort((a, b) => b[1].count - a[1].count);
    const topLocation = sortedLocations[0];
    
    // Best performing source (by conversion rate)
    const bestSource = sortedSources
        .filter(([_, data]) => data.count >= 5) // At least 5 leads
        .sort((a, b) => (b[1].converted/b[1].count) - (a[1].converted/a[1].count))[0];
    
    return `
        <div class="section">
            <h2>📊 Leads & Conversion Overview</h2>
            
            <div class="metrics-grid" style="grid-template-columns: repeat(6, 1fr); margin-bottom: 30px;">
                <div class="metric-card">
                    <div class="metric-label">🎯 Total Leads</div>
                    <div class="metric-value">${formatNumber(analysis.totalLeads)}</div>
                    <div class="metric-subtext">All lead entries</div>
                </div>
                
                <div class="metric-card" style="background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(30, 130, 50, 0.05));">
                    <div class="metric-label">✅ Converted</div>
                    <div class="metric-value">${formatNumber(analysis.converted)}</div>
                    <div class="metric-subtext">${conversionRate.toFixed(1)}% conversion rate</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">💰 Total LTV</div>
                    <div class="metric-value">${formatCurrency(analysis.totalLTV)}</div>
                    <div class="metric-subtext">From converted leads</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">📈 Avg LTV</div>
                    <div class="metric-value">${formatCurrency(avgLTV)}</div>
                    <div class="metric-subtext">Per converted lead</div>
                </div>
                
                <div class="metric-card" style="background: linear-gradient(135deg, rgba(1, 49, 96, 0.1), rgba(1, 49, 96, 0.05));">
                    <div class="metric-label">🏆 Top Source</div>
                    <div class="metric-value" style="font-size: 1.1em;">${topSource ? topSource[0].substring(0, 12) : 'N/A'}</div>
                    <div class="metric-subtext">${topSource ? formatNumber(topSource[1].count) : 0} leads</div>
                </div>
                
                <div class="metric-card" style="background: linear-gradient(135deg, rgba(113, 190, 210, 0.15), rgba(113, 190, 210, 0.05));">
                    <div class="metric-label">📍 Top Location</div>
                    <div class="metric-value" style="font-size: 1.1em;">${topLocation ? topLocation[0] : 'N/A'}</div>
                    <div class="metric-subtext">${topLocation ? formatNumber(topLocation[1].count) : 0} leads</div>
                </div>
            </div>
            
            ${bestSource ? `
            <div class="alert" style="background: linear-gradient(135deg, rgba(251, 181, 20, 0.1), rgba(251, 181, 20, 0.05)); border-left: 4px solid var(--highlight);">
                <h4>⭐ Best Performing Source</h4>
                <p><strong>${bestSource[0]}</strong> has the highest conversion rate: ${((bestSource[1].converted/bestSource[1].count)*100).toFixed(1)}% 
                (${formatNumber(bestSource[1].converted)} of ${formatNumber(bestSource[1].count)} leads converted)</p>
            </div>
            ` : ''}
        </div>
    `;
}


export function renderLeadsSourceAnalysis(analysis, leads, hasConvertedData) {
    const sortedSources = Object.entries(analysis.sources)
        .sort((a, b) => b[1].count - a[1].count);
    
    return `
        <div class="section">
            <h2>🎯 Lead Source Performance</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <h3>Lead Volume by Source</h3>
                    <div class="chart-wrapper">
                        <canvas id="leadsSourceVolumeChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Conversion Rate by Source</h3>
                    <div class="chart-wrapper">
                        <canvas id="leadsSourceConversionChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="table-container" style="margin-top: 20px;">
                <h3>Detailed Source Breakdown</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Source</th>
                            <th>Total Leads</th>
                            <th>Converted</th>
                            <th>Conversion Rate</th>
                            <th>Total LTV</th>
                            <th>Avg LTV</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sortedSources.map(([source, data], i) => {
                            const convRate = data.count > 0 ? (data.converted / data.count * 100) : 0;
                            const avgLTV = data.converted > 0 ? (data.ltv / data.converted) : 0;
                            return `
                                <tr>
                                    <td><strong>${i + 1}</strong></td>
                                    <td><strong>${source}</strong></td>
                                    <td>${formatNumber(data.count)}</td>
                                    <td>${formatNumber(data.converted)}</td>
                                    <td><span style="padding: 4px 8px; border-radius: 4px; background: ${convRate >= 50 ? '#d4edda' : convRate >= 30 ? '#fff3cd' : '#f8d7da'}; color: ${convRate >= 50 ? '#155724' : convRate >= 30 ? '#856404' : '#721c24'};">${convRate.toFixed(1)}%</span></td>
                                    <td>${formatCurrency(data.ltv)}</td>
                                    <td>${formatCurrency(avgLTV)}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}


export function renderLeadsLocationAnalysis(analysis, leads, hasConvertedData) {
    const sortedLocations = Object.entries(analysis.locations)
        .sort((a, b) => b[1].count - a[1].count);
    
    // Source x Location matrix
    const matrix = Object.values(analysis.sourcesByLocation)
        .sort((a, b) => b.count - a.count)
        .slice(0, 15); // Top 15 combinations
    
    return `
        <div class="section">
            <h2>📍 Location Performance</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <h3>Leads by Location</h3>
                    <div class="chart-wrapper">
                        <canvas id="leadsLocationChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>LTV by Location</h3>
                    <div class="chart-wrapper">
                        <canvas id="leadsLocationLTVChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="table-container" style="margin-top: 20px;">
                <h3>Top Source × Location Combinations</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Source</th>
                            <th>Location</th>
                            <th>Leads</th>
                            <th>Converted</th>
                            <th>Conv. Rate</th>
                            <th>Total LTV</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${matrix.map((combo, i) => {
                            const convRate = combo.count > 0 ? (combo.converted / combo.count * 100) : 0;
                            return `
                                <tr>
                                    <td><strong>${i + 1}</strong></td>
                                    <td>${combo.source}</td>
                                    <td>${combo.location}</td>
                                    <td>${formatNumber(combo.count)}</td>
                                    <td>${formatNumber(combo.converted)}</td>
                                    <td>${convRate.toFixed(1)}%</td>
                                    <td>${formatCurrency(combo.ltv)}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}


export function renderLeadsTimeline(leads, hasConvertedData) {
    let html = `
        <div class="section">
            <h2>📅 Lead Generation Timeline</h2>
            <div class="chart-container full-width">
                <h3>Daily Lead Activity</h3>
                <div class="chart-wrapper">
                    <canvas id="leadsDailyChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔥 Lead Generation Heatmap (01/10/25)</h2>
            <p style="color: #666; margin-bottom: 15px;">Click any cell to see detailed lead information for that day and hour</p>
            <div id="leadsHeatmapContainer" style="overflow-x: auto;">
                <div id="leadsHeatmap"></div>
            </div>
        </div>
    `;
    
    // Add location-specific heatmaps for SocialFitness leads
    if (hasConvertedData) {
        const sfLeads = leads.filter(lead => {
            const source = (lead['Lead source'] || '').trim();
            return source.startsWith('SF');
        });
        
        if (sfLeads.length > 0) {
            // Group by location
            const locationMap = {};
            sfLeads.forEach(lead => {
                const location = lead['Home location'] || 'Unknown';
                if (!locationMap[location]) {
                    locationMap[location] = [];
                }
                locationMap[location].push(lead);
            });
            
            // Create heatmaps for each location
            Object.keys(locationMap).sort().forEach(location => {
                const locationLeads = locationMap[location];
                html += `
                    <div class="section" style="margin-bottom: 50px; padding: 20px; background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                        <h2>🔥 SocialFitness Heatmap - ${location}</h2>
                        <p style="color: #666; margin-bottom: 15px;">
                            <strong>${locationLeads.length}</strong> leads from SocialFitness at ${location} location
                        </p>
                        <div id="sfHeatmapContainer-${location.replace(/\s+/g, '-')}" style="overflow-x: auto;">
                            <div id="sfHeatmap-${location.replace(/\s+/g, '-')}"></div>
                        </div>
                    </div>
                `;
            });
        }
    }
    
    return html;
}


export function renderLeadsConversionFunnel(analysis, hasConvertedData) {
    if (!hasConvertedData || Object.keys(analysis.convertedTo).length === 0) {
        return '';
    }
    
    const sortedConversions = Object.entries(analysis.convertedTo)
        .sort((a, b) => b[1].count - a[1].count);
    
    return `
        <div class="section">
            <h2>🎯 Conversion Breakdown</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <h3>What Leads Converted To</h3>
                    <div class="chart-wrapper">
                        <canvas id="leadsConvertedToChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>LTV by Membership Type</h3>
                    <div class="chart-wrapper">
                        <canvas id="leadsConvertedToLTVChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="table-container" style="margin-top: 20px;">
                <h3>Conversion Type Details</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Membership/Offer</th>
                            <th>Conversions</th>
                            <th>% of Total</th>
                            <th>Total LTV</th>
                            <th>Avg LTV</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sortedConversions.map(([type, data], i) => {
                            const pct = (data.count / analysis.converted * 100);
                            const avgLTV = data.count > 0 ? (data.ltv / data.count) : 0;
                            return `
                                <tr>
                                    <td><strong>${i + 1}</strong></td>
                                    <td>${type}</td>
                                    <td>${formatNumber(data.count)}</td>
                                    <td>${pct.toFixed(1)}%</td>
                                    <td>${formatCurrency(data.ltv)}</td>
                                    <td>${formatCurrency(avgLTV)}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}


export function renderLeadsCharts(analysis, leads, hasConvertedData) {
    // Source Volume Chart
    const sourceCanvas = document.getElementById('leadsSourceVolumeChart');
    if (sourceCanvas) {
        destroyChart('leadsSourceVolume');
        const ctx = sourceCanvas.getContext('2d');
        const sortedSources = Object.entries(analysis.sources).sort((a, b) => b[1].count - a[1].count).slice(0, 10);
        allCharts.leadsSourceVolume = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedSources.map(s => s[0]),
                datasets: [{
                    label: 'Total Leads',
                    data: sortedSources.map(s => s[1].count),
                    backgroundColor: '#013160',
                    borderColor: '#013160',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const source = sortedSources[index][0];
                        const sourceLeads = leads.filter(l => (l['Lead source'] || 'Unknown') === source);
                        showLeadsSourceDetails(source, sourceLeads);
                    }
                },
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
    
    // Source Conversion Rate Chart
    const sourceConvCanvas = document.getElementById('leadsSourceConversionChart');
    if (sourceConvCanvas) {
        destroyChart('leadsSourceConversion');
        const ctx = sourceConvCanvas.getContext('2d');
        const sortedSources = Object.entries(analysis.sources)
            .filter(([_, data]) => data.count >= 3) // At least 3 leads
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 10);
        allCharts.leadsSourceConversion = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedSources.map(s => s[0]),
                datasets: [{
                    label: 'Conversion Rate (%)',
                    data: sortedSources.map(s => (s[1].converted / s[1].count * 100)),
                    backgroundColor: '#28a745',
                    borderColor: '#28a745',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const source = sortedSources[index][0];
                        const sourceLeads = leads.filter(l => (l['Lead source'] || 'Unknown') === source);
                        showLeadsSourceDetails(source, sourceLeads);
                    }
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y.toFixed(1)}% conversion`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Location Chart
    const locationCanvas = document.getElementById('leadsLocationChart');
    if (locationCanvas) {
        destroyChart('leadsLocation');
        const ctx = locationCanvas.getContext('2d');
        const sortedLocations = Object.entries(analysis.locations).sort((a, b) => b[1].count - a[1].count);
        allCharts.leadsLocation = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sortedLocations.map(l => l[0]),
                datasets: [{
                    data: sortedLocations.map(l => l[1].count),
                    backgroundColor: ['#013160', '#71BED2', '#FBB514', '#28a745', '#dc3545', '#ffc107', '#9c27b0'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { padding: 15, font: { size: 12 } }
                    }
                }
            }
        });
    }
    
    // Location LTV Chart
    const locationLTVCanvas = document.getElementById('leadsLocationLTVChart');
    if (locationLTVCanvas) {
        destroyChart('leadsLocationLTV');
        const ctx = locationLTVCanvas.getContext('2d');
        const sortedLocations = Object.entries(analysis.locations).sort((a, b) => b[1].ltv - a[1].ltv);
        allCharts.leadsLocationLTV = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedLocations.map(l => l[0]),
                datasets: [{
                    label: 'Total LTV',
                    data: sortedLocations.map(l => l[1].ltv),
                    backgroundColor: '#71BED2',
                    borderColor: '#71BED2',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Daily Activity Chart
    const dailyCanvas = document.getElementById('leadsDailyChart');
    if (dailyCanvas) {
        destroyChart('leadsDaily');
        const ctx = dailyCanvas.getContext('2d');
        const sortedDates = Object.keys(analysis.byDate).sort();
        allCharts.leadsDaily = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedDates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                datasets: [{
                    label: 'Daily Leads',
                    data: sortedDates.map(d => analysis.byDate[d]),
                    borderColor: '#013160',
                    backgroundColor: 'rgba(1, 49, 96, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
    
    // Day of Week Chart - REMOVED
    // const dayCanvas = document.getElementById('leadsByDayChart');
    
    // Hour of Day Chart - REMOVED  
    // const hourCanvas = document.getElementById('leadsByHourChart');
    
    // Render the heatmap
    renderLeadsHeatmap(leads);
    
    // Render SF location-specific heatmaps
    if (hasConvertedData) {
        const sfLeads = leads.filter(lead => {
            const source = (lead['Lead source'] || '').trim();
            return source.startsWith('SF');
        });
        
        if (sfLeads.length > 0) {
            // Group by location
            const locationMap = {};
            sfLeads.forEach(lead => {
                const location = lead['Home location'] || 'Unknown';
                if (!locationMap[location]) {
                    locationMap[location] = [];
                }
                locationMap[location].push(lead);
            });
            
            // Render heatmap for each location
            Object.keys(locationMap).sort().forEach(location => {
                const containerId = `sfHeatmap-${location.replace(/\s+/g, '-')}`;
                const container = document.getElementById(containerId);
                if (container) {
                    renderLocationHeatmap(locationMap[location], containerId, location);
                }
            });
        }
    }
    
    // Monthly Conversions Chart
    const monthlyConvCanvas = document.getElementById('leadsMonthlyConversionsChart');
    if (monthlyConvCanvas) {
        destroyChart('leadsMonthlyConversions');
        const ctx = monthlyConvCanvas.getContext('2d');
        const sortedMonths = Object.keys(analysis.conversionsByMonth).sort();
        allCharts.leadsMonthlyConversions = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedMonths.map(m => {
                    const [year, month] = m.split('-');
                    return new Date(year, month - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
                }),
                datasets: [{
                    label: 'Conversions',
                    data: sortedMonths.map(m => analysis.conversionsByMonth[m]),
                    backgroundColor: '#28a745',
                    borderColor: '#28a745',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
    
    // Converted To Chart
    if (hasConvertedData && Object.keys(analysis.convertedTo).length > 0) {
        const convertedToCanvas = document.getElementById('leadsConvertedToChart');
        if (convertedToCanvas) {
            destroyChart('leadsConvertedTo');
            const ctx = convertedToCanvas.getContext('2d');
            const sortedTypes = Object.entries(analysis.convertedTo).sort((a, b) => b[1].count - a[1].count);
            allCharts.leadsConvertedTo = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: sortedTypes.map(t => t[0]),
                    datasets: [{
                        data: sortedTypes.map(t => t[1].count),
                        backgroundColor: ['#013160', '#71BED2', '#FBB514', '#28a745', '#dc3545', '#ffc107', '#9c27b0', '#ff5722'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { padding: 10, font: { size: 11 } }
                        }
                    }
                }
            });
        }
        
        // Converted To LTV Chart
        const convertedToLTVCanvas = document.getElementById('leadsConvertedToLTVChart');
        if (convertedToLTVCanvas) {
            destroyChart('leadsConvertedToLTV');
            const ctx = convertedToLTVCanvas.getContext('2d');
            const sortedTypes = Object.entries(analysis.convertedTo).sort((a, b) => b[1].ltv - a[1].ltv);
            allCharts.leadsConvertedToLTV = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sortedTypes.map(t => t[0]),
                    datasets: [{
                        label: 'Total LTV',
                        data: sortedTypes.map(t => t[1].ltv),
                        backgroundColor: '#28a745',
                        borderColor: '#28a745',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}

