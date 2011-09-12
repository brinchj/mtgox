import logging, time

from mtgox import MtGox
from config import KEY, SEC
from decimal import Decimal
from scalper import Scalper

logging.basicConfig(
    filename = 'interactive.log',
    filemode = 'w',
    format = '[%(asctime)s, %(threadName)s, %(name)s, %(levelname)s]\n   %(message)s',
    # format = '%(name)-12s: %(message)s',
    datefmt = '%d/%m %H:%M:%S',
    )

# logging.getLogger('MtGoxCore').setLevel(logging.DEBUG)
logging.getLogger('MtGox').setLevel(logging.DEBUG)
logging.getLogger('MtGoxCore').setLevel(logging.NOTSET)
# logging.getLogger('MtGox').setLevel(logging.INFO)

TIMEOUT = 60

_gox = MtGox(KEY, SEC)
_gox.start()
_scalper = Scalper(_gox)
_scalper.start()

def _to_decimal(x):
    return Decimal(str(x))

def stop():
    _gox.stop()
    _scalper.stop()
    quit()

def ticker():
    x = _gox.ticker()
    return {'buy': str(x['buy']),
            'sell': str(x['sell']),
            'high': str(x['high']),
            'low': str(x['low']),
            'last': str(x['last']),
            'avg': str(x['avg']),
            'vol': str(x['vol']),
            'vwap': str(x['vwap'])}

def depth():
    x = _gox.depth()
    f = lambda x: {'amount': str(x['amount']),
                   'price': str(x['price'])}
    return {'bids': map(f, x['bids']),
            'asks': map(f, x['asks'])}

def trunc_depth():
    return {'bids': depth()['bids'][0:5],
            'asks': depth()['asks'][0:5]}

def balance():
    x = _gox.balance()
    return {'btcs': str(x['btcs']),
            'usds': str(x['usds'])}

def _trade(amount, price, ttl):
    if amount > 0:
        action = 'Bought'
    else:
        action = 'Sold'
    def onProgress(o, amount, price):
        print '%s %.2f BTC at %.2f USD:' % (action, amount, price)
        print '   ', o['oid']
    def onFilled(o):
        print 'Order was filled:'
        print '   ', o['oid']
    def onCancel(o):
        print 'Order was cancelled:'
        print '   ', o['oid']
    def onTimeout(o):
        print 'Order has timed out:'
        print '   ', o['oid']
    return _gox.trade(_to_decimal(amount), _to_decimal(price), ttl,
                      onProgress,
                      onFilled,
                      onCancel,
                      onTimeout)

def buy(amount, price, ttl = TIMEOUT):
    return _trade(amount, price, ttl)

def sell(amount, price, ttl = TIMEOUT):
    return _trade(-amount, price, ttl)

def cancel(oid):
    _gox.cancel(oid)

def cancel_all():
    _gox.cancel_all()

def orders():
    return map(lambda x:
                   {'amount': str(x['amount']),
                    'orig_amount': str(x['orig_amount']),
                    'cancelled_amount': str(x['cancelled_amount']),
                    'price': str(x['price']),
                    'date': time.ctime(x['date']),
                    'oid': x['oid'],
                    'status': x['status'],
                    'ttl': x['ttl'],
                    'type': x['type']},
               _gox.orders())
