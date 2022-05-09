# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import exp

r""" The prefactor of the normal density: $1/\sqrt{2\Pi}$. """
ONE_OVER_SQRT_OF_TWO_PI = 0.398942280401433


def normal_pdf(x):
    """ Density function for normal distribution
    @param x: float value
    @return value of normal density function
    """
    return ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5 * x * x)


def normal_cdf(x):
    """
    The cumulative distribution function of the standard normal distribution.
    The standard implementation, following Abramowitz/Stegun, (26.2.17).
    """
    if x >= 0:
        # if x > 7.0:
        #    return 1 - ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5*x*x)/sqrt(1.0+x*x)
        result = 1.0 / (1.0 + 0.2316419 * x)
        ret = 1.0 - ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5 * x * x) * (
            result * (0.31938153 +
                      result * (-0.356563782 +
                                result * (1.781477937 +
                                          result * (-1.821255978 +
                                                    result * 1.330274429)))))
        return ret

    else:
        # if x < -7.0:
        #    return 1 - one_over_sqrt_of_two_pi() * exp(-0.5*x*x)/sqrt(1.0+x*x)
        result = 1.0 / (1.0 - 0.2316419 * x)
        ret = ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5 * x * x) * (
            result * (0.31938153 +
                      result * (-0.356563782 +
                                result * (1.781477937 +
                                          result * (-1.821255978 +
                                                    result * 1.330274429)))))

        return ret
