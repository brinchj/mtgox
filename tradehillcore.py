import urllib, post, json, logging

logger = logging.getLogger('TradehillCore')

class TradehillCore:
    URL = 'https://api.tradehill.com/APIv1/USD/%s'

    def __init__(self, name = '', passwd = ''):
        self.name = name
        self.passwd = passwd

    def req(self, url, values = {}):
        while True:
            if values != {}:
                values['user'] = self.user
                values['pass'] = self.passwd
            post_data = urllib.urlencode(values)

            js = post.post(url, post_data)
            try:
                dt = json.loads(js)
            except:
                logger.info('Got invalid JSON; retrying')
                logger.debug(js)
                continue
            return dt

    def orderbook(self):
        logger.info('orderbook')
        return self.req(TradehillCore.URL % 'Orderbook')

    def trades(self):
        logger.info('trades')
        return self.req(TradehillCore.URL % 'Trades')

    def ticker(self):
        logger.info('ticker()')
        return self.req(TradehillCore.URL % 'Ticker')
