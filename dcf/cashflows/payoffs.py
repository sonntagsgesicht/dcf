# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from ..daycount import day_count as default_day_count
from ..models.optionpricing import OptionPayOffModel
from ..plans import DEFAULT_AMOUNT


class CashFlowPayOff(object):
    """Cash flow payoff base class"""

    def __call__(self, _=None):
        return self.details(_).get('cashflow', 0.0)

    def __repr__(self):
        return str(getattr(self, 'amount', self))

    def details(self, _=None):
        return {'cashflow': 0.0}


class FixedCashFlowPayOff(CashFlowPayOff):
    def __init__(self, amount=DEFAULT_AMOUNT):
        r"""fixed cashflow payoff

        :param amount: notional amount $N$

        A fixed cashflow payoff $X$
        is given directly by the notional amount $N$

        Invoking $X()$ or $X(m)$ with a |OptionPayOffModel| object $m$
        as argument
        returns the actual expected cashflow payoff amount of $X$
        which is again just the notional amount $N$.

        >>> from dcf import FixedCashFlowPayOff
        >>> cf = FixedCashFlowPayOff(123.456)
        >>> cf()
        123.456

        """
        self.amount = amount

    def details(self, _=None):
        return {'cashflow': self.amount}


class RateCashFlowPayOff(CashFlowPayOff):
    def __init__(self, start, end, amount=DEFAULT_AMOUNT,
                 day_count=None, fixing_offset=None,
                 fixed_rate=0.0):
        r"""interest rate cashflow payoff

        :param start: cashflow accrued period start date $s$
        :param end: cashflow accrued period end date $e$
        :param amount: notional amount $N$
        :param day_count: function to calculate
            accrued period year fraction $\tau$
        :param fixing_offset: time difference between
            interest rate fixing date
            and interest period payment date $\delta$
        :param fixed_rate: agreed fixed rate $c$

        A contigent interest rate cashflow payoff $X$
        is given for a float rate $f$ at $T=s-\delta$

        $$X(f(T)) = (f(T) + c)\ \tau(s,e)\ N$$

        Invoking $X(m)$ with a |OptionPayOffModel| object $m$ as argument
        returns the actual expected cashflow payoff amount of $X$.

        >>> from dcf import RateCashFlowPayOff, CashRateCurve

        >>> cf = RateCashFlowPayOff(start=1.25, end=1.5, amount=1.0, fixed_rate=0.005)
        >>> f = CashRateCurve(domain=[0.0, 1.0, 2.0], data=[-0.005, 0.00, 0.001], forward_tenor=0.25)

        >>> cf()
        0.00125
        >>> cf(f)
        0.0013125

        """  # noqa 501
        self.start = start
        """interest accrued period start date"""
        self.end = end
        """interest accrued period end date"""
        self.day_count = day_count or default_day_count
        r"""interest accrued period day count method
        for rate period calculation $\tau$"""
        self.fixing_offset = fixing_offset
        """time difference between
        interest rate fixing date and interest period payment date"""
        self.amount = amount
        """cashflow notional amount"""
        self.fixed_rate = fixed_rate
        r""" agreed fixed rate $c$ """

    def details(self, forward_curve=None):
        yf = self.day_count(self.start, self.end)

        details = {
            'cashflow': 0.0,
            'notional': self.amount,
            'pay/rec': 'pay' if self.amount > 0 else 'rec',
            'fixed rate': self.fixed_rate,
            'start date': self.start,
            'end date': self.end,
            'year fraction': yf,
        }

        forward = 0.0
        if forward_curve:
            fixing_date = self.start
            if self.fixing_offset:
                fixing_date -= self.fixing_offset

            if hasattr(forward_curve, 'payoff_model'):
                forward_curve = forward_curve.payoff_model
            if hasattr(forward_curve, 'forward_curve'):
                forward_curve = forward_curve.forward_curve
            if hasattr(forward_curve, 'get_cash_rate'):
                forward = forward_curve.get_cash_rate(fixing_date)
            elif isinstance(forward_curve, (int, float)):
                forward = float(forward_curve)
            else:
                forward = forward_curve(fixing_date)

            details.update({
                'forward rate': forward,
                'fixing date': fixing_date,
                'tenor': getattr(forward_curve, 'forward_tenor', None),
                'forward-curve-id': id(forward_curve)
            })

        details['cashflow'] = (self.fixed_rate + forward) * yf * self.amount
        return details


class OptionCashFlowPayOff(CashFlowPayOff):

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
        |OptionCashFlowPayOff()| object.

        First, setup a classical log-normal *Black-Scholes* model.

        >>> from dcf.models import LogNormalOptionPayOffModel
        >>> from math import exp
        >>> f = lambda t: 100.0 * exp(t * 0.05)  # spot price 100 and yield of 5%
        >>> v = lambda v: 0.1  # flat volatility of 10%
        >>> m = LogNormalOptionPayOffModel(valuation_date=0.0, forward_curve=f, volatility_curve=v)

        Then, build a call option payoff.

        >>> from dcf import OptionCashFlowPayOff
        >>> c = OptionCashFlowPayOff(expiry=0.25, strike=110.0)
        >>> # get expected option payoff
        >>> c(m)
        0.10726740675017865

        And a put option payoff.

        >>> p = OptionCashFlowPayOff(expiry=0.25, strike=110.0, is_put=True)
        >>> # get expected option payoff
        >>> p(m)
        8.849422252686733

        """  # noqa E501
        self.expiry = expiry
        self.amount = amount
        self.strike = strike
        self.is_put = is_put

    def details(self, model=None):
        details = {
            'cashflow': 0.0,
            'put/call': 'put' if self.is_put else 'call',
            'long/short': 'long' if self.amount > 0 else 'short',
            'notional': self.amount,
            'strike': self.strike,
            'expiry date': self.expiry
        }
        if model:
            amount = self.amount
            if self.is_put:
                cf = amount * model.get_put_value(self.expiry, self.strike)
            else:
                cf = amount * model.get_call_value(self.expiry, self.strike)
            details['cashflow'] = cf
            details.update(
                model.details(self.expiry, self.strike)
            )

        return details


class OptionStrategyCashFlowPayOff(CashFlowPayOff):

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

        >>> from dcf import OptionStrategyCashFlowPayOff
        >>> call_amount_list = 1., -2., 1.
        >>> call_strike_list = 100, 110, 120
        >>> s = OptionStrategyCashFlowPayOff(expiry=1., call_amount_list=call_amount_list, call_strike_list=call_strike_list)
        >>> s(m)
        3.06924777745399

        """  # noqa E501
        if isinstance(put_amount_list, (int, float)):
            put_amount_list = [put_amount_list] * len(put_strike_list)
        if isinstance(call_amount_list, (int, float)):
            call_amount_list = [call_amount_list] * len(call_strike_list)

        self._options = list()
        cls = OptionCashFlowPayOff
        for amount, strike in zip(put_amount_list, put_strike_list):
            option = cls(expiry, amount, strike, is_put=True)
            self._options.append(option)
        for amount, strike in zip(call_amount_list, call_strike_list):
            option = cls(expiry, amount, strike, is_put=False)
            self._options.append(option)
        # sort by strike (in-place and stable, i.e. put < call)
        self._options.sort(key=lambda o: o.strike)

    def details(self, model=None):
        details = {
            'cashflow': 0.0
        }
        cf = 0.0
        for i, option in enumerate(self._options):
            for k, v in option.details(model).items():
                details[f"#{i} {k}"] = v
                if k == 'cashflow':
                    cf += v
        if model and self._options:
            d = model.details(self._options[0].expiry)
            d.pop('strike')
            details.update(
                d
            )
        # details['cashflow'] = sum(option(model) for option in self._options)
        details['cashflow'] = cf

        return details


class ContingentRateCashFlowPayOff(RateCashFlowPayOff):

    def __init__(self, start, end, amount=DEFAULT_AMOUNT,
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
        or resp. the caplet condition ($\min(\dots, L)$)
        will be ignored if $K$ is or resp. $L$ is **None**.

        Invoking $X(m)$ with a |OptionPayOffModel| object $m$ as argument
        returns the actual expected cashflow payoff amount of $X$.

        >>> from dcf import ContingentRateCashFlowPayOff, CashRateCurve
        >>> from dcf.models import NormalOptionPayOffModel, IntrinsicOptionPayOffModel

        evaluate just the fixed rate cashflow

        >>> cf = ContingentRateCashFlowPayOff(start=1.25, end=1.5, amount=1.0, fixed_rate=0.005, floor_strike=0.002)
        >>> cf()
        0.00125

        evaluate the fixed rate and float forward rate cashflow

        >>> f = CashRateCurve(domain=[0.0, 1.0, 2.0], data=[-0.005, 0.00, 0.001], forward_tenor=0.25)
        >>> cf(f)
        0.0013125

        evaluate the fixed rate and float forward rate cashflow plus intrisic option payoff

        >>> i = IntrinsicOptionPayOffModel(valuation_date=0.0, forward_curve=f)
        >>> cf(i)
        0.00175

        evaluate the fixed rate and float forward rate cashflow plus *Bachelier* model payoff

        >>> m = NormalOptionPayOffModel(valuation_date=0.0, forward_curve=f, volatility_curve=(lambda *_: 0.005))
        >>> cf(m)
        0.0021158872175425702

        """  # noqa 501
        super().__init__(start, end,
                         amount, day_count,
                         fixing_offset, fixed_rate)
        self.floor_strike = floor_strike
        """floor strike rate"""
        self.cap_strike = cap_strike
        """cap strike rate"""

    def details(self, model=None):
        # works even if the model is the forward_curve
        forward_curve = getattr(model, 'forward_curve', model)
        details = super().details(forward_curve)
        floorlet = caplet = 0.0
        if isinstance(model, OptionPayOffModel):
            fixing_date = details['fixing date']
            yf = details['year fraction']
            amount = details['notional']
            cf = details['cashflow']

            d = None
            if self.floor_strike is not None:
                d = model.details(fixing_date, self.floor_strike)
                floorlet = model.get_put_value(fixing_date, self.floor_strike)
                # floorlet -= forward_rate
                floorlet *= yf * amount
                details.update({
                    'floorlet': floorlet,
                    'floorlet strike': self.floor_strike,
                    'floorlet volatility': d.get('volatility', None),
                })

            if self.cap_strike is not None:
                d = model.details(fixing_date, self.cap_strike)
                caplet = model.get_call_value(fixing_date, self.cap_strike)
                # caplet += forward_rate
                caplet *= yf * amount
                details.update({
                    'caplet': caplet,
                    'caplet strike': self.cap_strike,
                    'caplet volatility': d.get('volatility', None),
                })

            if d:
                details.update({
                    'time to expiry': d.get('time to expiry', None),
                    'valuation date': d.get('valuation date', None)
                })
            details['cashflow'] = cf + floorlet - caplet
        return details
