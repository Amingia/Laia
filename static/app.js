let chartInstance = null;
let warmUpMsgElement = null;

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
                    tension: 0, // Cero tensión para líneas rectas honestas (interpoladas linearmente)
                    pointRadius: function(context) {
                        // Nodos ancla reales (1h, 2h, 4h, 24h) los hacemos más grandes, el resto (relleno matemático) son invisibles a menos que se haga hover
                        const index = context.dataIndex;
                        const anchorIndices = chartInstance.data.customAnchorIndices || [];
                        // index 0 es 'AHORA' (lo tratamos como ancla visual para enganchar)
                        return anchorIndices.includes(index) || index === 0 ? 5 : 0;
                    },
                    pointHoverRadius: 6,
                    fill: false,
                    order: 1
                },
                {
                    label: 'Incertidumbre',
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

    // Cargar 168 horas históricas exactas
    for (let i = 0; i < hist.prices.length; i++) {
        realData.push({ x: hist.times[i], y: hist.prices[i] });
    }
    const nowP = realData[realData.length - 1];

    // Configurar nodos y predicción
    if (pred && pred.prices && pred.prices.length > 0) {

        // Empalme visual en el punto "AHORA"
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

        // Color dinámico según proyección final a 24h
        const isBullish = pred.prices[pred.prices.length - 1] >= nowP.y;
        const cColor = isBullish ? '#0ecb81' : '#f6465d';
        const cBg = isBullish ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';

        chartInstance.data.datasets[1].borderColor = cColor;
        chartInstance.data.datasets[1].backgroundColor = cColor; // Para los nodos ancla
        chartInstance.data.datasets[2].backgroundColor = cBg;

        // Custom Legend updates
        const predBox = document.querySelector('.color-box.pred');
        const bandBox = document.querySelector('.color-box.band');
        if(predBox && bandBox) {
            predBox.style.backgroundColor = cColor;
            bandBox.style.backgroundColor = cBg;
            bandBox.style.borderColor = cColor;
        }

        // Pasamos los índices ancla (1h, 2h, 4h, 24h) al gráfico para engordar los puntos clave y no los interpolados
        if(pred.anchor_indices) {
            // El índice en el dataset está desplazado por 1 (el 0 es AHORA), sumamos +1 a cada anchor_index para encajar
            chartInstance.data.customAnchorIndices = pred.anchor_indices.map(i => i + 1);
        }
    }

    // Línea AHORA anclada al último timestamp real
    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = nowP.x;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = nowP.x;

    // Eje X Fijo de Hierro: 168h hacia atrás y 25h hacia adelante
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

    let totalEvals = metrics.total_evals_global || 0;

    // Si no hay ninguna evaluación en ningún horizonte
    if (totalEvals === 0) {
        document.getElementById('kpiAccEmpty').style.display = 'flex';
        document.getElementById('kpiAccData').style.display = 'none';
        return;
    }

    // Hay datos, mostramos el grid de auditoría
    document.getElementById('kpiAccEmpty').style.display = 'none';
    document.getElementById('kpiAccData').style.display = 'grid';

    // Rellenamos cada horizonte evaluado
    ['1h', '2h', '4h', '24h'].forEach(hz => {
        const data = metrics[hz];
        const badge = document.getElementById(`badge_${hz}`);
        const mae = document.getElementById(`mae_${hz}`);

        if (data && data.status === "ready") {
            if (data.color === "green") {
                badge.className = "audit-badge win";
                badge.innerText = `IA GANA (${data.accuracy}%)`;
                mae.innerHTML = `<span class="text-success">${data.mae_ai}%</span> vs ${data.mae_base}%`;
            } else {
                badge.className = "audit-badge lose";
                badge.innerText = `IA PIERDE (${data.accuracy}%)`;
                mae.innerHTML = `<span class="text-danger">${data.mae_ai}%</span> vs ${data.mae_base}%`;
            }
        } else {
            badge.className = "audit-badge pending";
            badge.innerText = "PENDIENTE";
            mae.innerText = "...";
        }
    });
}

function showWarmupState(msg) {
    // Si el gráfico y la UI principal aún no están listos, muestra los loaders
    const priceEl = document.getElementById('kpiPrice');
    if (priceEl) priceEl.innerText = 'Cargando...';

    const trendEl = document.getElementById('kpiTrend');
    if (trendEl) {
        trendEl.innerText = msg || "Iniciando motor...";
        trendEl.className = 'text-warning';
    }
}

function updateUI(data) {
    if (data.ready === false) {
        showWarmupState(data.status_msg);
        return;
    }

    if (!data.precio_actual || data.precio_actual === 0) return;

    // Precio en Vivo
    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    // Tendencia Esperada Global a 24h
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
            document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator live"></span> <span>Binance 1.5s Polling</span>';
        }
    } catch (error) {
        console.error("Error API:", error);
        document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Desconectado</span>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    warmUpMsgElement = document.getElementById('kpiTrend');
    initChart();
    fetchData();
    setInterval(fetchData, 1500);
});
