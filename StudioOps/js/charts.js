/**
 * Charts Module
 *
 * This module contains all chart rendering functions using Chart.js
 */

import { formatCurrency, formatNumber, parseLTV, parseDate, isIntroOffer, formatStaffName } from './utils.js';
import { filteredAppointments, filteredLeads, filteredMemberships, filteredCancellations, allCharts, filteredTimeTracking, membershipsData, leadsData, appointmentsData } from './data.js';
import { CONFIG, LTV_TIERS } from './config.js';
import * as modals from './modals.js';

// Helper function to calculate trendline
export function calculateTrendline(data) {
    const n = data.length;
    if (n === 0) return [];

    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

    data.forEach((value, index) => {
        sumX += index;
        sumY += value;
        sumXY += index * value;
        sumX2 += index * index;
    });

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return data.map((_, index) => slope * index + intercept);
}

// LTV Distribution Chart (already implemented, keeping it)
export function renderLTVDistributionChart(tier1, tier2, tier3, tier4, tier5, tier6) {
    const ctx = document.getElementById('ltvDistributionChart');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (allCharts['ltvDistribution']) {
        allCharts['ltvDistribution'].destroy();
    }

    // Get current tier configuration
    const currentTierConfig = LTV_TIERS[CONFIG.ltvTiers];
    const ranges = currentTierConfig.ranges;

    // Format labels based on tier ranges
    const labels = [
        \`$1-$\${ranges[0]}\`,
        \`$\${ranges[0]}-$\${ranges[1]}\`,
        \`$\${ranges[1]}-$\${ranges[2] >= 1000 ? (ranges[2] / 1000) + 'K' : ranges[2]}\`,
        \`$\${ranges[2] >= 1000 ? (ranges[2] / 1000) + 'K' : ranges[2]}-$\${ranges[3] >= 1000 ? (ranges[3] / 1000) + 'K' : ranges[3]}\`,
        \`$\${ranges[3] >= 1000 ? (ranges[3] / 1000) + 'K' : ranges[3]}-$\${ranges[4] >= 1000 ? (ranges[4] / 1000) + 'K' : ranges[4]}\`,
        \`$\${ranges[4] >= 1000 ? (ranges[4] / 1000) + 'K' : ranges[4]}+\`
    ];

    const data = {
        labels: labels,
        datasets: [{
            label: 'Number of Customers',
            data: [tier1, tier2, tier3, tier4, tier5, tier6],
            backgroundColor: [
                'rgba(54, 162, 235, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)',
                'rgba(255, 159, 64, 0.8)',
                'rgba(255, 206, 86, 0.8)',
                'rgba(255, 99, 132, 0.8)'
            ],
            borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 2
        }]
    };

    allCharts['ltvDistribution'] = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const range = labels[index];
                    const count = [tier1, tier2, tier3, tier4, tier5, tier6][index];
                    modals.showLTVDetails(range, count);
                }
            },
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Customer Lifetime Value Distribution',
                    font: { size: 16, weight: 'bold' }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return \`\${context.parsed.y} customers\`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// ============================================================================
// CHART RENDERING FUNCTIONS
// ============================================================================

export function formatTime(hour) {
    const h = parseInt(hour);
    if (h === 0) return '12 AM';
    if (h < 12) return `${h} AM`;
    if (h === 12) return '12 PM';
    return `${h - 12} PM`;
}
export function renderMonthlyGoalCharts(appointmentsData, revenueGoal, appointmentsGoal) {
    // Group data by month
    const monthlyData = {};
    const introGoal = CONFIG.goals.monthlyIntroAppointments;
    
    appointmentsData.forEach(row => {
        const date = parseDate(row['Appointment Date']);
        if (date) {
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            if (!monthlyData[monthKey]) {
                monthlyData[monthKey] = {
                    revenue: 0,
                    appointments: 0,
                    introAppointments: 0
                };
            }
            monthlyData[monthKey].revenue += parseFloat(row.Revenue) || 0;
            
            // Only count paid (non-intro) appointments toward the appointments goal
            if (isIntroOffer(row['Appointment'])) {
                monthlyData[monthKey].introAppointments++;
            } else {
                monthlyData[monthKey].appointments++;
            }
        }
    });
    
    const sortedMonths = Object.keys(monthlyData).sort();
    const monthLabels = sortedMonths.map(month => {
        const [year, mon] = month.split('-');
        const date = new Date(year, mon - 1);
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    });
    
    // Revenue Goal Chart
    const revenueCanvas = document.getElementById('monthlyRevenueGoalChart');
    if (revenueCanvas) {
        destroyChart('monthlyRevenueGoal');
        const ctx = revenueCanvas.getContext('2d');
        
        allCharts.monthlyRevenueGoal = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: 'Actual Revenue',
                        data: sortedMonths.map(m => monthlyData[m].revenue),
                        backgroundColor: '#71BED2',
                        borderColor: '#5aa8bf',
                        borderWidth: 2
                    },
                    {
                        label: 'Goal',
                        data: sortedMonths.map(() => revenueGoal),
                        backgroundColor: 'rgba(251, 181, 20, 0.3)',
                        borderColor: '#FBB514',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        type: 'line',
                        fill: false
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
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
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
    
    // Appointments Goal Chart
    const appointmentsCanvas = document.getElementById('monthlyAppointmentsGoalChart');
    if (appointmentsCanvas) {
        destroyChart('monthlyAppointmentsGoal');
        const ctx = appointmentsCanvas.getContext('2d');
        
        allCharts.monthlyAppointmentsGoal = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: 'Actual Paid Appointments',
                        data: sortedMonths.map(m => monthlyData[m].appointments),
                        backgroundColor: '#013160',
                        borderColor: '#001a3a',
                        borderWidth: 2
                    },
                    {
                        label: 'Goal',
                        data: sortedMonths.map(() => appointmentsGoal),
                        backgroundColor: 'rgba(251, 181, 20, 0.3)',
                        borderColor: '#FBB514',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        type: 'line',
                        fill: false
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
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatNumber(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 10
                        }
                    }
                }
            }
        });
    }
    
    // Intro Appointments Goal Chart
    const introCanvas = document.getElementById('monthlyIntroGoalChart');
    if (introCanvas) {
        destroyChart('monthlyIntroGoal');
        const ctx = introCanvas.getContext('2d');
        
        allCharts.monthlyIntroGoal = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: 'Actual Intro Appointments',
                        data: sortedMonths.map(m => monthlyData[m].introAppointments),
                        backgroundColor: '#FBB514',
                        borderColor: '#e5a313',
                        borderWidth: 2
                    },
                    {
                        label: 'Goal',
                        data: sortedMonths.map(() => introGoal),
                        backgroundColor: 'rgba(1, 49, 96, 0.3)',
                        borderColor: '#013160',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        type: 'line',
                        fill: false
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
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatNumber(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 5
                        }
                    }
                }
            }
        });
    }
}

// PERIOD COMPARISON FUNCTIONS
let comparisonData = null;

export function toggleComparison() {
    const comparisonType = document.getElementById('comparisonPeriod').value;
    if (comparisonType !== 'none') {
        calculateComparisonData();
    } else {
        comparisonData = null;
    }
    renderAllTabs();
}

export function renderRevenueByLocationChart() {
    const canvas = document.getElementById('revenueByLocationChart');
    if (!canvas) return;
    
    destroyChart('revenueByLocation');
    
    const revenueByLocation = {};
    filteredAppointments.forEach(row => {
        const location = row.Location || 'Unknown';
        revenueByLocation[location] = (revenueByLocation[location] || 0) + parseFloat(row.Revenue || 0);
    });
    
    const ctx = canvas.getContext('2d');
    allCharts.revenueByLocation = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(revenueByLocation),
            datasets: [{
                label: 'Revenue',
                data: Object.values(revenueByLocation),
                backgroundColor: '#71BED2',
                borderColor: '#013160',
                borderWidth: 2
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

export function renderRevenueByServiceChart() {
    const canvas = document.getElementById('revenueByServiceChart');
    if (!canvas) return;
    
    destroyChart('revenueByService');
    
    const revenueByService = {};
    filteredAppointments.forEach(row => {
        const service = row['Appointment'] || 'Unknown';
        revenueByService[service] = (revenueByService[service] || 0) + parseFloat(row.Revenue || 0);
    });
    
    // Filter out services with $0 revenue
    const filteredServices = Object.entries(revenueByService)
        .filter(([service, revenue]) => revenue > 0)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8);
    
    const ctx = canvas.getContext('2d');
    allCharts.revenueByService = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: filteredServices.map(s => s[0].substring(0, 25)),
            datasets: [{
                label: 'Revenue',
                data: filteredServices.map(s => s[1]),
                backgroundColor: '#013160',
                borderColor: '#71BED2',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const serviceName = filteredServices[index][0];
                    showServiceDetails(serviceName);
                }
            },
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

export function renderIntroSessionsChart() {
    const canvas = document.getElementById('introSessionsChart');
    if (!canvas) return;
    
    destroyChart('introSessions');
    
    const introCount = filteredAppointments.filter(row => 
        isIntroOffer(row['Appointment'])
    ).length;
    const regularCount = filteredAppointments.length - introCount;
    
    const ctx = canvas.getContext('2d');
    allCharts.introSessions = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Intro Offers', 'Regular Sessions'],
            datasets: [{
                data: [introCount, regularCount],
                backgroundColor: ['#FBB514', '#013160'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

export function renderPaymentMethodsChart() {
    const canvas = document.getElementById('paymentMethodsChart');
    if (!canvas) return;
    
    destroyChart('paymentMethods');
    
    const paymentMethods = {};
    filteredAppointments.forEach(row => {
        const method = row['Payment Methods'] || 'Unknown';
        paymentMethods[method] = (paymentMethods[method] || 0) + 1;
    });
    
    const ctx = canvas.getContext('2d');
    allCharts.paymentMethods = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(paymentMethods),
            datasets: [{
                data: Object.values(paymentMethods),
                backgroundColor: ['#013160', '#71BED2', '#FBB514', '#28a745', '#dc3545'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

export function renderHeatmap() {
    const container = document.getElementById('heatmapContainer');
    if (!container) return;
    
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    // Group appointments by location
    const locationData = {};
    filteredAppointments.forEach(row => {
        const location = row.Location || 'Unknown';
        if (!locationData[location]) {
            locationData[location] = {};
            days.forEach(day => {
                locationData[location][day] = {};
                for (let hour = 6; hour <= 21; hour++) {
                    locationData[location][day][hour] = 0;
                }
            });
        }
        
        const date = parseDate(row['Appointment Date']);
        const dayIndex = date.getDay();
        
        // Skip Sunday (0)
        if (dayIndex === 0) return;
        
        // Map day index to day name (1=Monday, 6=Saturday)
        const dayName = days[dayIndex - 1];
        const hour = date.getHours();
        
        if (locationData[location][dayName] && locationData[location][dayName][hour] !== undefined) {
            locationData[location][dayName][hour]++;
        }
    });
    
    // Sort locations alphabetically
    const locations = Object.keys(locationData).sort();
    
    // Render a heatmap for each location
    let html = '';
    locations.forEach((location, index) => {
        const heatmapData = locationData[location];
        
        // Find max value for this location
        let maxValue = 0;
        Object.values(heatmapData).forEach(dayData => {
            Object.values(dayData).forEach(count => {
                if (count > maxValue) maxValue = count;
            });
        });
        
        // Add location header
        html += `<div style="margin-top: ${index > 0 ? '30px' : '0'}; padding: 20px; background: ${index % 2 === 0 ? '#f8f9fa' : 'white'}; border-radius: 10px;">`;
        html += `<h3 style="margin-bottom: 15px; color: var(--primary);">${location}</h3>`;
        
        // Render table
        html += '<table class="heatmap-table"><thead><tr><th>Day</th>';
        for (let hour = 6; hour <= 21; hour++) {
            const displayHour = hour > 12 ? `${hour - 12}p` : (hour === 12 ? '12p' : `${hour}a`);
            html += `<th>${displayHour}</th>`;
        }
        html += '</tr></thead><tbody>';
        
        days.forEach(day => {
            html += `<tr><td onclick="showDayOfWeekDetails('${day}', '${location}')" style="cursor: pointer; font-weight: 500;">${day}</td>`;
            for (let hour = 6; hour <= 21; hour++) {
                const count = heatmapData[day][hour];
                const intensity = maxValue > 0 ? Math.ceil((count / maxValue) * 7) : 0;
                html += `<td class="heatmap-cell heatmap-${intensity}" 
                    title="${location} - ${day} ${hour}:00 - ${count} appointments" 
                    onclick="showHourDetails('${day}', ${hour}, '${location}')" 
                    style="cursor: pointer;">${count}</td>`;
            }
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        html += '</div>';
    });
    
    html += '<p style="margin-top: 15px; color: #666; font-size: 14px;"><strong>Tip:</strong> Click on a <strong>day name</strong> to see hourly breakdown. Click on an <strong>hour cell</strong> to see specific appointments.</p>';
    
    container.innerHTML = html;
}

export function renderCustomerTypesChart(customers, leads) {
    const canvas = document.getElementById('customerTypesChart');
    if (!canvas) return;
    
    destroyChart('customerTypes');
    
    const ctx = canvas.getContext('2d');
    allCharts.customerTypes = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Customers', 'Leads'],
            datasets: [{
                data: [customers, leads],
                backgroundColor: ['#013160', '#71BED2'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

export function renderVisitFrequencyChart(visitDist) {
    const canvas = document.getElementById('visitFrequencyChart');
    if (!canvas) return;
    
    destroyChart('visitFrequency');
    
    const ctx = canvas.getContext('2d');
    allCharts.visitFrequency = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(visitDist),
            datasets: [{
                label: 'Clients',
                data: Object.values(visitDist),
                backgroundColor: ['#dc3545', '#ffc107', '#71BED2', '#013160', '#28a745']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const labels = Object.keys(visitDist);
                    const values = Object.values(visitDist);
                    showVisitFrequencyDetails(labels[index], values[index]);
                }
            },
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

export function renderRetentionBreakdownChart(oneTime, returning) {
    const canvas = document.getElementById('retentionBreakdownChart');
    if (!canvas) return;
    
    destroyChart('retentionBreakdown');
    
    const ctx = canvas.getContext('2d');
    allCharts.retentionBreakdown = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['One-Time Visitors', 'Returning Clients'],
            datasets: [{
                data: [oneTime, returning],
                backgroundColor: ['#dc3545', '#28a745'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const labels = ['One-Time Visitors', 'Returning Clients'];
                    const values = [oneTime, returning];
                    showRetentionDetails(labels[index], values[index]);
                }
            },
            plugins: { 
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = oneTime + returning;
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${formatNumber(context.parsed)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

export function renderPractitionerCharts(practitionerData) {
    // Revenue chart
    const revenueCanvas = document.getElementById('practitionerRevenueChart');
    if (revenueCanvas) {
        destroyChart('practitionerRevenue');
        
        const sorted = Object.entries(practitionerData)
            .sort((a, b) => b[1].revenue - a[1].revenue);
        
        const ctx = revenueCanvas.getContext('2d');
        allCharts.practitionerRevenue = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sorted.map(p => p[0]),
                datasets: [{
                    label: 'Revenue',
                    data: sorted.map(p => p[1].revenue),
                    backgroundColor: '#FBB514',
                    borderColor: '#013160',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const practitionerName = sorted[index][0];
                        showPractitionerDetails(practitionerName);
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
    
    // Appointments chart
    const apptsCanvas = document.getElementById('practitionerApptsChart');
    if (apptsCanvas) {
        destroyChart('practitionerAppts');
        
        const sorted = Object.entries(practitionerData)
            .sort((a, b) => b[1].appointments - a[1].appointments);
        
        const ctx = apptsCanvas.getContext('2d');
        allCharts.practitionerAppts = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sorted.map(p => p[0]),
                datasets: [{
                    label: 'Appointments',
                    data: sorted.map(p => p[1].appointments),
                    backgroundColor: '#71BED2',
                    borderColor: '#013160',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const practitionerName = sorted[index][0];
                        showPractitionerDetails(practitionerName);
                    }
                },
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } }
            }
        });
    }
}

export function renderTimelineCharts(dailyData, dates) {
    // Fees timeline chart (stacked)
    const feesCanvas = document.getElementById('feesTimelineChart');
    if (feesCanvas) {
        destroyChart('feesTimeline');
        
        const ctx = feesCanvas.getContext('2d');
        const franchiseFees = dates.map(date => dailyData[date].revenue * CONFIG.franchiseFeePercent / 100);
        const brandFunds = dates.map(date => dailyData[date].revenue * CONFIG.brandFundPercent / 100);
        const ccFees = dates.map(date => dailyData[date].revenue * CONFIG.ccFeesPercent / 100);
        
        allCharts.feesTimeline = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Franchise Fee',
                        data: franchiseFees,
                        backgroundColor: 'rgba(1, 49, 96, 0.8)',
                        borderColor: 'rgba(1, 49, 96, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Brand Fund',
                        data: brandFunds,
                        backgroundColor: 'rgba(113, 190, 210, 0.8)',
                        borderColor: 'rgba(113, 190, 210, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'CC Processing',
                        data: ccFees,
                        backgroundColor: 'rgba(251, 181, 20, 0.8)',
                        borderColor: 'rgba(251, 181, 20, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                },
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Daily revenue chart
    const revenueCanvas = document.getElementById('dailyRevenueChart');
    if (revenueCanvas) {
        destroyChart('dailyRevenue');
        
        const ctx = revenueCanvas.getContext('2d');
        const revenueData = dates.map(date => dailyData[date].revenue);
        const trendlineData = calculateTrendline(revenueData);
        
        allCharts.dailyRevenue = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Daily Revenue',
                        data: revenueData,
                        borderColor: '#71BED2',
                        backgroundColor: 'rgba(113, 190, 210, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        order: 1
                    },
                    {
                        label: 'Trend',
                        data: trendlineData,
                        borderColor: 'rgba(113, 190, 210, 0.7)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 2
                    }
                ]
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
    
    // Cumulative revenue chart
    const cumulativeCanvas = document.getElementById('cumulativeRevenueChart');
    if (cumulativeCanvas) {
        destroyChart('cumulativeRevenue');
        
        let cumulative = 0;
        const cumulativeData = dates.map(date => {
            cumulative += dailyData[date].revenue;
            return cumulative;
        });
        
        const cumulativeTrendline = calculateTrendline(cumulativeData);
        
        const ctx = cumulativeCanvas.getContext('2d');
        allCharts.cumulativeRevenue = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Cumulative Revenue',
                        data: cumulativeData,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        order: 1
                    },
                    {
                        label: 'Trend',
                        data: cumulativeTrendline,
                        borderColor: 'rgba(40, 167, 69, 0.7)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 2
                    }
                ]
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
    
    // Daily appointments chart
    const apptsCanvas = document.getElementById('dailyAppointmentsChart');
    if (apptsCanvas) {
        destroyChart('dailyAppointments');
        
        const ctx = apptsCanvas.getContext('2d');
        const apptsData = dates.map(date => dailyData[date].appointments);
        const apptsTrendline = calculateTrendline(apptsData);
        
        allCharts.dailyAppointments = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Daily Appointments',
                        data: apptsData,
                        borderColor: '#013160',
                        backgroundColor: 'rgba(1, 49, 96, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        order: 1
                    },
                    {
                        label: 'Trend',
                        data: apptsTrendline,
                        borderColor: 'rgba(1, 49, 96, 0.7)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 2
                    }
                ]
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
    
    // Daily profit chart
    const profitCanvas = document.getElementById('dailyProfitChart');
    if (profitCanvas) {
        destroyChart('dailyProfit');
        
        const ctx = profitCanvas.getContext('2d');
        const profitData = dates.map(date => dailyData[date].profit);
        const profitTrendline = calculateTrendline(profitData);
        
        allCharts.dailyProfit = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Daily Profit',
                        data: profitData,
                        borderColor: '#FBB514',
                        backgroundColor: 'rgba(251, 181, 20, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        order: 1
                    },
                    {
                        label: 'Trend',
                        data: profitTrendline,
                        borderColor: 'rgba(251, 181, 20, 0.7)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 2
                    }
                ]
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
    
    // Daily revenue per appointment chart
    const revenuePerApptCanvas = document.getElementById('dailyRevenuePerApptChart');
    if (revenuePerApptCanvas) {
        destroyChart('dailyRevenuePerAppt');
        
        const ctx = revenuePerApptCanvas.getContext('2d');
        const revenuePerApptData = dates.map(date => {
            return dailyData[date].appointments > 0 
                ? dailyData[date].revenue / dailyData[date].appointments 
                : 0;
        });
        const revenuePerApptTrendline = calculateTrendline(revenuePerApptData);
        
        allCharts.dailyRevenuePerAppt = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Revenue per Appointment',
                        data: revenuePerApptData,
                        borderColor: '#9c27b0',
                        backgroundColor: 'rgba(156, 39, 176, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        order: 1
                    },
                    {
                        label: 'Trend',
                        data: revenuePerApptTrendline,
                        borderColor: 'rgba(156, 39, 176, 0.7)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 2
                    }
                ]
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
    
    // Daily hours chart
    const hoursCanvas = document.getElementById('dailyHoursChart');
    if (hoursCanvas) {
        destroyChart('dailyHours');
        
        const ctx = hoursCanvas.getContext('2d');
        const hoursData = dates.map(date => dailyData[date].hours);
        const hoursTrendline = calculateTrendline(hoursData);
        
        allCharts.dailyHours = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Daily Hours',
                        data: hoursData,
                        borderColor: '#ff6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        order: 1
                    },
                    {
                        label: 'Trend',
                        data: hoursTrendline,
                        borderColor: 'rgba(255, 99, 132, 0.7)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 2
                    }
                ]
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
                                return value.toFixed(1) + ' hrs';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Daily utilization chart
    const utilizationCanvas = document.getElementById('dailyUtilizationChart');
    if (utilizationCanvas) {
        destroyChart('dailyUtilization');
        
        const ctx = utilizationCanvas.getContext('2d');
        const utilizationData = dates.map(date => dailyData[date].utilization);
        const utilizationTrendline = calculateTrendline(utilizationData.map(v => v || 0));
        
        allCharts.dailyUtilization = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Daily Utilization %',
                        data: utilizationData,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        spanGaps: true,
                        order: 1
                    },
                    {
                        label: 'Trend',
                        data: utilizationTrendline,
                        borderColor: 'rgba(40, 167, 69, 0.7)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        order: 2
                    }
                ]
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
                            callback: function(value) {
                                return value.toFixed(0) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // New vs Returning clients chart
    const clientTypeCanvas = document.getElementById('dailyClientTypeChart');
    if (clientTypeCanvas) {
        destroyChart('dailyClientType');
        
        const ctx = clientTypeCanvas.getContext('2d');
        allCharts.dailyClientType = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'New Clients',
                        data: dates.map(date => dailyData[date].newClients.size),
                        backgroundColor: '#28a745',
                        borderColor: '#218838',
                        borderWidth: 1
                    },
                    {
                        label: 'Returning Clients',
                        data: dates.map(date => dailyData[date].returningClients.size),
                        backgroundColor: '#71BED2',
                        borderColor: '#5aa8bf',
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
}

// Render membership charts in timeline tab
export function renderMembershipTimelineCharts() {
    // Only render if memberships data is available
    if (!filteredMemberships || filteredMemberships.length === 0) {
        return;
    }
    
    // Weekly Sales Trend Chart
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
    
    // Average Sale Value Over Time Chart
    const avgValueCanvas = document.getElementById('membershipAvgValueChart');
    if (avgValueCanvas) {
        destroyChart('membershipAvgValue');
        const ctx = avgValueCanvas.getContext('2d');
        
        // Group by week to calculate averages
        const weeklyRevenue = {};
        filteredMemberships.forEach(m => {
            const boughtDate = m['Bought Date/Time (GMT)'] ? new Date(m['Bought Date/Time (GMT)']) : null;
            if (boughtDate) {
                const year = boughtDate.getFullYear();
                const week = Math.ceil((boughtDate - new Date(year, 0, 1)) / (7 * 24 * 60 * 60 * 1000));
                const weekKey = `${year}-W${String(week).padStart(2, '0')}`;
                if (!weeklyRevenue[weekKey]) {
                    weeklyRevenue[weekKey] = [];
                }
                weeklyRevenue[weekKey].push(parseFloat(m['Paid Amount']) || 0);
            }
        });
        
        const sortedWeeks = Object.keys(weeklyRevenue).sort();
        
        // Calculate average value per week
        const weeklyAvg = {};
        sortedWeeks.forEach(week => {
            const values = weeklyRevenue[week];
            if (values.length > 0) {
                weeklyAvg[week] = values.reduce((sum, v) => sum + v, 0) / values.length;
            } else {
                weeklyAvg[week] = 0;
            }
        });
        
        allCharts.membershipAvgValue = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedWeeks,
                datasets: [{
                    label: 'Average Membership Sale Value (Weekly Average)',
                    data: sortedWeeks.map(w => weeklyAvg[w]),
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
                plugins: { 
                    legend: { 
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Note: Values represent weekly averages',
                        font: {
                            size: 10,
                            style: 'italic'
                        },
                        color: '#666',
                        padding: {
                            top: 5,
                            bottom: 10
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
}

// Render leads timeline charts with location breakdown and click handlers
export function renderLeadsTimelineCharts() {
    if (!filteredLeadsConverted || filteredLeadsConverted.length === 0) return;
    
    // Group leads by date
    const leadsByDate = {};
    const leadsByLocationAndDate = {};
    const locations = new Set();
    
    filteredLeadsConverted.forEach(lead => {
        const convertedDate = parseDate(lead['Converted']);
        if (!convertedDate) return;
        
        const dateKey = convertedDate.toISOString().split('T')[0];
        const location = lead['Home location'] || 'Unknown';
        
        locations.add(location);
        
        // Total leads by date
        if (!leadsByDate[dateKey]) {
            leadsByDate[dateKey] = { count: 0, leads: [] };
        }
        leadsByDate[dateKey].count++;
        leadsByDate[dateKey].leads.push(lead);
        
        // Leads by location and date
        if (!leadsByLocationAndDate[location]) {
            leadsByLocationAndDate[location] = {};
        }
        if (!leadsByLocationAndDate[location][dateKey]) {
            leadsByLocationAndDate[location][dateKey] = { count: 0, leads: [] };
        }
        leadsByLocationAndDate[location][dateKey].count++;
        leadsByLocationAndDate[location][dateKey].leads.push(lead);
    });
    
    const sortedDates = Object.keys(leadsByDate).sort();
    const locationsArray = Array.from(locations).sort();
    
    // Store data globally for click handlers
    window.leadsTimelineData = { leadsByDate, leadsByLocationAndDate, sortedDates, locations: locationsArray };
    
    // Chart 1: All leads over time
    const allCanvas = document.getElementById('leadsTimelineAllChart');
    if (allCanvas) {
        destroyChart('leadsTimelineAll');
        const ctx = allCanvas.getContext('2d');
        allCharts.leadsTimelineAll = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedDates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                datasets: [{
                    label: 'Daily Leads',
                    data: sortedDates.map(d => leadsByDate[d].count),
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
                        const date = sortedDates[index];
                        showLeadsTimelineDetails(date, leadsByDate[date].leads, 'All Locations');
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${formatNumber(context.parsed.y)} leads`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
    
    // Chart 2: Stacked by location
    const stackedCanvas = document.getElementById('leadsTimelineLocationStackedChart');
    if (stackedCanvas) {
        destroyChart('leadsTimelineLocationStacked');
        const ctx = stackedCanvas.getContext('2d');
        
        const colors = ['#013160', '#71BED2', '#FBB514', '#28a745', '#dc3545', '#ffc107', '#9c27b0', '#ff5722'];
        
        const datasets = locationsArray.map((location, i) => ({
            label: location,
            data: sortedDates.map(d => leadsByLocationAndDate[location][d]?.count || 0),
            backgroundColor: colors[i % colors.length],
            borderColor: colors[i % colors.length],
            borderWidth: 1
        }));
        
        allCharts.leadsTimelineLocationStacked = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedDates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const datasetIndex = elements[0].datasetIndex;
                        const date = sortedDates[index];
                        const location = locationsArray[datasetIndex];
                        const leads = leadsByLocationAndDate[location][date]?.leads || [];
                        showLeadsTimelineDetails(date, leads, location);
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
    
    // Chart 3: Individual charts for each location - REMOVED
    /*
    let locationChartsHTML = '';
    locationsArray.forEach((location, i) => {
        locationChartsHTML += `
            <div class="chart-container full-width">
                <div class="interactive-badge" title="Click on any bar to see lead details"></div>
                <h3>Daily Leads: ${location}</h3>
                <div class="chart-wrapper">
                    <canvas id="leadsTimelineLocation${i}Chart"></canvas>
                </div>
            </div>
        `;
    });
    document.getElementById('leadsTimelineByLocation').innerHTML = locationChartsHTML;
    
    // Render individual location charts
    locationsArray.forEach((location, i) => {
        const canvas = document.getElementById(`leadsTimelineLocation${i}Chart`);
        if (canvas) {
            const chartKey = `leadsTimelineLocation${i}`;
            destroyChart(chartKey);
            const ctx = canvas.getContext('2d');
            
            const colors = ['#013160', '#71BED2', '#FBB514', '#28a745', '#dc3545', '#ffc107', '#9c27b0', '#ff5722'];
            
            allCharts[chartKey] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sortedDates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                    datasets: [{
                        label: 'Daily Leads',
                        data: sortedDates.map(d => leadsByLocationAndDate[location][d]?.count || 0),
                        backgroundColor: colors[i % colors.length],
                        borderColor: colors[i % colors.length],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const date = sortedDates[index];
                            const leads = leadsByLocationAndDate[location][date]?.leads || [];
                            showLeadsTimelineDetails(date, leads, location);
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    },
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
    */
}

// Show lead details when clicking on timeline chart
export function renderLeadsHeatmap(leads) {
    const heatmapContainer = document.getElementById('leadsHeatmap');
    if (!heatmapContainer) return;
    
    // Build data structure: day -> hour -> leads array
    const heatmapData = {};
    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    dayOrder.forEach(day => {
        heatmapData[day] = {};
        for (let hour = 0; hour < 24; hour++) {
            heatmapData[day][hour] = [];
        }
    });
    
    // Populate the heatmap data
    leads.forEach(lead => {
        let dateField = null;
        const hasConvertedData = lead['Lead source'] !== undefined;
        
        if (hasConvertedData) {
            dateField = parseDate(lead['Converted']);
        } else {
            dateField = parseDate(lead['Join date']);
        }
        
        if (!dateField) return;
        
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = dayNames[dateField.getDay()];
        const hour = dateField.getHours();
        
        // Only include Monday-Saturday
        if (dayOrder.includes(dayOfWeek)) {
            heatmapData[dayOfWeek][hour].push(lead);
        }
    });
    
    // Find max count for color scaling
    let maxCount = 0;
    dayOrder.forEach(day => {
        for (let hour = 0; hour < 24; hour++) {
            const count = heatmapData[day][hour].length;
            if (count > maxCount) maxCount = count;
        }
    });
    
    // Generate heatmap HTML
    let html = '<table style="border-collapse: collapse; margin: 0 auto; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">';
    
    // Header row with hours
    html += '<tr><th style="padding: 10px; border: 1px solid #ddd; background: #013160; color: white; font-weight: bold;">Day \\ Hour</th>';
    for (let hour = 0; hour < 24; hour++) {
        html += `<th style="padding: 8px; border: 1px solid #ddd; background: #013160; color: white; font-size: 11px; min-width: 35px;">${formatTime(hour)}</th>`;
    }
    html += '</tr>';
    
    // Data rows
    dayOrder.forEach(day => {
        html += '<tr>';
        html += `<td style="padding: 10px; border: 1px solid #ddd; background: #f5f5f5; font-weight: bold; color: #013160;">${day}</td>`;
        
        for (let hour = 0; hour < 24; hour++) {
            const count = heatmapData[day][hour].length;
            const intensity = maxCount > 0 ? count / maxCount : 0;
            
            // Color scale from white to dark blue
            let bgColor;
            if (count === 0) {
                bgColor = '#ffffff';
            } else {
                const r = Math.floor(255 - (intensity * 242)); // 255 -> 13
                const g = Math.floor(255 - (intensity * 206)); // 255 -> 49
                const b = Math.floor(255 - (intensity * 159)); // 255 -> 96
                bgColor = `rgb(${r}, ${g}, ${b})`;
            }
            
            const textColor = intensity > 0.5 ? 'white' : '#333';
            const cursor = count > 0 ? 'pointer' : 'default';
            const dataAttr = count > 0 ? `data-day="${day}" data-hour="${hour}"` : '';
            
            html += `<td ${dataAttr} style="padding: 12px; border: 1px solid #ddd; background: ${bgColor}; color: ${textColor}; text-align: center; font-weight: ${count > 0 ? 'bold' : 'normal'}; cursor: ${cursor}; transition: all 0.2s;" 
                    onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)'; this.style.zIndex='10';" 
                    onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none'; this.style.zIndex='1';"
                    ${count > 0 ? `onclick="showHeatmapDetails('${day}', ${hour})"` : ''}>
                ${count > 0 ? count : ''}
            </td>`;
        }
        
        html += '</tr>';
    });
    
    html += '</table>';
    heatmapContainer.innerHTML = html;
    
    // Store heatmap data globally for click handlers
    window.leadsHeatmapData = heatmapData;
}

// Render location-specific heatmap for SF leads
export function renderLocationHeatmap(leads, containerId, locationName) {
    const heatmapContainer = document.getElementById(containerId);
    if (!heatmapContainer) return;
    
    // Build data structure: day -> hour -> leads array
    const heatmapData = {};
    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    dayOrder.forEach(day => {
        heatmapData[day] = {};
        for (let hour = 0; hour < 24; hour++) {
            heatmapData[day][hour] = [];
        }
    });
    
    // Populate the heatmap data
    leads.forEach(lead => {
        const dateField = parseDate(lead['Converted']);
        if (!dateField) return;
        
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = dayNames[dateField.getDay()];
        const hour = dateField.getHours();
        
        // Only include Monday-Saturday
        if (dayOrder.includes(dayOfWeek)) {
            heatmapData[dayOfWeek][hour].push(lead);
        }
    });
    
    // Find max count for color scaling
    let maxCount = 0;
    dayOrder.forEach(day => {
        for (let hour = 0; hour < 24; hour++) {
            const count = heatmapData[day][hour].length;
            if (count > maxCount) maxCount = count;
        }
    });
    
    // Generate heatmap HTML
    let html = '<table style="border-collapse: collapse; margin: 0 auto; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">';
    
    // Header row with hours
    html += '<tr><th style="padding: 10px; border: 1px solid #ddd; background: #013160; color: white; font-weight: bold;">Day \\ Hour</th>';
    for (let hour = 0; hour < 24; hour++) {
        html += `<th style="padding: 8px; border: 1px solid #ddd; background: #013160; color: white; font-size: 11px; min-width: 35px;">${formatTime(hour)}</th>`;
    }
    html += '</tr>';
    
    // Data rows
    dayOrder.forEach(day => {
        html += '<tr>';
        html += `<td style="padding: 10px; border: 1px solid #ddd; background: #f5f5f5; font-weight: bold; color: #013160;">${day}</td>`;
        
        for (let hour = 0; hour < 24; hour++) {
            const count = heatmapData[day][hour].length;
            const intensity = maxCount > 0 ? count / maxCount : 0;
            
            // Color scale from white to orange (SocialFitness branding)
            let bgColor;
            if (count === 0) {
                bgColor = '#ffffff';
            } else {
                const r = Math.floor(255 - (intensity * 4)); // 255 -> 251
                const g = Math.floor(255 - (intensity * 74)); // 255 -> 181
                const b = Math.floor(255 - (intensity * 235)); // 255 -> 20
                bgColor = `rgb(${r}, ${g}, ${b})`;
            }
            
            const textColor = intensity > 0.5 ? 'white' : '#333';
            const cursor = count > 0 ? 'pointer' : 'default';
            const dataAttr = count > 0 ? `data-day="${day}" data-hour="${hour}" data-location="${locationName}"` : '';
            
            html += `<td ${dataAttr} style="padding: 12px; border: 1px solid #ddd; background: ${bgColor}; color: ${textColor}; text-align: center; font-weight: ${count > 0 ? 'bold' : 'normal'}; cursor: ${cursor}; transition: all 0.2s;" 
                    onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)'; this.style.zIndex='10';" 
                    onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none'; this.style.zIndex='1';"
                    ${count > 0 ? `onclick="showLocationHeatmapDetails('${locationName}', '${day}', ${hour})"` : ''}>
                ${count > 0 ? count : ''}
            </td>`;
        }
        
        html += '</tr>';
    });
    
    html += '</table>';
    heatmapContainer.innerHTML = html;
    
    // Store heatmap data globally for click handlers
    if (!window.sfHeatmapData) window.sfHeatmapData = {};
    window.sfHeatmapData[locationName] = heatmapData;
}

export function renderAppointmentHeatmap(appointments, containerId, locationName) {
    const heatmapContainer = document.getElementById(containerId);
    if (!heatmapContainer) return;
    
    // Build data structure: day -> hour -> appointments array
    const heatmapData = {};
    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    dayOrder.forEach(day => {
        heatmapData[day] = {};
        for (let hour = 0; hour < 24; hour++) {
            heatmapData[day][hour] = [];
        }
    });
    
    // Populate the heatmap data
    appointments.forEach(appt => {
        const dateField = parseDate(appt['Appointment Date']);
        if (!dateField) return;
        
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = dayNames[dateField.getDay()];
        const hour = dateField.getHours();
        
        // Only include Monday-Saturday
        if (dayOrder.includes(dayOfWeek)) {
            heatmapData[dayOfWeek][hour].push(appt);
        }
    });
    
    // Find max count for color scaling
    let maxCount = 0;
    dayOrder.forEach(day => {
        for (let hour = 0; hour < 24; hour++) {
            const count = heatmapData[day][hour].length;
            if (count > maxCount) maxCount = count;
        }
    });
    
    // Generate heatmap HTML
    let html = '<table style="border-collapse: collapse; margin: 0 auto; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">';
    
    // Header row with hours
    html += '<tr><th style="padding: 10px; border: 1px solid #ddd; background: #013160; color: white; font-weight: bold;">Day \\ Hour</th>';
    for (let hour = 0; hour < 24; hour++) {
        html += `<th style="padding: 8px; border: 1px solid #ddd; background: #013160; color: white; font-size: 11px; min-width: 35px;">${formatTime(hour)}</th>`;
    }
    html += '</tr>';
    
    // Data rows
    dayOrder.forEach(day => {
        html += '<tr>';
        html += `<td style="padding: 10px; border: 1px solid #ddd; background: #f5f5f5; font-weight: bold; color: #013160;">${day}</td>`;
        
        for (let hour = 0; hour < 24; hour++) {
            const count = heatmapData[day][hour].length;
            const intensity = maxCount > 0 ? count / maxCount : 0;
            
            // Color scale from white to accent blue
            let bgColor;
            if (count === 0) {
                bgColor = '#ffffff';
            } else {
                const r = Math.floor(255 - (intensity * 142)); // 255 -> 113
                const g = Math.floor(255 - (intensity * 65));  // 255 -> 190
                const b = Math.floor(255 - (intensity * 45));  // 255 -> 210
                bgColor = `rgb(${r}, ${g}, ${b})`;
            }
            
            const textColor = intensity > 0.5 ? 'white' : '#333';
            const cursor = count > 0 ? 'pointer' : 'default';
            const dataAttr = count > 0 ? `data-day="${day}" data-hour="${hour}" data-location="${locationName}"` : '';
            
            html += `<td ${dataAttr} style="padding: 12px; border: 1px solid #ddd; background: ${bgColor}; color: ${textColor}; text-align: center; font-weight: ${count > 0 ? 'bold' : 'normal'}; cursor: ${cursor}; transition: all 0.2s;" 
                    onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)'; this.style.zIndex='10';" 
                    onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none'; this.style.zIndex='1';"
                    ${count > 0 ? `onclick="showApptHeatmapDetails('${locationName}', '${day}', ${hour})"` : ''}>
                ${count > 0 ? count : ''}
            </td>`;
        }
        
        html += '</tr>';
    });
    
    html += '</table>';
    heatmapContainer.innerHTML = html;
    
    // Store heatmap data globally for click handlers
    if (!window.apptHeatmapData) window.apptHeatmapData = {};
    window.apptHeatmapData[locationName] = heatmapData;
}

