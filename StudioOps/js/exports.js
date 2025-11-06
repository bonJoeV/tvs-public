import { membershipTypes, salesByStaff } from './data.js';

// CSV Export Function
export function exportToCSV(data, filename) {
    if (!data || data.length === 0) {
        alert('No data to export');
        return;
    }

    // Get headers from first object
    const headers = Object.keys(data[0]);

    // Create CSV content
    let csv = headers.join(',') + '\n';

    data.forEach(row => {
        const values = headers.map(header => {
            let value = row[header];

            // Handle values with commas or quotes
            if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
                value = '"' + value.replace(/"/g, '""') + '"';
            }

            return value;
        });
        csv += values.join(',') + '\n';
    });

    // Create download link
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Modal data export
export function exportModalData(currentModalData) {
    if (currentModalData && currentModalData.length > 0) {
        const filename = 'modal-data-' + new Date().toISOString().split('T')[0] + '.csv';
        exportToCSV(currentModalData, filename);
    }
}

// Export membership types data
export function exportMembershipTypeData() {
    const data = [];
    Object.entries(membershipTypes).forEach(([type, stats]) => {
        data.push({
            'Membership Type': type,
            'Total Count': stats.count,
            'New Sales': stats.newSales || 0,
            'Renewals': stats.renewals || 0,
            'Active': stats.active,
            'Expired': stats.count - stats.active,
            'Revenue': stats.revenue.toFixed(2),
            'Average Value': (stats.revenue / stats.count).toFixed(2)
        });
    });
    exportToCSV(data, 'membership-types-' + new Date().toISOString().split('T')[0] + '.csv');
}

// Export staff sales data
export function exportStaffSalesData() {
    const data = [];
    Object.entries(salesByStaff).forEach(([staff, stats]) => {
        data.push({
            'Staff Member': staff,
            'Total Sales': stats.count,
            'New Sales': stats.newSales || 0,
            'Renewals': stats.renewals || 0,
            'Revenue Generated': stats.revenue.toFixed(2),
            'Average Sale Value': (stats.revenue / stats.count).toFixed(2)
        });
    });
    exportToCSV(data, 'staff-sales-' + new Date().toISOString().split('T')[0] + '.csv');
}
