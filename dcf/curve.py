# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.6, copyright Monday, 20 December 2021
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from abc import ABC
from warnings import warn

from .compounding import continuous_compounding, continuous_rate
from .interpolation import constant, linear, dyn_scheme
from .day_count import day_count as _default_day_count


def rate_table(curve, x_grid=None, y_grid=None):
    r""" table of calculated rates

    :param curve: function
    :param x_grid:
    :param y_grid:
    :return: list(list(float))

    >>> from tabulate import tabulate
    >>> from dcf import Curve, rate_table
    >>> curve = Curve([1, 4], [0, 1])
    >>> table = rate_table(curve, x_grid=(0, 1, 2, 3, 4, 5), y_grid=(.0, .25, .5, .75))
    >>> print(tabulate(table, headers='firstrow', floatfmt='.4f'))
           0.0    0.25     0.5    0.75
    --  ------  ------  ------  ------
     0  0.0000  0.0000  0.0000  0.0000
     1  0.0000  0.0833  0.1667  0.2500
     2  0.3333  0.4167  0.5000  0.5833
     3  0.6667  0.7500  0.8333  0.9167
     4  1.0000  1.0000  1.0000  1.0000
     5  1.0000  1.0000  1.0000  1.0000


    >>> from businessdate import BusinessDate, BusinessPeriod
    >>> from dcf import ZeroRateCurve

    >>> term = '1m', '3m', '6m', '1y', '2y', '5y',
    >>> rates = -0.008, -0.0057, -0.0053, -0.0036, -0.0010, 0.0014,
    >>> today = BusinessDate(20211201)
    >>> tenor = BusinessPeriod('1m')
    >>> dates = [today + t for t in term]
    >>> f = ZeroRateCurve(dates, rates, origin=today, forward_tenor=tenor)

    >>> print(tabulate(f.table, headers='firstrow', floatfmt=".4f", tablefmt='latex'))
    \begin{tabular}{lrrrrrrr}
    \hline
              &      0D &      1M &      2M &      3M &      6M &      1Y &     2Y \\
    \hline
     20211201 & -0.0080 &         &         &         &         &         &        \\
     20220101 & -0.0080 & -0.0068 &         &         &         &         &        \\
     20220301 & -0.0057 & -0.0056 & -0.0054 &         &         &         &        \\
     20220601 & -0.0053 & -0.0050 & -0.0047 & -0.0044 &         &         &        \\
     20221201 & -0.0036 & -0.0034 & -0.0032 & -0.0030 & -0.0023 &         &        \\
     20231201 & -0.0010 & -0.0009 & -0.0009 & -0.0008 & -0.0006 & -0.0002 & 0.0006 \\
     20261201 &  0.0014 &  0.0014 &  0.0014 &  0.0014 &  0.0014 &  0.0014 & 0.0014 \\
    \hline
    \end{tabular}
    """  # noqa: E501
    if x_grid is None:
        x_grid = curve.domain
        if curve.origin not in curve.domain:
            x_grid = [curve.origin] + x_grid

    if y_grid is None:
        diff = list(e-s for s, e in zip(x_grid[:-1], x_grid[1:]))
        step = diff[0]
        y_grid = [step * 0]
        for span in diff:
            line = [step]
            while line[-1] + step < span:
                line.append(line[-1] + step)
            y_grid.extend(line)
            step = span
        y_grid = tuple(sorted(set(y_grid)))

    # fill table
    grid = list()
    grid.append(('',) + tuple(y_grid))
    for i, x in enumerate(x_grid):
        lst = x_grid[i+1] if i < len(x_grid)-1 \
            else x_grid[-1] + y_grid[-1] + y_grid[-1]
        grid.append(((x,) + tuple(curve(x+y) for y in y_grid if x + y < lst)))

    return grid


class Curve(object):
    _interpolation = dyn_scheme(constant, linear, constant)

    def __init__(self, domain=(), data=(), interpolation=None):
        r"""
        Curve object to build function

        :param list(float) domain: source values
        :param list(float) data: target values
        :param function interpolation:
            interpolation function on x_list (optional),
               default is taken from class member _interpolation

               Interpolation functions can be constructed piecewise
               using via |interpolation_scheme|.

            Curve object to build function
            :math:`f:R \rightarrow R, x \mapsto y`
            from finite point vectors :math:`x` and :math:`y`
            using piecewise various interpolation functions.
        """
        # cast/extract inputs from RateCurve if given as argument
        if isinstance(domain, DateCurve):
            interpolation = domain.interpolation \
                if interpolation is None else interpolation
            data = domain(domain.domain)
            domain = [domain.day_count(domain.origin, x)
                      for x in domain.domain]
        elif isinstance(data, DateCurve):
            interpolation = data.interpolation \
                if interpolation is None else interpolation
            data = data(domain)  # assuming data is a list of dates !
            domain = [data.day_count(data.origin, x) for x in domain]

        # sort data by domain values
        if not len(domain) == len(data):
            raise ValueError('%s requires equal length input '
                             'for domain and data' % self.__class__.__name__)

        if domain:
            domain, data = map(list, zip(*sorted(zip(*(domain, data)))))

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

    @property
    def table(self):
        """ table of interpolated rates """
        # print(tabulate(curve.table, headers='firstrow'))  # for pretty print
        return rate_table(self)

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
            raise ZeroDivisionError("Division with %s requires on "
                                    "zero values." % other.__class__.__name__)
        y_list = [self(x) / other(x) for x in x_list]
        return self.__class__(x_list, y_list, self.interpolation)

    def __str__(self):
        inner = ''
        if self.domain:
            s, e = self.domain[0], self.domain[-1]
            t = s, e, self(s), self(e)
            inner = '[%s ... %s], [%s ... %s]' % \
                    tuple(map(repr, t)) + self._args(', ')
        s = self.__class__.__name__ + '(' + inner + ')'
        return s

    def __repr__(self):
        start = self.__class__.__name__ + '('
        fill = ' ' * len(start)
        s = start + str(self.domain) + ',\n' + fill + \
            str(self(self.domain)) + self._args(',\n' + fill) + ')'
        return s

    def _args(self, sep=''):
        s = ''
        for name in 'interpolation', 'origin', 'day_count', 'forward_tenor':
            if hasattr(self, name):
                attr = getattr(self, name)
                attr = attr.__name__ \
                    if hasattr(attr, '__name__') else repr(attr)
                s += sep + name + '=' + attr
        return s

    def shifted(self, delta=0.0):
        if delta:
            x_list = [x + delta for x in self.domain]
        else:
            x_list = self.domain
        y_list = self(self.domain)
        return self.__class__(x_list, y_list, self.interpolation)


class DateCurve(Curve):
    _time_shift = '1d'
    DAY_COUNT = _default_day_count

    def __init__(self, domain=(), data=(), interpolation=None,
                 origin=None, day_count=None):
        self._origin = domain[0] if origin is None and domain else origin
        self._day_count = self.__class__.DAY_COUNT \
            if day_count is None else day_count
        flt_domain = [self.day_count(self._origin, x) for x in domain]
        super(DateCurve, self).__init__(flt_domain, data, interpolation)
        self._domain = domain
        self.fixings = dict()

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
        if x in self.fixings:
            return self.fixings[x]
        return super(DateCurve, self).__call__(self.day_count(self.origin, x))

    def __add__(self, other):
        new = super(DateCurve, self).__add__(
            other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new.interpolation,
                       self.origin, self._day_count)
        return new

    def __sub__(self, other):
        new = super(DateCurve, self).__sub__(
            other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new.interpolation,
                       self.origin, self._day_count)
        return new

    def __mul__(self, other):
        new = super(DateCurve, self).__mul__(
            other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new.interpolation,
                       self.origin, self._day_count)
        return new

    def __div__(self, other):
        new = super(DateCurve, self).__div__(
            other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def day_count(self, start, end):
        return self._day_count(start, end)

    def to_curve(self):
        return Curve(self)

    def integrate(self, start, stop):
        """ integrates curve and returns results as annualized rates """
        # try use result, error = scipy.integrate(self, start, stop)
        try:
            from scipy.integrate import quad
            # raise ImportError()
            s = self.day_count(self.origin, start)
            e = self.day_count(self.origin, stop)
            f = super(DateCurve, self).__call__
            value, *_ = quad(f, s, e)
        except ImportError:
            value = 0.0
            step = self.__class__._time_shift
            current = start
            while current + step < stop:
                value += self(current) * \
                         self.day_count(current, current + step)
                current += step
            value += self(current) * self.day_count(current, stop)
        result = value / self.day_count(start, stop)
        return result

    def derivative(self, start):
        # todo use
        #  scipy.misc.derivative(self, start, self.__class__._time_shift)
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


class RateCurve(DateCurve, ABC):
    _time_shift = '1D'
    _forward_tenor = '3M'

    @staticmethod
    def _get_storage_value(curve, x):
        raise NotImplementedError

    def cast(self, cast_type, **kwargs):
        cls = self.__class__.__name__
        msg = "\n%s().cast(cast_type, **kwargs) is deprecated.\n" \
              "Please use for casting an object `curve` of type %s\n" \
              " cast_type(curve, **kwargs)\n" \
              "instead." % (cls, cls)
        warn(msg)

        if 'domain' in kwargs:
            kwargs['data'] = self
        else:
            kwargs['domain'] = self
        return cast_type(**kwargs)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        """
            abstract base class for InterestRateCurve and CreditCurve

        :param domain: either curve points or a RateCurve
        :param data: either curve values or a RateCurve
        :param interpolation: (optional) interpolation scheme
        :param origin: (optional) curve points origin
        :param day_count: (optional) day count convention
        :param forward_tenor: (optional) forward rate tenor

        """

        other = None
        # either domain or data can be RateCurve too.
        # if given extract arguments for casting
        if isinstance(domain, RateCurve):
            if data:
                raise TypeError("If first argument is %s, "
                                "data argument must not be given." %
                                domain.__class__.__name__)
            other = domain
            domain = other.domain
        if isinstance(data, RateCurve):
            other = data
            domain = other.domain if domain is None else domain
        if other:
            # get data as self._get_storage_value
            data = [self._get_storage_value(other, x) for x in domain]
            # use other properties if not give explicitly
            # interpolation should default to class defaults
            # interpolation = other.interpolation
            #  if interpolation is None else interpolation
            origin = other.origin if origin is None else origin
            day_count = other.day_count if day_count is None else day_count
            forward_tenor = other.forward_tenor \
                if forward_tenor is None else forward_tenor

        super(RateCurve, self).__init__(
            domain, data, interpolation, origin, day_count)
        self.forward_tenor = self.__class__._forward_tenor \
            if forward_tenor is None else forward_tenor

    def __add__(self, other):
        new = super(RateCurve, self).__add__(self.__class__(other))
        new.forward_tenor = self.forward_tenor
        return new

    def __sub__(self, other):
        new = super(RateCurve, self).__sub__(self.__class__(other))
        new.forward_tenor = self.forward_tenor
        return new

    def __mul__(self, other):
        new = super(RateCurve, self).__mul__(self.__class__(other))
        new.forward_tenor = self.forward_tenor
        return new

    def __div__(self, other):
        new = super(RateCurve, self).__div__(self.__class__(other))
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
            return self._get_compounding_rate(
                start, start + self.__class__._time_shift)
        df = self._get_compounding_factor(start, stop)
        t = self.day_count(start, stop)
        return continuous_rate(df, t)
