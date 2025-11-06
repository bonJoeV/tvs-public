// Global State - Data Storage
export let appointmentsData = [];
export let leadsData = [];
export let leadsConvertedData = [];
export let membershipsData = [];
export let membershipCancellationsData = [];
export let filteredAppointments = [];
export let filteredMemberships = [];
export let filteredLeads = [];
export let filteredLeadsConverted = [];
export let filteredCancellations = [];
export let filteredTimeTracking = [];
export let allCharts = {};
export let membershipTypes = {};
export let salesByStaff = {};
export let staffEmailToName = {}; // Map staff email to full name

// Setters for data
export function setAppointmentsData(data) { appointmentsData = data; }
export function setLeadsData(data) { leadsData = data; }
export function setLeadsConvertedData(data) { leadsConvertedData = data; }
export function setMembershipsData(data) { membershipsData = data; }
export function setMembershipCancellationsData(data) { membershipCancellationsData = data; }
export function setFilteredAppointments(data) { filteredAppointments = data; }
export function setFilteredMemberships(data) { filteredMemberships = data; }
export function setFilteredLeads(data) { filteredLeads = data; }
export function setFilteredLeadsConverted(data) { filteredLeadsConverted = data; }
export function setFilteredCancellations(data) { filteredCancellations = data; }
export function setFilteredTimeTracking(data) { filteredTimeTracking = data; }
export function setAllCharts(data) { allCharts = data; }
export function setMembershipTypes(data) { membershipTypes = data; }
export function setSalesByStaff(data) { salesByStaff = data; }
export function setStaffEmailToName(data) { staffEmailToName = data; }
