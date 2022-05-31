# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .curve import Price, ForwardCurve, RateCurve


class FxRate(Price):
    """price object for foreign currency exchange rates"""
    pass


class FxForwardCurve(ForwardCurve):

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, domestic_curve=None, foreign_curve=None):
        """ fx rate curve for currency pair """
        super().__init__(domain, data, interpolation, origin, day_count)
        self.domestic_curve = domestic_curve
        self.foreign_curve = foreign_curve

    def get_forward_price(self, value_date):
        last_date = self.domain[-1]
        if value_date <= last_date:
            return super().get_forward_price(value_date)
        else:
            y = super().get_forward_price(last_date)
            d = self.domestic_curve.get_discount_factor(last_date, value_date)
            f = self.foreign_curve.get_discount_factor(last_date, value_date)
            return y / f * d


'''
class FxCurveX(ForwardCurve):

    def __init__(self, domain=1., data=None, interpolation=None, origin=None,
                 day_count=None,
                 domestic_curve=None, foreign_curve=None):
        """ fx rate curve for currency pair """

        self.domestic_curve = domestic_curve
        self.foreign_curve = foreign_curve
        if origin is None:
            if not self.domestic_curve.origin == self.foreign_curve.origin:
                raise AssertionError()
            origin = self.domestic_curve.origin
        if data is None:
            if isinstance(domain, float):
                # build lists from single spot fx rate
                data = [domain]
                domain = [origin]
            elif isinstance(domain, Price):
                data = [domain.value]
                domain = [domain.origin]
                origin = None
        if not len(domain) == len(data):
            raise AssertionError()
        super(FxCurve, self).__init__(domain, data, interpolation, origin,
                                      day_count)

    def get_forward_price(self, value_date):
        last_date = self.domain[-1]
        if value_date <= last_date:
            return super(FxCurve, self).__call__(value_date)
        else:
            y = super(FxCurve, self).__call__(last_date)
            d = self.foreign_curve.get_discount_factor(last_date, value_date)
            d /= self.domestic_curve.get_discount_factor(last_date, value_date)
            return y * d
'''


class FxContainer(dict):
    """ FxDict factory object

    using triangulation over self.currency defined as a global container
    of fx information (mainly vs base currency)

    .. code-block:: python

        today = today()
        curve = ZeroRateCurve([today], [.02])
        container = FxContainer('USD', curve)
        foreign = ZeroRateCurve([today], [.01])
        container.add('EUR', foreign, 1.2)
        fx_curve = container['USD', 'EUR']  # fx_curve is FxCurve
        fx_dict = container['USD']  # dict of FxCurves containing fx_curve
        # returns True
        container['USD']['EUR'](today) == container['USD', 'EUR'](today)

    """

    # todo:
    #  First, searching for exact matching pair.
    #  Second, matching for swapped pair.
    #  Last, find linked pairs for triangulation,
    #  choosing based on a preference list of base currencies.

    def __init__(self, currency, domestic_curve):
        """
        :param currency: base currency of FxContainer
        :param RateCurve domestic_curve:
            base curve of FxContainer for discounting
        """
        super().__init__()
        self.currency = currency
        self.domestic_curve = domestic_curve
        self.add(currency, domestic_curve)

    def __getitem__(self, item):
        if item in self:
            return super(FxContainer, self).__getitem__(item)
        else:
            if not isinstance(item, type(self.currency)):
                raise AssertionError()
            # build corresponding dict of FxCurves
            # return dict([(f, self[d, f]) for d, f in self if d == item])
            fd = dict()
            for d, f in self:
                if d == item:
                    fd[f] = self[d, f]
            return fd

    def __setitem__(self, key, value):
        if isinstance(key, tuple) and len(key) == 2:
            d, f = key
            if not (isinstance(d, type(self.currency))
                    and isinstance(f, type(self.currency))
                    and isinstance(value, FxForwardCurve)):
                raise AssertionError()
            super(FxContainer, self).__setitem__(key, value)
        else:
            if not (isinstance(key, type(self.currency))
                    and isinstance(value, FxForwardCurve)
                    and value.domestic_curve == self.domestic_curve):
                raise AssertionError()
            self.add(key, value.foreign_curve,
                     value.get_forward_price(self.domestic_curve.origin))

    def add(self, foreign_currency, foreign_curve=None, fx_spot=1.0):
        """
        adds contents to FxShelf.
        If curve is FxCurve or FxDict,
        spot should turn curve.currency into self.currency,
        else spot should turn currency into self.currency by
        N in EUR * spot = N in USD for currency = EUR and self.currency = USD
        """
        if not (isinstance(foreign_currency, type(self.currency))
                and isinstance(foreign_curve, RateCurve)
                and isinstance(fx_spot, float)):
            raise AssertionError()

        # create missing FxCurves
        self[self.currency, foreign_currency] = \
            FxForwardCurve([self.domestic_curve.origin], [fx_spot],
                           domestic_curve=self.domestic_curve,
                           foreign_curve=foreign_curve)
        self[foreign_currency, self.currency] = \
            FxForwardCurve([self.domestic_curve.origin], [1 / fx_spot],
                           domestic_curve=self.domestic_curve,
                           foreign_curve=foreign_curve)
        # _update relevant FxCurves
        f = foreign_currency
        new = dict()
        for d, s in self:
            if s is self.currency and d is not foreign_currency:
                triangulated = self[d, s](self.domestic_curve.origin) * fx_spot
                if (d, f) in self:
                    self[d, f].foreign_curve = foreign_curve
                    self[d, f].fx_spot = triangulated
                    self[f, d].domestic_curve = foreign_curve
                    self[f, d].fx_spot = 1 / triangulated
                else:
                    new[d, f] = FxForwardCurve(
                        [self.domestic_curve.origin], [triangulated],
                        domestic_curve=self[d, s].domestic_curve,
                        foreign_curve=foreign_curve)
                    new[f, d] = FxForwardCurve(
                        [self.domestic_curve.origin], [1 / triangulated],
                        domestic_curve=foreign_curve,
                        foreign_curve=self[d, s].domestic_curve)
        self.update(new)

    def get_forward_price(self, domestic_currency, foreign_currency,
                          value_date):
        return self[domestic_currency, foreign_currency].get_forward_price(
            value_date)
