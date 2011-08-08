
import urllib
import urllib2
import time
import hmac
import json


from base64 import b64encode, b64decode
from hashlib import sha512 as hash
from threading import Thread


KEY = '8ebf8cf8-9fbd-454c-955b-02eaf5f12a05'
SEC = 'IzrAt6Bh1JzwigEn2+Xl++RH2660Hzy0NWbqTrafQhKe1nJbY+O0ssSVnkzYKlYoKyMWsLpx1UL854OgnjOWGQ=='


def hmac_digest(data, key):
    return hmac.new(key, data, hash).digest()


def get_nonce():
    return str(int(time.time()))


def post(url, data='', headers={}):
    req = urllib2.Request(url, data, headers)
    res = urllib2.urlopen(req, timeout=30)
    return res.read()


class MisterBot(Thread):
    def __init__(self, mtgox, history_window=24*3600, margin=0.05):
        Thread.__init__(self)

        self.active = False
        self.mtgox = mtgox
        self.btcs = 0
        self.usds = 0
        self.__bootstrap()

        self.history_window = history_window
        self.margin = margin


    def __bootstrap(self):
        balance = self.mtgox.getBalance()
        self.btcs = int(balance['btcs'])
        self.usds = int(balance['usds'])


    def __update(self):
        # remove old trades
        offset = time.time() - self.history_window
        self.trades = filter(lambda t: t['time'] > offset, self.trades)
        # add recent trades
        self.trades += recent_trades


    def decision(asks, bids):
        pass


    def run(self):
        self.active = True
        while self.active:
            pass


    def stop(self):
        self.active = False


class MtGox:
    URL = 'https://mtgox.com/api/0/%s.php?%s'

    def __init__(self, key, secret):
        self.key = key
        self.sec = secret


    def req(self, url, values={}):
        nonce = get_nonce()
        values['nonce'] = nonce
        post_data = urllib.urlencode(values)

        headers = {
            'Rest-Key': self.key,
            'Rest-Sign': b64encode(hmac_digest(post_data, b64decode(self.sec)))
            }

        return json.loads(post(url, post_data, headers))


    def getTrades(self, since=0):
        lst = self.req(MtGox.URL % ('data/getTrades', 'since='+str(since)))
        for e in lst:
            yield e
        if len(lst) == 100:
            last_tid = lst[-1]['tid']
            for e in self.getTrades(since=last_tid):
                yield e

    def getBalance(self):
        return self.req(MtGox.URL % ('getFunds', ''))


    def getDepth(self):
        return self.req(MtGox.URL % ('data/getDepth', ''))

    def getTickerData(self):
        return self.req(MtGox.URL % ('data/ticker', ''))


if __name__ == '__main__':
    mg = MtGox(KEY, SEC)
    print list(mg.getTrades())
