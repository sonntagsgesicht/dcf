# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .curves.interestratecurve import ZeroRateCurve, CashRateCurve

try:
    from businessdate import BusinessDate, BusinessPeriod

    today = BusinessDate(20211201)
    b = BusinessPeriod('1b')
    d = BusinessPeriod('1d')
    m = BusinessPeriod('1m')
    y = BusinessPeriod('1y')

except ImportError:

    BusinessDate = BusinessPeriod = None

    today = 0.0
    b = 1 / 365.25
    d = 1 / 365.25
    m = 1 / 12
    y = 12 / 12

tenor_1m = 1 * m
tenor_3m = 3 * m
tenor_6m = 6 * m

zeros_term = 1 * y, 2 * y, 5 * y, 10 * y, 15 * y, 20 * y, 30 * y
fwd_term = 2 * b, 3 * m, 6 * m, 1 * y, 2 * y, 5 * y, 10 * y

zeros = -0.0084, -0.0079, -0.0057, -0.0024, -0.0008, -0.0001, 0.0003

fwd_1m = -0.0057, -0.0057, -0.0053, -0.0036, -0.0010, 0.0014, 0.0066
fwd_3m = -0.0056, -0.0054, -0.0048, -0.0033, -0.0002, 0.0018, 0.0066
fwd_6m = -0.0053, -0.0048, -0.0042, -0.0022, 0.0002, 0.0022, 0.0065
