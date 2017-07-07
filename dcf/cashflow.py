# -*- coding: utf-8 -*-

#  dcf (discounted cashflow)
#  -------------------------
#  A Python library for generating discounted cashflows.
#  Typical banking business methods are provided like interpolation, compounding,
#  discounting and fx.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Copyright: 2016, 2017 Deutsche Postbank AG
#  Website: https://github.com/pbrisk/dcf
#  License: APACHE Version 2 License (see LICENSE file)

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from curve import ZeroRateCurve


def _frange(start, stop=None, step=None):
    """
    _frange range like function for float inputs
    :param start:
    :type start:
    :param stop:
    :type stop:
    :param step:
    :type step:
    :return:
    :rtype:
    """
    if stop is None:
        stop = start
        start = 0.0
    if step is None:
        step = 1.0
    r = start
    while r < stop:
        yield r
        r += step


class CashFlowList(OrderedDict):
    """
    CashFlowList
    """

    def __init__(self, pay_date_list, amount_list=None):
        if amount_list is None:
            amount_list = [1e6] * len(pay_date_list)
        assert len(amount_list) == len(pay_date_list)
        super(CashFlowList, self).__init__(zip(pay_date_list, amount_list))

    def __getitem__(self, item):
        if isinstance(item, (tuple, list)):
            return [self[i] for i in item]
        else:
            return super(CashFlowList, self).__getitem__(item)

    def get_value(self, discount_curve, valuation_date=None):
        if valuation_date is None:
            valuation_date = discount_curve.domain[0]
        pd = [d for d in self if valuation_date < d]
        return discount_curve.get_swap_leg_valuation(pd, self[pd])

    def yield_to_maturity(self, valuation_date):
        # todo bracketing on yield
        last = None
        ytm = None
        for ytm in _frange(-0.1, 0.1, 0.001):
            value = self.get_value(ZeroRateCurve([ytm], [valuation_date]))
            if last is None or abs(last) >= abs(value):
                last = value
        return ytm


class AmortizingCashFlowList(CashFlowList):
    """
    AmortizingCashFlowList
    """
    # todo AmortizingCashFlowList
    pass


class AnnuityCashFlowList(CashFlowList):
    """
    AnnuityCashFlowList
    """
    # todo  AnnuityCashFlowList
    pass


class RateCashFlowList(CashFlowList):
    """
    RateCashFlowList
    """

    def __init__(self, date_list, day_count, fixed_rate=0.0, forward_curve=None, notional_list=None):
        if notional_list is None:
            notional_list = [1e6] * len(date_list[1:])

        self.fixed_rate = fixed_rate
        self.forward_curve = forward_curve
        self.day_count = day_count

        amount_list = list()
        for s, e, n in zip(date_list[:-1], date_list[1:], notional_list):
            amount_list.append(n * day_count(s, e))

        super(RateCashFlowList, self).__init__(date_list[1:], notional_list)

    def __getitem__(self, item):
        """
            getitem does re-calc float cash flows and does not use store notional values
        """
        amount = super(RateCashFlowList, self).__getitem__(item)
        if self.forward_curve is None:
            return self.fixed_rate * amount
        else:
            return (self.fixed_rate + self.forward_curve(item)) * amount

    def interest_accrued(self, valuation_date):
        # todo RateCashFlowList.interest_accrued()
        # get next cf
        # get yf until pay_date
        # calc interest_accrued
        next_pay_date = [d for d in self if valuation_date <= d][0]
        return self[next_pay_date] / (1 - self.day_count(valuation_date, next_pay_date))


class MultiCashFlowList(CashFlowList):
    """
    MultiCashFlowList
    """

    def __init__(self, legs):
        for l in legs:
            assert isinstance(l, CashFlowList)
        date_list = list(set().union([l.keys() in legs]))
        super(MultiCashFlowList, self).__init__(zip(date_list, [None] * len(date_list)))
        self.legs = legs

    def __getitem__(self, item):
        """
            getitem does re-calc float cash flows and does not use store notional values
        """
        super(MultiCashFlowList, self).__getitem__(item)
        return sum([l[item] for l in self.legs if item in l])

    def __str__(self):
        return ', '.join([str(l) for l in self.legs])

    def interest_accrued(self, valuation_date):
        """
        interest_accrued
        :param valuation_date:
        :type valuation_date:
        :return:
        :rtype:
        """
        return sum([l.interest_accrued(valuation_date) for l in self.legs if hasattr(l, 'interest_accrued')])


class FixedLoan(MultiCashFlowList):
    """
    FixedLoan
    """
    pass


class FloatLoan(MultiCashFlowList):
    """
    FloatLoan
    """
    pass


class FixedFloatSwap(MultiCashFlowList):
    """
    ir swap that pays fixed and receives float.
    """

    def __init__(self, date_list, fixed_rate, forward_curve, notional_list=None, day_count=None):

        # if args are tuples turn them into lists else build dupe lists
        if isinstance(fixed_rate, tuple):
            fixed_rate = list(fixed_rate)
        else:
            fixed_rate = [fixed_rate, 0.0]

        if isinstance(forward_curve, tuple):
            forward_curve = list(forward_curve)
        else:
            forward_curve = [None, forward_curve]

        if isinstance(notional_list, tuple):
            notional_list = list(notional_list)
        else:
            if notional_list is None:
                notional_list = [1e6] * len(date_list[1:])
            notional_list = [notional_list, notional_list]

        if isinstance(day_count, tuple):
            day_count = list(day_count)
        else:
            day_count = [day_count, day_count]
            for i in (0, 1):
                if forward_curve[i] is not None:
                    day_count[i] = forward_curve[i].day_count

        if isinstance(date_list, tuple):
            date_list = list(date_list)
        else:
            date_list = [date_list, date_list]
            # gather details from forward_curve tenor
            for i in (0, 1):
                if forward_curve[i] is not None:
                    leg_date_list, leg_notional_list = self.gather_float_dates(date_list[i], notional_list[i],
                                                                               forward_curve[i].forward_tenor)
                    # if lists do not meet required length, we'll have to replace them
                    if not len(leg_date_list) == len(date_list[i]):
                        date_list[i] = leg_date_list
                    if not len(leg_notional_list) == len(notional_list[i]):
                        notional_list[i] = leg_notional_list

        # build legs
        notional_list[0] *= -1  # swap pay sign
        self.pay = RateCashFlowList(date_list[0], day_count[0], fixed_rate[0], forward_curve[0], notional_list[0])
        self.rec = RateCashFlowList(date_list[1], day_count[1], fixed_rate[1], forward_curve[1], notional_list[1])
        super(FixedFloatSwap, self).__init__([self.pay, self.rec])

    @staticmethod
    def gather_float_dates(date_list, notional_list, forward_tenor):
        flt_date_list = list()
        flt_notional_list = list()
        cd = date_list[0]
        for ed, nl in zip(date_list[1:], notional_list):
            while cd < ed:
                flt_date_list.append(cd)
                flt_notional_list.append(nl)
                cd += forward_tenor
        return flt_date_list, flt_notional_list

    def get_par_rate(self, discount_curve, leg_int=0, err=1e-8):
        x = self.legs[leg_int].fixed_rate
        pv = self.get_value(discount_curve)
        while abs(pv) > err:
            # todo implement bracketing
            break
        return x
