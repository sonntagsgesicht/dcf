# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from collections import OrderedDict
from inspect import signature
from warnings import warn

from ..daycount import day_count as _default_day_count
from dcf.plans import DEFAULT_AMOUNT, same as _same


class CashFlowList(object):

    @property
    def domain(self):
        """ payment date list """
        return self._domain

    @property
    def origin(self):
        """ cashflow list start date """
        if self._origin is None and self._domain:
            return self._domain[0]
        return self._origin

    @property
    def kwargs(self):
        warn('%s().kwargs is under construction' % self.__class__.__name__)
        kw = OrderedDict()
        for name in signature(self.__class__).parameters:
            attr = None
            if name == 'amount_list':
                attr = tuple(self._flows[d] for d in self.domain)
            if name == 'payment_date_list':
                attr = self.domain
            attr = getattr(self, '_' + name, attr)
            if isinstance(attr, (list, tuple)):
                attr = tuple(getattr(a, 'kwargs', a) for a in attr)
                attr = tuple(getattr(a, '__name__', a) for a in attr)
            attr = getattr(attr, 'kwargs', attr)
            attr = getattr(attr, '__name__', attr)
            if attr is not None:
                kw[name] = attr
        return kw

    def __init__(self, payment_date_list=(), amount_list=(), origin=None):
        """ basic cashflow list object

        :param domain: list of cashflow dates
        :param data: list of cashflow amounts
        :param origin: origin of object,
            i.e. start date of the cashflow list as a product

        Basicly |CashFlowList()| works like a read-only dictionary
        with payment dates as keys.

        And the |CashFlowList().domain| property holds the payment date list.

        >>> from dcf import CashFlowList
        >>> cf_list = CashFlowList([0, 1], [-100., 100.])
        >>> cf_list.domain
        (0, 1)

        In order to get cashflows

        >>> cf_list[0]
        -100.0
        >>> cf_list[cf_list.domain]
        (-100.0, 100.0)

        This works even for dates without cashflow

        >>> cf_list[-1, 0 , 1, 2]
        (0.0, -100.0, 100.0, 0.0)

        """
        if isinstance(amount_list, (int, float)):
            amount_list = _same(len(payment_date_list), amount_list)

        if not len(amount_list) == len(payment_date_list):
            msg = f"{self.__class__.__name__} arguments " \
                  f"`data` and `domain` must have same length."
            raise ValueError(msg)

        self._origin = origin
        self._domain = tuple(payment_date_list)
        self._flows = dict(zip(payment_date_list, amount_list))

    def __getitem__(self, item):
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            return self._flows.get(item, 0.)

    def __add__(self, other):
        for k in self._flows:
            self._flows[k].__add__(other)

    def __sub__(self, other):
        for k in self._flows:
            self._flows[k].__sub__(other)

    def __mul__(self, other):
        for k in self._flows:
            self._flows[k].__mul__(other)

    def __truediv__(self, other):
        for k in self._flows:
            self._flows[k].__truediv__(other)

    def __str__(self):
        inner = tuple()
        if self.domain:
            s, e = self.domain[0], self.domain[-1]
            inner = f'[{s!r} ... {e!r}]', \
                    f'[{self._flows[s]!r} ... {self._flows[e]!r}]'
        kw = self.kwargs
        kw.pop('amount_list', ())
        kw.pop('payment_date_list', ())
        inner += tuple(f"{k!s}={v!r}" for k, v in kw.items())
        s = self.__class__.__name__ + '(' + ', '.join(inner) + ')'
        return s

    def __repr__(self):
        s = self.__class__.__name__ + '()'
        if self.domain:
            fill = ',\n' + ' ' * (len(s) - 1)
            kw = self.kwargs
            inner = \
                str(kw.pop('payment_date_list', ())), \
                str(kw.pop('amount_list', ()))
            inner += tuple(f"{k!s}={v!r}" for k, v in kw.items())
            s = self.__class__.__name__ + '(' + fill.join(inner) + ')'
        return s


class FixedCashFlowList(CashFlowList):

    @property
    def table(self):
        """ cashflow details as list of tuples """
        header = [('cashflow', 'pay date')]
        table = list((self[d], d,) for d in self.domain)
        return header + table

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 origin=None):
        """ basic cashflow list object

        :param payment_date_list: list of cashflow payment dates
        :param amount_list: list of cashflow amounts
        :param origin: origin of object,
            i.e. start date of the cashflow list as a product
        """
        if isinstance(payment_date_list, CashFlowList):
            amount_list = payment_date_list[payment_date_list.domain]
            origin = origin or payment_date_list.kwargs.get('origin', None)
            payment_date_list = payment_date_list.domain
        super().__init__(payment_date_list, amount_list, origin=origin)


class RateCashFlowList(CashFlowList):
    """ list of cashflows by interest rate payments """

    DAY_COUNT = _default_day_count
    """ default day count function for rate period calculation

        **DAY_COUNT** is a static function
        and can be set on class level, e.g.

        :code:`RateCashFlowList.DAY_COUNT = (lambda s, e : e - s)`

        :param start: period start date
        :param end: period end date
        :returns: year fraction for **start** to **end** as a float

    """

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 origin=None, day_count=None,
                 fixing_offset=None, pay_offset=None,
                 fixed_rate=0., forward_curve=None):
        r""" list of interest rate cashflows

        :param payment_date_list: pay dates, assuming that pay dates agree
            with end dates of interest accrued period
        :param amount_list: notional amounts
        :param origin: start date of first interest accrued period
        :param day_count: day count convention
        :param fixed_rate: agreed fixed rate
        :param forward_curve: interest rate curve for forward estimation
        :param fixing_offset: time difference between
            interest rate fixing date and interest period payment date
        :param pay_offset: time difference between
            interest period end date and interest payment date

        Let $t_0$ be the list **origin**
        and $t_i$ $i=1, \dots n$ the **payment_date_list**
        with $N_i$ $i=1, \dots n$ the notional **amount_list**.

        Moreover, let $\tau$ be the **day_count** function,
        $c$ the **fixed_rate** and $f$ the **forward_curve**.

        Then, the rate cashflow $cf_i$ payed at time $t_i$ will be
        with
        $s_i = t_{i-1} - \delta$,
        $e_i = t_i -\delta$
        as well as
        $d_i = s_i - \epsilon$
        for **pay_offset** $\delta$ and **fixing_offset** $\epsilon$,

        $$cf_i = N_i \cdot \tau(s_i,e_i) \cdot (c + f(d_i)).$$

        Note, the **pay_offset** $\delta$ is not applied
        in case of the first cashflow, then $s_1=t_0$.

        """

        self.day_count = self.__class__.DAY_COUNT \
            if day_count is None else day_count
        r""" day count function for rate period calculation $\tau$"""

        self.fixed_rate = fixed_rate
        r""" cashflow fixed rate $c$ """
        self.forward_curve = forward_curve
        r""" cashflow forward curve to derive float rates $f$ """

        self.pay_offset = pay_offset
        r""" difference $\delta$
        between rate period end date and payment date """
        self.fixing_offset = fixing_offset
        r""" difference $\epsilon$
        between rate period start date and rate fixing date """

        super().__init__(payment_date_list, amount_list, origin=origin)

    @property
    def table(self):
        """ cashflow details as list of tuples """
        # print(tabulate(cf.table, headers='firstrow'))  # for pretty print

        header = 'cashflow', 'pay date', 'notional', \
                 'start date', 'end date', 'year fraction', 'fixed rate'
        if self.forward_curve:
            header += 'forward rate', 'fixing date', 'tenor'
        table = list()
        for d in self.domain:
            details = self._flow_details(d)
            table.append(tuple(details.get(h, '') for h in header))
        return [header] + table

    def _flow_details(self, item):
        if isinstance(item, (tuple, list)):
            return tuple(self._flow_details(i) for i in item)
        else:
            amount = self._flows.get(item, 0.)

            previous = list(d for d in self.domain if d < item)
            start = previous[-1] if previous else self.origin
            end = item
            if self.pay_offset:
                if previous:
                    start -= self.pay_offset
                end -= self.pay_offset
            tau = self.day_count(start, end)

            rate = self.fixed_rate
            details = {
                'notional': amount,
                'pay/rec': 'pay' if amount > 0 else 'rec',
                'fixed rate': rate,
                'start date': start,
                'end date': end,
                'year fraction': tau,
                'pay date': item,
            }
            fwd = 0.0
            if self.forward_curve is not None:
                fix = start
                if self.fixing_offset:
                    fix -= self.fixing_offset
                fwd = self.forward_curve.get_cash_rate(fix)
                details['tenor'] = self.forward_curve.forward_tenor
                details['fixing date'] = fix
                details['forward rate'] = fwd
                details['curve-id'] = id(self.forward_curve)

            details['cashflow'] = (rate + fwd) * amount * tau
            return details

    def __getitem__(self, item):
        """ getitem does re-calc float cashflows """
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            return self._flow_details(item)['cashflow']


class CashFlowLegList(CashFlowList):
    """ MultiCashFlowList """

    @property
    def legs(self):
        """ list of |CashFlowList| """
        return list(self._legs)

    def __init__(self, legs):
        """ container class for CashFlowList

        :param legs: list of |CashFlowList|

        """
        for leg in legs:
            if not isinstance(leg, (CashFlowList, RateCashFlowList)):
                cls = self.__class__.__name__, leg.__class__.__name__
                raise ValueError("Legs %s of can be either `CashFlowList` "
                                 "or `RateCashFlowList` but not %s." % cls)
        self._legs = legs
        domains = tuple(tuple(leg.domain) for leg in self._legs)
        domain = list(sorted(set().union(*domains)))
        origin = min(leg.origin for leg in self._legs)
        super().__init__(domain, [0] * len(domain), origin=origin)

    def __getitem__(self, item):
        """ getitem does re-calc float cash flows and
            does not use store notional values """
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            return sum(leg[item] for leg in self._legs if item in leg.domain)

    def __add__(self, other):
        for leg in self._legs:
            leg.__add__(other)

    def __sub__(self, other):
        for leg in self._legs:
            leg.__sub__(other)

    def __mul__(self, other):
        for leg in self._legs:
            leg.__mul__(other)

    def __truediv__(self, other):
        for leg in self._legs:
            leg.__truediv__(other)
