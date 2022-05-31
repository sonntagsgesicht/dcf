# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from dcf.compounding import continuous_rate, simple_compounding, simple_rate
from dcf.interpolation import constant, linear_scheme, \
    log_linear_rate_scheme
from .curve import RateCurve


class InterestRateCurve(RateCurve):
    r"""Base class of interest rate curve classes

    All interest rate curves share the same
    four fundamental methodological methods

    * |InterestRateCurve().get_discount_factor()|

    * |InterestRateCurve().get_zero_rate()|

    * |InterestRateCurve().get_cash_rate()|

    * |InterestRateCurve().get_short_rate()|

    * |InterestRateCurve().get_swap_annuity()|

    All subclasses differ only in data types for storage and interpolation.

    """
    @staticmethod
    def _get_storage_value(curve, x):
        raise NotImplementedError()

    def get_discount_factor(self, start, stop=None):
        r"""discounting factor for future cashflows

        :param start: date $t_0$ to discount to
        :param stop: date $t_1$ for discounting from
            (optional, if not given $t_0$ will be **origin**
            and $t_1$ by **start**)
        :return: discounting factor $df(t_0, t_1)$

        Assuming a constant bank account interest rate $r$
        over time and interest rate compounding a bank account of $B_0=1$
        at time $t_0$ will be some value $B_1$ at time $t_1$.

        For continuous compounding $B_1=B_0 * \exp(r\cdot (t_1-t_0))$,
        for more concepts of compounding see |dcf.compounding|.

        Since $B_1$ is equivalent to the value of $B_0$ at time $t_1$,
        $B_0/B_1$ can be understood to as the price at time $t_0$
        of a bank account of $1$ at $t_1$.

        In general, discount factor $df(t_0, t_1)= B_0/B_1$ are used to
        give the price or present value $v_0(CF)$ at time $t_0$
        of any cashflow $CF$ at time $t_1$ by

        $$v_0(CF) = df(t_0, t_1) \cdot CF.$$

        This concept relates to the zero bond yields
        |InterestRateCurve().get_zero_rate()|.

        """
        if stop is None:
            return self.get_discount_factor(self.origin, start)
        return self._get_compounding_factor(start, stop)

    def get_zero_rate(self, start, stop=None):
        r"""curve of zero rates, i.e. yields of zero cupon bonds

        :param start: zero bond start date $t_0$
        :param stop: zero bond end date $t_1$
        :return: zero bond rate $z(t_0, t_1)$

        Assume a current price is $P(t_0, t_1)$ at time $t_0$
        of a zero cupon bond $P$ paying $1$ at maturity $t_1$
        without any interest or cupons.

        Such zero bond prices are used to
        give the price or present value $v_0(CF)$ at time $t_0$
        of any cashflow $CF$ at time $t_1$ by

        $$v_0(CF)
        = P(t_0, t_1) \cdot CF
        = \exp(-z(t_1-t_0) \cdot \tau(t_1-t_0)) \cdot CF$$

        where $\tau$ is the day count method to calculate the year fraction
        of the interest accrual period form $t_i$ to $t_{i+1}$
        given by |DateCurve().day_count()|.

        Note, this concept relates to the discount factor $df(t_0, t_1)$ of
        |InterestRateCurve().get_discount_factor()| by

        $$df(t_0, t_1) = \exp(-z(t_1-t_0) \cdot \tau(t_1 - t_0)).$$

        Note, this concept relates to short rates $df(t_0, t_1)$ of
        |InterestRateCurve().get_short_rate()| by

        $$z(t_0,t_1)(t_1-t_0) = \int_{t_0}^{t_1} r(t) dt.$$

        """
        if stop is None:
            return self.get_zero_rate(self.origin, start)
        return self._get_compounding_rate(start, stop)

    def get_short_rate(self, start):
        r"""constant interpolated short rate derived from zero rate

        :param date start: point in time $t$ of short rate
        :return: short rate $r_t$ at given point in time

        Calculation assumes a zero rate derived
        from a interpolated short rate, i.e.

        Let $r_t=r(t)$ be the short rate on given time grid
        $t_0, t_1, \dots, t_n$ and
        let $z(s, t)$ be the zero rate from $s$ to $t$
        with $s, t \in \{t_0, t_1, \dots, t_n\}$.

        Hence,

        $$\int_s^t r(\tau) d\tau
        = \int_s^t c_s d\tau
        = \Big[c_s \tau \Big]_s^t
        = c_s(s-t)$$

        and so

        $$c_s = z(s, t).$$

        See also |InterestRateCurve().get_zero_rate()|.

        """

        return self._get_short_rate(start)

    def _get_short_rate(self, start):
        if start < min(self.domain):
            return self.get_short_rate(min(self.domain))
        if max(self.domain) <= start:
            return self.get_short_rate(
                max(self.domain) - self._TIME_SHIFT)

        previous = max(d for d in self.domain if d <= start)
        follow = min(d for d in self.domain if start < d)
        if not previous <= start <= follow:
            raise AssertionError()
        if not previous < follow:
            raise AssertionError(list(map(str, (previous, start, follow))))

        return self.get_zero_rate(previous, follow)

    def _get_linear_short_rate(self, start, previous, follow):
        r"""
            linear interpolated short rate derived from zero rate

        :param date start: point in time of short rate
        :param date previous: point in time of short rate grid before start
        :param date follow: point in time of short rate grid after start
        :return: short rate at given point in time

        Calculation assumes a zero rate derived
        from a linear interpolated short rate, i.e.

        let :math:`r_t` be the short rate on given time grid
        :math:`t_0, t_1, \dots, t_n` and
        let :math:`z_{T,t}` be the zero rate from :math:`t` to :math:`T`
        with :math:`t,T \in |{t_0, t_1, \dots, t_n\}`.

        Hence, we assume :math:`z_{T,t} (T-t) = \int_t^T r(\tau) d\tau`. Since

        .. math::

            \int_t^T r(\tau) d\tau
            = \int_t^T r_t + a_t (\tau - t) d\tau
            = \Big[r_t \tau + \frac{a_t}{2} \tau^2 - a_t \tau \Big]_t^T
            = r_t(T-t) + \frac{a_t}{2} (T^2-t^2) - a_t(T-t)
            = r_t(T-t) + \frac{a_t}{2} (T+t)(T-t) - a_t(T-t)
            = r_t(T-t) + \frac{a_t}{2} (T-t)^2

        and so

        .. math::

            a_t = 2 \frac{z_{T,t} - r_t}{T-t}

        """
        r = self.get_short_rate(previous)
        z = self.get_zero_rate(previous, follow)
        d = self.day_count(previous, follow)
        a = 2 * (z - r) / d
        return r + a * self.day_count(previous, start)

    def get_cash_rate(self, start, stop=None, step=None):
        r"""interbank cash lending rate

        :param start: start date of cash lending
        :param stop: end date of cash lending
            (optional; default **start** + **step**)
        :param step: period length of cash lending
            (optional; by default **step** is taken from
            |RateCurve().forward_tenor|)
        :return: simple compounded interest (forward) rate $f$

        Let **start** be $t_0$.
        If **step** and **stop** are given as $\tau$ and $t_1$
        then **start** + **step** = **stop** must meet such that
        $t_0 + \tau = t_1$ in

        $$f(t_0, t_1)=\frac{1}{\tau}\big(\frac{1}{df(t_0, t_1)}-1\big).$$

        Due to the `benchmark reform
        <https://www.isda.org/2022/05/16/benchmark-reform-and-transition-from-libor/>`_
        most classical cash rates as the *LIBOR* rates
        have been replaced by overnight rates,
        e.g. *SOFR*, *SONIA* etc.
        Derived from future prediictions of overnight rates
        (aka *short term* rates) long term rates with tenors of
        $1m$, $3m$, $6m$ and $12m$ are published, too.

        For classical term rates see
        `LIBOR <https://en.wikipedia.org/wiki/Libor>`_ and
        `EURIBOR <https://en.wikipedia.org/wiki/Euribor>`_,
        for overnight rates see
        `SOFR <https://en.wikipedia.org/wiki/SOFR>`_,
        `ESTR <https://en.wikipedia.org/wiki/ESTR>`_,
        `SONIA <https://en.wikipedia.org/wiki/SONIA>`_ and
        `SARON <https://en.wikipedia.org/wiki/SARON>`_ as well as
        `TONAR <https://en.wikipedia.org/wiki/TONAR>`_.

        """
        return self._get_cash_rate(start, stop, step)

    def _get_cash_rate(self, start, stop=None, step=None):
        if stop and step:
            if not start + step == stop:
                raise AssertionError(
                    "if stop and step given, start+step must meet stop.")
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step

        df = self._get_compounding_factor(start, stop)
        t = self.day_count(start, stop)
        return simple_rate(df, t)

    def get_swap_annuity(self, date_list):
        r"""swap annuity as the accrual period weighted sum of discount factors

        :param date_list: list of period $t_0, \dots t_n$
        :return: swap annuity $A(t_0, \dots, t_n)$

        As

        $$A(t_0, \dots, t_n) = \sum_{i=1}^n df(0, t_i) \tau (t_i, t_{i+1})$$

        with

        * $0$ given by |DateCurve().origin|

        * $df$ discount factor given by
          |InterestRateCurve().get_discount_factor()|

        * $\tau $ day count method to calculate the year fraction
          of the interest accrual period form $t_i$ to $t_{i+1}$
          given by |DateCurve().day_count()|

        """
        return sum(
            self.get_discount_factor(self.origin, e) * self.day_count(s, e)
            for s, e in zip(date_list[:-1], date_list[0:])
        )


class DiscountFactorCurve(InterestRateCurve):
    r"""Interest rate curve storing and interpolating data as discount factor

    $$df(t)=y_t$$

    """
    _INTERPOLATION = log_linear_rate_scheme

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_discount_factor(curve.origin, x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        if isinstance(domain, RateCurve):
            # if argument is a curve add extra curve points to domain
            # for better approximation
            if data:
                raise TypeError("If first argument is %s, "
                                "data argument must not be given." %
                                domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            domain = sorted(set(list(data.domain) + [origin + '1d',
                                                     max(data.domain) + '1d']))
        super(DiscountFactorCurve, self).__init__(domain, data, interpolation,
                                                  origin, day_count,
                                                  forward_tenor)

    def _get_compounding_factor(self, start, stop):
        if start is self.origin:
            return self(stop)
        return self(stop) / self(start)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            # zero rate proxy at origin
            stop = min(d for d in self.domain if self.origin < d)
            # todo:
            #  calc left extrapolation (for linear zero rate interpolation)
        return super(DiscountFactorCurve, self)._get_compounding_rate(start,
                                                                      stop)


class ZeroRateCurve(InterestRateCurve):
    r"""Interest rate curve storing and interpolating data as zero rates

    $$z(t)=y_t$$

    """
    _INTERPOLATION = linear_scheme

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_zero_rate(curve.origin, x)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            return self(self.origin)
        if start is self.origin:
            return self(stop)
        if start == stop:
            return self._get_compounding_rate(
                start, start + self.__class__._TIME_SHIFT)

        s = self(start) * self.day_count(self.origin, start)
        e = self(stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (e - s) / t


class ShortRateCurve(InterestRateCurve):
    r"""Interest rate curve storing and interpolating data as short rate

    $$r(t)=y_t$$

    """
    _INTERPOLATION = constant

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_short_rate(x)

    def _get_compounding_rate(self, start, stop):
        if start == stop:
            return self(start)

        current = start
        rate = 0.0
        step = self._TIME_SHIFT

        while current + step < stop:
            rate += self(current) * self.day_count(current, current + step)
            current += step

        rate += self(current) * self.day_count(current, stop)
        return rate / self.day_count(start, stop)

    def _get_short_rate(self, start):
        return self(start)


class CashRateCurve(InterestRateCurve):
    r"""Interest rate curve storing and interpolating data as cash rate

    $$f(t, t+\tau^*)=y_t$$

    """

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_cash_rate(x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        if isinstance(domain, RateCurve):
            # if argument is a curve add extra curve points to domain
            # for better approximation
            if data:
                raise TypeError("If first argument is %s, "
                                "data argument must not be given." %
                                domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            forward_tenor = data.forward_tenor \
                if forward_tenor is None else forward_tenor
            new_domain = list(data.domain)
            for x in data.domain:
                while origin < x:
                    new_domain.append(x)
                    x -= forward_tenor
            domain = sorted(set(new_domain))
        super(CashRateCurve, self).__init__(domain, data, interpolation,
                                            origin, day_count, forward_tenor)

    def _get_compounding_rate(self, start, stop):
        if start == stop:
            return self(start)

        current = start
        df = 1.0
        step = self.forward_tenor
        while current + step < stop:
            dc = self.day_count(current, current + step)
            df *= simple_compounding(self(current), dc)
            current += step
        dc = self.day_count(current, stop)
        df *= simple_compounding(self(current), dc)
        return continuous_rate(df, self.day_count(start, stop))

    def _get_cash_rate(self, start, stop=None, step=None):
        if stop and step:
            if not start + step == stop:
                raise AssertionError(
                    "if stop and step given, start+step must meet stop.")
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        if stop == start + self.forward_tenor:
            return self(start)
        return super(CashRateCurve, self).get_cash_rate(start, stop)
