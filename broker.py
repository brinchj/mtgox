import urllib2, time

from threading import Thread
from decimal import Decimal

def maybeRetry(action):
    while True:
        try:
            return action()
        except (urllib2.URLError, urllib2.HTTPError), e:
            pass

BTC_FACTOR = 10**8
USD_FACTOR = 10**5

def to_decimal(flt):
    return Decimal(str(flt))

def intBTC(btc):
    return int(to_decimal(btc) * BTC_FACTOR)

def intUSD(usd):
    return int(to_decimal(usd) * USD_FACTOR)

def strBTC(btc):
    return str(to_decimal(btc) / BTC_FACTOR)

def strUSD(usd):
    return str(to_decimal(usd) / USD_FACTOR)

class Broker(Thread):
    def __init__(self, gox):
        Thread.__init__(self)

        self.gox = gox
        self.queued = dict()
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            time.sleep(5)
            data = self.orders()
            now = time.time()
            for oid in self.queued.keys():
                if any(map(lambda x: x['oid'] == oid, data)):
                    if now > self.queued[oid]['timeout']:
                        self.queued[oid]['onTimeout'](oid)
                        self.cancel(oid)
                else:
                    self.queued[oid]['onSuccess'](oid)
                    del self.queued[oid]

    def stop(self):
        self.running = False

    def balance(self):
        data = maybeRetry(self.gox.balance)
        data['btcs'] = intBTC(data['btcs'])
        data['usds'] = intUSD(data['usds'])
        return data

    def offer(self, balance):
        btcs = balance['btcs']
        usds = balance['usds']
        data = maybeRetry(self.gox.depth)
        conv = lambda (usd,btc): (intUSD(usd), intBTC(btc))
        bids = map(conv, data['bids'][-1::-1])
        asks = map(conv, data['asks'])

        n = 0
        for (p, a) in bids:
            n += a
            if n >= btcs:
                sell = p
                break
        n = 0
        for (p, a) in asks:
            n += p * (a / BTC_FACTOR)
            if n >= usds:
                buy = p
                break
        return {'buy': buy, 'sell': sell}

    def orders(self):
        data = maybeRetry(self.gox.orders)
        return map(lambda x: {'amount': int(x['amount_int']),
                              'price': int(x['price_int']),
                              'status': x['real_status'],
                              'date': x['date'],
                              'oid': x['oid']},
                   data['orders'])

    def trades(self, since=None):
        trades = []
        while True:
            t = maybeRetry(lambda: self.gox.trades(since))
            if len(t) > 0:
                print "%s -- %s" % \
                    (time.ctime(t[0]['date']), time.ctime(t[-1]['date']))
            trades = trades + t
            if len(t) < 100:
                break
            since = t[-1]['tid']

        return map(lambda x: {'price': int(x['price_int']),
                              'amount': int(x['amount_int']),
                              'tid': x['tid'],
                              'date': x['date']},
                   trades)

    def cancel(self, oid):
        maybeRetry(lambda: self.gox.cancel(oid))
        if oid in self.queued:
            del self.queued[oid]

    def cancelAll(self):
        map(lambda x: self.cancel(x['oid']), self.orders())

    def trade(self, amount, price, ttl = None,
              onSuccess = None, onTimeout = None):
        if amount < 0:
            amount = -amount
            action = self.gox.sell
        else:
            action = self.gox.buy

        data = maybeRetry(lambda:action(strBTC(amount), strUSD(price)))
        oid = data['oid']
        self.queued[oid] = {'timeout': time.time() + ttl,
                            'onSuccess': onSuccess,
                            'onTimeout': onTimeout}

        return oid

    def ticker(self):
        return maybeRetry(self.gox.ticker)['ticker']

    def value(self):
        tic = self.ticker()
        rate = to_decimal(tic['last'])
        bal = self.balance()
        usds = to_decimal(bal['usds']) / USD_FACTOR
        btcs = to_decimal(bal['btcs']) / BTC_FACTOR
        val = {'btcs': usds / rate + btcs,
               'usds': btcs * rate + usds}
        return val
