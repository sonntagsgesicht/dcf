# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import sqrt, log

from .distibutions import normal_cdf, normal_pdf
from .base import OptionPayOffModel


class LogNormalOptionPayOffModel(OptionPayOffModel):

    def _call_price(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * normal_cdf(d) - strike * normal_cdf(d - vol)

    def _call_delta(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_cdf(d)

    def _call_gamma(self, tau, strike, forward, volatility):
        # vol = volatility * sqrt(tau)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma

    def _call_vega(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * sqrt(tau) * normal_pdf(d - vol)


class BinaryLogNormalOptionPayOffModel(OptionPayOffModel):

    def _call_price(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_cdf(d)

    def _call_delta(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_pdf(d - vol) / (vol * forward)

    def _call_gamma(self, tau, strike, forward, volatility):
        # vol = volatility * sqrt(tau)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma for digital payoff

    def _call_vega(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return (d - vol) * normal_pdf(d) / volatility
