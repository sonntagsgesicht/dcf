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

TIME_SHIFT = '1D'
FORWARD_CREDIT_TENOR = '1Y'


class CreditCurve(curve.RateCurve):
    """ generic curve for default probabilities (under construction) """

    def __init__(self, domain, data, interpolation=None, origin=None, day_count=None, forward_tenor=None):
        super(self.__class__, self).__init__(domain, data, interpolation, origin, day_count)
        self.forward_tenor = FORWARD_CREDIT_TENOR if forward_tenor is None else forward_tenor

    def get_survival_prob(self, start, stop):  # aka get_discount_factor
        return self._get_compounding_factor(start, stop)

    def get_flat_intensity(self, start, stop):  # aka get_zero_rate
        return self._get_compounding_rate(start, stop)

    def get_hazard_rate(self, start):  # aka get_short_rate
        return self._get_compounding_rate(start, start + TIME_SHIFT)


class SurvivalProbabilityCurve(CreditCurve):

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_survival_prob(curve.origin, x)

    def _get_compounding_factor(self, start, stop):
        return self(start) if stop is None or stop is self.origin else self(start) / self(stop)


class FlatIntensityCurve(CreditCurve):

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_flat_intensity(curve.origin, x)

    def _get_compounding_rate(self, start, stop):
        if stop is None:
            return self(start)
        if start is self.origin:
            return self(stop)
        s = self(start) * self.day_count(self.origin, start)
        e = self(stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (s - e) / t


class HazardRateCurve(CreditCurve):

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_hazard_rate(x)

    def _get_compounding_rate(self, start, stop):
        domain = [start] + [d for d in self.domain if start < d < stop] + [stop]
        rate = 0.0
        for s, e in zip(domain[:-1], domain[1:]):
            hz = self.get_hazard_rate(s)
            yf = self.day_count(s, e)
            rate += hz * yf
        return rate / self.day_count(start, stop)

    def get_hazard_rate(self, start):  # aka get_short_rate
        return self(start)
