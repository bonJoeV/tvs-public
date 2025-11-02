// Client Retention Feature Module
// Analyze repeat visits and client loyalty

function renderClientRetention() {
    const container = document.getElementById('clientRetentionContainer');
    if (!container || filteredData.length === 0) return;
    
    console.log('Rendering client retention analysis...');
    
    // Analyze client visits
    const clientVisits = {};
    const clientRevenue = {};
    
    filteredData.forEach(row => {
        const clientName = row['Customer Name'] || 'Unknown';
        const clientEmail = row['Customer E-mail'] || '';
        const clientId = clientEmail || clientName; // Use email as unique ID, fallback to name
        
        if (!clientVisits[clientId]) {
            clientVisits[clientId] = {
                name: clientName,
                visits: 0,
                revenue: 0,
                firstVisit: parseDate(row['Appointment Date']),
                lastVisit: parseDate(row['Appointment Date'])
            };
        }
        
        clientVisits[clientId].visits++;
        clientVisits[clientId].revenue += parseFloat(row.Revenue || 0);
        
        const visitDate = parseDate(row['Appointment Date']);
        if (visitDate < clientVisits[clientId].firstVisit) {
            clientVisits[clientId].firstVisit = visitDate;
        }
        if (visitDate > clientVisits[clientId].lastVisit) {
            clientVisits[clientId].lastVisit = visitDate;
        }
    });
    
    // Calculate metrics
    const totalClients = Object.keys(clientVisits).length;
    const repeatingClients = Object.values(clientVisits).filter(c => c.visits > 1).length;
    const retentionRate = totalClients > 0 ? (repeatingClients / totalClients * 100) : 0;
    const avgVisitsPerClient = totalClients > 0 
        ? Object.values(clientVisits).reduce((sum, c) => sum + c.visits, 0) / totalClients 
        : 0;
    
    // Get top clients
    const topClients = Object.values(clientVisits)
        .sort((a, b) => b.revenue - a.revenue)
        .slice(0, 20);
    
    // Visit frequency distribution
    const visitFrequency = { '1': 0, '2-3': 0, '4-5': 0, '6-10': 0, '10+': 0 };
    Object.values(clientVisits).forEach(client => {
        if (client.visits === 1) visitFrequency['1']++;
        else if (client.visits <= 3) visitFrequency['2-3']++;
        else if (client.visits <= 5) visitFrequency['4-5']++;
        else if (client.visits <= 10) visitFrequency['6-10']++;
        else visitFrequency['10+']++;
    });
    
    let html = `
        <div class="metrics-grid" style="margin-bottom: 30px;">
            <div class="metric-card">
                <div class="metric-label">Total Clients</div>
                <div class="metric-value">${totalClients}</div>
                <div class="metric-subtext">Unique clients</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Retention Rate</div>
                <div class="metric-value">${retentionRate.toFixed(1)}%</div>
                <div class="metric-subtext">${repeatingClients} returning clients</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Visits</div>
                <div class="metric-value">${avgVisitsPerClient.toFixed(1)}</div>
                <div class="metric-subtext">Per client</div>
            </div>
        </div>
        
        <div style="margin-bottom: 30px;">
            <h3 style="margin-bottom: 15px; color: var(--primary);">Visit Frequency Distribution</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                <div style="background: var(--gray-light); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: var(--primary);">${visitFrequency['1']}</div>
                    <div style="color: #666; font-size: 14px;">1 Visit</div>
                </div>
                <div style="background: var(--gray-light); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: var(--primary);">${visitFrequency['2-3']}</div>
                    <div style="color: #666; font-size: 14px;">2-3 Visits</div>
                </div>
                <div style="background: var(--gray-light); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: var(--primary);">${visitFrequency['4-5']}</div>
                    <div style="color: #666; font-size: 14px;">4-5 Visits</div>
                </div>
                <div style="background: var(--gray-light); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: var(--primary);">${visitFrequency['6-10']}</div>
                    <div style="color: #666; font-size: 14px;">6-10 Visits</div>
                </div>
                <div style="background: var(--gray-light); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: var(--primary);">${visitFrequency['10+']}</div>
                    <div style="color: #666; font-size: 14px;">10+ Visits</div>
                </div>
            </div>
        </div>
        
        <h3 style="margin-bottom: 15px; color: var(--primary);">Top 20 Clients by Revenue</h3>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Client Name</th>
                    <th>Visits</th>
                    <th>Total Revenue</th>
                    <th>Avg per Visit</th>
                    <th>First Visit</th>
                    <th>Last Visit</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    topClients.forEach((client, index) => {
        const avgPerVisit = client.visits > 0 ? client.revenue / client.visits : 0;
        html += `
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td>${client.name}</td>
                <td>${client.visits}</td>
                <td>${CONFIG.settings.currencySymbol}${client.revenue.toFixed(2)}</td>
                <td>${CONFIG.settings.currencySymbol}${avgPerVisit.toFixed(2)}</td>
                <td>${client.firstVisit.toLocaleDateString()}</td>
                <td>${client.lastVisit.toLocaleDateString()}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        
        <div class="alert info" style="margin-top: 20px;">
            <h4>ðŸ’¡ Retention Insights</h4>
            <p>
                ${retentionRate >= 50 
                    ? 'âœ… Great retention! Over half your clients return for additional sessions.' 
                    : 'âš ï¸ Consider implementing a follow-up program to increase repeat visits.'}
            </p>
            <p style="margin-top: 10px;">
                <strong>Recommendations:</strong><br>
                â€¢ Follow up with one-time visitors within 2 weeks<br>
                â€¢ Create a loyalty program for 5+ visit clients<br>
                â€¢ Send reminder emails for clients who haven't visited in 60+ days
            </p>
        </div>
    `;
    
    container.innerHTML = html;
}

// Auto-render when data changes
if (typeof filteredData !== 'undefined' && filteredData.length > 0) {
    renderClientRetention();
}
