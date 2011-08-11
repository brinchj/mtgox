import json
import time

from config import KEY, SEC
from mtgox import MtGox
from broker import Broker

from hrbot import HrBot


TIMEOUT = 60


mtgox = MtGox(KEY, SEC)
broker = Broker(mtgox)
bot = HrBot()

broker.start()

trades = json.load(file('history.last.json'))
btcs = 19*10**8
usds = 0

for i in xrange(len(trades)):
    print 'starting iteration..'

    print i, len(trades)
    trades_p = trades[:i+1][-1000:]
    off = time.time() - trades_p[-1]['date']
    trades_fix = map(lambda x: {'date': x['date'] + off,
                                    'price': int(x['price_int'])},
                     trades_p[:i+1])
    bot.update(trades_fix)

    p = trades_fix[-1]['price']
    buy = p * 1.02
    sell = p * 0.98
    prices = {'buy': buy, 'sell': sell}

    balance = {'btcs': btcs, 'usds': usds}
    print balance, prices

    value = bot.action(balance, prices)
    print 'bot says:', value

    if value > 0:
        btcs += value
        usds -= value * buy
    elif value < 0:
        btcs -= -value
        usds += -value * sell

