# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from abc import ABC
from ..daycount import day_count as _default_day_count


class OptionPricingFormula(ABC):

    def __call__(self, tau, strike, forward, volatility):
        return self._call_price(tau, strike, forward, volatility)

    def _call_price(self, tau, strike, forward, volatility):
        raise NotImplementedError()

    def _call_delta(self, tau, strike, forward, volatility):
        return

    def _call_gamma(self, tau, strike, forward, volatility):
        return

    def _call_vega(self, tau, strike, forward, volatility):
        return

    def _call_theta(self, tau, strike, forward, volatility):
        return


class OptionPayOffModel(OptionPricingFormula, ABC):
    DAY_COUNT = _default_day_count
    """ default day count function for rate period calculation

        **DAY_COUNT** is a static function
        and can be set on class level, e.g.

        :code:`RateCashFlowList.DAY_COUNT = (lambda s, e : e - s)`

        :param start: period start date
        :param end: period end date
        :returns: year fraction for **start** to **end** as a float

    """

    DELTA_SHIFT = 0.0001
    DELTA_SCALE = 0.0001
    VEGA_SHIFT = 0.01
    VEGA_SCALE = 0.01
    THETA_SHIFT = 1/365.25
    THETA_SCALE = 1/365.25

    def __init__(self, valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None, bump_greeks=None):
        self.valuation_date = valuation_date
        self.forward_curve = forward_curve
        self.volatility_curve = volatility_curve
        self.day_count = day_count
        self.bump_greeks = bump_greeks

    def _tsfv(self, date, strike=None):
        fwd = self.forward_curve(date) if self.forward_curve else 0.0
        strike = fwd if strike is None else strike
        vol = self.volatility_curve(date) if self.volatility_curve else 0.0

        if self.day_count:
            tau = self.day_count(self.valuation_date, date)
        elif self.volatility_curve:
            tau = self.volatility_curve.day_count(self.valuation_date, date)
        elif self.forward_curve:
            tau = self.forward_curve.day_count(self.valuation_date, date)
        else:
            tau = self.__class__.DAY_COUNT(self.valuation_date, date)

        return tau, strike, fwd, vol

    def get_call_value(self, date, strike=None):
        tau, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not tau:
            return max(fwd - strike, 0.0)
        return self._call_price(tau, strike, fwd, vol)

    def get_put_value(self, date, strike=None):
        tau, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not tau:
            return max(strike - fwd, 0.0)
        call = self._call_price(tau, strike, fwd, vol)
        return strike - fwd + call  # put/call parity

    def get_call_delta(self, date, strike=None):
        scale = self.__class__.DELTA_SCALE
        shift = self.__class__.DELTA_SHIFT
        tau, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not tau:
            return 0.0 if fwd < strike else 1.0 * scale  # cadlag
        if not self.bump_greeks:
            delta = self._call_delta(tau, strike, fwd, vol)
            if delta is not None:
                return delta * scale
        delta = self._call_price(tau, strike, fwd + shift, vol)
        delta -= self._call_price(tau, strike, fwd, vol)
        delta = delta / shift
        return delta * scale

    def get_put_delta(self, date, strike=None):
        scale = self.__class__.DELTA_SCALE
        # put/call parity
        return self.get_call_delta(date, strike) - 1.0 * scale

    def get_call_gamma(self, date, strike=None):
        scale = self.__class__.DELTA_SCALE
        shift = self.__class__.DELTA_SHIFT
        tau, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks:
            gamma = self._call_gamma(date, strike, fwd, vol)
            if gamma is not None:
                return gamma * (scale**2)
        gamma = self._call_price(tau, strike, fwd + shift, vol)
        gamma -= 2 * self._call_price(tau, strike, fwd, vol)
        gamma += self._call_price(tau, strike, fwd - shift, vol)
        gamma *= (scale / shift) ** 2
        return gamma

    def get_put_gamma(self, date, strike=None):
        return self.get_call_gamma(date, strike)  # put/call parity

    def get_call_vega(self, date, strike=None):
        shift = self.__class__.VEGA_SHIFT
        scale = self.__class__.VEGA_SCALE
        tau, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks:
            vega = self._call_vega(tau, strike, fwd, vol)
            if vega is not None:
                return vega * scale
        vega = self._call_price(tau, strike, fwd, vol + shift)
        vega -= self._call_price(date, strike, fwd, vol)
        vega *= scale / shift
        return vega

    def get_put_vega(self, date, strike=None):
        return self.get_call_vega(date, strike)

    def get_call_theta(self, date, strike=None):
        shift = self.__class__.THETA_SHIFT
        scale = self.__class__.THETA_SCALE
        tau, strike, fwd, vol = self._tsfv(date, strike)
        if not vol or not tau:
            return 0.0
        if not self.bump_greeks:
            theta = self._call_theta(date, strike, fwd, vol)
            if theta is not None:
                return theta * scale
        theta = self._call_price(tau + shift, strike, fwd, vol)
        theta -= self._call_price(tau, strike, fwd, vol)
        return theta * scale

    def get_put_theta(self, date, strike=None):
        return self.get_call_theta(date, strike)


class BinaryOptionPayOffModel(OptionPayOffModel):

    def __init__(self, pricing_formula, step=1000.0,
                 valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None,
                 bump_greeks=None):
        self._inner = pricing_formula
        self.step = step
        if isinstance(pricing_formula, OptionPayOffModel):
            valuation_date = valuation_date or pricing_formula.valuation_date
            forward_curve = forward_curve or pricing_formula.forward_curve
            volatility_curve = volatility_curve \
                or pricing_formula.volatility_curve
            day_count = day_count or pricing_formula.day_count
        super().__init__(valuation_date, forward_curve, volatility_curve,
                         day_count, bump_greeks)

    def _call_price(self, tau, strike, forward, volatility):
        high_strike = strike + 1 / self.step / 2
        low_strike = strike - 1 / self.step / 2
        call = self._inner(tau, low_strike, forward, volatility)
        call -= self._inner(tau, high_strike, forward, volatility)
        call *= self.step
        return call
