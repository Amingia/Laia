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
                    label: 'Histórico (168h)',
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
                    label: 'Proyección Interpolada',
                    data: [],
                    borderColor: '#0ecb81',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0,
                    pointRadius: function(context) {
                        const index = context.dataIndex;
                        const anchorIndices = chartInstance.data.customAnchorIndices || [];
                        return anchorIndices.includes(index) || index === 0 ? 5 : 0;
                    },
                    pointHoverRadius: 6,
                    fill: false,
                    order: 1
                },
                {
                    label: 'Incertidumbre Superior',
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
                            if(context.dataset.label.includes('Límite') || context.dataset.label.includes('Incertidumbre')) return null;
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
                    time: { displayFormats: { hour: 'HH:mm', day: 'dd MMM' }, tooltipFormat: 'dd MMM, HH:mm' },
                    grid: { color: '#1e2329', drawBorder: false, tickLength: 0 },
                    ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 14, font: {color: '#848e9c'} }
                },
                y: {
                    grid: { color: '#1e2329', drawBorder: false }, position: 'right',
                    ticks: { font: {color: '#848e9c', family: 'monospace'}, callback: function(value) { return '$' + value.toLocaleString('en-US'); } }
                }
            },
            animation: { duration: 0 }
        }
    });
}

function updateChart(chartData) {
    if (!chartInstance || !chartData || !chartData.history || chartData.history.prices.length === 0) return;

    const hist = chartData.history;
    const pred = chartData.prediction;

    const realData = [];
    const predData = [];
    const upperData = [];
    const lowerData = [];

    // Cargar Histórico (El backend envía exactamente 168 o lo que haya disponible sin petar)
    for (let i = 0; i < hist.prices.length; i++) {
        realData.push({ x: hist.times[i], y: hist.prices[i] });
    }

    const lastRealPoint = realData[realData.length - 1];

    // Si la IA aún entrena o falló, solo dibujamos histórico
    if (pred && pred.prices && pred.prices.length > 0) {

        predData.push({ x: lastRealPoint.x, y: lastRealPoint.y });
        upperData.push({ x: lastRealPoint.x, y: lastRealPoint.y });
        lowerData.push({ x: lastRealPoint.x, y: lastRealPoint.y });

        for (let i = 0; i < pred.prices.length; i++) {
            if (i < pred.times.length) {
                const t = pred.times[i];
                predData.push({ x: t, y: pred.prices[i] });
                upperData.push({ x: t, y: pred.upper_bound[i] });
                lowerData.push({ x: t, y: pred.lower_bound[i] });
            }
        }

        const endPrice = pred.prices[pred.prices.length - 1];
        const isBullish = endPrice >= lastRealPoint.y;

        const trendColor = isBullish ? '#0ecb81' : '#f6465d';
        const trendBgColor = isBullish ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';

        chartInstance.data.datasets[1].borderColor = trendColor;
        chartInstance.data.datasets[1].backgroundColor = trendColor;
        chartInstance.data.datasets[2].backgroundColor = trendBgColor;

        const predBox = document.querySelector('.color-box.pred');
        const bandBox = document.querySelector('.color-box.band');
        if(predBox && bandBox) {
            predBox.style.backgroundColor = trendColor;
            bandBox.style.backgroundColor = trendBgColor;
            bandBox.style.borderColor = trendColor;
        }

        if(pred.anchor_indices) {
            chartInstance.data.customAnchorIndices = pred.anchor_indices.map(i => i + 1);
        }
    } else {
        // Vaciamos si no hay predicción (warmup)
        chartInstance.data.customAnchorIndices = [];
    }

    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = lastRealPoint.x;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = lastRealPoint.x;

    // Eje X Fijo: 168h hacia atrás y 25h hacia adelante
    chartInstance.options.scales.x.min = lastRealPoint.x - (168 * 3600 * 1000);
    chartInstance.options.scales.x.max = lastRealPoint.x + (25 * 3600 * 1000);

    chartInstance.data.datasets[0].data = realData;
    chartInstance.data.datasets[1].data = predData;
    chartInstance.data.datasets[2].data = upperData;
    chartInstance.data.datasets[3].data = lowerData;

    chartInstance.update();
}

function updateAudit(metrics) {
    if (!metrics) return;

    let totalEvals = metrics.total_evals_global || 0;

    if (totalEvals === 0) {
        document.getElementById('kpiAccEmpty').style.display = 'flex';
        document.getElementById('kpiAccData').style.display = 'none';
        return;
    }

    document.getElementById('kpiAccEmpty').style.display = 'none';
    document.getElementById('kpiAccData').style.display = 'grid';

    ['1h', '2h', '4h', '24h'].forEach(hz => {
        const data = metrics[hz];
        const badge = document.getElementById(`badge_${hz}`);
        const mae = document.getElementById(`mae_${hz}`);

        if (data && data.status === "ready") {
            if (data.color === "green") {
                badge.className = "audit-badge win";
                badge.innerText = `+ GANA (${data.accuracy}%)`;
                mae.innerHTML = `<span class="text-success">${data.mae_ai}%</span> vs ${data.mae_base}%`;
            } else {
                badge.className = "audit-badge lose";
                badge.innerText = `- PIERDE (${data.accuracy}%)`;
                mae.innerHTML = `<span class="text-danger">${data.mae_ai}%</span> vs ${data.mae_base}%`;
            }
        } else {
            badge.className = "audit-badge pending";
            badge.innerText = "ESPERANDO";
            mae.innerText = "...";
        }
    });
}

function updateUI(data) {
    // Si hay precio, lo pintamos al instante, sin bloqueos.
    if (data.precio_actual && data.precio_actual > 0) {
        document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }

    // Status visual superior (Supervivencia, Entrenando o Vivo)
    const statusDiv = document.getElementById('binanceStatus');
    const banner = document.getElementById('fallbackBanner');
    const trendEl = document.getElementById('kpiTrend');
    const pctEl = document.getElementById('kpiPredPct');
    const predEl = document.getElementById('kpiPredPrice');

    if (data.is_fallback) {
        statusDiv.innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Aislado: Fallback</span>';
        banner.style.display = 'flex';
    } else {
        banner.style.display = 'none';
        if (data.is_training) {
            statusDiv.innerHTML = '<span class="status-indicator warning"></span> <span>Entrenando Modelos...</span>';
        } else {
            statusDiv.innerHTML = '<span class="status-indicator live"></span> <span>Binance 1.5s Streaming</span>';
        }
    }

    if (data.is_training) {
        trendEl.innerText = data.status_msg || "Sincronizando modelos, no cierre la pestaña...";
        trendEl.className = 'text-warning';
        predEl.innerText = '--';
        pctEl.innerText = '--';
        pctEl.className = 'text-muted';
    } else {
        trendEl.innerText = data.tendencia || "Predicción Emitida";
        trendEl.className = data.tendencia.includes("Alza") || data.tendencia.includes("Subida") ? 'text-success' :
                           (data.tendencia.includes("Caída") || data.tendencia.includes("Bajada") ? 'text-danger' : 'text-warning');

        if (data.prediccion_24h_usd) {
            predEl.innerText = `$${data.prediccion_24h_usd.toLocaleString('en-US', {minimumFractionDigits: 0})}`;
            pctEl.innerText = `${data.prediccion_24h_pct >= 0 ? '+' : ''}${data.prediccion_24h_pct.toFixed(2)}%`;
            pctEl.className = data.prediccion_24h_pct >= 0 ? 'text-success' : 'text-danger';
        }
    }

    if (data.evaluacion) {
        updateAudit(data.evaluacion);
    }

    // Pintar gráfico pase lo que pase, aunque sea solo con histórico parcial de arranque.
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
    } catch (error) {
        console.error("Error API:", error);
        document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Motor Backend Desconectado</span>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchData();
    // Polling súper rápido de la UI. El backend le dará lo que tenga listo (Asincronía total V13)
    setInterval(fetchData, 1500);
});
