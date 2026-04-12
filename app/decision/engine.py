def make_decision(current_price, predicted_24h_price, sentiment, onchain_flow):
    """Genera decisión BUY/SELL/HOLD basada en los datos actuales y predicciones"""

    # Calcular cambio porcentual esperado
    expected_change = ((predicted_24h_price - current_price) / current_price) * 100

    score = 0
    explanations = []

    # Factor Técnico (Predicción IA)
    if expected_change > 0.5:
        score += 2
        explanations.append(f"La IA predice una subida del {expected_change:.2f}% en 24h.")
    elif expected_change < -0.5:
        score -= 2
        explanations.append(f"La IA predice una caída del {abs(expected_change):.2f}% en 24h.")
    else:
        explanations.append("La IA predice que el precio se mantendrá estable.")

    # Factor Sentimiento
    if sentiment > 65:
        score += 1
        explanations.append("El sentimiento en redes es positivo (codicia).")
    elif sentiment < 35:
        score -= 1
        explanations.append("Hay miedo en el mercado según las redes.")

    # Factor On-chain
    if onchain_flow < -1000:
        score += 1
        explanations.append("Ballenas retirando fondos (presión alcista).")
    elif onchain_flow > 1000:
        score -= 1
        explanations.append("Fondos entrando a exchanges (posible venta).")

    # Decisión final
    if score >= 2:
        decision = "BUY"
        confianza = min(0.95, 0.6 + (score * 0.05))
        razon = "COMPRAR: " + " ".join(explanations)
    elif score <= -2:
        decision = "SELL"
        confianza = min(0.95, 0.6 + (abs(score) * 0.05))
        razon = "VENDER: " + " ".join(explanations)
    else:
        decision = "HOLD"
        confianza = 0.5
        razon = "MANTENER: " + " ".join(explanations)

    return decision, confianza, razon
