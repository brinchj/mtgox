import time

from mtgox import MtGox
from broker import Broker

from config import KEY, SEC

from decimal import Decimal

def to_decimal(flt):
    return Decimal(str(flt))

BTC_FACTOR = 10**8
USD_FACTOR = 10**5

gox = MtGox(KEY, SEC)
broker = Broker(gox)
while True:
    try:
        tic = broker.ticker()
        bal = broker.balance()

        last = to_decimal(tic['last'])
        buy = to_decimal(tic['sell'])
        sell = to_decimal(tic['buy'])
        usds = to_decimal(bal['usds']) / USD_FACTOR
        btcs = to_decimal(bal['btcs']) / BTC_FACTOR
        valusds = btcs * last + usds
        valbtcs = usds / last + btcs
        print "%.3f BTC + %.3f USD" % (btcs, usds)
        print "%.3f BTC / %.3f USD" % (valbtcs, valusds)
        print "Buy %.3f - Sell %.3f - Last %.3f" % (buy, sell, last)
        print ""
    except KeyboardInterrupt:
        exit(0)
    except:
        pass
    time.sleep(10)

