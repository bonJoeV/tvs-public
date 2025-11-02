// Smart Alerts Feature Module
// Provides intelligent business recommendations

function renderAlerts() {
    const container = document.getElementById('alertsContent');
    if (!container || filteredData.length === 0) return;
    
    console.log('Rendering alerts...');
    
    const alerts = [];
    
    // Calculate metrics
    const totalRevenue = filteredData.reduce((sum, row) => sum + parseFloat(row.Revenue || 0), 0);
    const revenueGoal = CONFIG.goals.monthlyRevenue;
    const revenueProgress = totalRevenue / revenueGoal;
    
    // Revenue Alert
    if (revenueProgress < CONFIG.alerts.lowRevenueThreshold) {
        const deficit = revenueGoal - totalRevenue;
        alerts.push({
            type: 'warning',
            title: 'âš ï¸ Revenue Below Target',
            message: `Current revenue is ${(revenueProgress * 100).toFixed(0)}% of goal. You're ${CONFIG.settings.currencySymbol}${deficit.toFixed(0)} short of your monthly target.`,
            action: 'Consider increasing booking frequency or promoting higher-value services.'
        });
    } else if (revenueProgress >= 1.0) {
        alerts.push({
            type: 'success',
            title: 'âœ… Revenue Goal Achieved!',
            message: `Excellent work! You've reached ${(revenueProgress * 100).toFixed(0)}% of your monthly revenue goal.`,
            action: 'Keep up the momentum and consider setting a stretch goal.'
        });
    }
    
    // Client frequency analysis
    const clientVisits = {};
    filteredData.forEach(row => {
        const clientId = row['Client Id'] || row['Client First Name'] + row['Client Last Name'];
        clientVisits[clientId] = (clientVisits[clientId] || 0) + 1;
    });
    
    const uniqueClients = Object.keys(clientVisits).length;
    const totalAppointments = filteredData.length;
    const avgVisitsPerClient = totalAppointments / uniqueClients;
    
    if (avgVisitsPerClient < 1.5) {
        alerts.push({
            type: 'info',
            title: 'ðŸ“Š Client Retention Opportunity',
            message: `Average visits per client: ${avgVisitsPerClient.toFixed(1)}. Many clients are only visiting once.`,
            action: 'Consider implementing a follow-up campaign or loyalty program to increase repeat visits.'
        });
    }
    
    // Practitioner utilization
    const practitionerStats = {};
    filteredData.forEach(row => {
        const name = `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`;
        if (!practitionerStats[name]) {
            practitionerStats[name] = {
                appointments: 0,
                hours: 0
            };
        }
        practitionerStats[name].appointments++;
        practitionerStats[name].hours += parseFloat(row['Time (h)'] || 0);
    });
    
    Object.entries(practitionerStats).forEach(([name, stats]) => {
        const utilizationRate = stats.appointments / totalAppointments;
        if (utilizationRate < CONFIG.alerts.lowUtilizationRate && Object.keys(practitionerStats).length > 1) {
            alerts.push({
                type: 'warning',
                title: `âš ï¸ Low Utilization: ${name}`,
                message: `${name} has ${stats.appointments} appointments (${(utilizationRate * 100).toFixed(0)}% of total).`,
                action: 'Consider adjusting scheduling or marketing to balance practitioner workload.'
            });
        }
    });
    
    // Peak times analysis
    const hourCounts = {};
    filteredData.forEach(row => {
        const date = parseDate(row['Appointment Date']);
        const hour = date.getHours();
        hourCounts[hour] = (hourCounts[hour] || 0) + 1;
    });
    
    const sortedHours = Object.entries(hourCounts).sort((a, b) => b[1] - a[1]);
    if (sortedHours.length > 0) {
        const peakHour = parseInt(sortedHours[0][0]);
        const peakCount = sortedHours[0][1];
        const displayHour = peakHour > 12 ? `${peakHour - 12}pm` : `${peakHour}am`;
        
        alerts.push({
            type: 'info',
            title: 'â° Peak Time Insight',
            message: `Your busiest hour is ${displayHour} with ${peakCount} appointments.`,
            action: 'Ensure you have adequate staffing during peak hours and consider premium pricing.'
        });
    }
    
    // Revenue per location
    const locationRevenue = {};
    filteredData.forEach(row => {
        const location = row.Location || 'Unknown';
        locationRevenue[location] = (locationRevenue[location] || 0) + parseFloat(row.Revenue || 0);
    });
    
    if (Object.keys(locationRevenue).length > 1) {
        const sortedLocations = Object.entries(locationRevenue).sort((a, b) => b[1] - a[1]);
        const topLocation = sortedLocations[0];
        const bottomLocation = sortedLocations[sortedLocations.length - 1];
        
        if (topLocation[1] > bottomLocation[1] * 2) {
            alerts.push({
                type: 'info',
                title: 'ðŸ“ Location Performance Gap',
                message: `${topLocation[0]} generates ${((topLocation[1] / bottomLocation[1]) * 100).toFixed(0)}% more revenue than ${bottomLocation[0]}.`,
                action: 'Analyze what makes your top location successful and apply those strategies to other locations.'
            });
        }
    }
    
    // Render alerts
    let html = '';
    
    if (alerts.length === 0) {
        html = `
            <div class="alert success">
                <h4>âœ¨ Everything Looks Great!</h4>
                <p>Your business metrics are healthy. Keep up the excellent work!</p>
            </div>
        `;
    } else {
        alerts.forEach(alert => {
            html += `
                <div class="alert ${alert.type}">
                    <h4>${alert.title}</h4>
                    <p>${alert.message}</p>
                    ${alert.action ? `<p style="margin-top: 10px; font-weight: 600;">ðŸ’¡ ${alert.action}</p>` : ''}
                </div>
            `;
        });
    }
    
    html += `
        <p style="margin-top: 20px; padding: 15px; background: var(--gray-light); border-radius: 8px; font-size: 14px;">
            <strong>About Smart Alerts:</strong> These alerts are generated based on your data and configured thresholds. 
            Adjust alert sensitivity in <code>js/config.js</code> under <code>CONFIG.alerts</code>.
        </p>
    `;
    
    container.innerHTML = html;
}

// Auto-render when data changes
if (typeof filteredData !== 'undefined' && filteredData.length > 0) {
    renderAlerts();
}
