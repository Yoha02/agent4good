/**
 * Respiratory Disease Rates Chart
 * Interactive visualization for RSV, COVID-19, and Influenza rates
 * Data source: CDC Rates of Laboratory-Confirmed Respiratory Diseases
 */

class RespiratoryDiseaseRatesChart {
    constructor(containerId) {
        this.containerId = containerId;
        this.chart = null;
        this.data = [];
        this.filteredData = [];
        this.dateRange = { start: null, end: null };
        this.selectedDiseases = ['RSV', 'COVID-19', 'Influenza'];
        
        // Chart colors
        this.colors = {
            'RSV': '#7b68ee',           // Purple
            'COVID-19': '#dc2626',      // Red
            'Influenza': '#2563eb'      // Blue
        };
        
        this.init();
    }

    init() {
        console.log('[RESPIRATORY RATES CHART] Initializing...');
        this.createChartContainer();
    }
    
    createChartContainer() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('[RESPIRATORY RATES CHART] Container not found:', this.containerId);
            return;
        }
        
        container.innerHTML = `
            <div class="respiratory-rates-chart-wrapper">
                <div class="chart-header mb-6">
                    <h3 class="text-2xl font-bold text-navy-700 mb-2">
                        Rates of Laboratory-Confirmed Respiratory Diseases
                    </h3>
                    <div class="flex items-center gap-4 text-sm text-gray-600">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-map-marker-alt text-blue-500"></i>
                            <span id="ratesChartLocationIndicator">United States</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <i class="fas fa-calendar text-blue-500"></i>
                            <span id="ratesChartDateRange">Loading...</span>
                        </div>
                    </div>
                </div>
                
                <div class="disease-filter-wrapper bg-white rounded-xl shadow-lg p-4 mb-4">
                    <div class="flex items-center gap-4 flex-wrap">
                        <label class="text-sm font-semibold text-gray-700">Filter Diseases:</label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" class="disease-checkbox" data-disease="RSV" checked>
                            <span class="text-sm" style="color: #7b68ee">RSV</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" class="disease-checkbox" data-disease="COVID-19" checked>
                            <span class="text-sm" style="color: #dc2626">COVID-19</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" class="disease-checkbox" data-disease="Influenza" checked>
                            <span class="text-sm" style="color: #2563eb">Influenza</span>
                        </label>
                    </div>
                </div>
                
                <div class="chart-canvas-wrapper bg-white rounded-xl shadow-lg p-6 mb-4">
                    <canvas id="respiratoryRatesCanvas" height="400"></canvas>
                </div>
                
                <div class="date-slider-wrapper bg-white rounded-xl shadow-lg p-6">
                    <div class="flex items-center gap-4">
                        <label class="text-sm font-semibold text-gray-700 whitespace-nowrap">
                            <i class="fas fa-sliders-h mr-2"></i>Date Range:
                        </label>
                        <input type="range" id="ratesDateSlider" class="flex-1" min="0" max="100" value="0">
                        <div class="text-sm font-mono text-gray-600">
                            <span id="ratesSliderStartDate">-</span> to <span id="ratesSliderEndDate">-</span>
                        </div>
                        <button id="ratesResetSlider" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition text-sm">
                            <i class="fas fa-undo mr-1"></i>Reset to 6 Months
                        </button>
                    </div>
                </div>
                
                <div class="chart-footer mt-4 text-xs text-gray-500">
                    <p>
                        <i class="fas fa-info-circle mr-1"></i>
                        Source: CDC Rates of Laboratory-Confirmed RSV, COVID-19, and Flu
                        • Updated weekly • Rates per 100,000 population
                    </p>
                </div>
            </div>
        `;
        
        // Add event listeners for disease checkboxes
        document.querySelectorAll('.disease-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const disease = e.target.dataset.disease;
                if (e.target.checked) {
                    if (!this.selectedDiseases.includes(disease)) {
                        this.selectedDiseases.push(disease);
                    }
                } else {
                    this.selectedDiseases = this.selectedDiseases.filter(d => d !== disease);
                }
                this.renderChart();
            });
        });
    }
    
    async loadData(geography = 'United States') {
        console.log('[RESPIRATORY RATES CHART] Loading data for geography:', geography);
        
        try {
            const url = `/api/respiratory-disease-rates?geography=${encodeURIComponent(geography)}&limit=52`;
            
            const response = await fetch(url);
            const result = await response.json();
            
            console.log('[RESPIRATORY RATES CHART] API result:', result.status);
            
            if (result.status === 'success' && result.data && result.data.length > 0) {
                // Filter to only "Overall" age category for simplicity
                this.data = result.data.filter(d => 
                    d.age_category === 'Overall' && d.date && d.disease
                );
                
                console.log('[RESPIRATORY RATES CHART] Loaded', this.data.length, 'data points');
                
                // Update location indicator
                const locationEl = document.getElementById('ratesChartLocationIndicator');
                if (locationEl) {
                    locationEl.textContent = geography;
                }
                
                // Set default to last 6 months
                this.setDefaultDateRange();
                this.initializeSlider();
                this.renderChart();
            } else {
                console.warn('[RESPIRATORY RATES CHART] No data available:', result);
                this.showNoDataMessage();
            }
        } catch (error) {
            console.error('[RESPIRATORY RATES CHART] Error loading data:', error);
            this.showErrorMessage(error.message);
        }
    }
    
    setDefaultDateRange() {
        if (this.data.length === 0) {
            console.error('[RESPIRATORY RATES CHART] Cannot set date range - no data!');
            return;
        }
        
        // Get the most recent date
        const dates = this.data.map(d => new Date(d.date)).sort((a, b) => b - a);
        const latestDate = dates[0];
        
        // Calculate 6 months ago
        const sixMonthsAgo = new Date(latestDate);
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
        
        this.dateRange.end = latestDate;
        this.dateRange.start = sixMonthsAgo;
        
        console.log('[RESPIRATORY RATES CHART] Date range set:', 
            this.dateRange.start.toLocaleDateString(), 'to', 
            this.dateRange.end.toLocaleDateString());
        
        this.filterDataByDateRange();
    }
    
    initializeSlider() {
        const slider = document.getElementById('ratesDateSlider');
        const resetBtn = document.getElementById('ratesResetSlider');
        
        if (!slider || this.data.length === 0) return;
        
        // Get all unique dates sorted
        const allDates = [...new Set(this.data.map(d => d.date))].sort();
        
        slider.min = 0;
        slider.max = allDates.length - 1;
        
        // Set slider to show last 6 months by default
        const endIndex = allDates.length - 1;
        const sixMonthsAgo = new Date(allDates[endIndex]);
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
        
        const startIndex = allDates.findIndex(d => new Date(d) >= sixMonthsAgo);
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
        const startEl = document.getElementById('ratesSliderStartDate');
        const endEl = document.getElementById('ratesSliderEndDate');
        
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
        
        console.log('[RESPIRATORY RATES CHART] Filtered to', this.filteredData.length, 'points');
    }
    
    renderChart() {
        const canvas = document.getElementById('respiratoryRatesCanvas');
        if (!canvas) {
            console.error('[RESPIRATORY RATES CHART] Canvas not found');
            return;
        }
        
        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }
        
        // Group data by date and disease
        const dataByDate = {};
        
        this.filteredData.forEach(item => {
            if (!this.selectedDiseases.includes(item.disease)) return;
            
            if (!dataByDate[item.date]) {
                dataByDate[item.date] = {};
            }
            dataByDate[item.date][item.disease] = item.rate;
        });
        
        // Get sorted dates
        const dates = Object.keys(dataByDate).sort();
        console.log('[RESPIRATORY RATES CHART] Unique dates for chart:', dates.length);
        
        // Create datasets for each disease
        const datasets = this.selectedDiseases.map(disease => {
            const data = dates.map(date => dataByDate[date][disease] || null);
            
            return {
                label: disease,
                data: data,
                borderColor: this.colors[disease] || '#7b68ee',
                backgroundColor: (this.colors[disease] || '#7b68ee') + '20',
                borderWidth: 3,
                tension: 0.4,
                fill: false,
                pointRadius: 4,
                pointHoverRadius: 7,
                pointBackgroundColor: this.colors[disease] || '#7b68ee',
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
                            padding: 20,
                            font: {
                                size: 13,
                                weight: 'bold',
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
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + ' per 100k';
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
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Rate per 100,000 Population',
                            font: {
                                size: 14,
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
        const dateRangeEl = document.getElementById('ratesChartDateRange');
        if (dateRangeEl && dates.length > 0) {
            const firstDate = new Date(dates[0]).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            const lastDate = new Date(dates[dates.length - 1]).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            dateRangeEl.textContent = `${firstDate} - ${lastDate}`;
        }
        
        console.log('[RESPIRATORY RATES CHART] Chart rendered with', dates.length, 'data points');
    }
    
    showNoDataMessage() {
        const canvas = document.getElementById('respiratoryRatesCanvas');
        if (canvas) {
            canvas.parentElement.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <i class="fas fa-chart-line text-5xl mb-4"></i>
                    <p class="text-lg">No respiratory disease rates data available</p>
                    <p class="text-sm mt-2">Try selecting a different location or date range</p>
                </div>
            `;
        }
    }
    
    showErrorMessage(message) {
        const canvas = document.getElementById('respiratoryRatesCanvas');
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
    
    updateLocation(geography) {
        console.log('[RESPIRATORY RATES CHART] Updating geography to:', geography);
        this.loadData(geography);
    }
}

// Initialize chart when DOM is ready
let respiratoryDiseaseRatesChart = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('[RESPIRATORY RATES CHART] DOM READY - Initializing');
    
    // Check if the container exists on this page
    const container = document.getElementById('respiratoryDiseaseRatesChartContainer');
    if (!container) {
        console.log('[RESPIRATORY RATES CHART] Container not found on this page, skipping initialization');
        return;
    }
    
    // Wait a bit for other scripts to initialize
    setTimeout(() => {
        console.log('[RESPIRATORY RATES CHART] Creating chart instance...');
        respiratoryDiseaseRatesChart = new RespiratoryDiseaseRatesChart('respiratoryDiseaseRatesChartContainer');
        console.log('[RESPIRATORY RATES CHART] Chart instance created');
        
        // Load initial data (national)
        respiratoryDiseaseRatesChart.loadData('United States');
    }, 500);
});

// Make globally available
window.respiratoryDiseaseRatesChart = respiratoryDiseaseRatesChart;
