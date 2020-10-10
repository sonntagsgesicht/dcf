# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .interestratecurve import ZeroRateCurve
from .cashflow import CashFlowLegList


def _simple_bracketing(func, a, b, precision=1e-13):
    """ find root by _simple_bracketing an interval

    :param callable func: function to find root
    :param float a: lower interval boundary
    :param float b: upper interval boundary
    :param float precision: max accepted error
    :rtype: tuple
    :return: :code:`(a, m, b)` of last recursion step with :code:`m = a + (b-a) *.5`

    """
    fa, fb = func(a), func(b)
    if fb < fa:
        f = (lambda x: -func(x))
        fa, fb = fb, fa
    else:
        f = func

    if not fa <= 0. <= fb:
        msg = "_simple_bracketing function must be loc monotone between %0.4f and %0.4f \n" % (a, b)
        msg += "and _simple_bracketing 0. between  %0.4f and %0.4f." % (fa, fb)
        raise AssertionError(msg)

    m = a + (b - a) * 0.5
    if abs(b - a) < precision and abs(fb - fa) < precision:
        return a, m, b

    a, b = (m, b) if f(m) < 0 else (a, m)
    return _simple_bracketing(f, a, b, precision)


def get_present_value(cashflow_list, discount_curve, valuation_date=None, include_value_date=True):
    valuation_date = discount_curve.origin if valuation_date is None else valuation_date

    # filter flows
    if include_value_date:
        pay_dates = list(d for d in cashflow_list.domain if valuation_date <= d)
    else:
        pay_dates = list(d for d in cashflow_list.domain if valuation_date < d)

    # discount flows
    value_flows = zip(pay_dates, cashflow_list[pay_dates])
    values = (discount_curve.get_discount_factor(valuation_date, t) * a for t, a in value_flows)
    return sum(values)


def get_yield_to_maturity(cashflow_list, valuation_date=None, present_value=0.):
    valuation_date = cashflow_list.origin if valuation_date is None else valuation_date

    # set error function
    def err(current):
        discount_curve = ZeroRateCurve([valuation_date], [current])
        return get_present_value(cashflow_list, discount_curve, valuation_date) - present_value

    # run bracketing
    _, ytm, _ = _simple_bracketing(err, -0.1, .2, 1e-2)
    return ytm


def get_interest_accrued(cashflow_list, valuation_date):
    if cashflow_list.domain[0] < valuation_date < cashflow_list.domain[-1]:
        if isinstance(cashflow_list, CashFlowLegList):
            return sum(get_interest_accrued(leg, valuation_date) for leg in cashflow_list.legs)
        last_payment_date = list(d for d in cashflow_list.domain if valuation_date > d)[0]
        next_payment_date = list(d for d in cashflow_list.domain if valuation_date <= d)[0]
        remaining = cashflow_list.day_count(valuation_date, next_payment_date)
        total = cashflow_list.day_count(last_payment_date, next_payment_date)
        return cashflow_list[next_payment_date] * (1. - remaining / total)
    return 0.


def get_par_rate(cashflow_list, discount_curve, valuation_date=None, present_value=0.):
    valuation_date = cashflow_list.origin if valuation_date is None else valuation_date
    fixed_rate = cashflow_list.fixed_rate

    # set error function
    def err(current):
        cashflow_list.fixed_rate = current
        return get_present_value(cashflow_list, discount_curve, valuation_date) - present_value

    # run bracketing
    _, par, _ = _simple_bracketing(err, -0.1, .2, 1e-7)

    # restore fixed rate
    cashflow_list.fixed_rate = fixed_rate
    return par
