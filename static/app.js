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
                    borderDash: [4, 4],
                    borderWidth: 2,
                    tension: 0.4, // Curva suavizada y realista
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: false,
                    order: 1
                },
                {
                    label: 'Límite Superior',
                    data: [],
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(14, 203, 129, 0.1)', // Sombreado
                    fill: '+1',
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    order: 3,
                    tension: 0.4
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
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false }, // Ocultamos la nativa porque hicimos una HTML custom
                tooltip: {
                    backgroundColor: 'rgba(24, 26, 32, 0.95)',
                    titleColor: '#eaecef',
                    bodyColor: '#eaecef',
                    borderColor: '#2b3139',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { size: 13, weight: 'normal' },
                    bodyFont: { size: 14, weight: 'bold' },
                    callbacks: {
                        title: (context) => {
                            const date = new Date(context[0].parsed.x);
                            return date.toLocaleString('es-ES', { weekday: 'long', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
                        },
                        label: (context) => {
                            if(context.dataset.label.includes('Límite')) return null; // No saturar el tooltip
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
                            borderColor: 'rgba(255, 255, 255, 0.5)',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            label: {
                                display: true,
                                content: 'PRECIO ACTUAL',
                                position: 'start',
                                backgroundColor: 'rgba(43, 49, 57, 0.8)',
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
                    time: {
                        displayFormats: { hour: 'HH:mm', day: 'MMM dd' },
                        tooltipFormat: 'dd MMM, HH:mm'
                    },
                    grid: { color: '#2b3139', drawBorder: false, tickLength: 0 },
                    ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12, font: {size: 11} }
                },
                y: {
                    grid: { color: '#1f2329', drawBorder: false },
                    position: 'right',
                    ticks: {
                        font: {size: 11},
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

    // Cargar Histórico (Últimos 48 puntos para mejor foco visual)
    const viewLimit = 48;
    const startIndex = Math.max(0, histData.prices.length - viewLimit);

    for (let i = startIndex; i < histData.prices.length; i++) {
        realDataFormatted.push({ x: histData.times[i], y: histData.prices[i] });
    }

    const lastRealPoint = realDataFormatted[realDataFormatted.length - 1];

    // Cargar Predicción a futuro
    if (predData && predData.prices && predData.prices.length > 0) {

        // Empalmamos el punto actual exacto en la predicción y en las bandas de confianza para dar continuidad sin salto
        const nowTime = lastRealPoint.x;
        const nowPrice = lastRealPoint.y;

        predDataFormatted.push({ x: nowTime, y: nowPrice });
        upperDataFormatted.push({ x: nowTime, y: nowPrice });
        lowerDataFormatted.push({ x: nowTime, y: nowPrice });

        for (let i = 0; i < predData.prices.length; i++) {
            if (i < predData.times.length) {
                const t = predData.times[i];
                predDataFormatted.push({ x: t, y: predData.prices[i] });
                upperDataFormatted.push({ x: t, y: predData.upper_bound[i] });
                lowerDataFormatted.push({ x: t, y: predData.lower_bound[i] });
            }
        }

        // El color de la predicción y su banda se ajusta dinámicamente si es subida o bajada a 24h
        const endPrice = predData.prices[predData.prices.length - 1];
        const isBullish = endPrice >= nowPrice;

        chartInstance.data.datasets[1].borderColor = isBullish ? '#0ecb81' : '#f6465d';
        chartInstance.data.datasets[2].backgroundColor = isBullish ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';

        // Reflejar colores en la leyenda HTML Custom
        document.querySelector('.color-box.pred').style.backgroundColor = isBullish ? '#0ecb81' : '#f6465d';
        document.querySelector('.color-box.band').style.backgroundColor = isBullish ? 'rgba(14, 203, 129, 0.2)' : 'rgba(246, 70, 93, 0.2)';
        document.querySelector('.color-box.band').style.borderColor = isBullish ? '#0ecb81' : '#f6465d';
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

    // Precio en vivo
    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    // Tarjeta Tendencia
    const trendEl = document.getElementById('kpiTrend');
    trendEl.innerText = data.tendencia || "Analizando...";

    if (data.tendencia && data.tendencia.includes("Alza") || data.tendencia.includes("Subida")) {
        trendEl.className = 'text-success';
    } else if (data.tendencia && data.tendencia.includes("Caída") || data.tendencia.includes("Bajada")) {
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

    // Validación Real (Excel)
    if (data.evaluacion && data.evaluacion.total_evals > 0) {
        document.getElementById('kpiAccEmpty').style.display = 'none';
        document.getElementById('kpiAccData').style.display = 'block';

        document.getElementById('kpiAccuracy').innerText = `${data.evaluacion.accuracy_pct}%`;
        document.getElementById('kpiMae').innerText = `${data.evaluacion.mae_pct.toFixed(2)}%`;
        document.getElementById('kpiEvals').innerText = data.evaluacion.total_evals;
    } else {
        document.getElementById('kpiAccEmpty').style.display = 'flex';
        document.getElementById('kpiAccData').style.display = 'none';
    }

    // Actualizar gráfico
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
        }
    } catch (error) {
        console.error("Error obteniendo datos API:", error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchData(); // Carga Inmediata
    // Polling rápido: el backend también hace polling rápido a Binance y cacheadas las curvas. Esto da sensación de vivo extremo.
    setInterval(fetchData, 2000);
});
