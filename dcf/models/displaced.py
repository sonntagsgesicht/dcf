# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .black76 import LogNormalOptionPayOffModel, \
    BinaryLogNormalOptionPayOffModel


class DisplacedLogNormalOptionPayOffModel(LogNormalOptionPayOffModel):

    def __init__(self, valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None, bump_greeks=None,
                 displacement=0.0):
        super().__init__(valuation_date, forward_curve, volatility_curve,
                         day_count, bump_greeks)
        self.displacement = displacement

    def _call_price(self, tau, strike, forward, volatility):
        return super()._call_price(tau,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)

    def _call_delta(self, tau, strike, forward, volatility):
        return super()._call_delta(tau,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)

    def _call_gamma(self, tau, strike, forward, volatility):
        return super()._call_gamma(tau,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)

    def _call_vega(self, tau, strike, forward, volatility):
        return super()._call_vega(tau,
                                  strike + self.displacement,
                                  forward + self.displacement,
                                  volatility)


class BinaryDisplacedLogNormalOptionPayOffModel(BinaryLogNormalOptionPayOffModel):  # noqa E501

    def __init__(self, valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None, bump_greeks=None,
                 displacement=0.0):
        super().__init__(valuation_date, forward_curve, volatility_curve,
                         day_count, bump_greeks)
        self.displacement = displacement

    def _call_price(self, tau, strike, forward, volatility):
        return super()._call_price(tau,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)
