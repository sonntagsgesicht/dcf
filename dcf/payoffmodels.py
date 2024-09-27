# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from .daycount import day_count as _default_day_count, \
    DAYS_IN_YEAR as _DAYS_IN_YEAR

from .optionpricing import Intrinsic, Bachelier, Black76, DisplacedBlack76
from .optionpricing.base import OptionPricingFormula

from .tools.pp import pretty


@pretty
class PayOffModel:
    """base payoff model to derive expected payoff cashflows"""

    def __init__(self,
                 forward_curve,
                 *,
                 valuation_date=None,
                 day_count=None):
        r"""linear payoff model

        :param forward_curve: curve for deriving forward values
        :param valuation_date: date of option valuation $t$
        :param day_count: day count function to calculate
            year fraction between dates, e.g. fixing date and valuation date

        """
        self.valuation_date = valuation_date
        r"""date of option valuation $t$"""
        self.forward_curve = forward_curve
        r"""curve for deriving forward values $F(t)$"""
        self.day_count = day_count
        r"""day count function to calculate year fraction between dates $\tau$"""

    def __call__(self, cashflow_payoff, valuation_date=None):
        _valuation_date = self.valuation_date
        if valuation_date is not None:
            self.valuation_date = valuation_date
        if isinstance(cashflow_payoff, list):
            cls = cashflow_payoff.__class__
            result = cls(cf(model=self) for cf in cashflow_payoff)
        else:
            result = cashflow_payoff(model=self)
        self.valuation_date = _valuation_date
        return result

    def details(self, expiry, *_, **__):
        """model parameter details

        :param expiry: fixing date
        :return: dict()

        """
        details = {'valuation date': self.valuation_date}
        if self.forward_curve:
            details['forward'] = self.forward(expiry)
            details['forward-curve-id'] = id(self.forward_curve)
            if hasattr(self.forward_curve, 'forward_tenor'):
                details['tenor'] = self.forward_curve.forward_tenor
        details['fixing date'] = expiry
        details['time to expiry'] = self.time(expiry)
        day_count = getattr(self.day_count, '__qualname__', self.day_count)
        details['day count'] = str(day_count)

        details['model-id'] = id(self)
        return details

    ### parameter

    def time(self, expiry):
        if self.day_count:
            time = self.day_count(self.valuation_date, expiry)
        elif hasattr(self.forward_curve, 'day_count'):
            time = self.forward_curve.day_count(self.valuation_date, expiry)
        else:
            time = _default_day_count(self.valuation_date, expiry)
        return time

    def forward(self, expiry):
        if callable(self.forward_curve):
            return self.forward_curve(expiry)
        return self.forward_curve


class OptionPayOffModel(PayOffModel):
    """base option payoff model to derive expected payoff cashflows"""
    BINARY_SHIFT = 0.0001
    r"""finite difference to calculate numerical binary option value
    """
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

    @classmethod
    def intrinsic(cls, forward_curve, volatility_curve=None, *,
                  valuation_date=None, day_count=None,
                  bump_greeks: bool=False, bump_binary: bool=False):
        option_pricing_formula = Intrinsic()
        return cls(forward_curve, option_pricing_formula,
                   volatility_curve=volatility_curve,
                   valuation_date=valuation_date, day_count=day_count,
                   bump_greeks=bump_greeks, bump_binary=bump_binary)

    @classmethod
    def bachelier(cls, forward_curve, volatility_curve=None, *,
                  valuation_date=None, day_count=None,
                  bump_greeks: bool=False, bump_binary: bool=False):
        option_pricing_formula = Bachelier()
        return cls(forward_curve, option_pricing_formula,
                   volatility_curve=volatility_curve,
                   valuation_date=valuation_date, day_count=day_count,
                   bump_greeks=bump_greeks, bump_binary=bump_binary)

    @classmethod
    def black76(cls, forward_curve, volatility_curve=None, *,
                valuation_date=None, day_count=None,
                bump_greeks: bool=False, bump_binary: bool=False):
        option_pricing_formula = Black76()
        return cls(forward_curve, option_pricing_formula,
                   volatility_curve=volatility_curve,
                   valuation_date=valuation_date, day_count=day_count,
                   bump_greeks=bump_greeks, bump_binary=bump_binary)

    @classmethod
    def displaced_black76(cls, forward_curve, volatility_curve=None, *,
                          displacement=0.0,
                          valuation_date=None, day_count=None,
                          bump_greeks: bool=False, bump_binary: bool=False):
        option_pricing_formula = DisplacedBlack76(displacement=displacement)
        return cls(forward_curve, option_pricing_formula,
                   volatility_curve=volatility_curve,
                   valuation_date=valuation_date, day_count=day_count,
                   bump_greeks=bump_greeks, bump_binary=bump_binary)

    def __init__(self, forward_curve,
                 option_pricing_formula: OptionPricingFormula,
                 volatility_curve=None,
                 *,
                 valuation_date=None,
                 day_count=None,
                 bump_greeks: bool=False,
                 bump_binary: bool=False):
        r"""option payoff model

        :param forward_curve: curve for deriving forward values
        :param option_pricing_formula: option pricing formulas
        :param volatility_curve: parameter curve of option pricing formulas
        :param valuation_date: date of option valuation $t$
        :param day_count: day count function to calculate
            year fraction between dates, e.g. option expiry and valuation date
        :param bump_greeks: **bool** - if **True** Greeks,
            i.e. sensitivities/derivatives, are derived numerically.
            If **False** analytics functions are used, if given.
            See also |OptionPricingFormula()|.
            (optional; default is **False**)
        :param bump_binary: **bool** - if **True** Binary option payoffs
            i.e. digital option, are derived numerically via call/ put spreads.
            If **False** analytics functions are used, if given.
            See also |OptionPricingFormula()|.
            (optional; default is **False**)
        """
        super().__init__(
            forward_curve, valuation_date=valuation_date, day_count=day_count)
        self.option_pricing_formula = option_pricing_formula
        r"""option pricing formula
            either simple pricing function or |OptionPricingFormula|. 
            The later provides attributes for Greeks like `delta` etc. """
        self.volatility_curve = volatility_curve
        r"""parameter curve of option pricing formulas $\nu(t)$"""
        self.bump_greeks = bump_greeks
        self.bump_binary = bump_binary

    def details(self, expiry, strike=None, *_, **__):
        """model parameter details

        :param expiry: option expiry date (also fixing date)
        :param strike: option strike value
            (optional; default **None**, i.e. *at-the-money*)
        :return: dict()

        """
        details = super().details(expiry)
        if self.volatility_curve:
            details['volatility'] = self.volatility(expiry, strike)
            details['volatility-curve-id'] = id(self.volatility_curve)
        if strike is None:
            strike = 'atm'  # self.forward(expiry)
        details['strike'] = strike
        opf = self.option_pricing_formula.__class__
        details['formula'] = getattr(opf, '__name__', str(opf))
        return details

    ### parameter (doesn't make use of 'option_pricing_formula')

    def volatility(self, expiry, strike=None, forward=None):
        if callable(self.volatility_curve):
            volatility = self.volatility_curve(expiry)
            if callable(volatility):
                volatility = volatility(strike, forward)
            return volatility
        return self.volatility_curve

    ### binding between model formulas and parameters

    def _tsfv(self, expiry, strike=None):
        time = self.time(expiry) or 0.0
        fwd = self.forward_curve(expiry) or 0.0
        vol = self.volatility(expiry, strike, fwd) or 0.0
        strike = fwd if strike is None else strike  # atm
        return float(time), float(strike), float(fwd), float(vol)

    ### vanilla (uses only '_tsfv', 'option_pricing_formula' and 'bump_...')

    def call_value(self, expiry, strike=None):
        r""" value of a call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $C_K(F(T))=E[\max(F(T)-K, 0)]$

        """
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return max(fwd - strike, 0.0)
        return self.option_pricing_formula(time, strike, fwd, vol)

    def put_value(self, expiry, strike=None):
        r""" value of a put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $P_K(F(T))=E[\max(K-F(T), 0)]$

        Note $P_K(F(T))$ is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_:
        $$P_K(F(T)) = K - F(T) + C_K(F(T))$$
        """
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return max(strike - fwd, 0.0)
        call = self.option_pricing_formula(time, strike, fwd, vol)
        return strike - fwd + call  # put/call parity

    def call_delta(self, expiry, strike=None):
        r""" delta sensitivity of a call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{C_K(F)} = \frac{d}{d F} C_K(F)$

        $\Delta_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in unterlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0 if fwd < strike else 1.0 * scale  # cadlag
        if not self.bump_greeks and hasattr(self.option_pricing_formula, 'delta'):
            delta = self.option_pricing_formula.delta(time, strike, fwd, vol)
            if delta is not None:
                return delta * scale
        shift = self.__class__.DELTA_SHIFT
        delta = self.option_pricing_formula(time, strike, fwd + shift, vol)
        delta -= self.option_pricing_formula(time, strike, fwd, vol)
        delta = delta / shift
        return delta * scale

    def put_delta(self, expiry, strike=None):
        r""" delta sensitivity of a put option

        :param expiry: expiry date $T$
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
        return self.call_delta(expiry, strike) - 1.0 * scale

    def call_gamma(self, expiry, strike=None):
        r""" gamma sensitivity of a call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{C_K(F)} = \frac{d^2}{d F^2} C_K(F)$

        $\Gamma_{C_K(F)}$ is the second derivative
        of $C_K(F)$ in unterlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks and hasattr(self.option_pricing_formula, 'gamma'):
            gamma = self.option_pricing_formula.gamma(time, strike, fwd, vol)
            if gamma is not None:
                return gamma * (scale ** 2)
        shift = self.__class__.DELTA_SHIFT
        gamma = self.option_pricing_formula(time, strike, fwd + shift, vol)
        gamma -= 2 * self.option_pricing_formula(time, strike, fwd, vol)
        gamma += self.option_pricing_formula(time, strike, fwd - shift, vol)
        gamma *= (scale / shift) ** 2
        return gamma

    def put_gamma(self, expiry, strike=None):
        r""" gamma sensitivity of a put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{P_K(F)} = \frac{d^2}{d F^2} P_K(F)$

        $\Gamma_{P_K(F)}$ is the second derivative
        of $P_K(F)$ in unterlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{P_K(F)} = \Gamma_{C_K(F)}$$

        """
        return self.call_gamma(expiry, strike)  # put/call parity

    def call_vega(self, expiry, strike=None):
        r""" vega sensitivity of a call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{C_K(F)} = \frac{d}{d v} C_K(F)$

        $\mathcal{V}_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in volatility parameter direction $v$.

        """
        scale = self.__class__.VEGA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0
        if (not self.bump_greeks and
                hasattr(self.option_pricing_formula, 'vega')):
            vega = self.option_pricing_formula.vega(time, strike, fwd, vol)
            if vega is not None:
                return vega * scale
        shift = self.__class__.VEGA_SHIFT
        vega = self.option_pricing_formula(time, strike, fwd, vol + shift)
        vega -= self.option_pricing_formula(expiry, strike, fwd, vol)
        vega *= scale / shift
        return vega

    def put_vega(self, expiry, strike=None):
        r""" vega sensitivity of a put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{P_K(F)} = \frac{d}{d v} P_K(F)$

        $\mathcal{V}_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in volatility parameter direction $v$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\mathcal{V}_{P_K(F)} = \mathcal{V}_{C_K(F)}$$

        """
        return self.call_vega(expiry, strike)

    def call_theta(self, expiry, strike=None):
        r""" time sensitivity of a call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{C_K(F)} = \frac{d}{d t} C_K(F)$

        $\Theta_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in time parameter direction, i.e. valuation date $t$.

        """
        scale = self.__class__.THETA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks and hasattr(self.option_pricing_formula, 'theta'):
            theta = self.option_pricing_formula.theta(expiry, strike, fwd, vol)
            if theta is not None:
                return theta * scale
        shift = self.__class__.THETA_SHIFT
        theta = self.option_pricing_formula(time + shift, strike, fwd, vol)
        theta -= self.option_pricing_formula(time, strike, fwd, vol)
        return theta * scale

    def put_theta(self, expiry, strike=None):
        r""" time sensitivity of a put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{P_K(F)} = \frac{d}{d t} P_K(F)$

        $\Theta_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in time parameter direction, i.e. valuation date $t$.

        """
        return self.call_theta(expiry, strike)

    ### binary (requires only '_tsfv' and 'option_pricing_formula')

    def binary_call(self, expiry, strike=None):
        r""" value of a binary call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\delta C_K(F(T))=E[ ]$

        """
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0 if fwd <= strike else 1.0
        if not self.bump_binary and hasattr(self.option_pricing_formula, 'binary'):
            call = self.option_pricing_formula.binary(time, strike, fwd, vol)
            if call is not None:
                return call
        shift = self.__class__.BINARY_SHIFT
        call = self.option_pricing_formula(time, strike + shift / 2, fwd, vol)
        call -= self.option_pricing_formula(time, strike - shift / 2, fwd, vol)
        call = call + shift
        return call

    def binary_put(self, expiry, strike=None):
        r""" value of a put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\delta P_K(F(T))=E[ ]$

        Note $P_K(F(T))$ is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_:
        $$\delta P_K(F(T)) = 1.0 - \delta C_K(F(T))$$

        """
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0 if strike < fwd else 1.0
        call = self.option_pricing_formula.binary(time, strike, fwd, vol)
        return 1.0 - call  # put/call parity

    def binary_call_delta(self, expiry, strike=None):
        r""" delta sensitivity of a binary call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{ \delta C_K(F)} = \frac{d}{d F} \delta C_K(F)$

        $\Delta_{ \delta C_K(F)}$ is the first derivative
        of $\delta C_K(F)$ in underlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0 if fwd < strike else 1.0 * scale  # cadlag
        if not self.bump_greeks and \
                hasattr(self.option_pricing_formula, 'binary_delta'):
            delta = self.option_pricing_formula.binary_delta(time, strike, fwd, vol)
            if delta is not None:
                return delta * scale
        shift = self.__class__.DELTA_SHIFT
        delta = self.option_pricing_formula.binary(time, strike, fwd + shift, vol)
        delta -= self.option_pricing_formula.binary(time, strike, fwd, vol)
        delta = delta / shift
        return delta * scale

    def binary_put_delta(self, expiry, strike=None):
        r""" delta sensitivity of a binary put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{ \delta P_K(F)} = \frac{d}{d F} \delta P_K(F)$

        $\Delta_{ \delta P_K(F)}$ is the first derivative
        of $P_K(F)$ in unterlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{P_K(F)} = \Delta_{ \delta C_K(F)} - 1$$

        Note, here $1$ is actually scaled by |OptionPayOffModel.DELTA_SCALE|.

        """
        scale = self.__class__.DELTA_SCALE
        # put/call parity
        return self.binary_call_delta(expiry, strike) - 1.0 * scale

    def binary_call_gamma(self, expiry, strike=None):
        r""" gamma sensitivity of a binary call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{ \delta C_K(F)} = \frac{d^2}{d F^2} \delta C_K(F)$

        $\Gamma_{ \delta C_K(F)}$ is the second derivative
        of $ \delta C_K(F)$ in underlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks and \
                hasattr(self.option_pricing_formula, 'binary_gamma'):
            gamma = self.option_pricing_formula.gamma(time, strike, fwd, vol)
            if gamma is not None:
                return gamma * (scale ** 2)
        shift = self.__class__.DELTA_SHIFT
        gamma = self.option_pricing_formula.binary(time, strike, fwd + shift, vol)
        gamma -= 2 * self.option_pricing_formula.binary(time, strike, fwd, vol)
        gamma += self.option_pricing_formula.binary(time, strike, fwd - shift, vol)
        gamma *= (scale / shift) ** 2
        return gamma

    def binary_put_gamma(self, expiry, strike=None):
        r""" gamma sensitivity of a binary put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{ \delta P_K(F)} = \frac{d^2}{d F^2} \delta P_K(F)$

        $\Gamma_{ \delta P_K(F)}$ is the second derivative
        of $ \delta P_K(F)$ in unterlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{ \delta P_K(F)} = \Gamma_{ \delta C_K(F)}$$

        """
        return self.binary_call_gamma(expiry, strike)  # put/call parity

    def binary_call_vega(self, expiry, strike=None):
        r""" vega sensitivity of a binary call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{ \delta C_K(F)} = \frac{d}{d v} \delta C_K(F)$

        $\mathcal{V}_{ \delta C_K(F)}$ is the first derivative
        of $ \delta C_K(F)$ in volatility parameter direction $v$.

        """
        scale = self.__class__.VEGA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks and \
                hasattr(self.option_pricing_formula, 'binary_vega'):
            vega = self.option_pricing_formula.vega(time, strike, fwd, vol)
            if vega is not None:
                return vega * scale
        shift = self.__class__.VEGA_SHIFT
        vega = self.option_pricing_formula.binary(time, strike, fwd, vol + shift)
        vega -= self.option_pricing_formula.binary(expiry, strike, fwd, vol)
        vega *= scale / shift
        return vega

    def binary_put_vega(self, expiry, strike=None):
        r""" vega sensitivity of a binary put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{ \delta P_K(F)} = \frac{d}{d v} \delta P_K(F)$

        $\mathcal{V}_{ \delta P_K(F)}$ is the first derivative
        of $\delta P_K(F)$ in volatility parameter direction $v$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\mathcal{V}_{ \delta P_K(F)} = \mathcal{V}_{ \delta C_K(F)}$$

        """
        return self.binary_call_vega(expiry, strike)

    def binary_call_theta(self, expiry, strike=None):
        r""" time sensitivity of a binary call option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{ \delta C_K(F)} = \frac{d}{d t} \delta C_K(F)$

        $\Theta_{ \delta C_K(F)}$ is the first derivative
        of $\delta C_K(F)$ in time parameter direction,
        i.e. valuation date $t$.

        """
        scale = self.__class__.THETA_SCALE
        time, strike, fwd, vol = self._tsfv(expiry, strike)
        if not vol or not time:
            return 0.0
        if not self.bump_greeks and \
                hasattr(self.option_pricing_formula, 'binary_theta'):
            theta = self.option_pricing_formula.theta(expiry, strike, fwd, vol)
            if theta is not None:
                return theta * scale
        shift = self.__class__.THETA_SHIFT
        theta = self.option_pricing_formula.binary(time + shift, strike, fwd, vol)
        theta -= self.option_pricing_formula.binary(time, strike, fwd, vol)
        return theta * scale

    def binary_put_theta(self, expiry, strike=None):
        r""" time sensitivity of a binary put option

        :param expiry: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{ \delta P_K(F)} = \frac{d}{d t} \delta P_K(F)$

        $\Theta_{ \delta P_K(F)}$ is the first derivative
        of $\delta P_K(F)$ in time parameter direction,
        i.e. valuation date $t$.

        """
        return self.binary_call_theta(expiry, strike)
