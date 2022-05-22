# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import sqrt, log

from .distibutions import normal_cdf, normal_pdf
from .optionpricing import OptionPayOffModel


class LogNormalOptionPayOffModel(OptionPayOffModel):
    r""" Black 76 option pricing formula

    implemented for call options
    (`see more on Black 76 model
    <https://en.wikipedia.org/wiki/Black_model>`_
    which is closly related to the
    `Black-Scholes model
    <https://en.wikipedia.org/wiki/Black–Scholes_model>`_)

    Let $f$ be a log-normaly distributed random variable
    with expectation $F=E[f]$, the current forward value
    and $\Phi$ the standard normal cummulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Let $K$ be the option strike value,
    $\tau$ the time to maturity, i.e. the option expiry date, and
    $\sigma$ the volatility parameter,
    i.e. the standard deviation of $\log(f)$.
    Moreover, let
    $$d =\frac{\log(F/K) + (\sigma^2 \cdot \tau)/2}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price:
          $$F \cdot \Phi(d) - K \cdot \Phi(d-\sigma \cdot \sqrt{\tau})$$

        * call delta: $$\Phi(d)$$

        * call gamma: $$\frac{\phi(d)}{F \cdot \sigma \cdot \sqrt{\tau}}$$

        * call vega: $$F \cdot \sqrt{\tau} \cdot \phi(d)$$
    """

    def _call_price(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * normal_cdf(d) - strike * normal_cdf(d - vol)

    def _call_delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_cdf(d)

    def _call_gamma(self, time, strike, forward, volatility):
        # vol = volatility * sqrt(time)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma

    def _call_vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * sqrt(time) * normal_pdf(d - vol)


class BinaryLogNormalOptionPayOffModel(OptionPayOffModel):
    r""" Black 76 option pricing formula for binary calls
    (see also |LogNormalOptionPayOffModel()|)

    Let $f$ be a log-normaly distributed random variable
    with expectation $F=E[f]$, the current forward value
    and $\Phi$ the standard normal cummulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Let $K$ be the option strike value,
    $\tau$ the time to maturity, i.e. the option expiry date, and
    $\sigma$ the volatility parameter,
    i.e. the standard deviation of $\log(f)$.
    Moreover, let
    $$d =\frac{\log(F/K) + (\sigma^2 \cdot \tau)/2}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price: $$\Phi(d)$$

        * call delta:
          $$\frac{\phi(d-\sigma \cdot \sqrt{\tau})}{\sigma \cdot \sqrt{\tau}}$$

        * call gamma: $$d \cdot \frac{\phi(d)}{\sigma^2 \cdot \tau}$$

        * call vega: $$(d/\sigma - \sqrt{\tau}) \cdot \phi(d)$$

    """

    def _call_price(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_cdf(d)

    def _call_delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_pdf(d - vol) / (vol * forward)

    def _call_gamma(self, time, strike, forward, volatility):
        # vol = volatility * sqrt(time)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma for digital payoff

    def _call_vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return (d - vol) * normal_pdf(d) / volatility
