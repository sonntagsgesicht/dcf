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

from sys import stdout
from os import getcwd
from datetime import datetime
from unittest import TestCase, TestLoader, TextTestRunner
import logging

from math import exp, log
from businessdate import BusinessDate, BusinessRange

from dcf import flat, linear, no, zero, left, right, nearest, spline, nak_spline, loglinearrate, logconstantrate, \
    loglinear, logconstant, constant
from dcf import continuous_compounding, continuous_rate, periodic_compounding, periodic_rate, \
    simple_compounding, simple_rate
from dcf import Curve, DateCurve
from dcf import DiscountFactorCurve, ZeroRateCurve, CashRateCurve, ShortRateCurve
from dcf import SurvivalProbabilityCurve, DefaultProbabilityCurve, FlatIntensityCurve, HazardRateCurve, \
    MarginalSurvivalProbabilityCurve, MarginalDefaultProbabilityCurve
from dcf import FxCurve, FxContainer
from dcf import CashFlowList, AmortizingCashFlowList, AnnuityCashFlowList, RateCashFlowList
from dcf import MultiCashFlowList, FixedLoan, FloatLoan, FixedFloatSwap
from dcf import RatingClass

logging.basicConfig()
# h = logging.StreamHandler()
# h.setFormatter(logging.Formatter('%(asctime)s %(module)-18s %(levelname)-8s %(message)-120s', '%Y%m%d %H%M%S'))
# logging.getLogger('dcf').addHandler(h)


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

    def test_logyxlinear(self):
        yy = [x * .5 for x in self.x]
        log_yy = [-log(y) / x for x, y in zip(self.x, yy)]
        lin = linear(self.x, log_yy)
        loglin = loglinearrate(self.x, yy)
        for w in [0.25]:
            for x in self.s:
                x = 0.01 + x * w
                self.assertAlmostEqual(loglin(x), exp(-lin(x) * x))

    def test_logyxconstant(self):
        yy = [x * .5 for x in self.x]
        log_yy = [-log(y) / x for x, y in zip(self.x, yy)]
        lin = constant(self.x, log_yy)
        loglin = logconstantrate(self.x, yy)
        for w in [0.25]:
            for x in self.s:
                x = 0.01 + x * w
                self.assertAlmostEqual(loglin(x), exp(-lin(x) * x))

    def test_loglinear(self):
        yy = [x * .5 for x in self.x]
        log_yy = [log(y) for x, y in zip(self.x, yy)]
        lin = linear(self.x, log_yy)
        loglin = loglinear(self.x, yy)
        for w in [0.25]:
            for x in self.s:
                x = 0.01 + x * w
                self.assertAlmostEqual(loglin(x), exp(lin(x)))

    def test_logconstant(self):
        yy = [x * .5 for x in self.x]
        log_yy = [log(y) for x, y in zip(self.x, yy)]
        lin = constant(self.x, log_yy)
        loglin = logconstant(self.x, yy)
        for w in [0.25]:
            for x in self.s:
                x = 0.01 + x * w
                self.assertAlmostEqual(loglin(x), exp(lin(x)))

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


class CubicSplineUnitTest(TestCase):
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


class CompoundingUnitTests(TestCase):
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


class CurveUnitTests(TestCase):
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

    def test_init(self):
        Curve()


class DateCurveUnitTests(TestCase):
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
        self.today_eom = self.today == BusinessDate.end_of_month(self.today.year, self.today.month)
        self.periods = ('0D', '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

        def pp(d, a, b):
            print d, abs(a(d) - b(d)) < self.precision, a(d), b(d)

        self.pp = pp

        def curve(p='0D'):
            grid = [self.today + p + _ for _ in self.grid]
            return self.cast_type(grid, self.points)

        self.curve = curve

    def test_interpolation(self):
        curve = self.curve()
        for t in (DiscountFactorCurve, ZeroRateCurve, ShortRateCurve):
            cast = curve.cast(t)
            recast = cast.cast(self.cast_type)
            self.assertEqual(map(type, self.cast_type._interpolation), map(type, curve.interpolation))
            self.assertEqual(map(type, t._interpolation), map(type, cast.interpolation))
            self.assertEqual(map(type, self.cast_type._interpolation), map(type, recast.interpolation))

    def test_discount_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(DiscountFactorCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_zero_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(ZeroRateCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_short_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(ShortRateCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_cash1m_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(CashRateCurve, forward_tenor='1M').cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.cash_precision)

    def test_cash3m_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(CashRateCurve, forward_tenor='3M').cast(self.cast_type)
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


class CreditCurveUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate()
        self.domain = BusinessRange(self.today, self.today + '1Y', '3M')
        self.len = len(self.domain)
        self.periods = ('0D', '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

    def test_survival_curve(self):
        i_curve = FlatIntensityCurve([self.today, self.today + '1d'], [.02, .02])
        s_curve = SurvivalProbabilityCurve(i_curve.domain, [1., i_curve.get_survival_prob(self.today + '1d')])
        for t in self.domain:
            for p in self.periods:
                x = t + p
                self.assertAlmostEqual(s_curve.get_survival_prob(x, x), 1.)
                z = i_curve.get_flat_intensity(x)
                d = s_curve.get_flat_intensity(x)
                self.assertAlmostEqual(z, d)
                z = i_curve.get_survival_prob(x)
                d = s_curve.get_survival_prob(x)
                self.assertAlmostEqual(z, d)
                z = i_curve.get_hazard_rate(x)
                d = s_curve.get_hazard_rate(x)
                self.assertAlmostEqual(z, d)

        s_curve = SurvivalProbabilityCurve(i_curve.domain, [0., 0.])
        for p in self.periods:
            x = self.today + p
            s = s_curve.get_survival_prob(s_curve.origin, x)
            self.assertAlmostEqual(s, 0.)

    def test_intensity_curve(self):
        rate = 0.02
        curve = FlatIntensityCurve(self.domain, [rate] * self.len)
        for d in self.domain:
            for p in self.periods:
                self.assertAlmostEqual(curve.get_survival_prob(d + p, d + p), 1.)

                self.assertAlmostEqual(curve.get_flat_intensity(self.today, d + p), rate)
                self.assertAlmostEqual(curve.get_hazard_rate(d + p), rate)

    def test_hazard_rate_curve(self):
        rate = 0.02
        curve = HazardRateCurve(self.domain, [rate] * self.len)
        flat = FlatIntensityCurve(self.domain, [rate] * self.len)
        for d in self.domain:
            for p in self.periods:
                t = d + p
                self.assertAlmostEqual(curve.get_survival_prob(t, t), 1.)
                self.assertAlmostEqual(curve.get_flat_intensity(t), rate)
                self.assertAlmostEqual(curve.get_hazard_rate(t), rate)
                self.assertAlmostEqual(flat.get_flat_intensity(t), rate)
                self.assertAlmostEqual(flat.get_hazard_rate(t), rate)

        curve = HazardRateCurve([self.today, self.today + '1y'], [0.1, 0.3])
        t = curve.origin
        self.assertAlmostEqual(curve.get_hazard_rate(t), .1)

        self.assertAlmostEqual(curve.get_flat_intensity(t + '1y'), .1)
        self.assertAlmostEqual(curve.get_hazard_rate(t + '1y'), .3)

        self.assertAlmostEqual(curve.get_flat_intensity(t + '2y'), .2, 3)
        self.assertAlmostEqual(curve.get_hazard_rate(t + '2y'), .3)

    def test_marginal_curve(self):
        rate = 0.1
        i = FlatIntensityCurve([self.today], [rate])
        m = MarginalSurvivalProbabilityCurve([self.today], [i.get_survival_prob(self.today + '1y')])
        for d in self.domain:
            for p in self.periods:
                mv = m.get_flat_intensity(d + p)
                fi = i.get_flat_intensity(d + p)
                self.assertAlmostEqual(mv, fi, 3)  # precision of 3 due to day_count effects

        for q in self.periods:
            m = MarginalDefaultProbabilityCurve([self.today + q], [1.00], origin=self.today)
            for d in self.domain:
                for p in self.periods:
                    s = m.get_survival_prob(d, d + p)
                    self.assertAlmostEqual(s, 0.)


class CastIntensityCurveUnitTests(TestCase):
    def setUp(self):
        self.cast_type = FlatIntensityCurve
        self.grid = ['0D', '3M', '12M']
        self.points = [0.02, 0.01, 0.015]
        self.grid = ['0D', '1M', '2M', '3M', '4M', '5M', '6M', '1Y']
        self.points = [0.02, 0.018, 0.0186, 0.018, 0.0167, 0.0155, 0.015, 0.015]

        self.precision = 10
        self.marginal_precision = 2

        self.today = BusinessDate()
        self.today_eom = self.today == BusinessDate.end_of_month(self.today.year, self.today.month)
        self.periods = ('0D', '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

        def pp(d, a, b):
            print d, abs(a(d) - b(d)) < self.precision, a(d), b(d)

        self.pp = pp

        def curve(p='0D'):
            grid = [self.today + p + _ for _ in self.grid]
            return self.cast_type(grid, self.points)

        self.curve = curve

    def test_interpolation(self):
        curve = self.curve()
        for t in (SurvivalProbabilityCurve, FlatIntensityCurve, HazardRateCurve):
            cast = curve.cast(t)
            recast = cast.cast(self.cast_type)
            self.assertEqual(map(type, self.cast_type._interpolation), map(type, curve.interpolation))
            self.assertEqual(map(type, t._interpolation), map(type, cast.interpolation))
            self.assertEqual(map(type, self.cast_type._interpolation), map(type, recast.interpolation))

    def test_survival_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(SurvivalProbabilityCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_intensity_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(FlatIntensityCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_hazard_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(HazardRateCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_default_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(DefaultProbabilityCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_marginal_survival_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(MarginalSurvivalProbabilityCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.marginal_precision)

    def test_marginal_default_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = curve.cast(MarginalDefaultProbabilityCurve).cast(self.cast_type)
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.marginal_precision)


class CastSurvivalCurveUnitTests(CastIntensityCurveUnitTests):
    def setUp(self):
        super(CastSurvivalCurveUnitTests, self).setUp()
        self.cast_type = SurvivalProbabilityCurve
        self.grid = ['0D', '3M', '12M']
        self.points = [1., 0.9999, 0.997]


class CastDefaultCurveUnitTests(CastSurvivalCurveUnitTests):
    def setUp(self):
        super(CastDefaultCurveUnitTests, self).setUp()
        self.cast_type = DefaultProbabilityCurve
        self.points = [1. - p for p in self.points]


class CastHazardRateCurveUnitTests(CastIntensityCurveUnitTests):
    def setUp(self):
        super(CastHazardRateCurveUnitTests, self).setUp()
        self.cast_type = HazardRateCurve


class CastMarginalSurvivalCurveUnitTests(CastIntensityCurveUnitTests):
    def setUp(self):
        super(CastMarginalSurvivalCurveUnitTests, self).setUp()
        self.cast_type = MarginalSurvivalProbabilityCurve
        self.grid = ['0D', '1Y', '2Y', '3Y']
        self.points = [0.02, 0.022, 0.02, 0.03]
        self.precision = 10
        self.marginal_precision = 10


class CastMarginalDefaultCurveUnitTests(CastMarginalSurvivalCurveUnitTests):
    def setUp(self):
        super(CastMarginalDefaultCurveUnitTests, self).setUp()
        self.cast_type = MarginalDefaultProbabilityCurve
        self.points = [1. - p for p in self.points]


class FxUnitTests(TestCase):
    def test_(self):
        pass


class CashflowUnitTests(TestCase):
    def test_(self):
        pass


class RatingClassUnitTets(TestCase):
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
        self.assertEqual('0.7777778 C + 0.2222222 D', str(r))
        self.assertEqual('[' + str(r) + ']-RatingClass(0.3000000)', repr(r))

        self.assertEqual(len(list(r)), len(r.masterscale))
        self.assertAlmostEqual(sum(list(r)), 1.)
        self.assertAlmostEqual(min(list(r)), 0.)

        r = RatingClass(value='A', masterscale=('A', 'B', 'C', 'D'))
        self.assertAlmostEqual(0.001, float(r))
        for k, v in r.masterscale.items():
            self.assertAlmostEqual(v, float(RatingClass(k, r.masterscale)))

        self.assertRaises(TypeError, RatingClass, 'X', r.masterscale)

    def test_sloppy_rating_class_with_master_scale(self):
        RatingClass.SLOPPY = True
        r = RatingClass(-0.001, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([-1.0, 0.0, 0.0, 0.0], list(r))
        r = RatingClass(0.0, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.0, 0.0, 0.0, 0.0], list(r))
        r = RatingClass(0.000001, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.001, 0.0, 0.0, 0.0], list(r))
        r = RatingClass(0.5, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.0, 0.0, 0.5555556, 0.4444444], list(r))
        r = RatingClass(2.0, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.0, 0.0, 0.0, 2.0], list(r))

    def test_master_scale_rating_classes(self):
        r = RatingClass(value=0.3, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual(r.masterscale.keys(), ['A', 'B', 'C', 'D'])
        self.assertEqual(str(r.masterscale), '[[A]-RatingClass(0.0010000), '
                                             '[B]-RatingClass(0.0100000), '
                                             '[C]-RatingClass(0.1000000), '
                                             '[D]-RatingClass(1.0000000)]')
        self.assertEqual(repr(r.masterscale), 'master_scale('
                                              '[A]-RatingClass(0.0010000), '
                                              '[B]-RatingClass(0.0100000), '
                                              '[C]-RatingClass(0.1000000), '
                                              '[D]-RatingClass(1.0000000))')

        for y, z in r.masterscale.items():
            x = RatingClass(z, r.masterscale)
            self.assertEqual(str(x), y)
            self.assertEqual(repr(x), '[%s]-RatingClass(%.7f)' % (y, z))

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

    suite = TestLoader().loadTestsFromModule(__import__("__main__"))
    testrunner = TextTestRunner(stream=stdout, descriptions=2, verbosity=2)
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
