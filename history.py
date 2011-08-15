from mtgoxcore import MtGoxCore
from config import KEY, SEC

import time, json

gox = MtGoxCore(KEY, SEC)

file_raw = 'history.raw.json'
file_prices = 'history.prices.pickled'

try:
    with open(file_raw) as f:
        print "Reading saved trades from disk"
        trades = json.load(f)
        since = trades[-1]['tid']
        print "Read %d trades from disk" % len(trades)
except:
    since = 0
    trades = []

while True:
    t = gox.trades(since)
    print "%s -- %s" % (time.ctime(t[0]['date']), time.ctime(t[-1]['date']))
    trades = trades + t
    if len(t) < 100:
        break
    since = t[-1]['tid']

with open(file_raw, 'w') as f:
    print "Writing %d trades to disk" % len(trades)
    json.dump(trades, f)

# prices = map(lambda x: float(x['price']), trades)

# with open(file_prices, 'w') as f:
#     print "Writing %d prices to disk" % len(prices)
#     json.dump(prices, f)
