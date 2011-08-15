import time

from mtgox import MtGox
from config import KEY, SEC
from decimal import Decimal

gox = MtGox(KEY, SEC)
while True:
    try:
        tic = gox.ticker()
        bal = gox.balance()

        last = tic['last']
        buy = tic['sell']
        sell = tic['buy']
        usds = bal['usds']
        btcs = bal['btcs']
        valusds = btcs * last + usds
        valbtcs = usds / last + btcs
        print '%.3f BTC + %.3f USD' % (btcs, usds)
        print '%.3f BTC / %.3f USD' % (valbtcs, valusds)
        print 'Buy %.3f - Sell %.3f - Last %.3f' % (buy, sell, last)
        print ''
    except KeyboardInterrupt:
        exit(0)
    except:
        pass
    time.sleep(10)
