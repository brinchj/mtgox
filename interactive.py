from mtgox import MtGox
from broker import Broker
from config import KEY, SEC
from decimal import Decimal

_gox = MtGox(KEY, SEC)
_broker = Broker(_gox)
_broker.start()

TIMEOUT = 60

_BTC_FACTOR = 10 ** 8
_USD_FACTOR = 10 ** 5
def _floatBTC(btc):
    return float(btc) / _BTC_FACTOR
def _floatUSD(usd):
    return float(usd) / _USD_FACTOR
def _to_decimal(flt):
    return Decimal(str(flt))
def _intBTC(btc):
    return int(_to_decimal(btc) * _BTC_FACTOR)
def _intUSD(usd):
    return int(_to_decimal(usd) * _USD_FACTOR)

def stop():
    _broker.stop()
    quit()

def balance():
    data = _broker.balance()
    return {'btcs': _floatBTC(data['btcs']),
            'usds': _floatUSD(data['usds'])}

def offer(balance = None):
    if balance is None:
        balance = {'btcs': 0, 'usds': 0}
    else:
        balance = {'btcs': _intBTC(balance['btcs']),
                   'usds': _intUSD(balance['usds'])}
    data = _broker.offer(balance)
    return {'sell': _floatUSD(data['sell']),
            'buy': _floatUSD(data['buy'])}

def orders():
    def f(x):
        x['amount'] = _floatBTC(x['amount'])
        x['price'] = _floatUSD(x['price'])
        return x
    return map(f, _broker.orders())

def cancel(oid):
    return _broker.cancel(oid)

def cancelAll():
    _broker.cancelAll()

def _successHandler(oid):
    print "Success! (%s)" % oid
def _timeoutHandler(oid):
    print "Timeout! (%s)" % oid

def buy(amount, price = None):
    if price is None:
        data = _offer({'btcs': 0, 'usds': amount})
        price = data['buy']
    return _broker.trade(_intBTC(amount / price), _intUSD(price), TIMEOUT,
                         _successHandler, _timeoutHandler)

def buyMax(price = None):
    amount = balance()['usds']
    return buy(amount, price)

def sell(amount, price = None):
    if price is None:
        data = _offer({'btcs': amount, 'usds': 0})
        price = data['sell']
    return _broker.trade(_intBTC(-amount), _intUSD(price), TIMEOUT,
                         _successHandler, _timeoutHandler)

def sellMax(price = None):
    amount = balance()['btcs']
    return sell(amount, price)

def value():
    data = _broker.value()
    return {'btcs': float(data['btcs']),
            'usds': float(data['usds'])}
