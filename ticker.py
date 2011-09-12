import time, convert

from mtgoxcore import MtGoxCore
from config import KEY, SEC
from decimal import Decimal

FEE = Decimal('0.0053')

gox = MtGoxCore(KEY, SEC)
while True:
    try:
        tic = convert.ticker(gox.ticker())
        bal = convert.balance(gox.balance())

        last = tic['last']
        buy = tic['sell']
        sell = tic['buy']
        usds = bal['usds']
        btcs = bal['btcs']
        valusds = (1 - FEE) * btcs * last + usds
        valbtcs = (1 - FEE) * usds / last + btcs
        print '%.3f BTC + %.3f USD' % (btcs, usds)
        print '%.3f BTC / %.3f USD' % (valbtcs, valusds)
        print 'Buy %.3f - Sell %.3f - Last %.3f' % (buy, sell, last)
        print ''
    except KeyboardInterrupt:
        exit(0)
    except Exception, e:
        print e
        pass
    time.sleep(60)
