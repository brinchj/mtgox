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

def floatBTC(btc):
    return str(to_decimal(btc) / BTC_FACTOR)

def floatUSD(usd):
    return str(to_decimal(usd) / USD_FACTOR)


class Broker(Thread):
    def __init__(self, gox):
        Thread.__init__(self)

        self.gox = gox
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            time.sleep(1)

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

    def trade(self, amount, price, ttl, onsuccess, onfailure):
        pass
