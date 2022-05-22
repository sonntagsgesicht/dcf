# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import sqrt

from .distibutions import normal_pdf, normal_cdf
from .optionpricing import OptionPayOffModel


class NormalOptionPayOffModel(OptionPayOffModel):
    r""" Bachelier option pricing formula

    implemented for call options
    (`see more on Bacheliers model
    <https://en.wikipedia.org/wiki/Bachelier_model>`_)

    Let $f$ be a normaly distributed random variable
    with expectation $F=E[f]$, the current forward value
    and $\Phi$ the standard normal cummulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Let $K$ be the option strike value,
    $\tau$ the time to matruity, i.e. the option expitry date, and
    $\sigma$ the volatility parameter,
    i.e. the standard deviation of $f$.
    Moreover, let $$d = \frac{F-K}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price:
          $$(F-K) \cdot \Phi(d) + \sigma \cdot \sqrt{\tau} \cdot \phi(d)$$

        * call delta: $$\Phi(d)$$

        * call gamma: $$\frac{\phi(d)}{\sigma \cdot \sqrt{\tau}}$$

        * call vega: $$\sqrt{\tau} \cdot \phi(d)$$
    """

    def _call_price(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return (forward - strike) * normal_cdf(d) + vol * normal_pdf(d)

    def _call_delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return normal_cdf(d)

    def _call_gamma(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return normal_pdf(d) / vol

    def _call_vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return sqrt(time) * normal_pdf(d)


class BinaryNormalOptionPayOffModel(OptionPayOffModel):
    r""" Bachelier option pricing formula for binary calls
    (see also |NormalOptionPayOffModel()|)

    Let $f$ be a normaly distributed random variable
    with expectation $F=E[f]$, the current forward value
    and $\Phi$ the standard normal cummulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Let $K$ be the option strike value,
    $\tau$ the time to matruity, i.e. the option expitry date, and
    $\sigma$ the volatility parameter,
    i.e. the stanard deviation of $f$.
    Moreover, let $$d = \frac{F-K}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price: $$\Phi(d)$$

        * call delta: $$\frac{\phi(d)}{\sigma \cdot \sqrt{\tau}}$$

        * call gamma: $$d \cdot \frac{\phi(d)}{\sigma^2 \cdot \tau}$$

        * call vega: $$\sqrt{\tau} \cdot \phi(d)$$

    """

    def _call_price(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return normal_cdf(d)

    def _call_delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return normal_pdf(d) / vol

    def _call_gamma(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return d * normal_pdf(d) / (vol * vol * time)

    def _call_vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return sqrt(time) * normal_pdf(d)
