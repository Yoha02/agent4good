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
        icon: '🏭',
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
async function initializePollutantCharts(zipCode, city, state, days = 7) {
    try {
        console.log('');
        console.log('ΓòöΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòù');
        console.log('Γòæ [PM2.5 POLLUTANT CHARTS] Starting initialization     Γòæ');
        console.log('ΓòáΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòú');
        console.log('Γòæ FUNCTION CALLED WITH:                                 Γòæ');
        console.log('Γòæ  - zipCode parameter:', zipCode || '(null/empty)');
        console.log('Γòæ  - city parameter:', city || '(null/empty)');
        console.log('Γòæ  - state parameter:', state || '(null/empty)');
        console.log('Γòæ  - days parameter:', days, 'days');
        console.log('ΓòÜΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓò¥');
        console.log('');
        
        // Show loading indicator for pollutant charts
        let loadingEl = document.getElementById('pollutant-loading');
        if (!loadingEl) {
            loadingEl = document.createElement('div');
            loadingEl.id = 'pollutant-loading';
            loadingEl.className = 'w-full text-center py-6';
            loadingEl.innerHTML = '<div class="inline-flex items-center gap-3"><div class="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-600"></div><div class="text-sm text-gray-600">Loading pollutant charts...</div></div>';
            
            // Insert into pollutant section if it exists, otherwise in body
            const pollutantSection = document.getElementById('pollutant-dashboard') || document.querySelector('#air-quality');
            if (pollutantSection) {
                pollutantSection.appendChild(loadingEl);
                console.log('[Pollutant Charts] Loading indicator added to pollutant section');
            } else {
                document.body.appendChild(loadingEl);
                console.log('[Pollutant Charts] Loading indicator added to body');
            }
        }
        loadingEl.style.display = 'block';
        console.log('[Pollutant Charts] Loading indicator shown');

        // Check if dashboard already exists
        let existingDashboard = document.getElementById('pollutant-dashboard');
        const isReload = existingDashboard !== null;
        
        if (isReload) {
            console.log('[Pollutant Charts] Reloading existing dashboard - preserving controls');
            // Only clear the chart grid, not the entire dashboard
            const chartGrid = document.getElementById('pollutant-grid');
            if (chartGrid) {
                chartGrid.innerHTML = '';
            }
        } else {
            console.log('[Pollutant Charts] Creating new dashboard');
            // Clear existing dashboard first
            if (existingDashboard) {
                existingDashboard.remove();
            }
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
            if (!isReload) createDashboardContainer();
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
            if (chartsCreated > 0 && !isReload) {
                addChartControls();
            }
            return;
        }
        
        // Fetch data for all parameters with the specified time period
    const data = await fetchPollutantData(zipCode, city, state, days);
        
        console.log('[Pollutant Charts] Received data:', data);
        
        // ALWAYS create dashboard, even if API fails (unless it's a reload)
        if (!isReload) createDashboardContainer();
        
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
            if (chartsCreated > 0 && !isReload) {
                addChartControls();
            }
            // Hide loading
            if (loadingEl) loadingEl.style.display = 'none';
            return;
        }
        
        if (!data.parameters) {
            console.error('[Pollutant Charts] No parameters in response');
            return;
        }
        
        // DEBUG: Log what parameters we actually received
        console.log('[Pollutant Charts] Parameters object:', data.parameters);
        console.log('[Pollutant Charts] Parameter keys:', Object.keys(data.parameters));
        
        // Create dashboard container (only if first time)
        if (!isReload) createDashboardContainer();
        
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
        
        // Add chart controls (only if first time)
        if (chartsCreated > 0 && !isReload) {
            addChartControls();
        }
            // Hide loading indicator
            if (loadingEl) loadingEl.style.display = 'none';
        
    } catch (error) {
        console.error('[Pollutant Charts] Error initializing:', error);
        
        // Hide loading indicator on error
        const loadingEl = document.getElementById('pollutant-loading');
        if (loadingEl) loadingEl.style.display = 'none';
        
        // Create empty dashboard so something shows (only if doesn't exist)
        const existingDashboard = document.getElementById('pollutant-dashboard');
        if (!existingDashboard) {
            createDashboardContainer();
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
            });
            addChartControls();
        }
    }
}

/**
 * Fetch data for all pollutants
 */
async function fetchPollutantData(zipCode, city, state, days = 1) {
    console.log('[Pollutant Charts] ≡ƒöä fetchPollutantData CALLED');
    console.log('[Pollutant Charts]   - zipCode:', zipCode);
    console.log('[Pollutant Charts]   - city:', city);
    console.log('[Pollutant Charts]   - state:', state);
    console.log('[Pollutant Charts]   - days:', days);
    
    const params = new URLSearchParams();
    if (zipCode) params.append('zipCode', zipCode);
    else if (city && state) {
        params.append('city', city);
        params.append('state', state);
    }

    // Use the days parameter for time range (reduced to 1 day to prevent timeout)
    params.append('days', days);
    params.append('detailed', 'true'); // Request parameter-specific data

    const url = `/api/air-quality-detailed?${params.toString()}`;
    console.log(`[Pollutant Charts] ≡ƒôí Fetching from: ${url}`);

    // Use AbortController to implement a fetch timeout so UI doesn't hang
    const controller = new AbortController();
    const timeoutMs = 15000; // 15s timeout (increased from 10s)
    const timeoutId = setTimeout(() => {
        console.log('[Pollutant Charts] ΓÅ▒∩╕Å Timeout reached, aborting fetch');
        controller.abort();
    }, timeoutMs);

    try {
        console.log('[Pollutant Charts] ≡ƒîÉ Starting fetch...');
        const response = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        console.log('[Pollutant Charts] Γ£à Fetch completed, status:', response.status);

        if (!response.ok) {
            console.error('[Pollutant Charts] Γ¥î Fetch failed, status:', response.status);
            return { success: false, error: `HTTP ${response.status}` };
        }

        const data = await response.json();
        console.log('[Pollutant Charts] ≡ƒôª Response data received:', data);
        return data;
    } catch (err) {
        clearTimeout(timeoutId);
        if (err.name === 'AbortError') {
            console.error('[Pollutant Charts] ΓÅ╣∩╕Å Fetch aborted due to timeout');
            return { success: false, error: 'Request timed out' };
        }
        console.error('[Pollutant Charts] Γ¥î Fetch error:', err);
        return { success: false, error: err.message || String(err) };
    }
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
        <div class="mb-8 text-center">
            <h2 class="text-4xl font-bold text-gray-800 mb-3">
                <span class="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    <i class="fas fa-chart-bar mr-2"></i> Air Quality Parameters
                </span>
            </h2>
            <p class="text-gray-600 text-lg">Detailed pollutant levels and trends over time</p>
        </div>
        
        <!-- Time Period Controls at the Top -->
        <div id="pollutant-controls" class="mb-6 flex justify-center gap-4 flex-wrap">
            <button class="chart-control-btn active px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-all duration-300 transform hover:scale-105" data-days="7">
                <i class="fas fa-calendar-week mr-2"></i> Last 7 Days
            </button>
            <button class="chart-control-btn px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-all duration-300 transform hover:scale-105" data-days="14">
                <i class="fas fa-calendar-alt mr-2"></i> Last 14 Days
            </button>
            <button class="chart-control-btn px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-all duration-300 transform hover:scale-105" data-days="30">
                <i class="fas fa-calendar mr-2"></i> Last 30 Days
            </button>
            <button class="chart-control-btn px-6 py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-all duration-300 transform hover:scale-105" data-export="true">
                <i class="fas fa-download mr-2"></i> Export Data
            </button>
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
        ? '<span class="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800"><i class="fas fa-check-circle mr-1"></i> Real-time EPA Data</span>'
        : '<span class="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800"><i class="fas fa-chart-line mr-1"></i> Estimated Data</span>';
    
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
    const controlsContainer = document.getElementById('pollutant-controls');
    if (!controlsContainer) {
        console.error('[Chart Controls] Controls container not found');
        return;
    }
    
    console.log('[Chart Controls] Attaching event listeners to time period buttons');
    
    // Add event listeners to the existing buttons
    controlsContainer.querySelectorAll('.chart-control-btn').forEach(btn => {
        btn.addEventListener('click', handleControlClick);
    });
}

/**
 * Handle control button clicks
 */
async function handleControlClick(e) {
    const btn = e.currentTarget;
    
    console.log('[DEBUG] Button clicked:', btn);
    console.log('[DEBUG] Button classes before:', btn.className);
    
    if (btn.dataset.export) {
        exportChartData();
        return;
    }
    
    const days = parseInt(btn.dataset.days);
    console.log(`[Chart Controls] ≡ƒöä Time period changed to ${days} days`);

    // Get location from global variables (defined in app.js)
    const zipCode = typeof currentZip !== 'undefined' ? currentZip : null;
    const city = typeof currentCity !== 'undefined' ? currentCity : null;
    const state = typeof currentState !== 'undefined' ? currentState : null;

    console.log(`[Chart Controls] ≡ƒôì Location: ZIP=${zipCode}, City=${city}, State=${state}`);

    if (!zipCode && !city) {
        console.warn('[Chart Controls] ΓÜá∩╕Å No location data available');
        return;
    }

    // Update active state FIRST - set all buttons to gray
    console.log('[DEBUG] Setting all buttons to gray...');
    document.querySelectorAll('.chart-control-btn[data-days]').forEach(b => {
        console.log('[DEBUG] Button before reset:', b.className);
        b.classList.remove('active');
        // Remove all Tailwind color classes
        b.classList.remove('bg-blue-600', 'bg-gray-200', 'text-white', 'text-gray-700', 'hover:bg-blue-700', 'hover:bg-gray-300');
        // Add gray classes
        b.classList.add('bg-gray-200', 'text-gray-700', 'hover:bg-gray-300');
        console.log('[DEBUG] Button after reset:', b.className);
    });
    
    // Set clicked button to blue
    console.log('[DEBUG] Setting clicked button to blue...');
    btn.classList.add('active');
    // Remove all color classes first
    btn.classList.remove('bg-gray-200', 'bg-blue-600', 'text-gray-700', 'text-white', 'hover:bg-gray-300', 'hover:bg-blue-700');
    // Add blue classes
    btn.classList.add('bg-blue-600', 'text-white', 'hover:bg-blue-700');
    console.log('[DEBUG] Clicked button classes after:', btn.className);

    // Disable controls while loading to avoid repeated clicks
    const controls = document.querySelectorAll('.chart-control-btn');
    controls.forEach(c => c.disabled = true);
    
    const originalText = btn.innerHTML;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>Loading...`;

    try {
        await initializePollutantCharts(zipCode, city, state, days);
        console.log(`[Chart Controls] Γ£à Charts reloaded successfully`);
    } catch (err) {
        console.error('[Chart Controls] Γ¥î Error reloading charts:', err);
    } finally {
        // Restore button text
        btn.innerHTML = originalText;
        console.log('[DEBUG] Button classes after loading:', btn.className);
        
        // Re-enable controls
        controls.forEach(c => c.disabled = false);
    }
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
