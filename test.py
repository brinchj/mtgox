from __future__ import print_function

import time

from mtgox import MtGox
from broker import Broker, intBTC, intUSD

from config import KEY, SEC


try:
    gox = MtGox(KEY, SEC)
    broker = Broker(gox)
    broker.start()

    # broker.cancelAll()
    bal = broker.balance()
    print(bal)
    penge = broker.offer({'btcs': intBTC(0.1), 'usds': intUSD(2)})
    print(penge)
    penge = broker.offer(bal)
    print(penge)

    # print(broker.trade(intBTC(-0.1), intUSD(15), 1,
    #                    lambda oid: print("Success", oid),
    #                    lambda oid: print("Timeout", oid)
    #                    )
    #       )
    # print(broker.orders())
    # print broker.trade(4 * 10**8, 10.1 * 10**5)
    # print broker.trade(4 * 10**8, 10.2 * 10**5)

    # print len(broker.orders())
    # broker.cancelAll()
    # print len(broker.orders())
    # time.sleep(10)
    broker.join()

finally:
    # pass
    broker.stop()
