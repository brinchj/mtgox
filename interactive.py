from mtgox import MtGox
from config import KEY, SEC
from decimal import Decimal

TIMEOUT = 60

_gox = MtGox(KEY, SEC)
_gox.start()

def _to_decimal(x):
    return Decimal(str(x))

def stop():
    _gox.stop()
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

def balance():
    x = _gox.balance()
    return {'btcs': str(x['btcs']),
            'usds': str(x['usds'])}

def _trade(amount, price, ttl):
    if amount > 0:
        action = 'Bought'
    else:
        action = 'Sold'
    def onProgress(oid, data):
        print '%s %.2f BTC at %.2f USD:' % (action, data['amount'], data['price'])
        print '   ', oid
    def onFilled(oid):
        print 'Order was filled:'
        print '   ', oid
    def onCancel(oid):
        print 'Order was cancelled:'
        print '   ', oid
    def onTimeout(oid):
        print 'Order has timed out:'
        print '   ', oid
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
                    'price': str(x['price']),
                    'date': time.ctime(x['date']),
                    'oid': x['oid'],
             'status': x['status'],
                    'ttl': x['ttl'],
                    'type': x['type']},
               _gox.orders())
