# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from math import exp, log

from unittest.case import TestCase

from dcf import FxRate, FxForwardCurve, ZeroRateCurve

class FxUnitTests(TestCase):

    def test_fx_rate(self):
        x = FxRate(0.8, 0.0)
        self.assertEqual(0.8, float(x))
        self.assertEqual(0.8, float(x.value))
        self.assertEqual(0.0, float(x.origin))

    def test_fx_forward_curve(self):
        d = ZeroRateCurve([0], [0.01])
        f = ZeroRateCurve([0], [0.01])
        x = FxForwardCurve([0, 1], [0.6, 0.8],
                           domestic_curve=d, foreign_curve=f)
        self.assertAlmostEqual(0.6, x(0))
        self.assertAlmostEqual(0.69282032, x(0.5))
        self.assertAlmostEqual(0.8, x(1))
        self.assertAlmostEqual(0.8, x(20))

        f = ZeroRateCurve([0], [0.02])
        x = FxForwardCurve([0, 1], [0.6, 0.8],
                           domestic_curve=d, foreign_curve=f)
        self.assertAlmostEqual(0.6, x(0))
        self.assertAlmostEqual(0.69282032, x(0.5))
        self.assertAlmostEqual(0.8, x(1))
        self.assertAlmostEqual(1.01699932, x(25))
