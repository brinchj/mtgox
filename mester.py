from config import KEY, SEC
from mtgox import MtGox
from broker import Broker

from hrbot import HrBot


TIMEOUT = 60


mtgox = MtGox(KEY, SEC)
broker = Broker(mtgox)
bot = HrBot()

trades = broker.trades()
broker.start()
bot.update(trades)

tid = trades[-1]['tid']

def iterate(tid):
    print 'starting iteration..'
    balance = broker.balance()
    prices = broker.offer(balance)

    print balance, prices

    trades = broker.trades(since=tid)
    bot.update(trades)
    tid = trades[-1]['tid']

    value = bot.action(balance, prices)
    print 'bot says:', value

    if value != 0:
        lmd = lambda : iterate(tid)
        broker.trade(value, prices[value > 0 and 'buy' or 'sell'],
                     ttl=TIMEOUT,
                     onSuccess=lmd, onTimeout=lmd)
    else:
        iterate(tid)


if __name__ == '__main__':
    iterate(tid)
