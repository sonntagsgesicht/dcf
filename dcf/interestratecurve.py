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

import curve
import compounding

TIME_SHIFT = '1D'
FORWARD_RATE_TENOR = '3M'


class InterestRateCurve(curve.RateCurve):
    def __init__(self, x_list, y_list, y_inter=None, origin=None, day_count=None, forward_tenor=None):
        super(InterestRateCurve, self).__init__(x_list, y_list, y_inter, origin, day_count)
        self.forward_tenor = forward_tenor if forward_tenor is not None else FORWARD_RATE_TENOR

    def get_discount_factor(self, start, stop):
        return self._get_compounding_factor(start, stop)

    def get_zero_rate(self, start, stop):
        return self._get_compounding_rate(start, stop)

    def get_short_rate(self, start):
        return self._get_compounding_rate(start, start + TIME_SHIFT)

    def get_cash_rate(self, start, stop=None, step=None):
        if stop and step:
            assert start+step == stop, "if stop and step given, start+step must meet stop."
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        df = self.get_discount_factor(start, stop)
        t = self.day_count(start, stop)
        return compounding.simple_rate(df, t)

    def get_swap_annuity(self, date_list):
        return sum([self.get_discount_factor(self.origin, t) for t in date_list])


class DiscountFactorCurve(InterestRateCurve):
    def get_storage_type(self, x):
        return self._get_compounding_factor(self.origin, x)

    def _get_compounding_factor(self, start, stop):
        return self(start) if stop is None or stop is self.origin else self(start) / self(stop)


class ZeroRateCurve(InterestRateCurve):
    def get_storage_type(self, x):
        return self._get_compounding_rate(self.origin, x)

    def _get_compounding_rate(self, start, stop):
        if stop is None:
            return self(start)
        if start is self.origin:
            return self(stop)
        s = self(start) * self.day_count(self.origin, start)
        e = self(stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (e - s) / t


class CashRateCurve(InterestRateCurve):
    def get_storage_type(self, x):
        return self.get_cash_rate(x)

    def get_discount_factor(self, start, stop):
        df = 1.0
        current = start
        while current < stop:
            t = self.day_count(current, current + self.forward_tenor)
            df *= compounding.simple_compounding(self(current), t)
            current += self.forward_tenor
        t = self.day_count(current, stop)
        df *= compounding.simple_compounding(self(current), t)
        return df

    def get_cash_rate(self, start, stop=None, step=None):
        if stop and step:
            assert start+step == stop, "if stop and step given, start+step must meet stop."
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        if stop == start + self.forward_tenor:
            return self(start)
        return super(CashRateCurve, self).get_cash_rate(start, stop)


class ShortRateCurve(InterestRateCurve):
    def get_storage_type(self, x):
        return self.get_short_rate(x)

    def _get_compounding_rate(self, start, stop):
        domain = [start] + [d for d in self.domain if start < d < stop] + [stop]
        rate = 0.0
        for s, e in zip(domain[:-1], domain[1:]):
            sh = self.get_short_rate(s)
            yf = self.day_count(s, e)
            rate += sh * yf
        return rate / self.day_count(start, stop)

    def get_short_rate(self, start):
        return self(start)
