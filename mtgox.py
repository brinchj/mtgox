import urllib2, time, convert, random, logging

from threading import Thread, Lock
from mtgoxcore import MtGoxCore
from decimal import Decimal

INTERVAL = 1
BUY_FEE = Decimal('0.0065')
SELL_FEE = Decimal('0')

logger = logging.getLogger('MtGox')

class MtGox(Thread):
    def __init__(self, key, sec):
        Thread.__init__(self)

        self._core = MtGoxCore(key, sec)
        # start with a clean order book
        logger.info('Initialising; Swiping order book...')
        while True:
            data = self._core.orders()
            oids = map(lambda o: o['oid'],
                       data['orders']
                       )
            logger.debug(oids)
            if oids == []:
                break
            map(self._core.cancel, oids)
        logger.info('Order book is clean')

        self._orders = {}
        self._balance = convert.balance(data)
        self._lock = Lock()
        self._running = False
        logger.info('Initialisation done!')

    def run(self):
        self._running = True
        logger.info('Syncronisation thread started (hi mom!)')
        while self._running:
            self._sync()
            time.sleep(INTERVAL)
        logger.info('Ending syncronisation thread')

    def stop(self):
        self._running = False

    def _sync(self):
        # logger.info('Syncronising orders...')
        # logger.debug('Acquiring lock...')
        self._lock.acquire()
        # logger.debug('Lock acquired!')
        if self._orders == {}:
            # logger.info('Nothing to do; Syncronisation done!')
            # logger.debug('Releasing lock')
            self._lock.release()
            return
        logger.info('Syncronising orders...')
        def index(orders):
            bids = {}
            asks = {}
            for o in orders:
                p = o['price']
                if o['type'] == 'bid':
                    d = bids
                else:
                    d = asks
                if not p in d:
                    d[p] = []
                d[p].append(o)
            return (bids, asks)
        def sum_amounts(xs):
            return sum(map(lambda x: x['amount'], xs))
        def tot_amounts(xs):
            return sum(map(sum_amounts, xs.values()))
        def partition(orders):
            live = []
            dead = []
            now = time.time()
            for o in orders:
                if o['status'] != 'open':
                    dead.append(o)
                elif o['ttl'] is not None and \
                        o['date'] + o['ttl'] < now:
                    o['status'] = 'timed_out'
                    dead.append(o)
                else:
                    live.append(o)
            f = lambda x: x['date']
            return (sorted(live, key = f),
                    sorted(dead, key = f))
        def callback(o, f, *args):
            logger.debug('Callback for %s: %s%s' % (o['oid'], f, repr(args)))
            try:
                o['callbacks'][f](o, *args)
            except Exception, e:
                logger.debug('Callback %s for order %s failed: %s' % (f, o['oid'], e))
                pass

        cancelled = None
        data = self._core.orders()
        orders = convert.orders(data)
        balance = convert.balance(data)
        while True:
            logger.debug('Building indexes')
            logger.debug('Orderbook from MtGox: %s' % data)
            (oldbids, oldasks) = index(self._orders.values())
            (oldbtcs, oldusds) = (self._balance['btcs'], self._balance['usds'])
            (newbids, newasks) = index(orders)
            (newbtcs, newusds) = (balance['btcs'], balance['usds'])

            # check for cancelation
            if cancelled is not None:
                logger.debug('Checking if %s was cancelled' % cancelled['oid'])
                bought = tot_amounts(oldbids) - tot_amounts(newbids)
                sold = tot_amounts(oldasks) - tot_amounts(newasks)
                delta1 = bought * (1 - BUY_FEE) - sold * (1 - SELL_FEE)
                if cancelled['type'] == 'bid':
                    delta2 = (bought - cancelled['amount']) * (1 - BUY_FEE) - \
                        sold * (1 - SELL_FEE)
                    d = oldbids
                    f = self._core.buy
                else:
                    delta2 = bought * (1 - BUY_FEE) - \
                        (sold - cancelled['amount']) * (1 - SELL_FEE)
                    d = oldasks
                    f = self._core.sell
                real_delta = newbtcs - oldbtcs
                logger.debug('Sold %.2f -- Bough %.2f' % (sold, bought))
                logger.debug('Deltas: not cancelled %.2f -- cancelled %.2f -- real %.2f' % (delta1, delta2, real_delta))
                if abs(abs(delta1) - abs(real_delta)) > abs(abs(delta2) - abs(real_delta)):
                    # Was cancelled - prune local orders
                    logger.debug('Order was cancelled: %s at %.2f USD' % (cancelled['oid'], cancelled['price']))
                    (live, dead) = partition(d[cancelled['price']])
                    logger.debug('Live: %s', live)
                    logger.debug('Dead: %s', dead)
                    dead_left = False
                    for o in dead:
                        if cancelled['amount'] >= o['amount']:
                            oid = o['oid']
                            cancelled['amount'] -= o['amount']
                            o['cancelled_amount'] = o['amount']
                            o['amount'] = Decimal(0)
                            if o['status'] == 'timed_out':
                                callback(o, 'onTimeout')
                            else:
                                callback(o, 'onCancel')
                            del self._orders[oid]
                            continue
                        if not cancelled['amount'].is_zero():
                            o['cancelled_amount'] += cancelled['amount']
                            o['amount'] -= cancelled['amount']
                        dead_left = True
                        break
                    # If the cancelled amount was too large:
                    if not dead_left and not cancelled['amount'].is_zero():
                        logger.debug('Cancelled order too large; replacing...')
                        f(cancelled['amount'], cancelled['price'])
                        logger.debug('Done!')
                    cancelled = None
                    continue # rebuild indexes
                else:
                    logger.debug('Order was not cancelled: %s as %.2f USD' % (cancelled['oid'], cancelled['price']))
                    # Was not cancelled - do nothing
                    cancelled = None

            # check for progress and/or filled orders
            try:
                price = (oldusds - newusds) / (newbtcs - oldbtcs)
            except:
                price = Decimal(0)
            def process(old, new):
                logger.debug('Processing orders...')
                logger.debug('Old: %s', old)
                logger.debug('New: %s', new)
                to_cancel = []
                for (p, os) in old.items():
                    logger.debug('Processing at price %.2f USD', p)
                    oldamount = sum_amounts(os)
                    if p in new:
                        newamount = sum_amounts(new[p])
                    else:
                        newamount = Decimal(0)
                    amount = oldamount - newamount
                    (live, dead) = partition(os)
                    os = live + dead
                    logger.debug('Bought %.2f BTC', amount)
                    logger.debug('Orders to process: %s', os)
                    for o in os:
                        oid = o['oid']
                        if o['amount'] <= amount:
                            # filled
                            amount -= o['amount']
                            a = o['amount']
                            o['filled_amount'] += o['amount']
                            o['amount'] = Decimal(0)
                            callback(o, 'onProgress', a, price)
                            callback(o, 'onFilled')
                            del self._orders[oid]
                            continue
                        if not amount.is_zero():
                            # part filled
                            o['filled_amount'] += amount
                            o['amount'] -= amount
                            callback(o, 'onProgress', amount, price)
                        if o['status'] is not 'open':
                            # we're processing non-open orders -- cancel!
                            logger.debug('Need to cancel at price %.2f' % p)
                            logger.debug('Candidates for cancelation: %s', new[p])
                            to_cancel += new[p]
                        break
                logger.debug('Processing done!')
                return to_cancel
            to_cancel = \
                process(oldbids, newbids) + \
                process(oldasks, newasks)
            # we're now up to date
            logger.debug('Old balance was: %s', self._balance)
            self._balance = balance
            logger.debug('New balance is: %s', self._balance)

            # check for orders to cancel
            if to_cancel == []:
                logger.info('Nothing to cancel; Synchronisation done!')
                break
            # pick 'invalid' orders first, then 'open', last 'pending'
            def key(x):
                s = x['status']
                if s == 'invalid':
                    return 0
                elif s == 'open':
                    return 1
                elif s == 'pending':
                    return 2
                return 0
            random.shuffle(to_cancel) # avoid always going for lowest bid
            cancelled = sorted(to_cancel, key = key)[0]
            # cancelled = to_cancel[random.randrange(0, len(to_cancel))]
            logger.debug('Cancelling order: %s at %.2f USD' % (cancelled['oid'], cancelled['price']))
            data = self._core.cancel(cancelled['oid'])
            orders = convert.orders(data)
            balance = convert.balance(data)
        #end while
        logger.debug('Releasing lock')
        self._lock.release()

    def ticker(self):
        return convert.ticker(self._core.ticker())

    def depth(self):
        return convert.depth(self._core.depth())

    def trades(self, since = None):
        return convert.trades(self._core.trades(since))

    def balance(self):
        return self._balance

    def trade(self, amount, price, ttl = None,
              onProgress = None,
              onFilled = None,
              onCancel = None,
              onTimeout = None):
        if amount > 0:
            f = self._core.buy
            t = 'bid'
        else:
            f = self._core.sell
            t = 'ask'
            amount = -amount
        self._lock.acquire()
        data = f(amount, price)
        if 'oid' not in data:
            return None
        oid = data['oid']
        os = filter(lambda o: o['oid'] == oid, data['orders'])
        if os == []:
            return None
        o = convert.order(os[0])
        self._orders[oid] = {'oid': oid,
                             'amount': o['amount'],
                             'filled_amount': Decimal(0),
                             'cancelled_amount': Decimal(0),
                             'orig_amount': o['amount'],
                             'price': o['price'],
                             'status': 'open',
                             'ttl': ttl,
                             'date': time.time(),
                             'type': t,
                             'callbacks':
                                 {'onProgress': onProgress,
                                  'onFilled': onFilled,
                                  'onCancel': onCancel,
                                  'onTimeout': onTimeout}
                             }
        self._lock.release()
        return oid

    def register(self, oid, callback, fun):
        if oid in self._orders:
            self._orders[oid]['callbacks'][callback] = fun

    def buy(self, *args):
        return self.trade(*args)

    def sell(self, amount, *args):
        return self.trade(-amount, *args)

    def cancel(self, oid):
        if oid in self._orders:
            self._orders[oid]['status'] = 'cancelled'
            self._sync()

    def cancel_all(self):
        for oid in self._orders.keys():
            self._orders[oid]['status'] = 'cancelled'
        self._sync()

    def orders(self):
        return self._orders.values()

if __name__ == '__main__':
    from config import KEY, SEC
    gox = MtGox(KEY, SEC)
    gox.start()
