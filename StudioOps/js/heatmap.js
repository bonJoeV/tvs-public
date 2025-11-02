// Heatmap Feature Module
// Shows appointment density by day and hour

function renderHeatmap() {
    const container = document.getElementById('heatmapContainer');
    if (!container || filteredData.length === 0) return;
    
    console.log('Rendering heatmap...');
    
    // Create heatmap data structure
    const heatmapData = {};
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    // Initialize structure
    days.forEach(day => {
        heatmapData[day] = {};
        for (let hour = 6; hour <= 21; hour++) {
            heatmapData[day][hour] = 0;
        }
    });
    
    // Populate with appointment data
    filteredData.forEach(row => {
        const date = parseDate(row['Appointment Date']);
        const dayName = days[date.getDay()];
        
        // Try to get hour from appointment time or date
        let hour = date.getHours();
        
        // If hour is 0 (midnight), try to parse from a time field if it exists
        if (hour === 0 && row['Appointment Time']) {
            const timeMatch = row['Appointment Time'].match(/(\d{1,2}):(\d{2})/);
            if (timeMatch) {
                hour = parseInt(timeMatch[1]);
            }
        }
        
        if (heatmapData[dayName] && heatmapData[dayName][hour] !== undefined) {
            heatmapData[dayName][hour]++;
        }
    });
    
    // Find max value for scaling
    let maxValue = 0;
    Object.values(heatmapData).forEach(dayData => {
        Object.values(dayData).forEach(count => {
            if (count > maxValue) maxValue = count;
        });
    });
    
    // Render heatmap table
    let html = '<table class="heatmap-table"><thead><tr><th>Day</th>';
    
    for (let hour = 6; hour <= 21; hour++) {
        const displayHour = hour > 12 ? `${hour - 12}pm` : (hour === 12 ? '12pm' : `${hour}am`);
        html += `<th>${displayHour}</th>`;
    }
    html += '</tr></thead><tbody>';
    
    days.forEach(day => {
        html += `<tr><td><strong>${day}</strong></td>`;
        
        for (let hour = 6; hour <= 21; hour++) {
            const count = heatmapData[day][hour];
            const intensity = maxValue > 0 ? Math.ceil((count / maxValue) * 7) : 0;
            const className = `heatmap-cell heatmap-${intensity}`;
            
            html += `<td class="${className}" title="${day} ${hour}:00 - ${count} appointments">${count}</td>`;
        }
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    html += '<p style="margin-top: 15px; color: #666; font-size: 14px;">';
    html += '<strong>Tip:</strong> Darker colors indicate busier times. Use this to optimize scheduling and staffing.';
    html += '</p>';
    
    container.innerHTML = html;
}

// Auto-render when data changes
if (typeof filteredData !== 'undefined' && filteredData.length > 0) {
    renderHeatmap();
}
