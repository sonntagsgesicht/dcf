# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .base import OptionPricingFormula


class Intrinsic(OptionPricingFormula):
    r""" intrisic option pricing formula

    implemented for call options
    (`see more on intrisic option values
    <https://en.wikipedia.org/wiki/Option_time_value>`_)

    Let $F$ be the current forward value.
    Let $K$ be the option strike value,
    $\tau$ the time to matruity, i.e. the option expitry date.

    Then

        * call price: $$\max(F-K, 0)$$

        * call delta: $$0 \text{ if } F < K \text{ else } 1$$

        * call gamma: $$0$$

        * call vega: $$0$$

        * binary call price: $$0 \text{ if } F < K \text{ else } 1$$

        * binary call delta: $$0$$

        * binary call gamma: $$0$$

        * binary call vega: $$0$$

    """

    ### vanilla

    def __call__(self, time, strike, forward, volatility):
        return max(forward - strike, 0.0)

    def delta(self, time, strike, forward, volatility):
        return 0.0 if forward < strike else 1.0

    def gamma(self, time, strike, forward, volatility):
        return 0.0

    def vega(self, time, strike, forward, volatility):
        return 0.0

    def theta(self, time, strike, forward, volatility):
        return 0.0

    ### binary

    def binary(self, time, strike, forward, volatility):
        return 0.0 if forward <= strike else 1.0

    def binary_delta(self, time, strike, forward, volatility):
        return 0.0

    def binary_gamma(self, time, strike, forward, volatility):
        return 0.0

    def binary_vega(self, time, strike, forward, volatility):
        return 0.0

    def binary_theta(self, time, strike, forward, volatility):
        return 0.0
