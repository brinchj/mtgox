from hrbot import HrBot

import pickle

with open('history.prices.pickled') as f:
    t = pickle.load(f)

bot = HrBot()

for p in t[-50000:]:
    bot.update([p])
    bot.action(p * 1.02, p * 0.98)
