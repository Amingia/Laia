from app.data.fetcher import determine_market_state

def make_decision(current_price, predicted_24h_price, sentiment, onchain_flow, volatility, momentum, sma_c, sma_m, acc):
    """
    Motor v4: Explicaciones amigables y soporte para identificar el estado del mercado.
    """
    expected_change = ((predicted_24h_price - current_price) / current_price) * 100
    net_expected = expected_change - 0.2

    score = 0
    confirmations = 0

    # Determinar contexto general
    market_state = determine_market_state(sma_c, sma_m, momentum, acc)

    # 1. IA Técnico
    if net_expected > 1.0:
        score += 2
        confirmations += 1
        ia_text = f"La IA proyecta una ganancia clara ({net_expected:.1f}% neto)"
    elif net_expected < -1.0:
        score -= 2
        confirmations += 1
        ia_text = f"La IA prevé una caída del mercado ({net_expected:.1f}% neto)"
    else:
        ia_text = "La IA no detecta un margen de ganancia suficiente (<1% neto)"

    # 2. Contexto Corto Plazo
    if market_state.startswith("Alcista"):
        score += 1
        confirmations += 1
        ctx_text = f"el mercado está {market_state.lower()}"
    elif market_state.startswith("Bajista"):
        score -= 1
        confirmations += 1
        ctx_text = f"el mercado está {market_state.lower()}"
    else:
        ctx_text = "el mercado está lateral (sin fuerza clara)"

    # 3. Flujo y Sentimiento (Filtro final)
    vol_text = "con alta volatilidad" if volatility > 2.0 else "con volumen estable"

    # Lógica Final
    if score >= 3 and confirmations >= 2:
        decision = "BUY"
        confianza = min(0.99, 0.7 + (score * 0.05))
        if market_state == "Lateral / Indecisión":
            # Override si es lateral, mejor no operar
            decision = "HOLD"
            razon = f"Se recomienda MANTENER. Aunque {ia_text.lower()}, {ctx_text} y es arriesgado comprar ahora."
        else:
            razon = f"Se recomienda COMPRAR porque {ctx_text} {vol_text}, y {ia_text.lower()}."

    elif score <= -3 and confirmations >= 2:
        decision = "SELL"
        confianza = min(0.99, 0.7 + (abs(score) * 0.05))
        razon = f"Se recomienda VENDER porque {ctx_text}, y {ia_text.lower()}."
    else:
        decision = "HOLD"
        confianza = 0.5
        razon = f"Se recomienda MANTENER. {ia_text}, y además {ctx_text}."

    return decision, confianza, razon, market_state
