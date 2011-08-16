import time

from threading import Thread
from decimal import Decimal

WINDOW = 60
MIN = 5
MARGIN = Decimal('0.02')
TIMEOUT = 30
INTERVAL = 5

class Scalper(Thread):
    def __init__(self, gox, btcs, usds):
        Thread.__init__(self)

        self.gox = gox
        self.btcs = btcs
        self.usds = usds
        self.since = None
        self.trades = []

    def run(self):
        while True:
            self._loop()
            time.sleep(INTERVAL)

    def _loop(self):
        print '.'
        trades = self.gox.trades(self.since)
        if trades == []:
            return
        self.trades += trades
        self.since = self.trades[-1]['tid']
        cutoff = time.time() - WINDOW
        self.trades = filter(lambda x: x['date'] > cutoff, self.trades)

        if len(self.trades) < MIN:
            return

        depth = self.gox.depth()
        bid = depth['bids'][0]
        ask = depth['asks'][0]
        movavg = sum(map(lambda x: x['price'], self.trades)) / len(self.trades)

        def onBuy(order, amount, price):
            self.btcs += amount
            self.usds -= amount * price
            print self.btcs
        def onSell(order, amount, price):
            self.btcs -= amount
            self.usds += amount * price

        if self.usds > 0 and ask['price'] < movavg * (1 - MARGIN):
            price = ask['price']
            amount = min(self.usds / price, ask['amount'])
            self.gox.buy(amount, price,
                         ttl = TIMEOUT,
                         onProgress = onBuy)
        elif self.btcs > 0 and bid['price'] > movavg * (1 + MARGIN):
            price = bid['price']
            amount = min(self.btcs, bid['amount'])
            self.gox.sell(amount, price,
                          ttl = TIMEOUT,
                          onProgress = onSell)
