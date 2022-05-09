# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .curve import DateCurve
from .interestratecurve import ZeroRateCurve
from dcf.interpolation import log_linear_scheme


class Price(object):
    @property
    def value(self):
        return self._value

    @property
    def origin(self):
        return self._origin

    def __init__(self, value=0., origin=None):
        self._value = value
        self._origin = origin

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return '%s(%f; %s)' % \
               (self.__class__.__name__, self.value, str(self.origin))


class ForwardCurve(DateCurve):
    """ forward price curve with yield extrapolation """
    _INTERPOLATION = log_linear_scheme

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, yield_curve=0.0):
        if not data:
            if isinstance(domain, float):
                # build lists from single spot price value
                data = [domain]
                domain = [origin]
            elif isinstance(domain, Price):
                # build lists from single spot price
                origin = domain.origin
                data = [domain.value]
                domain = [domain.origin]
        super().__init__(domain, data, interpolation, origin, day_count)
        if isinstance(yield_curve, float) and self.origin is not None:
            yield_curve = ZeroRateCurve([self.origin], [yield_curve])
        self.yield_curve = yield_curve

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return [self(xx) for xx in x]
        else:
            return self.get_forward_price(x)

    def get_forward_price(self, value_date):
        """ asset forward price at **value_date**

        derived by interpolation on given forward prices
        and extrapolation by given discount_factor resp. yield curve

        :param value_date: date
        :return: asset forward price at **value_date**
        """
        last_date = self.domain[-1]
        if value_date <= last_date:
            return super().__call__(value_date)
        last_price = super().__call__(last_date)
        df = self.yield_curve.get_discount_factor(last_date, value_date)
        return last_price / df
