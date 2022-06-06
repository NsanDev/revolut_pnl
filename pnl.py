from collections import OrderedDict, defaultdict

class Trade:
    def __init__(self, tradetime, symbol, quantity, fee, currency, price, is_close=False, id=''):
        self.tradetime = tradetime
        self.symbol = symbol
        self.quantity = quantity
        self.fee_opening = fee
        self.fee = fee
        self.currency = currency
        self.price = price
        self.is_close = is_close
        self.id = id

    def copy(self):
        obj = type(self).__new__(self.__class__)
        obj.__dict__.update(self.__dict__)
        return obj

    def is_long(self):
        return self.quantity >= 0 and not self.is_close

    def is_short(self):
        return self.quantity <= 0 and not self.is_close

    def is_close_long(self):
        return self.quantity < 0 and self.is_close

    def is_close_short(self):
        return self.quantity > 0 and self.is_close

class NetPosition:
    def __init__(self, tradetime, symbol, quantity, fee, currency, price, is_close=False, id=''):
        self.symbol = symbol
        self.quantity = quantity


class PnL:
    def __init__(self, close_order):
        self.close_order = close_order
        self.closed_trades = []

    def calculate(self):
        return - (sum(t.quantity * t.price for t in self.closed_trades) + self.close_order.quantity * self.close_order.price)

    def get_fees(self):
        return sum(t.fee for t in self.closed_trades) + self.close_order.fee


class Manager:

    def __init__(self):
        self.order_history = defaultdict(OrderedDict)  # collection of ordered dict

    def order(self, tradetime, symbol, quantity, fee, currency, price):
        self.order_history[symbol][tradetime] = Trade(tradetime, symbol, quantity, fee, currency, price, is_close=False)

    def close(self, tradetime, symbol, quantity, fee, currency, price):
        self.order_history[symbol][tradetime] = Trade(tradetime, symbol, quantity, fee, currency, price, is_close=True)

    def _get_pnl(self, symbol):
        if symbol not in self.order_history:
            return 0
        longs = [T.copy() for _, T in self.order_history[symbol].items() if T.is_long()]
        close_longs = [T.copy() for _, T in self.order_history[symbol].items() if T.is_close_long()]

        shorts = [T.copy() for _, T in self.order_history[symbol].items() if T.is_short()]
        close_shorts = [T.copy() for _, T in self.order_history[symbol].items() if T.is_close_short()]

        def calculate(close_order, open_trades):
            q_target = abs(close_order.quantity)
            sign = 1 if close_order.quantity < 0 else -1
            pnl = PnL(close_order)
            while q_target > 0 and len(open_trades) > 0:
                q = abs(open_trades[0].quantity)
                if q <= q_target:
                    pnl.closed_trades.append(open_trades.pop(0))
                if q > q_target:
                    t = open_trades[0].copy()
                    t.quantity = sign * q_target
                    fraction_fee = abs(q_target) / abs(q)
                    assert fraction_fee <= 1
                    assert fraction_fee >= 0
                    t.fee *= fraction_fee
                    open_trades[0].fee *= (1-fraction_fee)
                    pnl.closed_trades.append(t)
                    open_trades[0].quantity = sign * (q - q_target)
                q_target = round(max(0, q_target - q), 3)

            return pnl, open_trades

        pnl_long = []
        pnl_short = []
        for T in close_longs:
            pnl, longs = calculate(T, longs)
            pnl_long.append(pnl)

        for T in close_shorts:
            pnl, shorts = calculate(T, close_shorts)
            pnl_short.append(pnl)

        return {
            'longs': longs,
            'shorts': shorts,
            'pnl_long': pnl_long,
            'pnl_shorts': pnl_short,
            'total_pnl_long': sum(pnl.calculate() for pnl in pnl_long),
            'total_pnl_short': sum(pnl.calculate() for pnl in pnl_short)
        }

    def get_symbols(self):
        return list(self.order_history)

    def get_pnl_report(self):
        return {
            s: self._get_pnl(s) for s in self.get_symbols()
        }