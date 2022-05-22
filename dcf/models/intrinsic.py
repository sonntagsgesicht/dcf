# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .optionpricing import OptionPayOffModel


class IntrinsicOptionPayOffModel(OptionPayOffModel):
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

    """

    def _call_price(self, time, strike, forward, volatility):
        return max(forward - strike, 0.0)

    def _call_delta(self, time, strike, forward, volatility):
        return 0.0 if forward < strike else 1.0

    def _call_gamma(self, time, strike, forward, volatility):
        return 0.0

    def _call_vega(self, time, strike, forward, volatility):
        return 0.0


class BinaryIntrinsicOptionPayOffModel(OptionPayOffModel):
    r""" intrisic option pricing formula for binary call options
    (see also |IntrinsicOptionPayOffModel()|)

    Let $F$ be the current forward value.
    Let $K$ be the option strike value,
    $\tau$ the time to matruity, i.e. the option expitry date.

    Then

        * call price: $$0 \text{ if } F < K \text{ else } 1$$

        * call delta: $$0$$

        * call gamma: $$0$$

        * call vega: $$0$$

    """

    def _call_price(self, time, strike, forward, volatility):
        return 0.0 if forward <= strike else 1.0

    def _call_delta(self, time, strike, forward, volatility):
        return 0.0

    def _call_gamma(self, time, strike, forward, volatility):
        return 0.0

    def _call_vega(self, time, strike, forward, volatility):
        return 0.0
