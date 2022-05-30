# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import sys
import os

from unittest import TestCase

from datetime import date, timedelta
from math import floor
from businessdate import BusinessDate, BusinessRange
from scipy.interpolate import interp1d

from dcf.interpolation import linear, constant, _dyn_scheme as dyn_scheme

from dcf import Curve, DateCurve, RateCurve


def _silent(func, *args, **kwargs):
    _stout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    _res = func(*args, **kwargs)
    sys.stdout.close()
    sys.stdout = _stout
    return _res


class CurveUnitTests(TestCase):
    def setUp(self):
        self.x_list = [float(x) * 0.01 for x in range(10)]
        self.y_list = list(self.x_list)
        self.interpolation = dyn_scheme(constant, linear, constant)
        self.curve = Curve(self.x_list, self.y_list, self.interpolation)
        self.x_test = [float(x) * 0.005 for x in range(-10, 30)]

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
        self.assertEqual(str(Curve()), 'Curve()')
        self.assertEqual(str(DateCurve()), 'DateCurve()')
        self.assertEqual(str(RateCurve()), 'RateCurve()')

    def test_interpolation(self):
        # test default interpolation scheme
        for x in self.x_test:
            f = (lambda t: max(.0, min(t, .09)))
            self.assertAlmostEqual(f(x), self.curve(x))

        ccc = dyn_scheme(constant, constant, constant)
        curve = Curve(self.x_list, self.y_list, ccc)
        constant_curve = Curve(self.x_list, self.y_list, constant)
        for x in self.x_test:
            f = lambda t: max(.0, min(floor(t / .01) * .01, .09))
            self.assertAlmostEqual(f(x), curve(x))
            self.assertAlmostEqual(constant_curve(x), curve(x))

        lll = dyn_scheme(linear, linear, linear)
        curve = Curve(self.x_list, self.y_list, lll)
        linear_curve = Curve(self.x_list, self.y_list, linear)
        for x in self.x_test:
            f = lambda t: t
            self.assertAlmostEqual(f(x), curve(x))
            self.assertAlmostEqual(linear_curve(x), curve(x))

        dcf_curve = Curve(self.x_list, self.y_list,
                          dyn_scheme(constant, linear, constant))
        scipy_linear = lambda x, y: interp1d(x, y, kind="linear")
        scipy_curve = Curve(self.x_list, self.y_list,
                            dyn_scheme(constant, scipy_linear, constant))
        for x in self.x_test:
            self.assertAlmostEqual(scipy_curve(x), dcf_curve(x))

        dcf_curve = Curve(self.x_list, self.y_list,
                          dyn_scheme(linear, linear, linear))
        scipy_scheme = lambda x, y: \
            interp1d(x, y, kind="linear", fill_value="extrapolate")
        scipy_curve = Curve(self.x_list, self.y_list, scipy_scheme)
        for x in self.x_test:
            self.assertAlmostEqual(scipy_curve(x), dcf_curve(x))

        dcf_curve = Curve(self.x_list, self.y_list,
                          dyn_scheme(constant, linear, constant))
        scipy_scheme = lambda x, y: \
            interp1d(x, y, kind="linear", bounds_error=False,
                     fill_value=(self.y_list[0], self.y_list[-1]))
        scipy_curve = Curve(self.x_list, self.y_list, scipy_scheme)
        for x in self.x_test:
            self.assertAlmostEqual(scipy_curve(x), dcf_curve(x))


class DateCurveUnitTests(TestCase):
    def setUp(self):
        self.dates = [date(year=2020+y, month=1, day=12)
                      for y in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
        self.values = [0.01 * n ** 4 - 2 * n ** 2 for n in
                       range(0, len(self.dates))]
        self.curve = DateCurve(self.dates, self.values)
        self.period = timedelta(days=90)

    def test_dates(self):
        for d in self.dates:
            self.assertTrue(d in self.curve.domain)
        values = self.curve(self.dates)
        for d in self.dates:
            d += self.period
            self.assertTrue(min(values) <= self.curve(d) <= max(values))

    def test_shift_origin(self):
        origin1 = self.curve.origin
        origin2 = self.curve.origin + self.period
        Curve1 = DateCurve(self.dates, self.values, origin=origin1)
        Curve2 = DateCurve(self.dates, self.values, origin=origin2)
        for d in self.dates:
            self.assertAlmostEqual(Curve1(d), Curve2(d))

    def test_update(self):
        d = self.curve.domain[-1]
        v = self.curve(d)
        self.curve[d] = v*v
        self.assertAlmostEqual(v*v, self.curve(d))
        # self.assertAlmostEqual(v*v, self.curve[d])
        self.assertRaises(KeyError, self.curve.__getitem__, d + self.period)
        self.curve[d + self.period] = v*v*v
        self.assertAlmostEqual(v*v, self.curve(d))
        self.assertAlmostEqual(v*v, self.curve[d])
        self.assertAlmostEqual(v*v*v, self.curve(d + self.period))
        self.assertAlmostEqual(v*v*v, self.curve[d + self.period])


class DateCurveUnitTestsBusinessDate(DateCurveUnitTests):
    def setUp(self):
        self.dates = BusinessRange(BusinessDate(), BusinessDate() + '10Y',
                                   '1Y')
        self.values = [0.01 * n ** 4 - 2 * n ** 2 for n in
                       range(0, len(self.dates))]
        self.curve = DateCurve(self.dates, self.values)
        self.period = '3M'

    def test_fixings(self):
        curve = DateCurve(self.dates, self.values)
        date = BusinessDate() + '1y3m4d'
        value = curve(date)
        previous = curve(date - '1d')
        next = curve(date + '1d')
        curve.fixings[date] = value * 2
        self.assertAlmostEqual(curve.fixings[date], curve(date))
        self.assertAlmostEqual(value * 2, curve(date))
        self.assertAlmostEqual(previous, curve(date - '1d'))
        self.assertAlmostEqual(next, curve(date + '1d'))

    def test_cast(self):
        date_curve = DateCurve(self.dates, self.values)
        curve = Curve(date_curve)
        for x, d in zip(curve.domain, date_curve.domain):
            self.assertAlmostEqual(curve(x), date_curve(d))


class DateCurveUnitTestsYearFraction(DateCurveUnitTests):
    def setUp(self):
        self.dates = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.values = [0.01 * n ** 4 - 2 * n ** 2 for n in
                       range(0, len(self.dates))]
        self.curve = DateCurve(self.dates, self.values)
        self.period = 0.3
