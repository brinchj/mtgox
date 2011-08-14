import urllib
import urllib2
import time
import hmac
import json


from base64 import b64encode, b64decode
from hashlib import sha512 as hash

def _hmac_digest(data, key):
    return hmac.new(key, data, hash).digest()


def _get_nonce():
    return str(int(time.time() * 1000))


def _post(url, data='', headers={}):
    while True:
        try:
            req = urllib2.Request(url, data, headers)
            res = urllib2.urlopen(req, timeout=10)
            return res.read()
        except (urllib2.URLError, urllib2.HTTPError), e:
            pass

class MtGoxCore:
    URL = 'https://mtgox.com/api/0/%s.php?%s'

    def __init__(self, key = '', secret = ''):
        self.key = key
        self.sec = secret

    def req(self, url, values={'nonce': None}):
        while True:
            nonce = _get_nonce()
            values['nonce'] = nonce
            post_data = urllib.urlencode(values)

            headers = {
                'Rest-Key': self.key,
                'Rest-Sign': b64encode(_hmac_digest(post_data, b64decode(self.sec)))
                }

            js = _post(url, post_data, headers)
            try:
                dt = json.loads(js)
            except:
                continue
            if 'error' in dt:
                continue
            return dt

    def ticker(self):
        """Output:
         {ticker: {buy: float,
                   sell: float,
                   high: float,
                   low: float,
                   last: float,
                   avg: float,
                   vol: float,
                   vwap: float}
                   }"""
        # 'vwap' is weighed average
        return self.req(MtGoxCore.URL % ('data/ticker', ''))

    def depth(self):
        """Output:
        {bids: [option]],
         asks: [option]}

         Where 'option' is a list of two floats;
         first one is price, second is amount.

         Bids and asks are ordered by increasing price."""
        return self.req(MtGoxCore.URL % ('data/getDepth', ''))

    def trades(self, since = None):
        """Output:
        [{amount: float,
          amount_int: int,
          price: float,
          price_int: int,
          date: int,
          tid: int,
          trade_type: string ('bid' or 'ask'),
          item: string (always 'BTC'),
          price_currency: string (always 'USD')
          }]"""
        if since is not None:
            param = 'since=' + str(since)
        else:
            param = ''
        return self.req(MtGoxCore.URL % ('data/getTrades', param))

    def balance(self):
        """Output:
        {btcs: string,
         usds: string}"""
##        print '[MtGoxCore: balance]'
        return self.req(MtGoxCore.URL % ('getFunds', ''))

    def __mkOrder(self, kind, amount, price):
        return self.req(MtGoxCore.URL % (kind + 'BTC', ''),
                        {'amount': str(amount), 'price': str(price)}
                        )

    def buy(self, amount, price):
##        print '[MtGoxCore: buy]'
        return self.__mkOrder('buy', amount, price)

    def sell(self, amount, price):
##        print '[MtGoxCore: sell]'
        return self.__mkOrder('sell', amount, price)

    def cancel(self, oid):
        """Output:
        {btcs: string,
         usds: string,
         orders: [order]}"""
##        print '[MtGoxCore: cancel]'
        return self.req(MtGoxCore.URL % ('cancelOrder', ''), {'oid': oid})

    def orders(self):
##        print '[MtGoxCore: orders]'
        return self.req(MtGoxCore.URL % ('getOrders', ''))

    def withdraw(self, amount, address):
        return self.req(MtGoxCore.URL % ('withdraw', ''))
