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
                            if (!context || !context[0] || !context[0].parsed) return '';
                            const date = new Date(context[0].parsed.x);
                            return date.toLocaleString('es-ES', { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
                        },
                        label: (context) => {
                            if(!context || !context.dataset || !context.parsed) return '';
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
    if (!chartInstance) return;

    // Blindaje anti-vacio. No queremos bloquear el frontend, si hay historico (lineas amarillas) lo dibujamos SIEMPRE, haya prediccion o no.
    if (!chartData || !chartData.history || !chartData.history.prices || chartData.history.prices.length === 0) {
        console.warn("[V15 Chart] No se ha recibido historico desde el Backend todavía. Esperando...");
        return;
    }

    const hist = chartData.history;
    const pred = chartData.prediction;

    const realData = [];
    const predData = [];
    const upperData = [];
    const lowerData = [];

    // Cargar Histórico Real
    for (let i = 0; i < hist.prices.length; i++) {
        if(hist.times[i]) {
            realData.push({ x: hist.times[i], y: hist.prices[i] });
        }
    }

    if (realData.length === 0) return;

    const lastRealPoint = realData[realData.length - 1];

    // Si tenemos predicciones generadas y válidas (es decir, NO ESTAMOS en `is_training`)
    if (pred && pred.prices && pred.prices.length > 0 && pred.times && pred.times.length > 0) {

        // Empalme visual con el precio actual ("AHORA")
        predData.push({ x: lastRealPoint.x, y: lastRealPoint.y });
        upperData.push({ x: lastRealPoint.x, y: lastRealPoint.y });
        lowerData.push({ x: lastRealPoint.x, y: lastRealPoint.y });

        // Pintado del futuro
        for (let i = 0; i < pred.prices.length; i++) {
            if (i < pred.times.length) {
                const t = pred.times[i];
                const p = pred.prices[i];
                const b_pct = (pred.bounds_pct && pred.bounds_pct[i]) ? pred.bounds_pct[i] : 0.005; // Margen de seguridad default si no llega el % de confianza

                predData.push({ x: t, y: p });
                upperData.push({ x: t, y: p * (1 + (b_pct)) });
                lowerData.push({ x: t, y: p * (1 - (b_pct)) });
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
        // MODO IS_TRAINING o DEGRADADO: Sin predicción. Limpiamos nodos y vaciamos el dataset verde/rojo para pintar solo el amarillo
        chartInstance.data.customAnchorIndices = [];
    }

    // Configuración del Marco de Tiempo estático y blindado
    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = lastRealPoint.x;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = lastRealPoint.x;

    // Eje X Fijo: Siempre 168h pasado + 25h futuro. Si hay Fallback, se mantendrá inamovible gracias a esta fórmula.
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

    let totalEvals = 0;
    try {
        if(metrics["24h"]) totalEvals += metrics["24h"].evals || 0;
        if(metrics["4h"]) totalEvals += metrics["4h"].evals || 0;
        if(metrics["2h"]) totalEvals += metrics["2h"].evals || 0;
        if(metrics["1h"]) totalEvals += metrics["1h"].evals || 0;
    } catch(e) {}

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
    if (!data) return;

    const priceEl = document.getElementById('kpiPrice');
    const trendEl = document.getElementById('kpiTrend');
    const pctEl = document.getElementById('kpiPredPct');
    const predEl = document.getElementById('kpiPredPrice');
    const statusDiv = document.getElementById('binanceStatus');
    const banner = document.getElementById('fallbackBanner');
    const pulse = document.getElementById('pricePulse');

    // 1. Mostrar precio en vivo siempre, mitigando el "Cargando..."
    if (data.precio_actual && data.precio_actual > 0) {
        priceEl.innerText = `$${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        pulse.style.display = 'block';
    }

    // 2. Banner de Fallback Binance (Modo Supervivencia Extrema)
    if (data.is_fallback) {
        statusDiv.innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Binance Caído (Emergencia M-V15)</span>';
        if(banner) banner.style.display = 'flex';
    } else {
        if(banner) banner.style.display = 'none';
        if (data.is_training) {
            statusDiv.innerHTML = '<span class="status-indicator warning"></span> <span class="text-warning">Cargando contexto de Binance...</span>';
        } else {
            statusDiv.innerHTML = '<span class="status-indicator live"></span> <span class="text-success">Conexión Binance 1.5s</span>';
        }
    }

    // 3. Tarjeta Tendencia Desacoplada (Nunca bloquear al usuario)
    if (data.is_training) {
        trendEl.innerText = data.status_msg || "Analizando 168h para entrenar Modelos...";
        trendEl.className = 'text-warning';
        predEl.innerText = '--';
        pctEl.innerText = '--';
        pctEl.className = 'text-muted';
    } else {
        trendEl.innerText = data.tendencia || "Analizado";
        trendEl.className = (data.tendencia && (data.tendencia.includes("Alza") || data.tendencia.includes("Subida"))) ? 'text-success' :
                           (data.tendencia && (data.tendencia.includes("Caída") || data.tendencia.includes("Bajada")) ? 'text-danger' : 'text-warning');

        if (data.prediccion_24h_usd && data.prediccion_24h_usd > 0) {
            predEl.innerText = `$${data.prediccion_24h_usd.toLocaleString('en-US', {minimumFractionDigits: 0})}`;
            pctEl.innerText = `${data.prediccion_24h_pct >= 0 ? '+' : ''}${data.prediccion_24h_pct.toFixed(2)}%`;
            pctEl.className = data.prediccion_24h_pct >= 0 ? 'text-success' : 'text-danger';
        }
    }

    // 4. Panel de Auditoría (No bloqueante)
    if (data.evaluacion) {
        try {
            updateAudit(data.evaluacion);
        } catch(e) {
            console.error("[V15 UI] Error pintando auditoría:", e);
        }
    }

    // 5. Pintar gráfico pase lo que pase
    if (data.chart_data) {
        try {
            updateChart(data.chart_data);
        } catch(e) {
            console.error("[V15 Chart] Error renderizando Canvas:", e);
        }
    }
}

async function fetchData() {
    try {
        const response = await fetch('/api/analysis');
        if (response.ok) {
            const data = await response.json();
            console.log("[V15 Debug] API Data recibida. is_training:", data.is_training, "| is_fallback:", data.is_fallback);
            updateUI(data);
        } else {
            console.error("[V15 API] HTTP Error:", response.status);
            document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Backend Error '+response.status+'</span>';
        }
    } catch (error) {
        console.error("[V15 Network] Fetch fallido:", error);
        document.getElementById('binanceStatus').innerHTML = '<span class="status-indicator error"></span> <span class="text-danger">Servidor Fuera de Línea</span>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("[V15] Inicializando aplicación Zero-Wait. Desacoplamiento de Módulos activo.");
    initChart();
    fetchData(); // Llamada inmediata
    setInterval(fetchData, 1500);
});
