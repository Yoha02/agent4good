// Anime.js Animations

// Animate stats cards on load
function animateStatsCards() {
    anime({
        targets: '.stat-card',
        translateY: [50, 0],
        opacity: [0, 1],
        delay: anime.stagger(100),
        duration: 800,
        easing: 'easeOutExpo'
    });
}

// Animate disease cards
function animateDiseaseCards() {
    anime({
        targets: '.disease-card',
        scale: [0.8, 1],
        opacity: [0, 1],
        delay: anime.stagger(150, {start: 500}),
        duration: 600,
        easing: 'easeOutElastic(1, .6)'
    });
}

// Pulse animation for health indicator
function pulseHealthIndicator() {
    anime({
        targets: '.animate-pulse',
        scale: [1, 1.1, 1],
        duration: 2000,
        easing: 'easeInOutQuad',
        loop: true
    });
}

// Smooth scroll navigation with anime.js
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            anime({
                targets: 'html, body',
                scrollTop: targetElement.offsetTop - 80,
                duration: 1000,
                easing: 'easeInOutQuad'
            });
            
            // Update active state
            document.querySelectorAll('.nav-link').forEach(l => {
                l.classList.remove('text-white');
                l.classList.add('text-gray-300');
            });
            this.classList.remove('text-gray-300');
            this.classList.add('text-white');
        }
    });
});

// Animate chart appearance
function animateChart() {
    const chart = document.getElementById('aqiChart');
    if (chart) {
        anime({
            targets: chart.parentElement,
            opacity: [0, 1],
            translateY: [30, 0],
            duration: 800,
            easing: 'easeOutQuad'
        });
    }
}

// Animate chat messages
function animateMessage(element) {
    anime({
        targets: element,
        translateX: [-50, 0],
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutQuad'
    });
}

// Number counter animation
function animateNumber(element, start, end, duration = 2000) {
    const obj = { value: start };
    anime({
        targets: obj,
        value: end,
        duration: duration,
        easing: 'easeOutExpo',
        round: 1,
        update: function() {
            element.textContent = obj.value.toLocaleString();
        }
    });
}

// Floating animation for elements
function floatingAnimation(selector) {
    anime({
        targets: selector,
        translateY: [-10, 10],
        duration: 3000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
    });
}

// Initialize animations
function initAnimations() {
    animateStatsCards();
    
    // Observe disease cards for animation
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                if (entry.target.classList.contains('disease-card')) {
                    animateDiseaseCards();
                    observer.unobserve(entry.target);
                }
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.disease-card').forEach(card => {
        observer.observe(card);
    });
    
    // Pulse health indicator
    pulseHealthIndicator();
    
    // Animate chart when visible
    const chartObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateChart();
                chartObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });
    
    const chartElement = document.getElementById('aqiChart');
    if (chartElement) {
        chartObserver.observe(chartElement.parentElement);
    }
}

// Mobile menu toggle
function toggleMobileMenu() {
    const menu = document.querySelector('.nav-links');
    // Add mobile menu implementation
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnimations);
} else {
    initAnimations();
}

// Export functions for use in other scripts
window.animateMessage = animateMessage;
window.animateNumber = animateNumber;
window.toggleMobileMenu = toggleMobileMenu;
