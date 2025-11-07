/**
 * Main Module
 *
 * Entry point for the dashboard - handles initialization and orchestration
 *
 * Key Functions:
 * - initializeDashboard() - Main initialization function
 * - toggleCollapse() - Collapsible section handler
 * - showEmptyState() - Show empty state UI
 * - hideEmptyState() - Hide empty state UI
 * - DOMContentLoaded handler - Setup on page load
 */

import { initializeSettings, openSettingsModal, closeSettingsModal, saveFranchiseSettings } from './settings.js';
import { initializeModalListeners, closeModal } from './modals.js';
import { populateFilters, applyFilters, setQuickFilter, refreshData } from './filters.js';
import { renderAllTabs, switchTab } from './tabs.js';
import {
    initializeLeadsFileUpload,
    initializeLeadsConvertedFileUpload,
    initializeMembershipsFileUpload,
    openUploadModal,
    closeUploadModal
} from './upload.js';
import { appointmentsData } from './data.js';

// Toggle collapsible sections
export function toggleCollapse(contentId, iconId) {
    const content = document.getElementById(contentId);
    const icon = document.getElementById(iconId);

    content.classList.toggle('collapsed');
    icon.classList.toggle('collapsed');
}

// Show empty state
export function showEmptyState() {
    document.getElementById('emptyState').style.display = 'flex';
    document.getElementById('mainTabs').style.display = 'none';
    document.getElementById('filtersSection').style.display = 'none';
}

// Hide empty state
export function hideEmptyState() {
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('mainTabs').style.display = 'flex';
    document.getElementById('filtersSection').style.display = 'block';
}

// Initialize Dashboard
export function initializeDashboard() {
    if (appointmentsData.length === 0) return;

    hideEmptyState();

    document.getElementById('filtersSection').style.display = 'block';
    document.getElementById('mainTabs').style.display = 'flex';

    populateFilters();
    applyFilters(renderAllTabs); // Apply initial filters and render
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', function () {
    // Load saved settings
    initializeSettings();

    // Initialize modal listeners
    initializeModalListeners();

    // Initialize file upload handlers
    initializeLeadsFileUpload(
        () => applyFilters(renderAllTabs),
        renderAllTabs,
        hideEmptyState
    );

    initializeLeadsConvertedFileUpload(
        () => applyFilters(renderAllTabs),
        renderAllTabs,
        hideEmptyState
    );

    initializeMembershipsFileUpload(
        renderAllTabs,
        hideEmptyState
    );

    // TODO: Initialize payroll and attendance zip handlers

    // Show empty state initially
    showEmptyState();

    // Set up tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const tabName = this.getAttribute('data-tab');
            if (tabName) {
                switchTab(tabName);
            }
        });
    });
});

// Make functions globally accessible for inline onclick handlers
window.toggleCollapse = toggleCollapse;
window.initializeDashboard = initializeDashboard;
window.openUploadModal = openUploadModal;
window.closeUploadModal = closeUploadModal;
window.openSettingsModal = openSettingsModal;
window.closeSettingsModal = closeSettingsModal;
window.saveFranchiseSettings = saveFranchiseSettings;
window.closeModal = closeModal;
window.setQuickFilter = setQuickFilter;
window.refreshData = refreshData;
window.switchTab = switchTab;

// Export for use in other modules
export { renderAllTabs, applyFilters };
