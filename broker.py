import urllib2, time

from threading import Thread
from decimal import Decimal

def maybeRetry(action):
    while True:
        try:
            return action()
        except (urllib2.URLError, urllib2.HTTPError), e:
            print e

BTC_FACTOR = 10**8
USD_FACTOR = 10**5

def to_decimal(flt):
    return Decimal(str(flt))

def intBTC(usd):
    return int(to_decimal(usd) * BTC_FACTOR)

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

    def offer(self, amount):
        data = maybeRetry(self.gox.depth)
        if amount < 0:
            amount = -amount
            bids = data['bids'][-1::-1]
        else:
            bids = data['asks']

        bids = map(lambda (usd,btc): (intUSD(usd), intBTC(btc)), bids)
        n = 0
        for (p, a) in bids:
            n += a
            if n >= amount:
                return p

    def orders(self):
        data = maybeRetry(self.gox.orders)
        return data['orders']

    def trades(self, since=None):
        def _getTrades(since):
            trades = []
            while True:
                try:
                    t = self.gox.trades(since)
                except Exception,e:
                    print "!! Request timed out; trying again"
                    print e
                    time.sleep(1)
                    continue
                print "%s -- %s" % (time.ctime(t[0]['date']), time.ctime(t[-1]['date']))
                trades = trades + t
                if len(t) < 100:
                    break
                since = t[-1]['tid']

        data = maybeRetry(lambda : _getTrades(since))
        return data['trades']

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
        self.queued[oid] = {'timeout': time.time() + ttl * 60,
                            'onSuccess': onSuccess,
                            'onTimeout': onTimeout}

        return oid
