import pandas as pd
import os

from pnl import Manager
# from cryptofeed.rest import kraken
# api = kraken.Kraken()

BASEDIR = 'ressources/crypto_csv'
START = '20210101'
END = '202112312359'

df = pd.concat([pd.read_csv(os.path.join(BASEDIR, p)) for p in os.listdir(BASEDIR)])
df.sort_values('Completed Date', inplace=True)
df = df.loc[df['Type'] == 'EXCHANGE']
intra_transaction = {}

class C:
    Symbol = 'Currency'
    Fee = 'Fee'
    Qty = 'Amount'
    Fiat_Amount = 'Fiat amount'
    Currency = 'Base currency'
    Price = 'Price'
    Tradetime = 'Completed Date'
    From = 'From'
    To = 'To'
    Description = 'Description'
    Balance = 'Balance'

df[C.Price] = df[C.Fiat_Amount] / df[C.Qty]
df[C.To] = df[C.Description].str.extract('Exchanged to (.+)')
df[C.From] = df[C.Symbol]
df.loc[df[C.To] == df[C.From], C.From] = 'EUR'

manager = Manager()

for i, t in df.iterrows():
    if 'EUR' in [t[C.From], t[C.To]]:
        q = t[C.Qty]
        params = dict(tradetime=t[C.Tradetime], symbol=t[C.Symbol], quantity=t[C.Qty], fee=t[C.Fee], currency='EUR',
                      price=t[C.Price])
        if q > 0:
            manager.order(**params)
        else:
            manager.close(**params)
    else:
        q_from = t[C.Qty] # swap 'to' appear in another trade at the same timestamp as if bought with EUR. so we just need to close the long position 'from'
        params = dict(tradetime=t[C.Tradetime], currency='EUR', price=t[C.Price])
        manager.close(**params, symbol=t[C.From], quantity=q_from, fee=t[C.Fee])

d_pnl = manager.get_pnl_report()

def get_realized_pnl(start, end, pnls):
    def formatter_date(d):
        return pd.to_datetime(d).strftime('%Y-%m-%d %H:%M:%s')
    _start = formatter_date(start)
    _end = formatter_date(end)
    def _get_realized_pnl(pnl_long):
        _pnl_long = [x for x in pnl_long if _start <= x.close_order.tradetime <= _end]
        res = {
            'pnl': sum(x.calculate() for x in _pnl_long),
            'fees': sum(x.get_fees() for x in _pnl_long),
            'valeur globale cession': sum(x.close_order.price * -x.close_order.quantity  for x in _pnl_long),
            'frais de cession': sum(x.close_order.fee for x in _pnl_long),
            'prix total acquisition': sum(sum(t.price * t.quantity + t.fee for t in x.closed_trades) for x in _pnl_long)
        }
        dates_cessions = [x.close_order.tradetime for x in pnl_long if _start <= x.close_order.tradetime <= _end]
        if len(dates_cessions) > 0:
            res['date de cession'] = max(dates_cessions)
        res['pnl net of fees'] = res['pnl'] - res['fees']
        return res

    return {c: _get_realized_pnl(pnls[c]['pnl_long']) for c in pnls}

# Champs utiles pour impots
realized = get_realized_pnl(START, END, d_pnl)
print(realized)

#
# # Pour cross check
# def get_price(ticker):
#     ticker = api.ticker(ticker)
#     return float(ticker['bid'] + ticker['ask']) / 2
#
# latest_price = {
#     'BTC': get_price('BTC-EUR'),
#     'BCH': get_price('BCH-EUR'),
#     'ETH': get_price('ETH-EUR'),
#     'XLM': get_price('XLM-EUR'),
#     'XRP': get_price('XRP-EUR'),
#     'ADA': get_price('ADA-EUR'),
#     'LTC': get_price('LTC-EUR'),
#     'XTZ': get_price('XTZ-EUR'),
#     'DOGE': get_price('DOG-EUR'),
# }
#
# estim_holding = {c: sum(x.quantity for x in d_pnl[c]['longs']) for c in d_pnl} # issue with precision
# paid_holdings = {c: sum(x.quantity * x.price + x.fee for x in d_pnl[c]['longs']) for c in d_pnl}
#
# holding = {}
# unrealized = {}
# realized = {}
# fees_realized_pnl = {}
# total = {}
# for c in d_pnl:
#     holding[c] = latest_price[c] * estim_holding[c] - paid_holdings[c]
#     realized[c] = d_pnl[c]['total_pnl_long']
#     fees_realized_pnl[c] = sum(x.get_fees() for x in d_pnl[c]['pnl_long'])
#     total[c] = holding[c] + realized[c] - fees_realized_pnl[c]
#
# def log(*args):
#     to_print = []
#     for a in args:
#         if type(a) is float:
#             to_print.append(round(a, 2))
#         else:
#             to_print.append(a)
#     print(*to_print)
# log('PnL realized', realized)
# log('fees PnL realized', fees_realized_pnl)
# log('PnL RT', holding)
# log('Total split', total)
# log('Total ', round(sum(total.values()), 2))
#
# report = pd.DataFrame({
#     'PnL realized': realized,
#     'fees PnL realized': fees_realized_pnl,
#     'PnL RT': holding,
#     'Total split': total
# })
#
