class TradingSimulator:
    def __init__(self, initial_balance=1000.0):
        self.initial_euro = initial_balance
        self.euro = initial_balance
        self.btc = 0.0
        self.history = []
        self.last_action_time = None
        self.fee_rate = 0.001 # 0.1% de comisión por operación
        self.cooldown_seconds = 180 # 3 minutos de cooldown
        self.total_fees_paid = 0.0

    def process_signal(self, action, price, timestamp):
        # Enfriamiento: no operar si no ha pasado el cooldown
        if self.last_action_time and (timestamp - self.last_action_time).total_seconds() < self.cooldown_seconds:
            return

        trade_executed = False

        if action == "BUY" and self.euro > 50:
            # Comprar usando el 50% del balance en euros
            amount_to_spend = self.euro * 0.5
            fee = amount_to_spend * self.fee_rate
            net_amount = amount_to_spend - fee

            btc_bought = net_amount / price

            self.euro -= amount_to_spend
            self.btc += btc_bought
            self.total_fees_paid += fee
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "COMPRA",
                "price": round(price, 2),
                "amount_eur": round(amount_to_spend, 2),
                "btc": round(btc_bought, 6),
                "fee": round(fee, 2)
            })

        elif action == "SELL" and self.btc > 0.0005: # Mínimo a vender
            # Vender todos los BTC
            gross_receive = self.btc * price
            fee = gross_receive * self.fee_rate
            net_receive = gross_receive - fee

            self.euro += net_receive
            btc_sold = self.btc
            self.btc = 0
            self.total_fees_paid += fee
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "VENTA",
                "price": round(price, 2),
                "amount_eur": round(net_receive, 2),
                "btc": round(btc_sold, 6),
                "fee": round(fee, 2)
            })

        if trade_executed:
            self.last_action_time = timestamp
            # Mantener solo últimas 20 operaciones
            if len(self.history) > 20:
                self.history.pop()

    def get_portfolio_value(self, current_price):
        return self.euro + (self.btc * current_price)

    def get_stats(self, current_price):
        if current_price == 0:
            return None

        total_value = self.get_portfolio_value(current_price)
        profit_loss = total_value - self.initial_euro
        profit_percent = (profit_loss / self.initial_euro) * 100

        return {
            "balance_euro": round(self.euro, 2),
            "balance_btc": round(self.btc, 6),
            "total_value": round(total_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_percent": round(profit_percent, 2),
            "fees_paid": round(self.total_fees_paid, 2),
            "history": self.history
        }
