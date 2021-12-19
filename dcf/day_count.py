# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.6, copyright Sunday, 19 December 2021
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


def act_36525(start, end):
    if hasattr(start, 'diff_in_days'):
        # duck typing businessdate.BusinessDate.diff_in_days
        d = start.diff_in_days(end)
    else:
        d = end - start
        if hasattr(d, 'days'):
            # assume datetime.date or finance.BusinessDate (else days as float)
            d = d.days
    return float(d) / 365.25


def year_fraction(start, end):
    return float(end - start)


def day_count(start, end):
    if hasattr(start, 'diff_in_days') or hasattr(end - start, 'days'):
        return act_36525(start, end)
    else:
        return year_fraction(start, end)
