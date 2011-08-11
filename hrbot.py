
from operator import attrgetter
import time


WINDOW = 300
MIN = 5
MARGIN = 0.02

class HrBot:
    def __init__(self):
        self.trades = []

    def update(self, trades):
        self.trades += trades
        offset = time.time() - WINDOW
        self.trades = filter(lambda x: x['date'] > offset, self.trades)

    def action(self, balance, prices):
        if len(self.trades) < MIN:
            return None
        # price, amount, tid, date
        movavg = sum(map(lambda x: x['price'], self.trades)) / len(self.trades)

        btcs = balance['btcs']
        usds = balance['usds']

        buy = prices['buy']
        sell = prices['sell']

        if btcs == 0 and buy < movavg * (1 - MARGIN):
            return usds / buy
        elif btcs > 0 and sell > movavg * (1 + MARGIN):
            return -btcs
        return 0
