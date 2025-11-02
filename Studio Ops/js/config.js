// The Vital Stretch Dashboard - Configuration
// Edit this file to enable/disable features

const CONFIG = {
    // Feature Toggles - Set to true to enable, false to disable
    features: {
        heatmap: true,              // Interactive appointment heatmap
        clientRetention: true,      // Client retention analysis
        scheduleOptimization: true, // Schedule gap analysis
        goals: true,                // Goal tracking and progress
        alerts: true,               // Smart business alerts
        businessIntelligence: true, // Business Intelligence Dashboard with funnel analysis
        export: true,               // Export and reporting tools
        advancedCharts: false,      // Additional chart visualizations
        paymentAnalysis: false      // Payment method breakdown
    },
    
    // Business Goals (used in Goal Tracking feature)
    goals: {
        monthlyRevenue: 50000,      // Target monthly revenue in dollars
        monthlyAppointments: 300,   // Target number of appointments
        avgRevenuePerAppt: 150      // Target average revenue per appointment
    },
    
    // Dashboard Settings
    settings: {
        defaultTab: 'overview',     // Default tab to show: 'overview', 'timeline', 'practitioners'
        chartColors: {
            primary: '#013160',     // Deep Blue
            accent: '#71BED2',      // Light Blue
            highlight: '#FBB514'    // Yellow
        },
        dateFormat: 'MM/DD/YYYY',   // Date format for display
        currencySymbol: '$'         // Currency symbol
    },
    
    // Alert Thresholds (used in Smart Alerts feature)
    alerts: {
        lowRevenueThreshold: 0.8,   // Alert if revenue is below 80% of goal
        highCancellationRate: 0.15, // Alert if cancellation rate above 15%
        lowUtilizationRate: 0.6     // Alert if practitioner utilization below 60%
    },
    
    // Feature Descriptions (shown in settings panel)
    featureInfo: {
        heatmap: {
            name: 'Interactive Heatmap',
            description: 'Visualize busiest appointment times by day and hour',
            category: 'analytics'
        },
        clientRetention: {
            name: 'Client Retention',
            description: 'Track repeat visits, loyalty, and top clients',
            category: 'analytics'
        },
        scheduleOptimization: {
            name: 'Schedule Optimization',
            description: 'Identify gaps and improve scheduling efficiency',
            category: 'analytics'
        },
        goals: {
            name: 'Goal Tracking',
            description: 'Set and monitor revenue and appointment targets',
            category: 'business'
        },
        alerts: {
            name: 'Smart Alerts',
            description: 'Get intelligent business recommendations',
            category: 'business'
        },
        businessIntelligence: {
            name: 'Business Intelligence',
            description: 'Comprehensive funnel analysis and conversion metrics',
            category: 'business'
        },
        export: {
            name: 'Export Tools',
            description: 'Download CSV reports and print dashboard',
            category: 'reporting'
        },
        advancedCharts: {
            name: 'Advanced Charts',
            description: 'Additional detailed visualizations and trends',
            category: 'analytics'
        },
        paymentAnalysis: {
            name: 'Payment Analysis',
            description: 'Breakdown by payment method and processing fees',
            category: 'business'
        }
    }
};

// Feature Categories for Organization
const FEATURE_CATEGORIES = {
    analytics: '📊 Analytics & Insights',
    business: '💼 Business Intelligence',
    reporting: '📤 Export & Reporting'
};

// Export configuration
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, FEATURE_CATEGORIES };
}
