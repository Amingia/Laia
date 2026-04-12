let chartInstance = null;
let currentInterval = '1h';

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
        fetchChartData(); // Forzar actualización del gráfico
    });
});

function initChart() {
    const ctx = document.getElementById('btcChart').getContext('2d');
    Chart.defaults.color = '#848e9c';
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Precio Real',
                    data: [],
                    borderColor: '#fcd535',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: 'Predicción IA',
                    data: [],
                    borderColor: '#0ecb81',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', align: 'end' },
                annotation: { annotations: {} } // Para marcas de compra/venta
            },
            scales: {
                x: { grid: { color: '#2b3139', drawBorder: false } },
                y: { grid: { color: '#2b3139', drawBorder: false }, position: 'right' }
            },
            animation: { duration: 0 }
        }
    });
}

function renderAnnotations(history) {
    const annotations = {};
    if (!history) return annotations;

    // Solo mostramos las últimas operaciones (ej. del día) para no saturar
    history.forEach((op, index) => {
        // En una app real mapearíamos el timestamp exacto al index X.
        // Aquí lo simplificamos apuntando al último dato o aproximando.
        // Como simplificación visual para esta versión, ponemos una marca global
    });
    return annotations;
}

function updateChart(historicalData, predictions) {
    if (!chartInstance || !historicalData) return;

    const labels = [];
    const realData = [];
    const predData = [];

    const prices = historicalData.prices || historicalData;

    for (let i = 0; i < prices.length; i++) {
        labels.push(`-${prices.length - i}`);
        realData.push(prices[i]);
        predData.push(null);
    }

    const currentPoint = prices[prices.length - 1];

    if (predictions && predictions.length > 0) {
        predData[predData.length - 1] = currentPoint;
        const endPrice = predictions[predictions.length - 1];
        chartInstance.data.datasets[1].borderColor = (endPrice < currentPoint) ? '#f6465d' : '#0ecb81';

        for (let i = 0; i < predictions.length; i++) {
            labels.push(`+${i+1}`);
            realData.push(null);
            predData.push(predictions[i]);
        }
    }

    chartInstance.data.labels = labels;
    chartInstance.data.datasets[0].data = realData;
    chartInstance.data.datasets[1].data = predData;
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
        document.getElementById('iaSamples').innerText = data.ia_metrics.total;
    }

    if (data.prediccion_24h) {
        document.getElementById('iaPred24').innerText = `$${data.prediccion_24h.toLocaleString('en-US', {maximumFractionDigits: 0})}`;
    }

    document.getElementById('decisionExp').innerText = data.explicacion;

    // Simulador
    if (data.balance) {
        document.getElementById('modeToggle').checked = data.balance.mode_active;
        document.getElementById('simModeBadge').innerText = data.balance.mode_active ? "Simulación Activa" : "Modo Observación";

        document.getElementById('kpiBalance').innerText = `$${data.balance.total_value.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        const pnlEl = document.getElementById('kpiPnl');
        pnlEl.innerText = `${data.balance.profit_loss >= 0 ? '+' : ''}$${data.balance.profit_loss.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        pnlEl.className = data.balance.profit_loss >= 0 ? 'text-success' : 'text-danger';

        document.getElementById('simBtc').innerText = data.balance.balance_btc.toFixed(6);
        document.getElementById('simAvgPrice').innerText = `$${data.balance.average_buy_price.toLocaleString('en-US')}`;

        const openPnlEl = document.getElementById('simOpenPnl');
        openPnlEl.innerText = `$${data.balance.open_pnl.toLocaleString('en-US')} (${data.balance.open_pnl_pct}%)`;
        openPnlEl.className = data.balance.open_pnl > 0 ? 'text-success' : (data.balance.open_pnl < 0 ? 'text-danger' : '');

        document.getElementById('simTradesToday').innerText = data.balance.trades_today;

        const tbody = document.getElementById('historyBody');
        if (data.balance.history && data.balance.history.length > 0) {
            tbody.innerHTML = '';
            data.balance.history.forEach(op => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${op.time}</td>
                    <td class="${op.type.toLowerCase()}"><i class="fas ${op.type === 'COMPRA' ? 'fa-arrow-up' : 'fa-arrow-down'}"></i> ${op.type}</td>
                    <td>$${op.price.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    <td>$${op.amount_usd.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    <td class="fee">$${op.fee.toFixed(2)}</td>
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
            // Para mantener la predicción, la guardamos de la otra API temporalmente
            // En este loop no actualizamos la predicción, lo hace fetchData
            window.lastChartData = data;
        }
    } catch(e) {}
}

async function fetchData() {
    try {
        const response = await fetch('/api/auto');
        if (response.ok) {
            const data = await response.json();
            updateUI(data);

            // Si no tenemos datos del chart específico, usamos el que viene por defecto
            if (!window.lastChartData && currentInterval === '1h') {
                updateChart(data.history_prices, data.prediccion_horas);
            } else if (window.lastChartData) {
                updateChart(window.lastChartData.prices, data.prediccion_horas);
            }
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
    setInterval(fetchChartData, 15000); // Rango de gráfico se actualiza menos frecuente
});
