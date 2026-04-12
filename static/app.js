let chartInstance = null;
let currentInterval = '1h';
let lastHistoryData = null;

// Envía cambio de modo al backend
document.getElementById('modeToggle').addEventListener('change', async (e) => {
    const isActive = e.target.checked;
    await fetch('/api/mode', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({active: isActive})
    });
});

// Cambia rango del gráfico
document.querySelectorAll('.range-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        currentInterval = e.target.dataset.range;
        fetchChartData();
    });
});

function initChart() {
    const ctx = document.getElementById('btcChart').getContext('2d');
    Chart.defaults.color = '#848e9c';
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Histórico (Real)',
                    data: [], // Será un array de objetos {x: timestamp, y: precio}
                    borderColor: '#fcd535',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: false
                },
                {
                    label: 'Predicción IA',
                    data: [], // Será un array de objetos {x: timestamp, y: precio}
                    borderColor: '#0ecb81',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', align: 'end' },
                tooltip: {
                    callbacks: {
                        title: (context) => {
                            const date = new Date(context[0].parsed.x);
                            return date.toLocaleString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
                        },
                        label: (context) => {
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
                            borderColor: 'rgba(255, 255, 255, 0.4)',
                            borderWidth: 1,
                            borderDash: [3, 3],
                            label: {
                                display: true,
                                content: 'AHORA',
                                position: 'end',
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                color: '#fff',
                                font: { size: 10 }
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: {
                            millisecond: 'HH:mm:ss',
                            second: 'HH:mm:ss',
                            minute: 'HH:mm',
                            hour: 'HH:mm',
                            day: 'MMM dd',
                            week: 'MMM dd',
                            month: 'MMM yyyy'
                        }
                    },
                    grid: { color: '#2b3139', drawBorder: false },
                    ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }
                },
                y: {
                    grid: { color: '#2b3139', drawBorder: false },
                    position: 'right',
                    ticks: {
                        callback: function(value) { return '$' + value.toLocaleString('en-US'); }
                    }
                }
            },
            animation: { duration: 0 }
        }
    });
}

function updateChart(chartDataRaw) {
    if (!chartInstance || !chartDataRaw || !chartDataRaw.history) return;

    const histPrices = chartDataRaw.history.prices;
    const histTimes = chartDataRaw.history.times;

    const predPrices = chartDataRaw.prediction.prices;
    const predTimes = chartDataRaw.prediction.times;

    const realDataFormatted = [];
    const predDataFormatted = [];

    // Cargar histórico real
    for (let i = 0; i < histPrices.length; i++) {
        realDataFormatted.push({ x: histTimes[i], y: histPrices[i] });
    }

    // Cargar predicción
    if (predPrices && predTimes && predPrices.length > 0) {
        const lastRealPoint = realDataFormatted[realDataFormatted.length - 1];
        predDataFormatted.push({ x: lastRealPoint.x, y: lastRealPoint.y }); // Conectar curva

        for (let i = 0; i < predPrices.length; i++) {
            if (i < predTimes.length) {
                predDataFormatted.push({ x: predTimes[i], y: predPrices[i] });
            }
        }

        // Colorear verde o rojo según la predicción
        const currentPrice = lastRealPoint.y;
        const endPrice = predPrices[predPrices.length - 1];
        chartInstance.data.datasets[1].borderColor = (endPrice < currentPrice) ? '#f6465d' : '#0ecb81';
    }

    // Actualizar línea de "AHORA"
    const nowTime = realDataFormatted.length > 0 ? realDataFormatted[realDataFormatted.length - 1].x : Date.now();
    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = nowTime;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = nowTime;

    chartInstance.data.datasets[0].data = realDataFormatted;
    chartInstance.data.datasets[1].data = predDataFormatted;

    chartInstance.update();
}

function updateUI(data) {
    // Top Info
    document.getElementById('marketStateTag').innerText = data.market_state;

    // KPIs
    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US')}`;

    const kpiSig = document.getElementById('kpiSignal');
    kpiSig.innerText = data.decision;
    kpiSig.className = data.decision === 'BUY' ? 'text-success' : (data.decision === 'SELL' ? 'text-danger' : 'text-warning');
    document.getElementById('kpiConf').innerText = `Conf: ${(data.confianza * 100).toFixed(0)}%`;

    if (data.ia_metrics) {
        document.getElementById('kpiAcc').innerText = `${data.ia_metrics.accuracy}%`;
        document.getElementById('kpiMae').innerText = `Error: $${data.ia_metrics.mae}`;

        document.getElementById('iaStability').innerText = data.ia_metrics.estabilidad;
        document.getElementById('iaStreak').innerText = data.ia_metrics.racha;
    }

    document.getElementById('decisionExp').innerText = data.explicacion;

    // Simulador
    if (data.balance) {
        document.getElementById('modeToggle').checked = data.balance.mode_active;

        document.getElementById('kpiBalance').innerText = `$${data.balance.total_value.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        const pnlEl = document.getElementById('kpiPnl');
        pnlEl.innerText = `${data.balance.profit_loss >= 0 ? '+' : ''}$${data.balance.profit_loss.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        pnlEl.className = data.balance.profit_loss >= 0 ? 'text-success' : 'text-danger';

        const tbody = document.getElementById('historyBody');
        if (data.balance.history && data.balance.history.length > 0) {
            tbody.innerHTML = '';
            // Mostrar solo las últimas 10
            const recentOps = data.balance.history.slice(0, 10);
            recentOps.forEach(op => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${op.time}</td>
                    <td class="${op.type.toLowerCase()}"><i class="fas ${op.type === 'COMPRA' ? 'fa-arrow-up' : 'fa-arrow-down'}"></i></td>
                    <td>$${op.price.toLocaleString('en-US', {minimumFractionDigits: 0})}</td>
                    <td class="${op.type.toLowerCase()}">${op.type === 'VENTA' ? '+' : '-'}$${op.amount_usd.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }
}

async function fetchChartData() {
    try {
        const res = await fetch(`/api/chart?interval=${currentInterval}`);
        if (res.ok) {
            const data = await res.json();
            lastHistoryData = data;
            updateChart(data);
        }
    } catch(e) {}
}

async function fetchData() {
    try {
        const response = await fetch('/api/auto');
        if (response.ok) {
            const data = await response.json();
            updateUI(data);
        }
    } catch (error) {
        console.error("Error API:", error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchChartData();
    fetchData();
    setInterval(fetchData, 5000);
    setInterval(fetchChartData, 15000);
});
