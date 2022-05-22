# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


DEFAULT_AMOUNT = 1.
FIXED_RATE = 0.01


def same(num, amount=DEFAULT_AMOUNT):
    r""" all same payment plan

    :param num: number of payments $n$
    :param amount: amount of each payment $N$
    :return: list(float) payment plan $X_i$ for $i=1 \dots n$

    Payment plan with
    $$X_i = N \text{ for all } i=1 \dots n$$
    """
    return [amount] * int(num)


def bullet(num, amount=DEFAULT_AMOUNT):
    r""" bullet payment plan

    :param num: number of payments $n$
    :param amount: amount of last bullet payment $N$
    :return: list(float) payment plan $X_i$ for $i=1 \dots n$

    Payment plan with
    $$X_i = N \text{ for } i=n \text{ else } 0$$
    """
    return [0.] * (int(num) - 1) + [amount]


def amortize(num, amount=DEFAULT_AMOUNT):
    r""" linear amortize payment plan

    :param num: number of payments $n$
    :param amount: amount of total sum of payment $N$
    :return: list(float) payment plan $X_i$ for $i=1 \dots n$

    Payment plan with
    $$X_i = N/n \text{ for } i=1 \dots n$$
    """
    return [amount / num] * int(num)


def annuity(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
    r""" fixed rate annuity payment plan

    :param num: number of payments $n$
    :param amount: amount of total sum of payment $N$
    :param fixed_rate: amortization rate $r$
    :return: list(float) payment plan $X_i$ for $i=1 \dots n$

    Payment plan
    $$X_i = \frac{r}{(1 + r)^{n-i}} \cdot N \text{ for } i=1 \dots n$$
    """
    q = 1. + fixed_rate
    a = amount * (q - 1) / (q ** int(num) - 1)
    return list(a * q ** i for i in range(int(num)))


def consumer(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
    r""" consumer loan annuity payment plan

    :param num: number of payments $n$
    :param amount: amount of payment total $N$
    :param fixed_rate: amortization rate $r$
    :return: list(float) payment plan $X_i$ for $i=1 \dots n$

    Actutal payment plan total $T = N (1 + n \cdot r)$ such that
    $$X_i = T / n$$
    """
    total = amount * (1 + num * fixed_rate)
    return [total / num] * int(num)


def outstanding(plan, amount=DEFAULT_AMOUNT, sign=False):
    r"""sums up plans to remaining oustanding anmount

    :param plan: payment plan $X_i$
    :param amount: inital amount $N$
    :param sign: $\sigma$ sign of plan payments (optional, default: **-1**)
    :return: list(float) outstanding plan

    Adds or substracts payment plan payments $X_i$ from inital amount $N$
    such that
    $$O_i = N + \sigma \cdot \sum_{k=1}^{i-1} X_i$$
    """
    sgn = 1 if sign else -1
    out = [amount]
    for p in plan[:-1]:
        amount += sgn * p
        out.append(amount)
    return out
