// Goals Tracking Feature Module
// Track progress toward revenue and appointment goals

// Number formatting helper
function formatNumber(num) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function formatCurrency(num) {
    return CONFIG.settings.currencySymbol + formatNumber(num);
}

function renderGoals() {
    const container = document.getElementById('goalsContent');
    if (!container || filteredData.length === 0) return;
    
    console.log('Rendering goals...');
    
    // Calculate current metrics
    const totalRevenue = filteredData.reduce((sum, row) => sum + parseFloat(row.Revenue || 0), 0);
    const totalAppointments = filteredData.length;
    const avgRevenuePerAppt = totalAppointments > 0 ? totalRevenue / totalAppointments : 0;
    
    // Get goals from config
    const revenueGoal = CONFIG.goals.monthlyRevenue;
    const appointmentGoal = CONFIG.goals.monthlyAppointments;
    const avgRevenueGoal = CONFIG.goals.avgRevenuePerAppt;
    
    // Calculate progress percentages
    const revenueProgress = (totalRevenue / revenueGoal) * 100;
    const appointmentProgress = (totalAppointments / appointmentGoal) * 100;
    const avgRevenueProgress = (avgRevenuePerAppt / avgRevenueGoal) * 100;
    
    // Calculate remaining needs
    const revenueNeeded = Math.max(0, revenueGoal - totalRevenue);
    const apptsNeeded = Math.max(0, appointmentGoal - totalAppointments);
    const targetPerAppt = apptsNeeded > 0 ? revenueNeeded / apptsNeeded : 0;
    
    let html = `
        <div style="margin-bottom: 30px;">
            <div class="goal-header">
                <span>Revenue Goal</span>
                <span>${formatCurrency(totalRevenue)} / ${formatCurrency(revenueGoal)}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(revenueProgress, 100)}%">
                    ${revenueProgress.toFixed(0)}%
                </div>
            </div>
        </div>
        
        <div style="margin-bottom: 30px;">
            <div class="goal-header">
                <span>Appointment Goal</span>
                <span>${formatNumber(totalAppointments)} / ${formatNumber(appointmentGoal)}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(appointmentProgress, 100)}%">
                    ${appointmentProgress.toFixed(0)}%
                </div>
            </div>
        </div>
        
        <div style="margin-bottom: 30px;">
            <div class="goal-header">
                <span>Avg Revenue per Appointment</span>
                <span>${formatCurrency(avgRevenuePerAppt)} / ${formatCurrency(avgRevenueGoal)}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(avgRevenueProgress, 100)}%">
                    ${avgRevenueProgress.toFixed(0)}%
                </div>
            </div>
        </div>
        
        <div class="alert ${revenueProgress >= 100 ? 'success' : (revenueProgress >= 80 ? 'warning' : 'info')}" style="margin-top: 20px;">
            <h4>Progress Summary 📈</h4>
            <p>
                ${revenueProgress >= 100 ? '🎉 Congratulations! You\'ve exceeded your revenue goal!' :
                  revenueProgress >= 80 ? '💪 Great progress! You\'re on track to meet your goal.' :
                  '📈 Keep going! You\'re building momentum.'}
            </p>
            <p style="margin-top: 10px; font-size: 14px;">
                <strong>To reach your goals:</strong><br>
                • Need ${formatCurrency(revenueNeeded)} more in revenue<br>
                • Need ${formatNumber(apptsNeeded)} more appointments<br>
                • Target ${formatCurrency(revenueNeeded)} / ${formatNumber(apptsNeeded)} = ${formatCurrency(targetPerAppt)} per remaining appointment
            </p>
        </div>
        
        <p style="margin-top: 20px; padding: 15px; background: var(--gray-light); border-radius: 8px; font-size: 14px;">
            <strong>💡 Tip:</strong> Edit goal values in <code>js/config.js</code> under <code>CONFIG.goals</code>
        </p>
    `;
    
    container.innerHTML = html;
}

// Auto-render when data changes
if (typeof filteredData !== 'undefined' && filteredData.length > 0) {
    renderGoals();
}
