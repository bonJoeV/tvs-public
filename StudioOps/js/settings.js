import { CONFIG } from './config.js';
import { appointmentsData } from './data.js';

// Franchise Settings Management
export function saveFranchiseSettings(renderAllTabsCallback) {
    const settings = {
        timezone: document.getElementById('timezoneSelect').value,
        franchiseFeePercent: parseFloat(document.getElementById('franchiseFeePercent').value),
        brandFundPercent: parseFloat(document.getElementById('brandFundPercent').value),
        ccFeesPercent: parseFloat(document.getElementById('ccFeesPercent').value),
        monthlyPaidApptGoal: parseInt(document.getElementById('monthlyPaidApptGoal').value),
        monthlyIntroApptGoal: parseInt(document.getElementById('monthlyIntroApptGoal').value),
        monthlyRevenueGoal: parseFloat(document.getElementById('monthlyRevenueGoal').value),
        baseHourlyRate: parseFloat(document.getElementById('baseRateInput').value),
        ltvTiers: document.getElementById('ltvTiersSelect').value,
        salariedEmployees: [
            {
                name: document.getElementById('salaryEmp1Name').value.trim(),
                annualSalary: parseFloat(document.getElementById('salaryEmp1Salary').value) || 0,
                startDate: document.getElementById('salaryEmp1StartDate').value
            },
            {
                name: document.getElementById('salaryEmp2Name').value.trim(),
                annualSalary: parseFloat(document.getElementById('salaryEmp2Salary').value) || 0,
                startDate: document.getElementById('salaryEmp2StartDate').value
            },
            {
                name: document.getElementById('salaryEmp3Name').value.trim(),
                annualSalary: parseFloat(document.getElementById('salaryEmp3Salary').value) || 0,
                startDate: document.getElementById('salaryEmp3StartDate').value
            }
        ]
    };

    // Validate (skip timezone, ltvTiers, and salariedEmployees as they need special handling)
    for (const [key, value] of Object.entries(settings)) {
        if (key === 'timezone' || key === 'ltvTiers' || key === 'salariedEmployees') continue;
        if (isNaN(value) || value < 0) {
            showFranchiseSettingsStatus('❌ Please enter valid numbers (0 or greater) for all fields', 'error');
            return;
        }
    }

    // Validate salaried employees
    for (let i = 0; i < settings.salariedEmployees.length; i++) {
        const emp = settings.salariedEmployees[i];
        if (emp.name && emp.annualSalary <= 0) {
            showFranchiseSettingsStatus(`❌ Employee ${i + 1}: Please enter a valid salary`, 'error');
            return;
        }
        if (emp.annualSalary > 0 && !emp.startDate) {
            showFranchiseSettingsStatus(`❌ Employee ${i + 1}: Please enter a start date`, 'error');
            return;
        }
    }

    // Update CONFIG
    CONFIG.timezone = settings.timezone;
    CONFIG.franchiseFeePercent = settings.franchiseFeePercent;
    CONFIG.brandFundPercent = settings.brandFundPercent;
    CONFIG.ccFeesPercent = settings.ccFeesPercent;
    CONFIG.goals.monthlyAppointments = settings.monthlyPaidApptGoal;
    CONFIG.goals.monthlyIntroAppointments = settings.monthlyIntroApptGoal;
    CONFIG.goals.monthlyRevenue = settings.monthlyRevenueGoal;
    CONFIG.baseHourlyRate = settings.baseHourlyRate;
    CONFIG.ltvTiers = settings.ltvTiers;
    CONFIG.salariedEmployees = settings.salariedEmployees;

    // Save to localStorage
    localStorage.setItem('vitalStretchFranchiseSettings', JSON.stringify(settings));

    // Show success message
    showFranchiseSettingsStatus('✅ Settings saved successfully!', 'success');

    // Re-render tabs if data is loaded
    if (appointmentsData.length > 0 && renderAllTabsCallback) {
        renderAllTabsCallback();
    }
}

export function showFranchiseSettingsStatus(message, type) {
    const statusEl = document.getElementById('franchiseSettingsStatus');
    statusEl.textContent = message;
    statusEl.style.color = type === 'success' ? 'var(--success)' : 'var(--danger)';

    setTimeout(() => {
        statusEl.textContent = '';
    }, 3000);
}

export function loadFranchiseSettingsFromStorage() {
    const saved = localStorage.getItem('vitalStretchFranchiseSettings');
    if (saved) {
        try {
            const settings = JSON.parse(saved);

            // Update CONFIG
            CONFIG.timezone = settings.timezone || 'America/Chicago';
            CONFIG.franchiseFeePercent = settings.franchiseFeePercent || 7.0;
            CONFIG.brandFundPercent = settings.brandFundPercent || 1.5;
            CONFIG.ccFeesPercent = settings.ccFeesPercent || 2.9;
            CONFIG.goals.monthlyAppointments = settings.monthlyPaidApptGoal || 300;
            CONFIG.goals.monthlyIntroAppointments = settings.monthlyIntroApptGoal || 50;
            CONFIG.goals.monthlyRevenue = settings.monthlyRevenueGoal || 20000;
            CONFIG.baseHourlyRate = settings.baseHourlyRate || 13.00;
            CONFIG.ltvTiers = settings.ltvTiers || 'default';
            CONFIG.salariedEmployees = settings.salariedEmployees || [
                { name: '', annualSalary: 0, startDate: '' },
                { name: '', annualSalary: 0, startDate: '' },
                { name: '', annualSalary: 0, startDate: '' }
            ];

            // Update form fields
            document.getElementById('timezoneSelect').value = CONFIG.timezone;
            document.getElementById('franchiseFeePercent').value = CONFIG.franchiseFeePercent;
            document.getElementById('brandFundPercent').value = CONFIG.brandFundPercent;
            document.getElementById('ccFeesPercent').value = CONFIG.ccFeesPercent;
            document.getElementById('monthlyPaidApptGoal').value = CONFIG.goals.monthlyAppointments;
            document.getElementById('monthlyIntroApptGoal').value = CONFIG.goals.monthlyIntroAppointments;
            document.getElementById('monthlyRevenueGoal').value = CONFIG.goals.monthlyRevenue;
            document.getElementById('baseRateInput').value = CONFIG.baseHourlyRate;
            document.getElementById('ltvTiersSelect').value = CONFIG.ltvTiers;

            // Update salaried employee fields
            for (let i = 0; i < 3; i++) {
                const emp = CONFIG.salariedEmployees[i];
                document.getElementById(`salaryEmp${i + 1}Name`).value = emp.name || '';
                document.getElementById(`salaryEmp${i + 1}Salary`).value = emp.annualSalary || '';
                document.getElementById(`salaryEmp${i + 1}StartDate`).value = emp.startDate || '';
            }
        } catch (e) {
            console.error('Error loading settings:', e);
        }
    }
}

// Update LTV tier preview text
export function updateLTVTierPreview() {
    const tierSelect = document.getElementById('ltvTiersSelect');
    const previewEl = document.getElementById('ltvTierPreview');

    if (!tierSelect || !previewEl) return;

    const tierPreviews = {
        'default': '$1–$50, $50–$150, $150–$300, $300–$500, $500–$1K, $1K+',
        'tier2': '$1–$100, $100–$300, $300–$500, $500–$1K, $1K–$2K, $2K+',
        'tier3': '$1–$150, $150–$400, $400–$800, $800–$1.5K, $1.5K–$3K, $3K+',
        'tier4': '$1–$200, $200–$600, $600–$1K, $1K–$2K, $2K–$4K, $4K+',
        'tier5': '$1–$300, $300–$800, $800–$1.5K, $1.5K–$3K, $3K–$5K, $5K+'
    };

    previewEl.textContent = tierPreviews[tierSelect.value] || tierPreviews['default'];
}

// Initialize settings on page load
export function initializeSettings() {
    loadFranchiseSettingsFromStorage();

    // Add event listener for LTV tier dropdown
    const tierSelect = document.getElementById('ltvTiersSelect');
    if (tierSelect) {
        tierSelect.addEventListener('change', updateLTVTierPreview);
        updateLTVTierPreview(); // Initial update
    }
}
