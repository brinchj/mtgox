import json, time, convert

from decimal import Decimal
from scalper import Scalper

FEE = Decimal('0.0065')

print 'Loading history...'
history = json.load(file('history.raw.json'))[-1::-1]

class Sim():
    def __init__(self, history):
        self.history = history

    def trades(self, since):
        return [self.history.pop()]

    def depth(self):
        price = self.history[-1]['price']
        # print price
        return {'bids': [{'amount': Decimal('Infinity'),
                          'price': price * Decimal('0.98')}],
                'asks': [{'amount': Decimal('Infinity'),
                          'price': price * Decimal('1.02')}]
                }

    def buy(self, amount, price, ttl = None, onProgress = None):
        onProgress(None, amount * (1 - FEE), price)

    def sell(self, amount, price, ttl = None, onProgress = None):
        onProgress(None, amount, price * (1 + FEE))

# scalper = Scalper(Sim(history), Decimal(1), Decimal(0))
# scalper.start()


def sim(start, end):
    f = "%d/%m-%Y %H:%M"
    start = time.mktime(time.strptime(start, f))
    end = time.mktime(time.strptime(end, f))
    trades = filter(lambda x: x['date'] >= start and x['date'] <= end,
                    history
                    )

    print '%s -- %s:' % \
        (time.ctime(trades[0]['date']), time.ctime(trades[-1]['date'])),

    trades = map(lambda x: {'date': x['date'],
                            'price': Decimal(x['price_int']) / Decimal(10**5),
                            'tid': x['tid']},
                 trades)
    bot = Scalper(Sim(trades), Decimal(1), Decimal(0))
    try:
        bot.start()
    except:
        print bot.btcs, bot.usds

sim('01/08-2011 00:00', '14/08-2011 23:59')
