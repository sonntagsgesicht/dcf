# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import sqrt

from .distibutions import normal_pdf, normal_cdf
from .base import OptionPayOffModel


class NormalOptionPayOffModel(OptionPayOffModel):

    def _call_price(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return (forward - strike) * normal_cdf(d) + vol * normal_pdf(d)

    def _call_delta(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return normal_cdf(d)

    def _call_gamma(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return normal_pdf(d) / vol

    def _call_vega(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return sqrt(tau) * normal_pdf(d)


class BinaryNormalOptionPayOffModel(OptionPayOffModel):

    def _call_price(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return normal_cdf(d)

    def _call_delta(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return normal_pdf(d) / vol

    def _call_gamma(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return d * normal_pdf(d) / (vol * vol * tau)

    def _call_vega(self, tau, strike, forward, volatility):
        vol = volatility * sqrt(tau)
        d = (forward - strike) / vol
        return sqrt(tau) * normal_pdf(d)
