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
    let locationGroupBy = 'zipcode'; // 'zipcode', 'city', 'county', or 'state'
    let cachedChartReports = []; // Cache reports for chart updates
    let showAllColumns = false; // Column toggle state
    
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
                totalReports = data.total;
                applyClientSideFilters();
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
    
    // Handle search
    function handleSearch(event) {
        applyClientSideFilters();
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
                <p class="text-gray-700 text-sm leading-relaxed whitespace-pre-line">${messageContent}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bg-navy-700 text-white rounded-2xl rounded-tr-none p-3 shadow-md max-w-[280px]">
                <p class="text-sm leading-relaxed">${text}</p>
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
    const maxAttempts = 120; // 2 minutes max
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
            } else if (data.status === 'processing' || data.status === 'pending') {
                console.log(`[VIDEO WIDGET] Video still processing (progress: ${data.progress || 'unknown'})`);
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
async function postToTwitterWidget(videoData) {
    try {
        addChatMessage('Posting to Twitter...', 'bot');
        
        const response = await fetch('/api/post-to-twitter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_url: videoData.video_url,
                action_line: videoData.action_line,
                health_data: videoData.health_data || {}
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.tweet_url) {
            addChatMessage(
                `Posted to Twitter successfully!\n\nView your post: ${data.tweet_url}\n\nTweet posted successfully!`,
                'bot'
            );
            lastVideoData = null; // Clear after posting
        } else {
            addChatMessage(`Failed to post to Twitter: ${data.error || 'Unknown error'}`, 'bot');
        }
    } catch (error) {
        console.error('[TWITTER] Error posting:', error);
        addChatMessage('Error posting to Twitter. Please try again.', 'bot');
    }
}

// Make functions globally available
window.toggleChatWidget = toggleChatWidget;
window.minimizeChatWidget = minimizeChatWidget;
window.closeChatWidget = closeChatWidget;
window.sendChatWidgetMessage = sendChatWidgetMessage;
window.clearChatWidget = clearChatWidget;
window.askQuickQuestion = askQuickQuestion;