// D3.js Visualizations

// Initialize D3 Geographic Map
function initD3Map() {
    const container = d3.select('#d3-map');
    const width = container.node().getBoundingClientRect().width;
    const height = 400;
    
    // Clear existing
    container.selectAll('*').remove();
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('class', 'rounded-xl');
    
    // Sample data for states
    const stateData = [
        { state: 'California', aqi: 85, x: 100, y: 200 },
        { state: 'Texas', aqi: 65, x: 400, y: 250 },
        { state: 'New York', aqi: 72, x: 700, y: 150 },
        { state: 'Florida', aqi: 58, x: 650, y: 280 },
        { state: 'Illinois', aqi: 68, x: 500, y: 120 }
    ];
    
    // Color scale
    const colorScale = d3.scaleLinear()
        .domain([0, 50, 100, 150, 200])
        .range(['#10b981', '#fbbf24', '#f59e0b', '#ef4444', '#991b1b']);
    
    // Create circles for each state
    const circles = svg.selectAll('circle')
        .data(stateData)
        .enter()
        .append('circle')
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)
        .attr('r', 0)
        .attr('fill', d => colorScale(d.aqi))
        .attr('opacity', 0.7)
        .attr('stroke', '#1a3a52')
        .attr('stroke-width', 2);
    
    // Animate circles
    circles.transition()
        .duration(1000)
        .delay((d, i) => i * 100)
        .attr('r', d => Math.sqrt(d.aqi) * 3)
        .ease(d3.easeBounceOut);
    
    // Add labels
    svg.selectAll('text')
        .data(stateData)
        .enter()
        .append('text')
        .attr('x', d => d.x)
        .attr('y', d => d.y - Math.sqrt(d.aqi) * 3 - 10)
        .attr('text-anchor', 'middle')
        .attr('fill', '#1a3a52')
        .attr('font-weight', 'bold')
        .attr('font-size', '14px')
        .attr('opacity', 0)
        .text(d => `${d.state}: ${d.aqi}`)
        .transition()
        .duration(500)
        .delay((d, i) => i * 100 + 1000)
        .attr('opacity', 1);
    
    // Add connecting lines
    for (let i = 0; i < stateData.length - 1; i++) {
        svg.append('line')
            .attr('x1', stateData[i].x)
            .attr('y1', stateData[i].y)
            .attr('x2', stateData[i + 1].x)
            .attr('y2', stateData[i + 1].y)
            .attr('stroke', '#cbd5e1')
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', '5,5')
            .attr('opacity', 0)
            .transition()
            .duration(500)
            .delay(i * 100 + 1500)
            .attr('opacity', 0.3);
    }
    
    // Add interactivity
    circles
        .on('mouseover', function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('r', Math.sqrt(d.aqi) * 4)
                .attr('opacity', 1);
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('r', Math.sqrt(d.aqi) * 3)
                .attr('opacity', 0.7);
        });
}

// Disease Heatmap with D3
function initDiseaseHeatmap() {
    const container = d3.select('#disease-heatmap');
    const width = container.node().getBoundingClientRect().width;
    const height = 400;
    
    // Clear existing
    container.selectAll('*').remove();
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('class', 'rounded-xl');
    
    // Sample heatmap data (weeks x diseases)
    const data = [];
    const diseases = ['COVID-19', 'Influenza', 'RSV', 'Norovirus'];
    const weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7'];
    
    weeks.forEach((week, i) => {
        diseases.forEach((disease, j) => {
            data.push({
                week: week,
                disease: disease,
                value: Math.random() * 100,
                x: i,
                y: j
            });
        });
    });
    
    const cellWidth = width / weeks.length;
    const cellHeight = height / diseases.length;
    
    // Color scale
    const colorScale = d3.scaleSequential()
        .domain([0, 100])
        .interpolator(d3.interpolateRgb('#10b981', '#ef4444'));
    
    // Create cells
    const cells = svg.selectAll('rect')
        .data(data)
        .enter()
        .append('rect')
        .attr('x', d => d.x * cellWidth)
        .attr('y', d => d.y * cellHeight)
        .attr('width', cellWidth - 2)
        .attr('height', cellHeight - 2)
        .attr('fill', d => colorScale(d.value))
        .attr('opacity', 0)
        .attr('rx', 8);
    
    // Animate cells
    cells.transition()
        .duration(500)
        .delay((d, i) => i * 20)
        .attr('opacity', 0.8);
    
    // Add labels for diseases
    svg.selectAll('.disease-label')
        .data(diseases)
        .enter()
        .append('text')
        .attr('class', 'disease-label')
        .attr('x', -10)
        .attr('y', (d, i) => i * cellHeight + cellHeight / 2)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'middle')
        .attr('fill', '#1a3a52')
        .attr('font-weight', 'bold')
        .attr('font-size', '14px')
        .text(d => d);
    
    // Add labels for weeks
    svg.selectAll('.week-label')
        .data(weeks)
        .enter()
        .append('text')
        .attr('class', 'week-label')
        .attr('x', (d, i) => i * cellWidth + cellWidth / 2)
        .attr('y', height + 20)
        .attr('text-anchor', 'middle')
        .attr('fill', '#1a3a52')
        .attr('font-weight', 'bold')
        .attr('font-size', '12px')
        .text(d => d);
    
    // Add interactivity
    cells
        .on('mouseover', function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('opacity', 1)
                .attr('stroke', '#1a3a52')
                .attr('stroke-width', 2);
            
            // Show tooltip
            svg.append('text')
                .attr('class', 'tooltip')
                .attr('x', d.x * cellWidth + cellWidth / 2)
                .attr('y', d.y * cellHeight - 10)
                .attr('text-anchor', 'middle')
                .attr('fill', '#1a3a52')
                .attr('font-weight', 'bold')
                .text(`${Math.round(d.value)} cases`);
        })
        .on('mouseout', function() {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('opacity', 0.8)
                .attr('stroke', 'none');
            
            svg.selectAll('.tooltip').remove();
        });
}

// Initialize D3 visualizations when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initD3Map();
        initDiseaseHeatmap();
    });
} else {
    initD3Map();
    initDiseaseHeatmap();
}

// Reinitialize on window resize
window.addEventListener('resize', () => {
    initD3Map();
    initDiseaseHeatmap();
});
