/**
 * NREVSS Respiratory Virus Dashboard Chart
 * Interactive time series visualization with date slider and hover tooltips
 */

class RespiratoryChart {
    constructor(containerId) {
        this.containerId = containerId;
        this.chart = null;
        this.data = [];
        this.filteredData = [];
        this.dateRange = { start: null, end: null };
        
        // Chart colors matching CDC dashboard
        this.colors = {
            RSV: '#7b68ee',           // Purple
            'SARS-COV-2': '#2b2b2b',  // Black
            Influenza: '#4169e1',      // Blue
            HMPV: '#90ee90',          // Light Green
            HCOV: '#ff6347',          // Red
            PIV: '#ffd700',           // Gold
            Adenovirus: '#87ceeb',    // Sky Blue
            'RV/EV': '#ff69b4'        // Pink
        };
        
        this.init();
    }
    
    // Normalize item.date to ISO (YYYY-MM-DD) and drop malformed rows
    normalizeDataDates() {
        const monthMap = {
            'JAN': 0, 'FEB': 1, 'MAR': 2, 'APR': 3, 'MAY': 4, 'JUN': 5,
            'JUL': 6, 'AUG': 7, 'SEP': 8, 'OCT': 9, 'NOV': 10, 'DEC': 11
        };
        const originalLen = this.data.length;
        const normalized = [];
        for (const item of this.data) {
            let iso = null;
            const v = item && item.date;
            if (typeof v === 'string') {
                // ISO YYYY-MM-DD
                if (/^\d{4}-\d{2}-\d{2}$/.test(v)) {
                    const d = new Date(v);
                    if (!isNaN(d)) iso = v;
                } else if (/^\d{2}[A-Z]{3}\d{4}$/.test(v)) {
                    // ddMONyyyy e.g., 10JUL2010
                    const dd = parseInt(v.slice(0, 2), 10);
                    const mon = v.slice(2, 5).toUpperCase();
                    const yyyy = parseInt(v.slice(5, 9), 10);
                    const m = monthMap[mon];
                    if (!isNaN(dd) && !isNaN(yyyy) && m !== undefined) {
                        const d = new Date(Date.UTC(yyyy, m, dd));
                        if (!isNaN(d)) iso = d.toISOString().slice(0, 10);
                    }
                } else {
                    // Try native Date parsing last
                    const d = new Date(v);
                    if (!isNaN(d)) iso = d.toISOString().slice(0, 10);
                }
            } else if (v instanceof Date && !isNaN(v)) {
                iso = v.toISOString().slice(0, 10);
            }

            if (iso) {
                normalized.push({ ...item, date: iso });
            }
        }
        this.data = normalized;
        console.log('[RESPIRATORY CHART] Normalized dates:', this.data.length, '/', originalLen, 'valid');
        if (this.data.length && this.data[0]) {
            console.log('[RESPIRATORY CHART] First normalized item:', this.data[0]);
        }
    }

    init() {
        console.log('[RESPIRATORY CHART] Initializing...');
        this.createChartContainer();
    }
    
    createChartContainer() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('[RESPIRATORY CHART] Container not found:', this.containerId);
            return;
        }
        
        container.innerHTML = `
            <div class="respiratory-chart-wrapper">
                <div class="chart-header mb-6">
                    <h3 class="text-2xl font-bold text-navy-700 mb-2">
                        <i class="fas fa-database text-blue-500 mr-2"></i>
                        Infectious Disease Tracking Dashboard (BigQuery Data)
                    </h3>
                    <div class="flex items-center gap-4 text-sm text-gray-600">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-map-marker-alt text-blue-500"></i>
                            <span id="chartLocationIndicator">National</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-calendar text-blue-500"></i>
                            <span id="chartDateRange">Loading...</span>
                        </div>
                    </div>
                </div>
                
                <div class="chart-canvas-wrapper bg-white rounded-xl shadow-lg p-6 mb-4">
                    <canvas id="respiratoryCanvas" height="400"></canvas>
                </div>
                
                <div class="chart-controls-wrapper bg-white rounded-xl shadow-lg p-6 mb-4">
                    <div class="mb-3">
                        <h4 class="text-sm font-semibold text-gray-700 mb-3">
                            <i class="fas fa-filter mr-2"></i>Filter Data Series
                        </h4>
                        <div id="dataSeriesCheckboxes" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                            <!-- Checkboxes will be populated dynamically -->
                        </div>
                    </div>
                    <div class="flex items-center justify-between text-xs text-gray-500 mt-3 pt-3 border-t">
                        <button id="selectAllSeries" class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition">
                            <i class="fas fa-check-double mr-1"></i>Select All
                        </button>
                        <button id="deselectAllSeries" class="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition">
                            <i class="fas fa-times mr-1"></i>Deselect All
                        </button>
                    </div>
                </div>
                
                <div class="date-slider-wrapper bg-white rounded-xl shadow-lg p-6">
                    <div class="flex items-center gap-4">
                        <label class="text-sm font-semibold text-gray-700 whitespace-nowrap">
                            <i class="fas fa-sliders-h mr-2"></i>Date Range:
                        </label>
                        <div class="flex-1 relative">
                            <div class="range-slider-container relative h-6">
                                <input type="range" id="dateSliderMin" class="range-slider-input" min="0" max="100" value="0">
                                <input type="range" id="dateSliderMax" class="range-slider-input" min="0" max="100" value="100">
                                <div class="range-slider-track"></div>
                                <div class="range-slider-range" id="sliderRange"></div>
                            </div>
                        </div>
                        <div class="text-sm font-mono text-gray-600 min-w-[200px]">
                            <span id="sliderStartDate">-</span> to <span id="sliderEndDate">-</span>
                        </div>
                        <button id="resetSlider" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition text-sm">
                            <i class="fas fa-undo mr-1"></i>Reset to 3 Months
                        </button>
                    </div>
                    <style>
                        .range-slider-container {
                            position: relative;
                            width: 100%;
                        }
                        .range-slider-input {
                            position: absolute;
                            width: 100%;
                            height: 6px;
                            background: transparent;
                            pointer-events: none;
                            -webkit-appearance: none;
                            z-index: 3;
                        }
                        .range-slider-input::-webkit-slider-thumb {
                            -webkit-appearance: none;
                            appearance: none;
                            width: 18px;
                            height: 18px;
                            border-radius: 50%;
                            background: #3b82f6;
                            cursor: pointer;
                            pointer-events: all;
                            border: 2px solid white;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        }
                        .range-slider-input::-moz-range-thumb {
                            width: 18px;
                            height: 18px;
                            border-radius: 50%;
                            background: #3b82f6;
                            cursor: pointer;
                            pointer-events: all;
                            border: 2px solid white;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        }
                        .range-slider-track {
                            position: absolute;
                            width: 100%;
                            height: 6px;
                            background: #e5e7eb;
                            border-radius: 3px;
                            top: 50%;
                            transform: translateY(-50%);
                            z-index: 1;
                        }
                        .range-slider-range {
                            position: absolute;
                            height: 6px;
                            background: #3b82f6;
                            border-radius: 3px;
                            top: 50%;
                            transform: translateY(-50%);
                            z-index: 2;
                        }
                    </style>
                </div>
                
                <div class="chart-legend mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
                    <!-- Legend will be populated dynamically -->
                </div>
                
                <div class="chart-footer mt-4 text-xs text-gray-500">
                    <p>
                        <i class="fas fa-info-circle mr-1"></i>
                        Sources: CDC NREVSS (RSV PCR tests), CDC FluSurv-NET (Hospitalization rates), CDC COVID-19 Surveillance
                        ΓÇó Updated weekly ΓÇó Data from BigQuery
                    </p>
                </div>
            </div>
        `;
    }
    
    async loadData(state = '') {
        console.log('[RESPIRATORY CHART] Loading data from BigQuery for state:', state || 'National');
        
        try {
            // Use the new infectious disease dashboard endpoint that queries BigQuery directly
            const url = state 
                ? `/api/infectious-disease-dashboard?state=${encodeURIComponent(state)}&days=180`
                : '/api/infectious-disease-dashboard?days=180';
            
            const response = await fetch(url);
            const result = await response.json();
            
            console.log('[RESPIRATORY CHART] BigQuery dashboard response:', result.status);
            
            if (result.status === 'success') {
                // Combine data from all three BigQuery sources
                const combinedData = [];
                
                // 1. Add NREVSS PCR data (RSV from nrevss_respiratory_data table)
                if (result.nrevss_data && result.nrevss_data.length > 0) {
                    console.log('[RESPIRATORY CHART] Processing', result.nrevss_data.length, 'NREVSS records from BigQuery');
                    result.nrevss_data.forEach(item => {
                        combinedData.push({
                            date: item.date,
                            testtype: 'RSV (PCR)',
                            positivity_rate: item.pcr_percent_positive,
                            detections: item.pcr_detections,
                            source: 'NREVSS BigQuery'
                        });
                    });
                }
                
                // 2. Add respiratory disease rates (RSV, COVID-19, Flu from respiratory_disease_rates table)
                if (result.respiratory_rates && result.respiratory_rates.length > 0) {
                    console.log('[RESPIRATORY CHART] Processing', result.respiratory_rates.length, 'respiratory rate records from BigQuery');
                    result.respiratory_rates.forEach(item => {
                        // Map surveillance network to friendly names
                        const networkName = item.surveillance_network || 'Unknown';
                        let displayName = networkName;
                        
                        // Simplify network names
                        if (networkName.includes('COVID')) displayName = 'COVID';
                        else if (networkName.includes('RSV')) displayName = 'RSV';
                        else if (networkName.includes('Flu')) displayName = 'Flu';
                        
                        combinedData.push({
                            date: item.date,
                            testtype: displayName,
                            positivity_rate: item.rate, // Use actual rate (per 100k)
                            cumulative_rate: item.cumulative_rate,
                            source: 'FluSurv-NET BigQuery',
                            surveillance_network: networkName,
                            rate_type: 'hospitalization_per_100k'
                        });
                    });
                }
                
                // 3. Add COVID hospitalizations (from cdc_covid_hospitalizations table)
                if (result.covid_hospitalizations && result.covid_hospitalizations.length > 0) {
                    console.log('[RESPIRATORY CHART] Processing', result.covid_hospitalizations.length, 'COVID hospitalization records from BigQuery');
                    result.covid_hospitalizations.forEach(item => {
                        combinedData.push({
                            date: item.date,
                            testtype: 'COVID-19 Hospitalizations',
                            positivity_rate: item.weekly_rate,
                            cumulative_rate: item.cumulative_rate,
                            source: 'CDC Hospitalizations BigQuery'
                        });
                    });
                }
                
                this.data = combinedData;
                console.log('[RESPIRATORY CHART] Combined', this.data.length, 'data points from BigQuery tables');
                console.log('[RESPIRATORY CHART] Sample combined data:', this.data.slice(0, 3));
                
                // Log unique diseases found
                const uniqueDiseases = [...new Set(this.data.map(d => d.testtype))];
                console.log('[RESPIRATORY CHART] Unique diseases found:', uniqueDiseases);
                
                // Normalize dates to ISO and drop malformed entries
                this.normalizeDataDates();
                console.log('[RESPIRATORY CHART] Using', this.data.length, 'normalized data points');
                
                // Update location indicator
                const locationEl = document.getElementById('chartLocationIndicator');
                if (locationEl) {
                    locationEl.textContent = state || 'National';
                }
                
                // Update header with source info
                const headerEl = document.querySelector('.chart-header h3');
                if (headerEl) {
                    headerEl.innerHTML = `
                        <i class="fas fa-database text-blue-500 mr-2"></i>
                        Infectious Disease Tracking Dashboard (BigQuery Data)
                    `;
                }
                
                // Set default to last 3 months
                this.setDefaultDateRange();
                this.initializeSlider();
                this.renderChart();
            } else {
                console.warn('[RESPIRATORY CHART] No BigQuery data available:', result);
                this.showNoDataMessage();
            }
        } catch (error) {
            console.error('[RESPIRATORY CHART] Error loading BigQuery data:', error);
            this.showErrorMessage(error.message);
        }
    }
    
    setDefaultDateRange() {
        console.log('[RESPIRATORY CHART] setDefaultDateRange() - Data length:', this.data.length);
        if (this.data.length === 0) {
            console.error('[RESPIRATORY CHART] Cannot set date range - no data!');
            return;
        }
        
        // Get the most recent date
        console.log('[RESPIRATORY CHART] Sample date from data:', this.data[0].date);
        const dates = this.data.map(d => new Date(d.date)).sort((a, b) => b - a);
        console.log('[RESPIRATORY CHART] Parsed', dates.length, 'dates');
        const latestDate = dates[0];
        console.log('[RESPIRATORY CHART] Latest date:', latestDate);
        
        // Calculate 3 months ago
        const threeMonthsAgo = new Date(latestDate);
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        
        this.dateRange.end = latestDate;
        this.dateRange.start = threeMonthsAgo;
        
        console.log('[RESPIRATORY CHART] Date range set:', 
            this.dateRange.start.toLocaleDateString(), 'to', 
            this.dateRange.end.toLocaleDateString());
        
        this.filterDataByDateRange();
    }
    
    initializeSlider() {
        const sliderMin = document.getElementById('dateSliderMin');
        const sliderMax = document.getElementById('dateSliderMax');
        const sliderRange = document.getElementById('sliderRange');
        const resetBtn = document.getElementById('resetSlider');
        
        if (!sliderMin || !sliderMax || this.data.length === 0) return;
        
        // Get all unique dates sorted
        const allDates = [...new Set(this.data.map(d => d.date))].sort();
        
        sliderMin.min = 0;
        sliderMin.max = allDates.length - 1;
        sliderMax.min = 0;
        sliderMax.max = allDates.length - 1;
        
        // Set slider to show last 3 months by default
        const endIndex = allDates.length - 1;
        const threeMonthsAgo = new Date(allDates[endIndex]);
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        
        const startIndex = allDates.findIndex(d => new Date(d) >= threeMonthsAgo);
        const defaultStartIndex = startIndex >= 0 ? startIndex : 0;
        
        sliderMin.value = defaultStartIndex;
        sliderMax.value = endIndex;
        
        // Update visual range
        this.updateSliderRange(sliderMin, sliderMax, sliderRange);
        
        // Update date labels
        this.updateSliderLabels(allDates[defaultStartIndex], allDates[endIndex]);
        
        // Function to update range display
        const updateRange = () => {
            let minVal = parseInt(sliderMin.value);
            let maxVal = parseInt(sliderMax.value);
            
            // Ensure min doesn't exceed max
            if (minVal > maxVal) {
                const temp = minVal;
                minVal = maxVal;
                maxVal = temp;
                sliderMin.value = minVal;
                sliderMax.value = maxVal;
            }
            
            this.dateRange.start = new Date(allDates[minVal]);
            this.dateRange.end = new Date(allDates[maxVal]);
            
            this.updateSliderRange(sliderMin, sliderMax, sliderRange);
            this.updateSliderLabels(allDates[minVal], allDates[maxVal]);
            this.filterDataByDateRange();
            this.renderChart();
        };
        
        // Slider events
        sliderMin.addEventListener('input', updateRange);
        sliderMax.addEventListener('input', updateRange);
        
        // Reset button
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                sliderMin.value = defaultStartIndex;
                sliderMax.value = endIndex;
                this.setDefaultDateRange();
                this.updateSliderRange(sliderMin, sliderMax, sliderRange);
                this.updateSliderLabels(allDates[defaultStartIndex], allDates[endIndex]);
                this.renderChart();
            });
        }
    }
    
    updateSliderRange(sliderMin, sliderMax, rangeEl) {
        if (!rangeEl) return;
        
        const minVal = parseInt(sliderMin.value);
        const maxVal = parseInt(sliderMax.value);
        const minPercent = (minVal / sliderMin.max) * 100;
        const maxPercent = (maxVal / sliderMax.max) * 100;
        
        rangeEl.style.left = minPercent + '%';
        rangeEl.style.width = (maxPercent - minPercent) + '%';
    }
    
    updateSliderLabels(startDate, endDate) {
        const startEl = document.getElementById('sliderStartDate');
        const endEl = document.getElementById('sliderEndDate');
        
        if (startEl) startEl.textContent = new Date(startDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        if (endEl) endEl.textContent = new Date(endDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    }
    
    filterDataByDateRange() {
        if (!this.dateRange.start || !this.dateRange.end) {
            this.filteredData = this.data;
            return;
        }
        
        this.filteredData = this.data.filter(d => {
            const date = new Date(d.date);
            return date >= this.dateRange.start && date <= this.dateRange.end;
        });
        
        console.log('[RESPIRATORY CHART] Filtered to', this.filteredData.length, 'points');
    }
    
    renderChart() {
        const canvas = document.getElementById('respiratoryCanvas');
        if (!canvas) {
            console.error('[RESPIRATORY CHART] Canvas not found');
            return;
        }
        
        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }
        
        // Group data by date and testtype
        const dataByDate = {};
        
        this.filteredData.forEach(item => {
            if (!dataByDate[item.date]) {
                dataByDate[item.date] = {};
            }
            dataByDate[item.date][item.testtype] = item.positivity_rate;
        });
        
        // Get sorted dates
        const dates = Object.keys(dataByDate).sort();
        console.log('[RESPIRATORY CHART] Unique dates for chart:', dates.length);
        
        // Get all test types
        const testTypes = [...new Set(this.filteredData.map(d => d.testtype))];
        console.log('[RESPIRATORY CHART] Test types found:', testTypes);
        
        // Define comprehensive color mapping for surveillance networks
        const colorMap = {
            // Main surveillance networks (simplified names)
            'COVID': '#1a1a1a',                             // Very Dark Gray
            'RSV': '#7b68ee',                               // Purple
            'Flu': '#1e90ff',                               // Dodger Blue
            
            // NREVSS data (PCR tests)
            'RSV (PCR)': '#9370db',                         // Medium Purple
            'RSV (Antigen)': '#9370db',                     // Medium Purple
            
            // COVID surveillance (legacy)
            'COVID-19': '#2b2b2b',                          // Black
            'COVID-19 Hospitalizations': '#404040',         // Dark Gray
            
            // Full network names (fallback)
            'COVID-NET': '#1a1a1a',                         // Very Dark Gray
            'RSV-NET': '#7b68ee',                           // Purple
            'FluSurv-NET': '#1e90ff',                       // Dodger Blue
            
            // Generic fallbacks
            'Influenza': '#4169e1',                         // Royal Blue
            'SARS-COV-2': '#2b2b2b'                        // Black
        };
        
        // Function to generate color for unknown test types
        const getColorForTestType = (testType) => {
            if (colorMap[testType]) {
                return colorMap[testType];
            }
            
            // Generate color based on test type hash
            let hash = 0;
            for (let i = 0; i < testType.length; i++) {
                hash = testType.charCodeAt(i) + ((hash << 5) - hash);
            }
            const hue = Math.abs(hash % 360);
            return `hsl(${hue}, 70%, 50%)`;
        };
        
        // Create datasets for each test type
        const datasets = testTypes.map(testType => {
            const data = dates.map(date => dataByDate[date][testType] || null);
            
            // Determine color and label
            let color = getColorForTestType(testType);
            let label = testType;
            
            // Simplify labels if needed
            if (testType === 'Antigen') label = 'RSV (Antigen)';
            if (testType === 'PCR') label = 'RSV (PCR)';
            
            return {
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 2,
                tension: 0.4,
                fill: false,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                hidden: false  // Will be controlled by checkboxes
            };
        });
        
        // Format dates for labels
        const labels = dates.map(d => {
            const date = new Date(d);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
        });
        
        // Create chart
        const ctx = canvas.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12,
                                family: "'Inter', sans-serif"
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y.toFixed(2);
                                
                                // Check if this is a hospitalization rate (per 100k) or percentage
                                if (label.includes('(Hosp)')) {
                                    return label + ': ' + value + ' per 100k';
                                } else if (label.includes('Hospitalizations')) {
                                    return label + ': ' + value + ' per 100k';
                                } else {
                                    return label + ': ' + value + '%';
                                }
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Week Ending Date',
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Rate (% or per 100k)',
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1);
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });
        
        // Update date range indicator
        const dateRangeEl = document.getElementById('chartDateRange');
        if (dateRangeEl && dates.length > 0) {
            const firstDate = new Date(dates[0]).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            const lastDate = new Date(dates[dates.length - 1]).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            dateRangeEl.textContent = `${firstDate} - ${lastDate}`;
        }
        
        console.log('[RESPIRATORY CHART] Chart rendered with', dates.length, 'data points');
        
        // Create checkboxes for data series
        this.createSeriesCheckboxes();
    }
    
    createSeriesCheckboxes() {
        const container = document.getElementById('dataSeriesCheckboxes');
        if (!container || !this.chart) return;
        
        // Clear existing checkboxes
        container.innerHTML = '';
        
        // Create checkbox for each dataset
        this.chart.data.datasets.forEach((dataset, index) => {
            const checkboxId = `series-checkbox-${index}`;
            const color = dataset.borderColor;
            
            const checkboxHTML = `
                <label class="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer transition">
                    <input type="checkbox" 
                           id="${checkboxId}" 
                           class="series-checkbox w-4 h-4 rounded" 
                           data-index="${index}" 
                           checked>
                    <span class="w-3 h-3 rounded" style="background-color: ${color}"></span>
                    <span class="text-sm text-gray-700">${dataset.label}</span>
                </label>
            `;
            
            container.insertAdjacentHTML('beforeend', checkboxHTML);
        });
        
        // Add event listeners to checkboxes
        document.querySelectorAll('.series-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index);
                const meta = this.chart.getDatasetMeta(index);
                meta.hidden = !e.target.checked;
                this.chart.update();
            });
        });
        
        // Add select/deselect all buttons
        const selectAllBtn = document.getElementById('selectAllSeries');
        const deselectAllBtn = document.getElementById('deselectAllSeries');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                document.querySelectorAll('.series-checkbox').forEach(cb => {
                    cb.checked = true;
                    const index = parseInt(cb.dataset.index);
                    const meta = this.chart.getDatasetMeta(index);
                    meta.hidden = false;
                });
                this.chart.update();
            });
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => {
                document.querySelectorAll('.series-checkbox').forEach(cb => {
                    cb.checked = false;
                    const index = parseInt(cb.dataset.index);
                    const meta = this.chart.getDatasetMeta(index);
                    meta.hidden = true;
                });
                this.chart.update();
            });
        }
    }
    
    showNoDataMessage() {
        const canvas = document.getElementById('respiratoryCanvas');
        if (canvas) {
            canvas.parentElement.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i class="fas fa-chart-line text-5xl mb-4"></i>
                    <p class="text-lg">No respiratory surveillance data available</p>
                    <p class="text-sm mt-2">Try selecting a different location or date range</p>
                </div>
            `;
        }
    }
    
    showErrorMessage(message) {
        const canvas = document.getElementById('respiratoryCanvas');
        if (canvas) {
            canvas.parentElement.innerHTML = `
                <div class="text-center py-12 text-red-500">
                    <i class="fas fa-exclamation-circle text-5xl mb-4"></i>
                    <p class="text-lg">Error loading chart data</p>
                    <p class="text-sm mt-2">${message}</p>
                </div>
            `;
        }
    }
    
    updateLocation(state) {
        console.log('[RESPIRATORY CHART] Updating location to:', state);
        this.loadData(state);
    }
}

// Initialize chart when DOM is ready
let respiratoryChart = null;
let currentDiseasePeriod = 7; // Default to 7 days

document.addEventListener('DOMContentLoaded', function() {
    console.log('[RESPIRATORY CHART] ========================================');
    console.log('[RESPIRATORY CHART] DOM READY - Initializing');
    console.log('[RESPIRATORY CHART] ========================================');
    
    // Wait a bit for other scripts to initialize
    setTimeout(() => {
        console.log('[RESPIRATORY CHART] Creating RespiratoryChart instance...');
        respiratoryChart = new RespiratoryChart('respiratoryChartContainer');
        console.log('[RESPIRATORY CHART] Chart instance created:', !!respiratoryChart);
        
        // Load initial data (national or from stored location)
        const storedLocation = localStorage.getItem('selectedLocation');
        console.log('[RESPIRATORY CHART] Stored location:', storedLocation);
        
        if (storedLocation) {
            try {
                const location = JSON.parse(storedLocation);
                console.log('[RESPIRATORY CHART] Parsed location:', location);
                if (location.state) {
                    console.log('[RESPIRATORY CHART] Loading data for state:', location.state);
                    respiratoryChart.loadData(location.state);
                } else {
                    console.log('[RESPIRATORY CHART] Loading national data (no state in location)');
                    respiratoryChart.loadData();
                }
            } catch (e) {
                console.error('[RESPIRATORY CHART] Error parsing stored location:', e);
                console.log('[RESPIRATORY CHART] Loading national data (parse error)');
                respiratoryChart.loadData();
            }
        } else {
            console.log('[RESPIRATORY CHART] Loading national data (no stored location)');
            respiratoryChart.loadData();
        }
        
        // Load initial disease cards
        console.log('[RESPIRATORY CHART] Initializing disease cards...');
        updateDiseaseCards(7);
    }, 500);
});

/**
 * Update disease cards with data for specified time period
 */
async function updateDiseaseCards(days) {
    console.log('[DISEASE CARDS] ========== UPDATING CARDS (BigQuery) ==========');
    console.log('[DISEASE CARDS] Days:', days);
    
    currentDiseasePeriod = days;
    
    // Update button styles
    document.querySelectorAll('.disease-period-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-500', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    event?.target.classList.remove('bg-gray-200', 'text-gray-700');
    event?.target.classList.add('active', 'bg-blue-500', 'text-white');
    
    // Get current state - try multiple sources
    let state = '';
    if (typeof window.currentState !== 'undefined') {
        state = window.currentState;
    } else if (typeof currentState !== 'undefined') {
        state = currentState;
    }
    
    const locationText = state || 'National';
    console.log('[DISEASE CARDS] Current state from window:', window.currentState);
    console.log('[DISEASE CARDS] Current state from local:', typeof currentState !== 'undefined' ? currentState : 'undefined');
    console.log('[DISEASE CARDS] Using state:', state, 'Location text:', locationText);
    
    // Update location indicator
    const locationEl = document.getElementById('diseaseCardsLocation');
    if (locationEl) {
        locationEl.innerHTML = `<i class="fas fa-database mr-1"></i>${locationText} (BigQuery)`;
        console.log('[DISEASE CARDS] Updated location indicator');
    }
    
    try {
        // Fetch from BigQuery dashboard endpoint
        const url = state 
            ? `/api/infectious-disease-dashboard?state=${encodeURIComponent(state)}&days=${days}`
            : `/api/infectious-disease-dashboard?days=${days}`;
        
        console.log('[DISEASE CARDS] Fetching BigQuery data:', url);
        const response = await fetch(url);
        console.log('[DISEASE CARDS] Response status:', response.status);
        const result = await response.json();
        console.log('[DISEASE CARDS] BigQuery Result status:', result.status);
        console.log('[DISEASE CARDS] Full API Response:', JSON.stringify(result, null, 2));
        
        if (result.status === 'success') {
            console.log('[DISEASE CARDS] Γ£ô BigQuery data received');
            
            // Process RSV data from NREVSS
            if (result.nrevss_data && result.nrevss_data.length > 0) {
                const avgRsvPositivity = result.nrevss_data.reduce((sum, d) => 
                    sum + (d.pcr_percent_positive || 0), 0) / result.nrevss_data.length;
                console.log('[DISEASE CARDS] RSV avg positivity from BigQuery:', avgRsvPositivity.toFixed(2) + '%');
                
                updateDiseaseCard('rsv', {
                    positivity: avgRsvPositivity,
                    name: 'RSV',
                    color: 'blue',
                    trend: calculateTrend(result.nrevss_data, 'pcr_percent_positive')
                });
            } else {
                console.log('[DISEASE CARDS] No RSV data available - showing 0');
                updateDiseaseCard('rsv', { 
                    positivity: 0, 
                    name: 'RSV', 
                    color: 'blue', 
                    trend: 'stable' 
                });
            }
            
            // Process COVID data from respiratory_rates and hospitalizations
            const covidRates = result.respiratory_rates?.filter(d => d.disease === 'COVID-19') || [];
            const covidHosp = result.covid_hospitalizations || [];
            
            if (covidRates.length > 0 || covidHosp.length > 0) {
                // Use hospitalization rate as primary metric
                const avgCovidRate = covidHosp.length > 0
                    ? covidHosp.reduce((sum, d) => sum + (d.weekly_rate || 0), 0) / covidHosp.length
                    : covidRates.reduce((sum, d) => sum + (d.rate || 0), 0) / covidRates.length;
                
                console.log('[DISEASE CARDS] COVID avg rate from BigQuery:', avgCovidRate);
                
                updateDiseaseCard('covid', {
                    positivity: avgCovidRate,
                    name: 'COVID-19',
                    color: 'emerald',
                    trend: calculateTrend(covidHosp.length > 0 ? covidHosp : covidRates, 
                                         covidHosp.length > 0 ? 'weekly_rate' : 'rate')
                });
            } else {
                console.log('[DISEASE CARDS] No COVID data available - showing 0');
                updateDiseaseCard('covid', { 
                    positivity: 0, 
                    name: 'COVID-19', 
                    color: 'emerald', 
                    trend: 'stable' 
                });
            }
            
            // Process Flu data from respiratory_rates
            const fluRates = result.respiratory_rates?.filter(d => d.disease === 'Influenza') || [];
            
            if (fluRates.length > 0) {
                const avgFluRate = fluRates.reduce((sum, d) => sum + (d.rate || 0), 0) / fluRates.length;
                console.log('[DISEASE CARDS] Flu avg rate from BigQuery:', avgFluRate.toFixed(2));
                
                updateDiseaseCard('flu', {
                    positivity: avgFluRate,
                    name: 'Influenza',
                    color: 'amber',
                    trend: calculateTrend(fluRates, 'rate')
                });
            } else {
                console.log('[DISEASE CARDS] No Flu data available - showing 0');
                updateDiseaseCard('flu', { 
                    positivity: 0, 
                    name: 'Influenza', 
                    color: 'amber', 
                    trend: 'stable' 
                });
            }
            
            console.log('[DISEASE CARDS] Γ£ô All cards updated with BigQuery data');
            
        } else {
            console.error('[DISEASE CARDS] Γ£ù BigQuery data fetch failed:', result.error);
        }
        
    } catch (error) {
        console.error('[DISEASE CARDS] Γ£ùΓ£ùΓ£ù ERROR Γ£ùΓ£ùΓ£ù');
        console.error('[DISEASE CARDS] Error:', error);
        console.error('[DISEASE CARDS] Stack:', error.stack);
        
        // Show error state
        ['covid', 'flu', 'rsv'].forEach(disease => {
            document.getElementById(`${disease}Cases`).textContent = 'Error';
        });
    }
}

// Helper function to calculate trend
function calculateTrend(data, field) {
    if (!data || data.length < 2) return 'stable';
    
    // Sort by date
    const sorted = data.sort((a, b) => new Date(a.date) - new Date(b.date));
    const recent = sorted.slice(-7);  // Last 7 data points
    const older = sorted.slice(-14, -7);  // Previous 7 data points
    
    if (recent.length === 0 || older.length === 0) return 'stable';
    
    const recentAvg = recent.reduce((sum, d) => sum + (d[field] || 0), 0) / recent.length;
    const olderAvg = older.reduce((sum, d) => sum + (d[field] || 0), 0) / older.length;
    
    const change = ((recentAvg - olderAvg) / (olderAvg || 1)) * 100;
    
    if (change > 10) return 'increasing';
    if (change < -10) return 'decreasing';
    return 'stable';
}

/**
 * Update individual disease card
 */
function updateDiseaseCard(disease, data) {
    console.log('[DISEASE CARD]', disease, 'update with:', data);
    const { positivity, name, color } = data;
    
    // Update cases/positivity
    const casesEl = document.getElementById(`${disease}Cases`);
    if (casesEl) {
        casesEl.textContent = `${positivity.toFixed(1)}%`;
    }
    
    // Update progress bar
    const progressEl = document.getElementById(`${disease}Progress`);
    if (progressEl) {
        // Scale positivity to 0-100 for progress bar (assume max 20% is 100%)
        const progressPercent = Math.min((positivity / 20) * 100, 100);
        progressEl.style.width = `${progressPercent}%`;
    }
    
    // Determine risk level and trend
    let riskLevel, riskClass, trendIcon, trendText;
    
    if (positivity < 3) {
        riskLevel = 'Low Risk';
        riskClass = `bg-${color}-100 text-${color}-700`;
        trendIcon = '<i class="fas fa-arrow-down"></i>';
        trendText = 'Below threshold';
    } else if (positivity < 7) {
        riskLevel = 'Moderate';
        riskClass = `bg-amber-100 text-amber-700`;
        trendIcon = '<i class="fas fa-minus"></i>';
        trendText = 'Stable';
    } else {
        riskLevel = 'High';
        riskClass = `bg-red-100 text-red-700`;
        trendIcon = '<i class="fas fa-arrow-up"></i>';
        trendText = 'Elevated levels';
    }
    
    // Update risk badge
    const badgeEl = document.getElementById(`${disease}RiskBadge`);
    if (badgeEl) {
        badgeEl.textContent = riskLevel;
        badgeEl.className = `px-3 py-1 rounded-full text-sm font-semibold ${riskClass}`;
    }
    
    // Update trend
    const trendEl = document.getElementById(`${disease}Trend`);
    if (trendEl) {
        trendEl.innerHTML = `${trendIcon} ${trendText}`;
    }
}

// Make function globally available
window.updateDiseaseCards = updateDiseaseCards;
