import json, time, convert

FEE = 0.0065
WINDOW = 60
MIN = 5
MARGIN = 0.02

print 'Loading history...'
history = json.load(file('history.raw.json'))

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


def sim(start, end):
    bot = HrBot()
    btc = 1 * 10**8
    usd = 0
    f = "%d/%m-%Y %H:%M"
    start = time.mktime(time.strptime(start, f))
    end = time.mktime(time.strptime(end, f))
    trades = filter(lambda x: x['date'] >= start and x['date'] <= end,
                    history
                    )

    print '%s -- %s:' % \
        (time.ctime(trades[0]['date']), time.ctime(trades[-1]['date'])),

    trades = map(lambda x: {'date': x['date'],
                            'price': int(x['price_int'])},
                 trades)
    for t in trades:
        bot.update([t])
        p = t['price']
        buy = p * 1.02
        sell = p * 0.98
        x = bot.action({'buy': buy, 'sell': sell})
        if x != 0:
            bot.onTrade(x, 0)
            if x < 0:
                # print "sell", sell
                usd = (1 - FEE) * (btc * sell) / (10 ** 8)
                btc = 0
            else:
                # print "buy", buy
                btc = (1 - FEE) * usd / buy * (10 ** 8)
                usd = 0

    if btc == 0:
        btc = usd / trades[-1]['price']
    else:
        btc /= 10 ** 8

    print "%.2f%%" % ((btc - 1) * 100)

# for m in range(7, 13):
#     d = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
#     start = "01/%d-2010 00:00" % m
#     end   = "%d/%d-2010 23:59" % (d[m], m)

#     sim(start, end)

# for m in range(1, 9):
#     d = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
#     start = "01/%d-2011 00:00" % m
#     end   = "%d/%d-2011 23:59" % (d[m], m)

#     sim(start, end)

sim('01/05-2011 00:00', '15/08-2011 23:59')
