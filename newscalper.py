# import logging
# logging.basicConfig(
#     format = '%(name)-12s: %(message)s',
#     )
# logging.getLogger('MtGoxCore').setLevel(logging.DEBUG)
# logging.getLogger('MtGox').setLevel(logging.DEBUG)


import time, os

from threading import Thread
from decimal import Decimal

WINDOW = 60
MIN = 1
LEVELS = 2
MARGIN_BUY = Decimal('0.02')
MARGIN_SELL = Decimal('0.02')
INTERVAL = 30
CONSERVATISM = Decimal('0.01')

class Scalper(Thread):
    def __init__(self, gox):
        Thread.__init__(self)

        self.gox = gox
        self.since = None
        self.trades = []
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self._loop()
            time.sleep(INTERVAL)

    def stop(self):
        self.running = False

    def _loop(self):
        trades = self.gox.trades(self.since)
        if trades == []:
            self.gox.cancel_all()
            return
        self.trades += trades
        self.since = self.trades[-1]['tid']
        cutoff = time.time() - WINDOW
        self.trades = filter(lambda x: x['date'] > cutoff, self.trades)

        if len(self.trades) < MIN:
            return

        btcs = self.gox.balance()['btcs'] * (1 - CONSERVATISM)
        usds = self.gox.balance()['usds'] * (1 - CONSERVATISM)
        movavg = sum(map(lambda x: x['price'], self.trades)) / len(self.trades)

        def onBuy(order, amount, price):
            print "Bought %.2f BTC at %.2f USD" % (amount, price)
        def onSell(order, amount, price):
            print "Sold %.2f BTC at %.2f USD" % (amount, price)

        gox.cancel_all()
        print ''
        # os.system('clear')
        if usds > 0.1:
            for i in range(LEVELS, 0, -1):
                price = movavg / (1 + MARGIN_BUY * i)
                amount = (usds / LEVELS) / price
                print ("%.2f" % price)
                self.gox.buy(amount, price, None, onBuy)
        print '------'
        if btcs > 0.1:
            for i in range(1, LEVELS + 1):
                price = movavg * (1 + MARGIN_SELL * i)
                amount = btcs / LEVELS
                print ("%.2f " % price)
                self.gox.sell(amount, price, None, onSell)

if __name__ == "__main__":
    from mtgox import MtGox
    from config import KEY, SEC
    gox = MtGox(KEY, SEC)
    gox.start()
    scalper = Scalper(gox)
    scalper.start()
