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


from datetime import date, timedelta

from .ymd import from_excel_to_ymd, from_ymd_to_excel


class BaseDateFloat(float):
    """ native :class:`float` backed base class for a performing date calculations counting days since Jan, 1st 1900 """

    def __new__(cls, x=0):
        new = super(BaseDateFloat, cls).__new__(cls, x)
        new._ymd = None
        return new

    # --- property methods ---------------------------------------------------

    @property
    def day(self):
        if not self._ymd:
            self._ymd = self.to_ymd()
        return self._ymd[2]

    @property
    def month(self):
        if not self._ymd:
            self._ymd = self.to_ymd()
        return self._ymd[1]

    @property
    def year(self):
        if not self._ymd:
            self._ymd = self.to_ymd()
        return self._ymd[0]

    def weekday(self):
        return self.to_date().weekday()

    # --- constructor method -------------------------------------------------

    @classmethod
    def from_ymd(cls, year, month, day):
        """ creates instance from a :class:`tuple` of :class:`int` items `(year, month, day)` """
        return cls(from_ymd_to_excel(year, month, day))

    @classmethod
    def from_date(cls, d):
        """ creates instance from a :class:`datetime.date` object `d` """
        return cls.from_ymd(d.year, d.month, d.day)

    @classmethod
    def from_float(cls, x):
        """ creates from a :class:`float` `x` counting the days since Jan, 1st 1900 """
        return cls(x)

    # --- cast method --------------------------------------------------------

    def to_ymd(self):
        """ returns the :class:`tuple` of :class:`int` items `(year, month, day)` """
        if not self._ymd:
            self._ymd = from_excel_to_ymd(int(self))
        return self._ymd

    def to_date(self):
        """ returns `datetime.date(year, month, day)` """
        if not self._ymd:
            self._ymd = self.to_ymd()
        return date(*self._ymd)

    def to_float(self):
        """ returns :class:`float` counting the days since Jan, 1st 1900 """
        return float(self)

    # --- calculation methods ------------------------------------------------

    def _add_days(self, n):
        self._ymd = None
        return self.__class__(super(BaseDateFloat, self).__add__(n))

    def _diff_in_days(self, d):
        return super(BaseDateFloat, d).__sub__(float(self))


class BaseDateDatetimeDate(date):
    """ :class:`datetime.date` backed base class for a performing date calculations """

    # --- constructor method -------------------------------------------------

    @classmethod
    def from_ymd(cls, year, month, day):
        """ creates instance from a :class:`tuple` of :class:`int` items `(year, month, day)` """
        return cls(year, month, day)

    @classmethod
    def from_date(cls, d):
        """ creates instance from a :class:`datetime.date` object `d` """
        return cls.from_ymd(d.year, d.month, d.day)

    @classmethod
    def from_float(cls, x):
        """ creates from a :class:`float` `x` counting the days since Jan, 1st 1900 """
        y, m, d = from_excel_to_ymd(x)
        return cls.from_ymd(y, m, d)

    # --- cast method --------------------------------------------------------

    def to_ymd(self):
        """ returns the :class:`tuple` of :class:`int` items `(year, month, day)` """
        return self.year, self.month, self.day

    def to_date(self):
        """ returns `datetime.date(year, month, day)` """
        return date(*self.to_ymd())

    def to_float(self):
        """ returns :class:`float` counting the days since Jan, 1st 1900 """
        return float(from_ymd_to_excel(*self.to_ymd()))

    def to_serializable(self, *args, **kwargs):
        return str(self)

    # --- calculation methods ------------------------------------------------

    def _add_days(self, days_int):
        # return super(self.__class__, self).__add__(timedelta(days_int))
        res = super(BaseDateDatetimeDate, self).__add__(timedelta(days_int))
        return self.__class__.from_ymd(res.year, res.month, res.day)

    def _diff_in_days(self, end):
        delta = super(BaseDateDatetimeDate, end).__sub__(self)
        return float(delta.days)
