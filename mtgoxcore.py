import urllib, urllib2, ssl, post, time, hmac, json, logging

from base64 import b64encode, b64decode
from hashlib import sha512 as hash

logger = logging.getLogger('MtGoxCore')

def _hmac_digest(data, key):
    return hmac.new(key, data, hash).digest()

def _get_nonce():
    nonce = str(int(time.time() * 1000))
    logger.info('Produced nonce: %s' % nonce)
    return nonce

class MtGoxCore:
    URL = 'https://mtgox.com/api/0/%s.php?%s'

    def __init__(self, key = '', secret = ''):
        self.key = key
        self.sec = secret

    def req(self, url, values = {'nonce': None}):
        while True:
            nonce = _get_nonce()
            values['nonce'] = nonce
            post_data = urllib.urlencode(values)

            headers = {
                'Rest-Key': self.key,
                'Rest-Sign': b64encode(_hmac_digest(post_data, b64decode(self.sec)))
                }

            js = post.post(url, post_data, headers)
            try:
                dt = json.loads(js)
            except:
                logger.info('Got invalid JSON; retrying')
                logger.debug(js)
                continue
            if 'error' in dt:
                logger.info('MtGox reported an error; retrying')
                logger.debug(str(dt))
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
        logger.info('ticker()')
        return self.req(MtGoxCore.URL % ('data/ticker', ''))

    def depth(self):
        """Output:
        {bids: [option]],
         asks: [option]}

         Where 'option' is a list of two floats;
         first one is price, second is amount.

         Bids and asks are ordered by increasing price."""
        logger.info('depth()')
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
        logger.info('trades(%s)' % since)
        return self.req(MtGoxCore.URL % ('data/getTrades', param))

    def balance(self):
        """Output:
        {btcs: string,
         usds: string}"""
        logger.info('balance()')
        return self.req(MtGoxCore.URL % ('getFunds', ''))

    def __mkOrder(self, kind, amount, price):
        return self.req(MtGoxCore.URL % (kind + 'BTC', ''),
                        {'amount': str(amount), 'price': str(price)}
                        )

    def buy(self, amount, price):
        logger.info('buy(%s, %s)' % (amount, price))
        return self.__mkOrder('buy', amount, price)

    def sell(self, amount, price):
        logger.info('sell(%s, %s)' % (amount, price))
        return self.__mkOrder('sell', amount, price)

    def cancel(self, oid):
        """Output:
        {btcs: string,
         usds: string,
         orders: [order]}"""
        logger.info('cancel(%s)' % oid)
        return self.req(MtGoxCore.URL % ('cancelOrder', ''), {'oid': oid})

    def orders(self):
        logger.info('orders()')
        return self.req(MtGoxCore.URL % ('getOrders', ''))

    def withdraw(self, amount, address):
        logger.info('withdraw(%s, %s)' % (amount, address))
        return self.req(MtGoxCore.URL % ('withdraw', ''))
