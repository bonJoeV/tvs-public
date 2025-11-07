/**
 * Upload Module
 *
 * Handles all CSV and ZIP file uploads for the dashboard
 *
 * File Upload Handlers (lines ~3402-3916):
 * - Leads CSV upload
 * - Leads Converted CSV upload
 * - Memberships CSV upload (sales and cancellations)
 * - Payroll ZIP upload (appointments and time tracking)
 * - Attendance ZIP upload (VSP name mapping)
 *
 * Each handler:
 * 1. Validates file
 * 2. Parses CSV/ZIP content
 * 3. Processes and transforms data
 * 4. Updates global data stores
 * 5. Triggers dashboard refresh
 */

import { formatNumber } from './utils.js';
import {
    setLeadsData, setLeadsConvertedData, setMembershipsData, setMembershipCancellationsData,
    setAppointmentsData, setFilteredAppointments, setStaffEmailToName,
    leadsData, leadsConvertedData, membershipsData, membershipCancellationsData, appointmentsData,
    staffEmailToName
} from './data.js';

// Upload Modal Controls
export function openUploadModal() {
    document.getElementById('uploadModal').classList.add('show');
    document.body.style.overflow = 'hidden';
}

export function closeUploadModal() {
    document.getElementById('uploadModal').classList.remove('show');
    document.body.style.overflow = 'auto';
}

// Leads File Upload Handler
export function initializeLeadsFileUpload(applyFiltersCallback, renderAllTabsCallback, hideEmptyStateCallback) {
    document.getElementById('leadsFile').addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (!file) return;

        document.getElementById('leadsStatus').innerHTML = '<span class="spinner"></span> Processing...';

        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: function (results) {
                setLeadsData(results.data);

                // If leads converted was already loaded, merge lead source data
                if (leadsConvertedData.length > 0) {
                    // Create a map of email -> lead source from converted data
                    const leadSourceMap = new Map();
                    leadsConvertedData.forEach(row => {
                        const email = (row['E-mail'] || row['Email'] || '').toLowerCase().trim();
                        const leadSource = row['Lead source'] || '';
                        if (email && leadSource) {
                            leadSourceMap.set(email, leadSource);
                        }
                    });

                    // Merge lead sources into newly loaded leadsData
                    const mergedData = leadsData.map(customer => {
                        const email = (customer['E-mail'] || '').toLowerCase().trim();
                        if (email && leadSourceMap.has(email)) {
                            return {
                                ...customer,
                                'Aggregator': leadSourceMap.get(email),
                                'Lead source': leadSourceMap.get(email)
                            };
                        }
                        return customer;
                    });
                    setLeadsData(mergedData);
                }

                // Count customers vs leads
                const customers = leadsData.filter(row => (row['Type'] || '').toLowerCase() === 'customer').length;
                const leads = leadsData.filter(row => (row['Type'] || '').toLowerCase() === 'lead').length;

                let statusHTML = '<span style="color: var(--success); font-weight: 600;">✅ ';
                if (customers > 0 && leads > 0) {
                    statusHTML += `${formatNumber(customers)} customers, ${formatNumber(leads)} leads loaded`;
                } else if (customers > 0) {
                    statusHTML += `${formatNumber(customers)} customers loaded`;
                } else if (leads > 0) {
                    statusHTML += `${formatNumber(leads)} leads loaded`;
                } else {
                    statusHTML += `${formatNumber(leadsData.length)} records loaded`;
                }
                statusHTML += '</span>';

                document.getElementById('leadsStatus').innerHTML = statusHTML;

                if (appointmentsData.length > 0) {
                    hideEmptyStateCallback();
                    applyFiltersCallback();
                    renderAllTabsCallback();
                }
            },
            error: function (error) {
                document.getElementById('leadsStatus').innerHTML =
                    '<span style="color: var(--danger);">❌ Error loading file</span>';
                console.error('Parse error:', error);
            }
        });
    });
}

// Leads Converted File Upload Handler
export function initializeLeadsConvertedFileUpload(applyFiltersCallback, renderAllTabsCallback, hideEmptyStateCallback) {
    document.getElementById('leadsConvertedFile').addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (!file) return;

        document.getElementById('leadsConvertedStatus').innerHTML = '<span class="spinner"></span> Processing...';

        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: function (results) {
                setLeadsConvertedData(results.data);

                // If main leads CSV already loaded, MERGE lead sources into existing data
                if (leadsData.length > 0) {
                    const leadSourceMap = new Map();
                    leadsConvertedData.forEach(row => {
                        const email = (row['E-mail'] || row['Email'] || '').toLowerCase().trim();
                        const leadSource = row['Lead source'] || '';
                        if (email && leadSource) {
                            leadSourceMap.set(email, leadSource);
                        }
                    });

                    const mergedData = leadsData.map(customer => {
                        const email = (customer['E-mail'] || '').toLowerCase().trim();
                        if (email && leadSourceMap.has(email)) {
                            return {
                                ...customer,
                                'Aggregator': leadSourceMap.get(email),
                                'Lead source': leadSourceMap.get(email)
                            };
                        }
                        return customer;
                    });
                    setLeadsData(mergedData);
                } else {
                    // Main leads CSV not loaded yet - use converted data as primary
                    const processedData = leadsConvertedData.map(row => {
                        let type = row['Type'] || '';
                        if (!type || type.toLowerCase() === 'lead') {
                            type = (row['Converted to'] && row['Converted to'] !== 'N/A' && row['Converted to'] !== '') ? 'Customer' : 'Lead';
                        }

                        return {
                            'First name': row['First Name'] || row['First name'] || '',
                            'Last name': row['Last Name'] || row['Last name'] || '',
                            'E-mail': row['E-mail'] || row['Email'] || '',
                            'Type': type,
                            'Join date': row['Join date'] || row['Converted'] || '',
                            'First purchase': row['First purchase'] || row['Converted'] || '',
                            'Aggregator': row['Lead source'] || 'Unknown',
                            'LTV': row['LTV'] || '0',
                            'Home location': row['Home location'] || '',
                            'Converted to': row['Converted to'] || '',
                            'Converted': row['Converted'] || '',
                            'Lead source': row['Lead source'] || ''
                        };
                    });
                    setLeadsData(processedData);
                }

                // Count conversions and sources
                const converted = leadsConvertedData.filter(row => {
                    const convertedTo = (row['Converted to'] || '').trim();
                    return convertedTo && convertedTo !== 'N/A' && convertedTo !== '';
                }).length;

                const sources = new Set(leadsConvertedData.map(row => row['Lead source']).filter(s => s));

                let statusHTML = '<span style="color: var(--success); font-weight: 600;">✅ ';
                statusHTML += `${formatNumber(leadsConvertedData.length)} leads, `;
                statusHTML += `${formatNumber(converted)} converted, `;
                statusHTML += `${formatNumber(sources.size)} sources (merged into main data)`;
                statusHTML += '</span>';

                document.getElementById('leadsConvertedStatus').innerHTML = statusHTML;

                if (appointmentsData.length > 0) {
                    hideEmptyStateCallback();
                    applyFiltersCallback();
                    renderAllTabsCallback();
                }
            },
            error: function (error) {
                document.getElementById('leadsConvertedStatus').innerHTML =
                    '<span style="color: var(--danger);">❌ Error loading file</span>';
                console.error('Parse error:', error);
            }
        });
    });
}

// Memberships File Upload Handler
export function initializeMembershipsFileUpload(renderAllTabsCallback, hideEmptyStateCallback) {
    document.getElementById('membershipsFile').addEventListener('change', function (e) {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        document.getElementById('membershipsStatus').innerHTML = '<span class="spinner"></span> Processing...';

        let filesProcessed = 0;
        let statusMessages = [];

        // Process each file
        Array.from(files).forEach((file) => {
            Papa.parse(file, {
                header: true,
                skipEmptyLines: true,
                complete: function (results) {
                    if (results.data.length > 0) {
                        const headers = Object.keys(results.data[0]);

                        if (headers.includes('Cancelled at')) {
                            setMembershipCancellationsData(results.data);
                        } else if (headers.includes('Bought Date/Time (GMT)')) {
                            setMembershipsData(results.data);
                        } else {
                            statusMessages.push(`⚠️ Unknown file type`);
                        }
                    }

                    filesProcessed++;

                    if (filesProcessed === files.length) {
                        const currentStatus = [];

                        if (membershipsData.length > 0) {
                            currentStatus.push(`<span style="color: var(--success); font-weight: 600;">✅ ${formatNumber(membershipsData.length)} memberships loaded</span>`);
                        }

                        if (membershipCancellationsData.length > 0) {
                            currentStatus.push(`<span style="color: var(--success); font-weight: 600;">✅ ${formatNumber(membershipCancellationsData.length)} cancellations loaded</span>`);
                        }

                        if (statusMessages.length > 0) {
                            currentStatus.push(...statusMessages);
                        }

                        document.getElementById('membershipsStatus').innerHTML = currentStatus.join('<br>') ||
                            '<span style="color: var(--danger);">❌ No valid data found</span>';

                        if (appointmentsData.length > 0 && (membershipsData.length > 0 || membershipCancellationsData.length > 0)) {
                            hideEmptyStateCallback();
                            renderAllTabsCallback();
                        }
                    }
                },
                error: function (error) {
                    filesProcessed++;
                    statusMessages.push(`❌ Error in file`);
                    if (filesProcessed === files.length) {
                        document.getElementById('membershipsStatus').innerHTML =
                            statusMessages.map(msg => `<span style="color: var(--danger); font-weight: 600;">${msg}</span>`).join('<br>');
                    }
                    console.error('Parse error:', error);
                }
            });
        });
    });
}

// Payroll ZIP File Upload Handler
export function initializePayrollZipUpload(initializeDashboardCallback) {
    document.getElementById('payrollZipFile').addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        document.getElementById('payrollZipStatus').innerHTML = '<span class="spinner"></span> Processing zip file...';

        try {
            const zip = await JSZip.loadAsync(file);
            let allAppointments = [];
            let allTimeTracking = [];
            let allCommissions = [];
            let employeeStats = {};

            // Process all files in the zip
            for (const [filename, zipEntry] of Object.entries(zip.files)) {
                if (zipEntry.dir) continue;

                const content = await zipEntry.async('text');

                // Extract employee name from filename
                const nameParts = filename.match(/momence-payroll-(?:appointments|time)-(.+?)(?:-aggregate)?\.csv/);
                if (!nameParts) continue;

                const employeeName = nameParts[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                // Parse appointments files (not aggregate)
                if (filename.includes('appointments') && !filename.includes('aggregate')) {
                    Papa.parse(content, {
                        header: true,
                        skipEmptyLines: true,
                        complete: function(results) {
                            // Add employee name and practitioner info to each row
                            results.data.forEach(row => {
                                const names = employeeName.split(' ');
                                row['Practitioner First Name'] = names[0];
                                row['Practitioner Last Name'] = names.slice(1).join(' ');
                                row['Employee Name'] = employeeName;

                                // Convert Time booked (h) to Time (h) for consistency
                                if (row['Time booked (h)']) {
                                    row['Time (h)'] = row['Time booked (h)'];
                                }
                            });
                            allAppointments = allAppointments.concat(results.data);
                        }
                    });
                }

                // Parse time tracking files
                if (filename.includes('time') && !filename.includes('aggregate')) {
                    Papa.parse(content, {
                        header: true,
                        skipEmptyLines: true,
                        complete: function(results) {
                            results.data.forEach(row => {
                                row['Employee Name'] = employeeName;
                                // Store for cleaning later
                                if (!employeeStats[employeeName]) {
                                    employeeStats[employeeName] = { durations: [] };
                                }
                                const duration = parseFloat(row['Duration (h)']);
                                if (!isNaN(duration)) {
                                    employeeStats[employeeName].durations.push(duration);
                                }
                            });
                            allTimeTracking = allTimeTracking.concat(results.data);
                        }
                    });
                }

                // Parse commission files
                if (filename.includes('commissions') && !filename.includes('aggregate')) {
                    Papa.parse(content, {
                        header: true,
                        skipEmptyLines: true,
                        complete: function(results) {
                            results.data.forEach(row => {
                                row['Employee Name'] = employeeName;
                                // Clean product names - remove special characters
                                if (row['Item name']) {
                                    row['Item name'] = row['Item name']
                                        .replace(/[®™©Â®]/g, '')           // Remove special characters
                                        .replace(/[\u0080-\u00FF]/g, '')  // Remove extended ASCII
                                        .replace(/\s+/g, ' ')              // Normalize whitespace
                                        .trim();
                                }
                                // Only include Membership and Product commissions
                                const itemType = (row['Item type'] || '').toLowerCase();
                                if (itemType === 'membership' || itemType === 'product') {
                                    allCommissions = allCommissions || [];
                                    allCommissions.push(row);
                                }
                            });
                        }
                    });
                }
            }

            // Wait a bit for all parsing to complete
            await new Promise(resolve => setTimeout(resolve, 500));

            // Clean Duration (h) data - replace values > 12 with employee average
            Object.keys(employeeStats).forEach(employeeName => {
                const durations = employeeStats[employeeName].durations.filter(d => d > 0 && d <= 12);
                const avgDuration = durations.length > 0
                    ? durations.reduce((sum, d) => sum + d, 0) / durations.length
                    : 8; // Default to 8 hours if no valid data
                employeeStats[employeeName].avgDuration = avgDuration;
            });

            // Apply cleaning to time tracking data
            allTimeTracking = allTimeTracking.map(row => {
                const duration = parseFloat(row['Duration (h)']);
                if (!isNaN(duration) && duration > 12) {
                    const employeeName = row['Employee Name'];
                    const avgDuration = employeeStats[employeeName]?.avgDuration || 8;
                    row['Duration (h)'] = avgDuration.toFixed(2);
                    row['Original Duration (h)'] = duration.toFixed(2); // Keep original for reference
                    row['Duration Corrected'] = 'Yes';
                }
                return row;
            });

            // Calculate utilization for each employee
            const employeeUtilization = {};
            Object.keys(employeeStats).forEach(employeeName => {
                const employeeAppts = allAppointments.filter(a => a['Employee Name'] === employeeName);
                const employeeTime = allTimeTracking.filter(t => t['Employee Name'] === employeeName);

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

            // Store utilization data globally
            window.employeeUtilization = employeeUtilization;
            window.timeTrackingData = allTimeTracking;
            window.commissionsData = allCommissions;
            window.filteredCommissions = [...allCommissions];

            // Set appointments data
            setAppointmentsData(allAppointments);
            setFilteredAppointments([...allAppointments]);

            const totalAppts = allAppointments.length;
            const totalEmployees = Object.keys(employeeStats).length;
            const avgUtilization = Object.values(employeeUtilization)
                .reduce((sum, e) => sum + e.utilization, 0) / totalEmployees;

            document.getElementById('payrollZipStatus').innerHTML =
                `<span style="color: var(--success); font-weight: 600;">✅ ${formatNumber(totalAppts)} appointments from ${totalEmployees} employees (Avg Utilization: ${avgUtilization.toFixed(1)}%)</span>`;

            initializeDashboardCallback();

        } catch (error) {
            document.getElementById('payrollZipStatus').innerHTML =
                '<span style="color: var(--danger);">❌ Error processing zip file</span>';
            console.error('Zip processing error:', error);
        }
    });
}

// Attendance ZIP File Upload Handler
export function initializeAttendanceZipUpload(renderAllTabsCallback) {
    document.getElementById('attendanceZipFile').addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        document.getElementById('attendanceZipStatus').innerHTML = '<span class="spinner"></span> Processing attendance data...';

        try {
            const zip = await JSZip.loadAsync(file);

            // Look for the combined attendance report
            for (const [filename, zipEntry] of Object.entries(zip.files)) {
                if (zipEntry.dir) continue;

                if (filename.includes('attendance-report-combined')) {
                    const content = await zipEntry.async('text');

                    Papa.parse(content, {
                        header: true,
                        skipEmptyLines: true,
                        complete: function(results) {
                            // Store the full attendance data
                            window.attendanceData = results.data;

                            // Build email to name mapping
                            const updatedMapping = {...staffEmailToName};
                            results.data.forEach(row => {
                                const email = (row['Staff E-mail'] || '').toLowerCase().trim();
                                const name = (row['Staff Name'] || '').trim();

                                if (email && name && !updatedMapping[email]) {
                                    updatedMapping[email] = name;
                                }
                            });
                            setStaffEmailToName(updatedMapping);

                            const mappingCount = Object.keys(updatedMapping).length;
                            const attendanceCount = results.data.length;
                            document.getElementById('attendanceZipStatus').innerHTML =
                                `<span style="color: var(--success);">✅ Loaded ${attendanceCount} attendance records from ${mappingCount} VSPs</span>`;

                            // Re-render tabs to update staff names and attendance metrics
                            if (appointmentsData.length > 0) {
                                renderAllTabsCallback();
                            }
                        },
                        error: function(error) {
                            console.error('Parse error:', error);
                            document.getElementById('attendanceZipStatus').innerHTML =
                                '<span style="color: var(--danger);">❌ Error parsing attendance data</span>';
                        }
                    });
                    break;
                }
            }

        } catch (error) {
            document.getElementById('attendanceZipStatus').innerHTML =
                '<span style="color: var(--danger);">❌ Error processing zip file</span>';
            console.error('Zip processing error:', error);
        }
    });
}
