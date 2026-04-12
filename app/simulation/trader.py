class TradingSimulator:
    def __init__(self, initial_balance=1000.0):
        self.initial_euro = initial_balance
        self.euro = initial_balance
        self.btc = 0.0
        self.history = []
        self.last_action_time = None

    def process_signal(self, action, price, timestamp):
        # Evitar operar más de una vez por minuto
        if self.last_action_time and (timestamp - self.last_action_time).total_seconds() < 60:
            return

        trade_executed = False

        if action == "BUY" and self.euro > 10:
            # Comprar usando el 50% del balance en euros
            amount_to_spend = self.euro * 0.5
            btc_bought = amount_to_spend / price
            self.euro -= amount_to_spend
            self.btc += btc_bought
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "COMPRA",
                "price": round(price, 2),
                "amount_eur": round(amount_to_spend, 2),
                "btc": round(btc_bought, 6)
            })

        elif action == "SELL" and self.btc > 0.0001:
            # Vender todos los BTC
            amount_to_receive = self.btc * price
            self.euro += amount_to_receive
            btc_sold = self.btc
            self.btc = 0
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "VENTA",
                "price": round(price, 2),
                "amount_eur": round(amount_to_receive, 2),
                "btc": round(btc_sold, 6)
            })

        if trade_executed:
            self.last_action_time = timestamp
            # Mantener solo últimas 10 operaciones
            if len(self.history) > 10:
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
            "history": self.history
        }
