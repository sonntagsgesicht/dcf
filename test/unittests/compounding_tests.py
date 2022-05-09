# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from unittest.case import TestCase

from dcf.compounding import periodic_compounding, periodic_rate, \
    continuous_compounding, continuous_rate, simple_compounding, simple_rate


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
