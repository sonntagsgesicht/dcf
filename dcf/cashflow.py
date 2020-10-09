# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)
from abc import ABC

from .curve import DateCurve
from .interpolation import zero
from .interpolationscheme import dyn_scheme
from .plans import DEFAULT_AMOUNT, flat


class CashFlowList(object):

    @property
    def domain(self):
        raise NotImplementedError

    @property
    def origin(self):
        raise NotImplementedError

    def __getitem__(self, item):
        raise NotImplementedError


class FixedCashFlowList(DateCurve, CashFlowList):
    """
    CashFlowList
    """
    _interpolation = dyn_scheme(zero, zero, zero)

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT):
        if isinstance(amount_list, (int, float)):
            amount_list = flat(len(payment_date_list), amount_list)
        if not len(amount_list) == len(payment_date_list):
            cls = self.__class__.__name__
            raise ValueError("%s arguments `payment_date_list` and `amount_list` must have same length." % cls)
        # keep flows in dict for safety reasons due to numerical errors
        self._flows = dict(zip(payment_date_list, amount_list))
        super(FixedCashFlowList, self).__init__(payment_date_list, amount_list)

    def __getitem__(self, item):
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            return self._flows.get(item, 0.)


class RateCashFlowList(DateCurve, CashFlowList):
    """ list of cashflows by interest rate payments """
    _interpolation = dyn_scheme(zero, zero, zero)

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 day_count=None, start_date=None, fixed_rate=0., forward_curve=None):
        """

        :param payment_date_list: pay dates, assuming that pay dates agree with end dates of interest accrued period
        :param amount_list: notional amounts
        :param start_date: start date of first interest accrued period
        :param day_count: day count convention
        :param fixed_rate: agreed fixed rate
        :param forward_curve:
        """

        if isinstance(amount_list, (int, float)):
            amount_list = flat(len(payment_date_list), amount_list)
        if not len(amount_list) == len(payment_date_list):
            cls = self.__class__.__name__
            raise ValueError("%s arguments `payment_date_list` and `amount_list` must have same length." % cls)

        # keep flows in dict for safety reasons due to numerical errors
        self._flows = dict(zip(payment_date_list, amount_list))
        self.fixed_rate = fixed_rate
        self.forward_curve = forward_curve

        super(RateCashFlowList, self).__init__(payment_date_list, amount_list, day_count=day_count, origin=start_date)

    def __getitem__(self, item):
        """ getitem does re-calc float cash flows and does not use store notional values """
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            amount = self._flows.get(item, 0.)
            previous = list(d for d in self.domain if d < item)
            if previous:
                start = previous[-1]
            else:
                start = self.origin

            if self.forward_curve is None:
                return self.fixed_rate * amount * self.day_count(start, item)
            else:
                return (self.fixed_rate + self.forward_curve.get_cash_rate(item)) * amount * self.day_count(start, item)


class CashFlowLegList(CashFlowList):
    """
    MultiCashFlowList
    """

    @property
    def domain(self):
        if self._domain:
            return self._domain
        else:
            domains = tuple(tuple(leg.domain) for leg in self._legs)
            self._domain = list(sorted(set().union(*domains)))
            return self._domain

    @property
    def legs(self):
        return list(self._legs)

    @property
    def origin(self):
        return min(leg.origin for leg in self._legs)

    def __init__(self, legs, start_date=None):
        for leg in legs:
            if not isinstance(leg, (CashFlowList, RateCashFlowList)):
                cls = self.__class__.__name__, leg.__class__.__name__
                raise ValueError("Legs %s of con be either `CashFlowList` or `RateCashFlowList` but not %s." % cls)
        self._domain = None
        self._legs = legs

    def __getitem__(self, item):
        """ getitem does re-calc float cash flows and does not use store notional values """
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            return sum(leg[item] for leg in self._legs if item in leg.domain)
