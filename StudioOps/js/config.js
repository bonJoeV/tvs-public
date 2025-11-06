// Configuration
export const CONFIG = {
    currencySymbol: '$',
    dateFormat: 'en-US',
    timezone: 'America/Chicago', // Central Time
    goals: {
        monthlyRevenue: 20000,
        monthlyAppointments: 300,
        monthlyIntroAppointments: 50,
        avgRevenuePerAppt: 100
    },
    baseHourlyRate: 13.00,
    franchiseFeePercent: 7.0,
    brandFundPercent: 1.5,
    ccFeesPercent: 2.9,
    ltvTiers: 'default', // default, tier2, tier3, tier4
    salariedEmployees: [
        { name: '', annualSalary: 0, startDate: '' },
        { name: '', annualSalary: 0, startDate: '' },
        { name: '', annualSalary: 0, startDate: '' }
    ]
};

// LTV Tier definitions
export const LTV_TIERS = {
    default: { ranges: [50, 150, 300, 500, 1000, Infinity], vipMin: 1000 },
    tier2: { ranges: [100, 300, 500, 1000, 2000, Infinity], vipMin: 2000 },
    tier3: { ranges: [150, 400, 800, 1500, 3000, Infinity], vipMin: 3000 },
    tier4: { ranges: [200, 600, 1000, 2000, 4000, Infinity], vipMin: 4000 },
    tier5: { ranges: [300, 800, 1500, 3000, 5000, Infinity], vipMin: 5000 }
};
