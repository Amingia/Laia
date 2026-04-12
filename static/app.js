let chartInstance = null;

function initChart() {
    const ctx = document.getElementById('btcChart').getContext('2d');

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Precio Real',
                    data: [],
                    borderColor: '#2962ff',
                    backgroundColor: 'rgba(41, 98, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Predicción IA',
                    data: [],
                    borderColor: '#ff9100',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e0e0e0' }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#888888' },
                    grid: { color: '#333333' }
                },
                y: {
                    ticks: { color: '#888888' },
                    grid: { color: '#333333' }
                }
            },
            animation: {
                duration: 0 // Desactivar animación para actualizaciones fluidas
            }
        }
    });
}

function updateChart(history, predictions) {
    if (!chartInstance || !history || history.length === 0) return;

    const labels = [];
    const realData = [];
    const predData = [];

    // Llenar datos pasados
    for (let i = 0; i < history.length; i++) {
        labels.push(`H-${history.length - i}`);
        realData.push(history[i]);
        predData.push(null); // No hay predicción para el pasado en el gráfico principal
    }

    // El punto de unión actual
    const currentPoint = history[history.length - 1];

    // Si hay predicciones, añadirlas
    if (predictions && predictions.length > 0) {
        // Enlazar la predicción con el último punto real para continuidad
        predData[predData.length - 1] = currentPoint;

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
    // 1. Precios
    if (data.precio_actual) {
        document.getElementById('currentPrice').innerText = `€ ${data.precio_actual.toFixed(2)}`;
    }
    if (data.prediccion_24h) {
        document.getElementById('predictedPrice').innerText = `€ ${data.prediccion_24h.toFixed(2)}`;
    }

    // 2. Decisión
    if (data.decision) {
        const dBox = document.getElementById('decisionBox');
        const dSig = document.getElementById('decisionSignal');

        dBox.className = 'decision-box'; // Reset

        if (data.decision === 'BUY') {
            dBox.classList.add('signal-buy');
            dSig.innerText = 'COMPRAR';
        } else if (data.decision === 'SELL') {
            dBox.classList.add('signal-sell');
            dSig.innerText = 'VENDER';
        } else {
            dBox.classList.add('signal-hold');
            dSig.innerText = 'MANTENER';
        }

        document.getElementById('decisionConf').innerText = `Confianza IA: ${(data.confianza * 100).toFixed(0)}%`;
        document.getElementById('decisionExp').innerText = data.explicacion;
    }

    // 3. Simulador
    if (data.balance) {
        document.getElementById('simTotal').innerText = `€ ${data.balance.total_value.toFixed(2)}`;
        document.getElementById('simEur').innerText = `€ ${data.balance.balance_euro.toFixed(2)}`;
        document.getElementById('simBtc').innerText = `₿ ${data.balance.balance_btc.toFixed(6)}`;

        const profitEl = document.getElementById('simProfit');
        profitEl.innerText = `${data.balance.profit_percent.toFixed(2)}%`;
        profitEl.className = data.balance.profit_percent >= 0 ? 'profit-positive' : 'profit-negative';

        // Historial
        const tbody = document.getElementById('historyBody');
        if (data.balance.history && data.balance.history.length > 0) {
            tbody.innerHTML = '';
            data.balance.history.forEach(op => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${op.time}</td>
                    <td class="${op.type.toLowerCase()}">${op.type}</td>
                    <td>€ ${op.price.toFixed(2)}</td>
                    <td>€ ${op.amount_eur.toFixed(2)}</td>
                    <td>₿ ${op.btc.toFixed(6)}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

    // 4. Actualizar Gráfico
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

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    // Primera carga
    fetchData();
    // Actualización cada 5 segundos
    setInterval(fetchData, 5000);
});
