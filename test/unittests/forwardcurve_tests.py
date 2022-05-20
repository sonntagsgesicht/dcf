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

from dcf.curves.curve import ForwardCurve
from dcf.curves.interestratecurve import ZeroRateCurve


class ForwardCurveUnitTest(TestCase):

    def setUp(self):
        self.domain = tuple(range(1, 10))
        self.foo = lambda x: x * x
        self.data = tuple(map(self.foo, self.domain))
        self.rate = 0.01
        self.origin = self.domain[0]
        self.spot = self.data[-1]

    def test_interpolated_forward(self):
        m = max(self.domain)
        f = ForwardCurve(self.domain, self.data, yield_curve=self.rate)
        for x, y in zip(self.domain[:-1], self.domain[1:]):
            self.assertAlmostEqual(self.foo(x), f(x))
            self.assertTrue(f(x) < f(y))
            self.assertTrue(f(x) < f((x + y) / 2))
            self.assertTrue(f((x + y) / 2 < f(y)))
            self.assertAlmostEqual(self.foo(y), f(y))
        self.assertTrue(f(m) <= f(2 * m))

    def test_extrapolated_forward(self):
        m = max(self.domain)
        c = ZeroRateCurve([m], [self.rate])
        f = ForwardCurve(self.domain, self.data, yield_curve=self.rate)
        for x in self.domain:
            x += m
            self.assertAlmostEqual(self.spot/c.get_discount_factor(x), f(x))
