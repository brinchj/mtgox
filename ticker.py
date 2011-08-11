import time

from mtgox import MtGox

gox = MtGox()

while True:
    try:
        data = gox.ticker()['ticker']
        print "Buy  %r" % data['buy']
        print "Sell %r" % data['sell']
        print "Last %r" % data['last']
        print ""
    except KeyboardInterrupt:
        exit(0)
    except:
        pass
    time.sleep(10)
