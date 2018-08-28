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

from businessdate import BusinessRange

from curve import RateCurve
from compounding import continuous_compounding, continuous_rate, simple_compounding, simple_rate
from interpolation import zero, constant, linear, loglinear, logconstant


class InterestRateCurve(RateCurve):
    def cast(self, cast_type, **kwargs):
        old_domain = kwargs.get('domain', self.domain)

        if issubclass(cast_type, (DiscountFactorCurve,)):
            domain = kwargs.get('domain', self.domain)
            origin = kwargs.get('origin', self.origin)
            new_domain = list(domain) + [origin + '1d']
            kwargs['domain'] = sorted(set(new_domain))

        if issubclass(cast_type, (DiscountFactorCurve,)):
            domain = kwargs.get('domain', self.domain)
            new_domain = list(domain) + [max(domain) + '1d']
            kwargs['domain'] = sorted(set(new_domain))

        if issubclass(cast_type, (CashRateCurve,)):
            domain = kwargs.get('domain', self.domain)
            forward_tenor = kwargs.get('forward_tenor', self.forward_tenor)
            new_domain = list(domain)
            for x in domain:
                new_domain.extend(BusinessRange(self.origin, x, forward_tenor, x))
            kwargs['domain'] = sorted(set(new_domain))

        return super(InterestRateCurve, self).cast(cast_type, **kwargs)

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

        :param BusinessDate start: point in time of short rate
        :param BusinessDate previous: point in time of short rate grid before start
        :param BusinessDate follow: point in time of short rate grid after start
        :return: short rate at given point in time

        Calculation assumes a zero rate derived from a interpolated short rate, i.e.

        let :math:`r_t` be the short rate on given time grid :math:`t_0, t_1, \dots, t_n` and
        let :math:`z_{T,t}` be the zero rate from :math:`t` to :math:`T` with :math:`t,T \in |{t_0, t_1, \dots, t_n\}`.

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
            return self.get_short_rate(max(self.domain)-self.__class__._time_shift)

        previous = max(d for d in self.domain if d <= start)
        follow = min(d for d in self.domain if start < d)
        assert previous <= start <= follow
        assert previous < follow, map(str, (previous, start, follow))

        return self.get_zero_rate(previous, follow)

    def _get_linear_short_rate(self, start, previous, follow):
        r"""
            linear interpolated short rate derived from zero rate

        :param BusinessDate start: point in time of short rate
        :param BusinessDate previous: point in time of short rate grid before start
        :param BusinessDate follow: point in time of short rate grid after start
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
            assert start + step == stop, "if stop and step given, start+step must meet stop."
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step

        df = self._get_compounding_factor(start, stop)
        t = self.day_count(start, stop)
        return simple_rate(df, t)

    def get_swap_annuity(self, date_list):
        return sum([self.get_discount_factor(self.origin, t) for t in date_list])


class DiscountFactorCurve(InterestRateCurve):
    _interpolation = logconstant(), loglinear(), logconstant()

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_discount_factor(curve.origin, x)

    def _get_compounding_factor(self, start, stop):
        if start is self.origin:
            return self(stop)
        return self(stop) / self(start)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            # zero rate proxi at origin
            stop = min(d for d in self.domain if self.origin < d)
            # todo: calc left extrapolation (for linear zero rate interpolation)
        return super(DiscountFactorCurve, self)._get_compounding_rate(start, stop)


class ZeroRateCurve(InterestRateCurve):
    _interpolation = constant(), linear(), constant()

    @staticmethod
    def get_storage_type(curve, x):
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
    _interpolation = constant(), constant(), constant()

    @staticmethod
    def get_storage_type(curve, x):
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
    def get_storage_type(curve, x):
        return curve.get_cash_rate(x)

    def ____get_compounding_rate(self, start, stop):
        if start == stop:
            return self(start)

        df = 1.0
        step = self.forward_tenor
        grid = BusinessRange(start, stop, step, stop)
        if grid:
            for s, e in zip(grid[:-1], grid[1:]):
                dc = self.day_count(s, e)
                df *= simple_compounding(self(s), dc)
            dc = self.day_count(grid[-1], stop)
            df *= simple_compounding(self(grid[-1]), dc)
        else:
            dc = self.day_count(start, stop)
            df *= simple_compounding(self(start), dc)
        return continuous_rate(df, self.day_count(start, stop))

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

    def __get_compounding_rate(self, start, stop):
        if start == stop:
            return self._get_compounding_rate(start, start + self.__class__._time_shift)

        if start is self.origin:
            # negative time
            if stop <= self.origin:
                return self._get_compounding_rate(self.origin, self.origin)

            # first stub to join self.domain
            previous = max(d for d in self.domain if d <= self.origin)
            follow = min(d for d in self.domain if self.origin < d)
            if previous <= stop <= follow:
                dp = self.day_count(previous, previous + self.forward_tenor)
                cp = continuous_rate(simple_compounding(self(previous), dp), dp)
                df = self.day_count(follow, follow + self.forward_tenor)
                cf = continuous_rate(simple_compounding(self(follow), df), df)
                r = cp + (cf - cp) * (self.day_count(previous, stop) / self.day_count(previous, follow))
                return r

            # roll on domain as much as possible
            domain = [d for d in self.domain if self.origin < d <= stop]
            df = self.get_discount_factor(self.origin, min(domain))
            for s, e in zip(domain[:-1], domain[1:]):
                dc = self.day_count(s, e)
                df *= simple_compounding(self(s), dc)
            dc = self.day_count(max(domain), stop)
            df *= simple_compounding(self(max(domain)), dc)
            return continuous_rate(df, self.day_count(start, stop))

        # calc partial rates from full distance rates
        s = self._get_compounding_rate(self.origin, start) * self.day_count(self.origin, start)
        e = self._get_compounding_rate(self.origin, stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (e - s) / t

    def get_cash_rate(self, start, stop=None, step=None):
        if stop and step:
            assert start + step == stop, "if stop and step given, start+step must meet stop."
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        if stop == start + self.forward_tenor:
            return self(start)
        return super(CashRateCurve, self).get_cash_rate(start, stop)