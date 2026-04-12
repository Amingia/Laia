from datetime import datetime, date

class TradingSimulator:
    def __init__(self, initial_balance=1000.0):
        self.initial_usd = initial_balance
        self.usd = initial_balance
        self.btc = 0.0
        self.history = []
        self.last_action_time = None
        self.fee_rate = 0.001
        self.cooldown_seconds = 180
        self.total_fees_paid = 0.0
        self.average_buy_price = 0.0

        # Modo activo (True) vs Observación (False)
        self.is_active = False

        # Operaciones del día
        self.today = date.today()
        self.trades_today = 0

    def set_mode(self, is_active):
        self.is_active = is_active

    def _check_new_day(self):
        current = date.today()
        if current != self.today:
            self.today = current
            self.trades_today = 0

    def process_signal(self, action, price, timestamp):
        # Si estamos en modo observación, no hacemos nada con la cartera real (simulada)
        if not self.is_active:
            return

        self._check_new_day()

        if self.last_action_time and (timestamp - self.last_action_time).total_seconds() < self.cooldown_seconds:
            return

        trade_executed = False

        if action == "BUY" and self.usd > 50:
            amount_to_spend = self.usd * 0.95
            fee = amount_to_spend * self.fee_rate
            net_amount = amount_to_spend - fee

            btc_bought = net_amount / price

            # Recalcular precio medio de compra
            total_btc_cost = (self.average_buy_price * self.btc) + amount_to_spend
            self.usd -= amount_to_spend
            self.btc += btc_bought

            if self.btc > 0:
                self.average_buy_price = total_btc_cost / self.btc

            self.total_fees_paid += fee
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "COMPRA",
                "price": round(price, 2),
                "amount_usd": round(amount_to_spend, 2),
                "btc": round(btc_bought, 6),
                "fee": round(fee, 2),
                "timestamp": timestamp.timestamp()
            })

        elif action == "SELL" and (self.btc * price) > 10.0:
            gross_receive = self.btc * price
            fee = gross_receive * self.fee_rate
            net_receive = gross_receive - fee

            self.usd += net_receive
            btc_sold = self.btc
            self.btc = 0
            self.average_buy_price = 0.0 # Reset

            self.total_fees_paid += fee
            trade_executed = True

            self.history.insert(0, {
                "time": timestamp.strftime("%H:%M:%S"),
                "type": "VENTA",
                "price": round(price, 2),
                "amount_usd": round(net_receive, 2),
                "btc": round(btc_sold, 6),
                "fee": round(fee, 2),
                "timestamp": timestamp.timestamp()
            })

        if trade_executed:
            self.last_action_time = timestamp
            self.trades_today += 1
            if len(self.history) > 30: # Guardar hasta 30 operaciones para los gráficos
                self.history.pop()

    def get_portfolio_value(self, current_price):
        return self.usd + (self.btc * current_price)

    def get_stats(self, current_price):
        if current_price == 0: return None

        total_value = self.get_portfolio_value(current_price)
        profit_loss = total_value - self.initial_usd
        profit_percent = (profit_loss / self.initial_usd) * 100

        # Rentabilidad de la posición abierta actual
        open_pnl = 0.0
        open_pnl_pct = 0.0
        if self.btc > 0 and self.average_buy_price > 0:
            open_pnl = (current_price - self.average_buy_price) * self.btc
            open_pnl_pct = ((current_price - self.average_buy_price) / self.average_buy_price) * 100

        self._check_new_day()

        return {
            "mode_active": self.is_active,
            "balance_usd": round(self.usd, 2),
            "balance_btc": round(self.btc, 6),
            "total_value": round(total_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_percent": round(profit_percent, 2),
            "fees_paid": round(self.total_fees_paid, 2),
            "average_buy_price": round(self.average_buy_price, 2),
            "open_pnl": round(open_pnl, 2),
            "open_pnl_pct": round(open_pnl_pct, 2),
            "trades_today": self.trades_today,
            "history": self.history
        }
