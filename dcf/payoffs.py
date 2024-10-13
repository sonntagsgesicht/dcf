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
    _TS = 'pay_date'
    _FLT = 'pay_date'
    _OP = 'amount'

    def details(self, model=None):
        return CashFlowDetails()

    def __call__(self, model=None):
        return self.details(model=model)

    def __copy__(self):
        return self  # added for editor code check

    @property
    def __ts__(self):
        attr = self._TS
        return getattr(self, attr)

    def __float__(self):
        attr = self._FLT
        return getattr(self, attr)

    def __abs__(self):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__abs__()
        setattr(new, attr, value)
        return new

    def __neg__(self):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__neg__()
        setattr(new, attr, value)
        return new

    def __add__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__add__(other)
        setattr(new, attr, value)
        return new

    def __sub__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__sub__(other)
        setattr(new, attr, value)
        return new

    def __mul__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__mul__(other)
        setattr(new, attr, value)
        return new

    def __truediv__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__truediv__(other)
        setattr(new, attr, value)
        return new

    def __matmul__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__matmul__(other)
        setattr(new, attr, value)
        return new

    def __floordiv__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__floordiv__(other)
        setattr(new, attr, value)
        return new

    def __mod__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__mod__(other)
        setattr(new, attr, value)
        return new

    def __divmod__(self, other):
        new = self.__copy__()
        attr = self._OP
        value = getattr(new, attr).__divmod__(other)
        setattr(new, attr, value)
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
                 day_count=None, fixing_offset=None, fixed_rate=0.0):
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

        >>> cf = RateCashFlowPayOff(pay_date=1.0, start=1.25, end=1.5, amount=1.0, fixed_rate=0.005)
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
          'year fraction': 0.25}
        )

        >>> float(cf())
        0.00125

        >>> cf(f)
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

        >>> float(cf(f))
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

    def details(self, model=None):
        day_count = self.day_count or _default_day_count
        yf = day_count(self.start, self.end)

        details = {
            'pay date': self.pay_date,
            'cashflow': 0.0,
            'notional': self.amount,
            'pay rec': 'pay' if self.amount > 0 else 'rec',
            'fixed rate': self.fixed_rate,
            'start date': self.start,
            'end date': self.end,
            'year fraction': yf,
        }

        forward = 0.0
        if model:
            fixing_date = self.start
            if self.fixing_offset:
                fixing_date -= self.fixing_offset

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

        details['cashflow'] = (self.fixed_rate + forward) * yf * self.amount

        return CashFlowDetails(details.items())


class OptionCashFlowPayOff(CashFlowPayOff):

    def __init__(self, pay_date, expiry, amount=DEFAULT_AMOUNT,
                 strike=None, is_put=False):
        r""" European option payoff function

        :param pay_date: cashflow payment date
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

        >>> from dcf import OptionPayOffModel
        >>> from math import exp
        >>> f = lambda t: 100.0 * exp(t * 0.05)  # spot price 100 and yield of 5%
        >>> v = lambda *_: 0.1  # flat volatility of 10%
        >>> m = OptionPayOffModel.black76(valuation_date=0.0, forward_curve=f, volatility_curve=v)

        Then, build a call option payoff.

        >>> from dcf import OptionCashFlowPayOff
        >>> c = OptionCashFlowPayOff(pay_date=0.33, expiry=0.25, strike=110.0)
        >>> # get expected option payoff
        >>> c(m)
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

        >>> float(c(m))
        0.1072...

        And a put option payoff.

        >>> p = OptionCashFlowPayOff(pay_date=0.33, expiry=0.25, strike=110.0, is_put=True)
        >>> # get expected option payoff
        >>> p(m)
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
        
        >>> float(p(m))
        8.8494...

        """  # noqa E501
        self.pay_date = pay_date
        """cashflow payment date"""
        self.expiry = expiry
        self.amount = amount
        self.pay_date = pay_date
        """cashflow amount date"""
        self.strike = strike
        self.is_put = is_put

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


class OptionStrategyCashFlowPayOff(CashFlowPayOff):

    def __init__(self, pay_date, expiry,
                 call_amount_list=DEFAULT_AMOUNT, call_strike_list=(),
                 put_amount_list=DEFAULT_AMOUNT, put_strike_list=()):
        r"""option strategy,
        i.e. series of call and put options with single expiry

        :param pay_date: cashflow payment date
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

        >>> from dcf import OptionPayOffModel
        >>> from math import exp
        >>> #
        >>> f = lambda t: 100.0 * exp(t * 0.05)  # spot price 100 and yield of 5%
        >>> v = lambda *_: 0.1  # flat volatility of 10%
        >>> m = OptionPayOffModel.black76(valuation_date=0.0, forward_curve=f, volatility_curve=v)

        Then, setup a *butterlfy* payoff and evaluate it.

        >>> from dcf import OptionStrategyCashFlowPayOff
        >>> call_amount_list = 1., -2., 1.
        >>> call_strike_list = 100, 110, 120
        >>> s = OptionStrategyCashFlowPayOff(pay_date=0.5, expiry=1., call_amount_list=call_amount_list, call_strike_list=call_strike_list)
        >>> s(m)
        CashFlowDetails(
        { 'pay date': 0.5,
          'cashflow': 3.0692...,
          '#0 cashflow': 7.1538...,
          '#0 put call': 'call',
          '#0 long short': 'long',
          '#0 notional': 1.0,
          '#0 strike': 100,
          '#1 cashflow': -4.5708...,
          '#1 put call': 'call',
          '#1 long short': 'short',
          '#1 notional': -2.0,
          '#1 strike': 110,
          '#2 cashflow': 0.4862...,
          '#2 put call': 'call',
          '#2 long short': 'long',
          '#2 notional': 1.0,
          '#2 strike': 120,
          'valuation date': 0.0,
          'forward': 105.1271...,
          'forward-curve-id': ...,
          'fixing date': 1.0,
          'time to expiry': 1.0,
          'day count': 'None',
          'model-id': ...,
          'volatility': 0.1,
          'volatility-curve-id': ...,
          'formula': 'Black76'}
        )

        >>> float(s(m))
        3.0692...

        """  # noqa E501
        self.pay_date = pay_date
        """cashflow payment date"""

        if isinstance(put_amount_list, (int, float)):
            put_amount_list = [put_amount_list] * len(put_strike_list)
        if isinstance(call_amount_list, (int, float)):
            call_amount_list = [call_amount_list] * len(call_strike_list)

        self._options = list()
        cls = OptionCashFlowPayOff
        for amount, strike in zip(put_amount_list, put_strike_list):
            option = cls(pay_date, expiry, amount, strike, is_put=True)
            self._options.append(option)
        for amount, strike in zip(call_amount_list, call_strike_list):
            option = cls(pay_date, expiry, amount, strike, is_put=False)
            self._options.append(option)
        # sort by strike (in-place and stable, i.e. put < call)
        self._options.sort(key=lambda o: o.strike)

    def details(self, model=None):
        details = {
            'pay date': self.pay_date,
            'cashflow': 0.0
        }
        cf = 0.0
        for i, option in enumerate(self._options):
            for k, v in option(model).items():
                if k in ('cashflow', 'put call', 'long short', 'notional', 'strike'):
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

        return CashFlowDetails(details.items())


class ContingentRateCashFlowPayOff(RateCashFlowPayOff):

    def __init__(self, pay_date, start, end, amount=DEFAULT_AMOUNT,
                 day_count=None, fixing_offset=None, fixed_rate=0.0,
                 floor_strike=None, cap_strike=None):
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

        >>> cf = ContingentRateCashFlowPayOff(pay_date=1.5, start=1.25, end=1.5, amount=1.0, fixed_rate=0.005, floor_strike=0.002)
        >>> cf()
        CashFlowDetails(
        { 'pay date': 1.5,
          'cashflow': 0.00125,
          'notional': 1.0,
          'pay rec': 'pay',
          'fixed rate': 0.005,
          'start date': 1.25,
          'end date': 1.5,
          'year fraction': 0.25}
        )

        >>> float(cf())
        0.00125

        evaluate the fixed rate and float forward rate cashflow

        >>> f = PayOffModel(valuation_date=0.0, forward_curve=(lambda *_: 0.05))
        >>> cf(f)
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

        >>> float(cf(f))
        0.01375

        evaluate the fixed rate and float forward rate cashflow plus intrisic option payoff

        >>> i = OptionPayOffModel.intrinsic(valuation_date=0.0, forward_curve=(lambda *_: 0.05))
        >>> float(cf(i))
        0.01375

        evaluate the fixed rate and float forward rate cashflow plus *Bachelier* model payoff

        >>> v = lambda *_: 0.005
        >>> m = OptionPayOffModel.bachelier(valuation_date=0.0, forward_curve=(lambda *_: 0.05), volatility_curve=v)
        >>> float(cf(m))
        0.01375

        """  # noqa 501
        super().__init__(pay_date, start, end,
                         amount, day_count,
                         fixing_offset, fixed_rate)
        self.floor_strike = floor_strike
        """floor strike rate"""
        self.cap_strike = cap_strike
        """cap strike rate"""

    def details(self, model=None):
        # works even if the model is the forward_curve
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
