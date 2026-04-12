let chartInstance = null;
let lastPricesCount = 0;

function initChart() {
    const ctx = document.getElementById('btcChart').getContext('2d');
    Chart.defaults.color = '#848e9c';
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Histórico (Binance)',
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
                    label: 'Proyección IA',
                    data: [],
                    borderColor: '#0ecb81',
                    borderDash: [5, 5],
                    borderWidth: 2.5,
                    tension: 0.3, // Menos smoothing, más realista
                    pointRadius: 0,
                    pointHoverRadius: 4,
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
                    tension: 0.3
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
                    tension: 0.3
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
                    ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12, font: {size: 11, color: '#848e9c'} }
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

    // Proporción Fija: 48h de Histórico Visual (La IA usa 100h en backend, pero 48h es lo óptimo para la vista)
    for (let i = 0; i < histData.prices.length; i++) {
        realDataFormatted.push({ x: histData.times[i], y: histData.prices[i] });
    }

    const lastRealPoint = realDataFormatted[realDataFormatted.length - 1];

    if (predData && predData.prices && predData.prices.length > 0) {

        // Empalme Perfecto: El primer punto proyectado es el último punto real
        const nowTime = lastRealPoint.x;
        const nowPrice = lastRealPoint.y;

        predDataFormatted.push({ x: nowTime, y: nowPrice });
        upperDataFormatted.push({ x: nowTime, y: nowPrice });
        lowerDataFormatted.push({ x: nowTime, y: nowPrice });

        for (let i = 1; i < predData.prices.length; i++) { // Empezamos en 1 porque el 0 es "AHORA"
            if (i < predData.times.length) {
                const t = predData.times[i];
                predDataFormatted.push({ x: t, y: predData.prices[i] });
                upperDataFormatted.push({ x: t, y: predData.upper_bound[i] });
                lowerDataFormatted.push({ x: t, y: predData.lower_bound[i] });
            }
        }

        const endPrice = predData.prices[predData.prices.length - 1];
        const isBullish = endPrice >= nowPrice;

        const trendColor = isBullish ? '#0ecb81' : '#f6465d';
        const trendBgColor = isBullish ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';
        const legendBandBorder = isBullish ? 'rgba(14, 203, 129, 0.25)' : 'rgba(246, 70, 93, 0.25)';

        chartInstance.data.datasets[1].borderColor = trendColor;
        chartInstance.data.datasets[2].backgroundColor = trendBgColor;

        document.querySelector('.color-box.pred').style.backgroundColor = trendColor;
        document.querySelector('.color-box.band').style.backgroundColor = trendBgColor;
        document.querySelector('.color-box.band').style.borderColor = legendBandBorder;
    }

    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = lastRealPoint.x;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = lastRealPoint.x;

    chartInstance.data.datasets[0].data = realDataFormatted;
    chartInstance.data.datasets[1].data = predDataFormatted;
    chartInstance.data.datasets[2].data = upperDataFormatted;
    chartInstance.data.datasets[3].data = lowerDataFormatted;

    chartInstance.update();
}

function updateUI(data) {
    if (!data.precio_actual || data.precio_actual === 0) return;

    // Precio en Vivo
    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    // Tendencia Esperada
    const trendEl = document.getElementById('kpiTrend');
    trendEl.innerText = data.tendencia || "Analizando...";

    if (data.tendencia && (data.tendencia.includes("Alza") || data.tendencia.includes("Subida"))) {
        trendEl.className = 'text-success';
    } else if (data.tendencia && (data.tendencia.includes("Caída") || data.tendencia.includes("Bajada"))) {
        trendEl.className = 'text-danger';
    } else {
        trendEl.className = 'text-warning';
    }

    // Proyección 24h
    if (data.prediccion_24h_usd) {
        document.getElementById('kpiPredPrice').innerText = `$${data.prediccion_24h_usd.toLocaleString('en-US', {minimumFractionDigits: 0})}`;
        const pctEl = document.getElementById('kpiPredPct');
        const pctVal = data.prediccion_24h_pct;
        pctEl.innerText = `${pctVal >= 0 ? '+' : ''}${pctVal.toFixed(2)}%`;
        pctEl.className = pctVal >= 0 ? 'text-success' : 'text-danger';
    }

    // Validación Real de la IA (JSON Local)
    if (data.evaluacion && data.evaluacion.total_evals > 0 && data.evaluacion.accuracy_pct !== null) {
        document.getElementById('kpiAccEmpty').style.display = 'none';
        document.getElementById('kpiAccData').style.display = 'block';

        document.getElementById('kpiAccuracy').innerText = `${data.evaluacion.accuracy_pct.toFixed(1)}%`;
        document.getElementById('kpiMae').innerText = `${data.evaluacion.mae_pct.toFixed(2)}%`;
        document.getElementById('kpiEvals').innerText = data.evaluacion.total_evals;
    } else {
        document.getElementById('kpiAccEmpty').style.display = 'flex';
        document.getElementById('kpiAccData').style.display = 'none';
    }

    // Gráfico
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

            // Si la conexión va bien, verde
            document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator live"></span> <span>Streaming Binance Spot</span>';
        }
    } catch (error) {
        console.error("Error API:", error);
        // Si hay caída de red, rojo
        document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Conexión Inestable</span>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchData();
    // Polling súper rápido a 1.5s para igualar al backend y dar sensación de Websocket sin los problemas de websocket
    setInterval(fetchData, 1500);
});
