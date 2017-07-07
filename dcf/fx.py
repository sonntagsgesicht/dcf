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


class FxCurve(curve.DateCurve):
    """fx rate curve for currency pair"""

    @classmethod
    def cast(cls, fx_spot, domestic_curve=None, foreign_curve=None):
        """
        creator method to build FxCurve

        :param float fx_spot: fx spot rate
        :param RateCurve domestic_curve: domestic discount curve
        :param RateCurve foreign_curve: foreign discount curve
        :return:
        """
        assert domestic_curve.origin == foreign_curve.origin
        return cls(fx_spot, domestic_curve=domestic_curve, foreign_curve=foreign_curve)

    def __init__(self, x_list, y_list=None, y_inter=None, origin=None, day_count=None,
                 domestic_curve=None, foreign_curve=None):
        self.domestic_curve = domestic_curve
        self.foreign_curve = foreign_curve
        if origin is None:
            assert self.domestic_curve.origin == self.foreign_curve.origin
            origin = self.domestic_curve.origin
        if isinstance(x_list, float) and y_list is None:
            # build lists from single spot fx rate
            y_list = [x_list]
            x_list = [origin]
        else:
            assert len(x_list) == len(y_list)
        super(FxCurve, self).__init__(x_list, y_list, y_inter, origin, day_count)

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
    """
    FxDict factory object

    using triangulation over self.currency defined as a global container of fx information (mainly vs base currency)

    .. code-block:: python

        today = businessdate()
        curve = ZeroRateCurve([today], [.02])
        container = FxContainer('USD', curve)
        foreign = ZeroRateCurve([today], [.01])
        container.add('EUR', foreign, 1.2)
        fx_curve = container['USD', 'EUR']  # fx_curve is FxCurve
        fx_dict = container['USD']  # fx_dict is dict of FxCurves containing fx_curve
        container['USD']['EUR'](today) == container['USD', 'EUR'](today)  # True
    """

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
            assert isinstance(item, type(self.currency))
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
            assert isinstance(d, type(self.currency))
            assert isinstance(f, type(self.currency))
            assert isinstance(value, FxCurve)
            super(FxContainer, self).__setitem__(key, value)
        else:
            assert isinstance(key, type(self.currency))
            assert isinstance(value, FxCurve)
            assert value.domestic_curve == self.domestic_curve
            self.add(key, value.foreign_curve, value.get_fx_rate(self.domestic_curve.origin))

    def add(self, foreign_currency, foreign_curve=None, fx_spot=1.0):
        """
        adds contents to FxShelf.
        If curve is FxCurve or FxDict, spot should turn curve.currency into self.currency,
        else spot should turn currency into self.currency by
        N in EUR * spot = N in USD for currency = EUR and self.currency = USD
        """
        assert isinstance(foreign_currency, type(self.currency))
        assert isinstance(foreign_curve, curve.RateCurve)
        assert isinstance(fx_spot, float)

        # create missing FxCurves
        self[self.currency, foreign_currency] = FxCurve.cast(fx_spot, self.domestic_curve, foreign_curve)
        self[foreign_currency, self.currency] = FxCurve.cast(1 / fx_spot, foreign_curve, self.domestic_curve)
        # update relevant FxCurves
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
