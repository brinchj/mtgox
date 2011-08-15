import urllib2, time, convert, random, logging

from threading import Thread, Lock
from mtgoxcore import MtGoxCore
from decimal import Decimal

INTERVAL = 1
BUY_FEE = Decimal('0.003')
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
        logger.info('Syncronising orders...')
        logger.debug('Acquiring lock...')
        self._lock.acquire()
        logger.debug('Lock acquired!')
        if self._orders == {}:
            logger.info('Nothing to do; Syncronisation done!')
            logger.debug('Releasing lock')
            self._lock.release()
            return
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
        def callback(x, f, *args):
            logger.debug('Callback for %s: %s' % (x['oid'], f))
            try:
                x['callbacks'][f](o, *args)
            except:
                pass

        cancelled = None
        data = self._core.orders()
        orders = convert.orders(data)
        balance = convert.balance(data)
        while True:
            logger.debug('Building indexes')
            (oldbids, oldasks) = index(self._orders.values())
            (oldbtcs, oldusds) = (self._balance['btcs'], self._balance['usds'])
            (newbids, newasks) = index(orders)
            (newbtcs, newusds) = (balance['btcs'], balance['usds'])

            # check for cancelation
            if cancelled is not None:
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
                if abs(delta1 - real_delta) > abs(delta2 - real_delta):
                    # Was cancelled - prune local orders
                    logger.debug('Order was cancelled: %s' % cancelled['oid'])
                    (live, dead) = partition(d[cancelled['price']])
                    dead_left = False
                    for o in dead:
                        if cancelled['amount'] >= o['amount']:
                            oid = o['oid']
                            if o['status'] == 'timed_out':
                                callback(o, 'onTimeout')
                            else:
                                callback(o, 'onCancel')
                            del self._orders[oid]
                            cancelled['amount'] -= o['amount']
                        else:
                            dead_left = True
                    # If the cancelled amount was too large:
                    if not dead_left and not cancelled['amount'].is_zero():
                        logger.debug('Cancelled order too large; replacing...')
                        cancelled['oid'] = f(cancelled['amount'],
                                             cancelled['price'])
                        cancelled['status'] = 'pending'
                        cancelled['date'] = time.time()
                        orders.append(cancelled)
                        logger.debug('Done!')
                    cancelled = None
                    continue # rebuild indexes
                else:
                    logger.debug('Order was not cancelled: %s' % cancelled['oid'])
                    # Was not cancelled - do nothing
                    cancelled = None

            # check for progress and/or filled orders
            try:
                price = (newbtcs - oldbtcs) / (oldusds - newusds)
            except:
                price = Decimal(0)
            def process(old, new):
                logger.debug('Processing orders...')
                to_cancel = []
                for (p, os) in old.items():
                    oldamount = sum_amounts(os)
                    if p in new:
                        newamount = sum_amounts(new[p])
                    else:
                        newamount = Decimal(0)
                    amount = oldamount - newamount
                    (live, dead) = partition(os)
                    os = live + dead
                    for o in os:
                        oid = o['oid']
                        if o['amount'] <= amount:
                            # filled
                            callback(o, 'onProgress', o['amount'], price)
                            callback(o, 'onFilled')
                            del self._orders[oid]
                            amount -= o['amount']
                            continue
                        if not amount.is_zero():
                            # part filled
                            callback(o, 'onProgress', amount, price)
                            self._orders[oid]['amount'] -= amount
                        if o['status'] is not 'open':
                            # we're processing non-open orders -- cancel!
                            logger.debug('Need to cancel at price %.2f' % p)
                            to_cancel += new[p]
                        break
                logger.debug('Processing done!')
                return to_cancel
            to_cancel = \
                process(oldbids, newbids) + \
                process(oldasks, newasks)
            # we're now up to date
            self._balance = balance

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
            logger.debug('Cancelling order: %s' % cancelled['oid'])
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
        oid = f(amount, price)['oid']
        self._orders[oid] = {'oid': oid,
                             'amount': amount,
                             'orig_amount': amount,
                             'price': price,
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
