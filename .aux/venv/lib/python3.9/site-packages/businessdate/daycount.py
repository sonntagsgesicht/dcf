# -*- coding: utf-8 -*-

# businessdate
# ------------
# Python library for generating business dates for fast date operations
# and rich functionality.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.5, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/businessdate
# License:  Apache License 2.0 (see LICENSE file)


from datetime import date
from .ymd import is_leap_year


def diff_in_days(start, end):
    """ calculates days between start and end date """
    return float((end-start).days)


def get_30_360(start, end):
    """ implements 30/360 Day Count Convention. """
    start_day = min(start.day, 30)
    end_day = 30 if (start_day == 30 and end.day == 31) else end.day
    return (360 * (end.year - start.year) + 30 * (end.month - start.month) + (end_day - start_day)) / 360.0


def get_30e_360(start, end):
    """ implements the 30E/360 Day Count Convention. """

    y1, m1, d1 = start.timetuple()[:3]
    # adjust to date immediately following the the last day
    y2, m2, d2 = end.timetuple()[:3]

    d1 = min(d1, 30)
    d2 = min(d2, 30)

    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360.0


def get_30e_360i(start, end):
    """ implements the 30E/360 I. Day Count Convention. """
    y1, m1, d1 = start.timetuple()[:3]
    # adjust to date immediately following the last day
    y2, m2, d2 = end.timetuple()[:3]

    if (m1 == 2 and d1 >= 28) or d1 == 31:
        d1 = 30
    if (m2 == 2 and d2 >= 28) or d2 == 31:
        d2 = 30

    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360.0


def get_act_360(start, end):
    """ implements Act/360 day count convention. """
    return diff_in_days(start, end) / 360.0


def get_act_365(start, end):
    """ implements Act/365 day count convention. """
    return diff_in_days(start, end) / 365.0


def get_act_36525(start, end):
    """ implements Act/365.25 Day Count Convention """
    return diff_in_days(start, end) / 365.25


def get_act_act(start, end):
    """ implements Act/Act day count convention. """

    # if the period does not lie within a year split the days in the period as following:
    #           remaining days of start year / years in between / days in the end year
    # REMARK: following the before mentioned Definition the first day of the period is included whereas the
    # last day will be excluded
    # What remains to check now is only whether the start and end year are leap or non-leap years. The quotients
    # can be easily calculated and for the years in between they are always one (365/365 = 1; 366/366 = 1)

    if end.year - start.year == 0:
        if is_leap_year(start.year):
            return diff_in_days(start, end) / 366.0  # leap year: 366 days
        return diff_in_days(start, end) / 365.0  # non-leap year: 365 days

    rest_year1 = diff_in_days(start, date(start.year, 12, 31)) + 1  # since the first day counts
    rest_year2 = abs(diff_in_days(end, date(end.year, 1, 1)))  # here the last day is automatically not counted
    years_in_between = end.year - start.year - 1

    return years_in_between + rest_year1 / (366.0 if is_leap_year(start.year) else 365.0) + rest_year2 / (
        366.0 if is_leap_year(end.year) else 365.0)
