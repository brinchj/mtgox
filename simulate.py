from hrbot import HrBot

import pickle

with open('history.price.pickled') as f:
    t = pickle.load(f)

bot = HrBot()

for p in t:
    bot.update([p])
    bot.action(p * 1.01, p * 0.99)
