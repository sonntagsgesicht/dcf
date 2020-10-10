# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


DEFAULT_AMOUNT = 1.
FIXED_RATE = 0.01


def same(num, amount=DEFAULT_AMOUNT):
    return [amount] * int(num)


def bullet(num, amount=DEFAULT_AMOUNT):
    return [0.] * (int(num) - 1) + [amount]


def amortize(num, amount=DEFAULT_AMOUNT):
    return [amount / num] * int(num)


def annuity(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
    q = 1. + fixed_rate
    a = amount * (q - 1) / (q ** int(num) - 1)
    return list(a * q ** i for i in range(int(num)))


def consumer(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
    total = amount * (1 + num * fixed_rate)
    return [total / num] * int(num)


def outstanding(plan, amount=DEFAULT_AMOUNT, sign=False):
    sgn = 1 if sign else -1
    out = [amount]
    for p in plan[:-1]:
        amount += sgn * p
        out.append(amount)
    return out
