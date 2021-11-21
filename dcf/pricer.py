# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.5, copyright Sunday, 21 November 2021
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .interestratecurve import ZeroRateCurve, CashRateCurve
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


def get_present_value(cashflow_list, discount_curve,
                      valuation_date=None, include_value_date=True):
    if valuation_date is None:
        valuation_date = cashflow_list.origin

    # filter flows
    if include_value_date:
        pay_dates = list(d for d in cashflow_list.domain if valuation_date <= d)
    else:
        pay_dates = list(d for d in cashflow_list.domain if valuation_date < d)

    # discount flows
    value_flows = zip(pay_dates, cashflow_list[pay_dates])
    values = (discount_curve.get_discount_factor(valuation_date, t) * a for t, a in value_flows)
    return sum(values)


def get_yield_to_maturity(cashflow_list,
                          valuation_date=None, present_value=0., **kwargs):
    if valuation_date is None:
        valuation_date = cashflow_list.origin

    # set error function
    def err(current):
        discount_curve = ZeroRateCurve([valuation_date], [current], **kwargs)
        pv = get_present_value(cashflow_list, discount_curve, valuation_date)
        return pv - present_value

    # run bracketing
    _, ytm, _ = _simple_bracketing(err, -0.1, .2, 1e-2)
    return ytm


def get_interest_accrued(cashflow_list, valuation_date):
    """ calculates interest accrued for rate cashflows

    :param cashflow_list: requires a `day_count` property
    :param valuation_date: calculation date
    :return:
    """
    if cashflow_list.origin < valuation_date < cashflow_list.domain[-1]:
        if isinstance(cashflow_list, CashFlowLegList):
            return sum(get_interest_accrued(leg, valuation_date)
                       for leg in cashflow_list.legs)
        last = max((d for d in cashflow_list.domain if valuation_date > d),
                   default=cashflow_list.origin)

        next = list(d for d in cashflow_list.domain if valuation_date <= d)[0]
        if hasattr(cashflow_list, 'day_count'):
            remaining = cashflow_list.day_count(valuation_date, next)
            total = cashflow_list.day_count(last, next)
            return cashflow_list[next] * (1. - remaining / total)
    return 0.


def get_par_rate(cashflow_list, discount_curve,
                 valuation_date=None, present_value=0.):
    if valuation_date is None:
        valuation_date = cashflow_list.origin

    # todo: cashflow_list.payoff.fixed_rate
    fixed_rate = cashflow_list.fixed_rate

    # set error function
    def err(current):
        cashflow_list.fixed_rate = current
        pv = get_present_value(cashflow_list, discount_curve, valuation_date)
        return pv - present_value

    # run bracketing
    _, par, _ = _simple_bracketing(err, -0.1, .2, 1e-7)

    # restore fixed rate
    cashflow_list.fixed_rate = fixed_rate
    return par


def get_basis_point_value(cashflow_list, discount_curve,
                          delta_curve=None, valuation_date=None):
    if isinstance(cashflow_list, CashFlowLegList):
        return sum(get_basis_point_value(
            leg, discount_curve, delta_curve, valuation_date)
                   for leg in cashflow_list.legs)

    pv = get_present_value(cashflow_list, discount_curve, valuation_date)

    delta_curve = discount_curve if delta_curve is None else delta_curve
    # check if curve is CashRateCurve
    if isinstance(delta_curve, CashRateCurve):
        basis_point_curve = CashRateCurve([delta_curve.origin], [0.0001])
    else:
        basis_point_curve = ZeroRateCurve([delta_curve.origin], [0.0001])
    shifted_curve = delta_curve + basis_point_curve

    if delta_curve == discount_curve:
        discount_curve = shifted_curve

    # todo: cashflow_list.payoff_model.forward_curve
    fwd_curve = getattr(cashflow_list, 'forward_curve', None)
    if fwd_curve == delta_curve:
        # replace delta_curve by shifted_curve
        cashflow_list.forward_curve = shifted_curve
    sh = get_present_value(cashflow_list, discount_curve, valuation_date)
    if fwd_curve == delta_curve:
        # restore delta_curve by shifted_curve
        cashflow_list.forward_curve = shifted_curve

    return sh - pv
