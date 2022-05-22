# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from ..daycount import day_count as default_day_count
from ..plans import DEFAULT_AMOUNT
from .cashflow import CashFlowList as _CashFlowList


_DEFAULT_PAYOFF = (lambda *_: 0.)


class ContingentCashFlowList(_CashFlowList):
    """ list of contingent cashflows """

    @property
    def table(self):
        """cashflow details as list of tuples"""
        # todo: contigent cashflow tbl
        raise NotImplementedError()

    def __init__(self, payment_date_list, payoff_list=None,
                 origin=None, payoff_model=None):
        r"""generic cashflow list of expected contingent cashflows
        i.e. non-deterministc cashflows like option payoffs.

        :param payment_date_list: pay dates, assuming that pay dates
            agree with end dates of interest accrued period
        :param payoff_list: list of payoffs
        :param origin: start date of first interest accrued period
        :param payoff_model: payoff model to derive the expected payoff

        Since expectation depends on probabilities
        an approbiate **payoff_model** $m$
        to estimate expectations has
        to be supplied as argument to the list
        and applied - again as argument - to payoffs.

        Therefor any item $f_i$ in **payoff_list** has to be
        either a **int** pr **float** or callable
        with optional argument of a **payoff_model**
        and will return the expected cashflow amount as float value
        depending on the state given by the **payoff_model**.

        $$f_i(m)=E\big[f_i\mid m\big]$$

        This non-sense use case demonstrates the pattern of evaluating payoffs.
        For more details who to use |ContingentCashFlowList|
        see |OptionCashflowList|, |OptionStrategyCashflowList|
        or |ContingentRateCashFlowList|.

        >>> from dcf import ContingentCashFlowList
        >>> p = lambda x: x*x
        >>> c = ContingentCashFlowList([1,2], [p, p], payoff_model=4)
        >>> c[c.domain]
        [16, 16]
        >>> c.payoff_model = 2
        >>> c[c.domain]
        [4, 4]
        """
        if payoff_list is None:
            payoff_list = [_DEFAULT_PAYOFF]
        self.payoff_model = payoff_model
        super().__init__(payment_date_list, payoff_list, origin=origin)

    def __getitem__(self, item):
        """ getitem does re-calc contingent cashflows """
        if isinstance(item, (tuple, list)):
            return list(self[i] for i in item)
        else:
            payoff = self._flows.get(item, 0.)
            if isinstance(payoff, (int, float)):
                return payoff
            return payoff(self.payoff_model)

    def __call__(self, payoff_model):
        flows = list()
        for item in self.domain:
            payoff = self._flows.get(item, 0.)
            if not isinstance(payoff, (int, float)):
                payoff = payoff(payoff_model)
            flows.append(payoff)
        return _CashFlowList(self.domain, flows, self._origin)

    @property
    def forward_curve(self):
        r"""underlying model forward curve to derive float rates $f$"""
        return self.payoff_model.forward_curve

    @forward_curve.setter
    def forward_curve(self, value):
        self.payoff_model.forward_curve = value


class OptionCashflowList(ContingentCashFlowList):
    """ list of option cashflows """

    class OptionCashFlowPayOff(object):

        def __init__(self, expiry, amount=DEFAULT_AMOUNT,
                     strike=None, is_put=False):
            r""" European option payoff function

            :param expiry: option exipry date $T$
            :param amount: option notional amount $N$
            :param strike: strike price $K$
            :param is_put: bool **True**
                for put options and **False** for call options
                (optional with default **False**)

            An European call option $C_K(S(T))$ is the right to buy
            an agreed amount $N$
            of an asset with future price $S(T)$
            at a future point in time $T$ (the option exipry date)
            for a pre-agreed strike price $K$.

            The call option payoff provides the expected profit
            from such transaction, i.e.

            $$C_K(S(T)) = N \cdot E[ \max(S(T)-K,0) ]$$

            Resp. a put option $P_K(S(T))$ is the right to sell
            an asset at a pre-agreed strike price.
            Hence, the put option payoff provides the expected profit
            from such transaction, i.e.

            $$P_K(S(T)) = N \cdot E[ \max(K-S(T),0) ]$$

            As the asset price $S(t)$ is unknown at time $t < T$,
            the estimation of $C_K(S(T))$ resp. $P_K(S(T))$
            requires assumptions on the as randomness understood
            unkown behavior of $S$ until $T$.

            This is provided by **payoff_model**
            implementing |OptionPayOffModel|
            and is invoked by calling an
            |OptionCashflowList.OptionCashFlowPayOff()| object.

            First, setup a classical log-normal *Black-Scholes* model.

            >>> from dcf.models import LogNormalOptionPayOffModel
            >>> from math import exp
            >>> f = lambda t: 100.0 * exp(t * 0.05)  # spot price 100 and yield of 5%
            >>> v = lambda v: 0.1  # flat volatility of 10%
            >>> m = LogNormalOptionPayOffModel(valuation_date=0.0, forward_curve=f, volatility_curve=v)

            Then, build a call option payoff.

            >>> from dcf import OptionCashflowList
            >>> c = OptionCashflowList.OptionCashFlowPayOff(expiry=0.25, strike=110.0)
            >>> # get expected option payoff
            >>> c(m)
            0.10726740675017865

            And a put option payoff.

            >>> p = OptionCashflowList.OptionCashFlowPayOff(expiry=0.25, strike=110.0, is_put=True)
            >>> # get expected option payoff
            >>> p(m)
            8.849422252686733

            """  # noqa E501
            self.expiry = expiry
            self.amount = amount
            self.strike = strike
            self.is_put = is_put

        def __call__(self, model):
            if self.is_put:
                return self.amount * \
                       model.get_put_value(self.expiry, self.strike)
            else:
                return self.amount * \
                       model.get_call_value(self.expiry, self.strike)

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 strike_list=(), is_put_list=False,
                 fixing_offset=None, pay_offset=None,
                 origin=None, payoff_model=None):
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
        :param origin: origin of object,
            i.e. start date of the cashflow list as a product
        :param payoff_model: payoff model to derive the expected payoff

        List of |OptionCashflowList.OptionCashFlowPayOff()|.

        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)
        if isinstance(strike_list, (int, float)):
            strike_list = [strike_list] * len(payment_date_list)
        if isinstance(is_put_list, (bool, int, float)):
            is_put_list = [is_put_list] * len(payment_date_list)

        payoff_list = list()
        cls = OptionCashflowList.OptionCashFlowPayOff
        for expiry, amount, strike, is_put in \
                zip(payment_date_list, amount_list, strike_list, is_put_list):
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            option = cls(expiry, amount, strike, is_put)
            payoff_list.append(option)
        super().__init__(payment_date_list, payoff_list, origin, payoff_model)


class OptionStrategyCashflowList(ContingentCashFlowList):
    """ list of option strategy cashflows """

    class OptionStrategyCashFlowPayOff(object):

        def __init__(self, expiry,
                     call_amount_list=DEFAULT_AMOUNT, call_strike_list=(),
                     put_amount_list=DEFAULT_AMOUNT, put_strike_list=()):
            r"""option strategy,
            i.e. series of call and put options with single expiry

            :param expiry: option exiptry date $T$
            :param call_amount_list: list of call option notional amounts $N_i$
            :param call_strike_list: list of call option strikes $K_i$
            :param put_amount_list: list of put option notional amounts $N_j$
            :param put_strike_list: list of put option strikes $L_j$

            The option strategy payoff $X$ is the sum of call and put payoffs

            $$X(S(T))
            =\sum_{i=1}^m N_i \cdot C_{K_i}(S(T))
            + \sum_{j=1}^n N_j \cdot P_{L_j}(S(T))$$

            see more on `options strategies <https://en.wikipedia.org/wiki/Options_strategy>`_

            First, setup a classical log-normal *Black-Scholes* model.

            >>> from dcf.models import LogNormalOptionPayOffModel
            >>> from math import exp
            >>> #
            >>> f = lambda t: 100.0 * exp(t * 0.05)  # spot price 100 and yield of 5%
            >>> v = lambda v: 0.1  # flat volatility of 10%
            >>> m = LogNormalOptionPayOffModel(valuation_date=0.0, forward_curve=f, volatility_curve=v)

            Then, setup a *butterlfy* payoff and evaluate it.

            >>> from dcf import OptionStrategyCashflowList
            >>> call_amounts = 1., -2., 1.
            >>> call_strikes = 100, 110, 120
            >>> s = OptionStrategyCashflowList.OptionStrategyCashFlowPayOff(expiry=1., call_amount_list=call_amounts, call_strike_list=call_strikes)
            >>> s(m)
            3.06924777745399

            """  # noqa E501
            if isinstance(call_amount_list, (int, float)):
                call_amount_list = [call_amount_list] * len(call_strike_list)
            if isinstance(put_amount_list, (int, float)):
                put_amount_list = [put_amount_list] * len(put_strike_list)

            self._options = list()
            cls = OptionCashflowList.OptionCashFlowPayOff
            for amount, strike in zip(call_amount_list, call_strike_list):
                option = cls(expiry, amount, strike, is_put=False)
                self._options.append(option)
            for amount, strike in zip(put_amount_list, put_strike_list):
                option = cls(expiry, amount, strike, is_put=True)
                self._options.append(option)

        def __call__(self, model):
            return sum(option(model) for option in self._options)

    def __init__(self, payment_date_list,
                 call_amount_list=DEFAULT_AMOUNT, call_strike_list=(),
                 put_amount_list=DEFAULT_AMOUNT, put_strike_list=(),
                 fixing_offset=None, pay_offset=None,
                 origin=None, payoff_model=None):
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
        :param origin: origin of object,
            i.e. start date of the cashflow list as a product
        :param payoff_model: payoff model to derive the expected payoff

        |OptionStrategyCashflowList()| object provides a list of
        |OptionStrategyCashflowList.OptionStrategyCashFlowPayOff| $X_k$ objects
        with payment date $t_k$.

        Adjustetd by offset $X_k$ has expiry date $T_k=t_k-\delta-\epsilon$
        and for all $k$ the same $N_i$, $K_i$, $N_j$, $L_j$ are used.

        """
        payoff_list = list()
        cls = OptionStrategyCashflowList.OptionStrategyCashFlowPayOff
        for expiry in payment_date_list:
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            strategy = cls(expiry,
                           call_amount_list, call_strike_list,
                           put_amount_list, put_strike_list)
            payoff_list.append(strategy)
        super().__init__(payment_date_list, payoff_list, origin, payoff_model)


class ContingentRateCashFlowList(ContingentCashFlowList):
    """ list of cashflows by interest rate payments """

    class ContingentRateCashFlowPayOff(object):

        def __init__(self, start, end=None, amount=DEFAULT_AMOUNT,
                     day_count=None, fixing_offset=None, fixed_rate=0.0,
                     floor_strike=None, cap_strike=None):
            r""" contigent but collared interest rate cashflow payoff

            :param start: cashflow accrued period start date $s$
            :param end: cashflow accrued period end date $e$
            :param amount: notional amount $N$
            :param day_count: function to calculate
                accrued period year fraction $\tau$
            :param fixing_offset: time difference between
                interest rate fixing date
                and interest period payment date $\delta$
            :param fixed_rate: agreed fixed rate $c$
            :param floor_strike: lower interest rate boundary $K$
            :param cap_strike: upper interest rate boundary $L$

            A collared interest rate cashflow payoff $X$
            is given for a float rate $f$ at $T=s-\delta$

            $$X(f(T)) = [\max(K, \min(f(T), L)) + c]\ \tau(s,e)\ N$$

            The foorlet ($\max(K, \dots)$)
            or resp. the caplet condition ($\min(\dots, L)
            will be ignored if $K$ is or resp. $L$ is **None**.

            Invoking $X(m)$ with a |OptionPayOffModel| object $m$ as argument
            returns the acctual expected cashflow payoff amount of $X$.

            """
            self.start = start
            """interes accrued period start date"""
            self.end = end
            """interes accrued period end date"""
            self.day_count = day_count or default_day_count
            """interes accrued period day count method"""
            self.fixing_offset = fixing_offset
            """time difference between
            interest rate fixing date and interest period payment date"""
            self.amount = amount
            """cashflow notional amount"""
            self.fixed_rate = fixed_rate
            """agreed fixed rate"""
            self.floor_strike = floor_strike
            """floor strike rate"""
            self.cap_strike = cap_strike
            """cap strike rate"""

        def __call__(self, model):
            fixing_date = self.start
            if self.fixing_offset:
                fixing_date -= self.fixing_offset

            rate = self.fixed_rate
            if hasattr(model.forward_curve, 'get_cash_rate'):
                rate += model.forward_curve.get_cash_rate(fixing_date)
            else:
                rate += model.forward_curve(fixing_date)
            if self.cap_strike:
                rate -= model.get_call_value(fixing_date, self.cap_strike)
            if self.floor_strike:
                rate += model.get_put_value(fixing_date, self.floor_strike)
            yf = self.day_count(self.start, self.end)
            return rate * yf * self.amount

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 origin=None, day_count=None,
                 fixing_offset=None, pay_offset=None,
                 fixed_rate=0., cap_strike=None, floor_strike=None,
                 payoff_model=None):
        r""" list of contingend collared rate cashflows

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

        Each object consists of a list of
        |ContingentRateCashFlowList.ContingentRateCashFlowPayOff()|, i.e.
        of collared payoff functions

        $$X_i(f(T_i)) = [\max(K, \min(f(T_i), L)) + c]\ \tau(s,e)\ N$$

        with, according to a payment date $p_i$,
        $p_i-\epsilon=e_i$, $e_i=s_{i+1}$ and $s_i-\delta=T_i$.

        """
        cls = ContingentRateCashFlowList.ContingentRateCashFlowPayOff

        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)

        self.day_count = day_count or default_day_count

        payoff_list = list()
        if origin:
            start_dates = [origin]
            start_dates.extend(payment_date_list[:-1])
        elif origin is None and len(payment_date_list) > 1:
            step = payment_date_list[1] - payment_date_list[0]
            start_dates = [payment_date_list[0] - step]
            start_dates.extend(payment_date_list[:-1])
        elif payment_date_list:
            start_dates = payment_date_list

        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            if pay_offset:
                e -= pay_offset
                s -= pay_offset

            payoff = cls(
                start=s, end=e, day_count=day_count,
                fixing_offset=fixing_offset, amount=a, fixed_rate=fixed_rate,
                cap_strike=cap_strike, floor_strike=floor_strike
            )
            payoff_list.append(payoff)

        super().__init__(payment_date_list, payoff_list,
                         origin=origin, payoff_model=payoff_model)

    @property
    def fixed_rate(self):
        return self._flows[self.domain[0]].fixed_rate

    @fixed_rate.setter
    def fixed_rate(self, value):
        for date in self.domain:
            self._flows[date].fixed_rate = value
