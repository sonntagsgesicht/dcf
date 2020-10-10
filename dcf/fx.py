# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .curve import DateCurve, RateCurve


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
        return '%s(%f; %s)' % (self.__class__.__name__, self.value, str(self.origin))


class FxRate(Price):
    pass


class FxCurve(DateCurve):
    @classmethod
    def cast(cls, fx_spot, domestic_curve=None, foreign_curve=None):
        """ creator method to build FxCurve """
        if not domestic_curve.origin == foreign_curve.origin:
            raise AssertionError()
        return cls(fx_spot, domestic_curve=domestic_curve, foreign_curve=foreign_curve)

    def __init__(self, domain=1., data=None, interpolation=None, origin=None, day_count=None,
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
        super(FxCurve, self).__init__(domain, data, interpolation, origin, day_count)

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return [self(xx) for xx in x]
        else:
            return self.get_fx_rate(x)

    def get_fx_rate(self, value_date):
        last_date = self.domain[-1]
        if value_date <= last_date:
            return super(FxCurve, self).__call__(value_date)
        else:
            y = super(FxCurve, self).__call__(last_date)
            return y * self.foreign_curve.get_discount_factor(last_date, value_date) / \
                   self.domestic_curve.get_discount_factor(last_date, value_date)


class FxContainer(dict):
    """ FxDict factory object

    using triangulation over self.currency defined as a global container of fx information (mainly vs base currency)

    .. code-block:: python

        today = today()
        curve = ZeroRateCurve([today], [.02])
        container = FxContainer('USD', curve)
        foreign = ZeroRateCurve([today], [.01])
        container.add('EUR', foreign, 1.2)
        fx_curve = container['USD', 'EUR']  # fx_curve is FxCurve
        fx_dict = container['USD']  # fx_dict is dict of FxCurves containing fx_curve
        container['USD']['EUR'](today) == container['USD', 'EUR'](today)  # True
    """

    # todo: First, searching for exact matching pair.
    # todo: Second, matching for swapped pair.
    # todo: Last, find linked pairs for triangulation,
    # todo: choosing based on a preference list of base currencies.

    def __init__(self, currency, domestic_curve):
        """
        :param currency: base currency of FxContainer
        :param RateCurve domestic_curve: base curve of FxContainer for discounting
        """

        super(FxContainer, self).__init__()
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
                    and isinstance(value, FxCurve)):
                raise AssertionError()
            super(FxContainer, self).__setitem__(key, value)
        else:
            if not (isinstance(key, type(self.currency))
                    and  isinstance(value, FxCurve)
                    and value.domestic_curve == self.domestic_curve):
                raise AssertionError()
            self.add(key, value.foreign_curve, value.get_fx_rate(self.domestic_curve.origin))

    def add(self, foreign_currency, foreign_curve=None, fx_spot=1.0):
        """
        adds contents to FxShelf.
        If curve is FxCurve or FxDict, spot should turn curve.currency into self.currency,
        else spot should turn currency into self.currency by
        N in EUR * spot = N in USD for currency = EUR and self.currency = USD
        """
        if not (isinstance(foreign_currency, type(self.currency))
                and isinstance(foreign_curve, RateCurve)
                and isinstance(fx_spot, float)):
            raise AssertionError()

        # create missing FxCurves
        self[self.currency, foreign_currency] = FxCurve.cast(fx_spot, self.domestic_curve, foreign_curve)
        self[foreign_currency, self.currency] = FxCurve.cast(1 / fx_spot, foreign_curve, self.domestic_curve)
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
                    new[d, f] = FxCurve.cast(triangulated, self[d, s].domestic_curve, foreign_curve)
                    new[f, d] = FxCurve.cast(1 / triangulated, foreign_curve, self[d, s].domestic_curve)
        self.update(new)

    def get_fx_rate(self, domestic_currency, foreign_currency, value_date):
        return self[domestic_currency, foreign_currency].get_fx_rate(value_date)

    def get_forward(self, domestic_currency, foreign_currency, value_date):
        return self.get_fx_rate(domestic_currency, foreign_currency, value_date)
