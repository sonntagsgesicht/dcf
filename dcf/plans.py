# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht
# Version:  1.0, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import log

from curves.numerics import solve, EPS

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


def _annuity(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
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


def iam(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
    q = 1 + fixed_rate
    return [amount * fixed_rate * (q ** i) for i in range(num)]


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


def annuity(num=None, amount=None, fixed_rate=None, *,
            redemption_rate=None, annuity_amount=None):
    f"""list of redemption payments in fixed annuity payments

    :param num: number of periods
        (optional: if not given **num** will be derived from
        **fixed_rate** and **redemption_rate**)
    :param amount: total amount
        (optional: if neither **amount** nor **annuity_amount**
        is given, **amount** will be {DEFAULT_AMOUNT} is used)
    :param fixed_rate: interest rate per period
        (optional: if not given **fixed_rate** will be derived from
        **num** and **redemption_rate**.
        if even **num** or **redemption_rate** are not given,
        **fixed_rate** will be {FIXED_RATE})
    :param redemption_rate: initial redemption rate
        (optional: if not given **redemption_rate** will be derived from
        **num** and **fixed_rate**)
    :param annuity_amount: fixed annuity amount
    :return: list of redemption payments

    """

    def _r(x, n=num):
        """redemption_rate"""
        return x / ((x + 1) ** int(n) - 1)

    if num is not None:
        if redemption_rate is not None:
            if fixed_rate is None:
                fixed_rate = solve(_r, a=FIXED_RATE)

            elif abs(_r(fixed_rate) - redemption_rate) < EPS:
                msg = "inconsistent arguments for " \
                      "'num', 'fixed_rate' and 'redemption_rate'"
                raise ValueError(msg)

        elif fixed_rate is not None:
            redemption_rate = _r(fixed_rate, num)

        else:
            fixed_rate = FIXED_RATE
            redemption_rate = _r(fixed_rate, num)

    elif fixed_rate is not None:

        if redemption_rate is not None:
            num = log(1 + fixed_rate / redemption_rate) / log(1 + fixed_rate)

        elif amount is not None and annuity_amount is not None:
            redemption_rate = annuity_amount / amount - fixed_rate
            num = log(1 + fixed_rate / redemption_rate) / log(1 + fixed_rate)

    elif amount is not None and annuity_amount is not None:
        fixed_rate = annuity_amount / amount - redemption_rate
        num = log(1 + fixed_rate / redemption_rate) / log(1 + fixed_rate)

    else:
        msg = "no arguments for 'num', 'fixed_rate' and 'redemption_rate'"
        raise ValueError(msg)

    if amount is None and annuity_amount is None:
        amount = DEFAULT_AMOUNT

    elif amount is None:
        amount = annuity_amount / (fixed_rate + redemption_rate)

    return _annuity(int(num), amount, fixed_rate)
