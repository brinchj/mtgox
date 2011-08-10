import urllib
import urllib2
import time
import hmac
import json


from base64 import b64encode, b64decode
from hashlib import sha512 as hash

def hmac_digest(data, key):
    return hmac.new(key, data, hash).digest()


def get_nonce():
    return str(int(time.time() * 1000))


def post(url, data='', headers={}):
    req = urllib2.Request(url, data, headers)
    res = urllib2.urlopen(req, timeout=30)
    return res.read()


class MtGox:
    URL = 'https://mtgox.com/api/0/%s.php?%s'

    def __init__(self, key, secret):
        self.key = key
        self.sec = secret

    def stop(self):
        self.running = False

    def req(self, url, values={'nonce': None}):
        nonce = get_nonce()
        values['nonce'] = nonce
        post_data = urllib.urlencode(values)

        headers = {
            'Rest-Key': self.key,
            'Rest-Sign': b64encode(hmac_digest(post_data, b64decode(self.sec)))
            }

        return json.loads(post(url, post_data, headers))

    def trades(self, since = None):
        if since is not None:
            param = 'since=' + str(since)
        else:
            param = ''
        return self.req(MtGox.URL % ('data/getTrades', param))

    def balance(self):
        return self.req(MtGox.URL % ('getFunds', ''))

    def depth(self):
        return self.req(MtGox.URL % ('data/getDepth', ''))

    def __mkOrder(self, kind, amount, price):
        return self.req(MtGox.URL % (kind + 'BTC', ''),
                        {'amount': str(amount), 'price': str(price)}
                        )

    def buy(self, amount, price):
        return self.__mkOrder('buy', amount, price)

    def sell(self, amount, price):
        return self.__mkOrder('sell', amount, price)

    def cancel(self, oid):
        return self.req(MtGox.URL % ('cancelOrder', ''), {'oid': oid})

    def orders(self):
        return self.req(MtGox.URL % ('getOrders', ''))
