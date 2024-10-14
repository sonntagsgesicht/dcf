# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from pprint import pformat

from prettyclass import prettyclass

from .daycount import day_count as _default_day_count
from .payoffmodels import OptionPayOffModel
from .plans import DEFAULT_AMOUNT


class CashFlowDetails(dict):

    def __float__(self):
        return float(self.get('cashflow', 0.0))

    @property
    def __ts__(self):
        return self.get('pay date')

    def __getattr__(self, item):
        return self.get(item.replace('_', ' '))

    def __repr__(self):
        c = self.__class__.__name__
        s = pformat(dict(self.items()), indent=2, sort_dicts=False)
        return f"{c}(\n{s}\n)"


@prettyclass(init=False)
class CashFlowPayOff:
    """Cash flow payoff base class"""

    def details(self, model=None):
        return CashFlowDetails()

    def __call__(self, valuation_date=None):
        if hasattr(self, 'payoff_model') and valuation_date:
            return self.payoff_model(self, valuation_date)
        return self.details()

    def __copy__(self):
        return self  # added for editor code check

    @property
    def __ts__(self):
        return getattr(self, 'pay_date')

    def __float__(self):
        return float(self())

    def __abs__(self):
        new = self.__copy__()
        new.amount = new.amount.__abs__()
        return new

    def __neg__(self):
        new = self.__copy__()
        new.amount = new.amount.__neg__()
        return new

    def __add__(self, other):
        new = self.__copy__()
        new.amount = new.amount.__add__(other)
        return new

    def __sub__(self, other):
        new = self.__copy__()
        new.amount = new.amount.__sub__(other)
        return new

    def __mul__(self, other):
        new = self.__copy__()
        new.amount = new.amount.__mul__(other)
        return new

    def __truediv__(self, other):
        new = self.__copy__()
        new.amount = new.amount.__truediv__(other)
        return new

    def __matmul__(self, other):
        new = self.__copy__()
        new.amount = new.amount.__matmul__(other)
        return new

    def __floordiv__(self, other):
        new = self.__copy__()
        new.amount = new.amount.__floordiv__(other)
        return new

    def __mod__(self, other):
        new = self.__copy__()
        new.amount = new.amount.__mod__(other)
        return new


class FixedCashFlowPayOff(CashFlowPayOff):

    def __init__(self, pay_date, amount=DEFAULT_AMOUNT):
        r"""fixed cashflow payoff

        :param pay_date: cashflow payment date
        :param amount: notional amount $N$

        A fixed cashflow payoff $X$
        is given directly by the notional amount $N$

        Invoking $X()$ or $X(m)$ with a |OptionPayOffModel()| object $m$
        as argument returns the cashflow details as a dict-like object.

        >>> from dcf import FixedCashFlowPayOff
        >>> cf = FixedCashFlowPayOff(0.25, amount=123.456)
        >>> cf()
        CashFlowDetails(
        {'pay date': 0.25, 'cashflow': 123.456}
        )

        The actual expected cashflow payoff amount of $X$
        (which is again just the fixed amount $N$)
        can be obtained by casting to **float**.

        >>> float(cf())
        123.456

        """
        self.pay_date = pay_date
        """cashflow payment date"""
        self.amount = amount
        """cashflow notional amount"""

    def details(self, model=None):
        details = {
            'pay date': self.pay_date,
            'cashflow': self.amount
        }
        return CashFlowDetails(details.items())


class RateCashFlowPayOff(CashFlowPayOff):

    def __init__(self, pay_date, start, end, amount=DEFAULT_AMOUNT,
                 day_count=None, fixing_offset=None, fixed_rate=None,
                 forward_curve=None):
        r"""interest rate cashflow payoff

        :param pay_date: cashflow payment date
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

        >>> from dcf import RateCashFlowPayOff

        >>> cf = RateCashFlowPayOff(pay_date=1.0, start=1.25, end=1.5, amount=1.0, fixed_rate=0.005, forward_curve=0)
        >>> f = lambda *_: 0.05

        >>> cf()
        CashFlowDetails(
        { 'pay date': 1.0,
          'cashflow': 0.00125,
          'notional': 1.0,
          'pay rec': 'pay',
          'fixed rate': 0.005,
          'start date': 1.25,
          'end date': 1.5,
          'year fraction': 0.25,
          'forward rate': 0.0,
          'fixing date': 1.25,
          'tenor': None,
          'forward-curve-id': ...}
        )

        >>> float(cf())
        0.00125

        >>> cf.details(f)
        CashFlowDetails(
        { 'pay date': 1.0,
          'cashflow': 0.01375,
          'notional': 1.0,
          'pay rec': 'pay',
          'fixed rate': 0.005,
          'start date': 1.25,
          'end date': 1.5,
          'year fraction': 0.25,
          'forward rate': 0.05,
          'fixing date': 1.25,
          'tenor': None,
          'forward-curve-id': ...}
        )

        >>> float(cf.details(f))
        0.01375

        """  # noqa 501
        self.pay_date = pay_date
        """cashflow payment date"""
        self.start = start
        """interest accrued period start date"""
        self.end = end
        """interest accrued period end date"""
        self.day_count = day_count
        r"""interest accrued period day count method
        for rate period calculation $\tau$"""
        self.fixing_offset = fixing_offset
        """time difference between
        interest rate fixing date and interest period payment date"""
        self.amount = amount
        """cashflow notional amount"""
        self.fixed_rate = fixed_rate
        r""" agreed fixed rate $c$ """
        self.forward_curve = forward_curve

    def details(self, model=None):
        day_count = self.day_count or _default_day_count
        yf = day_count(self.start, self.end)
        fixed_rate = self.fixed_rate or 0.0

        details = {
            'pay date': self.pay_date,
            'cashflow': 0.0,
            'notional': self.amount,
            'pay rec': 'pay' if self.amount > 0 else 'rec',
            'fixed rate': fixed_rate,
            'start date': self.start,
            'end date': self.end,
            'year fraction': yf,
        }

        forward = 0.0
        if self.forward_curve is not None:
            # otherwise it's a fixed_rate only cashflow
            fixing_date = self.start
            if self.fixing_offset:
                fixing_date -= self.fixing_offset

            if model is None:
                model = self.forward_curve

            if hasattr(model, 'payoff_model'):
                model = model.payoff_model
            if hasattr(model, 'forward_curve'):
                model = model.forward_curve
            if callable(model):
                forward = model(fixing_date)
            else:
                forward = float(model or 0.0)

            details.update({
                'forward rate': forward,
                'fixing date': fixing_date,
                'tenor': getattr(model, 'forward_tenor', None),
                'forward-curve-id': id(model)
            })

        details['cashflow'] = (fixed_rate + forward) * yf * self.amount
        return CashFlowDetails(details.items())


class OptionCashFlowPayOff(CashFlowPayOff):

    def __init__(self, pay_date, expiry=None, amount=DEFAULT_AMOUNT,
                 strike=None, is_put=False, payoff_model=None):
        r""" European option payoff function

        :param pay_date: cashflow payment date
        :param expiry: option exipry date $T$ 
            (optional; by default **pay_date**) 
        :param amount: option notional amount $N$
            (optional: default is 1.0)
        :param strike: strike price $K$
            (optional: default is **None** i.e. at-the-money strike)
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

        >>> from dcf import OptionPayOffModel
        >>> from math import exp
        >>> f = lambda t: 100.0 * exp(t * 0.05)  # spot price 100 and yield of 5%
        >>> v = lambda *_: 0.1  # flat volatility of 10%
        >>> m = OptionPayOffModel.black76(valuation_date=0.0, forward_curve=f, volatility_curve=v)

        Then, build a call option payoff.

        >>> from dcf import OptionCashFlowPayOff
        >>> c = OptionCashFlowPayOff(pay_date=0.33, expiry=0.25, strike=110.0)
        >>> # get expected option payoff
        >>> c.details(m)
        CashFlowDetails(
        { 'pay date': 0.33,
          'cashflow': 0.1072...,
          'put call': 'call',
          'long short': 'long',
          'notional': 1.0,
          'strike': 110.0,
          'expiry date': 0.25,
          'valuation date': 0.0,
          'forward': 101.2578...,
          'forward-curve-id': ...,
          'fixing date': 0.25,
          'time to expiry': 0.25,
          'day count': 'None',
          'model-id': ...,
          'volatility': 0.1,
          'volatility-curve-id': ...,
          'formula': 'Black76'}
        )

        >>> float(c.details(m))
        0.1072...

        And a put option payoff.

        >>> p = OptionCashFlowPayOff(pay_date=0.33, expiry=0.25, strike=110.0, is_put=True)
        >>> # get expected option payoff
        >>> p.details(m)
        CashFlowDetails(
        { 'pay date': 0.33,
          'cashflow': 8.8494...,
          'put call': 'put',
          'long short': 'long',
          'notional': 1.0,
          'strike': 110.0,
          'expiry date': 0.25,
          'valuation date': 0.0,
          'forward': 101.2578...,
          'forward-curve-id': ...,
          'fixing date': 0.25,
          'time to expiry': 0.25,
          'day count': 'None',
          'model-id': ...,
          'volatility': 0.1,
          'volatility-curve-id': ...,
          'formula': 'Black76'}
        )
        
        >>> float(p.details(m))
        8.8494...

        """  # noqa E501
        self.pay_date = pay_date
        self.expiry = pay_date if expiry is None else expiry
        self.amount = amount
        self.strike = strike
        self.is_put = is_put
        self.payoff_model = payoff_model

    def details(self, model=None):
        details = {
            'pay date': self.pay_date,
            'cashflow': 0.0,
            'put call': 'put' if self.is_put else 'call',
            'long short': 'long' if self.amount > 0 else 'short',
            'notional': self.amount,
            'strike': self.strike,
            'expiry date': self.expiry
        }
        if model is None:
            model = self.payoff_model

        if isinstance(model, OptionPayOffModel):
            amount = self.amount
            if self.is_put:
                cf = amount * model.put_value(self.expiry, self.strike)
            else:
                cf = amount * model.call_value(self.expiry, self.strike)
            details['cashflow'] = cf
            details.update(
                model.details(self.expiry, self.strike)
            )

        return CashFlowDetails(details.items())


class ContingentRateCashFlowPayOff(RateCashFlowPayOff):

    def __init__(self, pay_date, start, end, amount=DEFAULT_AMOUNT,
                 day_count=None, fixing_offset=None, fixed_rate=None,
                 floor_strike=None, cap_strike=None, payoff_model=None):
        r""" contigent but collared interest rate cashflow payoff

        :param pay_date: cashflow payment date
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

        >>> from dcf import ContingentRateCashFlowPayOff
        >>> from dcf import PayOffModel, OptionPayOffModel

        evaluate just the fixed rate cashflow

        >>> cf = ContingentRateCashFlowPayOff(pay_date=1.5, start=1.25, end=1.5, amount=1.0, fixed_rate=0.005, floor_strike=0.002, payoff_model=0.0)
        >>> cf.details()
        CashFlowDetails(
        { 'pay date': 1.5,
          'cashflow': 0.00125,
          'notional': 1.0,
          'pay rec': 'pay',
          'fixed rate': 0.005,
          'start date': 1.25,
          'end date': 1.5,
          'year fraction': 0.25,
          'forward rate': 0.0,
          'fixing date': 1.25,
          'tenor': None,
          'forward-curve-id': ...}
        )

        >>> float(cf.details())
        0.00125

        evaluate the fixed rate and float forward rate cashflow

        >>> f = PayOffModel(valuation_date=0.0, forward_curve=(lambda *_: 0.05))
        >>> cf.details(f)
        CashFlowDetails(
        { 'pay date': 1.5,
          'cashflow': 0.01375,
          'notional': 1.0,
          'pay rec': 'pay',
          'fixed rate': 0.005,
          'start date': 1.25,
          'end date': 1.5,
          'year fraction': 0.25,
          'forward rate': 0.05,
          'fixing date': 1.25,
          'tenor': None,
          'forward-curve-id': ...}
        )

        >>> float(cf.details(f))
        0.01375

        evaluate the fixed rate and float forward rate cashflow plus intrisic option payoff

        >>> i = OptionPayOffModel.intrinsic(valuation_date=0.0, forward_curve=(lambda *_: 0.05))
        >>> float(cf.details(i))
        0.01375

        evaluate the fixed rate and float forward rate cashflow plus *Bachelier* model payoff

        >>> v = lambda *_: 0.005
        >>> m = OptionPayOffModel.bachelier(valuation_date=0.0, forward_curve=(lambda *_: 0.05), volatility_curve=v)
        >>> float(cf.details(m))
        0.01375

        """  # noqa 501
        super().__init__(pay_date, start, end,
                         amount, day_count,
                         fixing_offset, fixed_rate, forward_curve=payoff_model)
        self.floor_strike = floor_strike
        """floor strike rate"""
        self.cap_strike = cap_strike
        """cap strike rate"""
        self.payoff_model = payoff_model

    def details(self, model=None):
        # works even if the model is the forward_curve
        if model is None:
            model = self.payoff_model

        details = super().details(model=model)
        floorlet = caplet = 0.0

        yf = details['year fraction']
        amount = details['notional']
        cf = details['cashflow']

        if isinstance(model, OptionPayOffModel):
            d = None
            if self.floor_strike is not None:
                fixing_date = details['fixing date']
                d = model.details(fixing_date, self.floor_strike)
                floorlet = model.put_value(fixing_date, self.floor_strike)
                # floorlet -= forward_rate
                floorlet *= yf * amount
                details.update({
                    'floorlet': floorlet,
                    'floorlet strike': self.floor_strike,
                    'floorlet volatility': d.get('volatility', None),
                })

            if self.cap_strike is not None:
                fixing_date = details['fixing date']
                d = model.details(fixing_date, self.cap_strike)
                caplet = model.call_value(fixing_date, self.cap_strike)
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
        return CashFlowDetails(details.items())
