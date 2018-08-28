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

from curve import RateCurve
from interpolation import constant, linear, loglinear, logconstant


class CreditCurve(RateCurve):
    """ generic curve for default probabilities (under construction) """
    _forward_tenor = '1Y'

    def cast(self, cast_type, **kwargs):
        old_domain = kwargs.get('domain', self.domain)

        if issubclass(cast_type, (SurvivalProbabilityCurve,)):
            domain = kwargs.get('domain', self.domain)
            origin = kwargs.get('origin', self.origin)
            new_domain = list(domain) + [origin + '1d']
            kwargs['domain'] = sorted(set(new_domain))

        if issubclass(cast_type, (SurvivalProbabilityCurve,)):
            domain = kwargs.get('domain', self.domain)
            new_domain = list(domain) + [max(domain) + '1d']
            kwargs['domain'] = sorted(set(new_domain))

        return super(CreditCurve, self).cast(cast_type, **kwargs)

    def get_survival_prob(self, start, stop=None):  # aka get_discount_factor
        if stop is None:
            return self.get_survival_prob(self.origin, start)
        return self._get_compounding_factor(start, stop)

    def get_flat_intensity(self, start, stop=None):  # aka get_zero_rate
        if stop is None:
            return self.get_flat_intensity(self.origin, start)
        return self._get_compounding_rate(start, stop)

    def get_hazard_rate(self, start):  # aka get_short_rate
        if start < min(self.domain):
            return self.get_hazard_rate(min(self.domain))
        if max(self.domain) <= start:
            return self.get_hazard_rate(max(self.domain) - self.__class__._time_shift)

        previous = max(d for d in self.domain if d <= start)
        follow = min(d for d in self.domain if start < d)
        assert previous <= start <= follow
        assert previous < follow, map(str, (previous, start, follow))

        return self.get_flat_intensity(previous, follow)


class SurvivalProbabilityCurve(CreditCurve):
    _interpolation = logconstant(), loglinear(), logconstant()

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_survival_prob(curve.origin, x)

    def _get_compounding_factor(self, start, stop):
        if start is self.origin:
            return self(stop)
        return self(stop) / self(start)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            # intensity proxi at origin
            stop = min(d for d in self.domain if self.origin < d)
            # todo: calc left extrapolation (for linear zero rate interpolation)
        return super(SurvivalProbabilityCurve, self)._get_compounding_rate(start, stop)


class FlatIntensityCurve(CreditCurve):
    _interpolation = constant(), linear(), constant()

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_flat_intensity(curve.origin, x)

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


class HazardRateCurve(CreditCurve):
    _interpolation = constant(), constant(), constant()

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_hazard_rate(x)

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

    def get_hazard_rate(self, start):  # aka get_short_rate
        return self(start)
