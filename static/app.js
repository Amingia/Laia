let chartInstance = null;

function initChart() {
    const ctx = document.getElementById('btcChart').getContext('2d');

    // Paleta estilo Binance
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
                    borderColor: '#fcd535', // Amarillo Binance
                    backgroundColor: 'rgba(252, 213, 53, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: 'Predicción IA',
                    data: [],
                    borderColor: '#0ecb81', // Verde subida
                    borderDash: [5, 5],
                    borderWidth: 2,
                    fill: false,
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
                legend: { position: 'top', align: 'end', labels: { boxWidth: 12, usePointStyle: true } },
                tooltip: {
                    backgroundColor: '#2b3139', titleColor: '#eaecef', bodyColor: '#eaecef',
                    borderColor: '#474d57', borderWidth: 1, padding: 10
                }
            },
            scales: {
                x: { grid: { color: '#2b3139', drawBorder: false } },
                y: { grid: { color: '#2b3139', drawBorder: false }, position: 'right' }
            },
            animation: { duration: 0 } // Desactivada para fluidez
        }
    });
}

function updateChart(history, predictions) {
    if (!chartInstance || !history || history.length === 0) return;

    const labels = [], realData = [], predData = [];

    // Llenar pasado
    for (let i = 0; i < history.length; i++) {
        labels.push(`H-${history.length - i}`);
        realData.push(history[i]);
        predData.push(null);
    }

    const currentPoint = history[history.length - 1];

    // Si hay predicción y no es igual a pasado, colorear rojo/verde
    if (predictions && predictions.length > 0) {
        predData[predData.length - 1] = currentPoint;

        // Cambiar color de la predicción según si predice subida o bajada respecto al precio actual
        const endPrice = predictions[predictions.length - 1];
        if (endPrice < currentPoint) {
            chartInstance.data.datasets[1].borderColor = '#f6465d'; // Rojo
        } else {
            chartInstance.data.datasets[1].borderColor = '#0ecb81'; // Verde
        }

        for (let i = 0; i < predictions.length; i++) {
            labels.push(`H+${i+1}`);
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
    // Rendimiento IA
    if (data.ia_accuracy !== undefined) {
        document.getElementById('iaAccuracy').innerText = `${data.ia_accuracy.toFixed(1)}%`;
        document.getElementById('iaTotalPred').innerText = `(${data.total_predictions} muestras)`;
    }

    // Precios USD
    if (data.precio_actual) {
        document.getElementById('currentPrice').innerText = `$ ${data.precio_actual.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }
    if (data.prediccion_24h) {
        document.getElementById('predictedPrice').innerText = `$ ${data.prediccion_24h.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }

    // Decisión
    if (data.decision) {
        const dBox = document.getElementById('decisionBox');
        const dSig = document.getElementById('decisionSignal');
        dBox.className = 'decision-box';

        if (data.decision === 'BUY') { dBox.classList.add('signal-buy'); dSig.innerText = 'COMPRAR'; }
        else if (data.decision === 'SELL') { dBox.classList.add('signal-sell'); dSig.innerText = 'VENDER'; }
        else { dBox.classList.add('signal-hold'); dSig.innerText = 'MANTENER'; }

        document.getElementById('decisionConf').innerText = `Confianza IA: ${(data.confianza * 100).toFixed(0)}%`;
        document.getElementById('decisionExp').innerText = data.explicacion;
    }

    // Simulador USD
    if (data.balance) {
        document.getElementById('simTotal').innerText = `$ ${data.balance.total_value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById('simUsd').innerText = `$ ${data.balance.balance_usd.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById('simBtc').innerText = `₿ ${data.balance.balance_btc.toFixed(6)}`;

        const profitBox = document.getElementById('profitBox');
        const profitUsdEl = document.getElementById('simProfitUsd');
        const profitEl = document.getElementById('simProfit');

        profitEl.innerText = `${data.balance.profit_percent.toFixed(2)}%`;
        profitUsdEl.innerText = `${data.balance.profit_loss >= 0 ? '+' : ''}$ ${data.balance.profit_loss.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

        profitBox.className = 'sim-box highlight-box';
        if (data.balance.profit_loss > 0) profitBox.classList.add('profit-positive');
        else if (data.balance.profit_loss < 0) profitBox.classList.add('profit-negative');

        const tbody = document.getElementById('historyBody');
        if (data.balance.history && data.balance.history.length > 0) {
            tbody.innerHTML = '';
            data.balance.history.forEach(op => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${op.time}</td>
                    <td class="${op.type.toLowerCase()}"><i class="fas ${op.type === 'COMPRA' ? 'fa-arrow-up' : 'fa-arrow-down'}"></i> ${op.type}</td>
                    <td>$ ${op.price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td>$ ${op.amount_usd.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td>₿ ${op.btc.toFixed(6)}</td>
                    <td class="fee">$ ${op.fee.toFixed(2)}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

    // Gráfico
    updateChart(data.history_prices, data.prediccion_horas);
}

async function fetchData() {
    try {
        const response = await fetch('/api/auto');
        if (response.ok) {
            const data = await response.json();
            updateUI(data);
        }
    } catch (error) {
        console.error("Error obteniendo datos:", error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchData();
    setInterval(fetchData, 5000); // El frontend consulta cada 5s, pero el backend usa caché
});
