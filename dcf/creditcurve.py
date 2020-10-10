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
from sys import float_info

from .curve import RateCurve
from .compounding import continuous_compounding, continuous_rate
from .interpolation import constant, linear, logconstantrate, loglinearrate, neglogconstant, negloglinear
from . import dyn_scheme


class CreditCurve(RateCurve, ABC):
    """ generic curve for default probabilities (under construction) """
    _forward_tenor = '1Y'

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None, forward_tenor=None):
        if isinstance(domain, RateCurve):
            # if argument is a curve add extra curve points to domain for better approximation
            if data:
                raise TypeError("If first argument is %s, data argument must not be given." % domain.__class__.__name__)
            data = domain
            domain = sorted(set(list(data.domain) + [max(data.domain) + '1y']))
        super(CreditCurve, self).__init__(domain, data, interpolation, origin, day_count, forward_tenor)

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
        if not previous <= start <= follow:
            raise AssertionError()
        if not previous < follow:
            raise AssertionError(list(map(str, (previous, start, follow))))
        return self.get_flat_intensity(previous, follow)


class ProbabilityCurve(CreditCurve, ABC):

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None, forward_tenor=None):
        # validate probabilities
        if not isinstance(data, RateCurve):
            data = [max(float_info.min, min(d, 1. - float_info.min)) for d in data]
            if not all(data):
                raise ValueError('Found non positive survival probabilities.')
        # if argument is a curve add extra curve points to domain for better approximation
        if isinstance(domain, RateCurve):
            if data:
                raise TypeError("If first argument is %s, data argument must not be given." % domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            domain = sorted(set(list(data.domain) + [origin + '1d', max(data.domain) + '1y']))
        super(ProbabilityCurve, self).__init__(domain, data, interpolation, origin, day_count, forward_tenor)


class SurvivalProbabilityCurve(ProbabilityCurve):
    _interpolation = dyn_scheme(logconstantrate, loglinearrate, logconstantrate)

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(curve.origin, x)

    def _get_compounding_factor(self, start, stop):
        if start is self.origin:
            return self(stop)
        if start == stop:
            return 1. if 2*float_info.min <= self(start) else 0.
        return self(stop) / self(start)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            # intensity proxi at origin
            stop = min(d for d in self.domain if self.origin < d)
            # todo: calc left extrapolation (for linear zero rate interpolation)
        return super(SurvivalProbabilityCurve, self)._get_compounding_rate(start, stop)


class DefaultProbabilityCurve(SurvivalProbabilityCurve):
    """ wrapper of SurvivalProbabilityCurve """

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(curve.origin, x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None, forward_tenor=None):
        if not isinstance(data, RateCurve):
            data = [1. - d for d in data]
        super(DefaultProbabilityCurve, self).__init__(domain, data, interpolation, origin, day_count, forward_tenor)


class FlatIntensityCurve(CreditCurve):
    _interpolation = dyn_scheme(constant, linear, constant)

    @staticmethod
    def _get_storage_value(curve, x):
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
    _interpolation = dyn_scheme(constant, constant, constant)

    @staticmethod
    def _get_storage_value(curve, x):
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


class MarginalSurvivalProbabilityCurve(ProbabilityCurve):
    _interpolation = dyn_scheme(neglogconstant, negloglinear, neglogconstant)

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(x, x + curve.forward_tenor)

    def _get_compounding_factor(self, start, stop):
        if start == stop:
            return 1. if 2*float_info.min <= self(start) else 0.

        current = start
        df = 1.0
        step = self.forward_tenor
        while current + step < stop:
            df *= self(current) if 2 * float_info.min <= self(current) else 0.
            current += step

        if 2 * float_info.min <= self(current):
            r = continuous_rate(self(current), self.day_count(current, current + step))
            df *= continuous_compounding(r, self.day_count(current, stop))
        else:
            df *= 0.
        return df

    def get_hazard_rate(self, start):  # aka get_short_rate
        if start < min(self.domain):
            return self.get_hazard_rate(min(self.domain))
        if max(self.domain) <= start:
            return self.get_flat_intensity(max(self.domain), max(self.domain) + self.__class__._time_shift)

        previous = max(d for d in self.domain if d <= start)
        follow = min(d for d in self.domain if start < d)
        if not previous < follow:
            raise AssertionError(list(map(str, (previous, start, follow))))
        if not previous <= start <= follow:
            raise AssertionError(list(map(str, (previous, start, follow))))

        return self.get_flat_intensity(previous, follow)


class MarginalDefaultProbabilityCurve(MarginalSurvivalProbabilityCurve):
    """ wrapper of SurvivalProbabilityCurve """

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(x, x + curve.forward_tenor)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None, day_count=None, forward_tenor=None):
        if not isinstance(data, RateCurve):
            data = [1. - d for d in data]
        super(MarginalDefaultProbabilityCurve, self).__init__(
            domain, data, interpolation, origin, day_count, forward_tenor)
