# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht
# Version:  1.0, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from datetime import date, datetime
from inspect import getsource
from typing import Any as DateType  # noqa E401 E402


class _DayCount:
    r""" day count function for rate period calculation

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

    DAYS_IN_YEAR = 365.24
    DAY_COUNT = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_DayCount, cls).__new__(cls)
        return cls._instance

    def __call__(self, start, end):
        if not start:
            if type(end) == datetime:  # noqa E721
                start = datetime.now()
            elif type(end) == date:  # noqa E721
                start = date.today()
            else:
                start = type(end)()
        if self.DAY_COUNT is not None:
            return self.DAY_COUNT(start, end)
        if hasattr(start, 'diff_in_days'):
            # duck typing businessdate.BusinessDate.diff_in_days
            return float(start.diff_in_days(end)) / self.DAYS_IN_YEAR
        diff = end - start
        if hasattr(diff, 'days'):
            # assume datetime.date or finance.BusinessDate (else days as float)
            return float(diff.days) / self.DAYS_IN_YEAR
        # use year fraction directly
        return float(diff)

    def set(self, day_count=None):
        self.DAY_COUNT = day_count

    def __repr__(self):
        if self.DAY_COUNT is not None:
            if isinstance(self.DAY_COUNT, type(lambda: None)):
                return 'dcf.' + getsource(self.DAY_COUNT)
            dc = getattr(self.DAY_COUNT, '__qualname__', str(self.DAY_COUNT))
            return f"dcf.day_count.set({dc})"
        return 'dcf.day_count'


day_count = _DayCount()


def origin(curve, default=0.0):
    return getattr(curve, 'origin', default)


def year_fraction(curve, default=None):
    if hasattr(curve, 'year_fraction'):
        return curve.year_fraction
    if hasattr(curve, 'day_count'):
        return lambda x: curve.day_count(origin(curve), x)
    if default is None:
        return lambda x: day_count(origin(curve), x)
    return default
