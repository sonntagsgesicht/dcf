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

import compounding
import curve
import interestratecurve

TIME_SHIFT = '1D'
FORWARD_CREDIT_TENOR = '1Y'


class CreditCurve(curve.RateCurve):
    """ generic curve for default probabilities (under construction) """
    _inner_curve = curve.RateCurve

    def __init__(self, x_list, y_list, y_inter=None, origin=None, day_count=None, forward_tenor=None):
        super(self.__class__, self).__init__(x_list, y_list, y_inter, origin, day_count)
        self.forward_tenor = forward_tenor if forward_tenor is not None else FORWARD_CREDIT_TENOR

    def get_survival_prob(self, start, stop):  # aka get_discount_factor
        ir = self.get_flat_intensity(start, stop)
        t = self.day_count(start, stop)
        return compounding.continuous_compounding(ir, t)

    def get_flat_intensity(self, start, stop):  # aka get_zero_rate
        if start == stop:
            stop += TIME_SHIFT
        df = self.get_survival_prob(start, stop)
        t = self.day_count(start, stop)
        return compounding.continuous_rate(df, t)

    def get_hazard_rate(self, start, shift=TIME_SHIFT):  # aka get_short_rate
        up = self.get_flat_intensity(self.origin, start + shift)
        dn = self.get_flat_intensity(self.origin, start - shift)
        t = self.day_count(start - shift, start + shift)
        return (up - dn) / t

    def get_forward_survival_rate(self, start, stop=None, step=None):  # aka get_cash_rate
        if step is not None and stop is not None:
            raise TypeError("one argument (stop or step) must be None.")
        if stop is None:
            stop = start + self.forward_tenor if step is None else start + step
        df = self.get_survival_prob(start, stop)
        t = self.day_count(start, stop)
        return compounding.simple_rate(df, t)


class SurvivalProbabilityCurve(CreditCurve):
    def get_storage_type(self, x):
        return self.get_survival_prob(self.origin, x)

    def get_survival_prob(self, start, stop):
        return self(start) if stop is None or stop is self.origin else self(start) / self(stop)


class FlatIntensityCurve(CreditCurve):
    pass


class ForwardSurvivalRate(CreditCurve):
    pass


class HazardRateCurve(CreditCurve):
    pass
