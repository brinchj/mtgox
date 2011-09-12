import logging

from config import KEY, SEC
from mtgox import MtGox
from scalper import Scalper
from decimal import Decimal

logging.basicConfig(
    filename = 'bot.log',
    filemode = 'w',
    format = '[%(asctime)s, %(threadName)s, %(name)s, %(levelname)s]\n   %(message)s',
    # format = '%(name)-12s: %(message)s',
    datefmt = '%d/%m %H:%M:%S',
    )

# logging.getLogger('MtGoxCore').setLevel(logging.DEBUG)
# logging.getLogger('MtGox').setLevel(logging.DEBUG)
logging.getLogger('MtGoxCore').setLevel(logging.NOTSET)
logging.getLogger('MtGox').setLevel(logging.DEBUG)


gox = MtGox(KEY, SEC)
gox.start()
scalper = Scalper(gox, Decimal(14), Decimal(80))
scalper.start()
