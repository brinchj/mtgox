import json
import time

from config import KEY, SEC
from mtgox import MtGox
from broker import Broker

from hrbot import HrBot

# mtgox = MtGox(KEY, SEC)
# broker = Broker(mtgox)


# broker.start()

print 'Loading history...'
history = json.load(file('history.raw.json'))

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
        buy = p * 1.01
        sell = p * 0.99
        x = bot.action({'buy': buy, 'sell': sell})
        if x != 0:
            bot.onTrade(x, 0)
            if x < 0:
                # print "sell", sell
                usd = (btc * sell) / (10 ** 8)
                btc = 0
            else:
                # print "buy", buy
                btc = usd / buy * (10 ** 8)
                usd = 0

    if btc == 0:
        btc = usd / trades[-1]['price']
    else:
        btc /= 10 ** 8

    print "%.2f%%" % ((btc - 1) * 100)

for m in range(7, 13):
    d = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    start = "01/%d-2010 00:00" % m
    end   = "%d/%d-2010 23:59" % (d[m], m)

    sim(start, end)

for m in range(1, 9):
    d = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    start = "01/%d-2011 00:00" % m
    end   = "%d/%d-2011 23:59" % (d[m], m)

    sim(start, end)
