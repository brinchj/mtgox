from config import KEY, SEC
from mtgox import MtGox
from broker import Broker

from hrbot import HrBot


TIMEOUT = 60


mtgox = MtGox(KEY, SEC)
broker = Broker(mtgox)
bot = HrBot()

broker.start()
bot.update(broker.trades())

def iterate():
    print 'starting iteration..'
    balance = broker.balance()
    prices = broker.offer(balance)

    print balance, prices

    value = bot.action(balance, prices)
    print 'bot says:', value

    if value != 0:
        broker.trade(value, prices[value > 0 and 'buy' or 'sell'],
                     ttl=TIMEOUT,
                     onSuccess=iterate, onTimeout=iterate)
    else:
        iterate()


if __name__ == '__main__':
    iterate()
