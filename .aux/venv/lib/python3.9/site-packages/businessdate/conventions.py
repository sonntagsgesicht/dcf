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


from calendar import WEDNESDAY, FRIDAY
from datetime import date, timedelta
from .ymd import days_in_month, end_of_quarter_month

ONE_DAY = timedelta(1)


def is_business_day(business_date, holidays=list()):
    """ method to check if a date falls neither on weekend nor is in holidays. """

    if business_date.weekday() > FRIDAY:
        return False
    return business_date not in holidays


def adjust_no(business_date, holidays=()):
    """ does no adjustment. """
    return business_date


def adjust_previous(business_date, holidays=()):
    """ adjusts to Business Day Convention "Preceding". """
    while not is_business_day(business_date, holidays):
        business_date -= ONE_DAY
    return business_date


def adjust_follow(business_date, holidays=()):
    """ adjusts to Business Day Convention "Following". """
    while not is_business_day(business_date, holidays):
        business_date += ONE_DAY
    return business_date


def adjust_mod_follow(business_date, holidays=()):
    """ adjusts to Business Day Convention "Modified [Following]". """
    month = business_date.month
    new = adjust_follow(business_date, holidays)
    if month != new.month:
        new = adjust_previous(business_date, holidays)
    business_date = new
    return business_date


def adjust_mod_previous(business_date, holidays=()):
    """ adjusts to Business Day Convention "Modified Preceding". """
    month = business_date.month
    new = adjust_previous(business_date, holidays)
    if month != new.month:
        new = adjust_follow(business_date, holidays)
    business_date = new
    return business_date


def adjust_start_of_month(business_date, holidays=()):
    """ adjusts to Business Day Convention "Start of month", i.e. first business day. """
    business_date = date(business_date.year, business_date.month, 1)
    business_date = adjust_follow(business_date, holidays)
    return business_date


def adjust_end_of_month(business_date, holidays=()):
    """ adjusts to Business Day Convention "End of month", i.e. last business day. """
    y, m, d = business_date.year, business_date.month, business_date.day
    business_date = date(y, m, days_in_month(y, m))
    business_date = adjust_previous(business_date, holidays)
    return business_date


def adjust_imm(business_date, holidays=()):
    """ adjusts to Business Day Convention of "International Monetary Market". """
    business_date = date(business_date.year, end_of_quarter_month(business_date.month), 15)
    while business_date.weekday() == WEDNESDAY:
        business_date += ONE_DAY
    return business_date


def adjust_cds_imm(business_date, holidays=()):
    """ adjusts to Business Day Convention "Single Name CDS". """
    business_date = date(business_date.year, end_of_quarter_month(business_date.month), 20)
    return business_date
