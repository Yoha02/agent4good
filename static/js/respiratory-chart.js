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
                        Weekly Percent of Tests Positive for Respiratory Viruses Reported to NREVSS
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
                
                <div class="date-slider-wrapper bg-white rounded-xl shadow-lg p-6">
                    <div class="flex items-center gap-4">
                        <label class="text-sm font-semibold text-gray-700 whitespace-nowrap">
                            <i class="fas fa-sliders-h mr-2"></i>Date Range:
                        </label>
                        <input type="range" id="dateSlider" class="flex-1" min="0" max="100" value="0">
                        <div class="text-sm font-mono text-gray-600">
                            <span id="sliderStartDate">-</span> to <span id="sliderEndDate">-</span>
                        </div>
                        <button id="resetSlider" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition text-sm">
                            <i class="fas fa-undo mr-1"></i>Reset to 3 Months
                        </button>
                    </div>
                </div>
                
                <div class="chart-legend mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
                    <!-- Legend will be populated dynamically -->
                </div>
                
                <div class="chart-footer mt-4 text-xs text-gray-500">
                    <p>
                        <i class="fas fa-info-circle mr-1"></i>
                        Source: CDC NREVSS (National Respiratory and Enteric Virus Surveillance System)
                        • Updated weekly • Showing RSV test positivity rates
                    </p>
                </div>
            </div>
        `;
    }
    
    async loadData(state = '') {
        console.log('[RESPIRATORY CHART] Loading data for state:', state || 'National');
        
        try {
            const url = state 
                ? `/api/respiratory-timeseries?state=${encodeURIComponent(state)}&limit=500`
                : '/api/respiratory-timeseries?limit=500';
            
            const response = await fetch(url);
            const result = await response.json();
            
            // DEBUG: Log the actual data structure
            console.log('[RESPIRATORY CHART] First raw data item from API:', JSON.stringify(result.data && result.data[0], null, 2));
            
            if (result.status === 'success' && result.data && result.data.length > 0) {
                this.data = result.data;
                console.log('[RESPIRATORY CHART] Loaded', this.data.length, 'raw data points');
                // Normalize dates to ISO and drop malformed entries
                this.normalizeDataDates();
                console.log('[RESPIRATORY CHART] Using', this.data.length, 'normalized data points');
                
                // Update location indicator
                const locationEl = document.getElementById('chartLocationIndicator');
                if (locationEl) {
                    locationEl.textContent = state || 'National';
                }
                
                // Set default to last 3 months
                this.setDefaultDateRange();
                this.initializeSlider();
                this.renderChart();
            } else {
                console.warn('[RESPIRATORY CHART] No data available:', result);
                this.showNoDataMessage();
            }
        } catch (error) {
            console.error('[RESPIRATORY CHART] Error loading data:', error);
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
        const slider = document.getElementById('dateSlider');
        const resetBtn = document.getElementById('resetSlider');
        
        if (!slider || this.data.length === 0) return;
        
        // Get all unique dates sorted
        const allDates = [...new Set(this.data.map(d => d.date))].sort();
        
        slider.min = 0;
        slider.max = allDates.length - 1;
        
        // Set slider to show last 3 months by default
        const endIndex = allDates.length - 1;
        const threeMonthsAgo = new Date(allDates[endIndex]);
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        
        const startIndex = allDates.findIndex(d => new Date(d) >= threeMonthsAgo);
        slider.value = startIndex >= 0 ? startIndex : 0;
        
        // Update date labels
        this.updateSliderLabels(allDates[slider.value], allDates[endIndex]);
        
        // Slider event
        slider.addEventListener('input', (e) => {
            const startIdx = parseInt(e.target.value);
            const endIdx = allDates.length - 1;
            
            this.dateRange.start = new Date(allDates[startIdx]);
            this.dateRange.end = new Date(allDates[endIdx]);
            
            this.updateSliderLabels(allDates[startIdx], allDates[endIdx]);
            this.filterDataByDateRange();
            this.renderChart();
        });
        
        // Reset button
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                slider.value = startIndex >= 0 ? startIndex : 0;
                this.setDefaultDateRange();
                this.updateSliderLabels(allDates[startIndex], allDates[endIndex]);
                this.renderChart();
            });
        }
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
        
        // Create datasets for each test type
        const datasets = testTypes.map(testType => {
            const data = dates.map(date => dataByDate[date][testType] || null);
            
            return {
                label: testType === 'Antigen' ? 'RSV (Antigen)' : 'RSV (PCR)',
                data: data,
                borderColor: this.colors.RSV || '#7b68ee',
                backgroundColor: (this.colors.RSV || '#7b68ee') + '20',
                borderWidth: 2,
                tension: 0.4,
                fill: false,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: this.colors.RSV || '#7b68ee',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
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
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
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
                            text: 'Weekly Percent Positive',
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
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
    console.log('[DISEASE CARDS] ========== UPDATING CARDS ==========');
    console.log('[DISEASE CARDS] Days:', days);
    
    currentDiseasePeriod = days;
    
    // Update button styles
    document.querySelectorAll('.disease-period-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-500', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    event?.target.classList.remove('bg-gray-200', 'text-gray-700');
    event?.target.classList.add('active', 'bg-blue-500', 'text-white');
    
    // Get current state
    const state = currentState || '';
    const locationText = state || 'National';
    console.log('[DISEASE CARDS] State:', state, 'Location text:', locationText);
    
    // Update location indicator
    const locationEl = document.getElementById('diseaseCardsLocation');
    if (locationEl) {
        locationEl.innerHTML = `<i class="fas fa-map-marker-alt mr-1"></i>${locationText}`;
        console.log('[DISEASE CARDS] Updated location indicator');
    }
    
    try {
        // Fetch respiratory data for the time period
        const url = state 
            ? `/api/respiratory-timeseries?state=${encodeURIComponent(state)}&limit=${days * 2}`
            : `/api/respiratory-timeseries?limit=${days * 2}`;
        
        console.log('[DISEASE CARDS] Fetching:', url);
        const response = await fetch(url);
        console.log('[DISEASE CARDS] Response status:', response.status);
        const result = await response.json();
        console.log('[DISEASE CARDS] API Result:', result);
        
        if (result.status === 'success' && result.data && result.data.length > 0) {
            console.log('[DISEASE CARDS] ✓ Got', result.data.length, 'data points');
            // Group by disease type and calculate averages
            const rsvData = result.data.filter(d => d.testtype);
            console.log('[DISEASE CARDS] RSV data points:', rsvData.length);
            
            if (rsvData.length > 0) {
                // Calculate average positivity rate for RSV
                const rsvPositivity = rsvData.slice(0, days).reduce((sum, d) => sum + (d.positivity_rate || 0), 0) / Math.min(days, rsvData.length);
                console.log('[DISEASE CARDS] RSV positivity:', rsvPositivity);
                
                // Update RSV card
                updateDiseaseCard('rsv', {
                    positivity: rsvPositivity,
                    name: 'RSV',
                    color: 'blue'
                });
            }
        } else {
            console.error('[DISEASE CARDS] ✗ No data in API response');
        }
        
        // Update COVID and Flu with placeholder data (until we have real data sources)
        updateDiseaseCard('covid', {
            positivity: 2.3,
            name: 'COVID-19',
            color: 'emerald'
        });
        
        updateDiseaseCard('flu', {
            positivity: 5.8,
            name: 'Influenza',
            color: 'amber'
        });
        
    } catch (error) {
        console.error('[DISEASE CARDS] ✗✗✗ ERROR ✗✗✗');
        console.error('[DISEASE CARDS] Error:', error);
        console.error('[DISEASE CARDS] Stack:', error.stack);
        
        // Show error state
        ['covid', 'flu', 'rsv'].forEach(disease => {
            document.getElementById(`${disease}Cases`).textContent = 'Error';
            document.getElementById(`${disease}Trend`).innerHTML = '<i class="fas fa-exclamation-circle mr-1"></i>Unable to load data';
            document.getElementById(`${disease}RiskBadge`).textContent = 'Unknown';
        });
    }
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
        trendIcon = '↓';
        trendText = 'Below threshold';
    } else if (positivity < 7) {
        riskLevel = 'Moderate';
        riskClass = `bg-amber-100 text-amber-700`;
        trendIcon = '→';
        trendText = 'Stable';
    } else {
        riskLevel = 'High';
        riskClass = `bg-red-100 text-red-700`;
        trendIcon = '↑';
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
