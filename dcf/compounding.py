# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import math


def simple_compounding(rate_value, maturity_value):
    return 1.0 / (1.0 + rate_value * maturity_value)


def simple_rate(df, period_fraction):
    return (1.0 / df - 1.0) / period_fraction


def continuous_compounding(rate_value, maturity_value):
    return math.exp(-1.0 * rate_value * maturity_value)


def continuous_rate(df, period_fraction):
    if not df:
        pass
    return -math.log(df) / period_fraction


def periodic_compounding(rate_value, maturity_value, period_value):
    return math.pow(1.0 + float(rate_value) / period_value, -period_value * maturity_value)


def periodic_rate(df, period_fraction, frequency):
    return (math.pow(df, -1.0 / (period_fraction * frequency)) - 1.0) * frequency


def annually_compounding(rate_value, maturity_value):
    return periodic_compounding(rate_value, maturity_value, 1)


def semi_compounding(rate_value, maturity_value):
    return periodic_compounding(rate_value, maturity_value, 2)


def quarterly_compounding(rate_value, maturity_value):
    return periodic_compounding(rate_value, maturity_value, 4)


def monthly_compounding(rate_value, maturity_value):
    return periodic_compounding(rate_value, maturity_value, 12)


def daily_compounding(rate_value, maturity_value):
    return periodic_compounding(rate_value, maturity_value, 365)
