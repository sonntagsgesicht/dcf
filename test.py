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
from dcf import compounding

from dcf import flat, linear, no, zero, left, right, nearest, spline, nak_spline
from dcf import continuous_compounding, continuous_rate, periodic_compounding, periodic_rate, \
    simple_compounding, simple_rate
from dcf import Curve, DateCurve
from dcf import DiscountFactorCurve, ZeroRateCurve, CashRateCurve, ShortRateCurve
from dcf import SurvivalProbabilityCurve, FlatIntensityCurve, HazardRateCurve
from dcf import FxCurve, FxContainer
from dcf import CashFlowList, AmortizingCashFlowList, AnnuityCashFlowList, RateCashFlowList
from dcf import MultiCashFlowList, FixedLoan, FloatLoan, FixedFloatSwap
from dcf import RatingClass


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
    def test_(self):
        for t in (0.012, 0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 5.0):
            rate = 0.01
            factor = continuous_compounding(rate, t)
            self.assertAlmostEqual(continuous_rate(factor, t), rate)

            factor = 0.5
            rate = continuous_rate(factor, t)
            self.assertAlmostEqual(continuous_compounding(rate, t), factor)

            rate = 0.01
            factor = simple_compounding(rate, t)
            self.assertAlmostEqual(simple_rate(factor, t), rate)

            factor = 0.5
            rate = simple_rate(factor, t)
            self.assertAlmostEqual(simple_compounding(rate, t), factor)

            for p in (1, 2, 4, 12, 365):
                rate = 0.01
                factor = periodic_compounding(rate, t, p)
                self.assertAlmostEqual(periodic_rate(factor, t, p), rate)

                factor = 0.5
                rate = periodic_rate(factor, t, p)
                self.assertAlmostEqual(periodic_compounding(rate, t, p), factor)


class CurveUnitTests(unittest.TestCase):
    def setUp(self):
        self.x_list = [float(x) * 0.01 for x in range(10)]
        self.y_list = list(self.x_list)
        self.curve = Curve(self.x_list, self.y_list)

    def test_algebra(self):
        other = Curve(self.x_list, self.y_list)
        new = self.curve + other
        for x in new.domain:
            self.assertAlmostEqual(new(x), self.curve(x) * 2.)

        new = self.curve - other
        for x in new.domain:
            self.assertAlmostEqual(new(x), 0.)

        new = self.curve * other
        for x in new.domain:
            self.assertAlmostEqual(new(x), self.curve(x) ** 2)

        self.assertRaises(ZeroDivisionError, self.curve.__div__, other)

        new = self.curve / Curve(self.x_list, [0.1] * len(self.x_list))
        for x in new.domain:
            self.assertAlmostEqual(new(x), self.curve(x) / 0.1)


class DateCurveUnitTests(unittest.TestCase):
    def setUp(self):
        self.dates = BusinessRange(BusinessDate(), BusinessDate() + '10Y')
        self.values = [0.01 * n ** 4 - 2 * n ** 2 for n in range(0, len(self.dates))]
        self.curve = DateCurve(self.dates, self.values)

    def test_dates(self):
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


class InterestRateCurveUnitTests(unittest.TestCase):
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
                self.assertAlmostEqual(curve.get_cash_rate(d + p), rate, 3)

        curve = ZeroRateCurve([self.today, self.today + '1y'], [0.01, 0.02])
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            self.assertTrue(min(curve(curve.domain)) <= curve.get_zero_rate(self.today, self.today + p))
            self.assertTrue(curve.get_zero_rate(self.today, self.today + p) <= max(curve(curve.domain)))

            l = curve.get_zero_rate(self.today, self.today + p - '1B')
            m = curve.get_zero_rate(self.today, self.today + p)
            u = curve.get_zero_rate(self.today, self.today + p + '1B')
            # print l <= m <= u, p, l, m, u
            self.assertTrue(l <= m <= u)

        for p, q, r in zip(self.periods[:-2], self.periods[1:-1], self.periods[2:]):
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            l = curve.get_zero_rate(self.today, self.today + p)
            m = curve.get_zero_rate(self.today, self.today + q)
            u = curve.get_zero_rate(self.today, self.today + r)
            # print l < m < u, p, l, m, u
            self.assertTrue(l < m < u)

        curve = ZeroRateCurve([self.today, self.today + '1y'], [0.01, 0.02])
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            z = curve.get_zero_rate(self.today, self.today + p)
            s = curve.get_short_rate(self.today + p)
            c = curve.get_cash_rate(self.today + p, step='1M')
            # print z <= s <= c, p, z, s, c
            self.assertTrue(z <= s <= c)

        curve = ZeroRateCurve([self.today, self.today + '1y'], [0.02, 0.01])
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            z = curve.get_zero_rate(self.today, self.today + p)
            s = curve.get_short_rate(self.today + p) - 1E-16  # mismatch due to numerical issues
            c = curve.get_cash_rate(self.today + p, step='1M') - 1E-5  # mismatch due to simple compounding
            # print z >= s >= c, p, z, s, c
            self.assertTrue(z >= s >= c)

    def test_discount_factor_curve(self):
        curve = DiscountFactorCurve([self.today, self.today + '2y'], [1.0, 0.9])
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            z = curve.get_zero_rate(self.today, self.today + p)
            s = curve.get_short_rate(self.today + p)
            c = curve.get_cash_rate(self.today + p, step='1M')
            # print z <= s <= c, p, z, s, c
            self.assertTrue(z <= s <= c)

    def _test_short_rate_curve(self):
        curve = ShortRateCurve([self.today, self.today + '3M'], [0.01, 0.02])
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            z = curve.get_zero_rate(self.today, self.today + p)
            s = curve.get_short_rate(self.today + p)
            c = curve.get_cash_rate(self.today + p, step='1M')
            # print z <= s <= c, p, z, s, c
            self.assertTrue(z <= s <= c)

        curve = ShortRateCurve([self.today, self.today + '3M'], [0.02, 0.01])
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            z = curve.get_zero_rate(self.today, self.today + p)
            s = curve.get_short_rate(self.today + p)
            c = curve.get_cash_rate(self.today + p, step='1M') - 1E-5  # mismatch due to simple compounding
            # print z >= s >= c, p, z, s, c
            self.assertTrue(z >= s >= c)

    def test_cash_rate_curve(self):
        curve = CashRateCurve([self.today, self.today + '3M'], [0.01, 0.02], forward_tenor='1M')
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            z = curve.get_zero_rate(self.today, self.today + p)
            s = curve.get_short_rate(self.today + p)
            c = curve.get_cash_rate(self.today + p, step='1M')
            # print z <= s <= c, p, z, s, c
            # self.assertTrue(z <= s <= c)

        curve = CashRateCurve([self.today, self.today + '3M'], [0.02, 0.01], forward_tenor='1M')
        for p in self.periods:
            self.assertAlmostEqual(curve.get_discount_factor(self.today + p, self.today + p), 1.)

            z = curve.get_zero_rate(self.today, self.today + p)
            s = curve.get_short_rate(self.today + p)
            c = curve.get_cash_rate(self.today + p, step='1M') - 1E-4  # mismatch due to simple compounding
            # print z >= s >= c, p, z, s, c
            self.assertTrue(z >= s >= c)

    def test_cast_zero(self):
        zero = ZeroRateCurve([self.today, self.today + '3M', self.today + '12M'], [0.02, 0.01, 0.015])

        cast = ZeroRateCurve.cast(DiscountFactorCurve.cast(zero))
        for d in zero.domain:
            # print d, zero(d) == cast(d), zero(d), cast(d)
            self.assertAlmostEqual(cast(d), zero(d), 14)

        cast = ZeroRateCurve.cast(ShortRateCurve.cast(zero))
        for d in zero.domain:
            print d, zero(d) == cast(d), zero(d), cast(d)
            #self.assertAlmostEqual(cast(d), zero(d))

        cast = ZeroRateCurve.cast(CashRateCurve.cast(zero, '1M'))
        for d in zero.domain:
            # print d, zero(d) == cast(d), zero(d), cast(d)
            self.assertAlmostEqual(cast(d), zero(d), 3)

        cast = ZeroRateCurve.cast(CashRateCurve.cast(zero, '3M'))
        for d in zero.domain:
            #print d, zero(d) == cast(d), zero(d), cast(d)
            self.assertAlmostEqual(cast(d), zero(d), 5)


class CreditCurveUnitTests(unittest.TestCase):
    def test_survival_curve(self):
        pass

    def test_intensity_curve(self):
        pass

    def test_hazard_rate_curve(self):
        pass


class FxUnitTests(unittest.TestCase):
    def test_(self):
        pass


class CashflowUnitTests(unittest.TestCase):
    def test_(self):
        pass


class RatingClassUnitTets(unittest.TestCase):
    def test_rating_class_without_master_scale(self):
        self.assertRaises(TypeError, RatingClass, '*')

        r = RatingClass(masterscale=('A', 'B', 'C', 'D'))
        self.assertRaises(ValueError, list, r)

        r = RatingClass(0.2)
        self.assertEqual(repr(r), 'RatingClass(0.2000000)')
        self.assertEqual(str(r), repr(r))
        self.assertEqual(r.masterscale, None)
        self.assertEqual(list(r), [])

    def test_rating_class_with_master_scale(self):
        r = RatingClass(value=0.000001, masterscale=('A', 'B', 'C', 'D'))
        self.assertAlmostEqual(float(r), 0.000001)
        self.assertRaises(ValueError, list, r)

        r = RatingClass(value=0.3, masterscale=('A', 'B', 'C', 'D'))
        self.assertAlmostEqual(float(r), 0.3)
        self.assertAlmostEquals(list(r), [0., 0., 0.7777778, 0.2222222])
        self.assertEqual(str(r), '0.7777778 C + 0.2222222 D')
        self.assertEqual(repr(r), str(r) + '-RatingClass(0.3000000)')

        self.assertEqual(len(list(r)), len(r.masterscale))
        self.assertAlmostEqual(sum(list(r)), 1.)
        self.assertAlmostEqual(min(list(r)), 0.)

    def test_master_scale_rating_classes(self):
        r = RatingClass(value=0.3, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual(r.masterscale.keys(), ['A', 'B', 'C', 'D'])
        self.assertEqual(str(r.masterscale),
                         '[A-RatingClass(0.0010000), B-RatingClass(0.0100000), C-RatingClass(0.1000000), D-RatingClass(1.0000000)]')
        self.assertEqual(repr(r.masterscale),
                         'master_scale(A-RatingClass(0.0010000), B-RatingClass(0.0100000), C-RatingClass(0.1000000), D-RatingClass(1.0000000))')

        for y, z in r.masterscale.items():
            x = RatingClass(z, r.masterscale)
            self.assertEqual(str(x), y)
            self.assertEqual(repr(x), '%s-RatingClass(%.7f)' % (y, z))

        for i, (x, y) in enumerate(r.masterscale.items()):
            self.assertAlmostEqual(10 ** (len(r.masterscale) - i) * y, 10)
            vec = list(RatingClass(y, r.masterscale))
            self.assertEqual(vec.pop(i), 1.)
            self.assertAlmostEqual(max(vec), 0.)
            self.assertAlmostEqual(min(vec), 0.)

        for k in r.masterscale:
            r.masterscale[k] = -1.
        self.assertEqual(r.masterscale.values(), [-1.] * len(r.masterscale))


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
