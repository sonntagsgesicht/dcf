# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from ..daycount import day_count as _default_day_count, \
    DAYS_IN_YEAR as _DAYS_IN_YEAR


class OptionPricingFormula(object):
    r"""abstract base class for option pricing formulas

    A |OptionPricingFormula| $f$ serves as a kind of interface template
    to enhance |OptionPayOffModel| by a new model.

    To do so, $f$ should at least implement a method

    * **__call__(time, strike, forward, volatility)**

    to provide the expected payoff of an Europen call option.
    Alternativly, it could implement the same signatur for a private

    * **_call_price(time, strike, forward, volatility)**

    method. These and all follwing method are only related to call options
    since put options will be derivend by the use of
    `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_.

    Moreover, the **volatility** argument should be understood as
    a general input of model parameters which ar in case of classical
    option pricing formulas like |LogNormalOptionPayOffModel()|
    the volatility.

    To provide non-numerical derivatives implement

    * **_call_delta(time, strike, forward, volatility)**

    for delta $\Delta_f$, the first derivative along the underlying

    * **_call_gamma(time, strike, forward, volatility)**

    for gamma $\Gamma_f$, the second derivative along the underlying

    * **_call_vega(time, strike, forward, volatility)**

    for vega $\mathcal{V}_f$,
    the first derivative along the volatility parameters

    * **_call_theta(time, strike, forward, volatility)**

    for theta $\Theta_f$,
    the first derivative along the time parameter **time**

    """

    @classmethod
    def from_function(cls, func, name=None):
        """create new type (class) of an OptionPricingFormula

        :param func: function serving as **__call__** method
            as in |OptionPricingFormula|
        :return: subclass of |OptionPricingFormula|

        """
        if name is None:
            name = func.__name__ + cls.__name__
        return type(name, cls, {'__call__': func})

    def __call__(self, time, strike, forward, volatility):
        return self._call_price(time, strike, forward, volatility)

    def _call_price(self, time, strike, forward, volatility):
        return self.__call__(time, strike, forward, volatility)

    def _call_delta(self, time, strike, forward, volatility):
        return

    def _call_gamma(self, time, strike, forward, volatility):
        return

    def _call_vega(self, time, strike, forward, volatility):
        return

    def _call_theta(self, time, strike, forward, volatility):
        return


class OptionPayOffModel(OptionPricingFormula):
    """base option payoff model to derive expected payoff cashflows"""

    DELTA_SHIFT = 0.0001
    r"""finite difference to calculate numerical delta sensitivities
    """
    DELTA_SCALE = 0.0001
    r"""factor to express numerical delta sensitivities
    usually in a value of a basis point (bpv)

    Let $\delta$ be the **DELTA_SHIFT**
    and $\epsilon$ be the **DELTA_SCALE**
    and $f$ a forward $F$ sensitive function
    such that
    $$f' = \frac{df}{dF} \approx
    \Delta_f(F) = \frac{f(F+\delta) - f(x)}{\delta/\epsilon}.$$
    """
    VEGA_SHIFT = 0.01
    r"""finite difference to calculate numerical vega sensitivities
    """
    VEGA_SCALE = 0.01
    r"""factor to express numerical vega sensitivities

    Let $\delta$ be the **VEGA_SHIFT**
    and $\epsilon$ be the **VEGA_SCALE**
    and $f$ a volatility $\nu$ sensitive function
    such that
    $$f'_\nu = \frac{df}{d\nu} \approx
    \mathcal{V}_f(\nu) = \frac{f(\nu+\delta) - f(\nu)}{\delta/\epsilon}.$$
    """
    THETA_SHIFT = 1 / _DAYS_IN_YEAR
    r"""finite difference to calculate numerical theta sensitivities
    usually one day (1/365.25)"""
    THETA_SCALE = 1 / _DAYS_IN_YEAR
    r"""factor to express numerical theta sensitivities
    usually one day (1/365.25)

    Let $\delta$ be the **THETA_SHIFT**
    and $\epsilon$ be the **THETA_SCALE**
    and $f$ a time $\tau(t,T)$ sensitive function
    with valuation date $t$ and option maturity date $T$
    such that
    $$\dot{f} = \frac{df}{dt} \approx
    \Theta_f(t) = \frac{f(\tau(t,T)+\delta) - f(\tau(t,T))}{\delta/\epsilon}.$$
    """

    def __init__(self, valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None, bump_greeks=None):
        r"""option payoff model

        :param valuation_date: date of option valuation $t$
        :param forward_curve: curve for deriving forward values
        :param volatility_curve: parameter curve of option pricing formulas
        :param day_count: day count function to calculate
            year fraction between dates, e.g. option expiry and valueation date
        :param bump_greeks: **bool** - if **True** Greeks,
            i.e. sensitivities/derivatives, are derived numericaly.
            If **False** analytics functions are used, if given.
            See also |OptionPricingFormula()|.
            (optional; default is **False**)
        """
        self.valuation_date = valuation_date
        r"""date of option valuation $t$"""
        self.forward_curve = forward_curve
        r"""curve for deriving forward values $F(t)$"""
        self.volatility_curve = volatility_curve
        r"""parameter curve of option pricing formulas $\nu(t)$"""
        self.day_count = day_count
        r"""day count function to calculate year fraction between dates $\tau$"""  # noqa 501
        self.bump_greeks = bump_greeks

    def _tsfv(self, date, strike=None):
        details = self.details(date, strike)
        keys = 'time to expiry', 'strike', 'forward', 'volatility'
        return tuple(details.get(k, None) for k in keys)
        # fwd = 0.0
        # if self.forward_curve:
        #     if hasattr(self.forward_curve, 'get_forward_price'):
        #         fwd = self.forward_curve.get_forward_price(date)
        #     elif hasattr(self.forward_curve, 'get_cash_rate'):
        #         fwd = self.forward_curve.get_cash_rate(date)
        #     else:
        #         fwd = self.forward_curve(date)
        #
        # strike = fwd if strike is None else strike
        # vol = self.volatility_curve(date) if self.volatility_curve else 0.0
        #
        # if self.day_count:
        #     time = self.day_count(self.valuation_date, date)
        # elif hasattr(self.volatility_curve, 'day_count'):
        #     time = self.volatility_curve.day_count(self.valuation_date, date)
        # elif hasattr(self.forward_curve, 'day_count'):
        #     time = self.forward_curve.day_count(self.valuation_date, date)
        # else:
        #     time = _default_day_count(self.valuation_date, date)
        #
        # return time, strike, fwd, vol

    def details(self, date, strike=None):
        """model parameter details

        :param date: option expiry date (also fixing date)
        :param strike: option strike value
            (optional; default **None**, i.e. *at-the-money*)
        :return: dict()

        """
        details = {'valuation date': self.valuation_date}
        forward = 0.0
        if self.forward_curve:
            if hasattr(self.forward_curve, 'get_forward_price'):
                forward = self.forward_curve.get_forward_price(date)
            elif hasattr(self.forward_curve, 'get_cash_rate'):
                forward = self.forward_curve.get_cash_rate(date)
            elif isinstance(self.forward_curve, (int, float)):
                forward = float(self.forward_curve)
            else:
                forward = self.forward_curve(date)

            details['fixing date'] = date
            if hasattr(self.forward_curve, 'forward_tenor'):
                details['tenor'] = self.forward_curve.forward_tenor
            details['forward'] = forward
            details['forward-curve-id'] = id(self.forward_curve)

        strike = forward if strike is None else strike
        details['strike'] = strike

        volatility = 0.0
        if self.volatility_curve:
            if hasattr(self.volatility_curve, 'get_terminal_vol'):
                volatility = self.volatility_curve.get_terminal_vol(date)
            elif isinstance(self.volatility_curve, (int, float)):
                volatility = float(self.volatility_curve)
            else:
                volatility = self.volatility_curve(date)
            details['volatility'] = volatility
            details['volatility-curve-id'] = id(self.volatility_curve)

        if self.day_count:
            time = self.day_count(self.valuation_date, date)
        elif hasattr(self.volatility_curve, 'day_count'):
            time = self.volatility_curve.day_count(self.valuation_date, date)
        elif hasattr(self.forward_curve, 'day_count'):
            time = self.forward_curve.day_count(self.valuation_date, date)
        else:
            time = _default_day_count(self.valuation_date, date)
        details['time to expiry'] = time

        details['model-id'] = id(self)
        return details

    def get_call_value(self, date, strike=None):
        r""" value of a call option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $C_K(F(T))=E[\max(F(T)-K, 0)]$

        """
        time, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not time:
            return max(fwd - strike, 0.0)
        return self._call_price(time, strike, fwd, vol)

    def get_put_value(self, date, strike=None):
        r""" value of a put option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $P_K(F(T))=E[\max(K-F(T), 0)]$

        Note $P_K(F(T))$ is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_:
        $$P_K(F(T)) = K - F(T) + C_K(F(T))$$
        """
        time, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not time:
            return max(strike - fwd, 0.0)
        call = self._call_price(time, strike, fwd, vol)
        return strike - fwd + call  # put/call parity

    def get_call_delta(self, date, strike=None):
        r""" delta sensitivity of a call option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{C_K(F)} = \frac{d}{d F} C_K(F)$

        $\Delta_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in unterlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        shift = self.__class__.DELTA_SHIFT
        time, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not time:
            return 0.0 if fwd < strike else 1.0 * scale  # cadlag
        if not self.bump_greeks:
            delta = self._call_delta(time, strike, fwd, vol)
            if delta is not None:
                return delta * scale
        delta = self._call_price(time, strike, fwd + shift, vol)
        delta -= self._call_price(time, strike, fwd, vol)
        delta = delta / shift
        return delta * scale

    def get_put_delta(self, date, strike=None):
        r""" delta sensitivity of a put option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{P_K(F)} = \frac{d}{d F} P_K(F)$

        $\Delta_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in unterlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{P_K(F)} = \Delta_{C_K(F)} - 1$$

        Note, here $1$ is actualy scaled by |OptionPayOffModel.DELTA_SCALE|.

        """
        scale = self.__class__.DELTA_SCALE
        # put/call parity
        return self.get_call_delta(date, strike) - 1.0 * scale

    def get_call_gamma(self, date, strike=None):
        r""" gamma sensitivity of a call option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{C_K(F)} = \frac{d^2}{d F^2} C_K(F)$

        $\Gamma_{C_K(F)}$ is the second derivative
        of $C_K(F)$ in unterlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        shift = self.__class__.DELTA_SHIFT
        time, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks:
            gamma = self._call_gamma(date, strike, fwd, vol)
            if gamma is not None:
                return gamma * (scale ** 2)
        gamma = self._call_price(time, strike, fwd + shift, vol)
        gamma -= 2 * self._call_price(time, strike, fwd, vol)
        gamma += self._call_price(time, strike, fwd - shift, vol)
        gamma *= (scale / shift) ** 2
        return gamma

    def get_put_gamma(self, date, strike=None):
        r""" gamma sensitivity of a put option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{P_K(F)} = \frac{d^2}{d F^2} P_K(F)$

        $\Gamma_{P_K(F)}$ is the second derivative
        of $P_K(F)$ in unterlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{P_K(F)} = \Gamma_{C_K(F)}$$

        """
        return self.get_call_gamma(date, strike)  # put/call parity

    def get_call_vega(self, date, strike=None):
        r""" vega sensitivity of a call option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{C_K(F)} = \frac{d}{d v} C_K(F)$

        $\mathcal{V}_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in volatility parameter direction $v$.

        """
        shift = self.__class__.VEGA_SHIFT
        scale = self.__class__.VEGA_SCALE
        time, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks:
            vega = self._call_vega(time, strike, fwd, vol)
            if vega is not None:
                return vega * scale
        vega = self._call_price(time, strike, fwd, vol + shift)
        vega -= self._call_price(date, strike, fwd, vol)
        vega *= scale / shift
        return vega

    def get_put_vega(self, date, strike=None):
        r""" vega sensitivity of a put option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{P_K(F)} = \frac{d}{d v} P_K(F)$

        $\mathcal{V}_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in volatility parameter direction $v$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\mathcal{V}_{P_K(F)} = V{C_K(F)}$$

        """
        return self.get_call_vega(date, strike)

    def get_call_theta(self, date, strike=None):
        r""" time sensitivity of a call option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{C_K(F)} = \frac{d}{d t} C_K(F)$

        $\Theta_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in time parameter direction, i.e. valuation date $t$.

        """
        shift = self.__class__.THETA_SHIFT
        scale = self.__class__.THETA_SCALE
        time, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks:
            theta = self._call_theta(date, strike, fwd, vol)
            if theta is not None:
                return theta * scale
        theta = self._call_price(time + shift, strike, fwd, vol)
        theta -= self._call_price(time, strike, fwd, vol)
        return theta * scale

    def get_put_theta(self, date, strike=None):
        r""" time sensitivity of a put option

        :param date: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{P_K(F)} = \frac{d}{d t} P_K(F)$

        $\Theta_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in time parameter direction, i.e. valuation date $t$.

        """
        return self.get_call_theta(date, strike)


class BinaryOptionPayOffModel(OptionPayOffModel):
    STRIKE_SHIFT = 0.0001
    """finite difference to calculate binary option payoff as a call spread"""

    def __init__(self, pricing_formula, strike_shift=None,
                 valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None):
        r"""biniary option payoff model (derived by finite differences)

        :param pricing_formula: option pricing formula;
            eithter |OptionPricingFormula()| or |OptionPayOffModel()|
        :param strike_shift: finite difference to
            calculate binary option payoff as a call spread
            (optional: default taken from
            |BinaryOptionPayOffModel.STRIKE_SHIFT|)
        :param valuation_date: date of option valuation $t$
            (optional: default taken from **pricing_formula**)
        :param forward_curve: curve for deriving forward values
            (optional: default taken from **pricing_formula**)
        :param volatility_curve: parameter curve of option pricing formulas
            (optional: default taken from **pricing_formula**)
        :param day_count: day count function to calculate
            year fraction between dates, e.g. option expiry and valueation date
            (optional: default taken from **pricing_formula**)

        Let $\delta$ be the **STRIKE_SHIFT**
        and $f$ a option payoff with strike $K$
        such that the binary payoff is given as
        $$f' = \frac{df}{dK} \approx
        \frac{f(K+\delta/2) - f(K-\delta/2)}{\delta}.$$

        """
        self._inner = pricing_formula
        if isinstance(pricing_formula, OptionPayOffModel):
            valuation_date = valuation_date or pricing_formula.valuation_date
            forward_curve = forward_curve or pricing_formula.forward_curve
            volatility_curve = volatility_curve \
                or pricing_formula.volatility_curve
            day_count = day_count or pricing_formula.day_count
        super().__init__(valuation_date, forward_curve, volatility_curve,
                         day_count, bump_greeks=True)

    def _call_price(self, time, strike, forward, volatility):
        shift = self.__class__.STRIKE_SHIFT
        high_strike = strike + shift / 2
        low_strike = strike - shift / 2
        call = self._inner(time, low_strike, forward, volatility)
        call -= self._inner(time, high_strike, forward, volatility)
        call = call / shift
        return call
