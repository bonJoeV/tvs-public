import { CONFIG } from './config.js';
import { staffEmailToName } from './data.js';

// Utility Functions
export function formatNumber(num) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

export function formatCurrency(num) {
    // Only round to nearest dollar if >= 1000, otherwise show cents
    if (Math.abs(num) >= 1000) {
        return CONFIG.currencySymbol + formatNumber(Math.round(num));
    }
    return CONFIG.currencySymbol + num.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Helper function to parse LTV values robustly
export function parseLTV(value) {
    if (value === null || value === undefined || value === '') return 0;
    // Remove currency symbols, commas, and whitespace
    const cleaned = String(value).replace(/[$,\s]/g, '').trim();
    const parsed = parseFloat(cleaned);
    return isNaN(parsed) ? 0 : parsed;
}

// Format staff name to "First name, Last initial" format
export function formatStaffName(nameOrEmail) {
    if (!nameOrEmail || nameOrEmail === 'Direct/Online') return nameOrEmail;

    // Check if we have a mapping from email to full name
    const emailLower = nameOrEmail.toLowerCase().trim();
    if (staffEmailToName[emailLower]) {
        nameOrEmail = staffEmailToName[emailLower];
    }

    // If it's an email and we don't have a mapping, extract the name part
    if (nameOrEmail.includes('@') && !staffEmailToName[emailLower]) {
        nameOrEmail = nameOrEmail.split('@')[0].replace(/[._]/g, ' ');
    }

    // Split by spaces and get parts
    const parts = nameOrEmail.trim().split(/\s+/);
    if (parts.length === 0) return nameOrEmail;
    if (parts.length === 1) return parts[0]; // Just first name

    // Get first name and last initial
    const firstName = parts[0];
    const lastInitial = parts[parts.length - 1].charAt(0).toUpperCase();

    return `${firstName} ${lastInitial}.`;
}

// Calculate prorated salary costs for a given period
export function calculateSalaryCosts(startDate, endDate) {
    let totalSalaryCost = 0;
    const salaryDetails = [];

    if (!CONFIG.salariedEmployees) return { total: 0, details: [] };

    CONFIG.salariedEmployees.forEach((emp, index) => {
        if (!emp.name || emp.annualSalary <= 0 || !emp.startDate) return;

        const empStartDate = new Date(emp.startDate);
        const periodStart = new Date(startDate);
        const periodEnd = new Date(endDate);

        // Check if employee worked during this period
        if (empStartDate > periodEnd) return; // Started after period

        // Determine actual work start date (later of employee start or period start)
        const workStart = empStartDate > periodStart ? empStartDate : periodStart;

        // Calculate days worked in the period
        const daysInPeriod = Math.ceil((periodEnd - periodStart) / (1000 * 60 * 60 * 24));
        const daysWorked = Math.ceil((periodEnd - workStart) / (1000 * 60 * 60 * 24)) + 1; // +1 to include start day

        // Calculate prorated cost
        const dailyRate = emp.annualSalary / 365;
        const proratedCost = dailyRate * Math.min(daysWorked, daysInPeriod);

        totalSalaryCost += proratedCost;
        salaryDetails.push({
            name: emp.name,
            annualSalary: emp.annualSalary,
            startDate: emp.startDate,
            daysWorked: Math.min(daysWorked, daysInPeriod),
            proratedCost: proratedCost
        });
    });

    return {
        total: totalSalaryCost,
        details: salaryDetails
    };
}

// Memoized date parsing for performance
const dateCache = new Map();
export function parseDate(dateStr) {
    if (!dateStr) return new Date();

    // Check cache first
    if (dateCache.has(dateStr)) {
        return dateCache.get(dateStr);
    }

    let result;

    // Handle "YYYY-MM-DD, HH:MM AM/PM" format
    const parts = dateStr.split(',');
    if (parts.length >= 2) {
        const datePart = parts[0].trim();
        const timePart = parts[1].trim();

        // Parse date
        const dateComponents = datePart.split('-');
        if (dateComponents.length === 3) {
            const year = parseInt(dateComponents[0]);
            const month = parseInt(dateComponents[1]) - 1;
            const day = parseInt(dateComponents[2]);

            // Parse time
            const timeMatch = timePart.match(/(\d+):(\d+)\s*(AM|PM)/i);
            if (timeMatch) {
                let hour = parseInt(timeMatch[1]);
                const minute = parseInt(timeMatch[2]);
                const ampm = timeMatch[3].toUpperCase();

                // Convert to 24-hour format
                if (ampm === 'PM' && hour !== 12) {
                    hour += 12;
                } else if (ampm === 'AM' && hour === 12) {
                    hour = 0;
                }

                result = new Date(year, month, day, hour, minute);
            } else {
                result = new Date(year, month, day);
            }
        } else {
            result = new Date(dateStr);
        }
    } else {
        result = new Date(dateStr);
    }

    // Cache the result
    dateCache.set(dateStr, result);
    return result;
}

export function isIntroOffer(service) {
    if (!service) return false;
    const serviceLower = service.toLowerCase();
    return serviceLower.includes('intro') || serviceLower.includes('introductory');
}

export function formatTime(hour) {
    const h = parseInt(hour);
    if (h === 0) return '12 AM';
    if (h < 12) return `${h} AM`;
    if (h === 12) return '12 PM';
    return `${h - 12} PM`;
}
