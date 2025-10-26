/**
 * Multi-Pollutant Interactive Charts with Animations
 * Displays PM2.5, PM10, O3, CO, SO2, NO2 with beautiful animations
 */

// Chart instances
const pollutantCharts = {};

// EPA Parameter codes and info
const POLLUTANTS = {
    'PM2.5': {
        name: 'PM2.5',
        fullName: 'Fine Particulate Matter',
        unit: 'μg/m³',
        color: '#3b82f6',
        icon: '🌫️',
        description: 'Fine particles smaller than 2.5 micrometers'
    },
    'PM10': {
        name: 'PM10',
        fullName: 'Particulate Matter',
        unit: 'μg/m³',
        color: '#8b5cf6',
        icon: '💨',
        description: 'Particles smaller than 10 micrometers'
    },
    'OZONE': {
        name: 'O₃',
        fullName: 'Ozone',
        unit: 'ppb',
        color: '#06b6d4',
        icon: '☀️',
        description: 'Ground-level ozone'
    },
    'CO': {
        name: 'CO',
        fullName: 'Carbon Monoxide',
        unit: 'ppm',
        color: '#f59e0b',
        icon: '🏭',
        description: 'Colorless, odorless gas'
    },
    'SO2': {
        name: 'SO₂',
        fullName: 'Sulfur Dioxide',
        unit: 'ppb',
        color: '#ef4444',
        icon: '🌋',
        description: 'Gas produced by burning fossil fuels'
    },
    'NO2': {
        name: 'NO₂',
        fullName: 'Nitrogen Dioxide',
        unit: 'ppb',
        color: '#ec4899',
        icon: '🚗',
        description: 'Reddish-brown gas from combustion'
    }
};

/**
 * Generate mock data for testing
 */
function generateMockData(days = 7) {
    const dates = [];
    const values = [];
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
        values.push(Math.random() * 50 + 10); // Random value between 10-60
    }
    return { dates, values };
}

/**
 * Initialize all pollutant charts
 */
async function initializePollutantCharts(zipCode, city, state) {
    try {
        console.log('[Pollutant Charts] Initializing for:', zipCode, city, state);
        
        // Clear existing dashboard first
        const existingDashboard = document.getElementById('pollutant-dashboard');
        if (existingDashboard) {
            console.log('[Pollutant Charts] Clearing existing dashboard');
            existingDashboard.remove();
        }
        
        // Destroy existing chart instances
        Object.keys(pollutantCharts).forEach(key => {
            if (pollutantCharts[key]) {
                pollutantCharts[key].destroy();
                delete pollutantCharts[key];
            }
        });
        
        // If no location provided, show empty charts immediately
        if (!zipCode && !city) {
            console.log('[Pollutant Charts] No location - showing empty charts');
            createDashboardContainer();
            let chartsCreated = 0;
            Object.keys(POLLUTANTS).forEach(pollutant => {
                const emptyData = {
                    values: [],
                    dates: [],
                    current: 0,
                    min: 0,
                    max: 0,
                    avg: 0,
                    unit: POLLUTANTS[pollutant].unit
                };
                createPollutantChart(pollutant, emptyData, false);
                chartsCreated++;
            });
            console.log(`[Pollutant Charts] Created ${chartsCreated} empty charts (no location)`);
            if (chartsCreated > 0) {
                addChartControls();
            }
            return;
        }
        
        // Fetch data for all parameters
        const data = await fetchPollutantData(zipCode, city, state);
        
        console.log('[Pollutant Charts] Received data:', data);
        
        // ALWAYS create dashboard, even if API fails
        createDashboardContainer();
        
        if (!data || !data.success) {
            console.error('[Pollutant Charts] Failed to fetch data:', data?.error || 'Unknown error');
            console.log('[Pollutant Charts] Creating empty charts - API failure');
            
            // Create dashboard with empty charts
            let chartsCreated = 0;
            Object.keys(POLLUTANTS).forEach(pollutant => {
                const emptyData = {
                    values: [],
                    dates: [],
                    current: 0,
                    min: 0,
                    max: 0,
                    avg: 0,
                    unit: POLLUTANTS[pollutant].unit
                };
                createPollutantChart(pollutant, emptyData, false);
                chartsCreated++;
            });
            console.log(`[Pollutant Charts] Created ${chartsCreated} empty charts`);
            if (chartsCreated > 0) {
                addChartControls();
            }
            return;
        }
        
        if (!data.parameters) {
            console.error('[Pollutant Charts] No parameters in response');
            return;
        }
        
        // DEBUG: Log what parameters we actually received
        console.log('[Pollutant Charts] Parameters object:', data.parameters);
        console.log('[Pollutant Charts] Parameter keys:', Object.keys(data.parameters));
        
        // Create dashboard container
        createDashboardContainer();
        
        // Create charts for each pollutant
        let chartsCreated = 0;
        Object.keys(POLLUTANTS).forEach(pollutant => {
            const paramData = data.parameters[pollutant];
            console.log(`[Pollutant Charts] Looking for ${pollutant}, found:`, paramData);
            
            // Check if we have real data
            const hasRealData = paramData && paramData.values && paramData.values.length > 0;
            
            if (hasRealData) {
                console.log(`[Pollutant Charts] Creating chart for ${pollutant}:`, paramData);
                createPollutantChart(pollutant, paramData, true); // true = real data
                chartsCreated++;
            } else {
                // Create empty chart - NO mock data
                console.log(`[Pollutant Charts] No data for ${pollutant}, creating empty chart`);
                const emptyData = {
                    values: [],
                    dates: [],
                    current: 0,
                    min: 0,
                    max: 0,
                    avg: 0,
                    unit: POLLUTANTS[pollutant].unit
                };
                createPollutantChart(pollutant, emptyData, false); // false = no real data
                chartsCreated++;
            }
        });
        
        console.log(`[Pollutant Charts] Created ${chartsCreated} charts`);
        
        // Add chart controls
        if (chartsCreated > 0) {
            addChartControls();
        }
        
    } catch (error) {
        console.error('[Pollutant Charts] Error initializing:', error);
    }
}

/**
 * Fetch data for all pollutants
 */
async function fetchPollutantData(zipCode, city, state) {
    const params = new URLSearchParams();
    if (zipCode) params.append('zipCode', zipCode);
    else if (city && state) {
        params.append('city', city);
        params.append('state', state);
    }
    
    // Get date range from date picker inputs
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && startDateInput.value) {
        params.append('startDate', startDateInput.value);
    }
    if (endDateInput && endDateInput.value) {
        params.append('endDate', endDateInput.value);
    }
    
    // If no dates specified, default to 7 days
    if (!startDateInput?.value && !endDateInput?.value) {
        params.append('days', 7);
    }
    
    params.append('detailed', 'true'); // Request parameter-specific data
    
    const url = `/api/air-quality-detailed?${params.toString()}`;
    console.log('[Pollutant Charts] Fetching from:', url);
    
    const response = await fetch(url);
    const data = await response.json();
    
    console.log('[Pollutant Charts] Response:', data);
    
    return data;
}

/**
 * Create dashboard container for charts
 */
function createDashboardContainer() {
    console.log('[Dashboard] Creating dashboard container...');
    
    // Check if dashboard already exists
    let dashboard = document.getElementById('pollutant-dashboard');
    if (!dashboard) {
        console.log('[Dashboard] Dashboard does not exist, creating new one');
        dashboard = document.createElement('div');
        dashboard.id = 'pollutant-dashboard';
        dashboard.className = 'w-full max-w-7xl mx-auto px-4 mt-12 mb-12';
        
        // Find the weather/pollen grid and insert after it
        const weatherPollenGrid = document.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2');
        console.log('[Dashboard] Weather/pollen grid found:', !!weatherPollenGrid);
        
        if (weatherPollenGrid && weatherPollenGrid.parentElement) {
            // Insert after the grid's parent or the grid itself
            const insertTarget = weatherPollenGrid.closest('.mt-8') || weatherPollenGrid;
            insertTarget.insertAdjacentElement('afterend', dashboard);
            console.log('[Dashboard] Inserted after weather/pollen grid');
        } else {
            // Fallback: find the main content area
            const mainContent = document.querySelector('main') || document.querySelector('.relative.z-10');
            console.log('[Dashboard] Main content found:', !!mainContent);
            if (mainContent) {
                mainContent.appendChild(dashboard);
                console.log('[Dashboard] Appended to main content');
            } else {
                document.body.appendChild(dashboard);
                console.log('[Dashboard] Appended to body (fallback)');
            }
        }
    } else {
        console.log('[Dashboard] Dashboard already exists');
    }
    
    dashboard.innerHTML = `
        <div class="mb-8">
            <h2 class="text-4xl font-bold text-gray-800 mb-3">
                <span class="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    📊 Air Quality Parameters
                </span>
            </h2>
            <p class="text-gray-600 text-lg">Detailed pollutant levels and trends over time</p>
        </div>
        <div id="pollutant-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"></div>
    `;
    
    console.log('[Dashboard] Dashboard HTML set');
    console.log('[Dashboard] Dashboard element:', dashboard);
    console.log('[Dashboard] Dashboard in DOM:', document.getElementById('pollutant-dashboard'));
}

/**
 * Create individual pollutant chart
 */
function createPollutantChart(pollutantKey, data, isRealData = false) {
    console.log(`[Chart] Creating chart for ${pollutantKey}...`);
    
    const pollutant = POLLUTANTS[pollutantKey];
    if (!pollutant) {
        console.error(`[Chart] Pollutant ${pollutantKey} not found in POLLUTANTS`);
        return;
    }
    
    const grid = document.getElementById('pollutant-grid');
    console.log(`[Chart] Grid element:`, grid);
    
    if (!grid) {
        console.error('[Chart] pollutant-grid element not found!');
        return;
    }
    
    // Create chart card with proper sizing
    const card = document.createElement('div');
    card.className = 'pollutant-card bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-2xl transform hover:-translate-y-1';
    card.style.border = `2px solid ${pollutant.color}20`;
    card.style.minHeight = '400px';
    
    const chartId = `chart-${pollutantKey.toLowerCase()}`;
    
    // Add data source badge
    const dataBadge = isRealData 
        ? '<span class="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">📡 Real-time EPA Data</span>'
        : '<span class="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800">📊 Estimated Data</span>';
    
    card.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                    <span class="text-4xl">${pollutant.icon}</span>
                    <h3 class="text-2xl font-bold text-gray-800">${pollutant.name}</h3>
                </div>
                <p class="text-sm text-gray-600">${pollutant.description}</p>
                <div class="mt-2">${dataBadge}</div>
            </div>
            <div class="text-right ml-4">
                <div class="text-4xl font-bold" style="color: ${pollutant.color}">
                    ${Math.round(data.current || 0)}
                </div>
                <div class="text-xs text-gray-500 mt-1">${pollutant.unit}</div>
            </div>
        </div>
        
        <div class="relative mb-6" style="height: 200px;">
            <canvas id="${chartId}"></canvas>
        </div>
        
        <div class="grid grid-cols-3 gap-3">
            <div class="p-3 bg-gray-50 rounded-lg text-center">
                <div class="text-xs text-gray-500 mb-1">Min</div>
                <div class="text-lg font-semibold" style="color: ${pollutant.color}">${Math.round(data.min || 0)}</div>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg text-center">
                <div class="text-xs text-gray-500 mb-1">Avg</div>
                <div class="text-lg font-semibold" style="color: ${pollutant.color}">${Math.round(data.avg || 0)}</div>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg text-center">
                <div class="text-xs text-gray-500 mb-1">Max</div>
                <div class="text-lg font-semibold" style="color: ${pollutant.color}">${Math.round(data.max || 0)}</div>
            </div>
        </div>
    `;
    
    grid.appendChild(card);
    
    console.log(`[Chart] Card appended for ${pollutantKey}`);
    console.log(`[Chart] Card visible?`, card.offsetHeight > 0);
    console.log(`[Chart] Grid children count:`, grid.children.length);
    
    // Create Chart.js chart with animations
    setTimeout(() => {
        const ctx = document.getElementById(chartId);
        if (!ctx) return;
        
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, `${pollutant.color}40`);
        gradient.addColorStop(1, `${pollutant.color}00`);
        
        pollutantCharts[pollutantKey] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates || [],
                datasets: [{
                    label: pollutant.fullName,
                    data: data.values || [],
                    borderColor: pollutant.color,
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 8,
                    pointBackgroundColor: pollutant.color,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart',
                    from: 0,
                    loop: false
                },
                plugins: {
                    legend: {
                        display: false
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
                            label: (context) => {
                                return `${context.parsed.y.toFixed(1)} ${pollutant.unit}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 10
                            },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 5
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 10
                            },
                            callback: (value) => Math.round(value)
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
        
        // Add entrance animation
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        requestAnimationFrame(() => {
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
        
    }, 100);
}

/**
 * Add controls for chart interactions
 */
function addChartControls() {
    const dashboard = document.getElementById('pollutant-dashboard');
    if (!dashboard) return;
    
    const controls = document.createElement('div');
    controls.className = 'mt-8 flex justify-center gap-4 flex-wrap';
    controls.innerHTML = `
        <button class="chart-control-btn active" data-days="7">
            7 Days
        </button>
        <button class="chart-control-btn" data-days="14">
            14 Days
        </button>
        <button class="chart-control-btn" data-days="30">
            30 Days
        </button>
        <button class="chart-control-btn" data-export="true">
            📊 Export Data
        </button>
    `;
    
    dashboard.appendChild(controls);
    
    // Add event listeners
    controls.querySelectorAll('.chart-control-btn').forEach(btn => {
        btn.addEventListener('click', handleControlClick);
    });
}

/**
 * Handle control button clicks
 */
function handleControlClick(e) {
    const btn = e.currentTarget;
    
    if (btn.dataset.export) {
        exportChartData();
        return;
    }
    
    // Update active state
    document.querySelectorAll('.chart-control-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    // Reload charts with new timeframe
    const days = btn.dataset.days;
    const zipCode = currentZip;
    const city = currentCity;
    const state = currentState;
    
    initializePollutantCharts(zipCode, city, state);
}

/**
 * Export chart data as CSV
 */
function exportChartData() {
    // Create CSV content
    let csv = 'Pollutant,Date,Value,Unit\n';
    
    Object.keys(pollutantCharts).forEach(pollutantKey => {
        const chart = pollutantCharts[pollutantKey];
        const pollutant = POLLUTANTS[pollutantKey];
        
        chart.data.labels.forEach((label, index) => {
            const value = chart.data.datasets[0].data[index];
            csv += `${pollutant.fullName},${label},${value},${pollutant.unit}\n`;
        });
    });
    
    // Download CSV
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `air-quality-data-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Add CSS styles
const style = document.createElement('style');
style.textContent = `
    .pollutant-dashboard {
        animation: fadeInUp 0.6s ease;
    }
    
    .pollutant-card {
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    
    .chart-control-btn {
        padding: 0.75rem 1.5rem;
        border-radius: 9999px;
        background: white;
        border: 2px solid #e5e7eb;
        color: #6b7280;
        font-weight: 600;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .chart-control-btn:hover {
        border-color: #3b82f6;
        color: #3b82f6;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    
    .chart-control-btn.active {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        border-color: transparent;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);
