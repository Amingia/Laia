class TradingSimulator:
    def __init__(self, initial_balance=1000.0):
        self.initial_usd = initial_balance
        self.usd = initial_balance
        self.btc = 0.0
        self.history = []
        self.last_action_time = None
        self.fee_rate = 0.001 # 0.1% de comisión por operación en Binance
        self.cooldown_seconds = 180 # 3 minutos de cooldown
        self.total_fees_paid = 0.0

    def process_signal(self, action, price, timestamp):
        # Enfriamiento (Cooldown)
        if self.last_action_time and (timestamp - self.last_action_time).total_seconds() < self.cooldown_seconds:
            return

        trade_executed = False

        # Solo comprar si tenemos al menos 50 USD
        if action == "BUY" and self.usd > 50:
            amount_to_spend = self.usd * 0.95 # Usa el 95% del capital disponible
            fee = amount_to_spend * self.fee_rate
            net_amount = amount_to_spend - fee

            btc_bought = net_amount / price

            self.usd -= amount_to_spend
            self.btc += btc_bought
            self.total_fees_paid += fee
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "COMPRA",
                "price": round(price, 2),
                "amount_usd": round(amount_to_spend, 2),
                "btc": round(btc_bought, 6),
                "fee": round(fee, 2)
            })

        # Solo vender si el valor en USD del BTC es mayor a 10$
        elif action == "SELL" and (self.btc * price) > 10.0:
            gross_receive = self.btc * price
            fee = gross_receive * self.fee_rate
            net_receive = gross_receive - fee

            self.usd += net_receive
            btc_sold = self.btc
            self.btc = 0
            self.total_fees_paid += fee
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "VENTA",
                "price": round(price, 2),
                "amount_usd": round(net_receive, 2),
                "btc": round(btc_sold, 6),
                "fee": round(fee, 2)
            })

        if trade_executed:
            self.last_action_time = timestamp
            if len(self.history) > 20:
                self.history.pop()

    def get_portfolio_value(self, current_price):
        return self.usd + (self.btc * current_price)

    def get_stats(self, current_price):
        if current_price == 0:
            return None

        total_value = self.get_portfolio_value(current_price)
        profit_loss = total_value - self.initial_usd
        profit_percent = (profit_loss / self.initial_usd) * 100

        return {
            "balance_usd": round(self.usd, 2),
            "balance_btc": round(self.btc, 6),
            "total_value": round(total_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_percent": round(profit_percent, 2),
            "fees_paid": round(self.total_fees_paid, 2),
            "history": self.history
        }
