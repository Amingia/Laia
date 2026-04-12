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
                    label: 'Proyección IA (Nodos)',
                    data: [],
                    borderColor: '#0ecb81',
                    borderDash: [5, 5],
                    borderWidth: 2.5,
                    tension: 0,
                    pointRadius: 4,
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
                                font: { size: 11, weight: 'bold' },
                                yAdjust: 10
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: { displayFormats: { hour: 'HH:mm', day: 'dd MMM' }, tooltipFormat: 'dd MMM, HH:mm' },
                    grid: { color: '#1e2329', drawBorder: false, tickLength: 0 },
                    ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 14 }
                },
                y: {
                    grid: { color: '#1e2329', drawBorder: false }, position: 'right',
                    ticks: { callback: function(value) { return '$' + value.toLocaleString('en-US'); } }
                }
            },
            animation: { duration: 0 }
        }
    });
}

function updateChart(chartData) {
    if (!chartInstance || !chartData || chartData.history.prices.length === 0) return;

    const hist = chartData.history;
    const pred = chartData.prediction;

    const realData = [];
    const predData = [];
    const upperData = [];
    const lowerData = [];

    for (let i = 0; i < hist.prices.length; i++) {
        realData.push({ x: hist.times[i], y: hist.prices[i] });
    }
    const nowP = realData[realData.length - 1];

    if (pred && pred.prices && pred.prices.length > 0) {
        predData.push({ x: nowP.x, y: nowP.y });
        upperData.push({ x: nowP.x, y: nowP.y });
        lowerData.push({ x: nowP.x, y: nowP.y });

        for (let i = 0; i < pred.prices.length; i++) {
            const t = pred.times[i];
            const p = pred.prices[i];
            const b_pct = pred.bounds_pct[i];

            predData.push({ x: t, y: p });
            upperData.push({ x: t, y: p * (1 + (b_pct/100)) });
            lowerData.push({ x: t, y: p * (1 - (b_pct/100)) });
        }

        const isBullish = pred.prices[pred.prices.length - 1] >= nowP.y;
        const cColor = isBullish ? '#0ecb81' : '#f6465d';
        const cBg = isBullish ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';

        chartInstance.data.datasets[1].borderColor = cColor;
        chartInstance.data.datasets[1].backgroundColor = cColor;
        chartInstance.data.datasets[2].backgroundColor = cBg;

        document.querySelector('.color-box.pred').style.backgroundColor = cColor;
        document.querySelector('.color-box.band').style.backgroundColor = cBg;
        document.querySelector('.color-box.band').style.borderColor = cColor;
    }

    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = nowP.x;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = nowP.x;

    chartInstance.options.scales.x.min = nowP.x - (168 * 3600 * 1000);
    chartInstance.options.scales.x.max = nowP.x + (25 * 3600 * 1000);

    chartInstance.data.datasets[0].data = realData;
    chartInstance.data.datasets[1].data = predData;
    chartInstance.data.datasets[2].data = upperData;
    chartInstance.data.datasets[3].data = lowerData;

    chartInstance.update();
}

function updateAudit(metrics) {
    if (!metrics) return;

    let hasData = false;
    for (const [horizon, data] of Object.entries(metrics)) {
        const badge = document.getElementById(`badge_${horizon}`);
        const mae = document.getElementById(`mae_${horizon}`);

        if (data.status === "ready") {
            hasData = true;
            if (data.color === "green") {
                badge.className = "audit-badge win";
                badge.innerText = `+ IA GANA (${data.accuracy}%)`;
                mae.innerHTML = `<span class="text-success">${data.mae_ai}%</span> vs ${data.mae_base}%`;
            } else {
                badge.className = "audit-badge lose";
                badge.innerText = `- IA PIERDE (${data.accuracy}%)`;
                mae.innerHTML = `<span class="text-danger">${data.mae_ai}%</span> vs ${data.mae_base}%`;
            }
        } else {
            badge.className = "audit-badge pending";
            badge.innerText = "PENDIENTE";
            mae.innerText = "Recopilando...";
        }
    }

    if (hasData) {
        document.getElementById('kpiAccEmpty').style.display = 'none';
        document.getElementById('kpiAccData').style.display = 'flex';
    } else {
        document.getElementById('kpiAccEmpty').style.display = 'flex';
        document.getElementById('kpiAccData').style.display = 'none';
    }
}

function updateUI(data) {
    if (!data.precio_actual || data.precio_actual === 0) return;

    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const trendEl = document.getElementById('kpiTrend');
    trendEl.innerText = data.tendencia || "Analizando...";
    trendEl.className = data.tendencia.includes("Alza") || data.tendencia.includes("Subida") ? 'text-success' :
                       (data.tendencia.includes("Caída") || data.tendencia.includes("Bajada") ? 'text-danger' : 'text-warning');

    if (data.prediccion_24h_usd) {
        document.getElementById('kpiPredPrice').innerText = `$${data.prediccion_24h_usd.toLocaleString('en-US', {minimumFractionDigits: 0})}`;
        const pctEl = document.getElementById('kpiPredPct');
        pctEl.innerText = `${data.prediccion_24h_pct >= 0 ? '+' : ''}${data.prediccion_24h_pct.toFixed(2)}%`;
        pctEl.className = data.prediccion_24h_pct >= 0 ? 'text-success' : 'text-danger';
    }

    if (data.evaluacion) {
        updateAudit(data.evaluacion);
    }

    if(data.chart_data) {
        updateChart(data.chart_data);
    }
}

async function fetchData() {
    try {
        const response = await fetch('/api/analysis');
        if (response.ok) {
            const data = await response.json();
            updateUI(data);
        }
    } catch (error) {}
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchData();
    setInterval(fetchData, 1500);
});
