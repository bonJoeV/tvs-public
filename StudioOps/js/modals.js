import { exportToCSV } from './exports.js';
import { formatCurrency, parseLTV, parseDate, formatStaffName } from './utils.js';
import { filteredLeads, filteredAppointments, filteredMemberships, filteredCancellations, leadsData, membershipsData } from './data.js';
import { LTV_TIERS, CONFIG } from './config.js';

// Modal state
let currentModalData = null;

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

// Helper function - Format time for heatmap display
function formatTime(hour) {
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
    return `${displayHour}:00 ${ampm}`;
}

// Helper function - Analyze sentiment of cancellation reasons
function analyzeSentiment(reason) {
    const lowerReason = reason.toLowerCase();

    // Negative sentiment keywords
    const negativeWords = ['expensive', 'cost', 'price', 'afford', 'too much', 'financial', 'money',
                          'disappointed', 'unhappy', 'poor', 'bad', 'worst', 'terrible', 'horrible',
                          'pain', 'hurt', 'injury', 'problem', 'issue', 'dissatisfied', 'frustrat',
                          'rude', 'unprofessional', 'late', 'cancel', 'wait', 'inconvenient'];

    // Neutral sentiment keywords
    const neutralWords = ['moving', 'relocated', 'schedule', 'time', 'busy', 'travel', 'distance',
                         'far', 'changed', 'switch', 'prefer', 'different', 'other', 'work', 'job'];

    // Positive sentiment keywords (rare but possible)
    const positiveWords = ['achieved', 'goal', 'success', 'better', 'improved', 'healed', 'recovered'];

    let negativeScore = 0;
    let neutralScore = 0;
    let positiveScore = 0;

    negativeWords.forEach(word => {
        if (lowerReason.includes(word)) negativeScore++;
    });

    neutralWords.forEach(word => {
        if (lowerReason.includes(word)) neutralScore++;
    });

    positiveWords.forEach(word => {
        if (lowerReason.includes(word)) positiveScore++;
    });

    // Determine overall sentiment
    if (positiveScore > negativeScore && positiveScore > neutralScore) {
        return { sentiment: 'Positive', emoji: '😊', color: '#28a745' };
    } else if (negativeScore > neutralScore) {
        return { sentiment: 'Negative', emoji: '😞', color: '#dc3545' };
    } else {
        return { sentiment: 'Neutral', emoji: '😐', color: '#ffc107' };
    }
}

// Core Modal Functions
export function showModal(title, content, exportData = null) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    document.getElementById('dataModal').classList.add('show');
    document.body.style.overflow = 'hidden';

    // Store export data for the export button
    currentModalData = exportData;

    // Add export button if data is provided
    const modalHeader = document.querySelector('.modal-header');
    let exportBtn = document.getElementById('modalExportBtn');
    if (exportData && exportData.length > 0) {
        if (!exportBtn) {
            exportBtn = document.createElement('button');
            exportBtn.id = 'modalExportBtn';
            exportBtn.textContent = '📥 Export CSV';
            exportBtn.style.cssText = 'padding: 8px 16px; background: var(--accent); color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;';
            exportBtn.onclick = () => exportModalData();
            modalHeader.insertBefore(exportBtn, modalHeader.querySelector('.modal-close'));
        }
        exportBtn.style.display = 'inline-block';
    } else if (exportBtn) {
        exportBtn.style.display = 'none';
    }
}

function exportModalData() {
    if (currentModalData && currentModalData.length > 0) {
        const filename = 'modal-data-' + new Date().toISOString().split('T')[0] + '.csv';
        exportToCSV(currentModalData, filename);
    }
}

export function closeModal() {
    const modal = document.getElementById('dataModal');
    modal.classList.remove('show');
    modal.style.display = ''; // Clear any inline display styles
    document.body.style.overflow = 'auto';
    currentModalData = null;
}

// Initialize modal event listeners
export function initializeModalListeners() {
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// Modal Detail Functions
// Note: These functions show detailed information in modals when users click on charts or metrics

export function showLTVDetails(range, customers) {
    // Get current tier configuration
    const currentTierConfig = LTV_TIERS[CONFIG.ltvTiers];
    const ranges = currentTierConfig.ranges;

    // Helper function to parse K values
    const parseValue = (str) => {
        str = str.replace('$', '').trim();
        if (str.includes('K')) {
            return parseFloat(str.replace('K', '')) * 1000;
        }
        return parseFloat(str);
    };

    // Filter customers based on the range label
    const customersInRange = filteredLeads.filter(customer => {
        const ltv = parseLTV(customer.LTV);

        // Skip zero LTV
        if (ltv <= 0) return false;

        // Check if this is the VIP tier (has +)
        if (range.includes('+')) {
            return ltv > ranges[4];
        }

        // Parse the range from the label (e.g., "$1-$100" or "$1K-$2K")
        const parts = range.split('-');
        if (parts.length === 2) {
            const lower = parseValue(parts[0]);
            const upper = parseValue(parts[1]);

            // First tier starts at $1 (i.e., > 0)
            if (lower === 1) {
                return ltv > 0 && ltv <= upper;
            } else {
                return ltv > lower && ltv <= upper;
            }
        }

        return false;
    });

    // Get detailed info for each customer
    const customersWithDetails = customersInRange.map(c => {
        const customerEmail = c['E-mail'];
        const customerAppointments = filteredAppointments.filter(a => a['Customer Email'] === customerEmail);

        // Get latest appointment date
        let latestDate = null;
        customerAppointments.forEach(a => {
            const apptDate = parseDate(a['Appointment Date']);
            if (apptDate && (!latestDate || apptDate > latestDate)) {
                latestDate = apptDate;
            }
        });

        // Get practitioner counts
        const practitionerCounts = {};
        customerAppointments.forEach(a => {
            const firstName = a['Practitioner First Name'];
            const lastName = a['Practitioner Last Name'];
            if (firstName && lastName) {
                const key = `${firstName} ${lastName}`;
                practitionerCounts[key] = (practitionerCounts[key] || 0) + 1;
            }
        });

        // Format practitioners as "First L. (count)"
        const practitionerList = Object.entries(practitionerCounts)
            .sort((a, b) => b[1] - a[1]) // Sort by count descending
            .map(([name, count]) => {
                const parts = name.split(' ');
                const firstName = parts[0];
                const lastInitial = parts[1] ? parts[1].charAt(0) + '.' : '';
                return `${firstName} ${lastInitial} (${count})`;
            })
            .join(', ');

        return {
            ...c,
            latestDate: latestDate,
            latestDateStr: latestDate ? latestDate.toLocaleDateString('en-US') : 'N/A',
            practitionerList: practitionerList || 'N/A',
            joinDateStr: c['Join date'] ? c['Join date'].split(',')[0] : 'N/A'
        };
    });

    // Sort by latest appointment date descending (most recent first)
    customersWithDetails.sort((a, b) => {
        if (!a.latestDate) return 1;
        if (!b.latestDate) return -1;
        return b.latestDate - a.latestDate;
    });

    const totalLTV = customersWithDetails.reduce((sum, c) => sum + parseLTV(c.LTV), 0);
    const avgLTV = customersWithDetails.length > 0 ? totalLTV / customersWithDetails.length : 0;

    let tableRows = customersWithDetails.slice(0, 50).map(c => `
        <tr>
            <td class="name-cell" data-tooltip="Joined: ${c.joinDateStr}">${c['First name'] || ''} ${c['Last name'] || ''}</td>
            <td>${formatCurrency(parseLTV(c.LTV))}</td>
            <td>${c.latestDateStr}</td>
            <td>${c.practitionerList}</td>
        </tr>
    `).join('');

    if (customersWithDetails.length > 50) {
        tableRows += `<tr><td colspan="4" style="text-align: center; color: #666; font-style: italic;">Showing first 50 of ${customersWithDetails.length} customers</td></tr>`;
    }

    // Prepare CSV data
    const csvData = customersWithDetails.map(c => ({
        'Name': `${c['First name'] || ''} ${c['Last name'] || ''}`,
        'LTV': parseLTV(c.LTV),
        'Latest Visit': c.latestDateStr,
        'Join Date': c.joinDateStr,
        'Practitioners': c.practitionerList
    }));

    const content = `
        <div class="modal-highlight">
            <strong>LTV Range:</strong> ${range}<br>
            <strong>Total Customers:</strong> ${customersWithDetails.length}<br>
            <strong>Average LTV:</strong> ${formatCurrency(avgLTV)}<br>
            <strong>Total Revenue:</strong> ${formatCurrency(totalLTV)}
        </div>

        <div class="modal-section">
            <h4>Customer Details</h4>
            <p style="font-size: 12px; color: #999; margin: -10px 0 10px 0; font-style: italic;">↓ Sorted by Latest Visit (Most Recent First) | 💡 Hover over names for join date</p>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>LTV</th>
                        <th>Latest Visit</th>
                        <th>Practitioner(s)</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
            <button class="csv-export-btn" onclick='exportToCSV(${JSON.stringify(csvData)}, "ltv-distribution-${range.replace(/[^a-zA-Z0-9]/g, '-')}.csv")'>
                Export to CSV
            </button>
        </div>
    `;

    showModal(`LTV Distribution: ${range}`, content);
}

// ============================================================================
// MODAL DETAIL FUNCTIONS
// ============================================================================
// These functions are called when users click on charts or metrics to see detailed information
export function showVisitFrequencyDetails(range, count) {
    const clientVisits = {};
    const activeMemberEmails = getActiveMemberEmails();
    
    filteredAppointments.forEach(row => {
        const email = row['Customer Email'];
        if (email) {
            clientVisits[email] = (clientVisits[email] || 0) + 1;
        }
    });
    
    let clientsInRange = [];
    Object.entries(clientVisits).forEach(([email, visits]) => {
        let inRange = false;
        // Match the keys from visitDist: '1 visit', '2-3 visits', '4-6 visits', '7-10 visits', '11+ visits'
        if (range === '1 visit' && visits === 1) inRange = true;
        else if (range === '2-3 visits' && visits >= 2 && visits <= 3) inRange = true;
        else if (range === '4-6 visits' && visits >= 4 && visits <= 6) inRange = true;
        else if (range === '7-10 visits' && visits >= 7 && visits <= 10) inRange = true;
        else if (range === '11+ visits' && visits > 10) inRange = true;
        
        if (inRange) {
            const appointments = filteredAppointments.filter(a => a['Customer Email'] === email);
            // Calculate revenue excluding if they are an active member
            const customerEmail = email.toLowerCase().trim();
            const revenue = activeMemberEmails.has(customerEmail) ? 0 : 
                appointments.reduce((sum, a) => sum + (parseFloat(a.Revenue) || 0), 0);
            const customerName = appointments[0]?.['Customer Name'] || 'Unknown';
            const lastVisitDate = appointments[appointments.length - 1]?.['Appointment Date'] || 'N/A';
            
            clientsInRange.push({
                email,
                name: customerName,
                visits,
                revenue,
                lastVisit: lastVisitDate,
                lastVisitDate: parseDate(lastVisitDate)
            });
        }
    });
    
    // Sort by revenue descending by default
    clientsInRange.sort((a, b) => b.revenue - a.revenue);
    
    const totalRevenue = clientsInRange.reduce((sum, c) => sum + c.revenue, 0);
    const avgRevenue = clientsInRange.length > 0 ? totalRevenue / clientsInRange.length : 0;
    
    // Format range display
    const rangeDisplay = range; // Use the range as-is since it's already formatted
    
    let tableRows = '';
    if (clientsInRange.length === 0) {
        tableRows = '<tr><td colspan="4" style="text-align: center; color: #999; padding: 30px;">No clients found in this range</td></tr>';
    } else {
        tableRows = clientsInRange.slice(0, 50).map(c => `
            <tr>
                <td>${c.name}</td>
                <td>${c.visits}</td>
                <td>${formatCurrency(c.revenue)}</td>
                <td>${c.lastVisit.split(',')[0] || 'N/A'}</td>
            </tr>
        `).join('');
        
        if (clientsInRange.length > 50) {
            tableRows += `<tr><td colspan="4" style="text-align: center; color: #666; font-style: italic;">Showing first 50 of ${clientsInRange.length} clients</td></tr>`;
        }
    }
    
    // Prepare CSV data
    const csvData = clientsInRange.map(c => ({
        'Name': c.name,
        'Email': c.email,
        'Visits': c.visits,
        'Revenue': c.revenue,
        'Last Visit': c.lastVisit.split(',')[0] || 'N/A'
    }));
    
    const content = `
        <div class="modal-highlight">
            <strong>Visit Range:</strong> ${rangeDisplay}<br>
            <strong>Total Clients:</strong> ${clientsInRange.length}<br>
            <strong>Total Revenue:</strong> ${formatCurrency(totalRevenue)}<br>
            <strong>Average Revenue per Client:</strong> ${formatCurrency(avgRevenue)}
        </div>
        
        <div class="modal-section">
            <h4>Client Details</h4>
            <p style="font-size: 12px; color: #999; margin: -10px 0 10px 0; font-style: italic;">↓ Sorted by Revenue (Highest First)</p>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Visits</th>
                        <th>Revenue</th>
                        <th>Last Visit</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
            ${clientsInRange.length > 0 ? `<button class="csv-export-btn" onclick='exportToCSV(${JSON.stringify(csvData)}, "visit-frequency-${range.replace(/[^a-zA-Z0-9]/g, '-')}.csv")'>
                Export to CSV
            </button>` : ''}
        </div>
    `;
    
    showModal(`Visit Frequency: ${rangeDisplay}`, content);
}
export function showPractitionerDetails(practitionerName) {
    const appointments = filteredAppointments.filter(row => {
        return `${row['Practitioner First Name']} ${row['Practitioner Last Name']}` === practitionerName;
    });
    
    const revenue = appointments.reduce((sum, a) => sum + (parseFloat(a.Revenue) || 0), 0);
    const payout = appointments.reduce((sum, a) => sum + (parseFloat(a['Total Payout']) || 0), 0);
    const uniqueClients = new Set(appointments.map(a => a['Customer Email'])).size;
    
    // Service breakdown
    const services = {};
    appointments.forEach(a => {
        const service = a.Appointment;
        if (!services[service]) {
            services[service] = { count: 0, revenue: 0 };
        }
        services[service].count++;
        services[service].revenue += parseFloat(a.Revenue) || 0;
    });
    
    const sortedServices = Object.entries(services)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 10);
    
    const serviceRows = sortedServices.map(([service, data]) => `
        <tr>
            <td>${service}</td>
            <td>${data.count}</td>
            <td>${formatCurrency(data.revenue)}</td>
            <td>${formatCurrency(data.revenue / data.count)}</td>
        </tr>
    `).join('');
    
    // Prepare CSV data
    const csvData = sortedServices.map(([service, data]) => ({
        'Service': service,
        'Count': data.count,
        'Revenue': data.revenue,
        'Avg per Appt': data.revenue / data.count
    }));
    
    const content = `
        <div class="modal-highlight">
            <strong>Practitioner:</strong> ${practitionerName}<br>
            <strong>Total Appointments:</strong> ${appointments.length}<br>
            <strong>Unique Clients:</strong> ${uniqueClients}<br>
            <strong>Total Revenue:</strong> ${formatCurrency(revenue)}<br>
            <strong>Total Payout:</strong> ${formatCurrency(payout)}<br>
            <strong>Avg Revenue per Appointment:</strong> ${formatCurrency(revenue / appointments.length)}
        </div>
        
        <div class="modal-section">
            <h4>Service Breakdown</h4>
            <p style="font-size: 12px; color: #999; margin: -10px 0 10px 0; font-style: italic;">↓ Sorted by Appointment Count (Highest First)</p>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Count</th>
                        <th>Revenue</th>
                        <th>Avg per Appt</th>
                    </tr>
                </thead>
                <tbody>
                    ${serviceRows}
                </tbody>
            </table>
            <button class="csv-export-btn" onclick='exportToCSV(${JSON.stringify(csvData)}, "practitioner-${practitionerName.replace(/[^a-zA-Z0-9]/g, '-')}.csv")'>
                Export to CSV
            </button>
        </div>
    `;
    
    showModal(`Practitioner: ${practitionerName}`, content);
}
export function showServiceDetails(serviceName) {
    const appointments = filteredAppointments.filter(row => row.Appointment === serviceName);
    
    const revenue = appointments.reduce((sum, a) => sum + (parseFloat(a.Revenue) || 0), 0);
    const uniqueClients = new Set(appointments.map(a => a['Customer Email'])).size;
    const avgRevenue = appointments.length > 0 ? revenue / appointments.length : 0;
    
    // Practitioner breakdown
    const practitioners = {};
    appointments.forEach(a => {
        const name = `${a['Practitioner First Name']} ${a['Practitioner Last Name']}`;
        if (!practitioners[name]) {
            practitioners[name] = { count: 0, revenue: 0 };
        }
        practitioners[name].count++;
        practitioners[name].revenue += parseFloat(a.Revenue) || 0;
    });
    
    const sortedPractitioners = Object.entries(practitioners)
        .sort((a, b) => b[1].count - a[1].count);
    
    const practitionerRows = sortedPractitioners.map(([name, data]) => `
        <tr>
            <td>${name}</td>
            <td>${data.count}</td>
            <td>${formatCurrency(data.revenue)}</td>
            <td>${((data.count / appointments.length) * 100).toFixed(1)}%</td>
        </tr>
    `).join('');
    
    // Prepare CSV data
    const csvData = sortedPractitioners.map(([name, data]) => ({
        'Practitioner': name,
        'Appointments': data.count,
        'Revenue': data.revenue,
        '% of Total': ((data.count / appointments.length) * 100).toFixed(1)
    }));
    
    const content = `
        <div class="modal-highlight">
            <strong>Service:</strong> ${serviceName}<br>
            <strong>Total Appointments:</strong> ${appointments.length}<br>
            <strong>Unique Clients:</strong> ${uniqueClients}<br>
            <strong>Total Revenue:</strong> ${formatCurrency(revenue)}<br>
            <strong>Avg Revenue per Appointment:</strong> ${formatCurrency(avgRevenue)}
        </div>
        
        <div class="modal-section">
            <h4>Practitioner Breakdown</h4>
            <p style="font-size: 12px; color: #999; margin: -10px 0 10px 0; font-style: italic;">↓ Sorted by Appointment Count (Highest First)</p>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Practitioner</th>
                        <th>Appointments</th>
                        <th>Revenue</th>
                        <th>% of Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${practitionerRows}
                </tbody>
            </table>
            <button class="csv-export-btn" onclick='exportToCSV(${JSON.stringify(csvData)}, "service-${serviceName.replace(/[^a-zA-Z0-9]/g, '-')}.csv")'>
                Export to CSV
            </button>
        </div>
    `;
    
    showModal(`Service: ${serviceName}`, content);
}
export function showDayOfWeekDetails(dayName, location = null) {
    const dayAppointments = filteredAppointments.filter(row => {
        const date = parseDate(row['Appointment Date']);
        if (!date) return false;
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const matchesDay = days[date.getDay()] === dayName;
        const matchesLocation = !location || row.Location === location;
        return matchesDay && matchesLocation;
    });
    
    const revenue = dayAppointments.reduce((sum, a) => sum + (parseFloat(a.Revenue) || 0), 0);
    const uniqueClients = new Set(dayAppointments.map(a => a['Customer Email'])).size;
    
    // Hour breakdown
    const hourBreakdown = {};
    dayAppointments.forEach(a => {
        const date = parseDate(a['Appointment Date']);
        if (date) {
            const hour = date.getHours();
            if (!hourBreakdown[hour]) {
                hourBreakdown[hour] = { count: 0, revenue: 0 };
            }
            hourBreakdown[hour].count++;
            hourBreakdown[hour].revenue += parseFloat(a.Revenue) || 0;
        }
    });
    
    const sortedHours = Object.entries(hourBreakdown)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 10);
    
    const hourRows = sortedHours.map(([hour, data]) => {
        const hourNum = parseInt(hour);
        const ampm = hourNum >= 12 ? 'PM' : 'AM';
        const displayHour = hourNum > 12 ? hourNum - 12 : (hourNum === 0 ? 12 : hourNum);
        return `
            <tr>
                <td>${displayHour}:00 ${ampm}</td>
                <td>${data.count}</td>
                <td>${formatCurrency(data.revenue)}</td>
                <td>${formatCurrency(data.revenue / data.count)}</td>
            </tr>
        `;
    }).join('');
    
    // Prepare CSV data
    const csvData = sortedHours.map(([hour, data]) => {
        const hourNum = parseInt(hour);
        const ampm = hourNum >= 12 ? 'PM' : 'AM';
        const displayHour = hourNum > 12 ? hourNum - 12 : (hourNum === 0 ? 12 : hourNum);
        return {
            'Hour': `${displayHour}:00 ${ampm}`,
            'Appointments': data.count,
            'Revenue': data.revenue,
            'Avg Revenue': data.revenue / data.count
        };
    });
    
    const content = `
        <div class="modal-highlight">
            ${location ? `<strong>Location:</strong> ${location}<br>` : ''}
            <strong>Day:</strong> ${dayName}<br>
            <strong>Total Appointments:</strong> ${dayAppointments.length}<br>
            <strong>Unique Clients:</strong> ${uniqueClients}<br>
            <strong>Total Revenue:</strong> ${formatCurrency(revenue)}<br>
            <strong>Avg Revenue per Appointment:</strong> ${formatCurrency(revenue / dayAppointments.length)}
        </div>
        
        <div class="modal-section">
            <h4>Peak Hours on ${dayName}${location ? ` at ${location}` : ''}</h4>
            <p style="font-size: 12px; color: #999; margin: -10px 0 10px 0; font-style: italic;">↓ Sorted by Appointment Count (Highest First)</p>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Hour</th>
                        <th>Appointments</th>
                        <th>Revenue</th>
                        <th>Avg Revenue</th>
                    </tr>
                </thead>
                <tbody>
                    ${hourRows}
                </tbody>
            </table>
            <button class="csv-export-btn" onclick='exportToCSV(${JSON.stringify(csvData)}, "${dayName.toLowerCase()}-peak-hours.csv")'>
                Export to CSV
            </button>
        </div>
    `;
    
    showModal(`${dayName} Performance${location ? ` - ${location}` : ''}`, content);
}
export function showHourDetails(dayName, hour, location = null) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayIndex = days.indexOf(dayName);
    
    // Filter appointments for this specific day of week and hour
    const hourAppointments = filteredAppointments.filter(row => {
        const date = parseDate(row['Appointment Date']);
        if (!date) return false;
        const matchesTime = date.getDay() === dayIndex && date.getHours() === hour;
        const matchesLocation = !location || row.Location === location;
        return matchesTime && matchesLocation;
    });
    
    if (hourAppointments.length === 0) {
        showModal(`${dayName} ${hour}:00`, `<p>No appointments found for this time slot.</p>`);
        return;
    }
    
    const revenue = hourAppointments.reduce((sum, a) => sum + (parseFloat(a.Revenue) || 0), 0);
    const uniqueClients = new Set(hourAppointments.map(a => a['Customer Email'])).size;
    
    // Create detailed appointment list
    const appointmentRows = hourAppointments.map(appt => {
        const date = parseDate(appt['Appointment Date']);
        const dateStr = date ? date.toLocaleDateString() : 'N/A';
        const customerName = appt['Customer Name'] || 'Unknown';
        const revenue = parseFloat(appt.Revenue) || 0;
        const service = appt['Appointment'] || 'Unknown';
        const practitioner = `${appt['Practitioner First Name'] || ''} ${appt['Practitioner Last Name'] || ''}`.trim() || 'Unknown';
        
        return `
            <tr>
                <td>${dateStr}</td>
                <td>${customerName}</td>
                <td>${formatCurrency(revenue)}</td>
                <td style="font-size: 0.85em;">${service.substring(0, 30)}${service.length > 30 ? '...' : ''}</td>
                <td>${practitioner}</td>
            </tr>
        `;
    }).join('');
    
    // Prepare CSV data
    const csvData = hourAppointments.map(appt => {
        const date = parseDate(appt['Appointment Date']);
        return {
            'Date': date ? date.toLocaleDateString() : 'N/A',
            'Customer Name': appt['Customer Name'] || 'Unknown',
            'Customer Email': appt['Customer Email'] || 'N/A',
            'Revenue': parseFloat(appt.Revenue) || 0,
            'Service': appt['Appointment'] || 'Unknown',
            'Practitioner': `${appt['Practitioner First Name'] || ''} ${appt['Practitioner Last Name'] || ''}`.trim() || 'Unknown',
            'Duration (h)': appt['Time (h)'] || 'N/A'
        };
    });
    
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
    
    const content = `
        <div class="modal-highlight">
            ${location ? `<strong>Location:</strong> ${location}<br>` : ''}
            <strong>Time Slot:</strong> ${dayName}s at ${displayHour}:00 ${ampm}<br>
            <strong>Total Appointments:</strong> ${hourAppointments.length}<br>
            <strong>Unique Clients:</strong> ${uniqueClients}<br>
            <strong>Total Revenue:</strong> ${formatCurrency(revenue)}<br>
            <strong>Avg Revenue per Appointment:</strong> ${formatCurrency(revenue / hourAppointments.length)}
        </div>
        
        <div class="modal-section">
            <h4>All Appointments at This Time</h4>
            <p style="font-size: 12px; color: #999; margin: -10px 0 10px 0; font-style: italic;">↓ Showing all ${dayName} appointments at ${displayHour}:00 ${ampm}${location ? ` at ${location}` : ''}</p>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Customer</th>
                        <th>Revenue</th>
                        <th>Service</th>
                        <th>VSP</th>
                    </tr>
                </thead>
                <tbody>
                    ${appointmentRows}
                </tbody>
            </table>
            <button class="csv-export-btn" onclick='exportToCSV(${JSON.stringify(csvData)}, "${dayName.toLowerCase()}-${hour}00-appointments.csv")'>
                Export to CSV
            </button>
        </div>
    `;
    
    showModal(`${dayName} ${displayHour}:00 ${ampm} - Appointments`, content);
}
export function showRetentionDetails(segment, count) {
    const clientVisits = {};
    filteredAppointments.forEach(row => {
        const email = row['Customer Email'];
        if (email) {
            clientVisits[email] = (clientVisits[email] || 0) + 1;
        }
    });
    
    let clientsInSegment = [];
    Object.entries(clientVisits).forEach(([email, visits]) => {
        const isOneTime = visits === 1;
        const isReturning = visits > 1;
        
        if ((segment === 'One-Time Visitors' && isOneTime) || 
            (segment === 'Returning Clients' && isReturning)) {
            const appointments = filteredAppointments.filter(a => a['Customer Email'] === email);
            const revenue = appointments.reduce((sum, a) => sum + (parseFloat(a.Revenue) || 0), 0);
            const customerName = appointments[0]?.['Customer Name'] || 'Unknown';
            const firstVisit = appointments[0]?.['Appointment Date'] || 'N/A';
            const lastVisit = appointments[appointments.length - 1]?.['Appointment Date'] || 'N/A';
            
            clientsInSegment.push({
                email,
                name: customerName,
                visits,
                revenue,
                firstVisit,
                lastVisit
            });
        }
    });
    
    clientsInSegment.sort((a, b) => b.revenue - a.revenue);
    
    const totalRevenue = clientsInSegment.reduce((sum, c) => sum + c.revenue, 0);
    const avgRevenue = clientsInSegment.length > 0 ? totalRevenue / clientsInSegment.length : 0;
    
    let tableRows = clientsInSegment.slice(0, 50).map(c => `
        <tr>
            <td>${c.name}</td>
            <td>${c.email}</td>
            <td>${c.visits}</td>
            <td>${formatCurrency(c.revenue)}</td>
            <td>${c.firstVisit.split(',')[0] || 'N/A'}</td>
            <td>${c.lastVisit.split(',')[0] || 'N/A'}</td>
        </tr>
    `).join('');
    
    if (clientsInSegment.length > 50) {
        tableRows += `<tr><td colspan="6" style="text-align: center; color: #666; font-style: italic;">Showing first 50 of ${clientsInSegment.length} clients</td></tr>`;
    }
    
    // Prepare CSV data
    const csvData = clientsInSegment.map(c => ({
        'Name': c.name,
        'Email': c.email,
        'Visits': c.visits,
        'Revenue': c.revenue,
        'First Visit': c.firstVisit.split(',')[0] || 'N/A',
        'Last Visit': c.lastVisit.split(',')[0] || 'N/A'
    }));
    
    const content = `
        <div class="modal-highlight">
            <strong>Segment:</strong> ${segment}<br>
            <strong>Total Clients:</strong> ${clientsInSegment.length}<br>
            <strong>Total Revenue:</strong> ${formatCurrency(totalRevenue)}<br>
            <strong>Average Revenue per Client:</strong> ${formatCurrency(avgRevenue)}
        </div>
        
        <div class="modal-section">
            <h4>Client Details (Sorted by Revenue)</h4>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Visits</th>
                        <th>Revenue</th>
                        <th>First Visit</th>
                        <th>Last Visit</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
            <button class="csv-export-btn" onclick='exportToCSV(${JSON.stringify(csvData)}, "${segment.replace(/[^a-zA-Z0-9]/g, '-')}.csv")'>
                Export to CSV
            </button>
        </div>
    `;
    
    showModal(segment, content);
}
export function showSegmentDetails(segmentName, segmentData) {
    if (segmentData.length === 0) {
        alert('No clients in this segment.');
        return;
    }
    
    // Sort by LTV descending
    const sortedData = [...segmentData].sort((a, b) => b.ltv - a.ltv);
    const totalLTV = sortedData.reduce((sum, c) => sum + c.ltv, 0);
    const avgLTV = totalLTV / sortedData.length;
    const totalVisits = sortedData.reduce((sum, c) => sum + c.totalVisits, 0);
    const totalMembershipRevenue = sortedData.reduce((sum, c) => sum + (c.membershipAmount || 0), 0);
    
    // Determine if this is the inactive paid member segment
    const isInactivePaidSegment = segmentName.includes('Inactive Paid');
    
    let tableRows = sortedData.slice(0, 100).map((client, i) => {
        let extraInfo = '';
        if (client.daysSinceLastVisit !== undefined) {
            extraInfo = `${client.daysSinceLastVisit} days ago`;
        } else if (client.visitsPerWeek !== undefined) {
            extraInfo = `${client.visitsPerWeek.toFixed(1)}/week`;
        } else {
            extraInfo = client.lastVisitDate ? client.lastVisitDate.toLocaleDateString() : 'N/A';
        }
        
        const membershipInfo = client.membershipName ? `${client.membershipName}<br><small>${formatCurrency(client.membershipAmount)}/mo</small>` : 'None';
        
        return `
            <tr>
                <td>${i + 1}</td>
                <td>${client.firstName} ${client.lastName}</td>
                <td>${client.email}</td>
                <td><strong>${formatCurrency(client.ltv)}</strong></td>
                <td>${client.totalVisits}</td>
                ${isInactivePaidSegment ? `<td>${membershipInfo}</td>` : ''}
                <td>${extraInfo}</td>
            </tr>
        `;
    }).join('');
    
    if (sortedData.length > 100) {
        tableRows += `<tr><td colspan="${isInactivePaidSegment ? 7 : 6}" style="text-align: center; color: #666; font-style: italic;">Showing first 100 of ${sortedData.length} clients. Download CSV for complete list.</td></tr>`;
    }
    
    const modalBody = `
        <div class="modal-section">
            <h4>📊 ${segmentName} Segment Overview</h4>
            <div class="modal-highlight">
                <strong>Total Clients:</strong> ${formatNumber(sortedData.length)}<br>
                <strong>Total LTV:</strong> ${formatCurrency(totalLTV)}<br>
                <strong>Average LTV:</strong> ${formatCurrency(avgLTV)}<br>
                <strong>Total Visits:</strong> ${formatNumber(totalVisits)}
                ${isInactivePaidSegment ? `<br><strong>Monthly Membership Revenue:</strong> ${formatCurrency(totalMembershipRevenue)}` : ''}
            </div>
        </div>
        
        <div class="modal-section">
            <h4>👥 Client List</h4>
            <button class="csv-export-btn" onclick="downloadSegmentCSV('${segmentName}', currentSegmentData)" style="margin-bottom: 15px;">
                Download Complete List
            </button>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>LTV</th>
                        <th>Visits</th>
                        ${isInactivePaidSegment ? '<th>Membership</th>' : ''}
                        <th>Additional Info</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
    
    // Store current segment data globally for download
    window.currentSegmentData = segmentData;
    
    document.getElementById('modalTitle').textContent = `${segmentName} Segment Details`;
    document.getElementById('modalBody').innerHTML = modalBody;
    document.getElementById('dataModal').classList.add('show');
}
export function showCancellationReasonDetails(reason, count) {
    const cancellationsWithReason = filteredCancellations.filter(c => {
        const cancelReason = (c['Reason'] || '').trim();
        const reasonKey = cancelReason.split('>')[0].trim() || cancelReason;
        return reasonKey === reason;
    });
    
    // Get detailed info with membership data
    const detailedCancellations = cancellationsWithReason.map(c => {
        const membershipId = c['Membership ID'];
        let membershipValue = 0;
        let membershipType = c['Membership'] || 'Unknown';
        
        if (membershipId && membershipsData) {
            const matchingMembership = membershipsData.find(m => m['Membership ID'] === membershipId);
            if (matchingMembership) {
                membershipValue = parseFloat(matchingMembership['Paid Amount']) || 0;
            }
        }
        
        // Try different possible field names for customer name
        const firstName = c['First name'] || c['First Name'] || c['Customer First Name'] || '';
        const lastName = c['Last name'] || c['Last Name'] || c['Customer Last Name'] || '';
        const fullName = c['Customer Name'] || c['Name'] || '';
        const customerName = fullName || `${firstName} ${lastName}`.trim();
        
        return {
            customerName: customerName || 'Unknown',
            email: c['Email'] || c['E-mail'] || c['Customer Email'] || 'N/A',
            membership: membershipType,
            value: membershipValue,
            cancelledAt: c['Cancelled at'] || 'N/A',
            location: c['Home location'] || 'Unknown',
            fullReason: c['Reason'] || reason,
            improvements: c['Possible improvements'] || 'None provided'
        };
    });
    
    // Sort by value descending
    detailedCancellations.sort((a, b) => b.value - a.value);
    
    const totalValue = detailedCancellations.reduce((sum, c) => sum + c.value, 0);
    const avgValue = totalValue / count;
    
    const sentiment = analyzeSentiment(reason);
    
    let content = `
        <div class="modal-highlight" style="border-left: 4px solid ${sentiment.color};">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <div style="flex: 1;">
                    <strong>Reason:</strong> ${reason}<br>
                    <strong>Sentiment:</strong> ${sentiment.emoji} ${sentiment.sentiment}
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: bold; color: ${sentiment.color};">${count}</div>
                    <div style="font-size: 12px; color: #666;">cancellations</div>
                </div>
            </div>
            <strong>Total Lost Revenue:</strong> ${formatCurrency(totalValue)}<br>
            <strong>Average Per Cancellation:</strong> ${formatCurrency(avgValue)}
        </div>
        
        <div class="modal-section">
            <h4>Cancelled Customers (${count})</h4>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Membership</th>
                        <th>Value</th>
                        <th>Location</th>
                        <th>Cancelled</th>
                        <th>Feedback</th>
                    </tr>
                </thead>
                <tbody>
                    ${detailedCancellations.map(c => `
                        <tr>
                            <td>
                                <strong>${c.customerName || 'Unknown'}</strong><br>
                                <span style="font-size: 11px; color: #666;">${c.email}</span>
                            </td>
                            <td>${c.membership}</td>
                            <td><strong>${formatCurrency(c.value)}</strong></td>
                            <td>${c.location}</td>
                            <td style="font-size: 12px;">${c.cancelledAt}</td>
                            <td style="font-size: 12px; max-width: 200px;">${c.improvements.substring(0, 100)}${c.improvements.length > 100 ? '...' : ''}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    showModal(`Cancellation Reason: ${reason}`, content);
}

// Show Cancellation Type Details Modal
export function showCancellationTypeDetails(type, count) {
    const cancellationsOfType = filteredCancellations.filter(c => {
        const membershipType = c['Membership'] || 'Unknown';
        return membershipType === type;
    });
    
    const detailedCancellations = cancellationsOfType.map(c => {
        let membershipValue = 0;
        
        // Match by Customer Email instead of Membership ID
        const customerEmail = (c['Email'] || c['E-mail'] || c['Customer Email'] || '').toLowerCase().trim();
        if (customerEmail && membershipsData) {
            const matchingMemberships = membershipsData.filter(m => 
                (m['Customer Email'] || '').toLowerCase().trim() === customerEmail
            );
            if (matchingMemberships.length > 0) {
                // Sort by date and get most recent
                const sortedMemberships = matchingMemberships.sort((a, b) => {
                    const dateA = a['Bought Date/Time (GMT)'] ? new Date(a['Bought Date/Time (GMT)']) : new Date(0);
                    const dateB = b['Bought Date/Time (GMT)'] ? new Date(b['Bought Date/Time (GMT)']) : new Date(0);
                    return dateB - dateA;
                });
                // Use Paid Amount as monthly value
                membershipValue = parseFloat(sortedMemberships[0]['Paid Amount']) || 0;
            }
        }
        
        // Try different possible field names for customer name
        const firstName = c['First name'] || c['First Name'] || c['Customer First Name'] || '';
        const lastName = c['Last name'] || c['Last Name'] || c['Customer Last Name'] || '';
        const fullName = c['Customer Name'] || c['Name'] || '';
        const customerName = fullName || `${firstName} ${lastName}`.trim();
        
        return {
            customerName: customerName || 'Unknown',
            email: c['Email'] || c['E-mail'] || c['Customer Email'] || 'N/A',
            value: membershipValue,
            cancelledAt: c['Cancelled at'] || 'N/A',
            location: c['Home location'] || 'Unknown',
            reason: (c['Reason'] || '').split('>')[0].trim() || 'Not provided'
        };
    });
    
    detailedCancellations.sort((a, b) => b.value - a.value);
    
    const totalValue = detailedCancellations.reduce((sum, c) => sum + c.value, 0);
    
    let content = `
        <div class="modal-highlight">
            <strong>Membership Type:</strong> ${type}<br>
            <strong>Total Cancellations:</strong> ${count}<br>
            <strong>Total Lost Revenue:</strong> ${formatCurrency(totalValue)}
        </div>
        
        <div class="modal-section">
            <h4>Cancelled Members (${count})</h4>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Value</th>
                        <th>Location</th>
                        <th>Cancelled</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    ${detailedCancellations.map(c => `
                        <tr>
                            <td>
                                <strong>${c.customerName || 'Unknown'}</strong><br>
                                <span style="font-size: 11px; color: #666;">${c.email}</span>
                            </td>
                            <td><strong>${formatCurrency(c.value)}</strong></td>
                            <td>${c.location}</td>
                            <td style="font-size: 12px;">${c.cancelledAt}</td>
                            <td style="font-size: 12px;">${c.reason}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    showModal(`Cancellations: ${type}`, content);
}

// Show Cancellation Location Details Modal
export function showCancellationLocationDetails(location, count) {
    const cancellationsAtLocation = filteredCancellations.filter(c => {
        const loc = c['Home location'] || 'Unknown';
        return loc === location;
    });
    
    const detailedCancellations = cancellationsAtLocation.map(c => {
        let membershipValue = 0;
        
        // Match by Customer Email instead of Membership ID
        const customerEmail = (c['Email'] || c['E-mail'] || c['Customer Email'] || '').toLowerCase().trim();
        if (customerEmail && membershipsData) {
            const matchingMemberships = membershipsData.filter(m => 
                (m['Customer Email'] || '').toLowerCase().trim() === customerEmail
            );
            if (matchingMemberships.length > 0) {
                // Sort by date and get most recent
                const sortedMemberships = matchingMemberships.sort((a, b) => {
                    const dateA = a['Bought Date/Time (GMT)'] ? new Date(a['Bought Date/Time (GMT)']) : new Date(0);
                    const dateB = b['Bought Date/Time (GMT)'] ? new Date(b['Bought Date/Time (GMT)']) : new Date(0);
                    return dateB - dateA;
                });
                // Use Paid Amount as monthly value
                membershipValue = parseFloat(sortedMemberships[0]['Paid Amount']) || 0;
            }
        }
        
        // Try different possible field names for customer name
        const firstName = c['First name'] || c['First Name'] || c['Customer First Name'] || '';
        const lastName = c['Last name'] || c['Last Name'] || c['Customer Last Name'] || '';
        const fullName = c['Customer Name'] || c['Name'] || '';
        const customerName = fullName || `${firstName} ${lastName}`.trim();
        
        return {
            customerName: customerName || 'Unknown',
            email: c['Email'] || c['E-mail'] || c['Customer Email'] || 'N/A',
            membership: c['Membership'] || 'Unknown',
            value: membershipValue,
            cancelledAt: c['Cancelled at'] || 'N/A',
            reason: (c['Reason'] || '').split('>')[0].trim() || 'Not provided'
        };
    });
    
    detailedCancellations.sort((a, b) => b.value - a.value);
    
    const totalValue = detailedCancellations.reduce((sum, c) => sum + c.value, 0);
    
    let content = `
        <div class="modal-highlight">
            <strong>Location:</strong> ${location}<br>
            <strong>Total Cancellations:</strong> ${count}<br>
            <strong>Total Lost Revenue:</strong> ${formatCurrency(totalValue)}
        </div>
        
        <div class="modal-section">
            <h4>Cancelled Members at ${location} (${count})</h4>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Membership</th>
                        <th>Value</th>
                        <th>Cancelled</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    ${detailedCancellations.map(c => `
                        <tr>
                            <td>
                                <strong>${c.customerName || 'Unknown'}</strong><br>
                                <span style="font-size: 11px; color: #666;">${c.email}</span>
                            </td>
                            <td>${c.membership}</td>
                            <td><strong>${formatCurrency(c.value)}</strong></td>
                            <td style="font-size: 12px;">${c.cancelledAt}</td>
                            <td style="font-size: 12px;">${c.reason.substring(0, 40)}${c.reason.length > 40 ? '...' : ''}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    showModal(`Cancellations: ${location}`, content);
}

// Show Cancellation Month Details Modal
export function showCancellationMonthDetails(monthKey, count) {
    const [year, month] = monthKey.split('-');
    const monthName = new Date(year, parseInt(month) - 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    
    const cancellationsInMonth = filteredCancellations.filter(c => {
        const cancelledAt = c['Cancelled at'];
        if (cancelledAt) {
            const dateParts = cancelledAt.split(',')[0];
            const cancelDate = new Date(dateParts);
            if (!isNaN(cancelDate.getTime())) {
                const cancelMonthKey = `${cancelDate.getFullYear()}-${String(cancelDate.getMonth() + 1).padStart(2, '0')}`;
                return cancelMonthKey === monthKey;
            }
        }
        return false;
    });
    
    const detailedCancellations = cancellationsInMonth.map(c => {
        let membershipValue = 0;
        
        // Match by Customer Email instead of Membership ID
        const customerEmail = (c['Email'] || c['E-mail'] || c['Customer Email'] || '').toLowerCase().trim();
        if (customerEmail && membershipsData) {
            const matchingMemberships = membershipsData.filter(m => 
                (m['Customer Email'] || '').toLowerCase().trim() === customerEmail
            );
            if (matchingMemberships.length > 0) {
                // Sort by date and get most recent
                const sortedMemberships = matchingMemberships.sort((a, b) => {
                    const dateA = a['Bought Date/Time (GMT)'] ? new Date(a['Bought Date/Time (GMT)']) : new Date(0);
                    const dateB = b['Bought Date/Time (GMT)'] ? new Date(b['Bought Date/Time (GMT)']) : new Date(0);
                    return dateB - dateA;
                });
                // Use Paid Amount as monthly value
                membershipValue = parseFloat(sortedMemberships[0]['Paid Amount']) || 0;
            }
        }
        
        // Try different possible field names for customer name
        const firstName = c['First name'] || c['First Name'] || c['Customer First Name'] || '';
        const lastName = c['Last name'] || c['Last Name'] || c['Customer Last Name'] || '';
        const fullName = c['Customer Name'] || c['Name'] || '';
        const customerName = fullName || `${firstName} ${lastName}`.trim();
        
        return {
            customerName: customerName || 'Unknown',
            email: c['Email'] || c['E-mail'] || c['Customer Email'] || 'N/A',
            membership: c['Membership'] || 'Unknown',
            value: membershipValue,
            cancelledAt: c['Cancelled at'] || 'N/A',
            location: c['Home location'] || 'Unknown',
            reason: (c['Reason'] || '').split('>')[0].trim() || 'Not provided'
        };
    });
    
    detailedCancellations.sort((a, b) => b.value - a.value);
    
    const totalValue = detailedCancellations.reduce((sum, c) => sum + c.value, 0);
    
    let content = `
        <div class="modal-highlight">
            <strong>Month:</strong> ${monthName}<br>
            <strong>Total Cancellations:</strong> ${count}<br>
            <strong>Total Lost Revenue:</strong> ${formatCurrency(totalValue)}
        </div>
        
        <div class="modal-section">
            <h4>Cancellations in ${monthName} (${count})</h4>
            <table class="modal-table">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Membership</th>
                        <th>Value</th>
                        <th>Location</th>
                        <th>Cancelled</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    ${detailedCancellations.map(c => `
                        <tr>
                            <td>
                                <strong>${c.customerName || 'Unknown'}</strong><br>
                                <span style="font-size: 11px; color: #666;">${c.email}</span>
                            </td>
                            <td>${c.membership}</td>
                            <td><strong>${formatCurrency(c.value)}</strong></td>
                            <td>${c.location}</td>
                            <td style="font-size: 12px;">${c.cancelledAt}</td>
                            <td style="font-size: 12px;">${c.reason.substring(0, 30)}${c.reason.length > 30 ? '...' : ''}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    showModal(`Cancellations: ${monthName}`, content);
}

// CLIENT JOURNEY VISUALIZATION TAB
export function showJourneyDetails(stage, count) {
    let title, content;
    
    switch(stage) {
        case 'leads':
            title = 'Total Contacts';
            content = `<p>You have <strong>${formatNumber(count)}</strong> total people in your database.</p>
                       <p>These include both leads (prospects) and customers (people who have made at least one purchase).</p>`;
            break;
        case 'customers':
            title = 'Converted Customers';
            content = `<p><strong>${formatNumber(count)}</strong> people have become customers.</p>
                       <p>These are contacts who have made at least one appointment or purchase.</p>`;
            break;
        case 'intro':
            title = 'Tried Intro Offer';
            content = `<p><strong>${formatNumber(count)}</strong> customers tried an introductory offer.</p>
                       <p>Intro offers are a great way to let new clients experience your services at a lower barrier to entry.</p>`;
            break;
        case 'purchase':
            title = 'Made First Purchase';
            content = `<p><strong>${formatNumber(count)}</strong> customers made a paid purchase (non-intro).</p>
                       <p>This is a critical conversion point - they've decided to pay full price for your services.</p>`;
            break;
        case 'repeat':
            title = 'Repeat Customers (2+ visits)';
            content = `<p><strong>${formatNumber(count)}</strong> customers have visited multiple times.</p>
                       <p>Repeat customers are your foundation - they've experienced your value and come back for more.</p>`;
            break;
        case 'loyal':
            title = 'Loyal Customers (5+ visits)';
            content = `<p><strong>${formatNumber(count)}</strong> customers are loyal regulars with 5+ visits.</p>
                       <p>These are your MVPs! They trust you, love your services, and likely refer others.</p>`;
            break;
    }
    
    showModal(title, content);
}

// CHART RENDERING FUNCTIONS
// Helper function to calculate trendline using linear regression
export function showLeadsTimelineDetails(date, leads, location) {
    if (!leads || leads.length === 0) return;
    
    const dateObj = new Date(date);
    const formattedDate = `${String(dateObj.getMonth() + 1).padStart(2, '0')}/${String(dateObj.getDate()).padStart(2, '0')}/${dateObj.getFullYear()}`;
    
    let html = `<h3>${location} - ${formattedDate}</h3>`;
    html += `<p style="margin: 10px 0; color: #666;"><strong>${formatNumber(leads.length)}</strong> lead(s) joined on this date</p>`;
    
    // Count converted vs not converted
    const converted = leads.filter(l => {
        const convertedTo = (l['Converted to'] || '').trim();
        return convertedTo && convertedTo !== 'N/A' && convertedTo !== '';
    }).length;
    
    html += `<p style="margin: 10px 0;"><strong>Converted:</strong> ${converted} of ${leads.length} (${((converted/leads.length)*100).toFixed(1)}%)</p>`;
    
    html += '<div class="table-container" style="max-height: 400px; overflow-y: auto;">';
    html += '<table><thead><tr>';
    html += '<th>Name</th><th>Source</th><th>Converted To</th><th>LTV</th>';
    html += '</tr></thead><tbody>';
    
    leads.forEach(lead => {
        const convertedTo = lead['Converted to'] || 'N/A';
        const isConverted = convertedTo !== 'N/A';
        const ltv = parseLTV(lead['LTV']);
        
        html += '<tr>';
        html += `<td>${lead['First Name']} ${lead['Last Name']}</td>`;
        html += `<td>${lead['Lead source'] || 'Unknown'}</td>`;
        html += `<td><span style="padding: 4px 8px; border-radius: 4px; background: ${isConverted ? '#d4edda' : '#f8d7da'}; color: ${isConverted ? '#155724' : '#721c24'};">${convertedTo}</span></td>`;
        html += `<td>${formatCurrency(ltv)}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    // Add summary stats
    const totalLTV = leads.reduce((sum, l) => sum + (parseLTV(l['LTV'])), 0);
    const avgLTV = converted > 0 ? totalLTV / converted : 0;
    
    html += `<div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">`;
    html += `<strong>Summary:</strong> Total LTV: ${formatCurrency(totalLTV)} | Avg LTV: ${formatCurrency(avgLTV)}`;
    html += `</div>`;
    
    showModal(`Leads Details: ${location} - ${formattedDate}`, html);
}

// Show lead details when clicking on source chart
export function showLeadsSourceDetails(source, leads) {
    if (!leads || leads.length === 0) return;
    
    let html = `<h3>Leads from: ${source}</h3>`;
    html += `<p style="margin: 10px 0; color: #666;"><strong>${formatNumber(leads.length)}</strong> lead(s) from this source</p>`;
    
    // Count converted vs not converted
    const converted = leads.filter(l => {
        const convertedTo = (l['Converted to'] || (l['Type'] === 'Customer' ? 'Yes' : '')).trim();
        return convertedTo && convertedTo !== 'N/A' && convertedTo !== '';
    }).length;
    
    html += `<p style="margin: 10px 0;"><strong>Converted:</strong> ${converted} of ${leads.length} (${((converted/leads.length)*100).toFixed(1)}%)</p>`;
    
    // Group by location
    const byLocation = {};
    leads.forEach(l => {
        const location = l['Home location'] || 'Unknown';
        if (!byLocation[location]) byLocation[location] = 0;
        byLocation[location]++;
    });
    
    // Sort leads by date descending
    const sortedLeads = [...leads].sort((a, b) => {
        const dateA = parseDate(a['Converted'] || a['Join date']);
        const dateB = parseDate(b['Converted'] || b['Join date']);
        if (!dateA && !dateB) return 0;
        if (!dateA) return 1;
        if (!dateB) return -1;
        return dateB - dateA; // Descending
    });
    
    html += '<div class="table-container" style="max-height: 400px; overflow-y: auto;">';
    html += '<table><thead><tr>';
    html += '<th>Name</th><th>Date</th><th>Converted To</th><th>LTV</th>';
    html += '</tr></thead><tbody>';
    
    sortedLeads.forEach(lead => {
        const convertedTo = lead['Converted to'] || (lead['Type'] === 'Customer' ? 'Customer' : 'Lead');
        const isConverted = lead['Type'] === 'Customer' || (convertedTo !== 'N/A' && convertedTo !== 'Lead');
        const ltv = parseLTV(lead['LTV']);
        const date = parseDate(lead['Converted'] || lead['Join date']);
        const dateStr = date ? `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}/${date.getFullYear()}` : 'N/A';
        
        html += '<tr>';
        html += `<td>${lead['First Name'] || lead['First name'] || ''} ${lead['Last Name'] || lead['Last name'] || ''}</td>`;
        html += `<td>${dateStr}</td>`;
        html += `<td><span style="padding: 4px 8px; border-radius: 4px; background: ${isConverted ? '#d4edda' : '#f8d7da'}; color: ${isConverted ? '#155724' : '#721c24'};">${convertedTo}</span></td>`;
        html += `<td>${formatCurrency(ltv)}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    // Add summary stats with location breakdown
    const totalLTV = leads.reduce((sum, l) => sum + (parseLTV(l['LTV'])), 0);
    const avgLTV = converted > 0 ? totalLTV / converted : 0;
    
    // Sort locations by count descending
    const sortedLocations = Object.entries(byLocation).sort((a, b) => b[1] - a[1]);
    
    html += `<div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">`;
    html += `<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 15px;">`;
export function showLocationHeatmapDetails(location, day, hour) {
    if (!window.sfHeatmapData || !window.sfHeatmapData[location] || 
        !window.sfHeatmapData[location][day] || !window.sfHeatmapData[location][day][hour]) return;
    
    const leadsInCell = window.sfHeatmapData[location][day][hour];
    if (leadsInCell.length === 0) return;
    
    let html = `<h3>${location} - ${day} at ${formatTime(hour)}</h3>`;
    html += `<p style="margin: 10px 0; color: #666;"><strong>${formatNumber(leadsInCell.length)}</strong> SocialFitness lead(s) generated during this time</p>`;
    
    // Count converted vs not converted
    const converted = leadsInCell.filter(l => {
        const convertedTo = (l['Converted to'] || '').trim();
        return convertedTo && convertedTo !== 'N/A' && convertedTo !== '';
    }).length;
    
    html += `<p style="margin: 10px 0;"><strong>Converted:</strong> ${converted} of ${leadsInCell.length} (${((converted/leadsInCell.length)*100).toFixed(1)}%)</p>`;
    
    html += '<div class="table-container" style="max-height: 400px; overflow-y: auto;">';
    html += '<table><thead><tr>';
    html += '<th>Name</th><th>Date</th><th>Source</th><th>Converted To</th><th>LTV</th>';
    html += '</tr></thead><tbody>';
    
    leadsInCell.forEach(lead => {
        const convertedTo = lead['Converted to'] || 'N/A';
        const isConverted = convertedTo !== 'N/A';
        const ltv = parseLTV(lead['LTV']);
        const dateField = parseDate(lead['Converted']);
        const dateStr = dateField ? `${String(dateField.getMonth() + 1).padStart(2, '0')}/${String(dateField.getDate()).padStart(2, '0')}/${String(dateField.getFullYear()).slice(-2)}` : 'N/A';
        
        html += '<tr>';
        html += `<td>${lead['First Name']} ${lead['Last Name']}</td>`;
        html += `<td>${dateStr}</td>`;
        html += `<td>${lead['Lead source'] || 'Unknown'}</td>`;
        html += `<td><span style="padding: 4px 8px; border-radius: 4px; background: ${isConverted ? '#d4edda' : '#f8d7da'}; color: ${isConverted ? '#155724' : '#721c24'};">${convertedTo}</span></td>`;
        html += `<td>${formatCurrency(ltv)}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    // Add summary stats
    const totalLTV = leadsInCell.reduce((sum, l) => sum + (parseLTV(l['LTV'])), 0);
    const avgLTV = converted > 0 ? totalLTV / converted : 0;
    
    html += `<div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">`;
    html += `<strong>Summary:</strong> Total LTV: ${formatCurrency(totalLTV)} | Avg LTV: ${formatCurrency(avgLTV)}`;
    html += `</div>`;
    
    showModal(`SocialFitness Leads: ${location} - ${day} at ${formatTime(hour)}`, html);
}

// Render appointment heatmap for a specific location
export function showApptHeatmapDetails(location, day, hour) {
    if (!window.apptHeatmapData || !window.apptHeatmapData[location] || 
        !window.apptHeatmapData[location][day] || !window.apptHeatmapData[location][day][hour]) return;
    
    const apptsInCell = window.apptHeatmapData[location][day][hour];
    if (apptsInCell.length === 0) return;
    
    const activeMemberEmails = getActiveMemberEmails();
    
    let html = `<h3>${location} - ${day} at ${formatTime(hour)}</h3>`;
    html += `<p style="margin: 10px 0; color: #666;"><strong>${formatNumber(apptsInCell.length)}</strong> appointment(s) during this time</p>`;
    
    // Calculate stats
    const totalRevenue = apptsInCell.reduce((sum, a) => {
        const email = (a['Customer Email'] || '').toLowerCase().trim();
        const revenue = parseFloat(a.Revenue || 0);
        return sum + (activeMemberEmails.has(email) ? 0 : revenue);
    }, 0);
    const totalPayout = apptsInCell.reduce((sum, a) => sum + parseFloat(a['Total Payout'] || 0), 0);
    const profit = totalRevenue - totalPayout;
    
    html += `<p style="margin: 10px 0;">
        <strong>Revenue:</strong> ${formatCurrency(totalRevenue)} | 
        <strong>Payout:</strong> ${formatCurrency(totalPayout)} | 
        <strong>Profit:</strong> ${formatCurrency(profit)}
    </p>`;
    
    html += '<div class="table-container" style="max-height: 400px; overflow-y: auto;">';
    html += '<table><thead><tr>';
    html += '<th>Time</th><th>Customer</th><th>Service</th><th>VSP</th><th>Revenue</th>';
    html += '</tr></thead><tbody>';
    
    apptsInCell.forEach(appt => {
        const dateField = parseDate(appt['Appointment Date']);
        const time = dateField ? dateField.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : 'N/A';
        const email = (appt['Customer Email'] || '').toLowerCase().trim();
        const revenue = parseFloat(appt.Revenue || 0);
        const displayRevenue = activeMemberEmails.has(email) ? 0 : revenue;
        
        html += '<tr>';
        html += `<td>${time}</td>`;
        html += `<td>${appt['Customer First Name']} ${appt['Customer Last Name']}</td>`;
        html += `<td>${appt.Appointment}</td>`;
        html += `<td>${appt['Practitioner First Name']} ${appt['Practitioner Last Name']}</td>`;
        html += `<td>${formatCurrency(displayRevenue)}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    showModal(`Appointments: ${location} - ${day} at ${formatTime(hour)}`, html);
}

export function showHeatmapDetails(day, hour) {
    if (!window.leadsHeatmapData || !window.leadsHeatmapData[day] || !window.leadsHeatmapData[day][hour]) return;
    
    const leadsInCell = window.leadsHeatmapData[day][hour];
    if (leadsInCell.length === 0) return;
    
    const hasConvertedData = leadsInCell[0]['Lead source'] !== undefined;
    
    let html = `<h3>${day} at ${formatTime(hour)}</h3>`;
    html += `<p style="margin: 10px 0; color: #666;"><strong>${formatNumber(leadsInCell.length)}</strong> lead(s) generated during this time</p>`;
    
    // Count converted vs not converted
    let converted = 0;
    leadsInCell.forEach(lead => {
        if (hasConvertedData) {
            const convertedTo = (lead['Converted to'] || '').trim();
            if (convertedTo && convertedTo !== 'N/A' && convertedTo !== '') {
                converted++;
            }
        } else {
            const type = (lead['Type'] || '').toLowerCase();
            if (type === 'customer') converted++;
        }
    });
    
    html += `<p style="margin: 10px 0;"><strong>Converted:</strong> ${converted} of ${leadsInCell.length} (${((converted/leadsInCell.length)*100).toFixed(1)}%)</p>`;
    
    html += '<div class="table-container" style="max-height: 400px; overflow-y: auto;">';
    html += '<table><thead><tr>';
    html += '<th>Name</th><th>Date/Time</th><th>Source</th>';
    if (hasConvertedData) {
        html += '<th>Converted To</th><th>LTV</th>';
    } else {
        html += '<th>Type</th>';
    }
    html += '</tr></thead><tbody>';
    
    leadsInCell.forEach(lead => {
        html += '<tr>';
        html += `<td>${lead['First Name'] || ''} ${lead['Last Name'] || ''}</td>`;
        
        let dateField = null;
        if (hasConvertedData) {
            dateField = parseDate(lead['Converted']);
        } else {
            dateField = parseDate(lead['Join date']);
        }
        
        const formattedDate = dateField ? `${String(dateField.getMonth() + 1).padStart(2, '0')}/${String(dateField.getDate()).padStart(2, '0')}/${String(dateField.getFullYear()).slice(-2)}` : 'N/A';
        html += `<td>${formattedDate}</td>`;
        
        if (hasConvertedData) {
            html += `<td>${lead['Lead source'] || 'Unknown'}</td>`;
            const convertedTo = lead['Converted to'] || 'N/A';
            const isConverted = convertedTo !== 'N/A';
            html += `<td><span style="padding: 4px 8px; border-radius: 4px; background: ${isConverted ? '#d4edda' : '#f8d7da'}; color: ${isConverted ? '#155724' : '#721c24'};">${convertedTo}</span></td>`;
            html += `<td>${formatCurrency(parseLTV(lead['LTV']))}</td>`;
        } else {
            html += `<td>${lead['Aggregator'] || 'Unknown'}</td>`;
