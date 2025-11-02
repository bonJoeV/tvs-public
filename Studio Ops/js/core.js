// The Vital Stretch Dashboard - Core Functionality

// Global State
let rawData = [];
let filteredData = [];
let allCharts = {};

// Number Formatting Helpers
function formatNumber(num) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function formatCurrency(num) {
    return CONFIG.settings.currencySymbol + formatNumber(num);
}

// Initialize Dashboard
function initDashboard() {
    console.log('Initializing The Vital Stretch Dashboard...');
    
    // Initialize settings panel
    initSettingsPanel();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load enabled features
    loadEnabledFeatures();
    
    console.log('Dashboard initialized successfully');
}

// Initialize Settings Panel
function initSettingsPanel() {
    const panel = document.getElementById('settingsPanel');
    if (!panel) return;
    
    let html = '<h2>Dashboard Features</h2>';
    
    // Group features by category
    const featuresByCategory = {};
    Object.keys(CONFIG.features).forEach(key => {
        const info = CONFIG.featureInfo[key];
        if (!info) return;
        
        if (!featuresByCategory[info.category]) {
            featuresByCategory[info.category] = [];
        }
        featuresByCategory[info.category].push({
            key,
            ...info,
            enabled: CONFIG.features[key]
        });
    });
    
    // Render features by category
    Object.entries(FEATURE_CATEGORIES).forEach(([catKey, catName]) => {
        if (featuresByCategory[catKey] && featuresByCategory[catKey].length > 0) {
            html += `<div class="settings-group"><h3>${catName}</h3>`;
            
            featuresByCategory[catKey].forEach(feature => {
                html += `
                    <div class="feature-toggle">
                        <div class="feature-info">
                            <div class="feature-name">${feature.name}</div>
                            <div class="feature-desc">${feature.description}</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" data-feature="${feature.key}" ${feature.enabled ? 'checked' : ''}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                `;
            });
            
            html += '</div>';
        }
    });
    
    html += '<button class="reset-btn" onclick="resetAllFeatures()">Reset All Settings</button>';
    panel.innerHTML = html;
    
    // Add toggle listeners
    document.querySelectorAll('.feature-toggle input').forEach(input => {
        input.addEventListener('change', (e) => {
            const feature = e.target.dataset.feature;
            CONFIG.features[feature] = e.target.checked;
            toggleFeature(feature, e.target.checked);
            saveConfig();
        });
    });
}

// Setup Event Listeners
function setupEventListeners() {
    // Settings button
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsPanel = document.getElementById('settingsPanel');
    
    if (settingsBtn && settingsPanel) {
        settingsBtn.addEventListener('click', () => {
            settingsPanel.classList.toggle('open');
        });
        
        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!settingsPanel.contains(e.target) && !settingsBtn.contains(e.target)) {
                settingsPanel.classList.remove('open');
            }
        });
    }
    
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
    
    // CSV Upload
    const fileInput = document.getElementById('csvFileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
    
    // Filters
    ['monthFilter', 'locationFilter', 'practitionerFilter', 'serviceFilter', 'startDate', 'endDate'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', applyFilters);
        }
    });
    
    // Quick filters
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.addEventListener('click', handleQuickFilter);
    });
}

// Load Enabled Features
function loadEnabledFeatures() {
    Object.keys(CONFIG.features).forEach(feature => {
        toggleFeature(feature, CONFIG.features[feature]);
    });
}

// Toggle Feature
function toggleFeature(featureKey, enabled) {
    const section = document.getElementById(`${featureKey}Section`);
    if (section) {
        if (enabled) {
            section.classList.add('enabled');
            // Load feature module if it exists
            loadFeatureModule(featureKey);
        } else {
            section.classList.remove('enabled');
        }
    }
}

// Load Feature Module
function loadFeatureModule(featureKey) {
    const modulePath = `js/${featureKey}.js`;
    const scriptId = `module-${featureKey}`;
    
    // Check if already loaded
    if (document.getElementById(scriptId)) {
        return;
    }
    
    const script = document.createElement('script');
    script.id = scriptId;
    script.src = modulePath;
    script.onerror = () => {
        console.warn(`Module ${featureKey} not found, using inline functionality`);
        // Render with inline functionality if module doesn't exist
        if (filteredData.length > 0) {
            renderFeature(featureKey);
        }
    };
    script.onload = () => {
        console.log(`Module ${featureKey} loaded`);
        if (filteredData.length > 0) {
            renderFeature(featureKey);
        }
    };
    
    document.body.appendChild(script);
}

// Switch Tab
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    // Render appropriate content for the tab
    if (tabName === 'overview') {
        renderOverview();
    } else if (tabName === 'timeline') {
        renderTimeline();
    } else if (tabName === 'practitioners') {
        renderPractitioners();
    } else if (tabName === 'customers') {
        renderCustomerAnalytics();
    }
    // Instructions tab is static HTML, no rendering needed
    
    const tab = document.querySelector(`[data-tab="${tabName}"]`);
    const content = document.getElementById(tabName);
    
    if (tab) tab.classList.add('active');
    if (content) content.classList.add('active');
}

// Handle File Upload
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    document.getElementById('uploadStatus').textContent = 'Loading...';
    document.getElementById('uploadStatus').style.color = '#666';
    
    Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
            rawData = results.data;
            filteredData = [...rawData];
            
            document.getElementById('uploadStatus').innerHTML = `<span style="color: #28a745;">✅ Loaded ${formatNumber(rawData.length)} appointments</span>`;
            document.getElementById('uploadStatus').style.color = '#28a745';
            
            populateFilters();
            renderDashboard();
        },
        error: (error) => {
            document.getElementById('uploadStatus').textContent = `âœ— Error: ${error.message}`;
            document.getElementById('uploadStatus').style.color = '#dc3545';
        }
    });
}

// Parse Date
function parseDate(dateStr) {
    if (!dateStr) return new Date();
    
    // Try MM/DD/YYYY format
    const match = dateStr.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    if (match) {
        return new Date(match[3], match[1] - 1, match[2]);
    }
    
    return new Date(dateStr);
}

// Populate Filters
function populateFilters() {
    const months = new Set();
    const locations = new Set();
    const practitioners = new Set();
    const services = new Set();
    
    rawData.forEach(row => {
        const date = parseDate(row['Appointment Date']);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        months.add(monthKey);
        
        if (row.Location) locations.add(row.Location);
        
        if (row['Practitioner First Name'] && row['Practitioner Last Name']) {
            practitioners.add(`${row['Practitioner First Name']} ${row['Practitioner Last Name']}`);
        }
        
        if (row['Appointment']) services.add(row['Appointment']);
    });
    
    // Populate month filter
    const monthFilter = document.getElementById('monthFilter');
    monthFilter.innerHTML = '<option value="all">All Months</option>';
    Array.from(months).sort().reverse().forEach(month => {
        const [year, mon] = month.split('-');
        const date = new Date(year, mon - 1);
        const label = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        monthFilter.innerHTML += `<option value="${month}">${label}</option>`;
    });
    
    // Populate location filter
    const locationFilter = document.getElementById('locationFilter');
    locationFilter.innerHTML = '<option value="all">All Locations</option>';
    Array.from(locations).sort().forEach(loc => {
        locationFilter.innerHTML += `<option value="${loc}">${loc}</option>`;
    });
    
    // Populate practitioner filter
    const practitionerFilter = document.getElementById('practitionerFilter');
    practitionerFilter.innerHTML = '<option value="all">All Practitioners</option>';
    Array.from(practitioners).sort().forEach(prac => {
        practitionerFilter.innerHTML += `<option value="${prac}">${prac}</option>`;
    });
    
    // Populate service filter
    const serviceFilter = document.getElementById('serviceFilter');
    if (serviceFilter) {
        serviceFilter.innerHTML = '<option value="all">All Services</option>';
        Array.from(services).sort().forEach(service => {
            serviceFilter.innerHTML += `<option value="${service}">${service}</option>`;
        });
    }
}

// Apply Filters
function applyFilters() {
    const month = document.getElementById('monthFilter').value;
    const location = document.getElementById('locationFilter').value;
    const practitioner = document.getElementById('practitionerFilter').value;
    const service = document.getElementById('serviceFilter')?.value || 'all';
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    filteredData = rawData.filter(row => {
        const date = parseDate(row['Appointment Date']);
        
        // Month filter
        if (month !== 'all') {
            const rowMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            if (rowMonth !== month) return false;
        }
        
        // Location filter
        if (location !== 'all' && row.Location !== location) return false;
        
        // Practitioner filter
        if (practitioner !== 'all') {
            const rowPractitioner = `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`;
            if (rowPractitioner !== practitioner) return false;
        }
        
        // Service filter
        if (service !== 'all' && row['Appointment'] !== service) return false;
        
        // Date range filters
        if (startDate && date < new Date(startDate)) return false;
        if (endDate && date > new Date(endDate)) return false;
        
        return true;
    });
    
    renderDashboard();
}

// Handle Quick Filter
function handleQuickFilter(e) {
    const btn = e.target;
    const days = btn.dataset.days;
    const month = btn.dataset.month;
    const today = new Date();
    
    if (days) {
        const startDate = new Date(today);
        startDate.setDate(startDate.getDate() - parseInt(days));
        document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
        document.getElementById('monthFilter').value = 'all';
    } else if (month === 'current') {
        const monthStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
        document.getElementById('monthFilter').value = monthStr;
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
    } else if (month === 'last') {
        const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const monthStr = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;
        document.getElementById('monthFilter').value = monthStr;
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
    }
    
    applyFilters();
}

// Render Dashboard
function renderDashboard() {
    if (filteredData.length === 0) return;
    
    renderOverview();
    renderTimeline();
    renderPractitioners();
    
        // Render Business Intelligence (if enabled)
    if (CONFIG.features.businessIntelligence !== false) {
        renderBusinessIntelligence();
    }

    // Render enabled features
    Object.keys(CONFIG.features).forEach(feature => {
        if (CONFIG.features[feature]) {
            renderFeature(feature);
        }
    });
}

// Render Overview Tab
function renderOverview() {
    const data = filteredData;
    const totalRevenue = data.reduce((sum, row) => sum + parseFloat(row.Revenue || 0), 0);
    const totalPayout = data.reduce((sum, row) => sum + parseFloat(row['Total Payout'] || 0), 0);
    const totalHours = data.reduce((sum, row) => sum + parseFloat(row['Time (h)'] || 0), 0);
    const avgRevenue = data.length > 0 ? totalRevenue / data.length : 0;
    const profit = totalRevenue - totalPayout;
    const profitMargin = totalRevenue > 0 ? (profit / totalRevenue * 100) : 0;
    
    document.getElementById('overviewMetrics').innerHTML = `
        <div class="metric-card">
            <div class="metric-label">Total Revenue</div>
            <div class="metric-value">${formatCurrency(totalRevenue)}</div>
            <div class="metric-subtext">From ${formatNumber(data.length)} appointments</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Payout</div>
            <div class="metric-value">${formatCurrency(totalPayout)}</div>
            <div class="metric-subtext">To practitioners</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Profit</div>
            <div class="metric-value">${formatCurrency(profit)}</div>
            <div class="metric-subtext">${profitMargin.toFixed(1)}% margin</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Appointments</div>
            <div class="metric-value">${formatNumber(data.length)}</div>
            <div class="metric-subtext">Total sessions</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Hours</div>
            <div class="metric-value">${formatNumber(totalHours)}</div>
            <div class="metric-subtext">Service hours</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Revenue</div>
            <div class="metric-value">${formatCurrency(avgRevenue)}</div>
            <div class="metric-subtext">Per appointment</div>
        </div>
    `;
    
    // Render basic charts
    renderRevenueByLocationChart();
    renderRevenueByServiceChart();
    renderIntroOffersChart();
}

// Render Timeline Tab
function renderTimeline() {
    renderTimelineMetrics();
    renderDailyRevenueChart();
    renderAppointmentsTrendChart();
}

function renderTimelineMetrics() {
    const container = document.getElementById('timelineMetrics');
    if (!container) return;
    
    // Group by date
    const dailyData = {};
    filteredData.forEach(row => {
        const date = parseDate(row['Appointment Date']).toLocaleDateString();
        if (!dailyData[date]) {
            dailyData[date] = { revenue: 0, appointments: 0 };
        }
        dailyData[date].revenue += parseFloat(row.Revenue || 0);
        dailyData[date].appointments++;
    });
    
    const dates = Object.keys(dailyData).sort();
    const avgDailyRevenue = dates.length > 0 
        ? Object.values(dailyData).reduce((sum, d) => sum + d.revenue, 0) / dates.length 
        : 0;
    const avgDailyAppointments = dates.length > 0
        ? Object.values(dailyData).reduce((sum, d) => sum + d.appointments, 0) / dates.length
        : 0;
    
    const bestDay = dates.reduce((best, date) => {
        return dailyData[date].revenue > (dailyData[best]?.revenue || 0) ? date : best;
    }, dates[0]);
    
    container.innerHTML = `
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
            <div class="metric-label">Best Day</div>
            <div class="metric-value">${CONFIG.settings.currencySymbol}${(dailyData[bestDay]?.revenue || 0).toFixed(0)}</div>
            <div class="metric-subtext">${bestDay}</div>
        </div>
    `;
}

// Render Practitioners Tab
function renderPractitioners() {
    renderPractitionerTable();
    renderPractitionerRevenueChart();
}

// Render Feature
function renderFeature(featureKey) {
    // Features will call their specific render functions
    switch(featureKey) {
        case 'heatmap':
            if (typeof renderHeatmap === 'function') renderHeatmap();
            break;
        case 'clientRetention':
            if (typeof renderClientRetention === 'function') renderClientRetention();
            break;
        case 'scheduleOptimization':
            if (typeof renderScheduleOptimization === 'function') renderScheduleOptimization();
            break;
        case 'goals':
            if (typeof renderGoals === 'function') renderGoals();
            break;
        case 'alerts':
            if (typeof renderAlerts === 'function') renderAlerts();
            break;
    }
}

// Chart Rendering Functions
function renderRevenueByLocationChart() {
    const canvas = document.getElementById('revenueByLocationChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Aggregate data by location
    const revenueByLocation = {};
    filteredData.forEach(row => {
        const location = row.Location || 'Unknown';
        const revenue = parseFloat(row.Revenue || 0);
        revenueByLocation[location] = (revenueByLocation[location] || 0) + revenue;
    });
    
    // Destroy existing chart
    if (allCharts.revenueByLocation) {
        allCharts.revenueByLocation.destroy();
    }
    
    allCharts.revenueByLocation = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(revenueByLocation),
            datasets: [{
                label: 'Revenue by Location',
                data: Object.values(revenueByLocation),
                backgroundColor: CONFIG.settings.chartColors.accent,
                borderColor: CONFIG.settings.chartColors.primary,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return CONFIG.settings.currencySymbol + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

function renderRevenueByServiceChart() {
    const canvas = document.getElementById('revenueByServiceChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Aggregate data by service (using "Appointment" column)
    const revenueByService = {};
    filteredData.forEach(row => {
        const service = row['Appointment'] || 'Unknown';
        const revenue = parseFloat(row.Revenue || 0);
        revenueByService[service] = (revenueByService[service] || 0) + revenue;
    });
    
    // Sort and take top 10
    const sortedServices = Object.entries(revenueByService)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    // Destroy existing chart
    if (allCharts.revenueByService) {
        allCharts.revenueByService.destroy();
    }

// Render Introductory Offers Chart
function renderIntroOffersChart() {
    const canvas = document.getElementById('introOffersChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (allCharts.introOffers) {
        allCharts.introOffers.destroy();
    }
    
    // Count intro offers vs regular appointments
    let introCount = 0;
    let regularCount = 0;
    
    filteredData.forEach(row => {
        const serviceName = (row['Service Name'] || '').toLowerCase();
        if (serviceName.includes('intro')) {
            introCount++;
        } else {
            regularCount++;
        }
    });
    
    // Create chart
    allCharts.introOffers = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Introductory Offers', 'Regular Appointments'],
            datasets: [{
                data: [introCount, regularCount],
                backgroundColor: [
                    CONFIG.settings.chartColors.highlight,  // Yellow for intro
                    CONFIG.settings.chartColors.primary     // Blue for regular
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = introCount + regularCount;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${formatNumber(value)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    console.log(`Intro Offers Chart: ${introCount} intro, ${regularCount} regular`);
}

    
    allCharts.revenueByService = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedServices.map(s => s[0]),
            datasets: [{
                label: 'Revenue by Service',
                data: sortedServices.map(s => s[1]),
                backgroundColor: CONFIG.settings.chartColors.primary,
                borderColor: CONFIG.settings.chartColors.accent,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return CONFIG.settings.currencySymbol + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

function renderDailyRevenueChart() {
    const canvas = document.getElementById('dailyRevenueChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Group by date
    const dailyRevenue = {};
    filteredData.forEach(row => {
        const date = parseDate(row['Appointment Date']).toLocaleDateString();
        dailyRevenue[date] = (dailyRevenue[date] || 0) + parseFloat(row.Revenue || 0);
    });
    
    const sortedDates = Object.keys(dailyRevenue).sort((a, b) => {
        return new Date(a) - new Date(b);
    });
    
    // Destroy existing chart
    if (allCharts.dailyRevenue) {
        allCharts.dailyRevenue.destroy();
    }
    
    allCharts.dailyRevenue = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sortedDates,
            datasets: [{
                label: 'Daily Revenue',
                data: sortedDates.map(date => dailyRevenue[date]),
                borderColor: CONFIG.settings.chartColors.accent,
                backgroundColor: CONFIG.settings.chartColors.accent + '20',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return CONFIG.settings.currencySymbol + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

function renderAppointmentsTrendChart() {
    const canvas = document.getElementById('appointmentsTrendChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Group by date
    const dailyAppointments = {};
    filteredData.forEach(row => {
        const date = parseDate(row['Appointment Date']).toLocaleDateString();
        dailyAppointments[date] = (dailyAppointments[date] || 0) + 1;
    });
    
    const sortedDates = Object.keys(dailyAppointments).sort((a, b) => {
        return new Date(a) - new Date(b);
    });
    
    // Destroy existing chart
    if (allCharts.appointmentsTrend) {
        allCharts.appointmentsTrend.destroy();
    }
    
    allCharts.appointmentsTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sortedDates,
            datasets: [{
                label: 'Daily Appointments',
                data: sortedDates.map(date => dailyAppointments[date]),
                borderColor: CONFIG.settings.chartColors.primary,
                backgroundColor: CONFIG.settings.chartColors.primary + '20',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function renderPractitionerTable() {
    const container = document.getElementById('practitionersTable');
    if (!container) return;
    
    // Aggregate by practitioner
    const practitionerData = {};
    filteredData.forEach(row => {
        const name = `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`;
        if (!practitionerData[name]) {
            practitionerData[name] = {
                appointments: 0,
                revenue: 0,
                payout: 0,
                hours: 0
            };
        }
        practitionerData[name].appointments++;
        practitionerData[name].revenue += parseFloat(row.Revenue || 0);
        practitionerData[name].payout += parseFloat(row['Total Payout'] || 0);
        practitionerData[name].hours += parseFloat(row['Time (h)'] || 0);
    });
    
    let html = '<h2>Practitioner Performance</h2><table><thead><tr>';
    html += '<th>Practitioner</th><th>Appointments</th><th>Revenue</th><th>Payout</th><th>Hours</th><th>Avg/Appt</th>';
    html += '</tr></thead><tbody>';
    
    Object.entries(practitionerData).forEach(([name, data]) => {
        const avgRevenue = data.appointments > 0 ? data.revenue / data.appointments : 0;
        html += `<tr>
            <td>${name}</td>
            <td>${data.appointments}</td>
            <td>${CONFIG.settings.currencySymbol}${data.revenue.toFixed(2)}</td>
            <td>${CONFIG.settings.currencySymbol}${data.payout.toFixed(2)}</td>
            <td>${data.hours.toFixed(1)}</td>
            <td>${formatCurrency(avgRevenue)}</td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function renderPractitionerRevenueChart() {
    const canvas = document.getElementById('practitionerRevenueChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Aggregate by practitioner
    const practitionerRevenue = {};
    filteredData.forEach(row => {
        const name = `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`;
        const revenue = parseFloat(row.Revenue || 0);
        practitionerRevenue[name] = (practitionerRevenue[name] || 0) + revenue;
    });
    
    const sortedPractitioners = Object.entries(practitionerRevenue)
        .sort((a, b) => b[1] - a[1]);
    
    // Destroy existing chart
    if (allCharts.practitionerRevenue) {
        allCharts.practitionerRevenue.destroy();
    }
    
    allCharts.practitionerRevenue = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedPractitioners.map(p => p[0]),
            datasets: [{
                label: 'Revenue by Practitioner',
                data: sortedPractitioners.map(p => p[1]),
                backgroundColor: CONFIG.settings.chartColors.highlight,
                borderColor: CONFIG.settings.chartColors.primary,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return CONFIG.settings.currencySymbol + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

// Save Configuration
function saveConfig() {
    localStorage.setItem('tvsConfig', JSON.stringify(CONFIG));
}

// Load Configuration
function loadConfig() {
    const saved = localStorage.getItem('tvsConfig');
    if (saved) {
        try {
            const savedConfig = JSON.parse(saved);
            // Merge saved config with default config
            Object.assign(CONFIG.features, savedConfig.features || {});
            Object.assign(CONFIG.goals, savedConfig.goals || {});
        } catch (e) {
            console.error('Error loading config:', e);
        }
    }
}

// Reset All Features
function resetAllFeatures() {
    if (confirm('Reset all features to default? This will reload the page.')) {
        localStorage.removeItem('tvsConfig');
        location.reload();
    }
}

// Export to CSV
function exportToCSV() {
    if (filteredData.length === 0) {
        alert('No data to export');
        return;
    }
    
    const headers = Object.keys(filteredData[0]);
    let csv = headers.join(',') + '\n';
    
    filteredData.forEach(row => {
        const values = headers.map(header => {
            const value = row[header] || '';
            return value.toString().includes(',') ? `"${value}"` : value;
        });
        csv += values.join(',') + '\n';
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `tvs-export-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        loadConfig();
        initDashboard();
    });
} else {
    loadConfig();
    initDashboard();
}
// Business Intelligence Dashboard Feature
// Add this section to create a funnel analysis

function renderBusinessIntelligence() {
    console.log('Rendering Business Intelligence Dashboard...');
    
    if (filteredData.length === 0) return;
    
    // Get or create the BI section in the DOM
    let biSection = document.getElementById('businessIntelligenceSection');
    if (!biSection) {
        // Create the section if it doesn't exist
        const container = document.querySelector('.container');
        biSection = document.createElement('div');
        biSection.id = 'businessIntelligenceSection';
        biSection.className = 'feature-section';
        biSection.setAttribute('data-feature', 'businessIntelligence');
        container.appendChild(biSection);
    }
    
    // Calculate funnel metrics
    const totalRevenue = filteredData.reduce((sum, row) => sum + parseFloat(row.Revenue || 0), 0);
    const totalAppointments = filteredData.length;
    
    // Unique clients
    const clientIds = new Set();
    filteredData.forEach(row => {
        const clientId = row['Client Id'] || `${row['Client First Name']}_${row['Client Last Name']}`;
        if (clientId && clientId !== '_') {
            clientIds.add(clientId);
        }
    });
    const uniqueClients = clientIds.size;
    
    // Return clients (clients with more than 1 appointment)
    const clientVisits = {};
    filteredData.forEach(row => {
        const clientId = row['Client Id'] || `${row['Client First Name']}_${row['Client Last Name']}`;
        if (clientId && clientId !== '_') {
            clientVisits[clientId] = (clientVisits[clientId] || 0) + 1;
        }
    });
    const returningClients = Object.values(clientVisits).filter(count => count > 1).length;
    const returnRate = uniqueClients > 0 ? (returningClients / uniqueClients * 100) : 0;
    
    // Average appointments per client
    const avgApptsPerClient = uniqueClients > 0 ? (totalAppointments / uniqueClients) : 0;
    
    // Calculate conversion funnel
    const totalLeads = uniqueClients; // Assuming each unique client is a lead
    const bookedAppts = totalAppointments;
    const completedAppts = filteredData.filter(row => row.Status !== 'Cancelled' && row.Status !== 'No Show').length;
    const returningAppts = filteredData.filter(row => {
        const clientId = row['Client Id'] || `${row['Client First Name']}_${row['Client Last Name']}`;
        return clientVisits[clientId] > 1;
    }).length;
    
    // Conversion rates
    const bookingRate = totalLeads > 0 ? (bookedAppts / totalLeads) : 0;
    const completionRate = bookedAppts > 0 ? (completedAppts / bookedAppts) : 0;
    const returnRateCalc = completedAppts > 0 ? (returningAppts / completedAppts) : 0;
    
    // Format currency
    const formatCurrency = (num) => CONFIG.settings.currencySymbol + num.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const formatNumber = (num) => num.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 1});
    
    const html = `
        <div class="table-container">
            <h2>💼 Business Intelligence Dashboard</h2>
            <p style="margin-bottom: 20px; color: #666;">Comprehensive funnel analysis and conversion metrics</p>
            
            <div class="metrics-grid" style="margin-bottom: 30px;">
                <div class="metric-card">
                    <div class="metric-label">Total Clients</div>
                    <div class="metric-value">${formatNumber(uniqueClients)}</div>
                    <div class="metric-subtext">Unique individuals</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Return Rate</div>
                    <div class="metric-value">${returnRate.toFixed(1)}%</div>
                    <div class="metric-subtext">${formatNumber(returningClients)} returning clients</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Visits</div>
                    <div class="metric-value">${avgApptsPerClient.toFixed(1)}</div>
                    <div class="metric-subtext">Per client</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Client LTV</div>
                    <div class="metric-value">${formatCurrency(uniqueClients > 0 ? totalRevenue / uniqueClients : 0)}</div>
                    <div class="metric-subtext">Lifetime value</div>
                </div>
            </div>
            
            <h3 style="margin: 30px 0 15px 0;">Conversion Funnel</h3>
            <div class="funnel-container" style="margin-bottom: 30px;">
                <div class="funnel-stage" style="background: linear-gradient(to right, #013160 0%, #013160 100%); padding: 20px; margin-bottom: 2px; border-radius: 4px; color: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9;">Total Leads / Clients</div>
                            <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">${formatNumber(totalLeads)}</div>
                        </div>
                        <div style="font-size: 32px; opacity: 0.8;">👥</div>
                    </div>
                </div>
                
                <div class="funnel-stage" style="background: linear-gradient(to right, #71BED2 0%, #71BED2 ${bookingRate * 100}%); padding: 20px; margin-bottom: 2px; border-radius: 4px; color: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9;">Booked Appointments</div>
                            <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">${formatNumber(bookedAppts)}</div>
                            <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">${(bookingRate * 100).toFixed(1)}% booking rate</div>
                        </div>
                        <div style="font-size: 32px; opacity: 0.8;">📅</div>
                    </div>
                </div>
                
                <div class="funnel-stage" style="background: linear-gradient(to right, #FBB514 0%, #FBB514 ${completionRate * 100}%); padding: 20px; margin-bottom: 2px; border-radius: 4px; color: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9;">Completed Appointments</div>
                            <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">${formatNumber(completedAppts)}</div>
                            <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">${(completionRate * 100).toFixed(1)}% completion rate</div>
                        </div>
                        <div style="font-size: 32px; opacity: 0.8;">✅</div>
                    </div>
                </div>
                
                <div class="funnel-stage" style="background: linear-gradient(to right, #28a745 0%, #28a745 ${returnRateCalc * 100}%); padding: 20px; border-radius: 4px; color: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9;">Returning Appointments</div>
                            <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">${formatNumber(returningAppts)}</div>
                            <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">${(returnRateCalc * 100).toFixed(1)}% return rate</div>
                        </div>
                        <div style="font-size: 32px; opacity: 0.8;">🔄</div>
                    </div>
                </div>
            </div>
            
            <h3 style="margin: 30px 0 15px 0;">Key Insights</h3>
            <div class="alert info">
                <p><strong>📊 Funnel Performance:</strong></p>
                <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                    <li>From ${formatNumber(totalLeads)} unique clients, you have ${formatNumber(bookedAppts)} total appointments (${(bookingRate).toFixed(2)}x multiplier)</li>
                    <li>${(completionRate * 100).toFixed(1)}% of booked appointments are completed</li>
                    <li>${(returnRateCalc * 100).toFixed(1)}% of appointments are from returning clients</li>
                    <li>Average client lifetime value: ${formatCurrency(uniqueClients > 0 ? totalRevenue / uniqueClients : 0)}</li>
                </ul>
            </div>
            
            ${returnRate < 50 ? `
                <div class="alert warning" style="margin-top: 15px;">
                    <p><strong>⚠️ Opportunity:</strong> Less than 50% of clients are returning. Consider implementing:</p>
                    <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                        <li>Follow-up email campaigns</li>
                        <li>Loyalty programs or package deals</li>
                        <li>Personalized rebooking reminders</li>
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
    
    biSection.innerHTML = html;
    biSection.style.display = 'block';
}

// Make it available globally
window.renderBusinessIntelligence = renderBusinessIntelligence;
// Customer Analysis Module
// Analyzes leads/customers data for LTV, conversion, and segmentation

let leadsData = [];
let mergedCustomerData = [];

// Process leads/customers file upload
function handleLeadsUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    document.getElementById('leadsUploadStatus').textContent = 'Processing...';
    
    Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: function(results) {
            leadsData = results.data;
            console.log(`Loaded ${leadsData.length} leads/customers`);
            document.getElementById('leadsUploadStatus').innerHTML = `✅ Loaded ${formatNumber(leadsData.length)} customers`;
            
            // Merge with appointments data if available
            if (rawData.length > 0) {
                mergeCustomerData();
            }
            
            // Render customer insights
            renderCustomerAnalytics();
        },
        error: function(error) {
            console.error('Error parsing leads CSV:', error);
            document.getElementById('leadsUploadStatus').innerHTML = `❌ Error loading file`;
        }
    });
}

// Merge customer data with appointments
function mergeCustomerData() {
    console.log('Merging customer data with appointments...');
    
    mergedCustomerData = leadsData.map(customer => {
        const email = (customer['E-mail'] || '').toLowerCase().trim();
        const firstName = (customer['First name'] || '').toLowerCase().trim();
        const lastName = (customer['Last name'] || '').toLowerCase().trim();
        
        // Find matching appointments
        const customerAppointments = rawData.filter(appt => {
            const apptEmail = (appt['Client Email'] || '').toLowerCase().trim();
            const apptFirst = (appt['Client First Name'] || '').toLowerCase().trim();
            const apptLast = (appt['Client Last Name'] || '').toLowerCase().trim();
            
            // Match by email (primary) or name (backup)
            return (email && apptEmail === email) || 
                   (firstName && lastName && apptFirst === firstName && apptLast === lastName);
        });
        
        // Calculate metrics from appointments
        const apptCount = customerAppointments.length;
        const apptRevenue = customerAppointments.reduce((sum, a) => sum + parseFloat(a.Revenue || 0), 0);
        
        return {
            ...customer,
            appointmentCount: apptCount,
            appointmentRevenue: apptRevenue,
            appointments: customerAppointments
        };
    });
    
    console.log(`Merged ${mergedCustomerData.length} customer records`);
}

// Render complete customer insights
function renderCustomerAnalytics() {
    const container = document.getElementById('customerInsightsContainer');
    if (!container || leadsData.length === 0) return;
    
    console.log('Rendering customer insights...');
    
    // Calculate metrics
    const totalCustomers = leadsData.length;
    const customers = leadsData.filter(c => c.Type === 'Customer').length;
    const leads = leadsData.filter(c => c.Type === 'Lead').length;
    
    // LTV Analysis
    const ltvs = leadsData.map(c => parseFloat(c.LTV || 0));
    const totalLTV = ltvs.reduce((sum, ltv) => sum + ltv, 0);
    const avgLTV = totalLTV / ltvs.length;
    const maxLTV = Math.max(...ltvs);
    
    // LTV Distribution
    const zeroLTV = ltvs.filter(ltv => ltv === 0).length;
    const lowLTV = ltvs.filter(ltv => ltv > 0 && ltv <= 100).length;
    const midLTV = ltvs.filter(ltv => ltv > 100 && ltv <= 500).length;
    const highLTV = ltvs.filter(ltv => ltv > 500).length;
    
    // First Purchase Analysis
    const firstPurchases = {};
    const firstPurchaseLTV = {};
    
    leadsData.forEach(c => {
        const fp = c['First purchase'] || 'N/A';
        firstPurchases[fp] = (firstPurchases[fp] || 0) + 1;
        if (!firstPurchaseLTV[fp]) firstPurchaseLTV[fp] = [];
        firstPurchaseLTV[fp].push(parseFloat(c.LTV || 0));
    });
    
    // Sort first purchases by count
    const sortedFP = Object.entries(firstPurchases)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
    
    // Top customers
    const sortedByLTV = [...leadsData]
        .sort((a, b) => parseFloat(b.LTV || 0) - parseFloat(a.LTV || 0))
        .slice(0, 10);
    
    // Revenue opportunity
    const zeroLTVCustomers = leadsData.filter(c => parseFloat(c.LTV || 0) === 0);
    const potentialRevenue = zeroLTVCustomers.length * avgLTV;
    const neverPurchased = zeroLTVCustomers.filter(c => c['First purchase'] === 'N/A').length;
    
    let html = `
        <!-- Zero-LTV Alert (Top Priority) -->
        <div class="alert warning" style="margin-bottom: 30px;">
            <h3 style="margin: 0 0 15px 0;">⚠️ Revenue Opportunity Alert</h3>
            <div class="metrics-grid" style="margin-bottom: 15px;">
                <div class="metric-card">
                    <div class="metric-label">Zero-LTV Customers</div>
                    <div class="metric-value">${formatNumber(zeroLTVCustomers.length)}</div>
                    <div class="metric-subtext">${(zeroLTVCustomers.length/totalCustomers*100).toFixed(1)}% of total</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Potential Revenue</div>
                    <div class="metric-value">${formatCurrency(potentialRevenue)}</div>
                    <div class="metric-subtext">If converted at avg LTV</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Never Purchased</div>
                    <div class="metric-value">${formatNumber(neverPurchased)}</div>
                    <div class="metric-subtext">Need outreach campaign</div>
                </div>
            </div>
            <p style="margin: 0;"><strong>Recommended Action:</strong> Launch re-engagement campaign targeting ${formatNumber(neverPurchased)} leads who never purchased.</p>
        </div>
        
        <!-- LTV Overview -->
        <h2>💰 Customer Lifetime Value Analysis</h2>
        <div class="metrics-grid" style="margin-bottom: 30px;">
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
                <div class="metric-label">Highest LTV</div>
                <div class="metric-value">${formatCurrency(maxLTV)}</div>
                <div class="metric-subtext">Top customer</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">VIP Customers</div>
                <div class="metric-value">${formatNumber(highLTV)}</div>
                <div class="metric-subtext">> $500 LTV</div>
            </div>
        </div>
        
        <!-- LTV Distribution Chart -->
        <div class="charts-grid" style="margin-bottom: 30px;">
            <div class="chart-container">
                <h3>LTV Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="ltvDistributionChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Lead Conversion</h3>
                <div class="chart-wrapper">
                    <canvas id="leadConversionChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- First Purchase Analysis -->
        <h2>🎯 First Purchase Analysis</h2>
        <div class="table-container" style="margin-bottom: 30px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: var(--gray-light); text-align: left;">
                        <th style="padding: 12px;">First Purchase Type</th>
                        <th style="padding: 12px; text-align: right;">Count</th>
                        <th style="padding: 12px; text-align: right;">% of Total</th>
                        <th style="padding: 12px; text-align: right;">Avg LTV</th>
                    </tr>
                </thead>
                <tbody>
                    ${sortedFP.map(([type, count]) => {
                        const avgLTVForType = firstPurchaseLTV[type].reduce((a, b) => a + b, 0) / firstPurchaseLTV[type].length;
                        return `
                            <tr style="border-bottom: 1px solid var(--gray-light);">
                                <td style="padding: 12px;">${type}</td>
                                <td style="padding: 12px; text-align: right;">${formatNumber(count)}</td>
                                <td style="padding: 12px; text-align: right;">${(count/totalCustomers*100).toFixed(1)}%</td>
                                <td style="padding: 12px; text-align: right;">${formatCurrency(avgLTVForType)}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
        
        <!-- Top Customers -->
        <h2>👑 Top 10 Customers by LTV</h2>
        <div class="table-container" style="margin-bottom: 30px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: var(--gray-light); text-align: left;">
                        <th style="padding: 12px;">Rank</th>
                        <th style="padding: 12px;">Customer</th>
                        <th style="padding: 12px;">Email</th>
                        <th style="padding: 12px;">First Purchase</th>
                        <th style="padding: 12px; text-align: right;">LTV</th>
                    </tr>
                </thead>
                <tbody>
                    ${sortedByLTV.map((c, i) => `
                        <tr style="border-bottom: 1px solid var(--gray-light);">
                            <td style="padding: 12px;">${i + 1}</td>
                            <td style="padding: 12px;">${c['First name']} ${c['Last name']}</td>
                            <td style="padding: 12px;">${c['E-mail']}</td>
                            <td style="padding: 12px;">${c['First purchase'] || 'N/A'}</td>
                            <td style="padding: 12px; text-align: right; font-weight: bold;">${formatCurrency(parseFloat(c.LTV || 0))}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        
        <!-- Customer Segmentation -->
        <h2>👥 Customer Segmentation</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Records</div>
                <div class="metric-value">${formatNumber(totalCustomers)}</div>
                <div class="metric-subtext">Leads & Customers</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Customers</div>
                <div class="metric-value">${formatNumber(customers)}</div>
                <div class="metric-subtext">${(customers/totalCustomers*100).toFixed(1)}% conversion</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Leads</div>
                <div class="metric-value">${formatNumber(leads)}</div>
                <div class="metric-subtext">${(leads/totalCustomers*100).toFixed(1)}% of total</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Conversion Rate</div>
                <div class="metric-value">${(customers/totalCustomers*100).toFixed(1)}%</div>
                <div class="metric-subtext">Lead → Customer</div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Render charts
    setTimeout(() => {
        renderLTVDistributionChart(zeroLTV, lowLTV, midLTV, highLTV);
        renderLeadConversionChart(leads, customers);
    }, 100);
}

// Render LTV Distribution Chart
function renderLTVDistributionChart(zero, low, mid, high) {
    const canvas = document.getElementById('ltvDistributionChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (allCharts.ltvDistribution) {
        allCharts.ltvDistribution.destroy();
    }
    
    allCharts.ltvDistribution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['$0', '$1-$100', '$100-$500', '$500+'],
            datasets: [{
                label: 'Number of Customers',
                data: [zero, low, mid, high],
                backgroundColor: [
                    '#dc3545',  // Red for $0
                    '#ffc107',  // Yellow for low
                    '#28a745',  // Green for mid
                    '#013160'   // Blue for high
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = zero + low + mid + high;
                            const pct = ((context.parsed.y / total) * 100).toFixed(1);
                            return `${formatNumber(context.parsed.y)} customers (${pct}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            }
        }
    });
}

// Render Lead Conversion Chart
function renderLeadConversionChart(leads, customers) {
    const canvas = document.getElementById('leadConversionChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (allCharts.leadConversion) {
        allCharts.leadConversion.destroy();
    }
    
    allCharts.leadConversion = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Customers', 'Leads'],
            datasets: [{
                data: [customers, leads],
                backgroundColor: [
                    CONFIG.settings.chartColors.primary,
                    CONFIG.settings.chartColors.accent
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = customers + leads;
                            const pct = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${formatNumber(context.parsed)} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

console.log('Customer analysis module loaded');

// Add event listener for leads file upload
document.addEventListener('DOMContentLoaded', function() {
    const leadsInput = document.getElementById('leadsFileInput');
    if (leadsInput) {
        leadsInput.addEventListener('change', handleLeadsFileUpload);
    }
});
