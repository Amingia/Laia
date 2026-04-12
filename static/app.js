let chartInstance = null;
let currentInterval = '1h';

// Envía cambio de modo al backend y actualiza etiqueta en vivo
document.getElementById('modeToggle').addEventListener('change', async (e) => {
    const isActive = e.target.checked;

    const label = document.getElementById('modeLabelText');
    if(isActive) {
        label.innerText = "Modo Activo (Usando cartera virtual)";
        label.style.color = "var(--success)";
    } else {
        label.innerText = "Modo Observación (La IA solo analiza)";
        label.style.color = "var(--text-light)";
    }

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
                    data: [],
                    borderColor: '#fcd535',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: false
                },
                {
                    label: 'Predicción IA',
                    data: [],
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
                        displayFormats: { millisecond: 'HH:mm', second: 'HH:mm', minute: 'HH:mm', hour: 'HH:mm', day: 'MMM dd', week: 'MMM dd', month: 'MMM yyyy' }
                    },
                    grid: { color: '#2b3139', drawBorder: false },
                    ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: '#2b3139', drawBorder: false },
                    position: 'right',
                    ticks: { callback: function(value) { return '$' + value.toLocaleString('en-US'); } }
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

    for (let i = 0; i < histPrices.length; i++) {
        realDataFormatted.push({ x: histTimes[i], y: histPrices[i] });
    }

    if (predPrices && predTimes && predPrices.length > 0) {
        const lastRealPoint = realDataFormatted[realDataFormatted.length - 1];
        predDataFormatted.push({ x: lastRealPoint.x, y: lastRealPoint.y });

        for (let i = 0; i < predPrices.length; i++) {
            if (i < predTimes.length) {
                predDataFormatted.push({ x: predTimes[i], y: predPrices[i] });
            }
        }

        const currentPrice = lastRealPoint.y;
        const endPrice = predPrices[predPrices.length - 1];
        chartInstance.data.datasets[1].borderColor = (endPrice < currentPrice) ? '#f6465d' : '#0ecb81';
    }

    const nowTime = realDataFormatted.length > 0 ? realDataFormatted[realDataFormatted.length - 1].x : Date.now();
    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = nowTime;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = nowTime;

    chartInstance.data.datasets[0].data = realDataFormatted;
    chartInstance.data.datasets[1].data = predDataFormatted;
    chartInstance.update();
}

function updateUI(data) {
    // Top Info
    document.getElementById('marketStateTag').innerText = data.market_state || "Evaluando";

    // KPIs Básicos
    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US')}`;

    // Decisión (Coloreado dinámico del fondo de la tarjeta)
    const kpiSigCard = document.getElementById('kpiSignalCard');
    const kpiSig = document.getElementById('kpiSignal');
    kpiSig.innerText = data.decision;
    kpiSigCard.className = 'kpi-card'; // Reset
    if(data.decision === 'BUY') {
        kpiSigCard.classList.add('bg-buy');
        kpiSig.className = 'text-success';
    } else if(data.decision === 'SELL') {
        kpiSigCard.classList.add('bg-sell');
        kpiSig.className = 'text-danger';
    } else {
        kpiSigCard.classList.add('bg-hold');
        kpiSig.className = 'text-warning';
    }
    document.getElementById('kpiConf').innerText = `Confianza: ${(data.confianza * 100).toFixed(0)}%`;

    // IA Precisión Simple
    if (data.ia_metrics) {
        document.getElementById('kpiAcc').innerText = `${data.ia_metrics.accuracy}%`;
        document.getElementById('kpiTotalSamples').innerText = `De ${data.ia_metrics.total} predicciones`;
    }

    // Razón IA explicada
    document.getElementById('decisionExp').innerText = data.explicacion;

    // Simulador y Cartera
    if (data.balance) {
        // Solo mostrar la tarjeta de balance si el simulador está activo o tiene saldo alterado
        const balanceCard = document.getElementById('kpiBalanceCard');
        if(data.balance.mode_active || data.balance.profit_loss !== 0) {
            balanceCard.style.display = 'block';
            document.getElementById('kpiBalance').innerText = `$${data.balance.total_value.toLocaleString('en-US', {minimumFractionDigits:2})}`;

            const pnlEl = document.getElementById('kpiPnl');
            pnlEl.innerText = `${data.balance.profit_loss >= 0 ? '+' : ''}$${data.balance.profit_loss.toLocaleString('en-US', {minimumFractionDigits:2})}`;
            pnlEl.className = data.balance.profit_loss >= 0 ? 'text-success' : 'text-danger';
        } else {
            balanceCard.style.display = 'none';
        }

        // Sincronizar el toggle visual
        document.getElementById('modeToggle').checked = data.balance.mode_active;
        const label = document.getElementById('modeLabelText');
        if(data.balance.mode_active) {
            label.innerText = "Modo Activo (Usando cartera virtual)";
            label.style.color = "var(--success)";
        } else {
            label.innerText = "Modo Observación (La IA solo analiza)";
            label.style.color = "var(--text-muted)";
        }

        // Tabla Dinámica o Empty State
        const emptyState = document.getElementById('emptyStateMsg');
        const historyContainer = document.getElementById('historyContainer');
        const tbody = document.getElementById('historyBody');

        if (data.balance.history && data.balance.history.length > 0) {
            emptyState.style.display = 'none';
            historyContainer.style.display = 'block';

            tbody.innerHTML = '';
            // Mostrar últimas 10
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
        } else {
            emptyState.style.display = 'block';
            historyContainer.style.display = 'none';
        }
    }
}

async function fetchChartData() {
    try {
        const res = await fetch(`/api/chart?interval=${currentInterval}`);
        if (res.ok) {
            const data = await res.json();
            window.lastChartData = data;
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
            if (window.lastChartData) {
                // Actualizamos las predicciones futuras sobre el gráfico base
                window.lastChartData.prediction.prices = data.prediccion_horas;
                updateChart(window.lastChartData);
            }
        }
    } catch (error) {}
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchChartData();
    fetchData();
    setInterval(fetchData, 5000);
    setInterval(fetchChartData, 15000);
});
