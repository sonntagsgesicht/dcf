# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import log, exp
from unittest.case import TestCase

from dcf.interpolation import flat, no, left, right, loglinear, nearest, \
    linear, zero, loglinearrate, constant, logconstantrate


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
            for _ in self.s:
                self.assertAlmostEqual(f(x + 2), 0.01)

    def test_linear(self):
        f = linear(self.x, self.y)
        for x in [0.] + self.x:
            for s in self.s:
                self.assertAlmostEqual(f(x + s), self.a + self.b * (x + s))

    def test_no(self):
        f = no(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEqual(f(x), y)
        for x in self.x:
            self.assertEqual(None, f(x + 0.001))

    def test_zero(self):
        f = zero(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEqual(f(x), y)
        for x in self.x:
            self.assertAlmostEqual(f(x + 0.001), .0)
            self.assertAlmostEqual(f(x - 0.001), .0)

    def test_left(self):
        f = left(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEqual(f(x), y)
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
                self.assertAlmostEqual(f(x + s), y)

    def test_right(self):
        f = right(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEqual(f(x), y)
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
                self.assertAlmostEqual(f(x + s), y)

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
        const = constant(self.x, log_yy)
        logconst = constant(self.x, yy)
        for w in [0.25]:
            for x in self.s:
                x = 0.01 + x * w
                self.assertAlmostEqual(logconst(x), exp(const(x)))

    def test_nearest(self):
        f = nearest(self.x, self.y)
        for x, y in zip(self.x, self.y):
            self.assertAlmostEqual(f(x), y)
        for x in [0.] + self.x + [4.]:
            for s in self.s:
                if x + s <= self.x[0]:
                    y = self.y[0]
                elif x + s in self.x:
                    y = self.y[self.x.index(x + s)]
                elif x + s < self.x[-1]:
                    i = self.x.index(x)
                    if s <= self.x[i + 1] - x - s:
                        y = self.y[i]
                    else:
                        y = self.y[i + 1]
                else:
                    y = self.y[-1]
                self.assertAlmostEqual(f(x + s), y)

    def test_update(self):
        f = linear(self.x, self.y)
        for s in self.s:
            if s in self.x:
                self.assertTrue(s in f)
            else:
                self.assertFalse(s in f)
        y = [f(s) for s in reversed(self.s)]
        ff = no()
        ff._update(self.s, y)
        for s in self.s:
            self.assertTrue(s in ff)
        for s, e in zip(ff.x_list[:1], ff.x_list[1:]):
            self.assertTrue(s < e)
        for s in self.s:
            self.assertTrue(s in ff)
            ff._update([s])
            self.assertFalse(s in ff)
