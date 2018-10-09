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

import logging
from math import sqrt

from curve import DateCurve
from interpolation import zero, linear, constant

_logger = logging.getLogger('dcf')


class VolatilityCurve(DateCurve):
    """ generic curve for default probabilities (under construction) """
    _time_shift = '1d'
    _interpolation = zero(), linear(), constant()

    def cast(self, cast_type, **kwargs):
        old_domain = kwargs.get('domain', self.domain)

        if issubclass(cast_type, (TerminalVolatilityCurve)):
            domain = kwargs.get('domain', self.domain)
            origin = kwargs.get('origin', self.origin)
            new_domain = list(domain) + [origin + '1d']
            kwargs['domain'] = sorted(set(new_domain))

        if True:
            domain = kwargs.get('domain', self.domain)
            new_domain = list(domain) + [max(domain) + '1y']
            kwargs['domain'] = sorted(set(new_domain))

        if issubclass(cast_type, ()):
            domain = kwargs.get('domain', self.domain)
            new_domain = list(domain)
            kwargs['domain'] = sorted(set(new_domain))

        return super(VolatilityCurve, self).cast(cast_type, **kwargs)

    def get_instantaneous_vol(self, start):
        raise NotImplementedError

    def get_terminal_vol(self, start, stop=None):
        raise NotImplementedError


class InstantaneousVolatilityCurve(VolatilityCurve):
    def get_instantaneous_vol(self, start):
        return self(start)

    def get_terminal_vol(self, start, stop=None):
        if stop is None:
            return self.get_terminal_vol(self.origin, start)
        if start == stop:
            return self(start)
        if start > stop:
            return 0.0

        current = start
        vol = 0.0
        step = self.__class__._time_shift

        while current + step < stop:
            vol += self(current) * self.day_count(current, current + step)
            current += step

        vol += self(current) * self.day_count(current, stop)
        return vol / self.day_count(start, stop)


class TerminalVolatilityCurve(VolatilityCurve):
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
        var = var_end - var_start
        if var < 0.:
            r = self.origin, start, stop, self(start), self(stop), var_start, var_start, var
            m = 'Negative variance detected in %s at: %s' % (repr(self), ' '.join(map(str, r)))
            print m
            _logger.warning(m)

        var = 0. if var < 0. else var
        se = self.day_count(start, stop)
        return sqrt(var / se)


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
