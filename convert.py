from decimal import Decimal

def _to_decimal(x):
    return Decimal(str(x))

_BTC_FACTOR = Decimal(10 ** 8)
_USD_FACTOR = Decimal(10 ** 5)

def ticker(x):
    x = x['ticker']
    return {'buy': _to_decimal(x['buy']),
            'sell': _to_decimal(x['sell']),
            'high': _to_decimal(x['high']),
            'low': _to_decimal(x['low']),
            'last': _to_decimal(x['last']),
            'avg': _to_decimal(x['avg']),
            'vol': _to_decimal(x['vol']),
            'vwap': _to_decimal(x['vwap'])}

def depth(x):
    f = lambda x: {'amount': _to_decimal(x[1]),
                   'price': _to_decimal(x[0])}
    bids = map(f, x['bids'])
    asks = map(f, x['asks'])

    f = lambda x: x['price']
    return {'bids': sorted(bids, key = f, reverse = True),
            'asks': sorted(asks, key = f)}

def trade(x):
    return {'amount': _to_decimal(x['amount_int']) / _BTC_FACTOR,
            'price': _to_decimal(x['price_int']) / _USD_FACTOR,
            'date': x['date'],
            'tid': x['tid'],
            'type': x['trade_type']}

def trades(x):
    return map(trade, x)

def balance(x):
    return {'btcs': _to_decimal(x['btcs']),
            'usds': _to_decimal(x['usds'])}

def order(x):
    if x['type'] == 2:
        t = 'bid'
    else:
        t = 'ask'
    return {'amount': _to_decimal(x['amount_int']) / _BTC_FACTOR,
            'price': _to_decimal(x['price_int']) / _USD_FACTOR,
            'date': x['date'],
            'oid': x['oid'],
            'status': x['real_status'],
            'type': t}

def orders(x):
    return map(order, x['orders'])
