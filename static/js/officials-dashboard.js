// Officials Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Global variables
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
    
    let currentPage = 1;
    const rowsPerPage = 20;
    let totalReports = 0;
    let allReports = [];
    let chartGranularity = 'day'; // 'hour' or 'day'
    let cachedChartReports = []; // Cache reports for chart updates
    let showAllColumns = false; // Column toggle state
    
    // Define column sets
    const conciseColumns = ['report_type', 'timestamp', 'city', 'state', 'zip_code', 'severity', 'description', 'status'];
    const allColumns = [
        'report_id', 'report_type', 'description', 'severity', 'status', 
        'street_address', 'city', 'state', 'county', 'zip_code',
        'timestamp', 'when_happened', 'affected_count', 'specific_type',
        'reporter_name', 'reporter_contact', 'ai_overall_summary', 'ai_media_summary',
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
        });
        
        // Severity filter
        document.getElementById('severityFilter').addEventListener('change', function() {
            currentFilters.severity = this.value;
        });
        
        // Status filter
        document.getElementById('statusFilter').addEventListener('change', function() {
            currentFilters.status = this.value;
        });
        
        // Timeframe filter
        document.getElementById('timeframeFilter').addEventListener('change', function() {
            currentFilters.timeframe = this.value;
        });
        
        // Apply filters button
        document.getElementById('applyFiltersBtn').addEventListener('click', function() {
            currentPage = 1;
            loadReportsData();
        });
        
        // Clear filters button
        document.getElementById('clearFiltersBtn').addEventListener('click', clearAllFilters);
        
        // Export buttons
        document.getElementById('exportCsvBtn').addEventListener('click', () => exportData('csv'));
        document.getElementById('exportExcelBtn').addEventListener('click', () => exportData('xlsx'));
        document.getElementById('exportPdfBtn').addEventListener('click', () => exportData('pdf'));
        document.getElementById('exportPngBtn').addEventListener('click', () => exportData('png'));
        
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
            
            // Add all filters
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
                totalReports = data.total;
                renderReportsTable(allReports);
                updatePagination();
                updateStatsCards(allReports);
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
    
    // Render reports table
    function renderReportsTable(reports) {
        // Render table headers
        renderTableHeaders();
        
        const tbody = document.getElementById('reportsTableBody');
        tbody.innerHTML = '';
        
        if (reports.length === 0) {
            const colspan = showAllColumns ? 23 : 7;
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
                // Show concise columns
                rowHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <div class="flex items-center">
                            <i class="fas ${typeIcon} mr-2"></i>
                            <span class="font-medium text-gray-900">${capitalize(report.report_type)}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <div>${formattedDate}</div>
                        <div class="text-xs text-gray-400">${formattedTime}</div>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-900">
                        <div class="font-medium">${report.city}, ${report.state}</div>
                        <div class="text-xs text-gray-500">${report.zip_code}${report.county ? ' • ' + report.county : ''}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${severityClass}">
                            ${capitalize(report.severity)}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-700 max-w-md truncate">
                        ${report.description || '-'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusClass}">
                            ${capitalize(report.status)}
                        </span>
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
    
    // Handle search
    function handleSearch(event) {
        const searchTerm = event.target.value.toLowerCase();
        
        if (!searchTerm) {
            renderReportsTable(allReports);
            return;
        }
        
        const filtered = allReports.filter(report => {
            return (
                report.description?.toLowerCase().includes(searchTerm) ||
                report.city?.toLowerCase().includes(searchTerm) ||
                report.state?.toLowerCase().includes(searchTerm) ||
                report.zip_code?.includes(searchTerm) ||
                report.report_type?.toLowerCase().includes(searchTerm) ||
                report.specific_type?.toLowerCase().includes(searchTerm)
            );
        });
        
        renderReportsTable(filtered);
    }
    
    // Export data
    async function exportData(format) {
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
                        <p class="mt-1 text-gray-900">${report.people_affected || 'Not specified'}</p>
                    </div>
                    <div>
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Timeframe</label>
                        <p class="mt-1 text-gray-900">${report.timeframe ? formatTimeframe(report.timeframe) : 'Not specified'}</p>
                    </div>
                    ${!report.is_anonymous ? `
                    <div class="col-span-2 border-t pt-4">
                        <label class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Contact Information</label>
                        <div class="mt-2 space-y-1">
                            <p class="text-gray-900"><i class="fas fa-user mr-2 text-gray-400"></i>${report.contact_name}</p>
                            ${report.contact_email ? `<p class="text-gray-900"><i class="fas fa-envelope mr-2 text-gray-400"></i>${report.contact_email}</p>` : ''}
                            ${report.contact_phone ? `<p class="text-gray-900"><i class="fas fa-phone mr-2 text-gray-400"></i>${report.contact_phone}</p>` : ''}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        modal.classList.remove('hidden');
    };
    
    // Close modal
    window.closeReportDetailModal = function() {
        document.getElementById('reportDetailModal').classList.add('hidden');
    };
    
    // Utility functions
    function capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
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
            'closed': 'bg-gray-100 text-gray-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
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
        alert(message); // You can replace this with a nicer toast notification
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
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Description</th>
                    <th class="px-6 py-4 text-left text-xs font-bold text-white uppercase tracking-wider">Status</th>
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
        } else {
            // Last 30 days by day
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
            window.aqiChart.options.scales.x.title.text = chartGranularity === 'hour' ? 'Hour' : 'Date';
            
            // Adjust X-axis display for readability
            if (chartGranularity === 'hour') {
                window.aqiChart.options.scales.x.ticks.maxRotation = 90;
                window.aqiChart.options.scales.x.ticks.minRotation = 45;
                window.aqiChart.options.scales.x.ticks.autoSkip = true;
                window.aqiChart.options.scales.x.ticks.maxTicksLimit = 12; // Show max 12 labels
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
            
            // Show percentages on the chart
            window.diseasesChart.options.plugins.datalabels = {
                color: '#fff',
                font: {
                    weight: 'bold',
                    size: 14
                },
                formatter: (value, ctx) => {
                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                    return percentage > 5 ? `${percentage}%` : ''; // Only show if > 5%
                }
            };
            
            window.diseasesChart.update();
        }
    }
    
    // Update ZIP codes chart
    function updateZipChart(allChartReports) {
        const zipCounts = {};
        allChartReports.forEach(report => {
            const zip = report.zip_code || 'Unknown';
            zipCounts[zip] = (zipCounts[zip] || 0) + 1;
        });
        
        // Get top 10 ZIP codes
        const sortedZips = Object.entries(zipCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        
        const zipLabels = sortedZips.length > 0 ? 
            sortedZips.map(([zip, count]) => `${zip}`) : 
            ['No Data'];
        const zipData = sortedZips.length > 0 ? 
            sortedZips.map(([zip, count]) => count) : 
            [0];
        
        const zipColors = [
            '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', 
            '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
        ];
        
        const total = zipData.reduce((sum, val) => sum + val, 0);
        
        // Update ZIP codes chart
        if (window.zipCodesChart) {
            window.zipCodesChart.data.labels = zipLabels;
            window.zipCodesChart.data.datasets[0].data = zipData;
            window.zipCodesChart.data.datasets[0].backgroundColor = zipColors.slice(0, zipLabels.length);
            window.zipCodesChart.options.plugins.title.text = `Top 10 ZIP Codes (Total: ${total} reports)`;
            
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
                        return [
                            `ZIP ${label}: ${value} reports`,
                            `${percentage}% of total`
                        ];
                    }
                }
            };
            
            // Show percentages on the chart
            window.zipCodesChart.options.plugins.datalabels = {
                color: '#fff',
                font: {
                    weight: 'bold',
                    size: 12
                },
                formatter: (value, ctx) => {
                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                    return percentage > 5 ? `${percentage}%` : ''; // Only show if > 5%
                }
            };
            
            window.zipCodesChart.update();
        }
    }
});
