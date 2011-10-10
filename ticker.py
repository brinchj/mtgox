#!/usr/bin/python
# -*- coding: utf-8 -*-

# import logging
# logging.basicConfig(
#     format = '%(name)-12s: %(message)s',
#     )
# logging.getLogger('MtGoxCore').setLevel(logging.DEBUG)
# logging.getLogger('MtGox').setLevel(logging.DEBUG)


import time, convert, pynotify, logging

from mtgoxcore import MtGoxCore
from config import KEY, SEC
from decimal import Decimal

FEE = Decimal('0.0043')

gox = MtGoxCore(KEY, SEC)
bal = convert.balance(gox.balance())
#bal = {'btcs': Decimal(40), 'usds': Decimal(0)}
while True:
    try:
        tic = convert.ticker(gox.ticker())
        newbal = convert.balance(gox.balance())

        last = tic['last']
        buy = tic['sell']
        sell = tic['buy']
        usds = bal['usds']
        btcs = bal['btcs']
        newusds = newbal['usds']
        newbtcs = newbal['btcs']
        valusds = (1 - FEE) * newbtcs * last + newusds
        valbtcs = (1 - FEE) * newusds / last + newbtcs
        print '%.3f BTC + %.3f USD' % (newbtcs, newusds)
        print '%.3f BTC / %.3f USD' % (valbtcs, valusds)
        print 'Buy %.3f - Sell %.3f - Last %.3f' % (buy, sell, last)
        print ''
        if btcs != newbtcs:
            amount = newbtcs - btcs
            if usds != newusds:
                # Trade
                price = (usds - newusds) / amount
                if amount > 0:
                    #Buy
                    n = pynotify.Notification \
                        ('Bought', '%.2f ฿ at %.2f $' % (amount, price))
                    n.show()
                else:
                    #Sell
                    n = pynotify.Notification \
                        ('Sold', '%.2f BTC at %.2f $' % (-amount, price))
                    n.show()
            else:
                #Transfer
                n = pynotify.Notification('Transer', '%.2f BTC' % amount)
                n.show()
        bal = newbal

    except KeyboardInterrupt:
        gox.stop()
        exit(0)
    except Exception, e:
        print e
        pass
    time.sleep(60)
