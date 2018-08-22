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
            assert start + step == stop, "if stop and step given, start+step must meet stop."
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        df = self.get_discount_factor(start, stop)
        t = self.day_count(start, stop)
        return compounding.simple_rate(df, t)

    def get_swap_annuity(self, date_list):
        return sum([self.get_discount_factor(self.origin, t) for t in date_list])


class DiscountFactorCurve(InterestRateCurve):
    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_discount_factor(curve.origin, x)

    def _get_compounding_factor(self, start, stop):
        if start == stop:
            return 1.
        if stop is None:
            return self(start)
        if start is self.origin:
            return self(stop)
        return self(stop) / self(start)


class ZeroRateCurve(InterestRateCurve):
    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_zero_rate(curve.origin, x)

    def _get_compounding_rate(self, start, stop):
        if start == stop:
            return self._get_compounding_rate(start, start + TIME_SHIFT)
        if stop is None:
            return self(start)
        if start is self.origin:
            return self(stop)
        s = self(start) * self.day_count(self.origin, start)
        e = self(stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (e - s) / t


class ShortRateCurve(InterestRateCurve):
    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_short_rate(x)

    def _get_compounding_rate(self, start, stop):

        if start == stop:
            return self(start)

        current = start
        rate = 0.0
        step = '1B'

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
        new = cls(other.domain,
                  [other.get_cash_rate(x, step=forward_tenor) for x in other.domain],
                  other.interpolation,
                  other.origin,
                  other.day_count,
                  forward_tenor)
        return new


    def _get_compounding_factor(self, start, stop):

        if start == stop:
            return 1.

        df = 1.0
        step = self.forward_tenor
        current = start
        while current + step < stop:
            t = self.day_count(current, current + step)
            df *= compounding.simple_compounding(self(current), t)
            current += step
        t = self.day_count(current, stop)
        df *= compounding.simple_compounding(self(current), t)
        return df

    def __get_compounding_rate(self, start, stop):
        if start == stop or start + TIME_SHIFT == stop:
            return self(start)
        return super(CashRateCurve, self)._get_compounding_rate(start, stop)

    def get_cash_rate(self, start, stop=None, step=None):
        if stop and step:
            assert start + step == stop, "if stop and step given, start+step must meet stop."
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        if stop == start + self.forward_tenor:
            return self(start)
        return super(CashRateCurve, self).get_cash_rate(start, stop)
