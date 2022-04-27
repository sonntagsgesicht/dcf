# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.6, copyright Sunday, 19 December 2021
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


DAYS_IN_YEAR = 365.25


def day_count(start, end):
    if hasattr(start, 'diff_in_days'):
        # duck typing businessdate.BusinessDate.diff_in_days
        return float(start.diff_in_days(end)) / DAYS_IN_YEAR
    diff = end - start
    if hasattr(diff, 'days'):
        # assume datetime.date or finance.BusinessDate (else days as float)
        return float(diff.days) / DAYS_IN_YEAR
    # use year fraction directly
    return float(diff)
