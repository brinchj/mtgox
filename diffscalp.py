import time

from mtgoxcore import MtGoxCore
from tradehillcore import TradehillCore
from decimal import Decimal

GOXFEE = Decimal('0.0053')
HILFEE = Decimal('0.0054') # Referral code

gox = MtGoxCore()
hil = TradehillCore()

while True:
    goxtick = gox.ticker()['ticker']
    hiltick = hil.ticker()['ticker']
    goxsell = Decimal(goxtick['buy']) * (1 - GOXFEE)
    goxbuy = Decimal(goxtick['sell']) / (1 - GOXFEE)
    hilsell = Decimal(hiltick['buy']) * (1 - HILFEE)
    hilbuy = Decimal(hiltick['sell']) / (1 - HILFEE)
    if hilbuy < goxsell:
        print time.ctime(time.time())
        print '  Buy on Tradehill for %.3f, sell on MtGox for %.3f --\
 make %.2f%% profit!' % (hilbuy, goxsell, 100 * (goxsell - hilbuy) / hilbuy)
    if goxbuy < hilsell:
        print time.ctime(time.time())
        print '  Buy on MtGox for %.3f, sell on Tradehill for %.3f --\
 make %.2f%% profit!' % (goxbuy, hilsell, 100 * (hilsell - goxbuy) / goxbuy)
    time.sleep(60)
