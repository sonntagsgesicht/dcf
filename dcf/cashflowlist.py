# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from .payoffs import (FixedCashFlowPayOff, RateCashFlowPayOff,
                      OptionCashFlowPayOff, OptionStrategyCashFlowPayOff,
                      ContingentRateCashFlowPayOff)
from .payoffmodels import PayOffModel
from .plans import DEFAULT_AMOUNT

from .tools.ts import TSList


class CashFlowList(TSList):

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
                fixed_rate=fixed_rate
            )
            payoff_list.append(payoff)

        self = cls(payoff_list)
        if forward_curve is not None:
            self._payoff_model = PayOffModel(forward_curve=forward_curve)
        return self

    @classmethod
    def from_option_cashflows(
            cls,
            payment_date_list,
            amount_list=DEFAULT_AMOUNT,
            strike_list=(),
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
        if isinstance(strike_list, (int, float)):
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
                is_put=is_put
            )
            payoff_list.append(option)
        self = cls(payoff_list)
        self._payoff_model = payoff_model
        return self

    @classmethod
    def from_option_strategy_cashflows(
            cls,
            payment_date_list,
            call_amount_list=DEFAULT_AMOUNT,
            call_strike_list=(),
            put_amount_list=DEFAULT_AMOUNT,
            put_strike_list=(),
            fixing_offset=None,
            pay_offset=None,
            payoff_model=None):
        r"""series of identical option strategies

        :param payment_date_list: list of cashflow payment dates $t_k$
        :param call_amount_list: list of call option notional amounts $N_{i}$
        :param call_strike_list: list of call option strikes $K_{i}$
        :param put_amount_list: list of put option notional amounts $N_{j}$
        :param put_strike_list: list of put option strikes $L_{j}$
        :param fixing_offset: offset $\delta$ between
            underlying fixing date and cashflow end date
        :param pay_offset: offset $\epsilon$ between
            cashflow end date and payment date
        :param payoff_model: payoff model to derive the expected payoff

        This class method provides a list of
        |OptionStrategyCashFlowPayOff()| $X_k$ objects
        with payment date $t_k$.

        Adjusted by offset $X_k$ has expiry date $T_k=t_k-\delta-\epsilon$
        and for all $k$ the same $N_i$, $K_i$, $N_j$, $L_j$ are used.

        """

        if 10 < len(put_strike_list) + len(call_strike_list):
            raise KeyError('OptionStrategyCashflowList are limited '
                           'to 10 options per strategy payoff not '
                           f"{len(put_strike_list) + len(call_strike_list)}")
        payoff_list = list()
        for pay_date in payment_date_list:
            expiry = pay_date
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            strategy = OptionStrategyCashFlowPayOff(
                pay_date=pay_date,
                expiry=expiry,
                call_amount_list=call_amount_list,
                call_strike_list=call_strike_list,
                put_amount_list=put_amount_list,
                put_strike_list=put_strike_list
            )
            payoff_list.append(strategy)
        self = cls(payoff_list)
        self._payoff_model = payoff_model
        return self

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
        :param fixed_rate: agreed fixed rate
        :param forward_curve:
        :param fixing_offset: time difference between
            interest rate fixing date and interest period payment date
        :param pay_offset: time difference between
            interest period end date and interest payment date
        :param floor_strike: lower interest rate boundary $K$
        :param cap_strike: upper interest rate boundary $L$
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
                cap_strike=cap_strike, floor_strike=floor_strike
            )
            payoff_list.append(payoff)
        self = cls(payoff_list)
        self._payoff_model = payoff_model
        return self

    @property
    def table(self):
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
        return rows

    def print(self, *seq, sep='\n', end='\n', file=None):
        from tabulate import tabulate
        s = tabulate(self.table, headers="firstrow", floatfmt="_", intfmt="_")
        print(*seq, s, sep=sep, end=end, file=file)

    def html(self):
        from tabulate import tabulate
        return tabulate(self.table, tablefmt="html", headers="firstrow")

    def _repr_html_(self):
        return self.html()

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
    def payoff_model(self):
        """model to derive the expected cashflow"""
        return getattr(self, '_payoff_model', None)

    @payoff_model.setter
    def payoff_model(self, value):
        setattr(self, '_payoff_model', value)

    def details(self, model=None):
        return self(model)

    def __call__(self, model=None):
        model = model or self.payoff_model
        return TSList(super().__call__(model))
