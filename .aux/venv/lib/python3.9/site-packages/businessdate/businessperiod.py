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


from datetime import timedelta


class BusinessPeriod(object):

    def __init__(self, period='', years=0, quarters=0, months=0, weeks=0, days=0, businessdays=0):
        """ class to store and calculate date periods as combinations of days, weeks, years etc.

        :param str period: encoding a business period.
         Such is given by a sequence of digits as :class:`int` followed by a :class:`char` -
         indicating the number of
         years **Y**,
         quarters **Q** (which is equivalent to 3 month),
         month **M**,
         weeks **W** (which is equivalent to 7 days),
         days **D**,
         business days **B**.
         E.g. **1Y2W3D** what gives a period of 1 year plus 2 weeks and 3 days
         (see :doc:`tutorial <tutorial>` for details).

        :param int years: number of years in the period (equivalent to 12 months)
        :param int quarters: number of quarters in the period (equivalent to 3 months)
        :param int months: number of month in the period
        :param int weeks: number of weeks in the period (equivalent to 7 days)
        :param int days: number of days in the period
        :param int businessdays: number of business days,
         i.e. days which are neither weekend nor :class:`holidays <BusinessHolidays>`,  in the period.
         Only either `businessdays` or the others can be given.
         Both at the same time is not allowed.

        """
        if period and any((years, months, days, businessdays)):
            raise ValueError(
                "Either string or argument input only for %s" % self.__class__.__name__)

        super(BusinessPeriod, self).__init__()
        if isinstance(period, BusinessPeriod):
            years = period.years
            months = period.months
            days = period.days
            businessdays = period.businessdays
        elif isinstance(period, timedelta):
            days = period.days
        elif period is None:
            pass
        elif isinstance(period, str):
            if period.upper() == '':
                pass
            elif period.upper() == '0D':
                pass
            elif period.upper() == 'ON':
                businessdays = 1
            elif period.upper() == 'TN':
                businessdays = 2
            elif period.upper() == 'DD':
                businessdays = 3
            else:
                s, y, q, m, w, d, f = BusinessPeriod._parse_ymd(period)
                # no final businesdays allowed
                if f:
                    raise ValueError("Unable to parse %s as %s" % (period, self.__class__.__name__))
                # except the first non vanishing of y,q,m,w,d must have positive sign
                sgn = [int(x / abs(x)) for x in (y, q, m, w, d) if x]
                if [x for x in sgn[1:] if x < 0]:
                    raise ValueError(
                        "Except at the beginning no signs allowed in %s as %s" % (str(period), self.__class__.__name__))
                y, q, m, w, d = (abs(x) for x in (y, q, m, w, d))
                # use sign of first non vanishing of y,q,m,w,d
                sgn = sgn[0] if sgn else 1
                businessdays, years, quarters, months, weeks, days = s, sgn * y, sgn * q, sgn * m, sgn * w, sgn * d
        else:
            raise TypeError(
                "%s of Type %s not valid to create BusinessPeriod." %(str(period), period.__class__.__name__))

        self._months = 12 * years + 3 * quarters + months
        self._days = 7 * weeks + days
        self._businessdays = businessdays

        if businessdays and (self._months or self._days):
            raise ValueError(
                "Either (years,months,days) or businessdays must be zero for %s" % self.__class__.__name__)
        if self._months and not self._days / self._months >= 0:
            ymd = self.years, self.months, self.days
            raise ValueError(
                "(years, months, days)=%s must have equal sign for %s" % (str(ymd), self.__class__.__name__))

    @property
    def years(self):
        return int(-1 * (-1 * self._months // 12) if self._months < 0 else self._months // 12)

    @property
    def months(self):
        return int(-1 * (-1 * self._months % 12) if self._months < 0 else self._months % 12)

    @property
    def days(self):
        return int(self._days)

    @property
    def businessdays(self):
        return int(self._businessdays)

    # --- validation and information methods ---------------------------------

    @classmethod
    def _parse_ymd(cls, period):
        # can even parse strings like '-1B-2Y-4Q+5M' but also '0B', '-1Y2M3D' as well.
        period = period.upper().replace(' ', '')
        period = period.replace('BUSINESSDAYS', 'B')
        period = period.replace('YEARS', 'Y')
        period = period.replace('QUARTERS', 'Q')
        period = period.replace('MONTHS', 'M')
        period = period.replace('WEEKS', 'W')
        period = period.replace('DAYS', 'D')

        def _parse(p, letter):
            if p.find(letter) >= 0:
                s, p = p.split(letter, 1)
                s = s[1:] if s.startswith('+') else s
                sgn, s = (-1, s[1:]) if s.startswith('-') else (1, s)
                if not s.isdigit():
                    raise ValueError("Unable to parse %s in %s as %s" % (s, p, cls.__name__))
                return sgn * int(s), p
            return 0, p

        p = period.upper()

        # p[-1] is not 'B', p.strip('0123456789+-B')==''
        s, p = _parse(p, 'B') if not p[-1]=='B' else (0, p)
        s, p = _parse(p, 'B') if not p.strip('0123456789+-B') else (s, p)
        s, p = _parse(p, 'B') if p.count('B') > 1 else (s, p)
        y, p = _parse(p, 'Y')
        q, p = _parse(p, 'Q')
        m, p = _parse(p, 'M')
        w, p = _parse(p, 'W')
        d, p = _parse(p, 'D')
        f, p = _parse(p, 'B')
        if not p == '':
            raise ValueError("Unable to parse %s as %s" % (p, cls.__name__))
        return s, y, q, m, w, d, f

    @classmethod
    def is_businessperiod(cls, period):
        """ returns true if the argument can be understood as :class:`BusinessPeriod` """
        if period is None:
            return False
        if isinstance(period, (int, float, list, set, dict, tuple)):
            return False
        if isinstance(period, (timedelta, BusinessPeriod)):
            return True
        if period in ('', '0D', 'ON', 'TN', 'DD'):
            return True
        if isinstance(period, str):
            if period.isdigit():
                return False
            #if period.upper().strip('+-0123456789BYQMWD'):
            #    return False
            try:  # to be removed
                BusinessPeriod._parse_ymd(period)
            except ValueError:
                return False
            return True
        return False

    # --- operator methods ---------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__ + "('%s')" % str(self)

    def __str__(self):

        if self.businessdays:
            period_str = str(self.businessdays) + 'B'
        else:
            period_str = '-' if self.years < 0 or self.months < 0 or self.days < 0 else ''
            if self.years:
                period_str += str(abs(self.years)) + 'Y'
            if self.months:
                period_str += str(abs(self.months)) + 'M'
            if self.days:
                period_str += str(abs(self.days)) + 'D'

        if not period_str:
            period_str = '0D'
        return period_str

    def __abs__(self):
        ymdb = self.years, self.months, self.days, self.businessdays
        y,m,d,b = tuple(map(abs, ymdb))
        return self.__class__(years=y, months=m, days=d, businessdays=b)

    def __cmp__(self, other):
        other = self.__class__() if other == 0 else other
        if not isinstance(other, BusinessPeriod):
            other = BusinessPeriod(other)
        if self.businessdays:
            if other and not other.businessdays:
                # log warning on non compatible pair
                return None
            return self.businessdays - other.businessdays
        m = 12 * (self.years - other.years) + self.months - other.months
        d = self.days - other.days
        if m * 28 < -d < m * 31:
            p = self.__class__(months=m)
            if p.min_days() <= -d <= p.max_days():
                # log warning on non orderable pair
                return None
        return m * 30.5 + d

    def __eq__(self, other):
        if isinstance(other, type(self)):
            attr = 'years', 'months', 'days', 'businessdays'
            return all(getattr(self, a) == getattr(other, a) for a in attr)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        cmp = self.__cmp__(other)
        cmp = self.__cmp__(other + '1D') if cmp is None else cmp
        return cmp if cmp is None else cmp <= 0

    def __lt__(self, other):
        cmp = self.__cmp__(other)
        return cmp if cmp is None else cmp < 0

    def __ge__(self, other):
        lt = self.__lt__(other)
        return None if lt is None else not lt

    def __gt__(self, other):
        le = self.__le__(other)
        return None if le is None else not le

    def __hash__(self):
        return hash(repr(self))

    def __nonzero__(self):
        # return any((self.years, self.months, self.days, self.businessdays))
        return self.__bool__()

    def __bool__(self):
        # return self.__nonzero__()
        return any((self._months, self._days, self._businessdays))

    def __add__(self, other):
        if isinstance(other, (list, tuple)):
            return [self + o for o in other]
        if BusinessPeriod.is_businessperiod(other):
            p = BusinessPeriod(other)
            y = self.years + p.years
            m = self.months + p.months
            d = self.days + p.days
            b = self.businessdays + p.businessdays
            return self.__class__(years=y, months=m, days=d, businessdays=b)
        raise TypeError('addition of BusinessPeriod cannot handle objects of type %s.' % other.__class__.__name__)

    def __sub__(self, other):
        if isinstance(other, (list, tuple)):
            return [self - o for o in other]
        if BusinessPeriod.is_businessperiod(other):
            return self + (-1 * BusinessPeriod(other))
        raise TypeError('subtraction of BusinessPeriod cannot handle objects of type %s.' % other.__class__.__name__)

    def __mul__(self, other):
        if isinstance(other, (list, tuple)):
            return [self * o for o in other]
        if isinstance(other, int):
            m = other * self._months
            d = other * self._days
            b = other * self._businessdays
            return BusinessPeriod(months=m, days=d, businessdays=b)
        raise TypeError("expected int type but got %s" % other.__class__.__name__)

    def __rmul__(self, other):
        return self.__mul__(other)

    def max_days(self):
        if self._months < 0:
            sgn = -1
            days_in_month = 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28  # days from mar to feb forwards
        else:
            sgn = 1
            days_in_month = 31, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 28
        m = sgn * self._months
        # days from jan to feb backwards
        days = 0
        for i in range(m):
            days += days_in_month[int(i % 12)]
            days += 1 if int(i % 48) == 11 else 0
        return sgn * days + self._days

    def min_days(self):
        if self._months < 0 :
            sgn = -1
            days_in_month = 28, 31, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 # days from feb to jan backwards
        else:
            sgn = 1
            days_in_month = 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31 # days from feb to jan forwards
        m  = sgn * self._months
        days = 0
        for i in range(m):
            days += days_in_month[int(i % 12)]
            days += 1 if int(i % 48) == 36 else 0
        return sgn * days + self._days
