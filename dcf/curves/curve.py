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
from collections import OrderedDict
from inspect import signature
from warnings import warn

from ..base import interpolation as _interpolations
from ..base.compounding import continuous_compounding, continuous_rate
from ..base.interpolation import linear_scheme
from ..base.day_count import day_count as _default_day_count


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
    INTERPOLATION = vars(_interpolations)
    _INTERPOLATION = linear_scheme

    def __init__(self, domain=(), data=(), interpolation=None):
        r"""
        Curve object to build function

        :param list(float) domain: source values
        :param list(float) data: target values
        :param function interpolation:
            interpolation function on x_list (optional),
               default is taken from class member _INTERPOLATION

               Interpolation functions can be constructed piecewise
               using via |interpolation_scheme|.

            Curve object to build function
            :math:`f:R \rightarrow R, x \mapsto y`
            from finite point vectors :math:`x` and :math:`y`
            using piecewise various interpolation functions.
        """
        # cast/extract inputs from Curve if given as argument
        if isinstance(domain, Curve):
            data = domain
            domain = data.domain
        if isinstance(data, Curve):
            interpolation = \
                interpolation or data.kwargs.get('interpolation', None)
            _data = data(domain)  # assuming domain is a list of dates !
            if isinstance(data, DateCurve):
                domain = [data.day_count(d) for d in domain]
            data = _data

        # sort data by domain values
        if not len(domain) == len(data):
            raise ValueError('%s requires equal length input '
                             'for domain and data' % self.__class__.__name__)
        if domain:
            domain, data = map(list, zip(*sorted(zip(*(domain, data)))))

        if interpolation is None:
            self._func = self._INTERPOLATION(domain, data)
        else:
            func = self.INTERPOLATION.get(interpolation, interpolation)
            self._func = func(domain, data)
        self._interpolation = interpolation
        self._domain = domain

    @property
    def kwargs(self):
        kw = OrderedDict()
        for name in signature(self.__class__).parameters:
            attr = self(self.domain) if name == 'data' else None
            attr = getattr(self, '_' + name, attr)
            attr = getattr(attr, '__name__', attr)
            if attr is not None:
                kw[name] = attr
        return kw

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
            return tuple(self(xx) for xx in x)
        return self._func(x)

    def __add__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) + other(x) for x in x_list]
        return self.__class__(x_list, y_list, self._interpolation)

    def __sub__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) - other(x) for x in x_list]
        return self.__class__(x_list, y_list, self._interpolation)

    def __mul__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) * other(x) for x in x_list]
        return self.__class__(x_list, y_list, self._interpolation)

    def __truediv__(self, other):
        return self.__div__(other)

    def __div__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        if any(not other(x) for x in x_list):
            raise ZeroDivisionError("Division with %s requires on "
                                    "zero values." % other.__class__.__name__)
        y_list = [self(x) / other(x) for x in x_list]
        return self.__class__(x_list, y_list, self._interpolation)

    def __str__(self):
        inner = tuple()
        if self.domain:
            s, e = self.domain[0], self.domain[-1]
            inner = f'[{s!r} ... {e!r}]', f'[{self(s)!r} ... {self(e)!r}]'
        kw = self.kwargs
        kw.pop('data')
        kw.pop('domain')
        inner += tuple(f"{k!s}={v!r}" for k, v in kw.items())
        s = self.__class__.__name__ + '(' + ', '.join(inner) + ')'
        return s

    def __repr__(self):
        s = self.__class__.__name__ + '()'
        if self.domain:
            fill = ',\n' + ' ' * (len(s) - 1)
            kw = self.kwargs
            inner = str(kw.pop('domain')), str(kw.pop('data'))
            inner += tuple(f"{k!s}={v!r}" for k, v in kw.items())
            s = self.__class__.__name__ + '(' + fill.join(inner) + ')'
        return s

    def shifted(self, delta=0.0):
        if delta:
            x_list = [x + delta for x in self.domain]
        else:
            x_list = self.domain
        y_list = self(self.domain)
        return self.__class__(x_list, y_list, self.interpolation)


class DateCurve(Curve):
    _TIME_SHIFT = '1d'
    _DAY_COUNT = _default_day_count

    DAY_COUNT = dict()

    def __init__(self, domain=(), data=(), interpolation=None,
                 origin=None, day_count=None):
        if isinstance(domain, DateCurve):
            data = domain
            domain = data.domain
        elif isinstance(data, DateCurve):
            interpolation = \
                interpolation or data.kwargs.get('interpolation', None)
            origin = \
                origin or data.kwargs.get('origin', None)
            day_count = \
                day_count or data.kwargs.get('day_count', None)
            data = data(domain)  # assuming data is a list of dates !

        self._domain = domain
        self._origin = origin
        self._day_count = day_count
        flt_domain = [self.day_count(x) for x in domain]
        super(DateCurve, self).__init__(flt_domain, data, interpolation)
        self._domain = domain  # since super sets domain too
        self.fixings = dict()

    @property
    def domain(self):
        """ domain of curve as list of dates where curve values are given """
        return self._domain

    @property
    def origin(self):
        """ date of origin (date zero) """
        return self._domain[0] if self._origin is None else self._origin

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return tuple(self(xx) for xx in x)
        if x in self.fixings:
            return self.fixings[x]
        return super(DateCurve, self).__call__(self.day_count(x))

    def __add__(self, other):
        new = super(DateCurve, self).__add__(
            other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new._interpolation,
                       self.origin, self._day_count)
        return new

    def __sub__(self, other):
        new = super(DateCurve, self).__sub__(
            other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new._interpolation,
                       self.origin, self._day_count)
        return new

    def __mul__(self, other):
        new = super(DateCurve, self).__mul__(
            other.shifted(self.origin - other.origin))
        self.__class__(new.domain, new(new.domain), new._interpolation,
                       self.origin, self._day_count)
        return new

    def __div__(self, other):
        new = super(DateCurve, self).__div__(
            other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def day_count(self, start, end=None):
        if end is None:
            return self.day_count(self.origin, start)
        if self._day_count is None:
            return self.__class__._DAY_COUNT(start, end)
        day_count = self.DAY_COUNT.get(self._day_count, self._day_count)
        return day_count(start, end)

    def to_curve(self):
        return Curve(self)

    def integrate(self, start, stop):
        """ integrates curve and returns results as annualized rates """
        # try use result, error = scipy.integrate(self, start, stop)
        try:
            from scipy.integrate import quad
            # raise ImportError()
            s = self.day_count(start)
            e = self.day_count(stop)
            f = super(DateCurve, self).__call__
            value, *_ = quad(f, s, e)
        except ImportError:
            value = 0.0
            step = self._TIME_SHIFT
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
        #  scipy.misc.derivative(self, start, self._TIME_SHIFT)
        try:
            from scipy.misc import derivative
            s = self.day_count(start)
            dx = self.day_count(start, start + self._TIME_SHIFT)
            f = super(DateCurve, self).__call__
            result = derivative(f, s, dx)
        except ImportError:
            stop = start + self._TIME_SHIFT
            value = self(stop) - self(start)
            result = value / self.day_count(start, stop)
        return result


class RateCurve(DateCurve, ABC):
    _TIME_SHIFT = '1D'
    _FORWARD_TENOR = '3M'

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

    @property
    def forward_tenor(self):
        return self._FORWARD_TENOR \
            if self._forward_tenor is None else self._forward_tenor

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

        super(RateCurve, self).__init__(
            domain, data, interpolation, origin, day_count)
        self._forward_tenor = forward_tenor

    def __add__(self, other):
        new = super(RateCurve, self).__add__(self.__class__(other))
        new.forward_tenor = self._forward_tenor
        return new

    def __sub__(self, other):
        new = super(RateCurve, self).__sub__(self.__class__(other))
        new.forward_tenor = self._forward_tenor
        return new

    def __mul__(self, other):
        new = super(RateCurve, self).__mul__(self.__class__(other))
        new.forward_tenor = self._forward_tenor
        return new

    def __div__(self, other):
        new = super(RateCurve, self).__div__(self.__class__(other))
        new.forward_tenor = self._forward_tenor
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
                start, start + self._TIME_SHIFT)
        df = self._get_compounding_factor(start, stop)
        t = self.day_count(start, stop)
        return continuous_rate(df, t)