// Leads & Customers Analysis Module
// Handles customer lifetime value, lead conversion, and customer segmentation

// Global state for leads data
let leadsData = [];
let mergedCustomerData = [];

// Parse and load leads/customers CSV
function handleLeadsFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    document.getElementById('leadsUploadStatus').innerHTML = '<span style="color: #FBB514;">⏳ Loading leads data...</span>';
    
    Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: function(results) {
            leadsData = results.data;
            console.log(`Loaded ${formatNumber(leadsData.length)} leads/customers`);
            document.getElementById('leadsUploadStatus').innerHTML = `<span style="color: #28a745;">✅ Loaded ${formatNumber(leadsData.length)} leads/customers</span>`;
            
            // Attempt to merge with appointments data if available
            if (rawData.length > 0) {
                mergeCustomerData();
            }
            
            // Render customer analytics
            renderCustomerAnalytics();
        },
        error: function(error) {
            console.error('Error parsing leads CSV:', error);
            document.getElementById('leadsUploadStatus').innerHTML = '<span style="color: #dc3545;">❌ Error loading file</span>';
        }
    });
}

// Merge leads data with appointments data
function mergeCustomerData() {
    console.log('Merging customer data...');
    
    const mergeStatus = document.getElementById('mergeStatus');
    const mergeStatusText = document.getElementById('mergeStatusText');
    
    if (!mergeStatus || !mergeStatusText) return;
    
    mergeStatus.style.display = 'block';
    mergeStatusText.textContent = 'Matching customers between files...';
    
    // Create lookup maps from appointments data
    const appointmentsByEmail = {};
    const appointmentsByName = {};
    
    rawData.forEach(row => {
        const email = (row['Client Email'] || '').toLowerCase().trim();
        const name = `${(row['Client First Name'] || '').toLowerCase()}_${(row['Client Last Name'] || '').toLowerCase()}`;
        
        if (email) {
            if (!appointmentsByEmail[email]) appointmentsByEmail[email] = [];
            appointmentsByEmail[email].push(row);
        }
        
        if (name !== '_') {
            if (!appointmentsByName[name]) appointmentsByName[name] = [];
            appointmentsByName[name].push(row);
        }
    });
    
    // Match leads with appointments
    let matchedByEmail = 0;
    let matchedByName = 0;
    let unmatched = 0;
    
    mergedCustomerData = leadsData.map(lead => {
        const email = (lead['E-mail'] || '').toLowerCase().trim();
        const name = `${(lead['First name'] || '').toLowerCase()}_${(lead['Last name'] || '').toLowerCase()}`;
        
        let appointments = [];
        let matchMethod = 'none';
        
        // Try email match first
        if (email && appointmentsByEmail[email]) {
            appointments = appointmentsByEmail[email];
            matchMethod = 'email';
            matchedByEmail++;
        }
        // Fallback to name match
        else if (name !== '_' && appointmentsByName[name]) {
            appointments = appointmentsByName[name];
            matchMethod = 'name';
            matchedByName++;
        } else {
            unmatched++;
        }
        
        // Calculate appointment metrics
        const totalAppointments = appointments.length;
        const totalRevenue = appointments.reduce((sum, apt) => sum + parseFloat(apt.Revenue || 0), 0);
        
        return {
            ...lead,
            appointments: appointments,
            appointmentCount: totalAppointments,
            calculatedRevenue: totalRevenue,
            matchMethod: matchMethod
        };
    });
    
    console.log(`Merge complete: ${matchedByEmail} by email, ${matchedByName} by name, ${unmatched} unmatched`);
    mergeStatusText.innerHTML = `✅ Matched ${matchedByEmail + matchedByName} customers (${matchedByEmail} by email, ${matchedByName} by name) | ${unmatched} leads without appointments`;
}

// Render all customer analytics
function renderCustomerAnalytics() {
    if (leadsData.length === 0) return;
    
    renderLTVMetrics();
    renderLTVDistributionChart();
    renderFirstPurchaseChart();
    renderConversionFunnel();
    renderZeroLTVAlert();
    renderTopCustomers();
    renderCustomerSegmentation();
}

// Render LTV Metrics
function renderLTVMetrics() {
    const container = document.getElementById('ltvMetrics');
    if (!container) return;
    
    // Calculate LTV metrics
    const ltvs = leadsData.map(row => parseFloat(row.LTV || 0));
    const totalLTV = ltvs.reduce((sum, ltv) => sum + ltv, 0);
    const avgLTV = totalLTV / ltvs.length;
    const maxLTV = Math.max(...ltvs);
    
    const customers = leadsData.filter(row => row.Type === 'Customer').length;
    const leads = leadsData.filter(row => row.Type === 'Lead').length;
    
    const highValueCustomers = ltvs.filter(ltv => ltv > 500).length;
    const zeroLTV = ltvs.filter(ltv => ltv === 0).length;
    
    container.innerHTML = `
        <div class="metric-card">
            <div class="metric-label">Total LTV</div>
            <div class="metric-value">${formatCurrency(totalLTV)}</div>
            <div class="metric-subtext">From ${formatNumber(leadsData.length)} people</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Average LTV</div>
            <div class="metric-value">${formatCurrency(avgLTV)}</div>
            <div class="metric-subtext">Per customer</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Customers</div>
            <div class="metric-value">${formatNumber(customers)}</div>
            <div class="metric-subtext">${leads} leads | ${((customers/(customers+leads))*100).toFixed(1)}% conversion</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">VIP Customers</div>
            <div class="metric-value">${formatNumber(highValueCustomers)}</div>
            <div class="metric-subtext">>$500 LTV | ${maxLTV > 0 ? formatCurrency(maxLTV) + ' highest' : 'N/A'}</div>
        </div>
        <div class="metric-card ${zeroLTV > 0 ? 'warning' : ''}">
            <div class="metric-label">Zero LTV</div>
            <div class="metric-value">${formatNumber(zeroLTV)}</div>
            <div class="metric-subtext">${((zeroLTV/leadsData.length)*100).toFixed(1)}% of total</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Potential Revenue</div>
            <div class="metric-value">${formatCurrency(zeroLTV * avgLTV)}</div>
            <div class="metric-subtext">If zero-LTV converts</div>
        </div>
    `;
}

// Render LTV Distribution Chart
function renderLTVDistributionChart() {
    const canvas = document.getElementById('ltvDistributionChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (allCharts.ltvDistribution) {
        allCharts.ltvDistribution.destroy();
    }
    
    // Calculate distribution
    const ltvs = leadsData.map(row => parseFloat(row.LTV || 0));
    const zero = ltvs.filter(ltv => ltv === 0).length;
    const low = ltvs.filter(ltv => ltv > 0 && ltv <= 100).length;
    const mid = ltvs.filter(ltv => ltv > 100 && ltv <= 500).length;
    const high = ltvs.filter(ltv => ltv > 500).length;
    
    allCharts.ltvDistribution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['$0', '$1-$100', '$100-$500', '$500+'],
            datasets: [{
                label: 'Customers',
                data: [zero, low, mid, high],
                backgroundColor: [
                    '#dc3545',  // Red for $0
                    '#ffc107',  // Yellow for low
                    '#71BED2',  // Blue for mid
                    '#28a745'   // Green for high
                ]
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
                            const value = context.parsed.y;
                            const total = zero + low + mid + high;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${formatNumber(value)} customers (${percentage}%)`;
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

// Render First Purchase Chart
function renderFirstPurchaseChart() {
    const canvas = document.getElementById('firstPurchaseChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (allCharts.firstPurchase) {
        allCharts.firstPurchase.destroy();
    }
    
    // Calculate first purchase distribution
    const firstPurchases = {};
    const firstPurchaseLTV = {};
    
    leadsData.forEach(row => {
        const fp = row['First purchase'] || 'N/A';
        firstPurchases[fp] = (firstPurchases[fp] || 0) + 1;
        
        if (!firstPurchaseLTV[fp]) firstPurchaseLTV[fp] = [];
        firstPurchaseLTV[fp].push(parseFloat(row.LTV || 0));
    });
    
    // Get top 5 first purchase types
    const sorted = Object.entries(firstPurchases)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
    
    const labels = sorted.map(([name, ]) => name.length > 20 ? name.substring(0, 20) + '...' : name);
    const data = sorted.map(([, count]) => count);
    const avgLTVs = sorted.map(([name, ]) => {
        const ltvs = firstPurchaseLTV[name];
        return ltvs.reduce((sum, ltv) => sum + ltv, 0) / ltvs.length;
    });
    
    allCharts.firstPurchase = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Count',
                data: data,
                backgroundColor: CONFIG.settings.chartColors.primary,
                yAxisID: 'y'
            }, {
                label: 'Avg LTV',
                data: avgLTVs,
                backgroundColor: CONFIG.settings.chartColors.highlight,
                yAxisID: 'y1',
                type: 'line'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true, position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === 'Count') {
                                return `Count: ${formatNumber(context.parsed.y)}`;
                            } else {
                                return `Avg LTV: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// Continue in next file...
// Leads & Customers Analysis Module - Part 2
// Conversion funnel, alerts, and customer segmentation

// Render Conversion Funnel
function renderConversionFunnel() {
    const container = document.getElementById('conversionFunnelContainer');
    if (!container) return;
    
    const totalPeople = leadsData.length;
    const customers = leadsData.filter(row => row.Type === 'Customer').length;
    const leads = leadsData.filter(row => row.Type === 'Lead').length;
    
    const hasPurchased = leadsData.filter(row => row['First purchase'] !== 'N/A').length;
    const neverPurchased = totalPeople - hasPurchased;
    
    const ltvs = leadsData.map(row => parseFloat(row.LTV || 0));
    const hasRevenue = ltvs.filter(ltv => ltv > 0).length;
    
    const conversionRate = (customers / totalPeople * 100).toFixed(1);
    const purchaseRate = (hasPurchased / totalPeople * 100).toFixed(1);
    const revenueRate = (hasRevenue / totalPeople * 100).toFixed(1);
    
    container.innerHTML = `
        <div style="margin: 20px 0;">
            <div class="funnel-stage" style="background: linear-gradient(to right, #013160 0%, #013160 100%); padding: 25px; margin-bottom: 3px; border-radius: 8px; color: white;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 16px; opacity: 0.9; font-weight: bold;">TOTAL LEADS & CUSTOMERS</div>
                        <div style="font-size: 32px; font-weight: bold; margin-top: 8px;">${formatNumber(totalPeople)}</div>
                        <div style="font-size: 14px; margin-top: 5px; opacity: 0.8;">Everyone in your database</div>
                    </div>
                    <div style="font-size: 48px; opacity: 0.7;">👥</div>
                </div>
            </div>
            
            <div class="funnel-stage" style="background: linear-gradient(to right, #71BED2 0%, #71BED2 ${(customers/totalPeople)*100}%); padding: 25px; margin-bottom: 3px; border-radius: 8px; color: white;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 16px; opacity: 0.9; font-weight: bold;">CUSTOMERS (Converted)</div>
                        <div style="font-size: 32px; font-weight: bold; margin-top: 8px;">${formatNumber(customers)}</div>
                        <div style="font-size: 14px; margin-top: 5px; opacity: 0.8;">${conversionRate}% conversion rate | ${formatNumber(leads)} still leads</div>
                    </div>
                    <div style="font-size: 48px; opacity: 0.7;">✅</div>
                </div>
            </div>
            
            <div class="funnel-stage" style="background: linear-gradient(to right, #FBB514 0%, #FBB514 ${(hasPurchased/totalPeople)*100}%); padding: 25px; margin-bottom: 3px; border-radius: 8px; color: white;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 16px; opacity: 0.9; font-weight: bold;">MADE FIRST PURCHASE</div>
                        <div style="font-size: 32px; font-weight: bold; margin-top: 8px;">${formatNumber(hasPurchased)}</div>
                        <div style="font-size: 14px; margin-top: 5px; opacity: 0.8;">${purchaseRate}% purchase rate | ${formatNumber(neverPurchased)} never purchased</div>
                    </div>
                    <div style="font-size: 48px; opacity: 0.7;">🎫</div>
                </div>
            </div>
            
            <div class="funnel-stage" style="background: linear-gradient(to right, #28a745 0%, #28a745 ${(hasRevenue/totalPeople)*100}%); padding: 25px; border-radius: 8px; color: white;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 16px; opacity: 0.9; font-weight: bold;">GENERATING REVENUE</div>
                        <div style="font-size: 32px; font-weight: bold; margin-top: 8px;">${formatNumber(hasRevenue)}</div>
                        <div style="font-size: 14px; margin-top: 5px; opacity: 0.8;">${revenueRate}% revenue rate | ${formatNumber(totalPeople - hasRevenue)} with $0 LTV</div>
                    </div>
                    <div style="font-size: 48px; opacity: 0.7;">💰</div>
                </div>
            </div>
        </div>
        
        <div class="alert info" style="margin-top: 25px;">
            <h4>📊 Funnel Insights</h4>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                <li><strong>${conversionRate}%</strong> of people become customers (${customers} of ${totalPeople})</li>
                <li><strong>${purchaseRate}%</strong> have made at least one purchase (${hasPurchased} people)</li>
                <li><strong>${revenueRate}%</strong> are generating revenue (${hasRevenue} with LTV > $0)</li>
                <li><strong>${formatNumber(neverPurchased)} people</strong> have never made a purchase - key opportunity!</li>
            </ul>
        </div>
    `;
}

// Render Zero-LTV Alert
function renderZeroLTVAlert() {
    const container = document.getElementById('zeroLtvAlertContainer');
    if (!container) return;
    
    const ltvs = leadsData.map(row => parseFloat(row.LTV || 0));
    const avgLTV = ltvs.reduce((sum, ltv) => sum + ltv, 0) / ltvs.length;
    
    const zeroLTV = leadsData.filter(row => parseFloat(row.LTV || 0) === 0);
    const neverPurchased = zeroLTV.filter(row => row['First purchase'] === 'N/A').length;
    const purchasedButZero = zeroLTV.length - neverPurchased;
    
    const potentialRevenue = zeroLTV.length * avgLTV;
    
    const alertClass = zeroLTV.length > (leadsData.length * 0.5) ? 'warning' : 'info';
    
    container.innerHTML = `
        <div class="alert ${alertClass}" style="padding: 25px;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 20px;">
                <div>
                    <h3 style="margin: 0 0 10px 0; font-size: 24px;">⚠️ ${formatNumber(zeroLTV.length)} Customers with $0 LTV</h3>
                    <p style="margin: 0; font-size: 16px;">This represents a significant revenue opportunity for your business.</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 14px; opacity: 0.8;">Potential Revenue</div>
                    <div style="font-size: 32px; font-weight: bold; color: #28a745;">${formatCurrency(potentialRevenue)}</div>
                    <div style="font-size: 12px; opacity: 0.7;">If converted at avg LTV</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 25px 0;">
                <div style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #dc3545;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Never Purchased</div>
                    <div style="font-size: 28px; font-weight: bold; color: #dc3545;">${formatNumber(neverPurchased)}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">${((neverPurchased/zeroLTV.length)*100).toFixed(1)}% of zero-LTV</div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; font-size: 13px; color: #666;">
                        <strong>Action:</strong> Email campaign with intro offer
                    </div>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #ffc107;">
                    <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Purchased but $0 LTV</div>
                    <div style="font-size: 28px; font-weight: bold; color: #ffc107;">${formatNumber(purchasedButZero)}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">${((purchasedButZero/zeroLTV.length)*100).toFixed(1)}% of zero-LTV</div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; font-size: 13px; color: #666;">
                        <strong>Action:</strong> Verify payment data sync
                    </div>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px;">
                <h4 style="margin: 0 0 15px 0; color: #013160;">💡 Recommended Actions</h4>
                <ol style="margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li><strong>Launch Re-engagement Campaign</strong> - Target ${formatNumber(neverPurchased)} people who never purchased with a special intro offer</li>
                    <li><strong>Investigate Data Sync</strong> - ${formatNumber(purchasedButZero)} people show purchases but $0 LTV. Check payment processing.</li>
                    <li><strong>Personalized Outreach</strong> - Call or email high-potential leads individually</li>
                    <li><strong>Automated Drip Campaign</strong> - Set up automated email sequence for new leads</li>
                    <li><strong>Win-back Offers</strong> - Special pricing for inactive customers</li>
                </ol>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #e8f4f8; border-radius: 8px; border-left: 4px solid #71BED2;">
                <strong>💰 Revenue Impact:</strong> Converting just 25% of zero-LTV customers would generate approximately <strong>${formatCurrency(potentialRevenue * 0.25)}</strong> in additional revenue.
            </div>
        </div>
    `;
}

// Render Top Customers
function renderTopCustomers() {
    const container = document.getElementById('topCustomersContainer');
    if (!container) return;
    
    // Sort by LTV
    const sorted = [...leadsData].sort((a, b) => {
        const aLTV = parseFloat(a.LTV || 0);
        const bLTV = parseFloat(b.LTV || 0);
        return bLTV - aLTV;
    });
    
    const top10 = sorted.slice(0, 10);
    const top10Total = top10.reduce((sum, row) => sum + parseFloat(row.LTV || 0), 0);
    const totalLTV = leadsData.reduce((sum, row) => sum + parseFloat(row.LTV || 0), 0);
    const top10Percentage = (top10Total / totalLTV * 100).toFixed(1);
    
    let html = `
        <div style="margin-bottom: 20px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;">
                <div>
                    <div style="font-size: 14px; color: #666;">Top 10 Total</div>
                    <div style="font-size: 28px; font-weight: bold; color: #013160;">${formatCurrency(top10Total)}</div>
                </div>
                <div>
                    <div style="font-size: 14px; color: #666;">% of Total Revenue</div>
                    <div style="font-size: 28px; font-weight: bold; color: #28a745;">${top10Percentage}%</div>
                </div>
                <div>
                    <div style="font-size: 14px; color: #666;">Average LTV</div>
                    <div style="font-size: 28px; font-weight: bold; color: #71BED2;">${formatCurrency(top10Total / 10)}</div>
                </div>
            </div>
        </div>
        
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #013160; color: white;">
                    <th style="padding: 15px; text-align: left;">Rank</th>
                    <th style="padding: 15px; text-align: left;">Name</th>
                    <th style="padding: 15px; text-align: left;">Email</th>
                    <th style="padding: 15px; text-align: right;">LTV</th>
                    <th style="padding: 15px; text-align: left;">First Purchase</th>
                    ${mergedCustomerData.length > 0 ? '<th style="padding: 15px; text-align: center;">Appointments</th>' : ''}
                </tr>
            </thead>
            <tbody>
    `;
    
    top10.forEach((row, index) => {
        const name = `${row['First name'] || ''} ${row['Last name'] || ''}`.trim();
        const email = row['E-mail'] || 'N/A';
        const ltv = parseFloat(row.LTV || 0);
        const firstPurchase = (row['First purchase'] || 'N/A').substring(0, 25);
        
        // Find in merged data if available
        let appointmentCount = 'N/A';
        if (mergedCustomerData.length > 0) {
            const merged = mergedCustomerData.find(m => m['E-mail'] === row['E-mail']);
            if (merged) {
                appointmentCount = merged.appointmentCount || 0;
            }
        }
        
        const rowClass = index % 2 === 0 ? 'background: #f8f9fa;' : 'background: white;';
        
        html += `
            <tr style="${rowClass}">
                <td style="padding: 15px; font-weight: bold; color: ${index < 3 ? '#FBB514' : '#666'};">${index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}</td>
                <td style="padding: 15px; font-weight: bold;">${name}</td>
                <td style="padding: 15px; font-size: 13px; color: #666;">${email}</td>
                <td style="padding: 15px; text-align: right; font-weight: bold; color: #28a745;">${formatCurrency(ltv)}</td>
                <td style="padding: 15px; font-size: 13px;">${firstPurchase}</td>
                ${mergedCustomerData.length > 0 ? `<td style="padding: 15px; text-align: center;">${appointmentCount}</td>` : ''}
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        
        <div class="alert success" style="margin-top: 25px;">
            <h4>👑 VIP Customer Insights</h4>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                <li>Your top 10 customers generate <strong>${formatCurrency(top10Total)}</strong> (${top10Percentage}% of total revenue)</li>
                <li>Average LTV of top customers: <strong>${formatCurrency(top10Total / 10)}</strong></li>
                <li>${top10.filter(r => r['First purchase'] && r['First purchase'].toLowerCase().includes('intro')).length} of top 10 started with introductory sessions</li>
                <li>Consider creating a VIP loyalty program for high-value customers</li>
            </ul>
        </div>
    `;
    
    container.innerHTML = html;
}

// Render Customer Segmentation
function renderCustomerSegmentation() {
    const container = document.getElementById('customerSegmentationContainer');
    if (!container) return;
    
    // Segment customers by LTV
    const vip = leadsData.filter(row => parseFloat(row.LTV || 0) > 500);
    const regular = leadsData.filter(row => {
        const ltv = parseFloat(row.LTV || 0);
        return ltv > 100 && ltv <= 500;
    });
    const occasional = leadsData.filter(row => {
        const ltv = parseFloat(row.LTV || 0);
        return ltv > 0 && ltv <= 100;
    });
    const inactive = leadsData.filter(row => parseFloat(row.LTV || 0) === 0);
    
    const calculateAvg = (segment) => {
        if (segment.length === 0) return 0;
        const total = segment.reduce((sum, row) => sum + parseFloat(row.LTV || 0), 0);
        return total / segment.length;
    };
    
    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0;">
            
            <!-- VIP Customers -->
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 16px; opacity: 0.9; margin-bottom: 10px;">👑 VIP CUSTOMERS</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">${formatNumber(vip.length)}</div>
                <div style="font-size: 14px; opacity: 0.8; margin-bottom: 15px;">>$500 LTV | Avg: ${formatCurrency(calculateAvg(vip))}</div>
                <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; font-size: 13px;">
                    <strong>Characteristics:</strong><br>
                    • ${((vip.length/leadsData.length)*100).toFixed(1)}% of customer base<br>
                    • Highest engagement<br>
                    • Priority for loyalty programs
                </div>
            </div>
            
            <!-- Regular Customers -->
            <div style="background: linear-gradient(135deg, #71BED2 0%, #5a9ab3 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 16px; opacity: 0.9; margin-bottom: 10px;">✅ REGULAR CUSTOMERS</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">${formatNumber(regular.length)}</div>
                <div style="font-size: 14px; opacity: 0.8; margin-bottom: 15px;">$100-$500 LTV | Avg: ${formatCurrency(calculateAvg(regular))}</div>
                <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; font-size: 13px;">
                    <strong>Characteristics:</strong><br>
                    • ${((regular.length/leadsData.length)*100).toFixed(1)}% of customer base<br>
                    • Consistent visitors<br>
                    • Upsell opportunities
                </div>
            </div>
            
            <!-- Occasional Customers -->
            <div style="background: linear-gradient(135deg, #FBB514 0%, #f39c12 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 16px; opacity: 0.9; margin-bottom: 10px;">🔶 OCCASIONAL CUSTOMERS</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">${formatNumber(occasional.length)}</div>
                <div style="font-size: 14px; opacity: 0.8; margin-bottom: 15px;">$1-$100 LTV | Avg: ${formatCurrency(calculateAvg(occasional))}</div>
                <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; font-size: 13px;">
                    <strong>Characteristics:</strong><br>
                    • ${((occasional.length/leadsData.length)*100).toFixed(1)}% of customer base<br>
                    • Tried service once or twice<br>
                    • Re-engagement potential
                </div>
            </div>
            
            <!-- At-Risk / Inactive -->
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 16px; opacity: 0.9; margin-bottom: 10px;">⚠️ AT-RISK / INACTIVE</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">${formatNumber(inactive.length)}</div>
                <div style="font-size: 14px; opacity: 0.8; margin-bottom: 15px;">$0 LTV | Need activation</div>
                <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; font-size: 13px;">
                    <strong>Characteristics:</strong><br>
                    • ${((inactive.length/leadsData.length)*100).toFixed(1)}% of customer base<br>
                    • Never converted or inactive<br>
                    • Highest opportunity for growth
                </div>
            </div>
            
        </div>
        
        <div class="alert info" style="margin-top: 25px;">
            <h4>📊 Segmentation Strategy</h4>
            <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
                <li><strong>VIP Customers (${formatNumber(vip.length)}):</strong> Create exclusive benefits, priority booking, personalized service</li>
                <li><strong>Regular Customers (${formatNumber(regular.length)}):</strong> Encourage package purchases, refer-a-friend bonuses</li>
                <li><strong>Occasional Customers (${formatNumber(occasional.length)}):</strong> Win-back campaigns, special offers to increase frequency</li>
                <li><strong>At-Risk/Inactive (${formatNumber(inactive.length)}):</strong> Re-engagement emails, introductory pricing, limited-time offers</li>
            </ul>
        </div>
    `;
}

// Make functions available globally
window.handleLeadsFileUpload = handleLeadsFileUpload;
window.mergeCustomerData = mergeCustomerData;
window.renderCustomerAnalytics = renderCustomerAnalytics;
