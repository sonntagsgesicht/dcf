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

import curve
import compounding

TIME_SHIFT = '1D'
FORWARD_RATE_TENOR = '3M'


class InterestRateCurve(curve.RateCurve):

    def get_discount_factor(self, start, stop=None):
        if stop is None:
            return self.get_discount_factor(self.origin, start)
        return self._get_compounding_factor(start, stop)

    def get_zero_rate(self, start, stop=None):
        if stop is None:
            return self.get_zero_rate(self.origin, start)
        return self._get_compounding_rate(start, stop)

    def get_short_rate(self, start):
        return self._get_compounding_rate(start, start)

    def __get_compounding_rate(self, start, stop):
        if not start == stop:
            return super(InterestRateCurve, self)._get_compounding_rate(start, stop)
        r"""
            short rate derived from zero rate

        :param BusinessDate start: point in time of short rate
        :return: short rate at given point in time

        Calculation assumes a zero rate derived from a linear interpolated short rate, i.e.

        let :math:`r_t` be the short rate on given time grid :math:`t_0, t_1, \dots, t_n` and
        let :math:`z_{T,t}` be the zero rate from :math:`t` to :math:`T` with :math:`t,T \in |{t_0, t_1, \dots, t_n\}`.

        Hence, we assume :math:`z_{T,t} (T-t) = \int_t^T r(\tau) d\tau`. Since

        .. math::

            \int_t^T r(\tau) d\tau = \int_t^T r_t + a_t (\tau - t) d\tau
            = \Big[r_t \tau + \frac{a_t}{2} \tau^2 - a_t \tau \Big]_t^T
            = r_t(T-t) + \frac{a_t}{2} (T-t)^2

        and so

        .. math::

            a_t = 2 \frac{z_{T,t} - r_t}{T-t}

        """
        if start <= min(self.domain):
            return self(start)
        if max(self.domain) < start:
            return self.get_short_rate(max(self.domain))

        previous = max(d for d in self.domain if d < start)
        follow = min(d for d in self.domain if d >= start)
        assert previous < start

        # for linear interpolated short rate
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
        return compounding.simple_rate(df, t)  # todo: change to simple_compounding

    def get_swap_annuity(self, date_list):
        return sum([self.get_discount_factor(self.origin, t) for t in date_list])


class DiscountFactorCurve(InterestRateCurve):
    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_discount_factor(curve.origin, x)

    def _get_compounding_factor(self, start, stop):
        if start is self.origin:
            return self(stop)
        return self(stop) / self(start)


class ZeroRateCurve(InterestRateCurve):
    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_zero_rate(curve.origin, x)

    def _get_compounding_rate(self, start, stop):
        if start is self.origin:
            return self(stop)
        if start == stop:
            return self._get_compounding_rate(start, start + TIME_SHIFT)
        s = self(start) * self.day_count(self.origin, start)
        e = self(stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (e - s) / t


class ShortRateCurve(InterestRateCurve):
    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_short_rate(x)

    def _get_compounding_rate(self, start, stop):
        if start is self.origin and stop in self._compounding_rates:
            return self._compounding_rates[stop]
        if start == stop:
            return self(start)

        current = start
        rate = 0.0
        step = '1d'  # todo: 1d or 1b step?

        if current < min(self.domain):
            current = min(self.domain)
            rate += self(start) * self.day_count(start, current)

        while current + step < stop:
            if not current < max(self.domain):
                # leave, if loop does not provide anymore term structure information
                break
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

    @classmethod
    def cast(cls, other, forward_tenor=None):
        forward_tenor = other.forward_tenor if forward_tenor is None else forward_tenor
        rates_domain = BusinessRange(other.origin, other.origin + forward_tenor, '1D') + [other.origin + forward_tenor]
        compounding_rates = dict((x, other.get_zero_rate(other.origin, x)) for x in rates_domain)
        new_domain = list(other.domain)
        for x in other.domain:
            new_domain.extend(BusinessRange(other.origin, x, forward_tenor, x))
        new_domain = sorted(set(new_domain))
        new = cls(new_domain,  # other.domain,
                  [other.get_cash_rate(x, step=forward_tenor) for x in new_domain],  # other.domain],
                  other.interpolation,
                  other.origin,
                  other.day_count,
                  forward_tenor,
                  compounding_rates)
        return new

    def __init__(self, x_list, y_list, y_inter=None, origin=None, day_count=None, forward_tenor=None, compounding_rates={}):
        super(CashRateCurve, self).__init__(x_list, y_list, y_inter, origin, day_count, forward_tenor)
        self._compounding_rates = compounding_rates

    def _get_compounding_rate(self, start, stop):
        if start is self.origin and stop in self._compounding_rates:
            return self._compounding_rates[stop]
        if start == stop:
            return self._get_compounding_rate(start, start + TIME_SHIFT)
        if start is self.origin:
            domain = [d for d in self.domain if start <= d <= stop]

            if not domain:
                df = compounding.simple_compounding(self(start), self.day_count(start, stop))
                return compounding.continuous_rate(df, self.day_count(start, stop))

            df = 1.
            if min(domain) in self._compounding_rates:
                dc = self.day_count(self.origin, min(domain))
                df *= compounding.continuous_compounding(self._compounding_rates[min(domain)], dc)
            else:
                dc = self.day_count(self.origin, min(domain))
                df *= compounding.simple_compounding(self(self.origin), dc)
            for s, e in zip(domain[:-1], domain[1:]):
                dc = self.day_count(s, e)
                df *= compounding.simple_compounding(self(s), dc)
            dc = self.day_count(max(domain), stop)
            df *= compounding.simple_compounding(self(max(domain)), dc)

            return compounding.continuous_rate(df, self.day_count(start, stop))

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
