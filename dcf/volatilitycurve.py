# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import logging
from math import sqrt

from .curve import RateCurve
from .interpolation import zero, linear, constant
from .interpolationscheme import dyn_scheme

_logger = logging.getLogger('dcf')


class VolatilityCurve(RateCurve):
    """ generic curve for default probabilities (under construction) """
    _time_shift = '1d'
    _interpolation = dyn_scheme(zero, linear, constant)

    def cast(self, cast_type, **kwargs):
        old_domain = kwargs.get('domain', self.domain)

        if issubclass(cast_type, (TerminalVolatilityCurve)):
            domain = kwargs.get('domain', self.domain)
            origin = kwargs.get('origin', self.origin)
            new_domain = list(domain) + [origin + '1d'] + [max(domain) + '10y']
            kwargs['domain'] = sorted(set(new_domain))

        if False:
            domain = kwargs.get('domain', self.domain)
            new_domain = list(domain) + [max(domain) + '1y']
            kwargs['domain'] = sorted(set(new_domain))

        if issubclass(cast_type, (InstantaneousVolatilityCurve)):
            domain = kwargs.get('domain', self.domain)
            origin = kwargs.get('origin', self.origin)
            new_domain = list()
            for d in domain + [origin]:
                new_domain.extend([d - cast_type._time_shift, d, d + cast_type._time_shift])
            kwargs['domain'] = sorted(set(new_domain))

        return super(VolatilityCurve, self).cast(cast_type, **kwargs)

    def get_instantaneous_vol(self, start):
        raise NotImplementedError

    def get_terminal_vol(self, start, stop=None):
        raise NotImplementedError


class InstantaneousVolatilityCurve(VolatilityCurve):

    @staticmethod
    def get_storage_type(curve, x):
        return curve.get_instantaneous_vol(x)

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
    def get_storage_type(curve, x):
        return curve.get_terminal_vol(x)

    def get_instantaneous_vol(self, start):
        return self.get_terminal_vol(start, start + self.__class__._time_shift)

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
            r = self.origin, start, stop, self(start), self(stop), var_start, var_start, var
            m1 = 'Negative variance detected in %s' % repr(self)
            _logger.warning(m1)
            m2 = 'Negative variance detected at: %s' % ' '.join(map(str, r))
            _logger.warning(m2)
            if self.__class__.FLOOR is None:
                raise ZeroDivisionError(m1)
        var = max(var, self.__class__.FLOOR**2) if self.__class__.FLOOR is not None else var

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
