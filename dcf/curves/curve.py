# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Wednesday, 11 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from collections import OrderedDict
from inspect import signature
from math import exp
from warnings import warn

from .. import interpolation as _interpolations
from ..compounding import continuous_compounding, continuous_rate
from ..interpolation import linear_scheme, log_linear_scheme
from ..daycount import day_count as _default_day_count


def rate_table(curve, x_grid=None, y_grid=None):
    r""" table of calculated rates

    :param curve: function $f$
    :param x_grid: vertical date axis $x_0, \dots, x_m$
    :param y_grid: horizontal period axis $y_1, \dots, y_n$
        (implicitly added a non-period $y_0=0$)
    :return: list(list(float)) matrix $T=(t_{i,j})$ with
        $t_{i,j}=f(x_i+y_j) \text{ if } x_i+y_j < x_{i+1}$.

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
        x_grid = list(curve.domain)
        if curve.origin not in x_grid:
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


class Price(object):
    """Price object for assets"""

    @property
    def value(self):
        """ asset price value """
        return float(self._value)

    @property
    def origin(self):
        """ asset price date """
        return self._origin

    def __init__(self, value=0., origin=None):
        r"""
        :param value: price value
        :param origin: price date

        >>> from businessdate import BusinessDate
        >>> from dcf import Price
        >>> p=Price(100, BusinessDate(20201212))
        >>> p.value
        100.0
        >>> float(p)
        100.0
        >>> p
        Price(100.000000; origin=BusinessDate(20201212))

        """
        self._value = value
        self._origin = origin

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return '%s(%f; origin=%s)' % \
               (self.__class__.__name__, self.value, repr(self.origin))

    def __repr__(self):
        return str(self)


class Curve(object):
    """Curve function object"""
    INTERPOLATIONS = dict()
    """mapping (dict) of availiable interpolations
        additional to |dcf.interpolation|"""

    _INTERPOLATION = linear_scheme  # default interpolation

    @property
    def kwargs(self):
        """ returns constructor arguments as ordered dictionary """
        kw = type(self.__class__.__name__ + 'Kwargs', (OrderedDict,), {})()
        for name in signature(self.__class__).parameters:
            attr = self(self.domain) if name == 'data' else None
            attr = getattr(self, '_' + name, attr)
            attr = getattr(attr, '__name__', attr)
            if attr is not None:
                kw[name] = attr
            setattr(kw, name, attr)
        return kw

    @property
    def domain(self):
        """coordinates and date of given (not interpolated) x-values"""
        return self._domain

    @property
    def table(self):
        r""" table of interpolated rates (pretty printable)
        given by |rate_table()|.
        """

        # print(tabulate(curve.table, headers='firstrow'))  # for pretty print
        return rate_table(self)

    def __init__(self, domain=(), data=(), interpolation=None):
        r"""
        :param list(float) domain: source values $x_1 \dots x_n$
        :param list(float) data: target values $y_1 \dots y_n$
        :param function interpolation:
            (optional, default is defined on class level)

            Interpolation function $\gamma$
            such that $\gamma(x_i)=y_i$ for $i=1 \dots n$.

            If **interpolation** is a string,
            the interpolation function is
            taken from class member dictionary |Curve.INTERPOLATIONS|.

            Interpolation functions $\gamma$ can be constructed piecewise
            using via |interpolation_scheme|.

        Curve function object
        $$f:\mathbb{R} \rightarrow \mathbb{R}, x \mapsto f(x)=y$$
        build from finite point vectors $x$ and $y$
        using piecewise various interpolation functions.

        >>> from dcf import Curve
        >>> c = Curve([0, 1, 2], [1, 2, 3])

        get the grid of x values

        >>> c.domain
        [0, 1, 2]

        get the grid of y values

        >>> c(c.domain)
        (1.0, 2.0, 3.0)

        get a interpolated curve value

        >>> c(1.5)
        2.5

        update existing values

        >>> c[2] = 4
        >>> c(c.domain)
        (1.0, 2.0, 4.0)

        add new points

        >>> c[3] = 5
        >>> c(c.domain)
        (1.0, 2.0, 4.0, 5.0)

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
                             'for domain (%d) and data (%d) ' %
                             (self.__class__.__name__, len(domain), len(data)))

        self._interpolation = interpolation
        self._update(domain, data)

    def _update(self, domain, data):
        interpolation = self._interpolation
        if interpolation in self.INTERPOLATIONS:
            func = self.INTERPOLATIONS[interpolation]
        elif interpolation is None:
            func = self._INTERPOLATION
        else:
            func = vars(_interpolations).get(interpolation, interpolation)
        if domain:
            domain, data = map(list, zip(*sorted(zip(*(domain, data)))))
        self._func = func(domain, data)
        self._domain = domain

    def __contains__(self, item):
        return item in self.domain

    def __iter__(self):
        return self.domain

    def __getitem__(self, item):
        if item in self:
            return self(item)
        raise KeyError(item)

    def __setitem__(self, key, value):
        domain = list(self.domain)
        data = list(self(domain))
        if key in domain:
            data[domain.index(key)] = value
        else:
            domain.append(key)
            data.append(value)
        self._update(domain, data)

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
        """ build curve object with shifted **domain** by **delta**

        :param delta: shift size
        :return: curve object with shifted **domain** by **delta**
        """
        if delta:
            x_list = [x + delta for x in self.domain]
        else:
            x_list = self.domain
        # y_list = self(self.domain)
        # return self.__class__(x_list, y_list, self.interpolation)
        return self.__class__(x_list, self)


class DateCurve(Curve):
    """Curve function object with dates as domain (points)"""

    DAY_COUNT = dict()
    """mapping (dict) of availiable day count functions
        additional to |dcf.daycount|"""

    _TIME_SHIFT = '1D'
    """default time shift"""

    def __init__(self, domain=(), data=(), interpolation=None,
                 origin=None, day_count=None):
        """curve function object with dates as domain (points)

        :param domain: squences of date points
        :param data: squence of curve values
        :param interpolation: interpolation function
            (see |Curve|)
        :param origin: inital origin of date points
            (used to calculate year fractions of poins in domain)
        :param day_count: day count function
            to derive year fractions from time periods

        >>> from dcf import DateCurve

        **domain** given as date/time measured in year fraction (float)

        >>> domain = 0.5, 1.0, 1.5, 2.0
        >>> data = 1, 2, 3, 4

        >>> c = DateCurve(domain, data)
        >>> c.domain
        (0.5, 1.0, 1.5, 2.0)

        >>> c(0.75)
        1.5

        **domain** given as date/time measured in dates (date)

        >>> from datetime import date

        >>> domain = date(2022, 8, 12), date(2023, 2, 12), date(2023, 8, 12), date(2024, 2, 12)
        >>> data = 1, 2, 3, 4

        >>> c = DateCurve(domain, data)
        >>> c.domain
        (datetime.date(2022, 8, 12), datetime.date(2023, 2, 12), datetime.date(2023, 8, 12), datetime.date(2024, 2, 12))

        >>> c(date(2022, 11, 12))
        1.5

        **domain** given as date/time measured in dates (BusinessDate)

        >>> from businessdate import BusinessDate
        >>> t = BusinessDate(20220212)

        >>> domain = tuple(t + p for p in ('6m', '12m', '18m', '24m'))
        >>> data = 1, 2, 3, 4

        >>> c = DateCurve(domain, data)
        >>> c.domain
        (BusinessDate(20220812), BusinessDate(20230212), BusinessDate(20230812), BusinessDate(20240212))

        >>> c(t + '9m')
        1.5

        """  # noqa 501
        if isinstance(domain, DateCurve):
            data = domain
            domain = data.domain
        elif isinstance(data, DateCurve):
            interpolation = interpolation or data.kwargs.interpolation
            origin = origin or data.kwargs.origin
            day_count = day_count or data.kwargs.day_count
            data = data(domain)  # assuming data is a list of dates !

        self._domain = domain
        self._origin = origin
        self._day_count = day_count
        super().__init__(domain, data, interpolation)
        self.fixings = dict()

    @property
    def domain(self):
        r""" domain of curve $t_1 \dots t_n$ as list of dates
        where curve values are given explicit """
        return self._domain

    @property
    def origin(self):
        """ date of origin (date zero)
        as curve reference date for time calucations """
        if self._origin is not None:
            return self._origin
        return self._domain[0] if self._domain else None

    def _update(self, domain, data):
        flt_domain = tuple(self.day_count(d) for d in domain)
        super()._update(flt_domain, data)
        self._domain = domain

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
        """ day count function to calculate a year fraction of time period

        :param start: first date of period
        :param end: last date of period
        :return: (float) year fraction
        """
        if end is None:
            return self.day_count(self.origin, start)
        if self._day_count is None:
            return _default_day_count(start, end)
        if self._day_count in self.DAY_COUNT:
            day_count = self.DAY_COUNT.get(self._day_count)
            return day_count(start, end)
        return self._day_count(start, end)

    def to_curve(self):
        """deprecated method to cast to |Curve()| object"""
        cls = self.__class__.__name__
        msg = "\n%s().cast(cast_type, **kwargs) is deprecated.\n" \
              "Please use for casting an object `curve` of type %s\n" \
              " cast_type(curve, **kwargs)\n" \
              "instead." % (cls, cls)
        warn(msg)
        return Curve(self)

    def integrate(self, start, stop):
        r""" integrates curve and returns results as annualized rates

        :param start: lower integration boundary
        :param stop: upper integration boundary
        :return: (float) integral value$

        If $\gamma$ is this the curve. **integrate** returns
        $$\int_a^b \gamma(t)\ dt$$
        where $a$ is **start** and $b$ is **stop**.

        if available **integrate** uses
        `scipy.integrate.quad <https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.quad.html>`_

        """  # noqa E501

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
        r""" calculates numericaly the first derivative

        :param start: curve point to calcuate derivative at this point
        :return: (float) first derivative

        If $\gamma$ is this the curve **derivative** returns
        $$\frac{d}{dt}\gamma(t)$$
        where $t$ is **start** but derived numericaly.

        if available **derivative** uses
        `scipy.misc.derivative <https://docs.scipy.org/doc/scipy/reference/generated/scipy.misc.derivative.html>`_

        """  # noqa E501

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


class ForwardCurve(DateCurve):
    """Forward price curve with yield extrapolation """
    _INTERPOLATION = log_linear_scheme

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, yield_curve=0.0):
        r""" curve of future asset prices i.e. asset forward prices

        :param domain: dates of given asset prices $t_1 \dots t_n$
        :param data: actual asset prices $p_{t_1} \dots p_{t_n}$
        :param interpolation: interpolation method
            for interpolating given asset prices
        :param origin: origin of curve
        :param day_count: day count method resp. function $\tau$
            to calculate year fractions
        :param yield_curve: yield $y$ to extrapolate by continous compounding
            $$p_T = p_{t_n} \cdot \exp(y \cdot \tau(t_n, T))$$
            or yield curve function $\gamma_c$ to extrapolate by
            $$p_T = p_{t_n} \cdot \gamma_c(T)/\gamma_c(t_n)$$
            or interest rate curve $c$ extrapolate by
            $$p_T = p_{t_n} \cdot df_{c}^{-1}(t_n, T)$$

        """
        if not data:
            if isinstance(domain, float):
                # build lists from single spot price value
                data = [domain]
                domain = [origin]
            elif isinstance(domain, Price):
                # build lists from single spot price
                origin = domain.origin
                data = [domain.value]
                domain = [domain.origin]
        super().__init__(domain, data, interpolation, origin, day_count)
        if isinstance(yield_curve, float) and self.origin is not None:
            yc = (lambda x: exp(-self.day_count(x) * yield_curve))
        else:
            yc = yield_curve
        self.yield_curve = yc
        """ yield curve for extrapolation using discount factors """

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return [self(xx) for xx in x]
        else:
            return self.get_forward_price(x)

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: future date of asset price
        :return: asset forward price at **value_date**
        """
        last_date = self.domain[-1]
        if value_date <= last_date:
            return super().__call__(value_date)
        last_price = super().__call__(last_date)
        if self.yield_curve is None:
            df = 1.0
        elif hasattr(self.yield_curve, 'get_discount_factor'):
            df = self.yield_curve.get_discount_factor(last_date, value_date)
        else:
            df = self.yield_curve(value_date) / self.yield_curve(last_date)

        return last_price / df


class RateCurve(DateCurve):
    """Interest rate curve and credit curve"""
    _FORWARD_TENOR = '3M'

    @staticmethod
    def _get_storage_value(curve, x):
        raise NotImplementedError()

    def cast(self, cast_type, **kwargs):
        """deprecated method to cast a curve"""
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
        """tenor (time period) associated to the rates of the curve"""
        return self._FORWARD_TENOR \
            if self._forward_tenor is None else self._forward_tenor

    @property
    def spread(self):
        """spread curve to add spreads to curve"""
        return self._spread

    @spread.setter
    def spread(self, curve):
        """spread curve to add spreads to curve"""
        if curve is not None and self._spread is not None:
            raise TypeError("direct re-setting of spread curve not allowed."
                            "first re-set spread curve to None.")
        self._spread = curve

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        r"""
        :param domain: either curve points $t_1 \dots t_n$
            or a curve object $C$
        :param data: either curve values $y_1 \dots y_n$
            or a curve object $C$
        :param interpolation: (optional) interpolation scheme
        :param origin: (optional) curve points origin $t_0$
        :param day_count: (optional) day count convention function $\tau(s, t)$
        :param forward_tenor: (optional) forward rate tenor period $\tau^*$

        If **data** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given by **domain**.

        If **domain** is a |RateCurve| instance $C$,
        it is casted to this new class type
        with domain grid given **domain** property of $C$.

        Further arguments
        **interpolation**, **origin**, **day_count**, **forward_tenor**
        will replace the ones given by $C$ if not given explictly.

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
            # interpolation = \
            #     interpolation or other.kwargs.get('interpolation', None)
            origin = origin or other.kwargs.origin
            day_count = day_count or other.kwargs.day_count

        super(RateCurve, self).__init__(
            domain, data, interpolation, origin, day_count)
        self._forward_tenor = forward_tenor
        self._spread = None

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return tuple(self(xx) for xx in x)
        s = self._spread(x) if self._spread else 0.0
        return super().__call__(x) + s

    def __add__(self, other):
        new = super(RateCurve, self).__add__(self.__class__(other))
        return self.__class__(new, forward_tenor=self._forward_tenor)

    def __sub__(self, other):
        new = super(RateCurve, self).__sub__(self.__class__(other))
        return self.__class__(new, forward_tenor=self._forward_tenor)

    def __mul__(self, other):
        new = super(RateCurve, self).__mul__(self.__class__(other))
        return self.__class__(new, forward_tenor=self._forward_tenor)

    def __div__(self, other):
        new = super(RateCurve, self).__div__(self.__class__(other))
        return self.__class__(new, forward_tenor=self._forward_tenor)

    def _get_compounding_factor(self, start, stop):
        # aka discount factor
        if start == stop:
            return 1.
        ir = self._get_compounding_rate(start, stop)
        t = self.day_count(start, stop)
        return continuous_compounding(ir, t)

    def _get_compounding_rate(self, start, stop):
        # aka zero rate
        if start == stop:
            return self._get_compounding_rate(
                start, start + self._TIME_SHIFT)
        df = self._get_compounding_factor(start, stop)
        t = self.day_count(start, stop)
        return continuous_rate(df, t)
