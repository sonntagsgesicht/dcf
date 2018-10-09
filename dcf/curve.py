# -*- coding: utf-8 -*-

#  dcf (discounted cashflow)
#  -------------------------
#  A Python library for generating discounted cashflows.
#  Typical banking business methods are provided like interpolation, compounding,
#  discounting and fx.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Copyright: 2016, 2017 Deutsche Postbank AG
#  Website: https://github.com/pbrisk/dcf
#  License: APACHE Version 2 License (see LICENSE file)


from interpolation import base_interpolation, constant, linear
from compounding import continuous_compounding, continuous_rate


def DAY_COUNT(start, end):
    if hasattr(start, 'diff_in_years'):
        # duck typing businessdate.BusinessDate.diff_in_years
        return start.diff_in_years(end)
    else:
        d = end - start
        if hasattr(d, 'days'):
            # assume datetime.date or finance.BusinessDate (else days as float)
            d = d.days
        return float(d) / 365.25


class Curve(object):

    _interpolation = constant(), linear(), constant()

    def __init__(self, domain=(), data=(), interpolation=None):
        r"""
        Curve object to build function

        :param list(float) domain: source values
        :param list(float) data: target values
        :param list(interpolation) interpolation: interpolation function on x_list (optional)
            or triple of (left, mid, right) interpolation functions with
            left for x < x_list[0] (as default triple.right is used)
            right for x > x_list][-1] (as default constant is used)
            mid else (as default linear is used)

        Curve object to build function :math:`f:R \rightarrow R, x \mapsto y`
        from finite point vectors :math:`x` and :math:`y`
        using piecewise various interpolation functions.
        """
        if not interpolation:
            interpolation = self.__class__._interpolation

        y_left, y_mid, y_right = self.__class__._interpolation
        if isinstance(interpolation, (tuple, list)):
            if len(interpolation) == 3:
                y_left, y_mid, y_right = interpolation
            elif len(interpolation) == 2:
                y_mid, y_right = interpolation
                y_left = y_right
            elif len(interpolation) == 1:
                y_mid, = interpolation
            else:
                raise ValueError
        elif isinstance(interpolation, base_interpolation):
            y_mid = interpolation
        else:
            raise (AttributeError, str(interpolation) + " is not a proper ")

        assert len(domain) == len(data)
        assert len(domain) == len(set(domain))

        #: Interpolation:
        self._y_mid = type(y_mid)(domain, data)
        self._y_right = type(y_right)(domain, data)
        self._y_left = type(y_left)(domain, data)

    @property
    def interpolation(self):
        return self._y_left, self._y_mid, self._y_right

    @property
    def domain(self):
        return self._y_mid.x_list

    def __call__(self, x):
        if isinstance(x, (tuple, list)):
            return [self(xx) for xx in x]
        y = 0.0
        if x < self._y_left.x_list[0]:
            # extrapolate to left
            y = self._y_left(x)
        elif x > self._y_right.x_list[-1]:
            # extrapolate to right
            y = self._y_right(x)
        else:
            # interpolate in the middle
            y = self._y_mid(x)
        return y

    def __add__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) + other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __sub__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) - other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __mul__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) * other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __div__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        if any(not other(x) for x in x_list):
            raise ZeroDivisionError("Division with %s requires on zero values." % other.__class__.__name__)
        y_list = [self(x) / other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __str__(self):
        return str([z for z in zip(self.domain, self(self.domain))])

    def __repr__(self):
        return self.__class__.__name__ + '(' + self.__str__() + ')'

    def update(self, x_list=list(), y_list=list()):
        self._y_left.update(x_list, y_list)
        self._y_mid.update(x_list, y_list)
        self._y_right.update(x_list, y_list)

    def shifted(self, delta=0.0):
        if delta:
            x_list = [x + delta for x in self.domain]
        else:
            x_list = self.domain
        y_list = self(self.domain)
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))


class DateCurve(Curve):
    _time_shift = '1d'

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None):
        self.origin = domain[0] if origin is None and domain else origin
        self.day_count = DAY_COUNT if day_count is None else day_count
        super(DateCurve, self).__init__([self.day_count(self.origin, x) for x in domain], data, interpolation)
        self._domain = domain

    @property
    def domain(self):
        return self._domain

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return [self(xx) for xx in x]
        return super(DateCurve, self).__call__(self.day_count(self.origin, x))

    def __add__(self, other):
        new = super(DateCurve, self).__add__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def __sub__(self, other):
        new = super(DateCurve, self).__sub__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def __mul__(self, other):
        new = super(DateCurve, self).__mul__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def __div__(self, other):
        new = super(DateCurve, self).__div__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def to_curve(self):
        x_list = self.domain
        y_list = self([self.day_count(self.origin, x) for x in x_list])
        return Curve(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def update(self, x_list=list(), y_list=list()):
        if y_list:
            for x in x_list:
                if x not in self._domain:
                    self._domain.append(x)
            self._domain = sorted(self._domain)

            super(DateCurve, self).update([self.day_count(self.origin, x) for x in x_list], y_list)

    def integrate(self, start, stop):
        # todo use `result, error = scipy.integrate(self, start, stop)
        value = 0.0
        step = self.__class__._time_shift
        current = start
        while current + step < stop:
            value += self(current) * self.day_count(current, current + step)
            current += step
        value += self(current) * self.day_count(current, stop)
        return value / self.day_count(start, stop)

    def diff(self, start):
        # todo use `scipy`
        stop = start + self.__class__._time_shift
        value = self(stop) - self(start)
        return value / self.day_count(start, stop)


class RateCurve(DateCurve):

    _time_shift = '1D'
    _forward_tenor = '3M'

    @staticmethod
    def get_storage_type(curve, x):
        raise NotImplementedError

    def cast(self, cast_type, **kwargs):
        new = cast_type(kwargs.get('domain', self.domain),
                        [cast_type.get_storage_type(self, x) for x in kwargs.get('domain', self.domain)],
                        kwargs.get('interpolation', None),
                        kwargs.get('origin', self.origin),
                        kwargs.get('day_count', self.day_count),
                        kwargs.get('forward_tenor', self.forward_tenor))
        return new

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None, forward_tenor=None):
        super(RateCurve, self).__init__(domain, data, interpolation, origin, day_count)
        self.forward_tenor = self.__class__._forward_tenor if forward_tenor is None else forward_tenor

    def __add__(self, other):
        casted = other.cast(self.__class__)
        new = super(RateCurve, self).__add__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def __sub__(self, other):
        casted = other.cast(self.__class__)
        new = super(RateCurve, self).__sub__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def __mul__(self, other):
        casted = other.cast(self.__class__)
        new = super(RateCurve, self).__mul__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def __div__(self, other):
        casted = other.cast(self.__class__)
        new = super(RateCurve, self).__div__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def _get_compounding_factor(self, start, stop):
        if start == stop:
            return 1.
        ir = self._get_compounding_rate(start, stop)
        t = self.day_count(start, stop)
        return continuous_compounding(ir, t)

    def _get_compounding_rate(self, start, stop):
        if start == stop:
            return self._get_compounding_rate(start, start + self.__class__._time_shift)
        df = self._get_compounding_factor(start, stop)
        t = self.day_count(start, stop)
        return continuous_rate(df, t)
