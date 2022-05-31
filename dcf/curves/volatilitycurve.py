# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import logging
from math import sqrt

from ..interpolation import zero_linear_scheme
from .curve import RateCurve

_logger = logging.getLogger('dcf')


class VolatilityCurve(RateCurve):
    """ generic curve for default probabilities (under construction) """
    _TIME_SHIFT = '1d'
    _interpolation = zero_linear_scheme

    def get_instantaneous_vol(self, start):
        raise NotImplementedError

    def get_terminal_vol(self, start, stop=None):
        raise NotImplementedError


class InstantaneousVolatilityCurve(VolatilityCurve):

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_instantaneous_vol(x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        # if argument is a curve add extra curve points
        # to domain for better approximation
        if isinstance(domain, RateCurve):
            if data:
                raise TypeError("If first argument is %s, "
                                "data argument must not be given." %
                                domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            new_domain = list()
            for d in data.domain + [origin]:
                new_domain.extend(
                    [d - self._TIME_SHIFT, d, d + self._TIME_SHIFT])
            domain = sorted(set(new_domain))
        super(InstantaneousVolatilityCurve, self).__init__(
            domain, data, interpolation, origin, day_count, forward_tenor)

    def get_instantaneous_vol(self, start):
        return self(start)

    def get_terminal_vol(self, start, stop=None):
        if stop is None:
            return self.get_terminal_vol(self.origin, start)
        if start == stop:
            return self(start)
        if start > stop:
            return 0.0
        return self.integrate(start, stop)


class TerminalVolatilityCurve(VolatilityCurve):
    # class variable to set floor of volatility
    FLOOR = None

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_terminal_vol(x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        # if argument is a curve add extra curve points
        # to domain for better approximation
        if isinstance(domain, RateCurve):
            if data:
                raise TypeError("If first argument is %s, "
                                "data argument must not be given." %
                                domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            domain = sorted(set(list(data.domain) +
                                [origin + '1d', max(data.domain) + '10y']))
        super(TerminalVolatilityCurve, self).__init__(domain, data,
                                                      interpolation, origin,
                                                      day_count, forward_tenor)

    def get_instantaneous_vol(self, start):
        return self.get_terminal_vol(start, start + self.__class__._TIME_SHIFT)

    def get_terminal_vol(self, start, stop=None):
        if stop is None:
            return self(start)
        if start == self.origin:
            return self(stop)
        if start == stop:
            return self.get_instantaneous_vol(start)
        if start > stop:
            return 0.0

        var_start = self.day_count(self.origin, start) * self(start) ** 2
        var_end = self.day_count(self.origin, stop) * self(stop) ** 2
        var = (var_end - var_start) / self.day_count(start, stop)

        if var < 0.:
            r = self.origin, start, stop, self(start), self(
                stop), var_start, var_start, var
            m1 = 'Negative variance detected in %s' % repr(self)
            _logger.warning(m1)
            m2 = 'Negative variance detected at: %s' % ' '.join(map(str, r))
            _logger.warning(m2)
            if self.__class__.FLOOR is None:
                raise ZeroDivisionError(m1)
        var = max(var, self.__class__.FLOOR ** 2) \
            if self.__class__.FLOOR is not None else var

        return sqrt(var)

# class ForwardVolatilityCurve(TerminalVolatilityCurve):
#     def get_terminal_vol(self, start, stop=None):
#         if stop is None:
#             return self.get_terminal_vol(self.origin, start)
#         if start == stop:
#             return self.get_instantaneous_vol(start)
#         if start > stop:
#             return 0.0
#
#         last, vol = start, 0.0
#         for current in [s for s in self.domain if start <= s < stop]:
#             vol += (self(last) ** 2) * self.day_count(last, current)
#             last = current
#         vol += (self(last) ** 2) * self.day_count(last, stop)
#         vol = 0. if vol < 0. else vol
#         return sqrt(vol / self.day_count(start, stop))
