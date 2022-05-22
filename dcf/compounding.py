# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import exp, log, pow


def simple_compounding(rate_value, maturity_value):
    r"""simple compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $\frac{1}{1+r\cdot \tau}$
    """
    return 1.0 / (1.0 + rate_value * maturity_value)


def simple_rate(df, period_fraction):
    r"""interest rate from simple compounded dicount factor

    :param df: discount factor $df$
    :param period_fraction: interest rate period $\tau$
    :return: $\frac{1}{df-1}\cdot \frac{1}{\tau}$
    """
    return (1.0 / df - 1.0) / period_fraction


def continuous_compounding(rate_value, maturity_value):
    r"""continuous compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $\exp(-r\cdot \tau)$
    """
    return exp(-1.0 * rate_value * maturity_value)


def continuous_rate(df, period_fraction):
    r"""interest rate from continuous compounded dicount factor

    :param df: discount factor $df$
    :param period_fraction: interest rate period $\tau$
    :return: $-\log(df)\cdot \frac{1}{\tau}$
    """
    if not df:
        pass
    return -log(df) / period_fraction


def periodic_compounding(rate_value, maturity_value, period_value):
    r"""periodicly compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :param period_value: number of interest rate periods $m$
    :return: $(1+\frac{r}{m})^{-\tau\cdot m}$
    """
    ex = -period_value * maturity_value
    return pow(1.0 + float(rate_value) / period_value, ex)


def periodic_rate(df, period_fraction, frequency):
    r"""interest rate from continuous compounded dicount factor

    :param df: discount factor $df$
    :param period_fraction: interest rate period $\tau$
    :param frequency: number of interest rate periods $m$
    :return: $(df^{-\frac{1}{\tau\cdot m}}-1) \cdot m$
    """
    return (pow(df, -1.0 / (period_fraction * frequency)) - 1.0) * frequency


def annually_compounding(rate_value, maturity_value):
    r"""annually compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+r)^{-\tau}$
    """
    return periodic_compounding(rate_value, maturity_value, 1)


def semi_compounding(rate_value, maturity_value):
    r"""semi compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{2})^{-\tau\cdot 2}$
    """
    return periodic_compounding(rate_value, maturity_value, 2)


def quarterly_compounding(rate_value, maturity_value):
    r"""quarterly compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{4})^{-\tau\cdot 4}$
    """
    return periodic_compounding(rate_value, maturity_value, 4)


def monthly_compounding(rate_value, maturity_value):
    r"""monthly compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{12})^{-\tau\cdot 12}$
    """
    return periodic_compounding(rate_value, maturity_value, 12)


def daily_compounding(rate_value, maturity_value):
    r"""daily compounded discount factor

    :param rate_value: interest rate $r$
    :param maturity_value: loan maturity $\tau$
    :return: $(1+\frac{r}{365})^{-\tau\cdot 365}$
    """
    return periodic_compounding(rate_value, maturity_value, 365)
