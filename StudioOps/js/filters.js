import { parseDate } from './utils.js';
import {
    appointmentsData, leadsData, leadsConvertedData, membershipsData, membershipCancellationsData,
    setFilteredAppointments, setFilteredMemberships, setFilteredLeads, setFilteredLeadsConverted,
    setFilteredCancellations, setFilteredTimeTracking,
    filteredAppointments
} from './data.js';

// Populate Filter Dropdowns
export function populateFilters() {
    const months = new Set();
    const locations = new Set();
    const practitioners = new Set();
    const services = new Set();

    appointmentsData.forEach(row => {
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
    practitionerFilter.innerHTML = '<option value="all">All VSPs</option>';
    Array.from(practitioners).sort().forEach(prac => {
        practitionerFilter.innerHTML += `<option value="${prac}">${prac}</option>`;
    });

    // Populate service filter
    const serviceFilter = document.getElementById('serviceFilter');
    serviceFilter.innerHTML = '<option value="all">All Services</option>';
    Array.from(services).sort().forEach(service => {
        serviceFilter.innerHTML += `<option value="${service}">${service}</option>`;
    });

    // Add event listeners
    ['monthFilter', 'locationFilter', 'practitionerFilter', 'serviceFilter', 'startDate', 'endDate'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => applyFilters());
    });
}

// Display Active Filters
export function displayActiveFilters() {
    const month = document.getElementById('monthFilter').value;
    const location = document.getElementById('locationFilter').value;
    const practitioner = document.getElementById('practitionerFilter').value;
    const service = document.getElementById('serviceFilter').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    let badges = [];

    if (month !== 'all') {
        const [year, mon] = month.split('-');
        const date = new Date(year, mon - 1);
        const label = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        badges.push(label);
    }
    if (location !== 'all') badges.push(location);
    if (practitioner !== 'all') badges.push(practitioner);
    if (service !== 'all') badges.push(service.substring(0, 30));
    if (startDate && endDate) badges.push(`${startDate} to ${endDate}`);
    else if (startDate) badges.push(`From ${startDate}`);
    else if (endDate) badges.push(`Until ${endDate}`);

    const display = document.getElementById('activeFiltersDisplay');
    if (badges.length > 0) {
        display.innerHTML = '<strong>Active Filters:</strong> ' +
            badges.map(b => `<span class="filter-badge">${b}</span>`).join('');
        display.classList.add('show');
    } else {
        display.classList.remove('show');
    }
}

// Recalculate Utilization Based on Filtered Data
export function recalculateUtilization() {
    if (!window.timeTrackingData || window.timeTrackingData.length === 0) {
        return; // No time tracking data available
    }

    const month = document.getElementById('monthFilter').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    // Filter time tracking data by the same date range as appointments
    const filteredTimeTracking = window.timeTrackingData.filter(row => {
        const clockedIn = row['Clocked in'] ? new Date(row['Clocked in']) : null;
        if (!clockedIn) return false;

        // Month filter
        if (month !== 'all') {
            const rowMonth = `${clockedIn.getFullYear()}-${String(clockedIn.getMonth() + 1).padStart(2, '0')}`;
            if (rowMonth !== month) return false;
        }

        // Date range filters
        if (startDate && clockedIn < new Date(startDate)) return false;
        if (endDate && clockedIn > new Date(endDate)) return false;

        return true;
    });

    // Recalculate utilization for each employee based on filtered data
    const employeeUtilization = {};

    // Get unique employee names from filtered appointments
    const employeeNames = new Set();
    filteredAppointments.forEach(a => {
        if (a['Employee Name']) {
            employeeNames.add(a['Employee Name']);
        }
    });

    // Calculate utilization for each employee
    employeeNames.forEach(employeeName => {
        const employeeAppts = filteredAppointments.filter(a => a['Employee Name'] === employeeName);
        const employeeTime = filteredTimeTracking.filter(t => t['Employee Name'] === employeeName);

        const totalApptHours = employeeAppts.reduce((sum, a) => {
            const hours = parseFloat(a['Time (h)'] || a['Time booked (h)'] || 0);
            return sum + hours;
        }, 0);

        const totalClockedHours = employeeTime.reduce((sum, t) => {
            const hours = parseFloat(t['Duration (h)'] || 0);
            return sum + hours;
        }, 0);

        const utilization = totalClockedHours > 0
            ? (totalApptHours / totalClockedHours * 100)
            : 0;

        employeeUtilization[employeeName] = {
            totalApptHours: totalApptHours,
            totalClockedHours: totalClockedHours,
            utilization: utilization,
            appointmentCount: employeeAppts.length,
            shiftCount: employeeTime.length
        };
    });

    // Update the global employeeUtilization object
    window.employeeUtilization = employeeUtilization;
}

// Get Active Member Emails (for revenue exclusion)
export function getActiveMemberEmails() {
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

// Calculate appointment revenue excluding active members
export function calculateAppointmentRevenue(appointments) {
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

// Apply Filters
export function applyFilters(renderAllTabsCallback) {
    const month = document.getElementById('monthFilter').value;
    const location = document.getElementById('locationFilter').value;
    const practitioner = document.getElementById('practitionerFilter').value;
    const service = document.getElementById('serviceFilter').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    // Filter appointments
    const newFilteredAppointments = appointmentsData.filter(row => {
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
    setFilteredAppointments(newFilteredAppointments);

    // Filter memberships by date range (use Bought Date/Time)
    const newFilteredMemberships = membershipsData.filter(row => {
        const boughtDate = row['Bought Date/Time (GMT)'] ? new Date(row['Bought Date/Time (GMT)']) : null;
        if (!boughtDate) return false;

        // Month filter
        if (month !== 'all') {
            const rowMonth = `${boughtDate.getFullYear()}-${String(boughtDate.getMonth() + 1).padStart(2, '0')}`;
            if (rowMonth !== month) return false;
        }

        // Date range filters
        if (startDate && boughtDate < new Date(startDate)) return false;
        if (endDate && boughtDate > new Date(endDate)) return false;

        return true;
    });
    setFilteredMemberships(newFilteredMemberships);

    // Filter leads by date range (use Join date or First purchase date as fallback)
    let newFilteredLeads = [];
    if (leadsData.length > 0) {
        newFilteredLeads = leadsData.filter(row => {
            // Try Join date first, then First purchase date
            const joinDate = row['Join date'] ? parseDate(row['Join date']) :
                row['First purchase date'] ? parseDate(row['First purchase date']) : null;

            // If no date at all, include them (they might be legacy data)
            if (!joinDate) return true;

            // Month filter
            if (month !== 'all') {
                const rowMonth = `${joinDate.getFullYear()}-${String(joinDate.getMonth() + 1).padStart(2, '0')}`;
                if (rowMonth !== month) return false;
            }

            // Date range filters
            if (startDate && joinDate < new Date(startDate)) return false;
            if (endDate && joinDate > new Date(endDate)) return false;

            return true;
        });
    }
    setFilteredLeads(newFilteredLeads);

    // Filter leads converted data by date range
    const newFilteredLeadsConverted = leadsConvertedData.filter(row => {
        const convertedDate = row['Converted'] ? parseDate(row['Converted']) : null;
        if (!convertedDate) return false; // Exclude leads without converted dates

        // Month filter
        if (month !== 'all') {
            const rowMonth = `${convertedDate.getFullYear()}-${String(convertedDate.getMonth() + 1).padStart(2, '0')}`;
            if (rowMonth !== month) return false;
        }

        // Date range filters
        if (startDate && convertedDate < new Date(startDate)) return false;
        if (endDate && convertedDate > new Date(endDate)) return false;

        return true;
    });
    setFilteredLeadsConverted(newFilteredLeadsConverted);

    // Filter membership cancellations by date range (use Cancelled at)
    const newFilteredCancellations = membershipCancellationsData.filter(row => {
        const cancelledDate = row['Cancelled at'] ? parseDate(row['Cancelled at']) : null;
        if (!cancelledDate) return false;

        // Month filter
        if (month !== 'all') {
            const rowMonth = `${cancelledDate.getFullYear()}-${String(cancelledDate.getMonth() + 1).padStart(2, '0')}`;
            if (rowMonth !== month) return false;
        }

        // Date range filters
        if (startDate && cancelledDate < new Date(startDate)) return false;
        if (endDate && cancelledDate > new Date(endDate)) return false;

        return true;
    });
    setFilteredCancellations(newFilteredCancellations);

    // Filter commissions by date range
    if (window.commissionsData && window.commissionsData.length > 0) {
        window.filteredCommissions = window.commissionsData.filter(row => {
            const commDate = row['Date'] ? new Date(row['Date']) : null;
            if (!commDate) return false;

            // Month filter
            if (month !== 'all') {
                const rowMonth = `${commDate.getFullYear()}-${String(commDate.getMonth() + 1).padStart(2, '0')}`;
                if (rowMonth !== month) return false;
            }

            // Date range filters
            if (startDate && commDate < new Date(startDate)) return false;
            if (endDate && commDate > new Date(endDate)) return false;

            return true;
        });
    }

    // Filter time tracking by date range and location (via practitioners)
    let newFilteredTimeTracking = [];
    if (window.timeTrackingData && window.timeTrackingData.length > 0) {
        // First, get the list of practitioners from the filtered appointments
        // This ensures we only count time tracking for practitioners at the selected location/filters
        const practitionersInFiltered = new Set();
        newFilteredAppointments.forEach(row => {
            const empName = row['Employee Name'];
            if (empName) {
                practitionersInFiltered.add(empName);
            }
        });

        newFilteredTimeTracking = window.timeTrackingData.filter(row => {
            if (!row['Employee Name']) return false;

            const clockedDate = parseDate(row['Clocked in']);
            if (!clockedDate) return false;

            // CRITICAL: Only include time tracking for practitioners who have appointments in filtered data
            if (!practitionersInFiltered.has(row['Employee Name'])) {
                return false;
            }

            // Month filter
            if (month !== 'all') {
                const rowMonth = `${clockedDate.getFullYear()}-${String(clockedDate.getMonth() + 1).padStart(2, '0')}`;
                if (rowMonth !== month) return false;
            }

            // Date range filters
            if (startDate && clockedDate < new Date(startDate)) return false;
            if (endDate && clockedDate > new Date(endDate + 'T23:59:59')) return false;

            // Practitioner filter
            if (practitioner !== 'all' && row['Employee Name'] !== practitioner) return false;

            return true;
        });
    }
    setFilteredTimeTracking(newFilteredTimeTracking);

    // Recalculate utilization based on filtered data
    recalculateUtilization();

    displayActiveFilters();

    if (renderAllTabsCallback) {
        renderAllTabsCallback();
    }
}

// Refresh data with current filters
export function refreshData(renderAllTabsCallback) {
    applyFilters(renderAllTabsCallback);
}

// Quick Filters
export function setQuickFilter(filter, applyFiltersCallback) {
    const today = new Date();
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const monthFilter = document.getElementById('monthFilter');

    // Reset filters
    if (filter === 'reset') {
        startDateInput.value = '';
        endDateInput.value = '';
        monthFilter.value = 'all';
        document.getElementById('locationFilter').value = 'all';
        document.getElementById('practitionerFilter').value = 'all';
        document.getElementById('serviceFilter').value = 'all';
        if (applyFiltersCallback) applyFiltersCallback();
        return;
    }

    // Apply quick filter
    switch (filter) {
        case '7days':
            const sevenDaysAgo = new Date(today);
            sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
            startDateInput.value = sevenDaysAgo.toISOString().split('T')[0];
            endDateInput.value = today.toISOString().split('T')[0];
            monthFilter.value = 'all';
            break;
        case '30days':
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
            endDateInput.value = today.toISOString().split('T')[0];
            monthFilter.value = 'all';
            break;
        case '90days':
            const ninetyDaysAgo = new Date(today);
            ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
            startDateInput.value = ninetyDaysAgo.toISOString().split('T')[0];
            endDateInput.value = today.toISOString().split('T')[0];
            monthFilter.value = 'all';
            break;
        case 'thisMonth':
            const monthStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
            monthFilter.value = monthStr;
            startDateInput.value = '';
            endDateInput.value = '';
            break;
        case 'lastMonth':
            const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            const lastMonthStr = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;
            monthFilter.value = lastMonthStr;
            startDateInput.value = '';
            endDateInput.value = '';
            break;
    }

    if (applyFiltersCallback) applyFiltersCallback();
}
