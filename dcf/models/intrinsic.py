# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .base import OptionPayOffModel


class IntrinsicOptionPayOffModel(OptionPayOffModel):

    def _call_price(self, tau, strike, forward, volatility):
        return max(forward - strike, 0.0)

    def _call_delta(self, tau, strike, forward, volatility):
        return 0.0 if forward < strike else 1.0

    def _call_gamma(self, tau, strike, forward, volatility):
        return 0.0

    def _call_vega(self, tau, strike, forward, volatility):
        return 0.0


class BinaryIntrinsicOptionPayOffModel(OptionPayOffModel):

    def _call_price(self, tau, strike, forward, volatility):
        return 0.0 if forward <= strike else 1.0

    def _call_delta(self, tau, strike, forward, volatility):
        return 0.0

    def _call_gamma(self, tau, strike, forward, volatility):
        return 0.0

    def _call_vega(self, tau, strike, forward, volatility):
        return 0.0
