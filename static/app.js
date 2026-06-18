const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const analyzeBtn = document.getElementById('analyze-btn');
const loader = document.getElementById('loader');
const uploadBox = document.getElementById('upload-box');
const resultsContainer = document.getElementById('results-container');
let selectedFile = null;

// Drag and drop mechanics
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    if(!file.name.endsWith('.csv')) {
        alert("Please upload a valid CSV file.");
        return;
    }
    selectedFile = file;
    dropZone.innerHTML = `
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        <h3>${file.name}</h3>
        <p>File ready for analysis</p>
    `;
    analyzeBtn.disabled = false;
}

// Upload & Analyze Handle
analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    analyzeBtn.style.display = 'none';
    loader.style.display = 'block';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Analysis failed");
        
        const data = await response.json();
        
        // Hide upload, show results
        uploadBox.style.display = 'none';
        resultsContainer.style.display = 'block';

        populateResults(data);

    } catch (err) {
        alert("Error analyzing file: " + err.message);
        analyzeBtn.style.display = 'block';
        loader.style.display = 'none';
    }
});

let seasonalChartInstance = null;
let peaksChartInstance = null;

function populateResults(data) {
    // Top Stats
    document.getElementById('kpi-records').innerText = data.total_rows.toLocaleString();
    document.getElementById('kpi-peaks').innerText = data.total_peaks;
    
    // Insights Generator
    const insightsHtml = data.insights.map(i => `
        <div class="insight-item">
            <h4>${i.title}</h4>
            <p>${i.desc}</p>
        </div>
    `).join('');
    document.getElementById('insight-list').innerHTML = insightsHtml;

    // Charts Setup
    const commonOptions = {
        responsive: true,
        plugins: {
            legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } }
        },
        scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
    };

    // Seasonal Trends Chart
    const ctxSeasonal = document.getElementById('seasonalChart').getContext('2d');
    
    // In our quick dynamic version, data.seasonal_data has { labels: [...], values: [...] }
    if(seasonalChartInstance) seasonalChartInstance.destroy();
    seasonalChartInstance = new Chart(ctxSeasonal, {
        type: 'line',
        data: {
            labels: data.seasonal_data.labels,
            datasets: [{
                label: 'Average MW Load (Dynamic)',
                data: data.seasonal_data.values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                tension: 0.4,
                fill: true
            }]
        },
        options: commonOptions
    });

    // Top Peaks Bar Chart
    const ctxPeaks = document.getElementById('peaksChart').getContext('2d');
    
    if(peaksChartInstance) peaksChartInstance.destroy();
    peaksChartInstance = new Chart(ctxPeaks, {
        type: 'bar',
        data: {
            labels: data.peaks_data.labels,
            datasets: [{
                label: 'Top Hours (MW)',
                data: data.peaks_data.values,
                backgroundColor: '#8b5cf6',
                borderRadius: 4
            }]
        },
        options: {
            ...commonOptions,
            indexAxis: 'y'
        }
    });

    // Animate smoothly to results
    window.scrollTo({ top: 300, behavior: 'smooth' });
}
