def make_decision(current_price, predicted_24h_price, sentiment, onchain_flow, volatility, momentum):
    """Genera decisión BUY/SELL/HOLD basada en múltiples confirmaciones y evita el ruido"""

    # Calcular cambio porcentual neto esperado (restando comisiones futuras de compra/venta = 0.2%)
    expected_change = ((predicted_24h_price - current_price) / current_price) * 100
    net_expected = expected_change - 0.2

    score = 0
    confirmations = 0
    explanations = []

    # 1. Factor Técnico / Predictivo (PESO ALTO)
    if net_expected > 1.0: # Umbral alto para evitar sobre-operar
        score += 2
        confirmations += 1
        explanations.append(f"Predicción IA alcista (+{expected_change:.2f}%).")
    elif net_expected < -1.0:
        score -= 2
        confirmations += 1
        explanations.append(f"Predicción IA bajista ({expected_change:.2f}%).")
    else:
        explanations.append("El margen de ganancia predicho es demasiado bajo (< 1% neto).")

    # 2. Factor Tendencia Corta (Momentum)
    if momentum > 0.5:
        score += 1
        confirmations += 1
        explanations.append("Tendencia a corto plazo positiva.")
    elif momentum < -0.5:
        score -= 1
        confirmations += 1
        explanations.append("Tendencia a corto plazo negativa.")

    # 3. Factor Sentimiento
    if sentiment > 60:
        score += 1
        explanations.append("Fuerte sentimiento alcista.")
    elif sentiment < 40:
        score -= 1
        explanations.append("Sentimiento bajista predominante.")

    # 4. Factor On-chain
    if onchain_flow < -1000:
        score += 1
        explanations.append("Salidas en cadena (compras institucionales).")
    elif onchain_flow > 1000:
        score -= 1
        explanations.append("Entradas en cadena (riesgo de volcado).")

    # Decisión final requiere Puntuación y Confirmación múltiple (evita señales débiles)
    if score >= 3 and confirmations >= 2:
        decision = "BUY"
        confianza = min(0.99, 0.7 + (score * 0.05))
        razon = "COMPRAR porque hay confirmación múltiple: " + " ".join(explanations)
    elif score <= -3 and confirmations >= 2:
        decision = "SELL"
        confianza = min(0.99, 0.7 + (abs(score) * 0.05))
        razon = "VENDER porque hay confirmación múltiple: " + " ".join(explanations)
    else:
        decision = "HOLD"
        confianza = 0.5
        razon = "MANTENER (Falta de confirmación clara). " + " ".join(explanations)

    return decision, confianza, razon
