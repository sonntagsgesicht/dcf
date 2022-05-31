# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from collections import OrderedDict
from inspect import signature
from warnings import warn

from ..plans import DEFAULT_AMOUNT

from .payoffs import FixedCashFlowPayOff, RateCashFlowPayOff


class CashFlowList(object):
    _cashflow_details = 'cashflow', 'pay date'

    @property
    def table(self):
        """ cashflow details as list of tuples """
        # print(tabulate(cf.table, headers='firstrow'))  # for pretty print

        header, table = list(), list()
        for d in self.domain:
            payoff = self._flows.get(d, 0.)
            if hasattr(payoff, 'details'):
                fwd = getattr(self, 'forward_curve', None)
                details = payoff.details(fwd)
                details['pay date'] = d
            else:
                details = {'cashflow': float(payoff), 'pay date': d}
            for k in self.__class__._cashflow_details:
                if k in details and k not in header:
                    header.append(k)
            table.append(tuple(details.get(h, '') for h in header))
        return [tuple(header)] + table

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
        """returns constructor arguments as ordered dictionary
        (under construction)
        """
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

    def payoff(self, date):
        """dictionary of payoffs with pay_date keys"""
        if isinstance(date, (tuple, list)):
            return tuple(self.payoff(i) for i in date)
        return self._flows.get(date, None)

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
            amount_list = [amount_list] * len(payment_date_list)

        if not len(amount_list) == len(payment_date_list):
            msg = f"{self.__class__.__name__} arguments " \
                  f"`payment_date_list` and `amount_list` " \
                  f"must have same length."
            raise ValueError(msg)

        self._origin = origin
        self._domain = tuple(payment_date_list)
        self._flows = dict(zip(payment_date_list, amount_list))

    def __getitem__(self, item):
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            payoff = self._flows.get(item, 0.)
            if not isinstance(payoff, (int, float)):
                _ = None
                if hasattr(self, 'payoff_model'):
                    _ = self.payoff_model
                elif hasattr(self, 'forward_curve'):
                    _ = self.forward_curve
                payoff = payoff(_)
            return payoff

    def __call__(self, _=None):
        flows = list()
        for item in self.domain:
            payoff = self._flows.get(item, 0.)
            if not isinstance(payoff, (int, float)):
                if _ is None:
                    if hasattr(self, 'payoff_model'):
                        _ = self.payoff_model
                    elif hasattr(self, 'forward_curve'):
                        _ = self.forward_curve
                payoff = payoff(_)
            flows.append(payoff)
        return CashFlowList(self.domain, flows, self._origin)

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
            return sum(
                float(leg[item]) for leg in self._legs if item in leg.domain)

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


class FixedCashFlowList(CashFlowList):
    _header_keys = 'cashflow', 'pay date'

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
            origin = origin or getattr(payment_date_list, '_origin', None)
            payment_date_list = payment_date_list.domain

        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)

        payoff_list = tuple(FixedCashFlowPayOff(amount=a) for a in amount_list)
        super().__init__(payment_date_list, payoff_list, origin=origin)


class RateCashFlowList(CashFlowList):
    """ list of cashflows by interest rate payments """

    _cashflow_details = 'cashflow', 'pay date', 'notional', \
                        'start date', 'end date', 'year fraction', \
                        'fixed rate', 'forward rate', 'fixing date', 'tenor'

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
        :param fixing_offset: time difference between
            interest rate fixing date and interest period payment date
        :param pay_offset: time difference between
            interest period end date and interest payment date
        :param fixed_rate: agreed fixed rate
        :param forward_curve: interest rate curve for forward estimation

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

        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)

        if origin is not None:
            start_dates = [origin]
            start_dates.extend(payment_date_list[:-1])
        elif origin is None and len(payment_date_list) > 1:
            step = payment_date_list[1] - payment_date_list[0]
            start_dates = [payment_date_list[0] - step]
            start_dates.extend(payment_date_list[:-1])
        elif payment_date_list:
            start_dates = payment_date_list

        payoff_list = list()
        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            if pay_offset:
                e -= pay_offset
                s -= pay_offset

            payoff = RateCashFlowPayOff(
                start=s, end=e, day_count=day_count,
                fixing_offset=fixing_offset, amount=a,
                fixed_rate=fixed_rate
            )
            payoff_list.append(payoff)

        super().__init__(payment_date_list, payoff_list, origin=origin)
        self.forward_curve = forward_curve
        r""" cashflow forward curve to derive float rates $f$ """

    @property
    def fixed_rate(self):
        fixed_rates = tuple(cf.fixed_rate for cf in self._flows.values())
        if len(set(fixed_rates)) == 1:
            return fixed_rates[0]

    @fixed_rate.setter
    def fixed_rate(self, value):
        for cf in self._flows.values():
            cf.fixed_rate = value
