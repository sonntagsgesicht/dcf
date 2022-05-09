# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from unittest import TestCase

from businessdate import BusinessDate, BusinessRange

from dcf.compounding import simple_compounding, continuous_rate
from dcf import ZeroRateCurve, DiscountFactorCurve, ShortRateCurve, CashRateCurve


class InterestRateCurveUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate()
        self.domain = BusinessRange(self.today, self.today + '1Y', '3M')
        self.len = len(self.domain)
        self.periods = ('1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

    def test_zero_rate_curve(self):
        rate = 0.02
        curve = ZeroRateCurve(self.domain, [rate] * self.len)
        for d in self.domain:
            for p in self.periods:
                self.assertAlmostEqual(curve.get_discount_factor(d + p, d + p), 1.)

                self.assertAlmostEqual(curve.get_zero_rate(self.today, d + p), rate)
                self.assertAlmostEqual(curve.get_short_rate(d + p), rate)
                yf = curve.day_count(d + p, (d + p) + curve.forward_tenor)
                cr = simple_compounding(curve.get_cash_rate(d + p), yf)
                self.assertAlmostEqual(continuous_rate(cr, yf), rate)

    def test_discount_factor_curve(self):
        zr_curve = ZeroRateCurve([self.today, self.today + '1d'], [.02, .02])
        df_curve = DiscountFactorCurve(zr_curve.domain, [1., zr_curve.get_discount_factor(self.today + '1d')])
        for p in self.periods:
            x = self.today + p
            self.assertAlmostEqual(df_curve.get_discount_factor(x, x), 1.)
            z = zr_curve.get_zero_rate(x)
            d = df_curve.get_zero_rate(x)
            self.assertAlmostEqual(z, d)
            z = zr_curve.get_discount_factor(x)
            d = df_curve.get_discount_factor(x)
            self.assertAlmostEqual(z, d)
            z = zr_curve.get_short_rate(x)
            d = df_curve.get_short_rate(x)
            self.assertAlmostEqual(z, d)
            z = zr_curve.get_cash_rate(x)
            d = df_curve.get_cash_rate(x)
            self.assertAlmostEqual(z, d)


class CastZeroRateCurveUnitTests(TestCase):
    def setUp(self):
        self.cast_type = ZeroRateCurve
        self.grid = ['0D', '3M', '12M']
        self.points = [0.02, 0.01, 0.015]
        self.grid = ['0D', '1M', '2M', '3M', '4M', '5M', '6M', '1Y']
        self.points = [0.02, 0.018, 0.0186, 0.018, 0.0167, 0.0155, 0.015, 0.015]

        self.precision = 10
        self.cash_precision = 2

        self.today = BusinessDate()
        self.today_eom = self.today == self.today.end_of_month()
        self.periods = ('0D', '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

        def pp(d, a, b):
            print((d, abs(a(d) - b(d)) < self.precision, a(d), b(d)))

        self.pp = pp

        def curve(p='0D'):
            grid = [self.today + p + _ for _ in self.grid]
            return self.cast_type(grid, self.points)

        self.curve = curve

    def test_interpolation(self):
        curve = self.curve()
        for t in (DiscountFactorCurve, ZeroRateCurve, ShortRateCurve):
            cast = t(curve)
            curve.cast(t)
            recast = self.cast_type(cast)
            self.assertEqual(self.cast_type._INTERPOLATION, curve._INTERPOLATION)
            self.assertEqual(t._INTERPOLATION, cast._INTERPOLATION)
            self.assertEqual(self.cast_type._INTERPOLATION, recast._INTERPOLATION)

    def test_discount_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(DiscountFactorCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_zero_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(ZeroRateCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_short_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(ShortRateCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_cash1m_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(CashRateCurve(curve, forward_tenor='1M'))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.cash_precision)

    def test_cash3m_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(CashRateCurve(curve, forward_tenor='3M'))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.cash_precision)


class CastDiscountFactorCurveUnitTests(CastZeroRateCurveUnitTests):
    def setUp(self):
        super(CastDiscountFactorCurveUnitTests, self).setUp()
        self.cast_type = DiscountFactorCurve
        self.grid = ['0D', '3M', '12M']
        self.points = [1., 0.9999, 0.997]


class CastShortRateCurveUnitTests(CastZeroRateCurveUnitTests):
    def setUp(self):
        super(CastShortRateCurveUnitTests, self).setUp()
        self.cast_type = ShortRateCurve


class CastCashRateCurveUnitTests(CastZeroRateCurveUnitTests):
    def setUp(self):
        super(CastCashRateCurveUnitTests, self).setUp()
        self.cast_type = CashRateCurve
        self.precision = 2
        self.cash_precision = 10
