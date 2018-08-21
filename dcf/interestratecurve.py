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

from math import exp

import curve
import compounding

TIME_SHIFT = '1D'
FORWARD_RATE_TENOR = '3M'


class InterestRateCurve(curve.RateCurve):
    def __init__(self, x_list, y_list, y_inter=None, origin=None, day_count=None, forward_tenor=None):
        super(InterestRateCurve, self).__init__(x_list, y_list, y_inter, origin, day_count)
        self.forward_tenor = forward_tenor if forward_tenor is not None else FORWARD_RATE_TENOR

    def get_discount_factor(self, start, stop):
        ir = self.get_zero_rate(start, stop)
        t = self.day_count(start, stop)
        return compounding.continuous_compounding(ir, t)

    def get_zero_rate(self, start, stop):
        if start == stop:
            stop += TIME_SHIFT
        df = self.get_discount_factor(start, stop)
        t = self.day_count(start, stop)
        return compounding.continuous_rate(df, t)

    def get_short_rate(self, start, shift=TIME_SHIFT):
        up = self.get_zero_rate(self.origin, start + shift)
        dn = self.get_zero_rate(self.origin, start - shift)
        t = self.day_count(start - shift, start + shift)
        return (up - dn) / t

    def get_cash_rate(self, start, stop=None, step=None):
        if step is not None and stop is not None:
            raise TypeError("one argument (stop or step) must be None.")
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        df = self.get_discount_factor(start, stop)
        t = self.day_count(start, stop)
        return compounding.simple_rate(df, t)

    def get_swap_annuity(self, date_list):
        return sum([self.get_discount_factor(self.origin, t) for t in date_list])

    def get_swap_leg_valuation(self, date_list, flow_list):
        if isinstance(flow_list, float):
            return flow_list * self.get_swap_annuity(date_list)
        else:
            return sum([self.get_discount_factor(self.origin, t) * r for t, r in zip(date_list, flow_list)])


class DiscountFactorCurve(InterestRateCurve):
    def get_storage_type(self, x):
        return self.get_discount_factor(self.origin, x)

    def get_discount_factor(self, start, stop):
        return self(start) if stop is None or stop is self.origin else self(start) / self(stop)


class ZeroRateCurve(InterestRateCurve):
    def get_storage_type(self, x):
        return self.get_zero_rate(self.origin, x)

    def get_zero_rate(self, start, stop):
        if stop is None or stop is self.origin or start == stop:
            return self(start)
        else:
            df = exp(self(start) * self.day_count(self.origin, start)
                     - self(stop) * self.day_count(self.origin, stop))
            t = self.day_count(start, stop)
            return compounding.continuous_rate(df, t)


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
        if step is not None and stop is not None:
            raise TypeError, "one argument (stop or step) must be None."

        if stop is None:
            if step is None or step is self.forward_tenor:
                return self(start)
            else:
                return super(CashRateCurve, self).get_cash_rate(start, step=step)
        else:
            return super(CashRateCurve, self).get_cash_rate(start, stop)


class ShortRateCurve(InterestRateCurve):
    def get_storage_type(self, x):
        return self.get_short_rate(x)

    def get_zero_rate(self, start, stop):
        # integrate from start to stop
        ir = 0.0
        current = start
        while current < stop:
            t = self.day_count(current, current + TIME_SHIFT)
            ir = self(current) * t
            current += TIME_SHIFT
        t = self.day_count(current, stop)
        ir = self(current) * t
        return ir

    def get_short_rate(self, start, shift=None):
        return self(start)