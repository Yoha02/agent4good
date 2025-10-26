// Global variables
let aqiChart = null;
let currentState = '';
let currentDays = 7;
let lastVideoData = null; // Store video data for Twitter posting

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

// Initialize the application
function initializeApp() {
    loadAirQualityData();
    loadHealthRecommendations();
}

// Setup event listeners
function setupEventListeners() {
    // State selector
    const stateSelect = document.getElementById('stateSelect');
    if (stateSelect) {
        stateSelect.addEventListener('change', function(e) {
            currentState = e.target.value;
            loadAirQualityData();
            loadHealthRecommendations();
        });
    }

    // Enter key for AI chat
    const questionInput = document.getElementById('questionInput');
    if (questionInput) {
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askAI();
            }
        });
    }
}

// Load air quality data
async function loadAirQualityData() {
    showLoading();
    try {
        const params = new URLSearchParams({
            days: currentDays
        });
        
        if (currentState) {
            params.append('state', currentState);
        }

        const response = await fetch(`/api/air-quality?${params}`);
        const data = await response.json();

        if (data.success) {
            updateStatistics(data.statistics);
            updateDataTable(data.data);
            updateChart(data.data);
        } else {
            console.error('Failed to load air quality data');
        }
    } catch (error) {
        console.error('Error loading air quality data:', error);
    } finally {
        hideLoading();
    }
}

// Update statistics cards with animation
function updateStatistics(stats) {
    const totalRecordsEl = document.getElementById('totalRecords');
    const uniqueLocationsEl = document.getElementById('uniqueLocations');
    const avgAqiEl = document.getElementById('avgAqi');
    
    if (totalRecordsEl && window.animateNumber) {
        animateNumber(totalRecordsEl, 0, stats.total_records || 0, 1500);
    } else if (totalRecordsEl) {
        totalRecordsEl.textContent = formatNumber(stats.total_records || 0);
    }
    
    if (uniqueLocationsEl && window.animateNumber) {
        animateNumber(uniqueLocationsEl, 0, stats.unique_locations || 0, 1500);
    } else if (uniqueLocationsEl) {
        uniqueLocationsEl.textContent = formatNumber(stats.unique_locations || 0);
    }
    
    if (avgAqiEl && window.animateNumber) {
        animateNumber(avgAqiEl, 0, Math.round(stats.avg_aqi || 0), 1500);
    } else if (avgAqiEl) {
        avgAqiEl.textContent = formatNumber(stats.avg_aqi || 0, 1);
    }
}

// Load health recommendations
async function loadHealthRecommendations() {
    try {
        const params = new URLSearchParams();
        if (currentState) {
            params.append('state', currentState);
        }

        const response = await fetch(`/api/health-recommendations?${params}`);
        const data = await response.json();

        if (data.success) {
            updateAQIDisplay(data);
        }
    } catch (error) {
        console.error('Error loading health recommendations:', error);
    }
}


// Update AQI display
function updateAQIDisplay(data) {
    const aqiValue = document.getElementById('currentAqi');
    const aqiLevel = document.getElementById('aqiLevel');
    const recommendation = document.getElementById('recommendation');

    if (aqiValue) {
        if (window.animateNumber) {
            animateNumber(aqiValue, 0, Math.round(data.aqi), 1500);
        } else {
            aqiValue.textContent = Math.round(data.aqi);
        }
    }
    if (aqiLevel) aqiLevel.textContent = data.level;
    if (recommendation) recommendation.textContent = data.recommendation;
}

// Update data table with Tailwind styling
function updateDataTable(data) {
    const tableBody = document.getElementById('dataTableBody');
    if (!tableBody) return;

    if (!data || data.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                    <i class="fas fa-inbox text-3xl mb-2"></i>
                    <p>No data available</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = data.slice(0, 50).map(row => `
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-sm text-gray-700">${formatDate(row.date)}</td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.state_name || '-'}</td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.county_name || '-'}</td>
            <td class="px-6 py-4">
                <span class="px-3 py-1 text-sm font-bold rounded-full ${getAQIBadgeClass(row.aqi)}">
                    ${row.aqi || '-'}
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.parameter_name || '-'}</td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.site_name || '-'}</td>
        </tr>
    `).join('');
}

// Get AQI badge color class
function getAQIBadgeClass(aqi) {
    if (aqi <= 50) return 'bg-emerald-100 text-emerald-700';
    if (aqi <= 100) return 'bg-yellow-100 text-yellow-700';
    if (aqi <= 150) return 'bg-orange-100 text-orange-700';
    if (aqi <= 200) return 'bg-red-100 text-red-700';
    if (aqi <= 300) return 'bg-purple-100 text-purple-700';
    return 'bg-rose-100 text-rose-700';
}


// Update chart with modern styling
function updateChart(data) {
    if (!data || data.length === 0) return;

    // Aggregate data by date
    const dateAqiMap = {};
    data.forEach(row => {
        const date = formatDate(row.date);
        if (!dateAqiMap[date]) {
            dateAqiMap[date] = [];
        }
        dateAqiMap[date].push(row.aqi);
    });

    // Calculate average AQI per date
    const chartData = Object.keys(dateAqiMap)
        .sort()
        .slice(-currentDays)
        .map(date => ({
            date: date,
            aqi: average(dateAqiMap[date])
        }));

    const ctx = document.getElementById('aqiChart');
    if (!ctx) return;

    // Destroy existing chart
    if (aqiChart) {
        aqiChart.destroy();
    }

    // Create gradient
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    // Create new chart with modern styling
    aqiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.map(d => d.date),
            datasets: [{
                label: 'Average AQI',
                data: chartData.map(d => d.aqi),
                borderColor: '#10b981',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: '#10b981',
                pointBorderColor: '#fff',
                pointBorderWidth: 3,
                pointHoverBackgroundColor: '#10b981',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 58, 82, 0.95)',
                    padding: 16,
                    titleFont: {
                        size: 16,
                        weight: 'bold',
                        family: "'Inter', sans-serif"
                    },
                    bodyFont: {
                        size: 14,
                        family: "'Inter', sans-serif"
                    },
                    borderColor: '#10b981',
                    borderWidth: 2,
                    cornerRadius: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return 'AQI: ' + Math.round(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            family: "'Inter', sans-serif",
                            weight: '500'
                        },
                        color: '#6b7280'
                    },
                    border: {
                        display: false
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            family: "'Inter', sans-serif",
                            weight: '500'
                        },
                        color: '#6b7280',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    border: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Ask AI function
async function askAI() {
    const questionInput = document.getElementById('questionInput');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!questionInput || !chatMessages) return;
    
    const question = questionInput.value.trim();
    if (!question) return;

    // Check if user is approving Twitter post
    if (lastVideoData && isTwitterApproval(question)) {
        await postToTwitter(lastVideoData);
        questionInput.value = '';
        return;
    }

    // Add user message
    addMessage(question, 'user');
    questionInput.value = '';

    // Show loading
    const loadingMsg = addMessage('Thinking...', 'bot');
    
    try {
        // Get stored location data for chat agent
        const storedLocationData = localStorage.getItem('currentLocationData');
        let locationContext = null;
        
        if (storedLocationData) {
            try {
                locationContext = JSON.parse(storedLocationData);
                console.log('[Chat] Using stored location data:', locationContext);
            } catch (e) {
                console.warn('[Chat] Failed to parse stored location data:', e);
            }
        }
        
        // Get time frame from date inputs
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        let timeFrame = null;
        
        if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
            timeFrame = {
                start_date: startDateInput.value,
                end_date: endDateInput.value,
                period: `${startDateInput.value} to ${endDateInput.value}`
            };
            console.log('[Chat] Using time frame:', timeFrame);
        }
        
        // Try ADK agent first
        const response = await fetch('/api/agent-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                state: currentState,
                days: currentDays,
                location_context: locationContext,
                time_frame: timeFrame
            })
        });

        const data = await response.json();

        // Remove loading message
        loadingMsg.remove();

        if (data.success) {
            // Add agent badge if available
            const agentBadge = data.agent ? `<div class="text-xs text-gray-500 mt-1">via ${data.agent}</div>` : '';
            
            // Add context indicators if available
            let contextIndicators = '';
            if (locationContext) {
                const locationText = [locationContext.city, locationContext.state, locationContext.zipCode].filter(Boolean).join(', ');
                contextIndicators += `<div class="text-xs text-emerald-600 mt-1 flex items-center">
                    <i class="fas fa-map-marker-alt mr-1"></i>
                    Using location: ${locationText}
                </div>`;
            }
            
            if (timeFrame) {
                contextIndicators += `<div class="text-xs text-blue-600 mt-1 flex items-center">
                    <i class="fas fa-calendar-alt mr-1"></i>
                    Using time frame: ${timeFrame.period}
                </div>`;
            }
            
            // Add current time indicator
            const now = new Date();
            const currentTime = now.toLocaleString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            contextIndicators += `<div class="text-xs text-purple-600 mt-1 flex items-center">
                <i class="fas fa-clock mr-1"></i>
                Current time: ${currentTime}
            </div>`;
            
            addMessage(data.response + agentBadge + contextIndicators, 'bot');
            
            // If video generation started, begin polling
            if (data.task_id) {
                pollForVideoCompletion(data.task_id);
            }
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        loadingMsg.remove();
        addMessage('Sorry, I could not connect to the AI service.', 'bot');
        console.error('Error asking AI:', error);
    }
}

// Check if user message is Twitter approval
function isTwitterApproval(message) {
    const lowerMsg = message.toLowerCase().trim();
    const approvalPhrases = ['yes', 'yeah', 'sure', 'ok', 'okay', 'post it', 'post to twitter', 'tweet it', 'share it'];
    return approvalPhrases.some(phrase => lowerMsg === phrase || lowerMsg.includes(phrase));
}

// Post video to Twitter
async function postToTwitter(videoData) {
    const questionInput = document.getElementById('questionInput');
    
    // Add user's approval message
    addMessage('Yes, post to Twitter', 'user');
    
    // Show posting message
    const loadingMsg = addMessage('Posting to Twitter... (This may take 60-90 seconds: downloading video, uploading to Twitter, processing)', 'bot');
    
    try {
        // Create abort controller for timeout (2 minutes)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes
        
        const response = await fetch('/api/post-to-twitter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_url: videoData.video_url,
                message: videoData.action_line,
                hashtags: ['HealthAlert', 'PublicHealth', 'CommunityHealth', 'AirQuality']
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const result = await response.json();
        
        // Remove loading message
        loadingMsg.remove();
        
        if (result.success) {
            const successMessage = `✓ Posted to Twitter successfully!\n\nView your post: ${result.tweet_url}\n\n${result.message}`;
            addMessage(successMessage, 'bot');
            
            // Clear video data after posting
            lastVideoData = null;
        } else {
            addMessage(`Sorry, I couldn't post to Twitter: ${result.error}`, 'bot');
        }
        
    } catch (error) {
        loadingMsg.remove();
        if (error.name === 'AbortError') {
            addMessage('Twitter posting timed out. The video may still have been posted. Please check your Twitter feed at https://twitter.com/AI_mmunity', 'bot');
        } else {
            addMessage('Sorry, there was an error posting to Twitter. Please try again.', 'bot');
        }
        console.error('Twitter posting error:', error);
    }
    
    // Clear input
    if (questionInput) {
        questionInput.value = '';
    }
}

// Poll for video generation completion
const activeVideoPolls = new Set();

async function pollForVideoCompletion(taskId) {
    // Prevent duplicate polling
    if (activeVideoPolls.has(taskId)) return;
    activeVideoPolls.add(taskId);
    
    console.log(`[VIDEO] Starting poll for task: ${taskId}`);
    
    const maxAttempts = 30; // 30 * 5 sec = 2.5 minutes
    
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        
        try {
            const response = await fetch(`/api/check-video-task/${taskId}`);
            const status = await response.json();
            
            console.log(`[VIDEO] Poll ${i + 1}: ${status.status} - ${status.progress || 0}%`);
            
            if (status.status === 'complete') {
                // Store video data for potential Twitter posting
                lastVideoData = {
                    video_url: status.video_url,
                    action_line: status.action_line,
                    task_id: taskId
                };
                
                // Video is ready! Add new message with video
                const videoMessage = `✓ Your PSA video is ready!

[VIDEO:${status.video_url}]

Action: "${status.action_line}"

Would you like me to post this to Twitter?`;
                
                addMessage(videoMessage, 'bot');
                activeVideoPolls.delete(taskId);
                console.log(`[VIDEO] Task ${taskId} complete!`);
                console.log('[VIDEO] Video data stored for Twitter posting');
                return;
            } else if (status.status === 'error') {
                // Generation failed
                addMessage(`Sorry, video generation encountered an error: ${status.error}`, 'bot');
                activeVideoPolls.delete(taskId);
                console.error(`[VIDEO] Task ${taskId} failed:`, status.error);
                return;
            }
            // Continue polling if still processing
        } catch (error) {
            console.error('[VIDEO] Polling error:', error);
            // Continue polling despite errors
        }
    }
    
    // Timeout
    activeVideoPolls.delete(taskId);
    addMessage('Video generation timed out. Please try again.', 'bot');
    console.error(`[VIDEO] Task ${taskId} timeout`);
}


// Add message to chat with Tailwind styling
function addMessage(text, type) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return null;

    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-start space-x-3 ${type === 'user' ? 'justify-end' : ''}`;
    
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
                <div class="my-3">
                    <video 
                        controls 
                        class="w-full rounded-lg shadow-lg" 
                        style="max-width: 300px; max-height: 533px;"
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
            <div class="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-robot text-white"></i>
            </div>
            <div class="bg-white rounded-2xl rounded-tl-none p-4 shadow-md max-w-2xl">
                ${videoHtml}
                <p class="text-gray-700 leading-relaxed whitespace-pre-line">${messageContent}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bg-navy-700 text-white rounded-2xl rounded-tr-none p-4 shadow-md max-w-lg">
                <p class="leading-relaxed">${text}</p>
            </div>
            <div class="w-10 h-10 bg-navy-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-user text-white"></i>
            </div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Animate the message if anime.js is available
    if (window.animateMessage) {
        animateMessage(messageDiv);
    }

    return messageDiv;
}

// Change days function
function changeDays(days) {
    currentDays = days;
    loadAirQualityData();
}

// Utility functions
function formatNumber(num, decimals = 0) {
    if (typeof num !== 'number') return '-';
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function average(arr) {
    if (!arr || arr.length === 0) return 0;
    return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function adjustColor(color, amount) {
    // Simple color adjustment for gradient
    return color;
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
    }
}

function smoothScrollToSections() {
    // Handled by animations.js
}
