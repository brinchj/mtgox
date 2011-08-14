
from operator import attrgetter
import time


# WINDOW = 10
WINDOW = 60
MIN = 1
MARGIN = 0.015

class HrBot:
    def __init__(self):
        self.btc = True
        self.trades = []

    def update(self, trades):
        self.trades += trades
        # offset = time.time() - WINDOW
        offset = trades[-1]['date'] - WINDOW
        self.trades = filter(lambda x: x['date'] > offset, self.trades)
        # if len(self.trades) > WINDOW:
            # self.trades = self.trades[-WINDOW:]

    def onTrade(self, amount, price):
        self.btc = not self.btc

    def action(self, prices):
        # print 'got:', len(self.trades)
        if len(self.trades) < MIN:
            return 0
        # price, amount, tid, date
        # t = self.trades[-WINDOW:]
        # movavg = sum(map(lambda x: x['price'], t)) / WINDOW
        movavg = sum(map(lambda x: x['price'], self.trades)) / len(self.trades)

        buy = prices['buy']
        sell = prices['sell']

        if not self.btc and buy < movavg * (1 - MARGIN):
            # return (self.pool - self.balance)
            return 1
        elif self.btc and sell > movavg * (1 + MARGIN):
            # return -self.balance
            return -1
        return 0
