# -*- coding: utf-8 -*-

#  dcf (discounted cashflow)
#  -------------------------
#  A Python library for generating discounted cashflows.
#  Typical banking business methods are provided like interpolation, compounding,
#  discounting and fx.
#
#  Author:  pbrisk <pbrisk@icloud.com>
#  Copyright: 2016, 2017 Deutsche Postbank AG
#  Website: https://github.com/pbrisk/dcf
#  License: APACHE Version 2 License (see LICENSE file)


from os import getcwd
from datetime import datetime
from unittest import TestCase, main

from businessdate import BusinessDate, BusinessRange
from dcf.interpolation import flat, linear, no, zero, left, right, nearest
from dcf.compounding import continuous_compounding, continuous_rate
from dcf.compounding import periodic_compounding, periodic_rate
from dcf.curve import Curve, DateCurve, DiscountFactorCurve, ZeroRateCurve, CashRateCurve, ShortRateCurve
from dcf.curve import FlatIntensityCurve, SurvivalProbabilityCurve, FlatIntensityCurve, HazardRateCurve
from dcf.fx import FxCurve, FxContainer
from dcf.cashflow import CashFlowList, AmortizingCashFlowList, AnnuityCashFlowList, RateCashFlowList
from dcf.cashflow import MultiCashFlowList, FixedLoan, FloatLoan, FixedFloatSwap


class InterpolationUnitTests(TestCase):
    def setUp(self):
        self.a = 0.0
        self.b = 0.01
        self.x = [1., 2., 3.]
        self.y = [self.a + self.b * x for x in self.x]
        self.s = [.0, .1, .2, .3, .4, .5, .6, .7, .8, .9]

    def test_flat(self):
        f = flat(0.01)
        for x in self.x:
            for s in self.s:
                self.assertAlmostEquals(f(x + 2), 0.01)

    def test_linear(self):
        f = linear(self.x, self.y)
        for x in [0.] + self.x:
            for s in self.s:
                self.assertAlmostEquals(f(x + s), self.a + self.b * (x + s))

    def test_no(self):
        f = no(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEquals(f(x), y)
        for x in self.x:
            self.assertRaises(ValueError, lambda: f(x + 0.001))

    def test_zero(self):
        f = zero(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEquals(f(x), y)
        for x in self.x:
            self.assertAlmostEquals(f(x + 0.001), .0)
            self.assertAlmostEquals(f(x - 0.001), .0)

    def test_left(self):
        f = left(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEquals(f(x), y)
        for x in [0.] + self.x + [4.]:
            for s in self.s:
                if x + s < self.x[0]:
                    y = self.y[0]
                elif x + s in self.x:
                    y = self.y[self.x.index(x + s)]
                elif x + s < self.x[-1]:
                    y = self.y[self.x.index(x)]
                else:
                    y = self.y[-1]
                self.assertAlmostEquals(f(x + s), y)

    def test_right(self):
        f = right(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEquals(f(x), y)
        for x in [0.] + self.x + [4.]:
            for s in self.s:
                if x + s <= self.x[0]:
                    y = self.y[0]
                elif x + s in self.x:
                    y = self.y[self.x.index(x + s)]
                elif x + s < self.x[-1]:
                    y = self.y[self.x.index(x) + 1]
                else:
                    y = self.y[-1]
                self.assertAlmostEquals(f(x + s), y)

    def test_nearest(self):
        f = nearest(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEquals(f(x), y)
        for x in [0.] + self.x + [4.]:
            for s in self.s:
                if x + s <= self.x[0]:
                    y = self.y[0]
                elif x + s in self.x:
                    y = self.y[self.x.index(x + s)]
                elif x + s < self.x[-1]:
                    i = self.x.index(x)
                    if s < self.x[i + 1] - x - s:
                        y = self.y[i]
                    else:
                        y = self.y[i + 1]
                else:
                    y = self.y[-1]
                self.assertAlmostEquals(f(x + s), y)

    def test_update(self):
        f = linear(self.x, self.y)
        for s in self.s:
            if s in self.x:
                self.assertTrue(s in f)
            else:
                self.assertFalse(s in f)
        y = [f(s) for s in reversed(self.s)]
        ff = no()
        ff.update(self.s, y)
        for s in self.s:
            self.assertTrue(s in ff)
        for s, e in zip(ff.x_list[:1], ff.x_list[1:]):
            self.assertTrue(s < e)
        for s in self.s:
            self.assertTrue(s in ff)
            ff.update([s])
            self.assertFalse(s in ff)


class CompoundingUnitTests(TestCase):
    def setUp(self):
        pass

    def test_(self):
        self.assertTrue(True)


class CurveUnitTests(TestCase):
    def setUp(self):
        self.x_list = [float(x)*0.01 for x in range(10)]
        self.y_list = list(self.x_list)
        self.curve = Curve(self.x_list, self.y_list)

    def test_(self):
        other = Curve(self.x_list, self.y_list)
        new = self.curve + other
        for x in new.domain:
            self.assertAlmostEqual(new(x), self.curve(x)*2)


class DateCurveUnitTests(TestCase):
    def setUp(self):
        self.dates = BusinessRange(BusinessDate(), BusinessDate()+'10Y')
        self.values = [0.01] * len(self.dates)
        self.curve = DateCurve(self.dates, self.values)

    def test_(self):
        for d in self.dates:
            self.assertTrue(d in self.curve.domain)
        d = BusinessDate() + '3M'
        self.curve.update([d], [0.01])
        self.assertTrue(d in self.curve.domain)
        self.assertEqual(d, self.curve.domain[1])


class FxUnitTests(TestCase):
    def setUp(self):
        pass

    def test_(self):
        self.assertTrue(True)


class CashflowUnitTests(TestCase):
    def setUp(self):
        pass

    def test_(self):
        self.assertTrue(True)


if __name__ == "__main__":
    start_time = datetime.now()

    print('')
    print('======================================================================')
    print('')
    print('run %s' % __file__)
    print('in %s' % getcwd())
    print('started  at %s' % str(start_time))
    print('')
    print('----------------------------------------------------------------------')
    print('')

    main(verbosity=2)

    print('')
    print('======================================================================')
    print('')
    print('ran %s' % __file__)
    print('in %s' % getcwd())
    print('started  at %s' % str(start_time))
    print('finished at %s' % str(datetime.now()))
    print('')
    print('----------------------------------------------------------------------')
    print('')
