// Officials Dashboard JavaScript

// Toast Notification System
function showToast(message, type = 'success', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `transform transition-all duration-300 ease-in-out translate-x-full opacity-0`;
    
    const bgColors = {
        'success': 'bg-emerald-500',
        'error': 'bg-red-500',
        'warning': 'bg-amber-500',
        'info': 'bg-blue-500'
    };
    
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <div class="${bgColors[type]} text-white px-6 py-4 rounded-lg shadow-2xl flex items-center space-x-3 min-w-[320px] max-w-md">
            <i class="fas ${icons[type]} text-2xl"></i>
            <p class="font-medium flex-1">${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" class="text-white hover:text-gray-200 transition-colors">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    }, 10);
    
    // Auto dismiss
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Global variables - moved outside DOMContentLoaded for alert system
let currentFilters = {
    state: '',
    city: '',
    county: '',
    zipcode: '',
    report_type: '',
    severity: '',
    status: '',
    timeframe: '',
    timePeriod: 'live'
};

// Make currentFilters accessible globally
window.currentFilters = currentFilters;

document.addEventListener('DOMContentLoaded', function() {
    // Other variables remain in DOMContentLoaded scope
    let currentPage = 1;
    const rowsPerPage = 20;
    let totalReports = 0;
    let allReports = [];
    let chartGranularity = 'day'; // 'hour' or 'day'
    let locationGroupBy = 'zipcode'; // 'zipcode', 'city', 'county', or 'state'
    let cachedChartReports = []; // Cache reports for chart updates
    let showAllColumns = false; // Column toggle state
    
    // ===== NEW HELPER FUNCTIONS =====
    function capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    function formatTimeAgo(timestamp) {
        if (!timestamp) return 'unknown time';
        const now = new Date();
        const past = new Date(timestamp);
        const seconds = Math.floor((now - past) / 1000);
    
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " years ago";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        return Math.floor(seconds) + " seconds ago";
    }
    // ===== END NEW HELPER FUNCTIONS =====
    // Define column sets
    const conciseColumns = ['report_type', 'timestamp', 'city', 'state', 'severity', 'status', 'ai_tags', 'manual_tags'];
    const allColumns = [
        'report_id', 'report_type', 'description', 'severity', 'status', 
        'street_address', 'city', 'state', 'county', 'zip_code',
        'timestamp', 'when_happened', 'affected_count', 'specific_type',
        'reporter_name', 'reporter_contact', 'ai_overall_summary', 'ai_media_summary',
        'ai_tags', 'manual_tags', 'ai_confidence',
        'reviewed_by', 'reviewed_at', 'exclude_from_analysis', 'exclusion_reason'
    ];
    
    // Initialize dashboard
    initializeFilters();
    initializeEventListeners();
    loadReportsData();
    
    // Listen for chart granularity changes
    document.addEventListener('chartGranularityChange', function(e) {
        chartGranularity = e.detail.granularity;
        if (cachedChartReports.length > 0) {
            updateTimeChart(cachedChartReports);
        }
    });
    
    // Initialize location filters
    async function initializeFilters() {
        try {
            // Load states
            const response = await fetch('/api/locations/states');
            const data = await response.json();
            
            if (data.success) {
                const stateSelect = document.getElementById('stateFilter');
                data.states.forEach(state => {
                    const option = document.createElement('option');
                    option.value = state.code;
                    option.textContent = state.name;
                    stateSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading states:', error);
        }
    }
    
    // Initialize all event listeners
    function initializeEventListeners() {
        // Location filters
        document.getElementById('stateFilter').addEventListener('change', handleStateChange);
        document.getElementById('cityFilter').addEventListener('change', handleCityChange);
        document.getElementById('countyFilter').addEventListener('change', handleCountyChange);
        document.getElementById('zipcodeFilter').addEventListener('change', handleZipcodeChange);
        
        // Report type filter
        document.getElementById('reportTypeFilter').addEventListener('change', function() {
            currentFilters.report_type = this.value;
            loadReportsData();
        });
        
        // Severity filter
        document.getElementById('severityFilter').addEventListener('change', function() {
            currentFilters.severity = this.value;
            loadReportsData();
        });
        
        // Status filter
        document.getElementById('statusFilter').addEventListener('change', function() {
            currentFilters.status = this.value;
            loadReportsData();
        });
        
        // Timeframe filter
        document.getElementById('timeframeFilter').addEventListener('change', function() {
            currentFilters.timeframe = this.value;
            loadReportsData();
        });
        
        // Tag filter (client-side)
        document.getElementById('tagFilter').addEventListener('change', function() {
            currentFilters.tag = this.value;
            applyClientSideFilters();
        });
        
        // Clear filters button
        document.getElementById('clearFiltersBtn').addEventListener('click', clearAllFilters);
        
        // Export buttons
        document.getElementById('exportCsvBtn').addEventListener('click', (e) => exportData('csv', e));
        document.getElementById('exportExcelBtn').addEventListener('click', (e) => exportData('xlsx', e));
        document.getElementById('exportPdfBtn').addEventListener('click', (e) => exportData('pdf', e));
        document.getElementById('exportPngBtn').addEventListener('click', (e) => exportData('png', e));
        
        // Search input
        document.getElementById('searchInput').addEventListener('input', debounce(handleSearch, 300));
        
        // Pagination
        document.getElementById('prevPageBtn').addEventListener('click', () => changePage(-1));
        document.getElementById('nextPageBtn').addEventListener('click', () => changePage(1));
        
        // Column toggle
        document.getElementById('toggleColumnsBtn').addEventListener('click', toggleColumns);
        
        // Load column preference from localStorage
        const savedColumnPref = localStorage.getItem('showAllColumns');
        if (savedColumnPref !== null) {
            showAllColumns = savedColumnPref === 'true';
            updateColumnToggleButton();
        }
    }
    
    // Handle state selection
    async function handleStateChange() {
        const stateCode = this.value;
        const citySelect = document.getElementById('cityFilter');
        const countySelect = document.getElementById('countyFilter');
        const zipcodeSelect = document.getElementById('zipcodeFilter');
        
        // Reset dependent dropdowns
        citySelect.innerHTML = '<option value="">All Cities</option>';
        countySelect.innerHTML = '<option value="">All Counties</option>';
        zipcodeSelect.innerHTML = '<option value="">All ZIP Codes</option>';
        
        citySelect.disabled = !stateCode;
        countySelect.disabled = true;
        zipcodeSelect.disabled = true;
        
        currentFilters.state = stateCode;
        currentFilters.city = '';
        currentFilters.county = '';
        currentFilters.zipcode = '';
        window.currentFilters = currentFilters; // Ensure global reference is updated
        
        if (stateCode) {
            try {
                const response = await fetch(`/api/locations/cities/${stateCode}`);
                const data = await response.json();
                
                if (data.success) {
                    data.cities.forEach(city => {
                        const option = document.createElement('option');
                        option.value = city.name;
                        option.textContent = city.name;
                        citySelect.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading cities:', error);
            }
        }
    }
    
    // Handle city selection
    async function handleCityChange() {
        const cityName = this.value;
        const stateCode = document.getElementById('stateFilter').value;
        const countySelect = document.getElementById('countyFilter');
        const zipcodeSelect = document.getElementById('zipcodeFilter');
        
        countySelect.innerHTML = '<option value="">All Counties</option>';
        zipcodeSelect.innerHTML = '<option value="">All ZIP Codes</option>';
        
        countySelect.disabled = !cityName;
        zipcodeSelect.disabled = !cityName;
        
        currentFilters.city = cityName;
        currentFilters.county = '';
        currentFilters.zipcode = '';
        
        if (cityName && stateCode) {
            try {
                // Load counties
                const countiesResponse = await fetch(`/api/locations/counties/${stateCode}/${encodeURIComponent(cityName)}`);
                const countiesData = await countiesResponse.json();
                
                if (countiesData.success) {
                    countiesData.counties.forEach(county => {
                        const option = document.createElement('option');
                        option.value = county.name;
                        option.textContent = county.name;
                        countySelect.appendChild(option);
                    });
                }
                
                // Load ZIP codes
                const zipcodesResponse = await fetch(`/api/locations/zipcodes/${stateCode}?city=${encodeURIComponent(cityName)}`);
                const zipcodesData = await zipcodesResponse.json();
                
                if (zipcodesData.success) {
                    zipcodesData.zipcodes.forEach(zip => {
                        const option = document.createElement('option');
                        option.value = zip.zipcode;
                        option.textContent = `${zip.zipcode}`;
                        zipcodeSelect.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading location data:', error);
            }
        }
    }
    
    // Handle county selection
    function handleCountyChange() {
        currentFilters.county = this.value;
    }
    
    // Handle ZIP code selection
    function handleZipcodeChange() {
        currentFilters.zipcode = this.value;
    }
    
    // Clear all filters
    function clearAllFilters() {
        // Reset all select elements
        document.getElementById('stateFilter').value = '';
        document.getElementById('cityFilter').value = '';
        document.getElementById('countyFilter').value = '';
        document.getElementById('zipcodeFilter').value = '';
        document.getElementById('reportTypeFilter').value = '';
        document.getElementById('severityFilter').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('timeframeFilter').value = '';
        document.getElementById('tagFilter').value = '';
        document.getElementById('searchInput').value = '';
        
        // Disable dependent dropdowns
        document.getElementById('cityFilter').disabled = true;
        document.getElementById('countyFilter').disabled = true;
        document.getElementById('zipcodeFilter').disabled = true;
        
        // Reset filters object
        currentFilters = {
            state: '',
            city: '',
            county: '',
            zipcode: '',
            report_type: '',
            severity: '',
            status: '',
            timeframe: '',
            tag: '',
            timePeriod: 'live'
        };
        
        currentPage = 1;
        loadReportsData();
    }
    
    // Load reports data from API
    async function loadReportsData() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.remove('hidden');
        loadingOverlay.classList.add('flex');
        
        try {
            const params = new URLSearchParams();
            
            // Add all filters (except tag which is client-side)
            if (currentFilters.state) params.append('state', currentFilters.state);
            if (currentFilters.city) params.append('city', currentFilters.city);
            if (currentFilters.county) params.append('county', currentFilters.county);
            if (currentFilters.zipcode) params.append('zipcode', currentFilters.zipcode);
            if (currentFilters.report_type) params.append('report_type', currentFilters.report_type);
            if (currentFilters.severity) params.append('severity', currentFilters.severity);
            if (currentFilters.status) params.append('status', currentFilters.status);
            if (currentFilters.timeframe) params.append('timeframe', currentFilters.timeframe);
            
            // Add pagination
            params.append('limit', rowsPerPage);
            params.append('offset', (currentPage - 1) * rowsPerPage);
            
            console.log('Fetching reports with params:', params.toString());
            
            const response = await fetch(`/api/community-reports?${params}`);
            const data = await response.json();
            
           if (data.success) {
                allReports = data.reports;
                totalReports = data.stats.total_reports; // Use new stats object
                
                // 1. Update top stat cards
                updateQuickStats(data.stats); // <-- Renamed to avoid confusion
                
                // 2. Update critical alerts list
                updateCriticalAlertsList(allReports);
                
                // 3. Apply filters and render table
                applyClientSideFilters();
                
                // 4. Update pagination controls
                updatePagination();

                // 5. Update table summary stats (this is your original function)
                updateStatsCards(allReports); 
                
                // 6. Update charts
                updateCharts(allReports);
            } else {
                console.error('Failed to load reports:', data.error);
                showError('Failed to load reports: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            showError('Error loading reports. Please try again.');
        } finally {
            loadingOverlay.classList.add('hidden');
            loadingOverlay.classList.remove('flex');
        }
    }
    
    // Apply client-side filters (tag + search)
    function applyClientSideFilters() {
        let filtered = [...allReports];
        
        // Apply tag filter
        if (currentFilters.tag) {
            filtered = filtered.filter(report => {
                const aiTags = report.ai_tags ? parseAITags(report.ai_tags) : [];
                const manualTags = report.manual_tags ? parseAITags(report.manual_tags) : [];
                const allTags = [...aiTags, ...manualTags];
                return allTags.some(tag => 
                    tag.toLowerCase().replace(/_/g, '-') === currentFilters.tag.toLowerCase().replace(/_/g, '-')
                );
            });
        }
        
        // Apply search filter
        const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
        if (searchTerm) {
            filtered = filtered.filter(report => (
                report.description?.toLowerCase().includes(searchTerm) ||
                report.city?.toLowerCase().includes(searchTerm) ||
                report.state?.toLowerCase().includes(searchTerm) ||
                report.zip_code?.includes(searchTerm) ||
                report.report_type?.toLowerCase().includes(searchTerm) ||
                report.specific_type?.toLowerCase().includes(searchTerm)
            ));
        }
        
        renderReportsTable(filtered);
    }
    
    // Render reports table
    function renderReportsTable(reports) {
        // Render table headers
        renderTableHeaders();
        
        const tbody = document.getElementById('reportsTableBody');
        tbody.innerHTML = '';
        
        if (reports.length === 0) {
            const colspan = showAllColumns ? 25 : 8;
            tbody.innerHTML = `
                <tr>
                    <td colspan="${colspan}" class="px-6 py-12 text-center text-gray-500">
                        <i class="fas fa-inbox text-4xl mb-3 text-gray-300"></i>
                        <p class="text-lg font-semibold">No reports found</p>
                        <p class="text-sm">Try adjusting your filters</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        reports.forEach(report => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 transition-colors cursor-pointer';
            row.onclick = () => viewReportDetails(report);
            
            // Format timestamp
            const timestamp = new Date(report.timestamp);
            const formattedDate = timestamp.toLocaleDateString();
            const formattedTime = timestamp.toLocaleTimeString();
            
            // Check for attachments
            let hasAttachments = false;
            let attachmentCount = 0;
            if (report.attachment_urls) {
                try {
                    const urls = JSON.parse(report.attachment_urls);
                    hasAttachments = urls && urls.length > 0;
                    attachmentCount = urls.length;
                } catch (e) {
                    // Silent fail
                }
            }
            if (!hasAttachments && report.media_urls) {
                try {
                    const urls = Array.isArray(report.media_urls) ? report.media_urls : JSON.parse(report.media_urls);
                    hasAttachments = urls && urls.length > 0;
                    attachmentCount = urls.length;
                } catch (e) {
                    // Silent fail
                }
            }
            
            // Severity badge
            const severityColors = {
                'low': 'bg-green-100 text-green-800',
                'moderate': 'bg-yellow-100 text-yellow-800',
                'high': 'bg-orange-100 text-orange-800',
                'critical': 'bg-red-100 text-red-800'
            };
            const severityClass = severityColors[report.severity] || 'bg-gray-100 text-gray-800';
            
            // Status badge
            const statusColors = {
                'pending': 'bg-blue-100 text-blue-800',
                'reviewed': 'bg-purple-100 text-purple-800',
                'resolved': 'bg-green-100 text-green-800',
                'closed': 'bg-gray-100 text-gray-800'
            };
            const statusClass = statusColors[report.status] || 'bg-gray-100 text-gray-800';
            
            // Report type icon
            const typeIcons = {
                'health': 'fa-heartbeat text-red-500',
                'environmental': 'fa-leaf text-green-500',
                'weather': 'fa-cloud-rain text-blue-500',
                'emergency': 'fa-exclamation-triangle text-red-600'
            };
            const typeIcon = typeIcons[report.report_type] || 'fa-file-alt text-gray-500';
            
            // Build row HTML based on column selection
            let rowHTML = '';
            
            if (showAllColumns) {
                // Show all columns
                const aiTags = report.ai_tags ? parseAITags(report.ai_tags) : [];
                const manualTags = report.manual_tags ? parseAITags(report.manual_tags) : [];
                
                rowHTML = `
                    <td class="px-4 py-3 text-xs text-gray-600">${report.report_id ? report.report_id.substring(0, 8) + '...' : '-'}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm">
                        <div class="flex items-center">
                            <i class="fas ${typeIcon} mr-2"></i>
                            <span class="font-medium">${capitalize(report.report_type)}</span>
                        </div>
                    </td>
                    <td class="px-4 py-3 text-sm max-w-xs truncate">${report.description || '-'}</td>
                    <td class="px-4 py-3 whitespace-nowrap"><span class="px-2 py-1 rounded-full text-xs font-semibold ${severityClass}">${capitalize(report.severity)}</span></td>
                    <td class="px-4 py-3 whitespace-nowrap"><span class="px-2 py-1 rounded-full text-xs font-semibold ${statusClass}">${capitalize(report.status)}</span></td>
                    <td class="px-4 py-3 text-sm">${report.street_address || '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.city || '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.state || '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.county || '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.zip_code || '-'}</td>
                    <td class="px-4 py-3 text-xs">${formattedDate}<br>${formattedTime}</td>
                    <td class="px-4 py-3 text-xs">${report.when_happened ? formatTimeframe(report.when_happened) : '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.affected_count || '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.specific_type || '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.reporter_name || 'Anonymous'}</td>
                    <td class="px-4 py-3 text-sm">${report.reporter_contact || '-'}</td>
                    <td class="px-4 py-3 text-xs max-w-xs truncate">${report.ai_overall_summary || '-'}</td>
                    <td class="px-4 py-3 text-xs max-w-xs truncate">${report.ai_media_summary || '-'}</td>
                    <td class="px-4 py-3">
                        <div class="flex flex-wrap gap-1">
                            ${aiTags.map(tag => `<span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs">${tag}</span>`).join('')}
                            ${aiTags.length === 0 ? '-' : ''}
                        </div>
                    </td>
                    <td class="px-4 py-3">
                        <div class="flex flex-wrap gap-1">
                            ${manualTags.map(tag => `<span class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">${tag}</span>`).join('')}
                            ${manualTags.length === 0 ? '-' : ''}
                        </div>
                    </td>
                    <td class="px-4 py-3 text-sm">${report.ai_confidence !== null && report.ai_confidence !== undefined ? (report.ai_confidence * 100).toFixed(0) + '%' : '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.reviewed_by || '-'}</td>
                    <td class="px-4 py-3 text-xs">${report.reviewed_at ? new Date(report.reviewed_at).toLocaleString() : '-'}</td>
                    <td class="px-4 py-3 text-center">${report.exclude_from_analysis ? '<i class="fas fa-check-circle text-orange-500"></i>' : '-'}</td>
                    <td class="px-4 py-3 text-sm">${report.exclusion_reason || '-'}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm">
                        <button class="text-blue-600 hover:text-blue-800 font-medium" onclick="event.stopPropagation(); viewReportDetails(${JSON.stringify(report).replace(/"/g, '&quot;')})">
                            <i class="fas fa-eye mr-1"></i>View
                        </button>
                    </td>
                `;
            } else {
                // Show concise columns with tags
                const aiTags = report.ai_tags ? parseAITags(report.ai_tags) : [];
                const manualTags = report.manual_tags ? parseAITags(report.manual_tags) : [];
                
                rowHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <div class="flex items-center">
                            <i class="fas ${typeIcon} mr-2"></i>
                            <span class="font-medium text-gray-900">${capitalize(report.report_type)}</span>
                            ${hasAttachments ? `<i class="fas fa-paperclip ml-2 text-blue-500" title="${attachmentCount} attachment(s)"></i>` : ''}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <div>${formattedDate}</div>
                        <div class="text-xs text-gray-400">${formattedTime}</div>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-900">
                        <div class="font-medium">${report.city}, ${report.state}</div>
                        <div class="text-xs text-gray-500">${report.county || 'Unknown County'}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${severityClass}">
                            ${capitalize(report.severity)}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusClass}">
                            ${capitalize(report.status)}
                        </span>
                    </td>
                    <td class="px-6 py-4">
                        <div class="flex flex-wrap gap-1 max-w-xs">
                            ${aiTags.slice(0, 3).map(tag => `
                                <span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                                    ${tag}
                                </span>
                            `).join('')}
                            ${aiTags.length > 3 ? `<span class="text-xs text-gray-400">+${aiTags.length - 3}</span>` : ''}
                            ${aiTags.length === 0 ? '<span class="text-xs text-gray-400">-</span>' : ''}
                        </div>
                    </td>
                    <td class="px-6 py-4">
                        <div class="flex flex-wrap gap-1 max-w-xs">
                            ${manualTags.slice(0, 3).map(tag => `
                                <span class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                                    ${tag}
                                </span>
                            `).join('')}
                            ${manualTags.length > 3 ? `<span class="text-xs text-gray-400">+${manualTags.length - 3}</span>` : ''}
                            ${manualTags.length === 0 ? '<span class="text-xs text-gray-400">-</span>' : ''}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <button class="text-blue-600 hover:text-blue-800 font-medium" onclick="event.stopPropagation(); viewReportDetails(${JSON.stringify(report).replace(/"/g, '&quot;')})">
                            <i class="fas fa-eye mr-1"></i>View
                        </button>
                    </td>
                `;
            }
            
            row.innerHTML = rowHTML;
            
            tbody.appendChild(row);
        });
    }
    
    // Update pagination controls
    function updatePagination() {
        const totalPages = Math.ceil(totalReports / rowsPerPage);
        document.getElementById('currentPageInfo').textContent = `Page ${currentPage} of ${totalPages} (${totalReports} total reports)`;
        
        document.getElementById('prevPageBtn').disabled = currentPage === 1;
        document.getElementById('nextPageBtn').disabled = currentPage >= totalPages;
    }
    
    // Change page
    function changePage(direction) {
        currentPage += direction;
        loadReportsData();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Update stats cards
    function updateStatsCards(reports) {
        // Count by severity
        const severityCounts = {
            critical: 0,
            high: 0,
            moderate: 0,
            low: 0
        };
        
        // Count by type
        const typeCounts = {
            health: 0,
            environmental: 0,
            weather: 0,
            emergency: 0
        };
        
        // Count by status
        const statusCounts = {
            pending: 0,
            reviewed: 0,
            resolved: 0
        };
        
        reports.forEach(report => {
            if (severityCounts.hasOwnProperty(report.severity)) {
                severityCounts[report.severity]++;
            }
            if (typeCounts.hasOwnProperty(report.report_type)) {
                typeCounts[report.report_type]++;
            }
            if (statusCounts.hasOwnProperty(report.status)) {
                statusCounts[report.status]++;
            }
        });
        
        // Update DOM (you can customize these based on your stats cards)
        document.getElementById('totalReportsCount').textContent = totalReports;
        document.getElementById('criticalReportsCount').textContent = severityCounts.critical + severityCounts.high;
        document.getElementById('pendingReportsCount').textContent = statusCounts.pending;
        document.getElementById('resolvedReportsCount').textContent = statusCounts.resolved;
    }

    // ===== NEW FUNCTION for "Quick Stats" =====
    function updateQuickStats(stats) {
        // 1. Active Alerts
        const activeEl = document.querySelector('#quick-stat-active h3');
        const activeSubEl = document.querySelector('#quick-stat-active p:last-of-type');
        if (activeEl) activeEl.textContent = stats.active_high_priority_alerts;
        if (activeSubEl) activeSubEl.textContent = `${stats.active_high_priority_alerts} High Priority`;
        
        // 2. New Cases (re-purposing Avg AQI card)
        const newCasesEl = document.querySelector('#quick-stat-new-cases h3');
        const newCasesSubEl = document.querySelector('#quick-stat-new-cases p:last-of-type');
        const newCasesLabelEl = document.querySelector('#quick-stat-new-cases p:first-of-type');
        
        if (newCasesEl) newCasesEl.textContent = stats.new_cases_this_week;
        if (newCasesLabelEl) newCasesLabelEl.textContent = 'New Cases (This Week)'; // Change label

        // Calculate trend vs last week
        let trendText = 'vs last week';
        let trendClass = 'text-gray-500';
        if (stats.new_cases_last_week > 0) {
            const trend = ((stats.new_cases_this_week - stats.new_cases_last_week) / stats.new_cases_last_week) * 100;
            if (trend > 5) {
                trendText = `<i class="fas fa-arrow-up"></i> ${trend.toFixed(0)}% vs last week`;
                trendClass = 'text-red-500';
            } else if (trend < -5) {
                trendText = `<i class="fas fa-arrow-down"></i> ${Math.abs(trend).toFixed(0)}% vs last week`;
                trendClass = 'text-green-500';
            }
        } else if (stats.new_cases_this_week > 0) {
            trendText = `<i class="fas fa-arrow-up"></i> ${stats.new_cases_this_week} new`;
            trendClass = 'text-green-500';
        }
        if (newCasesSubEl) {
            newCasesSubEl.innerHTML = trendText;
            newCasesSubEl.className = `text-sm ${trendClass} mt-1`; // Apply color
        }

        // 3. Pending Review (re-purposing Disease Cases card)
        const pendingEl = document.querySelector('#quick-stat-pending h3');
        const pendingSubEl = document.querySelector('#quick-stat-pending p:last-of-type');
        const pendingLabelEl = document.querySelector('#quick-stat-pending p:first-of-type');
        if (pendingEl) pendingEl.textContent = stats.pending_review;
        if (pendingLabelEl) pendingLabelEl.textContent = 'Pending Review'; // Change label
        if (pendingSubEl) pendingSubEl.textContent = 'Awaiting triage'; // Change sub-label

        // 4. Total Reports (re-purposing Population card)
        const totalEl = document.querySelector('#quick-stat-total h3');
        const totalSubEl = document.querySelector('#quick-stat-total p:last-of-type');
        const totalLabelEl = document.querySelector('#quick-stat-total p:first-of-type');
        if (totalEl) totalEl.textContent = stats.total_reports;
        if (totalLabelEl) totalLabelEl.textContent = 'Total Reports'; // Change label
        if (totalSubEl) totalSubEl.textContent = 'In filtered view'; // Change sub-label
    }
    
    // Handle search
    function handleSearch(event) {
        applyClientSideFilters();
    }

    // ===== NEW FUNCTION for "Critical Alerts" =====
    function updateCriticalAlertsList(reports) {
        const container = document.getElementById('critical-alerts-list-container');
        if (!container) return; // Exit if ID not found
    
        // Filter for top 3 critical/high reports from the fetched data
        const criticalReports = reports
            .filter(r => r.severity === 'high' || r.severity === 'critical')
            .slice(0, 3); // Get the first 3
    
        if (criticalReports.length === 0) {
            container.innerHTML = `
                <div class="border-l-4 border-green-500 bg-green-50 p-4 rounded-r-xl">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <h4 class="font-semibold text-navy-800 mb-1">No Critical Alerts</h4>
                            <p class="text-sm text-gray-700">No high or critical severity reports found in the current view.</p>
                        </div>
                        <i class="fas fa-check-circle text-green-500 ml-4 mt-1"></i>
                    </div>
                </div>
            `;
            return;
        }
    
        // Build new HTML for the alerts
        container.innerHTML = criticalReports.map(report => {
            let displaySeverity, colorClass, borderColor, iconClass;
            
            // Map BQ severity to your HTML's style
            if (report.severity === 'critical') {
                displaySeverity = 'HIGH';
                colorClass = 'bg-red-500';
                borderColor = 'border-red-500';
                iconClass = 'text-red-600';
            } else { // 'high'
                displaySeverity = 'MEDIUM';
                colorClass = 'bg-amber-500';
                borderColor = 'border-amber-500';
                iconClass = 'text-amber-600';
            }

            const timeAgo = formatTimeAgo(report.timestamp);
            let title = report.specific_type || `${capitalize(report.report_type)} Report`;
            if (report.city) title += ` in ${report.city}`;
    
            return `
                <div class="border-l-4 ${borderColor} bg-gray-50 p-4 rounded-r-xl cursor-pointer hover:bg-white transition-all"
                     onclick="viewReportDetails(${JSON.stringify(report).replace(/"/g, '&quot;')})">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center space-x-2 mb-2">
                                <span class="px-2 py-1 ${colorClass} text-white text-xs font-bold rounded-full">${displaySeverity}</span>
                                <span class="text-sm text-gray-600">${timeAgo}</span>
                            </div>
                            <h4 class="font-semibold text-navy-800 mb-1">${title}</h4>
                            <p class="text-sm text-gray-700">${(report.ai_overall_summary || report.description || 'No description').substring(0, 100)}...</p>
                        </div>
                        <button class="text-gray-500 hover:${iconClass} ml-4">
                            <i class="fas fa-arrow-right"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    
    // Export data
    async function exportData(format, event) {
        try {
            const params = new URLSearchParams();
            
            // Add all current filters
            if (currentFilters.state) params.append('state', currentFilters.state);
            if (currentFilters.city) params.append('city', currentFilters.city);
            if (currentFilters.county) params.append('county', currentFilters.county);
            if (currentFilters.zipcode) params.append('zipcode', currentFilters.zipcode);
            if (currentFilters.report_type) params.append('report_type', currentFilters.report_type);
            if (currentFilters.severity) params.append('severity', currentFilters.severity);
            if (currentFilters.status) params.append('status', currentFilters.status);
            if (currentFilters.timeframe) params.append('timeframe', currentFilters.timeframe);
            
            // Show loading
            const exportBtn = event.target.closest('button');
            const originalHTML = exportBtn.innerHTML;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Exporting...';
            exportBtn.disabled = true;
            
            // Open download in new window
            window.location.href = `/api/export-reports/${format}?${params}`;
            
            // Reset button after delay
            setTimeout(() => {
                exportBtn.innerHTML = originalHTML;
                exportBtn.disabled = false;
            }, 2000);
            
        } catch (error) {
            console.error('Export error:', error);
            showError('Failed to export data');
        }
    }
    
    // View report details (modal)
    window.viewReportDetails = function(report) {
        const modal = document.getElementById('reportDetailModal');
        const modalBody = document.getElementById('reportDetailBody');
        
        // Parse attachment URLs
        let attachmentUrls = [];
        if (report.attachment_urls) {
            try {
                attachmentUrls = JSON.parse(report.attachment_urls);
            } catch (e) {
                console.error('Failed to parse attachment_urls:', e);
            }
        }
        // Fallback to media_urls if attachment_urls is empty
        if (attachmentUrls.length === 0 && report.media_urls) {
            if (Array.isArray(report.media_urls)) {
                attachmentUrls = report.media_urls;
            } else if (typeof report.media_urls === 'string') {
                try {
                    attachmentUrls = JSON.parse(report.media_urls);
                } catch (e) {
                    // If it's a single URL string, wrap it in an array
                    if (report.media_urls.startsWith('http')) {
                        attachmentUrls = [report.media_urls];
                    }
                }
            }
        }
        
        modalBody.innerHTML = `
            <div class="space-y-6">
                <!-- Header -->
                <div class="border-b pb-4">
                    <h3 class="text-2xl font-bold text-navy-800 mb-2">${capitalize(report.report_type)} Report</h3>
                    <p class="text-gray-500 text-sm">Report ID: ${report.report_id}</p>
                </div>
                
                <!-- Details Grid -->
                <div class="grid grid-cols-2 gap-6">
                    <div>
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Date & Time</label>
                        <p class="mt-1 text-gray-900">${new Date(report.timestamp).toLocaleString()}</p>
                    </div>
                    <div>
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Severity</label>
                        <p class="mt-1"><span class="px-3 py-1 rounded-full text-sm font-semibold ${getSeverityColor(report.severity)}">${capitalize(report.severity)}</span></p>
                    </div>
                    <div>
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Location</label>
                        <p class="mt-1 text-gray-900">${report.city}, ${report.state} ${report.zip_code}</p>
                        ${report.county ? `<p class="text-sm text-gray-500">${report.county} County</p>` : ''}
                    </div>
                    <div>
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Status</label>
                        <p class="mt-1"><span class="px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(report.status)}">${capitalize(report.status)}</span></p>
                    </div>
                    ${report.specific_type ? `
                    <div class="col-span-2">
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Specific Type</label>
                        <p class="mt-1 text-gray-900">${report.specific_type}</p>
                    </div>
                    ` : ''}
                    <div class="col-span-2">
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Description</label>
                        <p class="mt-1 text-gray-900">${report.description || 'No description provided'}</p>
                    </div>
                    <div>
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">People Affected</label>
                        <p class="mt-1 text-gray-900">${report.affected_count || report.people_affected || 'Not specified'}</p>
                    </div>
                    <div>
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Timeframe</label>
                        <p class="mt-1 text-gray-900">${report.when_happened || report.timeframe ? formatTimeframe(report.when_happened || report.timeframe) : 'Not specified'}</p>
                    </div>
                    
                    ${(report.ai_overall_summary || report.ai_tags || report.ai_confidence) ? `
                    <div class="col-span-2 border-t pt-4">
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3 block">
                            <i class="fas fa-robot mr-2 text-purple-600"></i>AI Analysis
                        </label>
                        <div class="bg-purple-50 rounded-lg p-4 space-y-3">
                            ${report.ai_overall_summary ? `
                            <div>
                                <div class="text-xs font-semibold text-purple-700 uppercase mb-1">Summary</div>
                                <p class="text-sm text-gray-800">${report.ai_overall_summary}</p>
                            </div>
                            ` : ''}
                            ${report.ai_tags ? `
                            <div>
                                <div class="text-xs font-semibold text-purple-700 uppercase mb-2">Tags</div>
                                <div class="flex flex-wrap gap-1">
                                    ${parseAITags(report.ai_tags).map(tag => `
                                        <span class="px-2 py-1 bg-purple-200 text-purple-800 rounded-full text-xs font-medium">
                                            ${tag}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                            ` : ''}
                            ${report.ai_confidence !== null && report.ai_confidence !== undefined ? `
                            <div>
                                <div class="text-xs font-semibold text-purple-700 uppercase mb-1">Confidence Score</div>
                                <div class="flex items-center gap-2">
                                    <div class="flex-1 bg-gray-200 rounded-full h-2">
                                        <div class="bg-purple-600 h-2 rounded-full" style="width: ${(report.ai_confidence * 100)}%"></div>
                                    </div>
                                    <span class="text-sm font-bold text-purple-800">${(report.ai_confidence * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                            ` : ''}
                            ${report.ai_media_summary ? `
                            <div>
                                <div class="text-xs font-semibold text-purple-700 uppercase mb-1">Media Analysis</div>
                                <p class="text-sm text-gray-800">${report.ai_media_summary}</p>
                            </div>
                            ` : ''}
                            ${report.ai_analyzed_at ? `
                            <div class="text-xs text-gray-500 italic">
                                Analyzed: ${new Date(report.ai_analyzed_at).toLocaleString()}
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${attachmentUrls.length > 0 ? `
                    <div class="col-span-2 border-t pt-4">
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3 block">
                            <i class="fas fa-paperclip mr-2"></i>Attachments (${attachmentUrls.length})
                        </label>
                        <div class="grid grid-cols-3 gap-3">
                            ${attachmentUrls.map((url, index) => {
                                const isImage = url.match(/\.(jpg|jpeg|png|gif)($|\?)/i);
                                return `
                                    <div class="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                                        ${isImage ? `
                                            <a href="${url}" target="_blank" class="block">
                                                <img src="${url}" alt="Attachment ${index + 1}" class="w-full h-32 object-cover">
                                                <div class="p-2 bg-gray-50 text-xs text-center text-gray-600">
                                                    <i class="fas fa-search-plus mr-1"></i>Click to view full size
                                                </div>
                                            </a>
                                        ` : `
                                            <a href="${url}" target="_blank" class="block p-4 bg-gray-50 hover:bg-gray-100 text-center">
                                                <i class="fas fa-file text-3xl text-gray-400 mb-2"></i>
                                                <div class="text-xs text-gray-600">Attachment ${index + 1}</div>
                                                <div class="text-xs text-blue-600 mt-1">Click to open</div>
                                            </a>
                                        `}
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${!report.is_anonymous ? `
                    <div class="col-span-2 border-t pt-4">
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Contact Information</label>
                        <div class="mt-2 space-y-1">
                            <p class="text-gray-900"><i class="fas fa-user mr-2 text-gray-400"></i>${report.contact_name || report.reporter_name}</p>
                            ${report.contact_email || report.reporter_contact ? `<p class="text-gray-900"><i class="fas fa-envelope mr-2 text-gray-400"></i>${report.contact_email || report.reporter_contact}</p>` : ''}
                            ${report.contact_phone ? `<p class="text-gray-900"><i class="fas fa-phone mr-2 text-gray-400"></i>${report.contact_phone}</p>` : ''}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- Review Controls Section -->
                    <div class="col-span-2 border-t pt-4">
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-4 block">
                            <i class="fas fa-edit mr-2 text-blue-600"></i>Review & Update
                        </label>
                        <div class="bg-blue-50 rounded-lg p-4 space-y-4">
                            <!-- Status Update -->
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="text-xs font-semibold text-blue-800 uppercase mb-2 block">Update Status</label>
                                    <select id="statusSelect_${report.report_id}" class="w-full px-3 py-2 border border-blue-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                                        <option value="Pending" ${report.status === 'Pending' ? 'selected' : ''}>Pending</option>
                                        <option value="Valid - Action Required" ${report.status === 'Valid - Action Required' ? 'selected' : ''}>Valid - Action Required</option>
                                        <option value="Valid - Monitoring" ${report.status === 'Valid - Monitoring' ? 'selected' : ''}>Valid - Monitoring</option>
                                        <option value="Under Review" ${report.status === 'Under Review' ? 'selected' : ''}>Under Review</option>
                                        <option value="Closed - Invalid" ${report.status === 'Closed - Invalid' ? 'selected' : ''}>Closed - Invalid</option>
                                        <option value="Resolved" ${report.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="text-xs font-semibold text-blue-800 uppercase mb-2 block">Reviewer Name</label>
                                    <input type="text" id="reviewerName_${report.report_id}" value="${report.reviewed_by || ''}" placeholder="Enter your name" class="w-full px-3 py-2 border border-blue-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                                </div>
                            </div>
                            
                            <!-- Manual Tags -->
                            <div>
                                <label class="text-xs font-semibold text-blue-800 uppercase mb-2 block">Add Manual Tags</label>
                                
                                <!-- Preset Tag Buttons -->
                                <div class="flex flex-wrap gap-2 mb-3">
                                    <button type="button" onclick="togglePresetTag('${report.report_id}', 'follow-up-needed')" 
                                        class="preset-tag-btn px-3 py-1 rounded-full text-xs font-medium border-2 transition-all
                                        ${report.manual_tags && report.manual_tags.includes('follow-up-needed') ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-blue-700 border-blue-300 hover:border-blue-500'}">
                                        <i class="fas fa-phone mr-1"></i>Follow-up Needed
                                    </button>
                                    <button type="button" onclick="togglePresetTag('${report.report_id}', 'high-priority')" 
                                        class="preset-tag-btn px-3 py-1 rounded-full text-xs font-medium border-2 transition-all
                                        ${report.manual_tags && report.manual_tags.includes('high-priority') ? 'bg-red-600 text-white border-red-600' : 'bg-white text-red-700 border-red-300 hover:border-red-500'}">
                                        <i class="fas fa-exclamation-triangle mr-1"></i>High Priority
                                    </button>
                                    <button type="button" onclick="togglePresetTag('${report.report_id}', 'needs-inspection')" 
                                        class="preset-tag-btn px-3 py-1 rounded-full text-xs font-medium border-2 transition-all
                                        ${report.manual_tags && report.manual_tags.includes('needs-inspection') ? 'bg-yellow-600 text-white border-yellow-600' : 'bg-white text-yellow-700 border-yellow-300 hover:border-yellow-500'}">
                                        <i class="fas fa-search mr-1"></i>Needs Inspection
                                    </button>
                                    <button type="button" onclick="togglePresetTag('${report.report_id}', 'awaiting-lab-results')" 
                                        class="preset-tag-btn px-3 py-1 rounded-full text-xs font-medium border-2 transition-all
                                        ${report.manual_tags && report.manual_tags.includes('awaiting-lab-results') ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-purple-700 border-purple-300 hover:border-purple-500'}">
                                        <i class="fas fa-flask mr-1"></i>Awaiting Lab Results
                                    </button>
                                    <button type="button" onclick="togglePresetTag('${report.report_id}', 'escalated')" 
                                        class="preset-tag-btn px-3 py-1 rounded-full text-xs font-medium border-2 transition-all
                                        ${report.manual_tags && report.manual_tags.includes('escalated') ? 'bg-orange-600 text-white border-orange-600' : 'bg-white text-orange-700 border-orange-300 hover:border-orange-500'}">
                                        <i class="fas fa-arrow-up mr-1"></i>Escalated
                                    </button>
                                    <button type="button" onclick="togglePresetTag('${report.report_id}', 'community-concern')" 
                                        class="preset-tag-btn px-3 py-1 rounded-full text-xs font-medium border-2 transition-all
                                        ${report.manual_tags && report.manual_tags.includes('community-concern') ? 'bg-green-600 text-white border-green-600' : 'bg-white text-green-700 border-green-300 hover:border-green-500'}">
                                        <i class="fas fa-users mr-1"></i>Community Concern
                                    </button>
                                </div>
                                
                                <!-- Custom Tags Input (hidden storage) -->
                                <input type="hidden" id="manualTags_${report.report_id}" value="${report.manual_tags ? parseAITags(report.manual_tags).join(', ') : ''}">
                                
                                <!-- Custom Tag Input -->
                                <div>
                                    <input type="text" id="customTag_${report.report_id}" placeholder="Add custom tag and press Enter" 
                                        class="w-full px-3 py-2 border border-blue-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        onkeypress="if(event.key==='Enter'){event.preventDefault();addCustomTag('${report.report_id}');}">
                                    <p class="text-xs text-gray-500 mt-1">Select preset tags above or add custom tags</p>
                                </div>
                                
                                <!-- Selected Tags Display -->
                                <div id="selectedTags_${report.report_id}" class="mt-2 flex flex-wrap gap-1">
                                    ${report.manual_tags ? parseAITags(report.manual_tags).map(tag => `
                                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                            ${tag}
                                            <button type="button" onclick="removeTag('${report.report_id}', '${tag}')" class="ml-1 text-blue-600 hover:text-blue-800">
                                                <i class="fas fa-times"></i>
                                            </button>
                                        </span>
                                    `).join('') : ''}
                                </div>
                            </div>
                            
                            <!-- Exclusion Controls -->
                            <div class="border-t border-blue-200 pt-3">
                                <label class="flex items-center space-x-2 mb-3 cursor-pointer">
                                    <input type="checkbox" id="excludeCheckbox_${report.report_id}" ${report.exclude_from_analysis ? 'checked' : ''} class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" onchange="toggleExclusionReason('${report.report_id}')">
                                    <span class="text-sm font-semibold text-blue-800">Exclude from Analysis</span>
                                </label>
                                <div id="exclusionReasonDiv_${report.report_id}" class="${report.exclude_from_analysis ? '' : 'hidden'}">
                                    <label class="text-xs font-semibold text-blue-800 uppercase mb-2 block">Exclusion Reason</label>
                                    <select id="exclusionReason_${report.report_id}" class="w-full px-3 py-2 border border-blue-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                                        <option value="" ${!report.exclusion_reason ? 'selected' : ''}>Select reason...</option>
                                        <option value="Duplicate" ${report.exclusion_reason === 'Duplicate' ? 'selected' : ''}>Duplicate</option>
                                        <option value="Spam" ${report.exclusion_reason === 'Spam' ? 'selected' : ''}>Spam</option>
                                        <option value="Test Entry" ${report.exclusion_reason === 'Test Entry' ? 'selected' : ''}>Test Entry</option>
                                        <option value="Out of Scope" ${report.exclusion_reason === 'Out of Scope' ? 'selected' : ''}>Out of Scope</option>
                                        <option value="Other" ${report.exclusion_reason === 'Other' ? 'selected' : ''}>Other</option>
                                    </select>
                                </div>
                            </div>
                            
                            <!-- Review Info Display -->
                            ${report.reviewed_by || report.reviewed_at ? `
                            <div class="border-t border-blue-200 pt-3">
                                <div class="text-xs text-gray-600">
                                    <i class="fas fa-info-circle mr-1"></i>
                                    Last reviewed by <strong>${report.reviewed_by || 'Unknown'}</strong>
                                    ${report.reviewed_at ? ` on ${new Date(report.reviewed_at).toLocaleString()}` : ''}
                                </div>
                            </div>
                            ` : ''}
                            
                            <!-- Save Button -->
                            <div class="flex justify-end">
                                <button onclick="saveReportUpdates('${report.report_id}')" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold text-sm shadow-md hover:shadow-lg">
                                    <i class="fas fa-save mr-2"></i>Save Changes
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        modal.classList.remove('hidden');
    };
    
    // Close modal
    window.closeReportDetailModal = function() {
        document.getElementById('reportDetailModal').classList.add('hidden');
    };
    
    // Toggle exclusion reason dropdown
    window.toggleExclusionReason = function(reportId) {
        const checkbox = document.getElementById(`excludeCheckbox_${reportId}`);
        const reasonDiv = document.getElementById(`exclusionReasonDiv_${reportId}`);
        
        if (checkbox.checked) {
            reasonDiv.classList.remove('hidden');
        } else {
            reasonDiv.classList.add('hidden');
        }
    };
    
    // Toggle preset tag
    window.togglePresetTag = function(reportId, tag) {
        const tagsInput = document.getElementById(`manualTags_${reportId}`);
        const currentTags = tagsInput.value ? tagsInput.value.split(',').map(t => t.trim()).filter(t => t) : [];
        
        if (currentTags.includes(tag)) {
            // Remove tag
            const index = currentTags.indexOf(tag);
            currentTags.splice(index, 1);
        } else {
            // Add tag
            currentTags.push(tag);
        }
        
        tagsInput.value = currentTags.join(', ');
        updateTagsDisplay(reportId);
    };
    
    // Add custom tag
    window.addCustomTag = function(reportId) {
        const customInput = document.getElementById(`customTag_${reportId}`);
        const tagsInput = document.getElementById(`manualTags_${reportId}`);
        const newTag = customInput.value.trim().toLowerCase().replace(/\s+/g, '-');
        
        if (!newTag) return;
        
        const currentTags = tagsInput.value ? tagsInput.value.split(',').map(t => t.trim()).filter(t => t) : [];
        
        if (!currentTags.includes(newTag)) {
            currentTags.push(newTag);
            tagsInput.value = currentTags.join(', ');
            customInput.value = '';
            updateTagsDisplay(reportId);
        } else {
            showError('Tag already exists');
        }
    };
    
    // Remove tag
    window.removeTag = function(reportId, tag) {
        const tagsInput = document.getElementById(`manualTags_${reportId}`);
        const currentTags = tagsInput.value ? tagsInput.value.split(',').map(t => t.trim()).filter(t => t) : [];
        const index = currentTags.indexOf(tag);
        
        if (index > -1) {
            currentTags.splice(index, 1);
            tagsInput.value = currentTags.join(', ');
            updateTagsDisplay(reportId);
        }
    };
    
    // Update tags display
    function updateTagsDisplay(reportId) {
        const tagsInput = document.getElementById(`manualTags_${reportId}`);
        const tagsDisplay = document.getElementById(`selectedTags_${reportId}`);
        const tags = tagsInput.value ? tagsInput.value.split(',').map(t => t.trim()).filter(t => t) : [];
        
        tagsDisplay.innerHTML = tags.map(tag => `
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                ${tag}
                <button type="button" onclick="removeTag('${reportId}', '${tag}')" class="ml-1 text-blue-600 hover:text-blue-800">
                    <i class="fas fa-times"></i>
                </button>
            </span>
        `).join('');
    }
    
    // Save report updates
    window.saveReportUpdates = async function(reportId) {
        try {
            const statusSelect = document.getElementById(`statusSelect_${reportId}`);
            const reviewerInput = document.getElementById(`reviewerName_${reportId}`);
            const manualTagsInput = document.getElementById(`manualTags_${reportId}`);
            const excludeCheckbox = document.getElementById(`excludeCheckbox_${reportId}`);
            const exclusionReasonSelect = document.getElementById(`exclusionReason_${reportId}`);
            
            // Validate reviewer name if status is being changed
            const currentReport = allReports.find(r => r.report_id === reportId);
            if (statusSelect.value !== currentReport.status && !reviewerInput.value.trim()) {
                showError('Please enter your name when updating status');
                reviewerInput.focus();
                return;
            }
            
            // Validate exclusion reason if excluded
            if (excludeCheckbox.checked && !exclusionReasonSelect.value) {
                showError('Please select an exclusion reason');
                exclusionReasonSelect.focus();
                return;
            }
            
            // Parse manual tags
            const manualTagsArray = manualTagsInput.value
                .split(',')
                .map(tag => tag.trim())
                .filter(tag => tag.length > 0);
            
            const updateData = {
                report_id: reportId,
                status: statusSelect.value,
                reviewed_by: reviewerInput.value.trim() || null,
                manual_tags: manualTagsArray.length > 0 ? JSON.stringify(manualTagsArray) : null,
                exclude_from_analysis: excludeCheckbox.checked,
                exclusion_reason: excludeCheckbox.checked ? exclusionReasonSelect.value : null
            };
            
            // Show loading state
            const saveBtn = event.target;
            const originalHTML = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
            saveBtn.disabled = true;
            
            const response = await fetch('/api/update-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showSuccess('Report updated successfully');
                // Close modal and refresh data
                closeReportDetailModal();
                await loadReportsData();
            } else {
                throw new Error(result.error || 'Failed to update report');
            }
            
        } catch (error) {
            console.error('Update error:', error);
            showError(error.message || 'Failed to update report');
            // Reset button
            if (event && event.target) {
                event.target.innerHTML = '<i class="fas fa-save mr-2"></i>Save Changes';
                event.target.disabled = false;
            }
        }
    };
    
    // Utility functions
    function capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    function parseAITags(tagsData) {
        if (!tagsData) return [];
        
        // If it's already an array, return it
        if (Array.isArray(tagsData)) return tagsData;
        
        // If it's a string, try to parse it as JSON
        if (typeof tagsData === 'string') {
            try {
                const parsed = JSON.parse(tagsData);
                return Array.isArray(parsed) ? parsed : [];
            } catch (e) {
                // If parsing fails, try splitting by comma
                return tagsData.split(',').map(t => t.trim()).filter(t => t);
            }
        }
        
        return [];
    }
    
    function formatTimeframe(timeframe) {
        const mapping = {
            'now': 'Happening Now',
            '1hour': 'Within 1 Hour',
            'today': 'Today',
            'yesterday': 'Yesterday',
            'week': 'This Week',
            'ongoing': 'Ongoing'
        };
        return mapping[timeframe] || timeframe;
    }
    
    function getSeverityColor(severity) {
        const colors = {
            'low': 'bg-green-100 text-green-800',
            'moderate': 'bg-yellow-100 text-yellow-800',
            'high': 'bg-orange-100 text-orange-800',
            'critical': 'bg-red-100 text-red-800'
        };
        return colors[severity] || 'bg-gray-100 text-gray-800';
    }
    
    function getStatusColor(status) {
        const colors = {
            'pending': 'bg-blue-100 text-blue-800',
            'reviewed': 'bg-purple-100 text-purple-800',
            'resolved': 'bg-green-100 text-green-800',
            'closed': 'bg-gray-100 text-gray-800',
            'valid - action required': 'bg-red-100 text-red-800',
            'valid - monitoring': 'bg-green-100 text-green-800',
            'under review': 'bg-yellow-100 text-yellow-800',
            'closed - invalid': 'bg-gray-100 text-gray-800'
        };
        return colors[status.toLowerCase()] || 'bg-gray-100 text-gray-800';
    }
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    function showError(message) {
        showToast(message, 'error');
    }
    
    function showSuccess(message) {
        showToast(message, 'success');
    }
    
    function showToast(message, type = 'info') {
        // Remove any existing toasts
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast-notification ${type}`;
        
        const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        
        toast.innerHTML = `
            <div class="${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3 max-w-md">
                <i class="fas ${icon} text-2xl"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Toggle columns between concise and all
    function toggleColumns() {
        showAllColumns = !showAllColumns;
        localStorage.setItem('showAllColumns', showAllColumns);
        updateColumnToggleButton();
        renderReportsTable(allReports); // Re-render table with new column set
    }
    
    // Update toggle button text
    function updateColumnToggleButton() {
        const btnText = document.getElementById('toggleColumnsText');
        if (showAllColumns) {
            btnText.textContent = 'Show Essential Columns';
        } else {
            btnText.textContent = 'Show All Columns';
        }
    }
    
    // Render table headers based on column selection
    function renderTableHeaders() {
        const thead = document.getElementById('reportsTableHead');
        let headers = '';
        
        if (showAllColumns) {
            headers = `
                <tr>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">ID</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Type</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Description</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Severity</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Status</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Street</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">City</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">State</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">County</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">ZIP</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Timestamp</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">When</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Affected</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Specific Type</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Reporter</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Contact</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">AI Summary</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Media Summary</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">AI Tags</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Manual Tags</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">AI Confidence</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Reviewed By</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Reviewed At</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Excluded</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Reason</th>
                    <th class="px-4 py-3 text-left text-xs font-bold text-white uppercase">Actions</th>
                </tr>
            `;
        } else {
            headers = `
                <tr>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Type</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Date/Time</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Location</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Severity</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Status</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">AI Tags</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Manual Tags</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Actions</th>
                </tr>
            `;
        }
        
        thead.innerHTML = headers;
    }
    
    // Update charts with community reports data
    async function updateCharts(reports) {
        // Get all reports for chart data (without pagination)
        try {
            const params = new URLSearchParams();
            
            // Add same filters but get all data
            if (currentFilters.state) params.append('state', currentFilters.state);
            if (currentFilters.city) params.append('city', currentFilters.city);
            if (currentFilters.county) params.append('county', currentFilters.county);
            if (currentFilters.zipcode) params.append('zipcode', currentFilters.zipcode);
            if (currentFilters.report_type) params.append('report_type', currentFilters.report_type);
            if (currentFilters.severity) params.append('severity', currentFilters.severity);
            if (currentFilters.status) params.append('status', currentFilters.status);
            if (currentFilters.timeframe) params.append('timeframe', currentFilters.timeframe);
            
            params.append('limit', 1000); // Get more data for charts
            params.append('offset', 0);
            
            const response = await fetch(`/api/community-reports?${params}`);
            const data = await response.json();
            
            if (!data.success || !data.reports) {
                console.error('Failed to load chart data');
                return;
            }
            
            cachedChartReports = data.reports; // Cache for granularity switching
            updateTimeChart(cachedChartReports);
            updateTypeChart(cachedChartReports);
            updateZipChart(cachedChartReports);
            
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }
    
    // Update time-based chart with current granularity
    function updateTimeChart(allChartReports) {
        let timeCounts = {};
        let timeRange, timeLabel, dateFormat;
        
        if (chartGranularity === 'hour') {
            // Last 24 hours by hour
            timeRange = new Date();
            timeRange.setHours(timeRange.getHours() - 24);
            timeLabel = 'Last 24 Hours';
            
            allChartReports.forEach(report => {
                const date = new Date(report.timestamp);
                if (date >= timeRange) {
                    // Create a sortable hour key
                    const hourKey = date.toLocaleString('en-US', { 
                        month: '2-digit', 
                        day: '2-digit', 
                        hour: '2-digit', 
                        hour12: false
                    });
                    const displayKey = date.toLocaleString('en-US', { 
                        month: 'short', 
                        day: 'numeric', 
                        hour: 'numeric', 
                        hour12: true 
                    });
                    if (!timeCounts[hourKey]) {
                        timeCounts[hourKey] = { display: displayKey, count: 0 };
                    }
                    timeCounts[hourKey].count++;
                }
            });
        } else if (chartGranularity === 'week') {
            // Last 12 weeks by week
            timeRange = new Date();
            timeRange.setDate(timeRange.getDate() - 84); // 12 weeks
            timeLabel = 'Last 12 Weeks';
            
            allChartReports.forEach(report => {
                const date = new Date(report.timestamp);
                if (date >= timeRange) {
                    // Get week start (Sunday)
                    const weekStart = new Date(date);
                    weekStart.setDate(date.getDate() - date.getDay());
                    const weekKey = weekStart.toISOString().split('T')[0];
                    const displayKey = weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    if (!timeCounts[weekKey]) {
                        timeCounts[weekKey] = { display: displayKey, count: 0 };
                    }
                    timeCounts[weekKey].count++;
                }
            });
        } else if (chartGranularity === 'month') {
            // Last 12 months by month
            timeRange = new Date();
            timeRange.setMonth(timeRange.getMonth() - 12);
            timeLabel = 'Last 12 Months';
            
            allChartReports.forEach(report => {
                const date = new Date(report.timestamp);
                if (date >= timeRange) {
                    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                    const displayKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
                    if (!timeCounts[monthKey]) {
                        timeCounts[monthKey] = { display: displayKey, count: 0 };
                    }
                    timeCounts[monthKey].count++;
                }
            });
        } else {
            // Last 30 days by day (default)
            timeRange = new Date();
            timeRange.setDate(timeRange.getDate() - 30);
            timeLabel = 'Last 30 Days';
            
            allChartReports.forEach(report => {
                const date = new Date(report.timestamp);
                if (date >= timeRange) {
                    const dateKey = date.toISOString().split('T')[0]; // YYYY-MM-DD for sorting
                    const displayKey = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    if (!timeCounts[dateKey]) {
                        timeCounts[dateKey] = { display: displayKey, count: 0 };
                    }
                    timeCounts[dateKey].count++;
                }
            });
        }
        
        const sortedTimes = Object.keys(timeCounts).sort();
        
        const countLabels = sortedTimes.length > 0 ? 
            sortedTimes.map(key => timeCounts[key].display) : 
            ['No Data'];
        const countData = sortedTimes.length > 0 ? 
            sortedTimes.map(key => timeCounts[key].count) : 
            [0];
        
        // Update first chart (reports over time)
        if (window.aqiChart) {
            window.aqiChart.data.labels = countLabels;
            window.aqiChart.data.datasets[0].data = countData;
            window.aqiChart.data.datasets[0].label = 'Number of Reports';
            window.aqiChart.options.plugins.title.text = `Community Reports Over Time (${timeLabel})`;
            window.aqiChart.options.scales.y.title.text = 'Number of Reports';
            window.aqiChart.options.scales.y.max = 25; // Set max Y-axis to 25
            window.aqiChart.options.scales.x.title.text = chartGranularity === 'hour' ? 'Hour' : chartGranularity === 'week' ? 'Week' : chartGranularity === 'month' ? 'Month' : 'Date';
            
            // Adjust X-axis display for readability
            if (chartGranularity === 'hour') {
                window.aqiChart.options.scales.x.ticks.maxRotation = 90;
                window.aqiChart.options.scales.x.ticks.minRotation = 45;
                window.aqiChart.options.scales.x.ticks.autoSkip = true;
                window.aqiChart.options.scales.x.ticks.maxTicksLimit = 12; // Show max 12 labels
            } else if (chartGranularity === 'week' || chartGranularity === 'month') {
                window.aqiChart.options.scales.x.ticks.maxRotation = 45;
                window.aqiChart.options.scales.x.ticks.minRotation = 0;
                window.aqiChart.options.scales.x.ticks.autoSkip = true;
                window.aqiChart.options.scales.x.ticks.maxTicksLimit = 12;
            } else {
                window.aqiChart.options.scales.x.ticks.maxRotation = 45;
                window.aqiChart.options.scales.x.ticks.minRotation = 0;
                window.aqiChart.options.scales.x.ticks.autoSkip = true;
                window.aqiChart.options.scales.x.ticks.maxTicksLimit = 15; // Show max 15 labels
            }
            
            window.aqiChart.update();
        }
    }
    
    // Update report types chart
    function updateTypeChart(allChartReports) {
        const typeCounts = {};
        allChartReports.forEach(report => {
            const type = report.report_type || 'unknown';
            typeCounts[type] = (typeCounts[type] || 0) + 1;
        });
        
        const typeLabels = Object.keys(typeCounts).length > 0 ? 
            Object.keys(typeCounts).map(type => type.charAt(0).toUpperCase() + type.slice(1)) : 
            ['No Data'];
        const typeData = Object.keys(typeCounts).length > 0 ? 
            Object.values(typeCounts) : 
            [0];
        
        const typeColors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        const total = typeData.reduce((sum, val) => sum + val, 0);
        
        // Update second chart (report types)
        if (window.diseasesChart) {
            window.diseasesChart.data.labels = typeLabels;
            window.diseasesChart.data.datasets[0].data = typeData;
            window.diseasesChart.data.datasets[0].backgroundColor = typeColors.slice(0, typeLabels.length);
            window.diseasesChart.options.plugins.title.text = `Reports by Type (Total: ${total})`;
            
            // Add percentage and value labels
            window.diseasesChart.options.plugins.tooltip = {
                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                titleFont: {
                    size: 16,
                    weight: 'bold'
                },
                bodyFont: {
                    size: 14
                },
                padding: 16,
                displayColors: true,
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                        return [
                            `${label}: ${value} reports`,
                            `${percentage}% of total`
                        ];
                    }
                }
            };
            
            // Show category labels on the chart instead of percentages
            window.diseasesChart.options.plugins.datalabels = {
                color: '#fff',
                font: {
                    weight: 'bold',
                    size: 12
                },
                formatter: (value, ctx) => {
                    const label = ctx.chart.data.labels[ctx.dataIndex];
                    return label; // Show category name
                }
            };
            
            window.diseasesChart.update();
        }
    }
    
    // Update ZIP codes chart
    function updateZipChart(allChartReports) {
        const locationCounts = {};
        let locationKey, locationLabel;
        
        // Determine which field to group by
        switch(locationGroupBy) {
            case 'city':
                locationKey = 'city';
                locationLabel = 'City';
                allChartReports.forEach(report => {
                    const location = report.city && report.state ? `${report.city}, ${report.state}` : 'Unknown';
                    locationCounts[location] = (locationCounts[location] || 0) + 1;
                });
                break;
            case 'county':
                locationKey = 'county';
                locationLabel = 'County';
                allChartReports.forEach(report => {
                    const location = report.county && report.state ? `${report.county}, ${report.state}` : 'Unknown';
                    locationCounts[location] = (locationCounts[location] || 0) + 1;
                });
                break;
            case 'state':
                locationKey = 'state';
                locationLabel = 'State';
                allChartReports.forEach(report => {
                    const location = report.state || 'Unknown';
                    locationCounts[location] = (locationCounts[location] || 0) + 1;
                });
                break;
            case 'zipcode':
            default:
                locationKey = 'zip_code';
                locationLabel = 'ZIP Code';
                allChartReports.forEach(report => {
                    const location = report.zip_code || 'Unknown';
                    locationCounts[location] = (locationCounts[location] || 0) + 1;
                });
                break;
        }
        
        // Get top 10 locations
        const sortedLocations = Object.entries(locationCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        
        const locationLabels = sortedLocations.length > 0 ? 
            sortedLocations.map(([location, count]) => `${location}`) : 
            ['No Data'];
        const locationData = sortedLocations.length > 0 ? 
            sortedLocations.map(([location, count]) => count) : 
            [0];
        
        const locationColors = [
            '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', 
            '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
        ];
        
        const total = locationData.reduce((sum, val) => sum + val, 0);
        
        // Update location chart
        if (window.zipCodesChart) {
            window.zipCodesChart.data.labels = locationLabels;
            window.zipCodesChart.data.datasets[0].data = locationData;
            window.zipCodesChart.data.datasets[0].backgroundColor = locationColors.slice(0, locationLabels.length);
            window.zipCodesChart.options.plugins.title.text = `Top 10 ${locationLabel}s (Total: ${total} reports)`;
            
            // Add percentage and value labels
            window.zipCodesChart.options.plugins.tooltip = {
                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                titleFont: {
                    size: 16,
                    weight: 'bold'
                },
                bodyFont: {
                    size: 14
                },
                padding: 16,
                displayColors: true,
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                        const prefix = locationGroupBy === 'zipcode' ? 'ZIP ' : '';
                        return [
                            `${prefix}${label}: ${value} reports`,
                            `${percentage}% of total`
                        ];
                    }
                }
            };
            
            // Show location labels on the chart instead of percentages
            window.zipCodesChart.options.plugins.datalabels = {
                color: '#fff',
                font: {
                    weight: 'bold',
                    size: 11
                },
                formatter: (value, ctx) => {
                    const label = ctx.chart.data.labels[ctx.dataIndex];
                    // Truncate long labels
                    if (label.length > 15) {
                        return label.substring(0, 13) + '...';
                    }
                    return label;
                }
            };
            
            window.zipCodesChart.update();
        }
    }
    
    // Make updateLocationGrouping available globally
    window.updateLocationGrouping = function(grouping) {
        locationGroupBy = grouping;
        
        // Update button states
        document.querySelectorAll('.location-grouping-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`${grouping}Btn`).classList.add('active');
        
        if (cachedChartReports.length > 0) {
            updateZipChart(cachedChartReports);
        }
    };
});

// ========================================
// CHAT WIDGET FUNCTIONALITY
// ========================================

let chatWidgetOpen = false;
let chatWidgetMinimized = false;
let lastVideoData = null; // Store video data for Twitter posting

/**
 * Toggle chat widget visibility
 */
function toggleChatWidget() {
    const widget = document.getElementById('chatWidget');
    const button = document.getElementById('chatToggleBtn');
    
    chatWidgetOpen = !chatWidgetOpen;
    
    if (chatWidgetOpen) {
        widget.classList.remove('hidden');
        button.classList.add('hidden');
        initializeChatWidget();
        updateChatLocationContext();
    } else {
        widget.classList.add('hidden');
        button.classList.remove('hidden');
        chatWidgetMinimized = false;
        widget.classList.remove('minimized');
    }
}

/**
 * Initialize chat widget with welcome message
 */
function initializeChatWidget() {
    const messagesDiv = document.getElementById('chatWidgetMessages');
    if (messagesDiv && messagesDiv.children.length === 0) {
        addChatMessage(
            'Hello! I\'m your Health Official AI Assistant. I can help you:\n\n' +
            '• Analyze community reports and identify trends\n' +
            '• Search reports semantically\n' +
            '• Generate PSA videos for public health alerts\n' +
            '• Provide data-driven recommendations\n' +
            '• Answer questions about current health data\n\n' +
            'How can I assist you today?',
            'bot'
        );
    }
}

/**
 * Update location context display based on current filters
 */
function updateChatLocationContext() {
    const contextDiv = document.getElementById('chatWidgetLocationContext');
    const contextText = document.getElementById('chatWidgetLocationText');
    
    if (!contextDiv || !contextText) return;
    
    const parts = [];
    if (currentFilters.city) parts.push(currentFilters.city);
    if (currentFilters.county) parts.push(`${currentFilters.county} County`);
    if (currentFilters.state) parts.push(currentFilters.state);
    if (currentFilters.zipcode) parts.push(`ZIP ${currentFilters.zipcode}`);
    
    if (parts.length > 0) {
        contextText.textContent = parts.join(', ');
        contextDiv.classList.remove('hidden');
    } else {
        contextDiv.classList.add('hidden');
    }
}

/**
 * Send chat message
 */
async function sendChatWidgetMessage() {
    const input = document.getElementById('chatWidgetInput');
    if (!input) return;
    
    const question = input.value.trim();
    if (!question) return;
    
    // Check if user is approving Twitter post
    if (lastVideoData && isTwitterApproval(question)) {
        await postToTwitterWidget(lastVideoData);
        input.value = '';
        return;
    }
    
    // Add user message
    addChatMessage(question, 'user');
    input.value = '';
    
    // Show loading
    const loadingMsg = addChatMessage('Analyzing...', 'bot');
    
    try {
        // Build location context from current filters (if available)
        const locationContext = {};
        if (typeof currentFilters !== 'undefined') {
            if (currentFilters.state) locationContext.state = currentFilters.state;
            if (currentFilters.city) locationContext.city = currentFilters.city;
            if (currentFilters.county) locationContext.county = currentFilters.county;
            if (currentFilters.zipcode) locationContext.zipCode = currentFilters.zipcode;
        }
        
        console.log('[CHAT WIDGET] Sending message:', question);
        console.log('[CHAT WIDGET] Location context:', locationContext);
        console.log('[CHAT WIDGET] Persona: Health Official');
        
        // Call AI agent with Health Official persona
        const response = await fetch('/api/agent-chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                location_context: Object.keys(locationContext).length > 0 ? locationContext : null,
                persona: 'Health Official',  // Always use Health Official persona
                state: (typeof currentFilters !== 'undefined' && currentFilters.state) ? currentFilters.state : '',
                days: 30  // Default to 30 days for officials
            })
        });
        
        console.log('[CHAT WIDGET] Response status:', response.status);
        
        const data = await response.json();
        
        console.log('[CHAT WIDGET] Response data:', data);
        
        // Remove loading
        if (loadingMsg && loadingMsg.remove) {
            loadingMsg.remove();
        }
        
        if (data.success) {
            // Add context indicators
            let responseText = data.response;
            
            // Add agent badge if available
            if (data.agent) {
                responseText += `\n\n<div class="text-xs text-gray-500 mt-2 italic">via ${data.agent}</div>`;
            }
            
            addChatMessage(responseText, 'bot');
            
            // If video generation started, begin polling
            if (data.task_id) {
                console.log('[VIDEO] Task ID received:', data.task_id);
                pollForVideoCompletion(data.task_id);
            }
        } else {
            console.error('[CHAT WIDGET] Error response:', data);
            const errorMsg = data.error || 'Sorry, I encountered an error. Please try again.';
            addChatMessage(errorMsg, 'bot');
        }
    } catch (error) {
        if (loadingMsg && loadingMsg.remove) {
            loadingMsg.remove();
        }
        console.error('[CHAT WIDGET] Exception:', error);
        console.error('[CHAT WIDGET] Error stack:', error.stack);
        addChatMessage('Sorry, I could not connect to the AI service. Please try again.', 'bot');
    }
}

/**
 * Add message to chat widget
 */
function addChatMessage(text, type) {
    const messagesDiv = document.getElementById('chatWidgetMessages');
    if (!messagesDiv) return null;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-start space-x-2 chat-message-enter ${type === 'user' ? 'justify-end' : ''}`;
    
    // Parse video markers for bot messages
    let messageContent = text;
    let videoHtml = '';
    
    if (type === 'bot' && text.includes('[VIDEO:')) {
        const videoMatch = text.match(/\[VIDEO:(.*?)\]/);
        if (videoMatch) {
            const videoUrl = videoMatch[1];
            
            // Remove video marker from text
            messageContent = text.replace(/\[VIDEO:.*?\]/, '').trim();
            
            // Create video player
            videoHtml = `
                <div class="my-2">
                    <video 
                        controls 
                        class="w-full rounded-lg shadow-lg" 
                        style="max-width: 280px; max-height: 500px;"
                        preload="metadata"
                    >
                        <source src="${videoUrl}" type="video/mp4">
                        Your browser doesn't support video playback.
                    </video>
                </div>
            `;
        }
    }
    
    if (type === 'bot') {
        messageDiv.innerHTML = `
            <div class="w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-robot text-white text-sm"></i>
            </div>
            <div class="bg-white rounded-2xl rounded-tl-none p-3 shadow-md max-w-[280px]">
                ${videoHtml}
                <p class="text-gray-700 text-sm leading-relaxed whitespace-pre-line break-words overflow-wrap-anywhere">${messageContent}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bg-navy-700 text-white rounded-2xl rounded-tr-none p-3 shadow-md max-w-[280px]">
                <p class="text-sm leading-relaxed break-words overflow-wrap-anywhere">${text}</p>
            </div>
            <div class="w-8 h-8 bg-navy-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-user text-white text-sm"></i>
            </div>
        `;
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    return messageDiv;
}

/**
 * Clear chat history
 */
function clearChatWidget() {
    const messagesDiv = document.getElementById('chatWidgetMessages');
    if (!messagesDiv) return;
    
    messagesDiv.innerHTML = '';
    initializeChatWidget();
    console.log('[CHAT WIDGET] Chat history cleared');
}

/**
 * Minimize/maximize chat widget
 */
function minimizeChatWidget() {
    const widget = document.getElementById('chatWidget');
    if (!widget) return;
    
    chatWidgetMinimized = !chatWidgetMinimized;
    
    if (chatWidgetMinimized) {
        widget.classList.add('minimized');
    } else {
        widget.classList.remove('minimized');
    }
}

/**
 * Close chat widget
 */
function closeChatWidget() {
    toggleChatWidget();
}

/**
 * Ask a quick action question
 */
function askQuickQuestion(question) {
    const input = document.getElementById('chatWidgetInput');
    if (input) {
        input.value = question;
        sendChatWidgetMessage();
    }
}

/**
 * Check if user message is Twitter approval
 */
function isTwitterApproval(message) {
    const lowerMsg = message.toLowerCase().trim();
    return lowerMsg.includes('yes') && (lowerMsg.includes('post') || lowerMsg.includes('twitter'));
}

/**
 * Poll for video completion
 */
async function pollForVideoCompletion(taskId) {
    const maxAttempts = 240; // 4 minutes max (Veo 3 can take 2-3 minutes)
    let attempts = 0;
    
    console.log(`[VIDEO WIDGET] Starting to poll for task ${taskId}`);
    
    const pollInterval = setInterval(async () => {
        attempts++;
        
        console.log(`[VIDEO WIDGET] Poll attempt ${attempts}/${maxAttempts} for task ${taskId}`);
        
        if (attempts > maxAttempts) {
            clearInterval(pollInterval);
            console.error(`[VIDEO WIDGET] Timeout after ${maxAttempts} attempts`);
            addChatMessage('Video generation is taking longer than expected. Please check back later.', 'bot');
            return;
        }
        
        try {
            const response = await fetch(`/api/check-video-task/${taskId}`);
            console.log(`[VIDEO WIDGET] Response status: ${response.status}`);
            
            if (!response.ok) {
                console.error(`[VIDEO WIDGET] HTTP error: ${response.status}`);
                return; // Continue polling
            }
            
            const data = await response.json();
            console.log(`[VIDEO WIDGET] Poll response:`, data);
            
            if (data.status === 'complete' && data.video_url) {
                clearInterval(pollInterval);
                console.log(`[VIDEO WIDGET] Video ready:`, data.video_url);
                
                // Store video data for potential Twitter posting
                lastVideoData = data;
                
                // Add video message with approval prompt
                const videoMessage = `[VIDEO:${data.video_url}]\n\nYour PSA video is ready!\n\nAction: "${data.action_line}"\n\nWould you like me to post this to Twitter?`;
                addChatMessage(videoMessage, 'bot');
            } else if (data.status === 'error' || data.status === 'failed') {
                clearInterval(pollInterval);
                console.error(`[VIDEO WIDGET] Video generation failed`);
                addChatMessage('Sorry, video generation failed. Please try again.', 'bot');
            } else if (data.status === 'initializing' || 
                       data.status === 'generating_action_line' || 
                       data.status === 'creating_prompt' || 
                       data.status === 'generating_video' ||
                       data.status === 'processing' || 
                       data.status === 'pending') {
                console.log(`[VIDEO WIDGET] Video still ${data.status} (progress: ${data.progress || 'unknown'}%)`);
                // Continue polling
            } else {
                console.warn(`[VIDEO WIDGET] Unknown status: ${data.status}`);
                // Continue polling
            }
        } catch (error) {
            console.error(`[VIDEO WIDGET] Error polling task ${taskId}:`, error);
            // Continue polling despite error
        }
    }, 1000);
}

/**
 * Post video to Twitter (widget version)
 */
const isPostingToTwitterWidget = { value: false }; // Flag to prevent duplicate posts

async function postToTwitterWidget(videoData) {
    // Prevent duplicate posting
    if (isPostingToTwitterWidget.value) {
        console.log('[TWITTER WIDGET] Already posting, ignoring duplicate call');
        return;
    }
    isPostingToTwitterWidget.value = true;
    
    try {
        // Show posting message with expected time
        const loadingMsg = addChatMessage('Posting to Twitter... (This may take 60-90 seconds: downloading video, uploading to Twitter, processing)', 'bot');
        
        // Create abort controller for timeout (2 minutes)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes
        
        const response = await fetch('/api/post-to-twitter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_url: videoData.video_url,
                message: videoData.action_line,  // Backend expects 'message' field
                hashtags: ['HealthAlert', 'PublicHealth', 'CommunityHealth', 'AirQuality']
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const data = await response.json();
        
        // Remove loading message
        if (loadingMsg && loadingMsg.remove) {
            loadingMsg.remove();
        }
        
        if (data.success && data.tweet_url) {
            const successMessage = `Posted to Twitter successfully!\n\nView your post: ${data.tweet_url}\n\n${data.message || 'Tweet posted successfully!'}`;
            addChatMessage(successMessage, 'bot');
            lastVideoData = null; // Clear after posting
        } else {
            addChatMessage(`Sorry, I couldn't post to Twitter: ${data.error || 'Unknown error'}`, 'bot');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            addChatMessage('Twitter posting timed out. The video may still have been posted. Please check the Twitter feed at https://twitter.com/AI_mmunity', 'bot');
        } else {
            addChatMessage('Sorry, there was an error posting to Twitter. Please try again.', 'bot');
        }
        console.error('[TWITTER WIDGET] Error posting:', error);
    } finally {
        // Reset posting flag
        isPostingToTwitterWidget.value = false;
    }
}

// Make functions globally available
window.toggleChatWidget = toggleChatWidget;
window.minimizeChatWidget = minimizeChatWidget;
window.closeChatWidget = closeChatWidget;
window.sendChatWidgetMessage = sendChatWidgetMessage;
window.clearChatWidget = clearChatWidget;
window.askQuickQuestion = askQuickQuestion;

// ===== PUBLIC HEALTH ALERT SYSTEM =====
let currentAlertLevel = 'critical';
let currentAlertDuration = null; // null means "until cancelled"
let currentActiveAlert = null;
let currentAlertFilter = 'all'; // Status filter (all, active, expired, cancelled)
let selectedLevels = ['critical', 'warning', 'info']; // All levels selected by default
let currentAlertStatus = 'all'; // Track current status filter for reloading

function openAlertModal() {
    const modal = document.getElementById('alertModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Generate AI summary when modal opens
        generateAlertSummary();
    }
}

function closeAlertModal() {
    const modal = document.getElementById('alertModal');
    if (modal) {
        modal.classList.add('hidden');
        // Clear the input
        document.getElementById('alertMessageInput').value = '';
    }
}

function setAlertLevel(level) {
    currentAlertLevel = level;
    
    // Update button states
    const buttons = document.querySelectorAll('.alert-level-btn');
    buttons.forEach(btn => {
        const btnLevel = btn.getAttribute('data-level');
        if (btnLevel === level) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function setAlertDuration(hours) {
    currentAlertDuration = hours;
    
    // Update button states
    const buttons = document.querySelectorAll('.alert-duration-btn');
    buttons.forEach(btn => {
        const btnDuration = btn.getAttribute('data-duration');
        if ((btnDuration === 'null' && hours === null) || (btnDuration === String(hours))) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

async function generateAlertSummary() {
    const summaryContent = document.getElementById('aiSummaryContent');
    
    try {
        summaryContent.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-spinner fa-spin text-blue-600"></i>
                <span>Generating summary based on recent reports...</span>
            </div>
        `;
        
        // Ensure currentFilters exists
        const filters = window.currentFilters || currentFilters || {
            state: '',
            city: '',
            county: '',
            zipcode: '',
            report_type: '',
            severity: '',
            status: '',
            timeframe: '',
            timePeriod: 'live'
        };
        
        const response = await fetch('/api/officials/generate-alert-summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filters: filters
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            summaryContent.innerHTML = `
                <div class="space-y-2">
                    <p class="text-gray-700">${data.summary}</p>
                    <div class="text-xs text-gray-500 mt-2">
                        <i class="fas fa-info-circle mr-1"></i>
                        Based on ${data.report_count} recent reports
                        ${data.high_severity_count > 0 ? `(${data.high_severity_count} high severity)` : ''}
                    </div>
                    <button onclick="useAISummary()" class="mt-2 text-sm text-blue-600 hover:text-blue-700 font-semibold">
                        <i class="fas fa-arrow-down mr-1"></i>Use this summary
                    </button>
                </div>
            `;
        } else {
            summaryContent.innerHTML = `
                <p class="text-red-600">
                    <i class="fas fa-exclamation-circle mr-1"></i>
                    Failed to generate summary: ${data.error || 'Unknown error'}
                </p>
            `;
        }
    } catch (error) {
        console.error('Error generating summary:', error);
        summaryContent.innerHTML = `
            <p class="text-red-600">
                <i class="fas fa-exclamation-circle mr-1"></i>
                Error: ${error.message || 'Please try again.'}
            </p>
        `;
    }
}

function useAISummary() {
    const summaryText = document.querySelector('#aiSummaryContent p').textContent;
    document.getElementById('alertMessageInput').value = summaryText;
}

async function sendAlert() {
    const message = document.getElementById('alertMessageInput').value.trim();
    
    if (!message) {
        showToast('Please enter an alert message', 'warning');
        return;
    }
    
    try {
        // Ensure currentFilters exists
        const filters = window.currentFilters || currentFilters || {
            state: '',
            city: '',
            county: '',
            zipcode: '',
            report_type: '',
            severity: '',
            status: '',
            timeframe: '',
            timePeriod: 'live'
        };
        
        const response = await fetch('/api/officials/post-alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                level: currentAlertLevel,
                duration_hours: currentAlertDuration,
                filters: filters
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close modal
            closeAlertModal();
            
            // Display alert banner
            displayAlertBanner(data.alert);
            
            // Store current alert
            currentActiveAlert = data.alert;
            
            // Show cancel button
            const cancelBtn = document.getElementById('cancelAlertBtn');
            if (cancelBtn) {
                cancelBtn.classList.remove('hidden');
            }
            
            // Reload alerts table
            if (typeof loadAlerts === 'function') {
                loadAlerts(currentAlertFilter || 'all');
            }
            
            // Show success toast notification
            showToast('Public health alert issued successfully!', 'success');
            
            // Add to recent activity
            addRecentActivity('Public health alert issued', 'Just now');
            
            // Clear sessionStorage dismissal flag so alert shows everywhere
            sessionStorage.removeItem('alertDismissed');
        } else {
            showToast('Failed to post alert: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error posting alert:', error);
        showToast('Error posting alert. Please try again.', 'error');
    }
}

function displayAlertBanner(alert) {
    const banner = document.getElementById('alertBanner');
    const messageEl = document.getElementById('alertMessage');
    const timestampEl = document.getElementById('alertTimestamp');
    
    if (banner && messageEl && timestampEl) {
        messageEl.textContent = alert.message;
        
        // Use issued_at instead of timestamp
        const timestamp = new Date(alert.issued_at);
        timestampEl.textContent = `Issued ${timestamp.toLocaleString()} by ${alert.issued_by}`;
        
        banner.classList.remove('hidden');
        
        // Add color based on level
        banner.classList.remove('from-red-600', 'to-red-700', 'from-yellow-500', 'to-yellow-600', 'from-blue-500', 'to-blue-600');
        if (alert.level === 'critical') {
            banner.classList.add('from-red-600', 'to-red-700');
        } else if (alert.level === 'warning') {
            banner.classList.add('from-yellow-500', 'to-yellow-600');
        } else {
            banner.classList.add('from-blue-500', 'to-blue-600');
        }
        
        // Smooth scroll to top to show banner
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function dismissAlert() {
    const banner = document.getElementById('alertBanner');
    if (banner) {
        banner.classList.add('hidden');
    }
}

function openCancelAlertModal() {
    const modal = document.getElementById('cancelAlertModal');
    const currentAlertText = document.getElementById('currentAlertText');
    
    if (modal && currentActiveAlert) {
        currentAlertText.textContent = currentActiveAlert.message;
        modal.classList.remove('hidden');
    } else {
        // Fetch current alert if not in memory
        fetch('/api/officials/get-active-alert')
            .then(res => res.json())
            .then(data => {
                if (data.success && data.alert) {
                    currentActiveAlert = data.alert;
                    currentAlertText.textContent = data.alert.message;
                    modal.classList.remove('hidden');
                } else {
                    alert('No active alert to cancel');
                }
            })
            .catch(err => {
                console.error('Error fetching alert:', err);
                alert('Error loading alert information');
            });
    }
}

function closeCancelAlertModal() {
    const modal = document.getElementById('cancelAlertModal');
    if (modal) {
        modal.classList.add('hidden');
        document.getElementById('cancellerName').value = '';
    }
}

async function confirmCancelAlert() {
    const name = document.getElementById('cancellerName').value.trim();
    
    if (!name) {
        alert('Please enter your name to confirm cancellation');
        return;
    }
    
    if (name.length < 3) {
        alert('Please enter your full name');
        return;
    }
    
    try {
        const response = await fetch('/api/officials/cancel-alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cancelled_by: name
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close modal
            closeCancelAlertModal();
            
            // Hide banner
            dismissAlert();
            
            // Hide cancel button
            const cancelBtn = document.getElementById('cancelAlertBtn');
            if (cancelBtn) {
                cancelBtn.classList.add('hidden');
            }
            
            // Clear current alert
            currentActiveAlert = null;
            
            alert(`Alert cancelled successfully by ${name}`);
        } else {
            alert('Failed to cancel alert: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error cancelling alert:', error);
        alert('Error cancelling alert: ' + (error.message || 'Please try again.'));
    }
}

// Check for active alert on page load
async function checkForActiveAlert() {
    try {
        const response = await fetch('/api/officials/get-active-alert');
        const data = await response.json();
        
        if (data.success && data.alert) {
            currentActiveAlert = data.alert;
            displayAlertBanner(data.alert);
            
            // Show cancel button
            const cancelBtn = document.getElementById('cancelAlertBtn');
            if (cancelBtn) {
                cancelBtn.classList.remove('hidden');
            }
        }
    } catch (error) {
        console.error('Error checking for active alert:', error);
    }
}

// Alert Management Functions
// currentAlertFilter declared above in alert system variables section

async function loadAlerts(status = 'all', levels = null) {
    try {
        const response = await fetch(`/api/officials/list-alerts?status=${status}`);
        const data = await response.json();
        
        if (data.success) {
            // Filter by selected levels
            let filteredAlerts = data.alerts;
            const levelsToUse = levels || selectedLevels;
            if (levelsToUse.length > 0 && levelsToUse.length < 3) {
                filteredAlerts = data.alerts.filter(alert => levelsToUse.includes(alert.level));
            }
            displayAlertsTable(filteredAlerts);
        } else {
            console.error('Failed to load alerts:', data.error);
            showEmptyAlertsState();
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
        showEmptyAlertsState();
    }
}

function toggleLevelFilterDropdown() {
    const dropdown = document.getElementById('levelFilterDropdown');
    dropdown.classList.toggle('hidden');
}

function toggleAllLevels(checkbox) {
    const individualCheckboxes = document.querySelectorAll('.individual-level');
    individualCheckboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateLevelFilters();
}

function updateLevelFilters() {
    const individualCheckboxes = document.querySelectorAll('.individual-level:checked');
    selectedLevels = Array.from(individualCheckboxes).map(cb => cb.value);
    
    // Update "All" checkbox
    const allCheckbox = document.getElementById('levelAllCheckbox');
    allCheckbox.checked = selectedLevels.length === 3;
    
    // Update button text
    const buttonText = document.querySelector('#levelFilterButton span');
    if (selectedLevels.length === 3) {
        buttonText.textContent = 'Levels: All';
    } else if (selectedLevels.length === 0) {
        buttonText.textContent = 'Levels: None';
    } else {
        buttonText.textContent = `Levels: ${selectedLevels.length} selected`;
    }
    
    // Reload alerts with new filter
    loadAlerts(currentAlertFilter, selectedLevels);
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('levelFilterDropdown');
    const button = document.getElementById('levelFilterButton');
    if (dropdown && button && !dropdown.contains(event.target) && !button.contains(event.target)) {
        dropdown.classList.add('hidden');
    }
});

function displayAlertsTable(alerts) {
    const tbody = document.getElementById('alertsTableBody');
    const emptyState = document.getElementById('alertsEmptyState');
    
    if (!alerts || alerts.length === 0) {
        showEmptyAlertsState();
        return;
    }
    
    emptyState.classList.add('hidden');
    
    tbody.innerHTML = alerts.map(alert => {
        const statusBadge = getStatusBadge(alert.status, alert.cancelled_by);
        const levelBadge = getLevelBadge(alert.level);
        const issuedDate = new Date(alert.issued_at).toLocaleString();
        const expiresText = alert.expires_at ? new Date(alert.expires_at).toLocaleString() : 'Until Cancelled';
        
        // Action buttons - show for all alerts, not just active ones
        const actionButtons = `
            <div class="flex items-center space-x-2">
                <button onclick="viewAlertDetails('${alert.alert_id}')" class="px-3 py-1 bg-gray-500 hover:bg-gray-600 text-white text-xs font-medium rounded transition-colors" title="View details">
                    <i class="fas fa-eye"></i>
                </button>
                ${alert.status === 'active' ? `
                    <button onclick="editAlertFromTable('${alert.alert_id}')" class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs font-medium rounded transition-colors" title="Edit alert">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="resolveAlertFromTable('${alert.alert_id}')" class="px-3 py-1 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-medium rounded transition-colors" title="Mark as resolved">
                        <i class="fas fa-check"></i>
                    </button>
                    <button onclick="cancelAlertFromTable('${alert.alert_id}')" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white text-xs font-medium rounded transition-colors" title="Cancel alert">
                        <i class="fas fa-ban"></i>
                    </button>
                ` : ''}
            </div>`;
        
        const cancelledInfo = alert.cancelled ? 
            `<div class="text-xs text-gray-500 mt-1">
                <i class="fas fa-user mr-1"></i>Cancelled by ${alert.cancelled_by}
                <i class="fas fa-clock ml-2 mr-1"></i>${new Date(alert.cancelled_at).toLocaleString()}
            </div>` : '';
        
        return `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-3 py-4 whitespace-nowrap w-28">${statusBadge}</td>
                <td class="px-3 py-4 whitespace-nowrap w-24">${levelBadge}</td>
                <td class="px-6 py-4" style="max-width: 700px; min-width: 300px; word-wrap: break-word; overflow-wrap: break-word;">
                    <div class="overflow-hidden">
                        <p class="text-sm text-gray-900 font-medium break-words">${escapeHtml(alert.message)}</p>
                        ${cancelledInfo}
                    </div>
                </td>
                <td class="px-3 py-4 text-sm text-gray-700 font-medium" style="max-width: 120px; word-wrap: break-word; overflow-wrap: break-word;">
                    <div class="overflow-hidden break-words">${escapeHtml(alert.issued_by)}</div>
                </td>
                <td class="px-3 py-4 text-xs text-gray-600" style="max-width: 140px; white-space: normal;">
                    <div class="overflow-hidden">${issuedDate}</div>
                </td>
                <td class="px-3 py-4 text-xs text-gray-600" style="max-width: 140px; white-space: normal;">
                    <div class="overflow-hidden">${expiresText}</div>
                </td>
                <td class="px-3 py-4 whitespace-nowrap w-48">${actionButtons}</td>
            </tr>
        `;
    }).join('');
}

function getStatusBadge(status, cancelled_by) {
    // Check if it was resolved (cancelled_by contains "Resolved")
    if (status === 'cancelled' && cancelled_by && cancelled_by.includes('Resolved')) {
        return '<span class="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full"><i class="fas fa-check-circle mr-1"></i>Resolved</span>';
    }
    
    const badges = {
        'active': '<span class="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full"><i class="fas fa-check-circle mr-1"></i>Active</span>',
        'expired': '<span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full"><i class="fas fa-clock mr-1"></i>Expired</span>',
        'cancelled': '<span class="px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full"><i class="fas fa-ban mr-1"></i>Cancelled</span>'
    };
    return badges[status] || badges['expired'];
}

function getLevelBadge(level) {
    const badges = {
        'critical': '<span class="px-2 py-1 bg-red-500 text-white text-xs font-bold rounded"><i class="fas fa-exclamation-triangle mr-1"></i>CRITICAL</span>',
        'warning': '<span class="px-2 py-1 bg-amber-500 text-white text-xs font-bold rounded"><i class="fas fa-exclamation-circle mr-1"></i>WARNING</span>',
        'info': '<span class="px-2 py-1 bg-blue-500 text-white text-xs font-bold rounded"><i class="fas fa-info-circle mr-1"></i>INFO</span>'
    };
    return badges[level] || badges['info'];
}

function showEmptyAlertsState() {
    const tbody = document.getElementById('alertsTableBody');
    const emptyState = document.getElementById('alertsEmptyState');
    
    tbody.innerHTML = '';
    emptyState.classList.remove('hidden');
}

function filterAlerts(status) {
    currentAlertFilter = status;
    currentAlertStatus = status; // Also update currentAlertStatus for consistency
    
    // Update filter button styles
    document.querySelectorAll('.alert-filter-btn').forEach(btn => {
        if (btn.dataset.filter === status) {
            btn.classList.remove('bg-gray-200', 'text-gray-700');
            btn.classList.add('bg-emerald-500', 'text-white');
        } else {
            btn.classList.remove('bg-emerald-500', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        }
    });
    
    // Load alerts with current filters
    loadAlerts(status, selectedLevels);
}

function toggleAlertsTable() {
    const container = document.getElementById('alertsTableContainer');
    const icon = document.getElementById('alertsToggleIcon');
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        icon.classList.remove('fa-chevron-right');
        icon.classList.add('fa-chevron-down');
    } else {
        container.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-right');
    }
}

async function cancelAlertFromTable(alertId) {
    // Fetch alert details first
    try {
        const response = await fetch(`/api/officials/list-alerts?status=all&limit=100`);
        const data = await response.json();
        
        if (data.success) {
            const alert = data.alerts.find(a => a.id === alertId);
            if (alert) {
                currentActiveAlert = alert;
                // Update modal with alert details
                const alertTextEl = document.getElementById('currentAlertText');
                if (alertTextEl) {
                    alertTextEl.textContent = alert.message;
                }
                openCancelAlertModal();
            } else {
                showToast('Alert not found', 'error');
            }
        }
    } catch (error) {
        console.error('Error fetching alert:', error);
        showToast('Failed to load alert details', 'error');
    }
}

async function editAlertFromTable(alertId) {
    showToast('Edit functionality coming soon! You can cancel and create a new alert.', 'info', 4000);
    // TODO: Implement edit modal with pre-filled values
}

async function resolveAlertFromTable(alertId) {
    // Fetch alert details first
    try {
        const response = await fetch(`/api/officials/list-alerts?status=all&limit=100`);
        const data = await response.json();
        
        if (data.success) {
            const alert = data.alerts.find(a => a.id === alertId);
            if (alert) {
                currentActiveAlert = alert;
                // Update modal with alert details
                const alertTextEl = document.getElementById('resolveAlertText');
                if (alertTextEl) {
                    alertTextEl.textContent = alert.message;
                }
                openResolveAlertModal();
            } else {
                showToast('Alert not found', 'error');
            }
        }
    } catch (error) {
        console.error('Error fetching alert:', error);
        showToast('Failed to load alert details', 'error');
    }
}

function openResolveAlertModal() {
    const modal = document.getElementById('resolveAlertModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeResolveAlertModal() {
    const modal = document.getElementById('resolveAlertModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

async function confirmResolveAlert() {
    if (!currentActiveAlert || !currentActiveAlert.id) {
        showToast('No alert selected', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/officials/cancel-alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                alert_id: currentActiveAlert.id,
                is_resolved: true  // Mark this as a resolution, not a cancellation
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Alert marked as resolved successfully!', 'success');
            
            // Close modal
            closeResolveAlertModal();
            
            // Reload alerts table
            loadAlerts(currentAlertFilter);
            
            // Check if this was the active alert and hide banner
            checkForActiveAlert();
            
            // Add to recent activity
            addRecentActivity('Alert resolved', 'Just now');
        } else {
            showToast('Failed to resolve alert: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error resolving alert:', error);
        showToast('Failed to resolve alert. Please try again.', 'error');
    }
}

// Update confirmCancelAlert to use alert ID from table
async function confirmCancelAlertOriginal() {
    const nameInput = document.getElementById('cancellerName');
    const name = nameInput ? nameInput.value.trim() : '';
    
    if (name.length < 3) {
        showToast('Please enter your full name (minimum 3 characters)', 'warning');
        return;
    }
    
    try {
        const alertId = currentActiveAlert ? currentActiveAlert.id : null;
        
        if (!alertId) {
            showToast('No alert selected for cancellation', 'error');
            return;
        }
        
        const response = await fetch('/api/officials/cancel-alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                alert_id: alertId,
                cancelled_by: name
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Alert cancelled:', data.message);
            
            // Hide the banner
            const alertBanner = document.getElementById('alertBanner');
            if (alertBanner) {
                alertBanner.classList.add('hidden');
            }
            
            // Hide the Cancel Alert button
            const cancelBtn = document.getElementById('cancelAlertBtn');
            if (cancelBtn) {
                cancelBtn.classList.add('hidden');
            }
            
            // Close modal and clear input
            closeCancelAlertModal();
            if (nameInput) nameInput.value = '';
            
            // Reload alerts table
            loadAlerts(currentAlertFilter);
            
            // Add to recent activity
            addRecentActivity(`Alert cancelled by ${name}`, 'Just now');
            
            showToast(`Alert cancelled by ${name}`, 'success');
        } else {
            showToast('Failed to cancel alert: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error cancelling alert:', error);
        showToast('Failed to cancel alert. Please try again.', 'error');
    }
}

// Recent Activity Management
let recentActivities = [
    { text: 'Dashboard loaded', time: 'Just now' }
];

function addRecentActivity(text, time) {
    recentActivities.unshift({ text, time });
    if (recentActivities.length > 10) {
        recentActivities.pop();
    }
    updateRecentActivityDisplay();
}

function updateRecentActivityDisplay() {
    // Recent Activity section removed - alerts are shown in the main alerts card above
    console.log('Recent activities:', recentActivities);
}

// Edit Alert Modal Functions
let currentEditAlertId = null;
let editAlertLevel = 'critical';
let editAlertDuration = null;

function editAlertFromTable(alertId) {
    console.log('[EDIT] Starting edit for alert ID:', alertId);
    currentEditAlertId = alertId;
    
    // Fetch alert details using the correct endpoint
    fetch(`/api/officials/list-alerts?status=all`)
        .then(response => {
            console.log('[EDIT] Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('[EDIT] Response data:', data);
            if (data.success) {
                console.log('[EDIT] Number of alerts:', data.alerts.length);
                console.log('[EDIT] Alert IDs in response:', data.alerts.map(a => a.alert_id));
                const alert = data.alerts.find(a => a.alert_id === alertId);
                console.log('[EDIT] Found alert:', alert);
                if (alert) {
                    openEditAlertModal(alert);
                } else {
                    console.error('[EDIT] Alert not found. Looking for:', alertId);
                    showToast('Alert not found', 'error');
                }
            } else {
                console.error('[EDIT] API returned success=false:', data);
                showToast(data.error || 'Failed to load alerts', 'error');
            }
        })
        .catch(error => {
            console.error('[EDIT] Error fetching alert:', error);
            showToast('Error loading alert details', 'error');
        });
}

function openEditAlertModal(alert) {
    document.getElementById('editAlertMessage').value = alert.message || '';
    editAlertLevel = alert.level || 'critical';
    editAlertDuration = alert.duration_hours;
    
    // Update level buttons
    document.querySelectorAll('.edit-alert-level-btn').forEach(btn => {
        btn.classList.remove('active', 'border-blue-500', 'bg-blue-50', 'border-amber-500', 'bg-amber-50', 'border-red-500', 'bg-red-50');
        if (btn.dataset.level === editAlertLevel) {
            btn.classList.add('active');
            if (editAlertLevel === 'info') {
                btn.classList.add('border-blue-500', 'bg-blue-50');
            } else if (editAlertLevel === 'warning') {
                btn.classList.add('border-amber-500', 'bg-amber-50');
            } else if (editAlertLevel === 'critical') {
                btn.classList.add('border-red-500', 'bg-red-50');
            }
        }
    });
    
    // Update duration buttons
    document.querySelectorAll('.edit-alert-duration-btn').forEach(btn => {
        btn.classList.remove('active', 'border-navy-500', 'bg-navy-50');
        const btnDuration = btn.dataset.duration === 'null' ? null : parseInt(btn.dataset.duration);
        if (btnDuration === editAlertDuration) {
            btn.classList.add('active', 'border-navy-500', 'bg-navy-50');
        }
    });
    
    document.getElementById('editAlertModal').classList.remove('hidden');
}

function closeEditAlertModal() {
    document.getElementById('editAlertModal').classList.add('hidden');
    currentEditAlertId = null;
    document.getElementById('editAlertMessage').value = '';
    editAlertLevel = 'critical';
    editAlertDuration = null;
}

function setEditAlertLevel(level) {
    editAlertLevel = level;
    document.querySelectorAll('.edit-alert-level-btn').forEach(btn => {
        btn.classList.remove('active', 'border-blue-500', 'bg-blue-50', 'border-amber-500', 'bg-amber-50', 'border-red-500', 'bg-red-50');
        if (btn.dataset.level === level) {
            btn.classList.add('active');
            if (level === 'info') {
                btn.classList.add('border-blue-500', 'bg-blue-50');
            } else if (level === 'warning') {
                btn.classList.add('border-amber-500', 'bg-amber-50');
            } else if (level === 'critical') {
                btn.classList.add('border-red-500', 'bg-red-50');
            }
        }
    });
}

function setEditAlertDuration(hours) {
    editAlertDuration = hours;
    document.querySelectorAll('.edit-alert-duration-btn').forEach(btn => {
        btn.classList.remove('active', 'border-navy-500', 'bg-navy-50');
        const btnDuration = btn.dataset.duration === 'null' ? null : parseInt(btn.dataset.duration);
        if (btnDuration === hours) {
            btn.classList.add('active', 'border-navy-500', 'bg-navy-50');
        }
    });
}

function confirmEditAlert() {
    const message = document.getElementById('editAlertMessage').value.trim();
    
    if (!message) {
        showToast('Please enter an alert message', 'error');
        return;
    }
    
    if (!currentEditAlertId) {
        showToast('Invalid alert ID', 'error');
        return;
    }
    
    fetch('/api/officials/update-alert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            alert_id: currentEditAlertId,
            message: message,
            level: editAlertLevel,
            duration_hours: editAlertDuration
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Alert updated successfully!', 'success');
            closeEditAlertModal();
            loadAlerts(currentAlertStatus, selectedLevels);
            addRecentActivity('Alert updated', 'Just now');
            updateRecentActivityDisplay();
        } else {
            showToast(data.error || 'Failed to update alert', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating alert:', error);
        showToast('Error updating alert', 'error');
    });
}

// View Alert Details Modal Functions
function viewAlertDetails(alertId) {
    console.log('[VIEW] Starting view for alert ID:', alertId);
    
    // Fetch alert details using the correct endpoint
    fetch(`/api/officials/list-alerts?status=all`)
        .then(response => {
            console.log('[VIEW] Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('[VIEW] Response data:', data);
            if (data.success) {
                console.log('[VIEW] Number of alerts:', data.alerts.length);
                const alert = data.alerts.find(a => a.alert_id === alertId);
                console.log('[VIEW] Found alert:', alert);
                if (alert) {
                    openViewAlertModal(alert);
                } else {
                    console.error('[VIEW] Alert not found. Looking for:', alertId);
                    showToast('Alert not found', 'error');
                }
            } else {
                console.error('[VIEW] API returned success=false:', data);
                showToast(data.error || 'Failed to load alerts', 'error');
            }
        })
        .catch(error => {
            console.error('[VIEW] Error fetching alert:', error);
            showToast('Error loading alert details', 'error');
        });
}

function openViewAlertModal(alert) {
    // Populate status badge
    let statusBadge = '';
    if (alert.status === 'active') {
        statusBadge = '<span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold"><i class="fas fa-circle-check mr-1"></i>Active</span>';
    } else if (alert.cancelled_by && alert.cancelled_by.includes('System (Resolved)')) {
        statusBadge = '<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold"><i class="fas fa-check-circle mr-1"></i>Resolved</span>';
    } else {
        statusBadge = '<span class="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-semibold"><i class="fas fa-ban mr-1"></i>Cancelled</span>';
    }
    document.getElementById('viewAlertStatusBadge').innerHTML = statusBadge;
    
    // Populate level badge
    let levelBadge = '';
    if (alert.level === 'critical') {
        levelBadge = '<span class="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-semibold"><i class="fas fa-exclamation-triangle mr-1"></i>Critical</span>';
    } else if (alert.level === 'warning') {
        levelBadge = '<span class="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-semibold"><i class="fas fa-exclamation-circle mr-1"></i>Warning</span>';
    } else {
        levelBadge = '<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold"><i class="fas fa-info-circle mr-1"></i>Info</span>';
    }
    document.getElementById('viewAlertLevelBadge').innerHTML = levelBadge;
    
    // Populate message
    document.getElementById('viewAlertMessage').textContent = alert.message || 'No message';
    
    // Populate metadata
    document.getElementById('viewAlertIssuedBy').textContent = alert.issued_by || 'Unknown';
    document.getElementById('viewAlertIssuedAt').textContent = alert.issued_at ? new Date(alert.issued_at).toLocaleString() : 'Unknown';
    document.getElementById('viewAlertDuration').textContent = alert.duration_hours ? `${alert.duration_hours} hours` : 'Until Cancelled';
    document.getElementById('viewAlertExpiresAt').textContent = alert.expires_at ? new Date(alert.expires_at).toLocaleString() : 'Never';
    
    // Handle cancellation info
    if (alert.status === 'cancelled' && alert.cancelled_by) {
        document.getElementById('viewAlertCancellationInfo').classList.remove('hidden');
        document.getElementById('viewAlertCancelledBy').textContent = alert.cancelled_by;
        document.getElementById('viewAlertCancelledAt').textContent = alert.cancelled_at ? new Date(alert.cancelled_at).toLocaleString() : 'Unknown';
    } else {
        document.getElementById('viewAlertCancellationInfo').classList.add('hidden');
    }
    
    // Add action buttons for active alerts
    const actionsContainer = document.getElementById('viewAlertActions');
    if (alert.status === 'active') {
        actionsContainer.innerHTML = `
            <button onclick="editAlertFromView('${alert.alert_id}')" class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors">
                <i class="fas fa-edit mr-2"></i>Edit Alert
            </button>
            <button onclick="resolveAlertFromView('${alert.alert_id}')" class="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold transition-colors">
                <i class="fas fa-check mr-2"></i>Mark Resolved
            </button>
            <button onclick="cancelAlertFromView('${alert.alert_id}')" class="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors">
                <i class="fas fa-ban mr-2"></i>Cancel Alert
            </button>
        `;
    } else {
        actionsContainer.innerHTML = '';
    }
    
    // Show modal
    document.getElementById('viewAlertModal').classList.remove('hidden');
}

function editAlertFromView(alertId) {
    closeViewAlertModal();
    editAlertFromTable(alertId);
}

function resolveAlertFromView(alertId) {
    closeViewAlertModal();
    resolveAlertFromTable(alertId);
}

function cancelAlertFromView(alertId) {
    closeViewAlertModal();
    cancelAlertFromTable(alertId);
}

function closeViewAlertModal() {
    document.getElementById('viewAlertModal').classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== GENERATE REPORT FUNCTIONS =====

function openGenerateReportModal() {
    // Set default dates (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('reportStartDate').valueAsDate = startDate;
    document.getElementById('reportEndDate').valueAsDate = endDate;
    
    // Set default title with current date
    const today = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    document.getElementById('reportTitle').value = `Health Dashboard Report - ${today}`;
    
    // Show modal
    document.getElementById('generateReportModal').classList.remove('hidden');
    
    // Setup character counter for custom notes
    const notesDiv = document.getElementById('reportCustomNotes');
    const charCount = document.getElementById('reportNotesCharCount');
    notesDiv.addEventListener('input', function() {
        charCount.textContent = `${this.textContent.length} characters`;
    });
}

function closeGenerateReportModal() {
    document.getElementById('generateReportModal').classList.add('hidden');
}

function toggleAISummaryPreview() {
    const isChecked = document.getElementById('includeAISummary').checked;
    const container = document.getElementById('aiSummaryPreviewContainer');
    container.style.display = isChecked ? 'block' : 'none';
}

async function generateAISummaryPreview() {
    const button = event.target.closest('button');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
    button.disabled = true;
    
    try {
        const startDate = document.getElementById('reportStartDate').value;
        const endDate = document.getElementById('reportEndDate').value;
        
        const response = await fetch('/api/officials/generate-report-summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ startDate, endDate })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const summaryDiv = document.getElementById('aiSummaryText');
            summaryDiv.innerHTML = data.summary.replace(/\n/g, '<br>');
            document.getElementById('aiSummaryPreview').classList.remove('hidden');
            showToast('AI summary generated!', 'success');
        } else {
            showToast(data.error || 'Failed to generate summary', 'error');
        }
    } catch (error) {
        console.error('Error generating AI summary:', error);
        showToast('Error generating AI summary', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

function regenerateAISummary() {
    generateAISummaryPreview();
}

function setReportDateRange(days) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    document.getElementById('reportStartDate').valueAsDate = startDate;
    document.getElementById('reportEndDate').valueAsDate = endDate;
}

function formatReportText(format) {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    
    const range = selection.getRangeAt(0);
    const selectedText = range.toString();
    
    if (!selectedText) {
        showToast('Please select text to format', 'info');
        return;
    }
    
    let formattedElement;
    switch(format) {
        case 'bold':
            formattedElement = document.createElement('strong');
            break;
        case 'italic':
            formattedElement = document.createElement('em');
            break;
        case 'underline':
            formattedElement = document.createElement('u');
            break;
        case 'bullet':
            formattedElement = document.createElement('li');
            break;
    }
    
    if (formattedElement) {
        try {
            range.surroundContents(formattedElement);
        } catch(e) {
            // If can't surround (mixed elements), just apply execCommand
            document.execCommand(format === 'bullet' ? 'insertUnorderedList' : format, false, null);
        }
    }
}

async function generatePDFReport() {
    // Get all form values
    const customNotesDiv = document.getElementById('reportCustomNotes');
    const aiSummaryDiv = document.getElementById('aiSummaryText');
    
    const reportConfig = {
        includeAISummary: document.getElementById('includeAISummary').checked,
        aiSummaryText: aiSummaryDiv.innerHTML || '',
        startDate: document.getElementById('reportStartDate').value,
        endDate: document.getElementById('reportEndDate').value,
        includeCharts: document.getElementById('includeCharts').checked,
        includeAlerts: document.getElementById('includeAlerts').checked,
        includeReports: document.getElementById('includeReports').checked,
        includeAirQuality: document.getElementById('includeAirQuality').checked,
        includeStatistics: document.getElementById('includeStatistics').checked,
        includeLocations: document.getElementById('includeLocations').checked,
        customNotes: customNotesDiv.innerHTML || '',
        reportTitle: document.getElementById('reportTitle').value,
        preparedBy: document.getElementById('reportPreparedBy').value,
        recipients: document.getElementById('reportRecipients').value
    };
    
    // Validate
    if (!reportConfig.startDate || !reportConfig.endDate) {
        showToast('Please select start and end dates', 'error');
        return;
    }
    
    if (!reportConfig.reportTitle) {
        showToast('Please enter a report title', 'error');
        return;
    }
    
    // Show loading state
    showToast('Generating report... This may take a moment', 'info');
    
    try {
        // Call backend to generate PDF
        const response = await fetch('/api/officials/generate-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reportConfig)
        });
        
        if (response.ok) {
            // Check if response is PDF or JSON error
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/pdf')) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${reportConfig.reportTitle.replace(/[^a-z0-9]/gi, '_')}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                showToast('Report generated successfully!', 'success');
                closeGenerateReportModal();
                
                // If recipients specified, show send confirmation
                if (reportConfig.recipients) {
                    showToast(`Report sent to: ${reportConfig.recipients}`, 'success');
                }
            } else {
                // Handle error response
                const error = await response.json();
                showToast(error.error || 'Failed to generate report', 'error');
            }
        } else {
            // Try to parse error message
            try {
                const error = await response.json();
                showToast(error.error || 'Failed to generate report', 'error');
            } catch (e) {
                showToast(`Failed to generate report (${response.status})`, 'error');
            }
        }
    } catch (error) {
        console.error('Error generating report:', error);
        showToast('Error generating report. Please try again.', 'error');
    }
}

// Call check on page load
document.addEventListener('DOMContentLoaded', function() {
    checkForActiveAlert();
    loadAlerts('all'); // Load all alerts on page load
});

// Make alert functions globally available
window.openAlertModal = openAlertModal;
window.closeAlertModal = closeAlertModal;
window.setAlertLevel = setAlertLevel;
window.setAlertDuration = setAlertDuration;
window.sendAlert = sendAlert;
window.useAISummary = useAISummary;
window.dismissAlert = dismissAlert;
window.openCancelAlertModal = openCancelAlertModal;
window.closeCancelAlertModal = closeCancelAlertModal;
window.confirmCancelAlert = confirmCancelAlertOriginal;
window.filterAlerts = filterAlerts;
window.toggleLevelFilterDropdown = toggleLevelFilterDropdown;
window.toggleAllLevels = toggleAllLevels;
window.updateLevelFilters = updateLevelFilters;
window.editAlertFromTable = editAlertFromTable;
window.openEditAlertModal = openEditAlertModal;
window.closeEditAlertModal = closeEditAlertModal;
window.setEditAlertLevel = setEditAlertLevel;
window.setEditAlertDuration = setEditAlertDuration;
window.confirmEditAlert = confirmEditAlert;
window.viewAlertDetails = viewAlertDetails;
window.openViewAlertModal = openViewAlertModal;
window.closeViewAlertModal = closeViewAlertModal;
window.editAlertFromView = editAlertFromView;
window.resolveAlertFromView = resolveAlertFromView;
window.cancelAlertFromView = cancelAlertFromView;
window.toggleAlertsTable = toggleAlertsTable;
window.cancelAlertFromTable = cancelAlertFromTable;
window.editAlertFromTable = editAlertFromTable;
window.resolveAlertFromTable = resolveAlertFromTable;
window.openResolveAlertModal = openResolveAlertModal;
window.closeResolveAlertModal = closeResolveAlertModal;
window.confirmResolveAlert = confirmResolveAlert;
window.viewAlertDetails = viewAlertDetails;
window.openGenerateReportModal = openGenerateReportModal;
window.closeGenerateReportModal = closeGenerateReportModal;
window.toggleAISummaryPreview = toggleAISummaryPreview;
window.generateAISummaryPreview = generateAISummaryPreview;
window.regenerateAISummary = regenerateAISummary;
window.setReportDateRange = setReportDateRange;
window.formatReportText = formatReportText;
window.generatePDFReport = generatePDFReport;
window.loadAlerts = loadAlerts;
window.showToast = showToast;