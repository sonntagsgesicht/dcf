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

from .base import OptionPricingFormula, DisplacedOptionPricingFormula
from .math import normal_cdf, normal_pdf


class Black76(OptionPricingFormula):
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

        * binary call price: $$\Phi(d)$$

        * binary call delta:
          $$\frac{\phi(d-\sigma \cdot \sqrt{\tau})}{\sigma \cdot \sqrt{\tau}}$$

        * binary call gamma: $$d \cdot \frac{\phi(d)}{\sigma^2 \cdot \tau}$$

        * binary call vega: $$(d/\sigma - \sqrt{\tau}) \cdot \phi(d)$$

    """

    ### vanilla

    def __call__(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * normal_cdf(d) - strike * normal_cdf(d - vol)

    def delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_cdf(d)

    def gamma(self, time, strike, forward, volatility):
        # vol = volatility * sqrt(time)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma

    def vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * sqrt(time) * normal_pdf(d - vol)

    ### binary

    def binary(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_cdf(d)

    def binary_delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return normal_pdf(d - vol) / (vol * forward)

    def binary_gamma(self, time, strike, forward, volatility):
        # vol = volatility * sqrt(time)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma for digital payoff

    def binary_vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return (d - vol) * normal_pdf(d) / volatility


class DisplacedBlack76(DisplacedOptionPricingFormula):
    r""" displaced Black 76 option pricing formula

    implemented for call options
    (see also |Black76()|)

    The displaced Black 76 is adopted to handel moderate negative
    underlying forward prices or rates $f$,
    e.g. as see for interest rates in the past.
    To do so, rather than $f$ a shifted or displaced version $f + \alpha$
    is assumed to be log-normally distributed
    for some negative value of $\alpha$.

    Hence, let $f + \alpha$ be a log-normally distributed random variable
    with expectation $F + \alpha=E[f + \alpha]$,
    where $F=E[f]$ is the current forward value
    and $\Phi$ the standard normal cumulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Uses |Black76()| formulas
    with

        * displaced forward $F+\alpha$

    and

        * displaced strike $K+\alpha$

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

        * binary call price:

        * binary call delta:

        * binary call gamma:

        * binary call vega:

    """

    INNER = Black76()
