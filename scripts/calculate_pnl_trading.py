import pandas as pd
import numpy as np

PATH_TO_EXCHANGE_RATE = 'ressources/EUR_USD.csv'
PATH_TO_REVOLUT_CSV = 'ressources/revolut2021.csv'
START = '2021-01-01' #  definir periode fiscale. Le format est important
END = '2021-12-31'
rate = pd.read_csv(PATH_TO_EXCHANGE_RATE, decimal=',')
df = pd.read_csv(PATH_TO_REVOLUT_CSV)

###### Definir periode fiscale ######
df = df[(START <= df['Date sold']) & (df['Date sold'] <= END)]

###### Ajout pnl (eur) to df ######
rate['Date'] = pd.to_datetime(rate['Date'], dayfirst=True)
ts_rate = 1 / rate.set_index('Date')['Dernier'].sort_index()
dates = pd.date_range(ts_rate.index.min(), ts_rate.index.max(), freq='d')
ts_rate = ts_rate.reindex(dates).ffill()
ts_rate.index = ts_rate.index.strftime('%Y-%m-%d')

def convert_pnl(r):
    buy = ts_rate[r['Date acquired']] * r['Cost basis']
    sold = ts_rate[r['Date sold']] * r['Amount']
    return sold - buy
df['pnl'] = df.apply(convert_pnl, axis=1) # pnl en euro


###### Filtering time period ######
#a reporter dans formulaire 2074. Dans les champs qui ne sont pas grisés
gain = df.loc[df['pnl'] > 0, 'pnl'].sum()
loss = - df.loc[df['pnl'] < 0, 'pnl'].sum()
print('gain', np.floor(gain), 'loss', np.floor(loss), 'total', np.floor(gain-loss), 'checksum', df['pnl'].sum())