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
from warnings import warn

from prettyclass import prettyclass

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

from .daycount import day_count as _default_day_count
from .details import Details
from .plans import DEFAULT_AMOUNT


@prettyclass(init=False)
class CashFlowPayOff:
    """Cash flow payoff base class"""

    def details(self, valuation_date=None, **__):
        return Details()

    def __call__(self, valuation_date=None, **__):
        return self.details(valuation_date, **__).get('cashflow', None)

    def __copy__(self):
        return self  # added for editor code check

    @property
    def __ts__(self):
        return getattr(self, 'pay_date')

    def __float__(self):
        return float(self() or 0.0)

    def __abs__(self):
        new = self.__copy__()
        new.amount = new.amount.__abs__()
        return new

    def __neg__(self):
        new = self.__copy__()
        new.amount = new.amount.__neg__()
        return new

    def __add__(self, other):
        if isinstance(other, CashFlowPayOff):
            return CashFlowList([self, other])
        new = self.__copy__()
        new.amount = new.amount.__add__(other)
        return new

    def __sub__(self, other):
        if isinstance(other, CashFlowPayOff):
            return CashFlowList([self, -other])
        new = self.__copy__()
        new.amount = new.amount.__sub__(other)
        return new

    def __mul__(self, other):
        new = self.__copy__()
        if isinstance(other, CashFlowPayOff):
            new.amount = (other * new.amount)
        else:
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

    def __init__(self, pay_date, amount=DEFAULT_AMOUNT, forward_curve=None):
        r"""fixed cashflow payoff

        :param pay_date: cashflow payment date $t$
        :param amount: notional amount $N$ (might be a callable function)
        :param forward_curve: price forward curve $P$

        A fixed cashflow payoff $X(t)$ at $t$
        is given directly by the notional amount $N + P(t)$

        Invoking **details** method $X()$ or $X(m)$
        with a |OptionPayOffModel()| object $m$
        as argument returns the cashflow details as a dict-like object.

        >>> from dcf import FixedCashFlowPayOff
        >>> cf = FixedCashFlowPayOff(0.25, amount=123.456)
        >>> cf.details()
        Details(
        {'pay date': 0.25, 'cashflow': 123.456}
        )

        >>> cf = FixedCashFlowPayOff(0.25, amount=123.456)
        >>> cf.details()

        The actual expected cashflow payoff amount of $X$
        (which is again just the fixed amount $N$)
        can be obtained by casting to **float**.

        >>> cf()
        123.456

        """
        self.pay_date = pay_date
        r"""cashflow payment date $t$"""
        self.amount = amount
        r"""cashflow notional amount $N$"""
        self.forward_curve = forward_curve
        r"""forward price curve $S(t)$"""

    def details(self, valuation_date=None, *, forward_curve=None, **__):
        amount = self.amount
        if callable(amount):
            amount = amount(valuation_date)
        details = {
            'pay date': self.pay_date,
            'cashflow': float(amount or 0.0)
        }
        forward = 0.0
        if self.forward_curve is not None:
            if forward_curve is None:
                forward_curve = self.forward_curve

            if callable(forward_curve):
                forward = forward_curve(self.pay_date)
            else:
                forward = forward_curve

            details.update({
                'fixed amount': float(amount or 0.0),
                'forward price': float(forward or 0.0),
            })
            if hasattr(forward_curve, 'details'):
                details.update(forward_curve.details())
            details['forward-curve-id'] = id(forward_curve)

        details['cashflow'] += forward
        return Details(details.items())


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
        :param forward_curve: float rate forward curve
            either as numerical value or function.
            If **forward_curve** is **None** 
            no float rate is applied, 
            even not if |RateCashFlowPayOff().details()| is invoked 
            with a forward furve or |PayOffModel()|.   
            (optional; default is None, i.e. no float rate is applied)

        A contigent interest rate cashflow payoff $X$
        is given for a float rate $f$ at $T=s-\delta$

        $$X(f(T)) = (f(T) + c)\ \tau(s,e)\ N$$

        Invoking $X(m)$ with a |OptionPayOffModel| object $m$ as argument
        returns the actual expected cashflow payoff amount of $X$.

        >>> from dcf import RateCashFlowPayOff

        >>> cf = RateCashFlowPayOff(pay_date=1.0, start=1.25, end=1.5, amount=1.0, fixed_rate=0.005, forward_curve=0)
        >>> cf.details()
        Details(
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

        >>> cf()
        0.00125

        suppying an iterest forward curve changes float forward rate  
        
        >>> forward_curve = 0.05
        >>> cf.details(forward_curve)
        Details(
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

        >>> cf(forward_curve)  # expected cashflow
        0.01375

        If **forward_curve** is **None** (default) no float rate is applied.
        Even if **forward_curve** is given for details calculation.

        >>> cf = RateCashFlowPayOff(pay_date=1.0, start=1.25, end=1.5, amount=1.0, fixed_rate=0.005)
        >>> cf.details(forward_curve)
        Details(
        { 'pay date': 1.0,
          'cashflow': 0.00125,
          'notional': 1.0,
          'pay rec': 'pay',
          'fixed rate': 0.005,
          'start date': 1.25,
          'end date': 1.5,
          'year fraction': 0.25}
        )

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
        r"""agreed fixed rate $c$ """
        self.forward_curve = forward_curve
        r"""forward rate curve $f(t)$"""

    def details(self, valuation_date=None, *, forward_curve=None, **__):
        amount = self.amount
        if callable(amount):
            amount = amount(valuation_date)
        day_count = self.day_count or _default_day_count
        yf = day_count(self.start, self.end)
        fixed_rate = self.fixed_rate or 0.0
        details = {
            'pay date': self.pay_date,
            'cashflow': 0.0,
            'notional': amount,
            'pay rec': 'pay' if amount > 0 else 'rec',
            'fixed rate': fixed_rate,
            'start date': self.start,
            'end date': self.end,
            'year fraction': yf,
        }
        if self.day_count:
            dc = getattr(self.day_count, '__qualname__', str(self.day_count))
            details['day count'] = dc

        forward = 0.0
        if self.forward_curve is not None:
            # otherwise it's a fixed_rate only cashflow
            fixing_date = self.start
            if self.fixing_offset:
                fixing_date -= self.fixing_offset

            if forward_curve is None:
                forward_curve = self.forward_curve
            if callable(forward_curve):
                forward = forward_curve(fixing_date)
            else:
                forward = float(forward_curve)

            details.update({
                'forward rate': float(forward or 0.0),
                'fixing date': fixing_date,
            })
            if hasattr(forward_curve, 'details'):
                details.update(forward_curve.details())
            details['forward-curve-id'] = id(forward_curve)
        details['cashflow'] = \
            (fixed_rate + forward) * yf * float(amount or 0.0)
        return Details(details.items()).drop(None)


class OptionCashFlowPayOff(CashFlowPayOff):

    PUT_TYPES = 'put', 'floor',  # 'floorlet'
    CALL_TYPES = 'call', 'cap',  # 'caplet'
    OPTION_TYPES = {k: k for k in PUT_TYPES + CALL_TYPES}

    def __init__(self, pay_date, expiry=None, amount=DEFAULT_AMOUNT,
                 strike=None, option_type='call', *,
                 forward_curve=None, option_curve=None):
        r""" European option payoff function

        :param pay_date: cashflow payment date
        :param expiry: option exipry date $T$ 
            (optional; by default **pay_date**) 
        :param amount: option notional amount $N$
            (optional: default is 1.0)
        :param strike: strike price $K$
            (optional: default is **None** i.e. at-the-money strike)
        :param option_type: str or **OptionCashFlowPayOff.OPTION_TYPES** enum
            to prick for option type **call**, **put**, **cap**, **floor**
            (optional with default **call**)

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

        >>> from dcf import OptionPricingCurve
        >>> from math import exp
        >>> f = lambda t: 100.0 * exp(t * 0.05)  # spot price 100 and yield of 5%
        >>> v = lambda *_: 0.1  # flat volatility of 10%
        >>> m = OptionPricingCurve.black76(f, volatility_curve=v)

        Then, build a call option payoff.

        >>> from dcf import OptionCashFlowPayOff
        >>> c = OptionCashFlowPayOff(pay_date=0.33, expiry=0.25, strike=110.0)
        >>> # get expected option payoff
        >>> c.details(forward_curve=m)
        Details(
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

        >>> float(c.details(forward_curve=m))
        0.1072...

        And a put option payoff.

        >>> p = OptionCashFlowPayOff(pay_date=0.33, expiry=0.25, strike=110.0, is_put=True)
        >>> # get expected option payoff
        >>> p.details(forward_curve=m)
        Details(
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
        
        >>> float(p.details(forward_curve=m))
        8.8494...

        """  # noqa E501
        self.pay_date = pay_date
        self.expiry = expiry
        self.amount = amount
        self.strike = strike
        self.option_type = str(self.OPTION_TYPES[str(option_type).lower()])

        self.forward_curve = forward_curve
        self.option_curve = option_curve

    def details(self, valuation_date=None, *,
                forward_curve=None, option_curve=None, **__):
        if forward_curve is None:
            forward_curve = self.forward_curve
        if option_curve is None:
            option_curve = self.option_curve
        amount = self.amount
        if callable(amount):
            amount = amount(valuation_date)
        expiry_date = self.pay_date if self.expiry is None else self.expiry
        is_put = str(self.option_type) in self.PUT_TYPES

        details = {
            'pay date': self.pay_date,
            'cashflow': 0.0,
            'option type': str(self.option_type),
            'is put': is_put,
            'long short': 'long' if float(amount or 0.0) > 0 else 'short',
            'notional': float(amount or 0.0),
            'strike': 'atm' if self.strike is None else self.strike,
            'forward': None,
            'tenor': None,
            'valuation date': valuation_date,
            'expiry date': expiry_date,
            'time to expiry': None,
            'volatility': None,
            'option model': 'unknown'
        }

        if forward_curve is not None or option_curve is not None:
            x, y = valuation_date, expiry_date

            # gather further details

            if hasattr(forward_curve, 'details'):
                details.update(forward_curve.details(x, y))
            if hasattr(option_curve, 'details'):
                details.update(option_curve.details(x, y, strike=self.strike))

            # put curve-id details at end

            if forward_curve is not None:
                details['forward-curve-id'] = \
                    details.pop('forward-curve-id', id(forward_curve))
            if option_curve is not None:
                details['option-curve-id'] = \
                    details.pop('option-curve-id', id(option_curve))

            # value vanilla option (prio option_curve over forward_curve)

            if hasattr(option_curve, 'call'):
                option = option_curve.call(x, y, strike=self.strike)
            elif option_curve is not None:
                option = option_curve(x, y, strike=self.strike)
            elif hasattr(forward_curve, 'call'):
                option = forward_curve.call(x, y, strike=self.strike)
            else:
                option = 0.0
                if self.strike is not None:
                    # fallback to forward_curve
                    forward = forward_curve
                    if callable(forward):
                        forward = forward(y)
                    details['forward'] = forward = float(forward)
                    option = max(forward - self.strike, 0.0)
                details['option model'] = 'no model'

            if is_put and self.strike is not None:
                # put call parity
                forward = forward_curve
                if callable(forward):
                    forward = forward(y)
                details['forward'] = forward = float(forward)
                option = self.strike - forward + option

            details['cashflow'] = option * float(amount or 0.0)

        return Details(details.items()).drop(None)


class DigitalOptionCashFlowPayOff(OptionCashFlowPayOff):

    def details(self, valuation_date=None, *,
                forward_curve=None, option_curve=None, **__):

        details = super().details(valuation_date, forward_curve=forward_curve,
                                  option_curve=option_curve, **__)
        # add 'is digital' flag
        pos = list(details.keys()).index('is put')
        items = list(details.items())
        items.insert(pos, ('is digital', True))
        details = dict(items)

        # value binary option (prio option_curve over forward_curve)

        if forward_curve is not None or option_curve is not None:
            x, y = valuation_date, details['expiry date']

            if hasattr(option_curve, 'binary_call'):
                option = option_curve.binary(x, y, strike=self.strike)
            elif hasattr(option_curve, 'binary'):
                option = option_curve.call(x, y, strike=self.strike)
            elif option_curve is not None:
                option = option_curve(x, y, strike=self.strike)
            elif hasattr(forward_curve, 'binary_call'):
                option = forward_curve.binary_call(x, y, strike=self.strike)
            elif hasattr(forward_curve, 'binary'):
                option = forward_curve.binary(x, y, strike=self.strike)
            else:
                option = 1.0
                # fallback to forward_curve
                forward = forward_curve
                if callable(forward):
                    forward = forward(y)
                details['forward'] = forward = float(forward)
                if self.strike is not None and forward < self.strike:
                    option = 0.0
                details['option model'] = 'no model'

            if details['is put'] and self.strike is not None:
                # put call parity
                option = 1.0 - option

            details['cashflow'] = option * details['notional']


class CashFlowList(TSList):
    """cashflow payoff container"""

    @classmethod
    def from_fixed_cashflows(
            cls,
            payment_date_list,
            amount_list=DEFAULT_AMOUNT,
            forward_curve=None):
        """ basic cashflow list object

        :param payment_date_list: list of cashflow payment dates
        :param amount_list: list of cashflow amounts
        :param forward_curve: curve to derive forward values
        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)
        ta_list = zip(payment_date_list, amount_list)
        return cls(FixedCashFlowPayOff(t, a, forward_curve=forward_curve)
                   for t, a in ta_list)

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
            option_type='call',
            is_digital=False,
            fixing_offset=None,
            pay_offset=None,
            forward_curve=None):
        r""" list of European option payoffs

        :param payment_date_list: list of cashflow payment dates $t_k$
        :param amount_list: list of option notional amounts $N_k$
        :param strike_list: list of option strike prices $K_k$
        :param option_type: enum to prick for option type
            **call**, **put**, **cap**, **floor**
            (optional with default **call**)
        :param is_digital: bool flag if option is digital/binary option
            (optional with default **False**)
        :param fixing_offset: offset $\delta$ between
            underlying fixing date and cashflow end date
        :param pay_offset: offset $\epsilon$ between
            cashflow end date and payment date
        :param forward_curve: curve to derive underlying forward value

        List of |OptionCashFlowPayOff()| or |DigitalOptionCashFlowPayOff()|.

        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)
        if isinstance(strike_list, (int, float)) or strike_list is None:
            strike_list = [strike_list] * len(payment_date_list)
        if isinstance(option_type, str):
            option_type = [option_type] * len(payment_date_list)

        payoff_list = list()
        option_cls = \
            DigitalOptionCashFlowPayOff if is_digital else OptionCashFlowPayOff
        for pay_date, amount, strike, o_type in \
                zip(payment_date_list, amount_list, strike_list, option_type):
            expiry = pay_date
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            option = option_cls(
                pay_date=pay_date,
                expiry=expiry,
                amount=amount,
                strike=strike,
                option_type=o_type,
                forward_curve=forward_curve
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
            forward_curve=None):
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
        :param forward_curve: curve to derive underlying forward value

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
            forward = RateCashFlowPayOff(
                pay_date=pay_date,
                start=s, end=e, day_count=day_count,
                fixing_offset=fixing_offset, amount=a, fixed_rate=fixed_rate,
                # cap_strike=cap_strike, floor_strike=floor_strike,
                forward_curve=forward_curve
            )
            expiry = s
            if fixing_offset:
                expiry -= fixing_offset
            payoff_list.append(forward)
            floorlet = OptionCashFlowPayOff(
                pay_date=pay_date, expiry=expiry, amount=a,
                strike=floor_strike, option_type='floor',
                forward_curve=forward_curve
            )
            payoff_list.append(floorlet)
            caplet = OptionCashFlowPayOff(
                pay_date=pay_date, expiry=expiry, amount=a,
                strike=cap_strike, option_type='cap',
                forward_curve=forward_curve
            )
            payoff_list.append(caplet)

        return cls(payoff_list)

    @property
    def domain(self):
        """ payment date list """
        return tuple(getattr(v, 'pay_date', None) for v in self)

    @property
    def origin(self):
        """ cashflow list start date """
        origin = min(self.domain, default=None)
        starts = (getattr(v, 'start', None) for v in self)
        return min(starts, default=origin)

    def __init__(self, iterable=(), /):
        """cashflow payoff container

        :param iterable:
        """
        super().__init__(iterable)

    def __call__(self, valuation_date=None, **__):
        return [v(valuation_date, **__) for v in self]

    def details(self, valuation_date=None, **__):
        return [v.details(valuation_date, **__) for v in self]

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

    def __add__(self, other):
        if isinstance(other, list):
            return self.__class__(super().__add__(other))
        if isinstance(other, CashFlowPayOff):
            return self + [other]
        return self.__class__(v.__add__(other) for v in self)

    def __sub__(self, other):
        if isinstance(other, list):
            # lousy hack since other might just be list and not List
            return self.__neg__().__add__(other).__neg__()
        if isinstance(other, CashFlowPayOff):
            return self - [other]
        return self.__class__(v.__sub__(other) for v in self)

    def __mul__(self, other):
        return self.__class__(v.__mul__(other) for v in self)

    def __truediv__(self, other):
        return self.__class__(v.__truediv__(other) for v in self)

    def __matmul__(self, other):
        return self.__class__(v.__matmul__(other) for v in self)
