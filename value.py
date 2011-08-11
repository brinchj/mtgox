import time

from mtgox import MtGox
from broker import Broker

from config import KEY, SEC


gox = MtGox(KEY, SEC)
broker = Broker(gox)
while True:
    try:
        val = broker.value()
        print "%.2fBTC / %.2fUSD" % (val['btcs'], val['usds'])
    except KeyboardInterrupt:
        exit(0)
    except:
        pass
    time.sleep(10)

