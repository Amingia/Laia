def make_decision(current_price, predicted_24h_price, sentiment, onchain_flow, volatility, momentum):
    """
    Genera decisión BUY/SELL/HOLD basada en confirmaciones fuertes.
    Evita operaciones innecesarias si no hay rentabilidad clara.
    """

    # Calcular cambio porcentual neto esperado (restando comisiones del 0.2% total ida y vuelta)
    expected_change = ((predicted_24h_price - current_price) / current_price) * 100
    net_expected = expected_change - 0.2

    score = 0
    confirmations = 0
    explanations = []

    # 1. Factor Técnico (Predictor) - Exige >1% neto para operar
    if net_expected > 1.0:
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
    if momentum > 0.3:
        score += 1
        confirmations += 1
        explanations.append("Tendencia corta positiva (alcista).")
    elif momentum < -0.3:
        score -= 1
        confirmations += 1
        explanations.append("Tendencia corta negativa (bajista).")

    # 3. Factor Sentimiento
    if sentiment > 65:
        score += 1
        explanations.append("Fuerte sentimiento alcista en mercado.")
    elif sentiment < 35:
        score -= 1
        explanations.append("Fuerte sentimiento bajista en mercado.")

    # 4. Factor On-chain
    if onchain_flow < -50000:
        score += 1
        explanations.append("Salidas masivas de exchanges (acumulación).")
    elif onchain_flow > 50000:
        score -= 1
        explanations.append("Entradas masivas a exchanges (posible venta).")

    # Decisión final requiere Puntuación Alta (>=3) y Confirmación Múltiple (>=2)
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
