# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


class OptionPricingFormula:
    r"""abstract base class for option pricing formulas

    A |OptionPricingFormula()| $f$ serves as a kind of supply template
    to enhance |OptionPayOffModel()| by a new methodology.

    To do so, $f$ should at least implement a method
    **__call__(time, strike, forward, volatility)**
    to provide the expected payoff of an European call option.

    These and all following method are only related to call options
    since put options will be derived by the use of
    `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_.

    Moreover, the **volatility** argument should be understood as
    a general input of model parameters which ar in case of classical
    option pricing formulas like |Black76()|
    the volatility.

    To provide non-numerical derivatives implement

    |OptionPricingFormula().delta()| for delta $\Delta_f$,
    the first derivative along the underlying

    |OptionPricingFormula().gamma()| for gamma $\Gamma_f$,
    the second derivative along the underlying

    |OptionPricingFormula().vega()| for vega $\mathcal{V}_f$,
    the first derivative along the volatility parameters

    |OptionPricingFormula().theta()| for theta $\Theta_f$,
    the first derivative along the time parameter **time**

    Moreover, similar methods for binary options may be provided.

    """

    # --- vanilla

    def __call__(self, time, strike, forward, volatility):
        return 0.0

    def delta(self, time, strike, forward, volatility):
        return

    def gamma(self, time, strike, forward, volatility):
        return

    def vega(self, time, strike, forward, volatility):
        return

    def theta(self, time, strike, forward, volatility):
        return

    # --- binary

    def binary(self, time, strike, forward, volatility):
        return

    def binary_delta(self, time, strike, forward, volatility):
        return

    def binary_gamma(self, time, strike, forward, volatility):
        return

    def binary_vega(self, time, strike, forward, volatility):
        return

    def binary_theta(self, time, strike, forward, volatility):
        return


class FunctionalOptionPricingFormula(OptionPricingFormula):

    def __init__(self, pricing_formula):
        self._inner = pricing_formula

    def __call__(self, time, strike, forward, volatility):
        return self._inner(time, strike, forward, volatility)


class DisplacedOptionPricingFormula(OptionPricingFormula):

    INNER = OptionPricingFormula()

    def __init__(self, displacement=0.0, *, pricing_formula=None):
        self.displacement = displacement
        """model displacement for strike and forward"""
        self._inner = pricing_formula or self.__class__.INNER
        if not isinstance(self._inner, OptionPricingFormula):
            self._inner = FunctionalOptionPricingFormula(self._inner)

    # --- vanilla

    def __call__(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner(time, strike, forward, volatility)

    def delta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.delta(time, strike, forward, volatility)

    def gamma(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.gamma(time, strike, forward, volatility)

    def vega(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.vega(time, strike, forward, volatility)

    def theta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.theta(time, strike, forward, volatility)

    # --- binary

    def binary(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.binary(time, strike, forward, volatility)

    def binary_delta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.binary_delta(time, strike, forward, volatility)

    def binary_gamma(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.binary_gamma(time, strike, forward, volatility)

    def binary_vega(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.binary_vega(time, strike, forward, volatility)

    def binary_theta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self._inner.binary_theta(time, strike, forward, volatility)
