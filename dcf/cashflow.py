# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.5, copyright Sunday, 21 November 2021
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .curve import DateCurve
from .plans import DEFAULT_AMOUNT, same


class CashFlowList(object):

    @property
    def domain(self):
        return self._domain

    @property
    def origin(self):
        return self._origin

    def __init__(self, domain=(), data=(), origin=None):
        if isinstance(data, (int, float)):
            data = same(len(domain), data)

        if not len(data) == len(domain):
            cls = self.__class__.__name__
            msg = "%s arguments `data` and `domain` must have same length." % \
                  cls
            raise ValueError(msg)

        self._origin = domain[0] if origin is None and domain else origin
        self._domain = domain
        self._flows = dict(zip(domain, data))

    def __getitem__(self, item):
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            return self._flows.get(item, 0.)

    def __str__(self):
        inner = ''
        if self.domain:
            s, e = self.domain[0], self.domain[-1]
            t = s, e, self._flows[s], self._flows[e]
            inner = '[%s ... %s], [%s ... %s]' % tuple(map(repr, t)) + self._args(', ')
        s = self.__class__.__name__ + '(' + inner + ')'
        return s

    def __repr__(self):
        start = self.__class__.__name__ + '('
        fill = ' ' * len(start)
        s = start + str(self.domain) + ',\n' + fill + str(self[self.domain]) + self._args(',\n' + fill) + ')'
        return s

    def _args(self, sep=''):
        s = ''
        for name in 'origin', 'day_count':
            if hasattr(self, name):
                attr = getattr(self, name)
                attr = attr.__name__ if hasattr(attr, '__name__') else repr(attr)
                s += sep + name + '=' + attr
        return s


class FixedCashFlowList(CashFlowList):

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 origin=None):
        super().__init__(payment_date_list, amount_list, origin=origin)


class RateCashFlowList(CashFlowList):
    """ list of cashflows by interest rate payments """

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 origin=None, day_count=None,
                 fixed_rate=0., forward_curve=None):
        """

        :param payment_date_list: pay dates, assuming that pay dates agree
            with end dates of interest accrued period
        :param amount_list: notional amounts
        :param origin: start date of first interest accrued period
        :param day_count: day count convention
        :param fixed_rate: agreed fixed rate
        :param forward_curve:
        """

        if day_count is None:
            day_count = DateCurve().day_count
        self.day_count = day_count

        self.fixed_rate = fixed_rate
        self.forward_curve = forward_curve

        super().__init__(payment_date_list, amount_list, origin=origin)

    def __getitem__(self, item):
        """ getitem does re-calc float cashflows """
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            amount = self._flows.get(item, 0.)
            previous = list(d for d in self.domain if d < item)
            start = previous[-1] if previous else self.origin

            rate = self.fixed_rate
            if self.forward_curve is not None:
                rate += self.forward_curve.get_cash_rate(start)
            return rate * amount * self.day_count(start, item)


class CashFlowLegList(CashFlowList):
    """
    MultiCashFlowList
    """

    @property
    def legs(self):
        return list(self._legs)

    def __init__(self, legs, start_date=None):
        for leg in legs:
            if not isinstance(leg, (CashFlowList, RateCashFlowList)):
                cls = self.__class__.__name__, leg.__class__.__name__
                raise ValueError("Legs %s of con be either `CashFlowList` or `RateCashFlowList` but not %s." % cls)
        self._legs = legs
        domains = tuple(tuple(leg.domain) for leg in self._legs)
        domain = list(sorted(set().union(*domains)))
        origin = min(leg.origin for leg in self._legs)
        super().__init__(domain, [0] * len(domain), origin=origin)

    def __getitem__(self, item):
        """ getitem does re-calc float cash flows and does not use store notional values """
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            return sum(leg[item] for leg in self._legs if item in leg.domain)
