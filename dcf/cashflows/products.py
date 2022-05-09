# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


try:
    import businessdate as bd
except ImportError:
    bd = None

from .cashflow import CashFlowLegList, FixedCashFlowList, RateCashFlowList

TODAY = 0.0
MATURITY = 10
BOND_TENOR = 1
SWAP_TENOR = 3 / 12


def _interest_payment_dates(
        start_date, end_date, period, convention, holidays):
    if bd and isinstance(start_date, bd.BusinessDate):
        start_date = bd.BusinessDate(start_date)
        if bd.BusinessPeriod.is_businessperiod(end_date):
            end_date = start_date + bd.BusinessPeriod(end_date)
        end_date = bd.BusinessDate(end_date)

        payment_date_list = bd.BusinessSchedule(
            start_date, end_date, period, end_date)
        payment_date_list.adjust(convention, holidays)
        return payment_date_list[1:]

    else:
        payment_date_list = [end_date]
        cnt = 1
        while start_date + period <= payment_date_list[0]:
            payment_date_list.append(end_date - period * cnt)
            cnt += 1
        payment_date_list.reverse()
        for d in payment_date_list:
            if hasattr('adjust', d):
                d.adjust(convention, holidays)
        return payment_date_list


def bond(start_date=TODAY,
         end_date=TODAY + MATURITY,
         period=BOND_TENOR,
         convention='mod_follow',
         holidays=None,
         notional_amount=1.0,
         day_count='thirty360',
         fixed_rate=0.0,
         forward_curve=None,
         fixing_offset=None,
         pay_offset=None):
    """ simple bond product

    :param start_date: pay date of inital notional amount
    :param end_date: rolling date for interest pay dates
        and pay date of notional redemption
    :param period: rolling period of interest payments
    :param convention: business date adjustement convention
        to adjust fixingdates
    :param holidays: list of business holidays
    :param notional_amount: bond notional amount
    :param day_count: day count convention
    :param fixed_rate: fixed interest rate
    :param forward_curve: forward curve for estimation of float rates
    :param fixing_offset: time difference between
        interest rate fixing date and interest period payment date
    :param pay_offset: time difference between
        interest period end date and interest payment date
    :return: |CashFlowLegList|

    """
    interest_payment_date_list = _interest_payment_dates(
        start_date, end_date, period, convention, holidays)

    if isinstance(notional_amount, (int, float)):
        # case bullet loan
        notional_payment_date_list = start_date, end_date
        notional_amount_list = -notional_amount, notional_amount
        interest_notional_amount_list = \
            [notional_amount] * len(interest_payment_date_list)
    elif isinstance(notional_amount, (tuple, list)):
        # case explicit notional plan
        notional_payment_date_list = start_date, *interest_payment_date_list
        if not len(notional_amount) == len(interest_payment_date_list):
            raise ValueError("require full notional amount plan")
        outstanding = sum(notional_amount)
        notional_amount_list = -outstanding, *notional_amount
        interest_notional_amount_list = list()
        for payback in notional_amount:
            interest_notional_amount_list.append(outstanding)
            outstanding -= payback
    else:
        raise ValueError(
            "notional_amount argument must be either number or list")

    notional_leg = FixedCashFlowList(
        payment_date_list=notional_payment_date_list,
        amount_list=notional_amount_list,
        origin=start_date
    )

    coupon_leg = RateCashFlowList(
        payment_date_list=interest_payment_date_list,
        amount_list=interest_notional_amount_list,
        fixed_rate=fixed_rate,
        forward_curve=forward_curve,
        day_count=day_count,
        origin=start_date,
        fixing_offset=fixing_offset,
        pay_offset=pay_offset
    )

    legs = notional_leg, coupon_leg
    return CashFlowLegList(legs)


def interest_rate_swap(start_date=TODAY,
                       end_date=TODAY + MATURITY,
                       period=BOND_TENOR,
                       convention='mod_follow',
                       holidays='target',
                       notional_amount=1.0,
                       day_count='thirty360',
                       fixed_rate=0.0,
                       forward_curve=None,
                       fixing_offset=None,
                       pay_offset=None,
                       rec_leg_period=SWAP_TENOR,
                       rec_leg_day_count='actact',
                       rec_leg_fixed_rate=0.0,
                       rec_leg_forward_curve=None):
    """ plain vanilla swap

    :param start_date: pay date of inital notional amount
    :param end_date: rolling date for interest pay dates
        and pay date of notional redemption
    :param period: rolling period of pay leg interest payments
    :param convention: business date adjustement convention
        to adjust fixingdates
    :param holidays: list of business holidays
    :param notional_amount: bond notional amount
    :param day_count: day count convention of pay leg
    :param fixed_rate: fixed interest rate of pay leg
    :param forward_curve: forward curve for estimation of pay leg float rates
    :param fixing_offset: time difference between
        interest rate fixing date and interest period payment date
    :param pay_offset: time difference between
        interest period end date and interest payment date
    :param rec_leg_period: rolling period of receive leg interest payments
    :param rec_leg_day_count: day count convention of receive leg
    :param rec_leg_fixed_rate: fixed interest rate of receive leg
    :param rec_leg_forward_curve: forward curve for estimation
        of receive leg float rates

    :return: |CashFlowLegList|

    remark
    ======

    if not mentioned explicitly all arguments are applied to both legs,
    pay and receive leg.

    """

    pay_leg_payment_date_list = _interest_payment_dates(
        start_date, end_date,
        period, convention, holidays)

    pay_leg = RateCashFlowList(
        payment_date_list=pay_leg_payment_date_list,
        amount_list=[-notional_amount] * len(pay_leg_payment_date_list),
        fixed_rate=fixed_rate,
        forward_curve=forward_curve,
        day_count=day_count,
        origin=start_date,
        fixing_offset=fixing_offset,
        pay_offset=pay_offset
    )

    rec_leg_payment_date_list = _interest_payment_dates(
        start_date, end_date,
        rec_leg_period, convention, holidays)
    rec_leg = RateCashFlowList(
        payment_date_list=rec_leg_payment_date_list,
        amount_list=[notional_amount] * len(rec_leg_payment_date_list),
        fixed_rate=rec_leg_fixed_rate,
        forward_curve=rec_leg_forward_curve,
        day_count=rec_leg_day_count,
        origin=start_date,
        fixing_offset=fixing_offset,
        pay_offset=pay_offset
    )

    legs = pay_leg, rec_leg
    return CashFlowLegList(legs)


def asset_swap(coupon_leg, forward_curve, spread=0.0,
               convention='mod_follow', holidays='target'):
    pay_leg = -1 * coupon_leg
    payment_date_list = _interest_payment_dates(
        coupon_leg.origin, coupon_leg.domain[-1],
        forward_curve.forward_tenor, convention, holidays)
    coupon_leg_date_list = [max(d for d in coupon_leg.domain if d <= p)
                            for p in payment_date_list]

    rec_leg = RateCashFlowList(
        payment_date_list=payment_date_list,
        amount_list=coupon_leg[coupon_leg_date_list],
        fixed_rate=spread,
        forward_curve=forward_curve,
        day_count=forward_curve.day_count,
        origin=coupon_leg.origin,
        fixing_offset=coupon_leg.fixing_offset,
        pay_offset=coupon_leg.pay_offset
    )
    legs = pay_leg, rec_leg
    return CashFlowLegList(legs)
