# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


DAYS_IN_YEAR = 365.25


def day_count(start, end):
    r""" default day count function for rate period calculation

    :param start: period start date $t_s$
    :param end: period end date $t_e$
    :returns: year fraction $\tau(t_s, t_e)$
        from **start** to **end** as a float

    this default **day_count** function calculates the number of days
    between $t_s$ and $t_e$ expressed as a fraction of a year, i.e.
    $$\tau(t_s, t_e) = \frac{t_e-t_s}{365.25}$$
    as an average year has nearly $365.25$ days.

    Since different date packages have differnet concepts to derive
    the number of days between two dates, **day_count** tries to adopt
    at least some of them. As there are:

    * dates given already as year fractions as a
      `float <https://docs.python.org/3/library/functions.html?#float>`_
      so $\tau(t_s, t_e) = t_e - t_s$.

    * `datetime <https://docs.python.org/3/library/datetime.html>`_
      the native Python package, so $\delta = t_e - t_s$ is a **timedelta**
      object with attribute **days** which is used.

    * `businessdate <https://pypi.org/project/businessdate/>`_
      a specialised package for banking business calendar
      and time period calculations,
      so the **BusinessDate** object **start** has a method
      **start.diff_in_days** which is used.

    """
    if hasattr(start, 'diff_in_days'):
        # duck typing businessdate.BusinessDate.diff_in_days
        return float(start.diff_in_days(end)) / DAYS_IN_YEAR
    diff = end - start
    if hasattr(diff, 'days'):
        # assume datetime.date or finance.BusinessDate (else days as float)
        return float(diff.days) / DAYS_IN_YEAR
    # use year fraction directly
    return float(diff)
