
WINDOW = 10
MARGIN = 0.01
FEE = 0.0065

class HrBot:
    def __init__(self):
        self.trades = []
        self.btc = False
        self.balance = 1.0
        self.numt = 0

    def update(self, trades):
        self.trades += trades
        if len(self.trades) > WINDOW:
            self.trades = self.trades[-WINDOW:]

    def action(self, buy, sell):
        if len(self.trades) < WINDOW:
            return None
        movavg = sum(self.trades)/WINDOW
        if not self.btc and buy < movavg * (1 - MARGIN):
            print "buy", buy
            self.btc = True
            self.balance /= buy
            # self.balance *= 1 - FEE
        elif self.btc and sell > movavg * (1 + MARGIN):
            print "sell", sell
            self.btc = False
            self.balance *= sell
            self.balance *= 1 - FEE
            self.numt += 1
            print "balance", self.numt, self.balance
