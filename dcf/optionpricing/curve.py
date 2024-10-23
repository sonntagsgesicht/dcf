# -*- coding: utf-8 -*-
# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from typing import Callable

from prettyclass import prettyclass

from ..daycount import day_count as _default_day_count, DateType
from ..details import Details
from .base import OptionPricingFormula
from .intrinsic import Intrinsic
from .bachelier import Bachelier
from .black76 import Black76, DisplacedBlack76


@prettyclass(init=False)
class OptionPricingCurve:
    """model to derive expected option payoff cashflows"""
    if True:
        DELTA_SHIFT = 0.0001
        r"""finite difference to calculate numerical delta sensitivities"""
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
        THETA_SHIFT = 1 / _default_day_count.DAYS_IN_YEAR
        r"""finite difference to calculate numerical theta sensitivities
        usually one day (1/365.25)"""
        THETA_SCALE = 1 / _default_day_count.DAYS_IN_YEAR
        r"""factor to express numerical theta sensitivities
        usually one day (1/365.25)

        Let $\delta$ be the **THETA_SHIFT**
        and $\epsilon$ be the **THETA_SCALE**
        and $f$ a tau $\tau(t,T)$ sensitive function
        with valuation date $t$ and option maturity date $T$
        such that
        $$\dot{f} = \frac{df}{dt} \approx
        \Theta_f(t) = \frac{f(\tau(t,T)+\delta)
        - f(\tau(t,T))}{\delta/\epsilon}.$$
        """

    @classmethod
    def intrinsic(cls, curve, volatility=None, *, day_count=None, origin=None):
        return cls(curve, formula=Intrinsic(),
                   day_count=day_count, origin=origin)

    @classmethod
    def bachelier(cls, curve, volatility=None, *, day_count=None, origin=None):
        return cls(curve, formula=Bachelier(), volatility=volatility,
                   day_count=day_count, origin=origin)

    @classmethod
    def black76(cls, curve, volatility=None, *, day_count=None, origin=None):
        return cls(curve, formula=Black76(), volatility=volatility,
                   day_count=day_count, origin=origin)

    @classmethod
    def displaced_black76(cls, curve, volatility=None,
                          *, displacement=0.0, day_count=None, origin=None):
        formula = DisplacedBlack76(displacement=displacement)
        return cls(curve, formula=formula, volatility=volatility,
                   day_count=day_count, origin=origin)

    def __init__(self, curve: Callable, *,
                 formula: OptionPricingFormula = None,
                 volatility: Callable = None,
                 day_count: Callable = None,
                 origin: DateType = None,
                 bump_greeks: bool = False,
                 bump_binary: float | bool | None = 0.0001):
        """curve extension for option pricing

        :param curve: forward curve to derives forward values
        :param formula: option pricing formula
            callable which must provide float consuming signature
            **formula(tau, strike, forward, volatility)**
            here **tau** is the time to expiry in year fractions
        :param volatility: volatility curve
        :param day_count: day count convention to calculate year fractions
            (optional)
        :param origin: curve origin to calculate year fractions
            (optional)
        :param bump_greeks: **bool** - if **True** Greeks,
            i.e. sensitivities/derivatives, are derived numerically.
            If **False** analytics functions are used, if given.
            See also |OptionPricingFormula()|.
            (optional; default is **False**)
        :param bump_binary: finite difference
            to calculate Binary option payoffs numerically
            i.e. digital options are derived numerically via call/ put spreads.
            If **False**, **None** or **0.0** analytics functions are used,
            e.g. **formula.binary_call** if present.
            See also |OptionPricingFormula()|.
            (optional; default is 0.0001)
        """
        self.curve = curve
        r"""curve for deriving forward values $F(t)$"""
        self.volatility = volatility
        self.formula = formula
        self.day_count = day_count
        self.origin = origin
        self.bump_binary = bump_binary
        self.bump_greeks = bump_greeks

    def __call__(self, x, y=None):
        return self.forward(x, y)

    def forward(self, x, y=None):
        if callable(self.curve):
            if y is None:
                return self.curve(x)
            return self.curve(x, y)
        return self.curve

    def details(self, x, y=None, *, strike=None, **__):
        """model parameter details

        :param x: option valuation date
        :param y: option expiry date (also fixing date)
            (optional; if not given **x** will be expiry date)
        :param strike: option strike value
            (optional; default **None**, i.e. *at-the-money*)
        :return: dict()

        """
        tau, _strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if y is None:
            x, y = self.origin, x
        formula_cls = self.formula.__class__

        details = {
            'valuation date': x,
            'expiry date': y,
            'tau to expiry': tau,
            'strike': _strike,
            'forward': fwd,
            'volatility': vol,
            'option model': getattr(formula_cls, '__name__', str(formula_cls)),
            'forward-curve-id': id(self.curve),
            'volatility-curve-id': id(self.volatility),
            'option-pricer-id': id(self)
        }
        if strike is None:
            details.pop('strike', None)
        if self.volatility:
            details.pop('volatility', None)
            details.pop('volatility-curve-id', None)

        return Details(details)

    def _tsfv(self, x, y=None, *, strike=None):
        """tau, strike, forward, volatility

        :param x: valuation date
        :param y: expiry date
        :param strike: strike
        :return: tuple
        """
        if y is None:
            x, y = self.origin, x
        fwd = self(y)
        if strike is None:
            strike = fwd
        vol = self.volatility
        if callable(vol):
            # assume terminal vol curve
            vol = vol(y)
        if callable(vol):
            # for vol smile models
            vol = vol(strike, fwd)
        dc = self.day_count or _default_day_count
        tau = dc(x, y)
        return tau, strike, fwd, vol

    # --- vanilla (uses only '_tsfv', 'formula' and 'bump_...')

    def call(self, x, y=None, *, strike=None):
        r""" value of a call option

        :param x: valuation date $t$
        :param y: expiry date $T$
         :param strike: option strike price $K$ of underlying $F(T)$
         :return: $C_K(F(T))=E[\max(F(T)-K, 0)]$

         """
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if self.formula is None or not vol or not tau:
            return max(0.0, fwd - strike)
        return self.formula(tau, strike, fwd, vol)

    def put(self, x, y=None, *, strike=None):
        r""" value of a put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $P_K(F(T))=E[\max(K-F(T), 0)]$

        Note $P_K(F(T))$ is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_:
        $$P_K(F(T)) = K - F(T) + C_K(F(T))$$

        """
        fwd = self(x, y)
        call = self.call(x, y, strike=strike)
        if strike is None:
            strike = fwd
        return strike - fwd + call  # put/call parity

    def call_delta(self, x, y=None, *, strike=None):
        r""" delta sensitivity of a call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{C_K(F)} = \frac{d}{d F} C_K(F)$

        $\Delta_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in unterlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0 if fwd < strike else 1.0 * scale  # cadlag
        if not self.bump_greeks \
                and hasattr(self.formula, 'delta'):
            delta = self.formula.delta(tau, strike, fwd, vol)
            if delta is not None:
                return delta * scale
        shift = self.__class__.DELTA_SHIFT
        delta = self.formula(tau, strike, fwd + shift, vol)
        delta -= self.formula(tau, strike, fwd, vol)
        delta = delta / shift
        return delta * scale

    def put_delta(self, x, y=None, *, strike=None):
        r""" delta sensitivity of a put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{P_K(F)} = \frac{d}{d F} P_K(F)$

        $\Delta_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in underlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{P_K(F)} = \Delta_{C_K(F)} - 1$$

        Note, here $1$ is actualy scaled by |OptionPayOffModel.DELTA_SCALE|.

        """
        scale = self.__class__.DELTA_SCALE
        # put/call parity
        return self.call_delta(x, y, strike=strike) - 1.0 * scale

    def call_gamma(self, x, y=None, *, strike=None):
        r""" gamma sensitivity of a call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{C_K(F)} = \frac{d^2}{d F^2} C_K(F)$

        $\Gamma_{C_K(F)}$ is the second derivative
        of $C_K(F)$ in unterlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks \
                and hasattr(self.formula, 'gamma'):
            gamma = self.formula.gamma(tau, strike, fwd, vol)
            if gamma is not None:
                return gamma * (scale ** 2)
        shift = self.__class__.DELTA_SHIFT
        gamma = self.formula(tau, strike, fwd + shift, vol)
        gamma -= 2 * self.formula(tau, strike, fwd, vol)
        gamma += self.formula(tau, strike, fwd - shift, vol)
        gamma *= (scale / shift) ** 2
        return gamma

    def put_gamma(self, x, y=None, *, strike=None):
        r""" gamma sensitivity of a put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{P_K(F)} = \frac{d^2}{d F^2} P_K(F)$

        $\Gamma_{P_K(F)}$ is the second derivative
        of $P_K(F)$ in unterlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{P_K(F)} = \Gamma_{C_K(F)}$$

        """
        return self.call_gamma(x, y, strike=strike)  # put/call parity

    def call_vega(self, x, y=None, *, strike=None):
        r""" vega sensitivity of a call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{C_K(F)} = \frac{d}{d v} C_K(F)$

        $\mathcal{V}_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in volatility parameter direction $v$.

        """
        scale = self.__class__.VEGA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0
        if (not self.bump_greeks and
                hasattr(self.formula, 'vega')):
            vega = self.formula.vega(tau, strike, fwd, vol)
            if vega is not None:
                return vega * scale
        shift = self.__class__.VEGA_SHIFT
        vega = self.formula(tau, strike, fwd, vol + shift)
        vega -= self.formula(tau, strike, fwd, vol)
        vega *= scale / shift
        return vega

    def put_vega(self, x, y=None, *, strike=None):
        r""" vega sensitivity of a put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{P_K(F)} = \frac{d}{d v} P_K(F)$

        $\mathcal{V}_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in volatility parameter direction $v$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\mathcal{V}_{P_K(F)} = \mathcal{V}_{C_K(F)}$$

        """
        return self.call_vega(x, y, strike=strike)

    def call_theta(self, x, y=None, *, strike=None):
        r""" tau sensitivity of a call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{C_K(F)} = \frac{d}{d t} C_K(F)$

        $\Theta_{C_K(F)}$ is the first derivative
        of $C_K(F)$ in tau parameter direction, i.e. valuation date $t$.

        """
        scale = self.__class__.THETA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks \
                and hasattr(self.formula, 'theta'):
            theta = self.formula.theta(tau, strike, fwd, vol)
            if theta is not None:
                return theta * scale
        shift = self.__class__.THETA_SHIFT
        theta = self.formula(tau + shift, strike, fwd, vol)
        theta -= self.formula(tau, strike, fwd, vol)
        return theta * scale

    def put_theta(self, x, y=None, *, strike=None):
        r""" tau sensitivity of a put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{P_K(F)} = \frac{d}{d t} P_K(F)$

        $\Theta_{P_K(F)}$ is the first derivative
        of $P_K(F)$ in tau parameter direction, i.e. valuation date $t$.

        """
        return self.call_theta(x, y, strike=strike)

    # --- binary (requires only '_tsfv' and 'option_...' and 'bump_...')

    def binary_call(self, x, y=None, *, strike=None):
        r""" value of a binary call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\delta C_K(F(T))=E[ ]$

        """
        if self.bump_binary is None:
            tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
            if self.formula is None or vol is None or not tau:
                return 1.0 if strike < fwd else 0.0
            call = self.formula.binary(tau, strike, fwd, vol)
            if call is not None:
                return call

        shift = self.bump_binary or 0.0001
        strike = self(x, y) if strike is None else strike
        call_spread = self.call(x, y, strike=strike + shift / 2)
        call_spread -= self.call(x, y, strike=strike - shift / 2)
        return call_spread / shift

    def binary_put(self, x, y=None, *, strike=None):
        r""" value of a put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\delta P_K(F(T))=E[ ]$

        Note $P_K(F(T))$ is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_:
        $$\delta P_K(F(T)) = 1.0 - \delta C_K(F(T))$$

        """
        call = self.binary_call(x, y, strike=strike)
        return 1.0 - call  # put/call parity

    def binary_call_delta(self, x, y=None, *, strike=None):
        r""" delta sensitivity of a binary call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Delta_{ \delta C_K(F)} = \frac{d}{d F} \delta C_K(F)$

        $\Delta_{ \delta C_K(F)}$ is the first derivative
        of $\delta C_K(F)$ in underlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0 if fwd < strike else 1.0 * scale  # cadlag
        if not self.bump_greeks and \
                hasattr(self.formula, 'binary_delta'):
            delta = self.formula.binary_delta(
                tau, strike, fwd, vol)
            if delta is not None:
                return delta * scale
        shift = self.__class__.DELTA_SHIFT
        delta = \
            self.formula.binary(tau, strike, fwd + shift, vol)
        delta -= self.formula.binary(tau, strike, fwd, vol)
        delta = delta / shift
        return delta * scale

    def binary_put_delta(self, x, y=None, *, strike=None):
        r""" delta sensitivity of a binary put option

        :param x: valuation date $t$
        :param y: expiry date $T$
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
        return self.binary_call_delta(x, y, strike=strike) - 1.0 * scale

    def binary_call_gamma(self, x, y=None, *, strike=None):
        r""" gamma sensitivity of a binary call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{ \delta C_K(F)} = \frac{d^2}{d F^2} \delta C_K(F)$

        $\Gamma_{ \delta C_K(F)}$ is the second derivative
        of $ \delta C_K(F)$ in underlying direction $F$.

        """
        scale = self.__class__.DELTA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks and \
                hasattr(self.formula, 'binary_gamma'):
            gamma = self.formula.gamma(tau, strike, fwd, vol)
            if gamma is not None:
                return gamma * (scale ** 2)
        shift = self.__class__.DELTA_SHIFT
        gamma = \
            self.formula.binary(tau, strike, fwd + shift, vol)
        gamma -= 2 * self.formula.binary(tau, strike, fwd, vol)
        gamma += \
            self.formula.binary(tau, strike, fwd - shift, vol)
        gamma *= (scale / shift) ** 2
        return gamma

    def binary_put_gamma(self, x, y=None, *, strike=None):
        r""" gamma sensitivity of a binary put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Gamma_{ \delta P_K(F)} = \frac{d^2}{d F^2} \delta P_K(F)$

        $\Gamma_{ \delta P_K(F)}$ is the second derivative
        of $ \delta P_K(F)$ in unterlying direction $F$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\Gamma_{ \delta P_K(F)} = \Gamma_{ \delta C_K(F)}$$

        """
        return self.binary_call_gamma(x, y, strike=strike)  # put/call parity

    def binary_call_vega(self, x, y=None, *, strike=None):
        r""" vega sensitivity of a binary call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{ \delta C_K(F)} = \frac{d}{d v} \delta C_K(F)$

        $\mathcal{V}_{ \delta C_K(F)}$ is the first derivative
        of $ \delta C_K(F)$ in volatility parameter direction $v$.

        """
        scale = self.__class__.VEGA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks and \
                hasattr(self.formula, 'binary_vega'):
            vega = self.formula.vega(tau, strike, fwd, vol)
            if vega is not None:
                return vega * scale
        shift = self.__class__.VEGA_SHIFT
        vega = \
            self.formula.binary(tau, strike, fwd, vol + shift)
        vega -= self.formula.binary(tau, strike, fwd, vol)
        vega *= scale / shift
        return vega

    def binary_put_vega(self, x, y=None, *, strike=None):
        r""" vega sensitivity of a binary put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\mathcal{V}_{ \delta P_K(F)} = \frac{d}{d v} \delta P_K(F)$

        $\mathcal{V}_{ \delta P_K(F)}$ is the first derivative
        of $\delta P_K(F)$ in volatility parameter direction $v$
        and is derived by
        `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_,
        too:
        $$\mathcal{V}_{ \delta P_K(F)} = \mathcal{V}_{ \delta C_K(F)}$$

        """
        return self.binary_call_vega(x, y, strike=strike)

    def binary_call_theta(self, x, y=None, *, strike=None):
        r""" tau sensitivity of a binary call option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{ \delta C_K(F)} = \frac{d}{d t} \delta C_K(F)$

        $\Theta_{ \delta C_K(F)}$ is the first derivative
        of $\delta C_K(F)$ in tau parameter direction,
        i.e. valuation date $t$.

        """
        scale = self.__class__.THETA_SCALE
        tau, strike, fwd, vol = self._tsfv(x, y, strike=strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks and \
                hasattr(self.formula, 'binary_theta'):
            theta = self.formula.theta(tau, strike, fwd, vol)
            if theta is not None:
                return theta * scale
        shift = self.__class__.THETA_SHIFT
        theta = \
            self.formula.binary(tau + shift, strike, fwd, vol)
        theta -= self.formula.binary(tau, strike, fwd, vol)
        return theta * scale

    def binary_put_theta(self, x, y=None, *, strike=None):
        r""" tau sensitivity of a binary put option

        :param x: valuation date $t$
        :param y: expiry date $T$
        :param strike: option strike price $K$ of underlying $F$
        :return: $\Theta_{ \delta P_K(F)} = \frac{d}{d t} \delta P_K(F)$

        $\Theta_{ \delta P_K(F)}$ is the first derivative
        of $\delta P_K(F)$ in tau parameter direction,
        i.e. valuation date $t$.

        """
        return self.binary_call_theta(x, y, strike=strike)
