import time

from mtgox import MtGox
from broker import Broker

from config import KEY, SEC

gox = MtGox(KEY, SEC)
broker = Broker(gox)
broker.start()

print broker.balance()
print broker.offer(-1 * 10**8)

try:
    time.sleep(0)
finally:
    broker.stop()
