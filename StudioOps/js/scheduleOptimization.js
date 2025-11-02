// Schedule Optimization Feature Module
// Analyze scheduling efficiency and identify gaps

function renderScheduleOptimization() {
    const container = document.getElementById('scheduleOptContainer');
    if (!container || filteredData.length === 0) return;
    
    console.log('Rendering schedule optimization...');
    
    // Group appointments by practitioner and date
    const practitionerSchedules = {};
    
    filteredData.forEach(row => {
        const practitioner = `${row['Practitioner First Name']} ${row['Practitioner Last Name']}`;
        const date = parseDate(row['Appointment Date']);
        const dateKey = date.toLocaleDateString();
        
        if (!practitionerSchedules[practitioner]) {
            practitionerSchedules[practitioner] = {};
        }
        
        if (!practitionerSchedules[practitioner][dateKey]) {
            practitionerSchedules[practitioner][dateKey] = [];
        }
        
        practitionerSchedules[practitioner][dateKey].push({
            time: date,
            duration: parseFloat(row['Time (h)'] || 0),
            revenue: parseFloat(row.Revenue || 0),
            service: row['Appointment'] || 'Unknown'
        });
    });
    
    // Calculate efficiency metrics
    const efficiencyData = [];
    let totalGaps = 0;
    let totalGapMinutes = 0;
    let totalWorkingHours = 0;
    
    Object.entries(practitionerSchedules).forEach(([practitioner, dates]) => {
        Object.entries(dates).forEach(([date, appointments]) => {
            // Sort by time
            appointments.sort((a, b) => a.time - b.time);
            
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
            
            if (appointments.length > 1) {
                efficiencyData.push({
                    practitioner,
                    date,
                    appointments: appointments.length,
                    gaps: dayGaps,
                    gapMinutes: dayGapMinutes,
                    workingHours: dayWorkingHours,
                    utilizationRate
                });
            }
        });
    });
    
    // Sort by most gaps
    efficiencyData.sort((a, b) => b.gapMinutes - a.gapMinutes);
    
    // Calculate overall metrics
    const avgGapMinutes = efficiencyData.length > 0 ? totalGapMinutes / totalGaps : 0;
    const overallUtilization = totalWorkingHours > 0 
        ? ((totalWorkingHours - (totalGapMinutes / 60)) / totalWorkingHours * 100) 
        : 0;
    const potentialRevenue = (totalGapMinutes / 60) * 150; // Assuming $150/hour average
    
    let html = `
        <div class="metrics-grid" style="margin-bottom: 30px;">
            <div class="metric-card">
                <div class="metric-label">Schedule Efficiency</div>
                <div class="metric-value">${overallUtilization.toFixed(1)}%</div>
                <div class="metric-subtext">Overall utilization</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Gaps</div>
                <div class="metric-value">${totalGaps}</div>
                <div class="metric-subtext">${(totalGapMinutes / 60).toFixed(1)} hours of gaps</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Gap Duration</div>
                <div class="metric-value">${avgGapMinutes.toFixed(0)} min</div>
                <div class="metric-subtext">Per gap</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Potential Revenue</div>
                <div class="metric-value">${CONFIG.settings.currencySymbol}${potentialRevenue.toFixed(0)}</div>
                <div class="metric-subtext">From filling gaps</div>
            </div>
        </div>
        
        <h3 style="margin-bottom: 15px; color: var(--primary);">Days with Largest Scheduling Gaps</h3>
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
    `;
    
    efficiencyData.slice(0, 20).forEach(day => {
        const potentialForDay = (day.gapMinutes / 60) * 150;
        const utilizationClass = day.utilizationRate >= 80 ? 'success' : (day.utilizationRate >= 60 ? 'warning' : 'danger');
        
        html += `
            <tr>
                <td>${day.practitioner}</td>
                <td>${day.date}</td>
                <td>${day.appointments}</td>
                <td>${day.gaps}</td>
                <td>${day.gapMinutes.toFixed(0)} min</td>
                <td><span style="color: ${day.utilizationRate >= 80 ? 'var(--success)' : (day.utilizationRate >= 60 ? 'var(--warning)' : 'var(--danger)')}">${day.utilizationRate.toFixed(1)}%</span></td>
                <td>${CONFIG.settings.currencySymbol}${potentialForDay.toFixed(0)}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        
        <div class="alert ${overallUtilization >= 80 ? 'success' : (overallUtilization >= 60 ? 'warning' : 'info')}" style="margin-top: 20px;">
            <h4>ðŸ“Š Schedule Optimization Insights</h4>
            <p>
                ${overallUtilization >= 80 
                    ? 'âœ… Excellent scheduling efficiency! Your practitioners have minimal gaps.' 
                    : overallUtilization >= 60
                    ? 'âš ï¸ Good scheduling, but there are opportunities to fill gaps and increase revenue.'
                    : 'ðŸ“ˆ Significant scheduling gaps detected. Optimizing could substantially increase revenue.'}
            </p>
            <p style="margin-top: 10px;">
                <strong>Recommendations:</strong><br>
                â€¢ Offer discounted "fill-in" appointments for last-minute bookings<br>
                â€¢ Block schedule appointments closer together when possible<br>
                â€¢ Consider adding express services (30-45 min) to fill small gaps<br>
                â€¢ Review practitioner availability patterns to match demand<br>
                â€¢ Potential additional revenue: ${CONFIG.settings.currencySymbol}${potentialRevenue.toFixed(0)} by filling gaps
            </p>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: var(--gray-light); border-radius: 8px; font-size: 14px;">
            <strong>ðŸ’¡ How to improve scheduling:</strong><br>
            â€¢ Gaps over 15 minutes are opportunities for additional appointments<br>
            â€¢ Target 80%+ utilization rate for optimal efficiency<br>
            â€¢ Back-to-back appointments maximize revenue potential<br>
            â€¢ Consider practitioner preferences and client needs when optimizing
        </div>
    `;
    
    container.innerHTML = html;
}

// Auto-render when data changes
if (typeof filteredData !== 'undefined' && filteredData.length > 0) {
    renderScheduleOptimization();
}
