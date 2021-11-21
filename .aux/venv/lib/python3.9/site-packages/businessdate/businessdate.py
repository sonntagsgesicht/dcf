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


from datetime import date, datetime, timedelta

from . import conventions
from . import daycount
from .ymd import is_leap_year, days_in_year, days_in_month, end_of_quarter_month
from .basedate import BaseDateFloat, BaseDateDatetimeDate
from .businessholidays import TargetHolidays
from .businessperiod import BusinessPeriod


class BusinessDate(BaseDateDatetimeDate):
    ADJUST = 'No'
    BASE_DATE = None
    DATE_FORMAT = '%Y%m%d'
    DAY_COUNT = 'act_36525'
    DEFAULT_HOLIDAYS = TargetHolidays()

    _adj_func = {
        'no': conventions.adjust_no,
        'previous': conventions.adjust_previous,
        'prev': conventions.adjust_previous,
        'prv': conventions.adjust_previous,
        'mod_previous': conventions.adjust_mod_previous,
        'modprevious': conventions.adjust_mod_previous,
        'modprev': conventions.adjust_mod_previous,
        'modprv': conventions.adjust_mod_previous,
        'follow': conventions.adjust_follow,
        'flw': conventions.adjust_follow,
        'modified': conventions.adjust_mod_follow,
        'mod_follow': conventions.adjust_mod_follow,
        'modfollow': conventions.adjust_mod_follow,
        'modflw': conventions.adjust_mod_follow,
        'start_of_month': conventions.adjust_start_of_month,
        'startofmonth': conventions.adjust_start_of_month,
        'som': conventions.adjust_start_of_month,
        'end_of_month': conventions.adjust_end_of_month,
        'endofmonth': conventions.adjust_end_of_month,
        'eom': conventions.adjust_end_of_month,
        'imm': conventions.adjust_imm,
        'cds_imm': conventions.adjust_cds_imm,
        'cdsimm': conventions.adjust_cds_imm,
        'cds': conventions.adjust_cds_imm,
    }
    _dc_func = {
        '30_360': daycount.get_30_360,
        '30360': daycount.get_30_360,
        'thirty360': daycount.get_30_360,
        '30e_360': daycount.get_30e_360,
        '30e360': daycount.get_30e_360,
        'thirtye360': daycount.get_30e_360,
        '30e_360_i': daycount.get_30e_360i,
        '30e360i': daycount.get_30e_360i,
        'thirtye360i': daycount.get_30e_360i,
        'act_360': daycount.get_act_360,
        'act360': daycount.get_act_360,
        'act_365': daycount.get_act_365,
        'act365': daycount.get_act_365,
        'act_36525': daycount.get_act_36525,
        'act_365.25': daycount.get_act_36525,
        'act36525': daycount.get_act_36525,
        'act_act': daycount.get_act_act,
        'actact': daycount.get_act_act,
    }

    def __new__(cls, year=None, month=0, day=0, convention=None, holidays=None):
        """ date class to perform calculations coming from financial businesses

        :param year: number of year or some other input value t
         o create :class:`BusinessDate` instance.
         When applying other input, this can be either
         :class:`int`, :class:`float`, :class:`datetime.date` or :class:`string`
         which will be parsed and transformed into equivalent
         :class:`tuple` of :class:`int` items `(year,month,day)`
         (See :doc:`tutorial <tutorial>` for details).
        :param int month: number of month in year 1 ... 12
         (default: 0, required to be 0 when other input of year is used)
        :param int days: number of day in month 1 ... 31
         (default: 0, required to be 0 when other input of year is used)

        For all input arguments exits read only properties.

        """

        '''
        :param str convention: keyword to select a business day adjustment convention
         which is used as default for :meth:`BusinessDate.adjust`.
         For more details on the conventions see module :mod:`businessdate.conventions`.
        :param list holidays: container containing items of type :class:`datetime.date`
         which is used as default for :meth:`BusinessDate.adjust`.
        '''

        if isinstance(year, str):
            year, month, day = cls._parse_date_string(year, default=(year, month, day))

        if isinstance(year, (date, BaseDateFloat, BaseDateDatetimeDate, BusinessDate)):
            year, month, day = year.year, year.month, year.day

        if isinstance(year, (int, float)) and 10000101 <= year:  # start 20191231 representation from 1000 a.d.
            ymd = str(year)
            year, month, day = int(ymd[:4]), int(ymd[4:6]), int(ymd[6:])

        if isinstance(year, int) and month and day:
            if 12 < month:
                year += int(month // 12)
                month = int(month % 12)
            if issubclass(cls, BaseDateFloat):
                return cls.from_ymd(year, month, day)
            return super(BusinessDate, cls).__new__(cls, year, month, day)

        if isinstance(year, (int, float)) and 1 < year < 10000101:  # excel representation before 1000 a.d.
            if issubclass(cls, BaseDateDatetimeDate):
                return cls.from_float(year)
            return super(BusinessDate, cls).__new__(cls, year)

        if isinstance(year, (list, tuple)):
            return list(map(BusinessDate, year))

        if year is None:
            if cls.BASE_DATE is None:
                return cls(date.today())
            return cls(cls.BASE_DATE)

        if isinstance(year, timedelta):
            year = '%sD' % year.days

        # try to split complex or period input, e.g. '0B1D2BMOD20191231' or '3Y2M1D' or '-2B'
        return cls._from_complex_input(str(year))

    @classmethod
    def _parse_date_string(cls, date_str, default=None):
        date_str = str(date_str)
        if date_str.count('-'):
            str_format = '%Y-%m-%d'
        elif date_str.count('.'):
            str_format = '%d.%m.%Y'
        elif date_str.count('/'):
            str_format = '%m/%d/%Y'
        elif len(date_str) == 8 and date_str.isdigit():
            str_format = '%Y%m%d'
        else:
            str_format = ''
        if str_format:
            date_date = datetime.strptime(date_str, str_format)
            return date_date.year, date_date.month, date_date.day

        if default is None:
            raise ValueError("The input %s has not the right format for %s" % (date_str, cls.__name__))
        return default

    @classmethod
    def _from_complex_input(cls, date_str):
        date_str = str(date_str).upper()
        convention, origin, holidays = None, None, None

        # first, extract origin
        if len(date_str) > 8:
            try:
                datetime.strptime(date_str[-8:], '%Y%m%d')
                origin = date_str[-8:]
                date_str = date_str[:-8]
            except ValueError:
                # no date found a the end of the string
                pass

        # second, extract convention
        for a in sorted(cls._adj_func.keys(), key=len, reverse=True):
            if date_str.find(a.upper()) >= 0:
                convention = a
                date_str = date_str[:-len(a)]
                break
        if not date_str:
            date_str = '0B'

        # third, parse spot, period and final
        pfields = date_str.strip('0123456789+-B')
        spot, period, final = date_str, '', ''
        if pfields:
            spot, period, final = '', '', ''
            x = pfields[-1]
            period, final = date_str.split(x, 1)
            period += x
            if period.find('B') >= 0:
                spot, period = period.split('B', 1)
                spot += 'B'

        # third, build BusinessDate and adjust by conventions to periods
        res = cls(origin)
        if spot:
            if convention:
                res = res.adjust(convention, holidays)
            res = res.add_period(spot, holidays)
        if period:
            res = res.add_period(period, holidays)
        if final:
            if convention:
                res = res.adjust(convention, holidays)
            res = res.add_period(final, holidays)
        return res

    @classmethod
    def is_businessdate(cls, d):
        """ checks whether the provided input can be a date """
        if not isinstance(d, (date, BaseDateFloat, BaseDateDatetimeDate)):
            try:  # to be removed
                cls(d)
            except ValueError:
                return False
        return True

    def __copy__(self):
        return self.__deepcopy__()

    def __deepcopy__(self, memodict={}):
        return BusinessDate(date(*self.to_ymd()))

    # --- operator methods ---------------------------------------------------

    def __add__(self, other):
        """
            addition of BusinessDate.

        :param other: can be BusinessPeriod or
        any thing that might be casted to it. Or a list of them.
        """
        if isinstance(other, (list, tuple)):
            return [self + pd for pd in other]
        if BusinessPeriod.is_businessperiod(other):
            return self.add_period(other)
        raise TypeError('addition of BusinessDates cannot handle objects of type %s.' % other.__class__.__name__)

    def __sub__(self, other):
        """
            subtraction of BusinessDate.

        :param other: can be other BusinessDate, BusinessPeriod or
        any thing that might be casted to those. Or a list of them.
        """
        if isinstance(other, (list, tuple)):
            return [self - pd for pd in other]
        if BusinessPeriod.is_businessperiod(other):
            return self + (-1 * BusinessPeriod(other))
        if BusinessDate.is_businessdate(other):
            y, m, d = BusinessDate(other).diff_in_ymd(self)
            return BusinessPeriod(years=y, months=m, days=d)
        raise TypeError('subtraction of BusinessDates cannot handle objects of type %s.' % other.__class__.__name__)

    def __str__(self):
        date_format = self.__class__.DATE_FORMAT
        return self.to_date().strftime(date_format)

    def __repr__(self):
        return self.__class__.__name__ + "(%s)" % str(self)

    # --- validation and information methods ------------------------

    def is_leap_year(self):
        """ returns `True` for leap year and False otherwise """
        return is_leap_year(self.year)

    def days_in_year(self):
        """ returns number of days in the given calendar year """
        return days_in_year(self.year)

    def days_in_month(self):
        """ returns number of days for the month """
        return days_in_month(self.year, self.month)

    def end_of_month(self):
        """ returns the day of the end of the month as :class:`BusinessDate` object"""
        return BusinessDate(self.year, self.month, self.days_in_month())

    def end_of_quarter(self):
        """ returns the day of the end of the quarter as :class:`BusinessDate` object"""
        return BusinessDate(self.year, end_of_quarter_month(self.month), 0o1).end_of_month()

    def is_business_day(self, holidays=None):
        """ returns `True` if date falls neither on weekend nor is in holidays (if given as container object) """
        holidays = self.__class__.DEFAULT_HOLIDAYS if holidays is None else holidays
        return conventions.is_business_day(self.to_date(), holidays)

    # --- calculation methods --------------------------------------------

    def _add_business_days(self, days_int, holidays=None):
        holidays = self.__class__.DEFAULT_HOLIDAYS if holidays is None else holidays

        res = self.__deepcopy__()
        if days_int >= 0:
            count = 0
            while count < days_int:
                res = res._add_days(1)
                if res.is_business_day(holidays):
                    count += 1
        else:
            count = 0
            while count > days_int:
                res = res._add_days(-1)
                if res.is_business_day(holidays):
                    count -= 1

        return res

    def _add_ymd(self, years=0, months=0, days=0):
        s = self
        y = s.year + years
        m = s.month + months
        while m < 1:
            m += 12
            y -= 1
        som = self.__class__(y, m, 1)
        d = min(self.day, som.days_in_month()) - 1 + days
        return som._add_days(d)

    def add_period(self, period_obj, holidays=None):
        """ adds a :class:`BusinessPeriod` object
        or anythings that create one and returns :class:`BusinessDate` object.

        It is simply adding the number of `years`, `months` and `days` or
        if `businessdays` given the number of business days,
        i.e. days neither weekend nor in holidays (see also :meth:`BusinessDate.is_business_day`)
        """

        p = BusinessPeriod(period_obj)
        res = self
        res = res._add_business_days(p.businessdays, holidays)
        res = res._add_ymd(p.years, p.months, p.days)
        return res

    def diff_in_days(self, end_date):
        """ calculates the distance to a :class:`BusinessDate` in days """
        return int(self._diff_in_days(end_date))

    def diff_in_ymd(self, end_date):

        if end_date < self:
            y,m,d = 0,0,0
            while end_date < self._add_ymd(y,0,0):
                y -= 1
            while end_date < self._add_ymd(y+1,m,0):
                m -= 1
            while end_date < self._add_ymd(y+1,m+1,d):
                d -= 1
            return y+1, m+1, d

        y = end_date.year - self.year
        m = end_date.month - self.month
        d = end_date.day - self.day

        while m < 0:
            y -= 1
            m += 12

        while d < 0:
            m -= 1
            if m < 0:
                y -= 1
                m += 12
            d = self._add_ymd(y, m, 0)._diff_in_days(end_date)

        # if not any((0 <= y, 0 <= m < 12, 0 <= d < 31)):
        #     raise AssertionError((y,m,d))
        # if not end_date == self._add_ymd(y, m, d):
        #     raise AssertionError('%s!=%s==%s._add_ymd(%d,%d,%d)' %
        #                    (end_date, self._add_ymd(y, m, d), self, y, m, d))
        # if not self == end_date._add_ymd(-y, -m, -d) and min(end_date, self).day < 29:
        #     raise AssertionError('%s!=%s==%s._add_ymd(%d,%d,%d)' %
        #                    (self, end_date._add_ymd(-y, -m, -d), end_date, -y,-m,-d))

        return int(y), int(m), int(d)

    # --- business day adjustment and day count fraction methods -----------------------------------------

    def get_day_count(self, end=None, convention=''):
        """ counts the days as a year fraction to given date following the specified convention.

        For more details on the conventions see module :mod:`businessdate.daycount`.
        """
        convention = convention if convention else BusinessDate.DAY_COUNT
        dc_func = self.__class__._dc_func
        return dc_func[convention.lower()](self.to_date(), BusinessDate(end).to_date())

    def get_year_fraction(self, end=None, convention=''):
        """ wrapper for :meth:`BusinessDate.get_day_count` method for different naming preferences """
        return self.get_day_count(end, convention)

    def adjust(self, convention='', holidays=None):
        """ returns an adjusted :class:`BusinessDate` if it was not a business day following the specified convention.

        For details on business days see :meth:`BusinessDate.is_business_day`.

        For more details on the conventions see module :mod:`businessdate.conventions`
        """
        convention = convention if convention else BusinessDate.ADJUST
        adj_func = self.__class__._adj_func
        holidays = self.__class__.DEFAULT_HOLIDAYS if holidays is None else holidays
        return BusinessDate(adj_func[convention.lower()](self.to_date(), holidays))


    def __getattr__(self, item):
        if item.startswith('adjust_'):
            return  lambda h=None: self.adjust(item.replace('adjust_',''), h)
        if item.startswith('get_'):
            return  lambda e: self.get_year_fraction(e, item.replace('get_',''))
        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, item))


# add additional __doc__ at runtime (during import)
try:
    s = '\n' \
        '        In order to get the year fraction according a day count convention \n' \
        '        provide one of the following convention key words: \n\n'
    for k, v in BusinessDate._dc_func.items():
         s +='           * ' + (":code:`%s`" % k).ljust(16) + '' + v.__doc__ + '\n\n'
    BusinessDate.get_day_count.__doc__ +=s

    s = '\n' \
        '        In order to adjust according a business day convention \n' \
        '        provide one of the following convention key words: \n\n'
    for k, v in BusinessDate._adj_func.items():
        s += '           * ' + (":code:`%s`" % k).ljust(16) + '' + v.__doc__ + '\n\n'
    BusinessDate.adjust.__doc__ +=s

    del s
except AttributeError:
    pass
