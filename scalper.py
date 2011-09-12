import time

from threading import Thread
from decimal import Decimal

WINDOW = 60
MIN = 1
MARGIN_BUY = Decimal('0.015')
MARGIN_SELL = Decimal('0.015')
TIMEOUT = 30
INTERVAL = 5

class Scalper(Thread):
    def __init__(self, gox):
        Thread.__init__(self)

        self.order_in_progress = False
        self.gox = gox
        # self.btcs = btcs
        # self.usds = usds
        self.since = None
        self.trades = []
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if not self.order_in_progress:
                self._loop()
            time.sleep(INTERVAL)

    def stop(self):
        self.running = False

    def _loop(self):
        trades = self.gox.trades(self.since)
        if trades == []:
            return
        self.trades += trades
        self.since = self.trades[-1]['tid']
        cutoff = time.time() - WINDOW
        self.trades = filter(lambda x: x['date'] > cutoff, self.trades)

        if len(self.trades) < MIN:
            return

        btcs = self.gox.balance()['btcs']
        usds = self.gox.balance()['usds']
        depth = self.gox.depth()
        try:
            bid = depth['bids'][0]
            ask = depth['asks'][0]
        except:
            return
        movavg = sum(map(lambda x: x['price'], self.trades)) / len(self.trades)

        def onBuy(order, amount, price):
            print "  Bought %.2f BTC at %.2f USD" % (amount, price)
            # self.btcs += amount
            # self.usds -= amount * price
        def onSell(order, amount, price):
            print "  Sold %.2f BTC at %.2f USD" % (amount, price)
            # self.btcs -= amount
            # self.usds += amount * price
        def onTimeout(order):
            print "  Timeout"
            self.order_in_progress = False
        def onFilled(order):
            print "  Filled"
            self.order_in_progress = False

        # print "%s: AVG %.2f - Buy %.2f%% - Sell %.2f%%" % \
        #     (time.ctime(),
        #      movavg,
        #      max(100 * (movavg - ask['price']) / movavg, 0),
        #      max(100 * (bid['price'] - movavg) / movavg, 0))
        if usds > 0 and ask['price'] < movavg * (1 - MARGIN_BUY):
            price = ask['price'] * Decimal('1.001')
            amount = min(usds / price, ask['amount'])
            print time.ctime()
            print "  Buying %.2f BTC at %.2f USD" % (amount, price)
            self.order_in_progress = True
            self.gox.buy(amount, price,
                         TIMEOUT,
                         onBuy,
                         onFilled,
                         None,
                         onTimeout)
        elif btcs > 0 and bid['price'] > movavg / (1 - MARGIN_SELL):
            price = bid['price'] / Decimal('1.001')
            amount = min(btcs, bid['amount'])
            print time.ctime()
            print "  Selling %.2f BTC at %.2f USD" % (amount, price)
            self.order_in_progress = True
            self.gox.sell(amount, price,
                          TIMEOUT,
                          onSell,
                          onFilled,
                          None,
                          onTimeout)
