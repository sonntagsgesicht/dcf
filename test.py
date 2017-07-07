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

import sys
from os import getcwd
from datetime import datetime
import unittest

from businessdate import BusinessDate, BusinessRange

from dcf import flat, linear, no, zero, left, right, nearest, spline, nak_spline
from dcf import Curve, DateCurve, DiscountFactorCurve, ZeroRateCurve, CashRateCurve, ShortRateCurve
from dcf import continuous_compounding, continuous_rate, periodic_compounding, periodic_rate
from dcf import FlatIntensityCurve, SurvivalProbabilityCurve, FlatIntensityCurve, HazardRateCurve
from dcf import FxCurve, FxContainer
from dcf.cashflow import CashFlowList, AmortizingCashFlowList, AnnuityCashFlowList, RateCashFlowList
from dcf.cashflow import MultiCashFlowList, FixedLoan, FloatLoan, FixedFloatSwap


class InterpolationUnitTests(unittest.TestCase):
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


class CubicSplineUnitTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_spline_linear(self):
        x = [0, 2, 4, 6]
        y0 = [5, 5.4, 5.8, 6.2]
        f = spline(x, y0)
        self.assertAlmostEqual(f(1), 5.2)
        self.assertAlmostEqual(f(3), 5.6)
        # self.assertRaises(ValueError, f(-1))

    def test_spline_quadratic(self):
        x = [0, 2, 4, 6]
        y1 = [1, 5, 17, 37]
        f = spline(x, y1, (2, 2))
        self.assertAlmostEqual(f(3), 9 + 1)
        self.assertAlmostEqual(f(5), 25 + 1)

    def test_importance_of_bordercondition(self):
        x = [0, 2, 4, 6]
        y1 = [1, 5, 17, 37]
        f = spline(x, y1, (0, 0))
        self.assertNotAlmostEqual(f(3), 9 + 1)
        self.assertNotAlmostEqual(f(5), 25 + 1)

    def test_spline_cubic(self):
        x = [0, 2, 4, 6]
        y2 = [0, 8, 64, 216]
        f = spline(x, y2, (0, 36))
        self.assertAlmostEqual(f(5), 125)

    def test_compare_with_data(self):
        file = open('test_data/cubic_spline.txt')
        self.read_data = False
        self.read_interpolation = False

        xdata = list()
        ydata = list()
        grid = list()
        interpolation_values = list()

        for line in file:
            if line.rstrip('\n') == 'DATAPOINTS':
                self.read_data = True
                self.read_interpolation = False
            elif line.rstrip('\n') == 'INTERPOLATIONPOINTS':
                self.read_data = False
                self.read_interpolation = True
            elif self.read_data:
                parts = line.rstrip().split(';')
                xdata.append(float(parts[0]))
                ydata.append(float(parts[1]))
            elif self.read_interpolation:
                parts = line.rstrip().split(';')
                grid.append(float(parts[0]))
                interpolation_values.append(float(parts[1]))

        file.close()

        f = spline(xdata, ydata)
        g = nak_spline(xdata, ydata)
        for point, value in zip(grid, interpolation_values):
            self.assertEqual(f(point), g(point))
            self.assertAlmostEqual(f(point), value, 12)


class CompoundingUnitTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_(self):
        self.assertTrue(True)


class CurveUnitTests(unittest.TestCase):
    def setUp(self):
        self.x_list = [float(x) * 0.01 for x in range(10)]
        self.y_list = list(self.x_list)
        self.curve = Curve(self.x_list, self.y_list)

    def test_addition(self):
        other = Curve(self.x_list, self.y_list)
        new = self.curve + other
        for x in new.domain:
            self.assertAlmostEqual(new(x), self.curve(x) * 2)


class DateCurveUnitTests(unittest.TestCase):
    def setUp(self):
        self.dates = BusinessRange(BusinessDate(), BusinessDate() + '10Y')
        self.values = [0.01 * n ** 4 - 2 * n ** 2 for n in range(0, len(self.dates))]
        self.curve = DateCurve(self.dates, self.values)

    def test_(self):
        for d in self.dates:
            self.assertTrue(d in self.curve.domain)
        d = BusinessDate() + '3M'
        self.curve.update([d], [0.01])
        self.assertTrue(d in self.curve.domain)
        self.assertEqual(d, self.curve.domain[1])

    def test_shift_origin(self):
        origin1 = BusinessDate()
        origin2 = BusinessDate() + "3m2d"
        Curve1 = DateCurve(self.dates, self.values, origin=origin1)
        Curve2 = DateCurve(self.dates, self.values, origin=origin2)
        for d in self.dates:
            self.assertAlmostEqual(Curve1(d), Curve2(d))


class FxUnitTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_(self):
        self.assertTrue(True)


class CashflowUnitTests(unittest.TestCase):
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

    suite = unittest.TestLoader().loadTestsFromModule(__import__("__main__"))
    testrunner = unittest.TextTestRunner(stream=sys.stdout, descriptions=2, verbosity=2)
    testrunner.run(suite)

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
