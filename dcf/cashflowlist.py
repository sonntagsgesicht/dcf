# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from warnings import warn
from pprint import pformat

try:
    from tslist import TSList
except ImportError:
    class TSList(list):
        def __init__(self, seq=()):
            msg = ("tslist not found. consider 'pip install tslist' "
                   "for more flexible datetime list operations")
            warn(msg)
            super().__init__(seq)

try:
    from tabulate import tabulate
except ImportError:
    def tabulate(x, *_, **__):
        msg = ("tabulate not found. consider 'pip install tabulate' "
               "for more flexible table representation")
        warn(msg)
        return pformat(x, indent=2, sort_dicts=False)


from .payoffs import (FixedCashFlowPayOff, RateCashFlowPayOff,
                      OptionCashFlowPayOff, ContingentRateCashFlowPayOff)
from .plans import DEFAULT_AMOUNT


class CashFlowList(TSList):
    """cashflow payoff container"""

    @classmethod
    def from_fixed_cashflows(
            cls,
            payment_date_list,
            amount_list=DEFAULT_AMOUNT):
        """ basic cashflow list object

        :param payment_date_list: list of cashflow payment dates
        :param amount_list: list of cashflow amounts
        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)
        ta_list = zip(payment_date_list, amount_list)
        return cls(FixedCashFlowPayOff(t, a) for t, a in ta_list)

    @classmethod
    def from_rate_cashflows(
            cls,
            payment_date_list,
            amount_list=DEFAULT_AMOUNT,
            origin=None,
            day_count=None,
            fixing_offset=None,
            pay_offset=None,
            fixed_rate=0.,
            forward_curve=None):
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
        else:
            start_dates = []

        payoff_list = list()
        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            pay_date = e
            if pay_offset:
                e -= pay_offset
                s -= pay_offset
            payoff = RateCashFlowPayOff(
                pay_date=pay_date,
                start=s, end=e, day_count=day_count,
                fixing_offset=fixing_offset, amount=a,
                fixed_rate=fixed_rate,
                forward_curve=forward_curve
            )
            payoff_list.append(payoff)
        return cls(payoff_list)

    @classmethod
    def from_option_cashflows(
            cls,
            payment_date_list,
            amount_list=DEFAULT_AMOUNT,
            strike_list=None,
            is_put_list=False,
            fixing_offset=None,
            pay_offset=None,
            payoff_model=None):
        r""" list of European option payoffs

        :param payment_date_list: list of cashflow payment dates $t_k$
        :param amount_list: list of option notional amounts $N_k$
        :param strike_list: list of option strike prices $K_k$
        :param is_put_list: list of boolean flags indicating
            if options are put options (optional: default is **False**)
        :param fixing_offset: offset $\delta$ between
            underlying fixing date and cashflow end date
        :param pay_offset: offset $\epsilon$ between
            cashflow end date and payment date
        :param payoff_model: payoff model to derive the expected payoff

        List of |OptionCashFlowPayOff()|.

        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)
        if isinstance(strike_list, (int, float)) or strike_list is None:
            strike_list = [strike_list] * len(payment_date_list)
        if isinstance(is_put_list, (bool, int, float)):
            is_put_list = [is_put_list] * len(payment_date_list)

        payoff_list = list()
        for pay_date, amount, strike, is_put in \
                zip(payment_date_list, amount_list, strike_list, is_put_list):
            expiry = pay_date
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            option = OptionCashFlowPayOff(
                pay_date=pay_date,
                expiry=expiry,
                amount=amount,
                strike=strike,
                is_put=is_put,
                payoff_model=payoff_model
            )
            payoff_list.append(option)
        return cls(payoff_list)

    @classmethod
    def from_contingent_rate_cashflows(
            cls,
            payment_date_list,
            amount_list=DEFAULT_AMOUNT,
            origin=None,
            day_count=None,
            fixing_offset=None,
            pay_offset=None,
            fixed_rate=0.,
            cap_strike=None,
            floor_strike=None,
            payoff_model=None):
        r""" list of contingent collared rate cashflows

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
        :param cap_strike: upper interest rate boundary $L$
        :param floor_strike: lower interest rate boundary $K$
        :param payoff_model: option valuation model to derive the
            expected cashflow of option payoffs

        Each object consists of a list of
        |ContingentRateCashFlowPayOff()|, i.e.
        of collared payoff functions

        $$X_i(f(T_i)) = [\max(K, \min(f(T_i), L)) + c]\ \tau(s,e)\ N$$

        with, according to a payment date $p_i$,
        $p_i-\epsilon=e_i$, $e_i=s_{i+1}$ and $s_i-\delta=T_i$.

        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)

        if origin:
            start_dates = [origin]
            start_dates.extend(payment_date_list[:-1])
        elif origin is None and len(payment_date_list) > 1:
            step = payment_date_list[1] - payment_date_list[0]
            start_dates = [payment_date_list[0] - step]
            start_dates.extend(payment_date_list[:-1])
        else:
            start_dates = []

        payoff_list = list()
        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            pay_date = e
            if pay_offset:
                e -= pay_offset
                s -= pay_offset

            payoff = ContingentRateCashFlowPayOff(
                pay_date=pay_date,
                start=s, end=e, day_count=day_count,
                fixing_offset=fixing_offset, amount=a, fixed_rate=fixed_rate,
                cap_strike=cap_strike, floor_strike=floor_strike,
                payoff_model=payoff_model
            )
            payoff_list.append(payoff)
        return cls(payoff_list)

    def __init__(self, iterable=(), /):
        """cashflow payoff container

        :param iterable:
        """
        super().__init__(iterable)

    @property
    def domain(self):
        """ payment date list """
        return tuple(getattr(v, 'pay_date', None) for v in self)

    @property
    def origin(self):
        """ cashflow list start date """
        origin = min(self.domain, default=None)
        origin = \
            min((getattr(v, 'origin', None) for v in self), default=origin)
        return origin

    @property
    def fixed_rate(self):
        fixed_rates = (getattr(cf, 'fixed_rate', None) for cf in self)
        fixed_rates = set(fr for fr in fixed_rates if fr is not None)
        if len(fixed_rates) == 1:
            return max(fixed_rates)
        raise ValueError(f"list contains various fixed rates:"
                         f" {', '.join(map(str, fixed_rates))}")

    @fixed_rate.setter
    def fixed_rate(self, value):
        if not self.fixed_rate == value:
            for cf in self:
                if getattr(cf, 'fixed_rate', None) is not None:
                    cf.fixed_rate = value

    def details(self, model=None):
        return [v.details(model) for v in self]

    def _tabulate(self, **kwargs):
        details = self.details()
        header = {}
        for d in details:
            header.update(d)
        header = list(header.keys())
        rows = [header]
        for d in details:
            r = dict.fromkeys(header)
            r.update(d)
            rows.append(list(r.values()))
        return tabulate(rows, **kwargs)

    def _repr_html_(self):
        return self._tabulate(tablefmt="html", headers="firstrow")

    def __str__(self):
        return self._tabulate(headers="firstrow", floatfmt="_", intfmt="_")

    def __abs__(self):
        return self.__class__(v.__abs__() for v in self)

    def __neg__(self):
        return self.__class__(v.__neg__() for v in self)

    def __call__(self, model=None):
        return [v(model) for v in self]

    def __add__(self, other):
        if isinstance(other, list):
            return self.__class__(super().__add__(other))
        return self.__class__(v.__add__(other) for v in self)

    def __sub__(self, other):
        if isinstance(other, list):
            # lousy hack since other might just be list and not List
            return self.__neg__().__add__(other).__neg__()
        return self.__class__(v.__sub__(other) for v in self)

    def __mul__(self, other):
        return self.__class__(v.__mul__(other) for v in self)

    def __truediv__(self, other):
        return self.__class__(v.__truediv__(other) for v in self)

    def __matmul__(self, other):
        return self.__class__(v.__matmul__(other) for v in self)
