# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from abc import ABC

from .curve import RateCurve
from .compounding import continuous_rate, simple_compounding, simple_rate
from .interpolation import constant, linear, loglinearrate, logconstantrate
from . import dyn_scheme


class InterestRateCurve(RateCurve, ABC):

    def get_discount_factor(self, start, stop=None):
        if stop is None:
            return self.get_discount_factor(self.origin, start)
        return self._get_compounding_factor(start, stop)

    def get_zero_rate(self, start, stop=None):
        if stop is None:
            return self.get_zero_rate(self.origin, start)
        return self._get_compounding_rate(start, stop)

    def get_short_rate(self, start):
        r"""
            constant interpolated short rate derived from zero rate

        :param date start: point in time of short rate
        :return: short rate at given point in time

        Calculation assumes a zero rate derived from a interpolated short rate, i.e.

        let :math:`r_t` be the short rate on given time grid :math:`t_0, t_1, \dots, t_n` and
        let :math:`z_{T,t}` be the zero rate from :math:`t` to :math:`T` with :math:`t,T \in \{t_0, t_1, \dots, t_n\}`.

        Hence, we assume :math:`z_{T,t} (T-t) = \int_t^T r(\tau) d\tau`. Since

        .. math::

            \int_t^T r(\tau) d\tau
            = \int_t^T c_t d\tau
            = \Big[c_t \tau \Big]_t^T
            = c_t(T-t)

        and so

        .. math::

            c_t = z_{T,t}

        """

        if start < min(self.domain):
            return self.get_short_rate(min(self.domain))
        if max(self.domain) <= start:
            return self.get_short_rate(max(self.domain) - self.__class__._time_shift)

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

        Calculation assumes a zero rate derived from a linear interpolated short rate, i.e.

        let :math:`r_t` be the short rate on given time grid :math:`t_0, t_1, \dots, t_n` and
        let :math:`z_{T,t}` be the zero rate from :math:`t` to :math:`T` with :math:`t,T \in |{t_0, t_1, \dots, t_n\}`.

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

        if stop and step:
            if not start + step == stop:
                raise AssertionError("if stop and step given, start+step must meet stop.")
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step

        df = self._get_compounding_factor(start, stop)
        t = self.day_count(start, stop)
        return simple_rate(df, t)

    def get_swap_annuity(self, date_list):
        return sum([self.get_discount_factor(self.origin, t) for t in date_list])


class DiscountFactorCurve(InterestRateCurve):
    _interpolation = dyn_scheme(logconstantrate, loglinearrate, logconstantrate)

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_discount_factor(curve.origin, x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None, forward_tenor=None):
        if isinstance(domain, RateCurve):
            # if argument is a curve add extra curve points to domain for better approximation
            if data:
                raise TypeError("If first argument is %s, data argument must not be given." % domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            domain = sorted(set(list(data.domain) + [origin + '1d', max(data.domain) + '1d']))
        super(DiscountFactorCurve, self).__init__(domain, data, interpolation, origin, day_count, forward_tenor)

    def _get_compounding_factor(self, start, stop):
        if start is self.origin:
            return self(stop)
        return self(stop) / self(start)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            # zero rate proxy at origin
            stop = min(d for d in self.domain if self.origin < d)
            # todo: calc left extrapolation (for linear zero rate interpolation)
        return super(DiscountFactorCurve, self)._get_compounding_rate(start, stop)


class ZeroRateCurve(InterestRateCurve):
    _interpolation = dyn_scheme(constant, linear, constant)

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_zero_rate(curve.origin, x)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            return self(self.origin)
        if start is self.origin:
            return self(stop)
        if start == stop:
            return self._get_compounding_rate(start, start + self.__class__._time_shift)

        s = self(start) * self.day_count(self.origin, start)
        e = self(stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (e - s) / t


class ShortRateCurve(InterestRateCurve):
    _interpolation = dyn_scheme(constant, constant, constant)

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_short_rate(x)

    def _get_compounding_rate(self, start, stop):
        if start == stop:
            return self(start)

        current = start
        rate = 0.0
        step = self.__class__._time_shift

        while current + step < stop:
            rate += self(current) * self.day_count(current, current + step)
            current += step

        rate += self(current) * self.day_count(current, stop)
        return rate / self.day_count(start, stop)

    def get_short_rate(self, start):
        return self(start)


class CashRateCurve(InterestRateCurve):

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_cash_rate(x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None, forward_tenor=None):
        if isinstance(domain, RateCurve):
            # if argument is a curve add extra curve points to domain for better approximation
            if data:
                raise TypeError("If first argument is %s, data argument must not be given." % domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            forward_tenor = data.forward_tenor if forward_tenor is None else forward_tenor
            new_domain = list(data.domain)
            for x in data.domain:
                while origin < x:
                    new_domain.append(x)
                    x -= forward_tenor
            domain = sorted(set(new_domain))
        super(CashRateCurve, self).__init__(domain, data, interpolation, origin, day_count, forward_tenor)

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

    def get_cash_rate(self, start, stop=None, step=None):
        if stop and step:
            if not start + step == stop:
                raise AssertionError("if stop and step given, start+step must meet stop.")
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        if stop == start + self.forward_tenor:
            return self(start)
        return super(CashRateCurve, self).get_cash_rate(start, stop)
