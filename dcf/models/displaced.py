# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .black76 import LogNormalOptionPayOffModel, \
    BinaryLogNormalOptionPayOffModel


class DisplacedLogNormalOptionPayOffModel(LogNormalOptionPayOffModel):
    r""" displaced Black 76 option pricing formula

    implemented for call options
    (see also |LogNormalOptionPayOffModel()|)

    The displaced Black 76 is adopted to handel moderate negative
    underlying forward prices or rates $f$,
    e.g. as see for interest rates in the past.
    To do so, rather than $f$ a shifted or displaced version $f + \alpha$
    is assumed to be log-normaly distributed
    for some negative value of $\alpha$.

    Hence, let $f + \alpha$ be a log-normaly distributed random variable
    with expectation $F + \alpha=E[f + \alpha]$,
    where $F=E[f]$ is the current forward value
    and $\Phi$ the standard normal cummulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Let $K$ be the option strike value,
    $\tau$ the time to maturity, i.e. the option expiry date, and
    $\sigma$ the volatility parameter,
    i.e. the standard deviation of $\log(f + \alpha)$.
    Moreover, let
    $$d =\frac{\log((F+\alpha)/(K+\alpha))
    + (\sigma^2 \cdot \tau)/2}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price:
          $$(F+\alpha) \cdot \Phi(d)
          - (K+\alpha) \cdot \Phi(d-\sigma \cdot \sqrt{\tau})$$

        * call delta: $$\Phi(d)$$

        * call gamma:
          $$\frac{\phi(d)}{(F+\alpha) \cdot \sigma \cdot \sqrt{\tau}}$$

        * call vega: $$(F+\alpha) \cdot \sqrt{\tau} \cdot \phi(d)$$
    """

    def __init__(self, valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None, bump_greeks=None,
                 displacement=0.0):
        super().__init__(valuation_date, forward_curve, volatility_curve,
                         day_count, bump_greeks)
        self.displacement = displacement

    def _call_price(self, time, strike, forward, volatility):
        return super()._call_price(time,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)

    def _call_delta(self, time, strike, forward, volatility):
        return super()._call_delta(time,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)

    def _call_gamma(self, time, strike, forward, volatility):
        return super()._call_gamma(time,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)

    def _call_vega(self, time, strike, forward, volatility):
        return super()._call_vega(time,
                                  strike + self.displacement,
                                  forward + self.displacement,
                                  volatility)


class BinaryDisplacedLogNormalOptionPayOffModel(BinaryLogNormalOptionPayOffModel):  # noqa E501
    r""" displaced Black 76 option pricing formula for binary calls
    (see also |DisplacedLogNormalOptionPayOffModel()|)

    Uses |BinaryLogNormalOptionPayOffModel()| formulas
    with

    * displaced forward $F+\alpha$

    and

    * displaced strike $K+\alpha$

    """
    def __init__(self, valuation_date=None, forward_curve=None,
                 volatility_curve=None, day_count=None, bump_greeks=None,
                 displacement=0.0):
        super().__init__(valuation_date, forward_curve, volatility_curve,
                         day_count, bump_greeks)
        self.displacement = displacement

    def _call_price(self, time, strike, forward, volatility):
        return super()._call_price(time,
                                   strike + self.displacement,
                                   forward + self.displacement,
                                   volatility)
