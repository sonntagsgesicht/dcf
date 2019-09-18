# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .interpolation import constant, linear
from .interpolationscheme import dyn_scheme
from .compounding import continuous_compounding, continuous_rate


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


class Curve(object):
    _interpolation = dyn_scheme(constant, linear, constant)

    def __init__(self, domain=(), data=(), interpolation=None):
        r"""
        Curve object to build function

        :param list(float) domain: source values
        :param list(float) data: target values
        :param function interpolation: interpolation function on x_list (optional), default is taken from class member _interpolation

            Curve object to build function :math:`f:R \rightarrow R, x \mapsto y`
            from finite point vectors :math:`x` and :math:`y`
            using piecewise various interpolation functions.
        """
        # sort data by domain values
        if not len(domain) == len(data):
            raise ValueError('%s requires equal length input for domain and data' % self.__class__.__name__)

        if domain:
            domain, data = map(list,zip(*sorted(zip(*(domain, data)))))

        if interpolation is None:
            interpolation = self.__class__._interpolation

        self._scheme = interpolation
        self._func = interpolation(domain, data)
        self._domain = domain

    @property
    def interpolation(self):
        return self._scheme

    @property
    def domain(self):
        return self._domain

    def __call__(self, x):
        if isinstance(x, (tuple, list)):
            return [self(xx) for xx in x]
        return self._func(x)

    def __add__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) + other(x) for x in x_list]
        return self.__class__(x_list, y_list, self.interpolation)

    def __sub__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) - other(x) for x in x_list]
        return self.__class__(x_list, y_list, self.interpolation)

    def __mul__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) * other(x) for x in x_list]
        return self.__class__(x_list, y_list, self.interpolation)

    def __truediv__(self, other):
        return self.__div__(other)

    def __div__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        if any(not other(x) for x in x_list):
            raise ZeroDivisionError("Division with %s requires on zero values." % other.__class__.__name__)
        y_list = [self(x) / other(x) for x in x_list]
        return self.__class__(x_list, y_list, self.interpolation)

    def __str__(self):
        return str([z for z in zip(self.domain, self(self.domain))])

    def __repr__(self):
        return self.__class__.__name__ + '(' + self.__str__() + ')'

    def shifted(self, delta=0.0):
        if delta:
            x_list = [x + delta for x in self.domain]
        else:
            x_list = self.domain
        y_list = self(self.domain)
        return self.__class__(x_list, y_list, self.interpolation)


class DateCurve(Curve):

    @staticmethod
    def _default_day_count(start, end):
        if hasattr(start, 'diff_in_days'):
            # duck typing businessdate.BusinessDate.diff_in_days
            d = start.diff_in_days(end)
        else:
            d = end - start
            if hasattr(d, 'days'):
                # assume datetime.date or finance.BusinessDate (else days as float)
                d = d.days
        return float(d) / 365.25

    _time_shift = '1d'

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None):
        self._origin = domain[0] if origin is None and domain else origin
        self._day_count = self._default_day_count if day_count is None else day_count
        flt_domain = [self._day_count(self._origin, x) for x in domain]
        super(DateCurve, self).__init__(flt_domain, data, interpolation)
        self._domain = domain

    @property
    def domain(self):
        """ domain of curve as list of dates where curve values are given """
        return self._domain

    @property
    def origin(self):
        """ date of origin (date zero) """
        return self._origin

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return [self(xx) for xx in x]
        return super(DateCurve, self).__call__(self.day_count(self.origin, x))

    def __add__(self, other):
        new = super(DateCurve, self).__add__(other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new.interpolation, self.origin, self._day_count)
        return new

    def __sub__(self, other):
        new = super(DateCurve, self).__sub__(other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new.interpolation, self.origin, self._day_count)
        return new

    def __mul__(self, other):
        new = super(DateCurve, self).__mul__(other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new.interpolation, self.origin, self._day_count)
        return new

    def __div__(self, other):
        new = super(DateCurve, self).__div__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def day_count(self, start, end):
        return self._day_count(start, end)

    def to_curve(self, origin=None):
        origin = self.origin if origin is None else origin
        x_list = [self.day_count(origin, x) for x in self.domain]
        y_list = self(self.domain)
        return Curve(x_list, y_list, self.interpolation)

    def integrate(self, start, stop):
        """ integrates curve and returns results as annualized rates """
        # try use result, error = scipy.integrate(self, start, stop)
        try:
            from scipy.integrate import quad
            #raise ImportError()
            s = self.day_count(self.origin, start)
            e = self.day_count(self.origin, stop)
            f = super(DateCurve, self).__call__
            value, error = quad(f, s, e)
        except ImportError:
            value = 0.0
            step = self.__class__._time_shift
            current = start
            while current + step < stop:
                value += self(current) * self.day_count(current, current + step)
                current += step
            value += self(current) * self.day_count(current, stop)
        result = value / self.day_count(start, stop)
        return result

    def derivative(self, start):
        # todo use scipy.misc.derivative(self, start, self.__class__._time_shift)
        try:
            from scipy.misc import derivative
            s = self.day_count(self.origin, start)
            dx = self.day_count(start, start + self.__class__._time_shift)
            f = super(DateCurve, self).__call__
            result = derivative(f, s, dx)
        except ImportError:
            stop = start + self.__class__._time_shift
            value = self(stop) - self(start)
            result = value / self.day_count(start, stop)
        return result


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
