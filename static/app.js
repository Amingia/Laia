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
                    label: 'Histórico (Real)',
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
                    label: 'Predicción IA',
                    data: [],
                    borderColor: '#0ecb81',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: false,
                    order: 1
                },
                {
                    // Banda Superior
                    label: 'Banda Superior',
                    data: [],
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(14, 203, 129, 0.1)', // Se actualizará color dinámicamente
                    fill: '+1', // Rellena hasta el siguiente dataset (banda inferior)
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    order: 3,
                    tension: 0.2
                },
                {
                    // Banda Inferior
                    label: 'Banda Inferior',
                    data: [],
                    borderColor: 'transparent',
                    backgroundColor: 'transparent',
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    order: 4,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top', align: 'end',
                    labels: { filter: function(item, chart) { return !item.text.includes('Banda'); } }
                },
                tooltip: {
                    callbacks: {
                        title: (context) => {
                            const date = new Date(context[0].parsed.x);
                            return date.toLocaleString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
                        },
                        label: (context) => {
                            if(context.dataset.label.includes('Banda')) return null; // No mostrar las bandas en el tooltip
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

function updateChart(histData, predData) {
    if (!chartInstance || !histData || !histData.prices || histData.prices.length === 0) return;

    const realDataFormatted = [];
    const predDataFormatted = [];
    const upperDataFormatted = [];
    const lowerDataFormatted = [];

    // Cargar Histórico
    for (let i = 0; i < histData.prices.length; i++) {
        realDataFormatted.push({ x: histData.times[i], y: histData.prices[i] });
    }

    const lastRealPoint = realDataFormatted[realDataFormatted.length - 1];

    // Cargar Predicción y Bandas
    if (predData && predData.prices && predData.prices.length > 0) {
        predDataFormatted.push({ x: lastRealPoint.x, y: lastRealPoint.y });
        upperDataFormatted.push({ x: lastRealPoint.x, y: lastRealPoint.y });
        lowerDataFormatted.push({ x: lastRealPoint.x, y: lastRealPoint.y });

        for (let i = 0; i < predData.prices.length; i++) {
            if (i < predData.times.length) {
                const t = predData.times[i];
                predDataFormatted.push({ x: t, y: predData.prices[i] });
                upperDataFormatted.push({ x: t, y: predData.upper_bound[i] });
                lowerDataFormatted.push({ x: t, y: predData.lower_bound[i] });
            }
        }

        const currentPrice = lastRealPoint.y;
        const endPrice = predData.prices[predData.prices.length - 1];
        const isBullish = endPrice >= currentPrice;

        chartInstance.data.datasets[1].borderColor = isBullish ? '#0ecb81' : '#f6465d';
        chartInstance.data.datasets[2].backgroundColor = isBullish ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';
    }

    const nowTime = lastRealPoint.x;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMin = nowTime;
    chartInstance.options.plugins.annotation.annotations.nowLine.xMax = nowTime;

    chartInstance.data.datasets[0].data = realDataFormatted;
    chartInstance.data.datasets[1].data = predDataFormatted;
    chartInstance.data.datasets[2].data = upperDataFormatted;
    chartInstance.data.datasets[3].data = lowerDataFormatted;

    chartInstance.update();
}

function updateUI(data) {
    if (!data.precio_actual || data.precio_actual === 0) return; // Evitar renderizar vacíos

    // KPIs Básicos
    document.getElementById('kpiPrice').innerText = `$${data.precio_actual.toLocaleString('en-US')}`;

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

    if (data.ia_metrics) {
        document.getElementById('kpiAcc').innerText = `${data.ia_metrics.accuracy}%`;
        document.getElementById('kpiTotalSamples').innerText = `Basado en ${data.ia_metrics.total} eval.`;
    }

    document.getElementById('decisionExp').innerText = data.explicacion;

    // Cartera y Operaciones
    if (data.balance) {
        document.getElementById('kpiBalance').innerText = `$${data.balance.total_value.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        const pnlEl = document.getElementById('kpiPnl');
        pnlEl.innerText = `${data.balance.profit_loss >= 0 ? '+' : ''}$${data.balance.profit_loss.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        pnlEl.className = data.balance.profit_loss >= 0 ? 'text-success' : 'text-danger';

        const emptyState = document.getElementById('emptyStateMsg');
        const historyContainer = document.getElementById('historyContainer');
        const tbody = document.getElementById('historyBody');

        if (data.balance.history && data.balance.history.length > 0) {
            emptyState.style.display = 'none';
            historyContainer.style.display = 'block';

            tbody.innerHTML = '';
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

    if(data.chart_data) {
        updateChart(data.chart_data.history, data.chart_data.prediction);
    }
}

async function fetchData() {
    try {
        const response = await fetch('/api/auto');
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
    fetchData(); // Carga inicial
    setInterval(fetchData, 5000); // Refresco constante
});
