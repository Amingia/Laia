let chartInstance = null;

function initChart() {
    const ctx = document.getElementById('btcChart').getContext('2d');
    Chart.defaults.color = '#848e9c';
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Histórico Real (168h)',
                    data: [],
                    borderColor: '#fcd535',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: false,
                    order: 2
                },
                {
                    label: 'Proyección IA Nodos',
                    data: [],
                    borderColor: '#0ecb81',
                    borderDash: [5, 5],
                    borderWidth: 2.5,
                    tension: 0, // Cero tensión para líneas rectas honestas entre nodos
                    pointRadius: 4, // Nodos visibles explícitamente
                    pointHoverRadius: 6,
                    fill: false,
                    order: 1
                },
                {
                    label: 'Límite Superior',
                    data: [],
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(14, 203, 129, 0.1)',
                    fill: '+1',
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    order: 3,
                    tension: 0
                },
                {
                    label: 'Límite Inferior',
                    data: [],
                    borderColor: 'transparent',
                    backgroundColor: 'transparent',
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    order: 4,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(11, 14, 17, 0.95)',
                    titleColor: '#848e9c',
                    bodyColor: '#eaecef',
                    borderColor: '#2b3139',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { size: 12, weight: 'normal' },
                    bodyFont: { size: 14, weight: 'bold' },
                    callbacks: {
                        title: (context) => {
                            const date = new Date(context[0].parsed.x);
                            return date.toLocaleString('es-ES', { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
                        },
                        label: (context) => {
                            if(context.dataset.label.includes('Límite')) return null;
                            return `${context.dataset.label}: $${context.parsed.y.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
                        }
                    }
                },
                annotation: {
                    annotations: {
                        nowLine: {
                            type: 'line',
                            xMin: Date.now(),
                            xMax: Date.now(),
                            borderColor: 'rgba(234, 236, 239, 0.6)',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            label: {
                                display: true,
                                content: 'AHORA',
                                position: 'start',
                                backgroundColor: 'rgba(30, 35, 41, 0.9)',
                                color: '#eaecef',
                                font: { size: 11, weight: 'bold', family: 'monospace' },
                                yAdjust: 10
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: { hour: 'HH:mm', day: 'dd MMM' },
                        tooltipFormat: 'dd MMM, HH:mm'
                    },
                    grid: { color: '#1e2329', drawBorder: false, tickLength: 0 },
                    ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 14, font: {size: 11, color: '#848e9c'} }
                },
                y: {
                    grid: { color: '#1e2329', drawBorder: false },
                    position: 'right',
                    ticks: {
                        font: {size: 11, color: '#848e9c', family: 'monospace'},
                        callback: function(value) { return '$' + value.toLocaleString('en-US'); }
                    }
                }
            },
            animation: { duration: 0 }
        }
    });
}

function updateChart(histData, predData) {
    if (!chartInstance || !histData || !histData.prices || histData.prices.length === 0) return;

    const realDataFormatted = [];
    const predDataFormatted = [];
    const upperDataFormatted = [];
    const lowerDataFormatted = [];

    // Exactamente 168h visuales del array
    for (let i = 0; i < histData.prices.length; i++) {
        realDataFormatted.push({ x: histData.times[i], y: histData.prices[i] });
    }

    const lastRealPoint = realDataFormatted[realDataFormatted.length - 1];

    // Conexión del futuro a partir de los Nodos limpios
    if (predData && predData.prices && predData.prices.length > 0) {

        const nowTime = lastRealPoint.x;
        const nowPrice = lastRealPoint.y;

        predDataFormatted.push({ x: nowTime, y: nowPrice });
        upperDataFormatted.push({ x: nowTime, y: nowPrice });
        lowerDataFormatted.push({ x: nowTime, y: nowPrice });

        for (let i = 0; i < predData.prices.length; i++) {
            if (i < predData.times.length) {
                const t = predData.times[i];
                predDataFormatted.push({ x: t, y: predData.prices[i] });

                // Las bounds vienen en %, las pasamos a precio real
                const b_pct = predData.bounds_pct[i];
                upperDataFormatted.push({ x: t, y: predData.prices[i] * (1 + (b_pct/100)) });
                lowerDataFormatted.push({ x: t, y: predData.prices[i] * (1 - (b_pct/100)) });
            }
        }

        const endPrice = predData.prices[predData.prices.length - 1];
        const isBullish = endPrice >= nowPrice;

        const trendColor = isBullish ? '#0ecb81' : '#f6465d';
        const trendBgColor = isBullish ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';
        const legendBandBorder = isBullish ? 'rgba(14, 203, 129, 0.25)' : 'rgba(246, 70, 93, 0.25)';

        chartInstance.data.datasets[1].borderColor = trendColor;
        chartInstance.data.datasets[1].backgroundColor = trendColor; // Nodos del color de la linea
        chartInstance.data.datasets[2].backgroundColor = trendBgColor;

        document.querySelector('.color-box.pred').style.backgroundColor = trendColor;
        document.querySelector('.color-box.band').style.backgroundColor = trendBgColor;
        document.querySelector('.color-box.band').style.borderColor = legendBandBorder;
    }

    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = lastRealPoint.x;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = lastRealPoint.x;

    // Fijar el eje temporal forzosamente para que el gráfico no 'patine' o desproporcione: (168h + 24h = 192h total vista)
    const viewMin = lastRealPoint.x - (168 * 3600 * 1000);
    const viewMax = lastRealPoint.x + (25 * 3600 * 1000);
    chartInstance.options.scales.x.min = viewMin;
    chartInstance.options.scales.x.max = viewMax;

    chartInstance.data.datasets[0].data = realDataFormatted;
    chartInstance.data.datasets[1].data = predDataFormatted;
    chartInstance.data.datasets[2].data = upperDataFormatted;
    chartInstance.data.datasets[3].data = lowerDataFormatted;

    chartInstance.update();
}

function updateUI(data) {
    if (!data.precio_actual || data.precio_actual === 0) return;

    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const trendEl = document.getElementById('kpiTrend');
    trendEl.innerText = data.tendencia || "Analizando...";

    if (data.tendencia && (data.tendencia.includes("Alza") || data.tendencia.includes("Subida"))) {
        trendEl.className = 'text-success';
    } else if (data.tendencia && (data.tendencia.includes("Caída") || data.tendencia.includes("Bajada"))) {
        trendEl.className = 'text-danger';
    } else {
        trendEl.className = 'text-warning';
    }

    if (data.prediccion_24h_usd) {
        document.getElementById('kpiPredPrice').innerText = `$${data.prediccion_24h_usd.toLocaleString('en-US', {minimumFractionDigits: 0})}`;
        const pctEl = document.getElementById('kpiPredPct');
        const pctVal = data.prediccion_24h_pct;
        pctEl.innerText = `${pctVal >= 0 ? '+' : ''}${pctVal.toFixed(2)}%`;
        pctEl.className = pctVal >= 0 ? 'text-success' : 'text-danger';
    }

    // Auditoría vs Baseline
    if (data.evaluacion && data.evaluacion.total > 0 && data.evaluacion.mae_ai !== null) {
        document.getElementById('kpiAccEmpty').style.display = 'none';
        document.getElementById('kpiAccData').style.display = 'block';

        const statusMsg = document.getElementById('auditStatus');
        statusMsg.innerText = data.evaluacion.status;

        // Color dinámico según la comparación del Json Tracker
        const cardBorder = document.getElementById('auditCard');
        if (data.evaluacion.color === "green") {
            statusMsg.className = 'audit-status text-success';
            cardBorder.style.borderTopColor = 'var(--success)';
            document.getElementById('kpiMaeIA').className = 'text-success';
        } else if (data.evaluacion.color === "red") {
            statusMsg.className = 'audit-status text-danger';
            cardBorder.style.borderTopColor = 'var(--danger)';
            document.getElementById('kpiMaeIA').className = 'text-danger';
        } else {
            statusMsg.className = 'audit-status text-warning';
            cardBorder.style.borderTopColor = 'var(--warning)';
            document.getElementById('kpiMaeIA').className = 'text-warning';
        }

        document.getElementById('kpiAccuracy').innerText = `${data.evaluacion.accuracy.toFixed(1)}%`;
        document.getElementById('kpiMaeIA').innerText = `${data.evaluacion.mae_ai.toFixed(2)}%`;
        document.getElementById('kpiMaeBase').innerText = `${data.evaluacion.mae_baseline.toFixed(2)}%`;
        document.getElementById('kpiEvals').innerText = data.evaluacion.total;
    } else {
        document.getElementById('kpiAccEmpty').style.display = 'flex';
        document.getElementById('kpiAccData').style.display = 'none';
    }

    if(data.chart_data) {
        updateChart(data.chart_data.history, data.chart_data.prediction);
    }
}

async function fetchData() {
    try {
        const response = await fetch('/api/analysis');
        if (response.ok) {
            const data = await response.json();
            updateUI(data);
            document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator live"></span> <span>Binance 1s Polling</span>';
        }
    } catch (error) {
        console.error("Error API:", error);
        document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Desconectado</span>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchData();
    setInterval(fetchData, 1500);
});
