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

from businessdate import BusinessDate, BusinessRange

from dcf import TerminalVolatilityCurve, InstantaneousVolatilityCurve


class VolCurveUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate()
        self.domain = BusinessRange(self.today, self.today + '5Y', '1Y')
        self.len = len(self.domain)
        self.periods = ('0D', '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

    def test_flat_curve(self):
        for value in (0.0, 0.01, 0.1, 0.2):
            data = [value] * len(self.domain)
            term_curve = TerminalVolatilityCurve(self.domain, data)
            inst_curve = InstantaneousVolatilityCurve(self.domain, data)
            for t in self.domain:
                for p in self.periods:
                    x = t + p
                    self.assertAlmostEqual(value, term_curve.get_terminal_vol(x))
                    self.assertAlmostEqual(value, inst_curve.get_terminal_vol(x))

                    self.assertAlmostEqual(value, term_curve.get_terminal_vol(x, x))
                    self.assertAlmostEqual(value, inst_curve.get_terminal_vol(x, x))

                    self.assertAlmostEqual(value, term_curve.get_instantaneous_vol(x))
                    self.assertAlmostEqual(value, inst_curve.get_instantaneous_vol(x))

    def test_terminal_curve(self):
        pre = 2
        domain = [self.today, self.today + '2y', self.today + '3y', self.today + '4y']
        data = [0.15, 0.2, 0.2, 0.19]
        term_curve = TerminalVolatilityCurve(domain, data)
        inst_curve = InstantaneousVolatilityCurve(term_curve)
        for t in self.domain:
            for p in self.periods:
                x = t + p
                self.assertAlmostEqual(term_curve.get_terminal_vol(x), inst_curve.get_terminal_vol(x), pre)
                self.assertAlmostEqual(term_curve.get_terminal_vol(x, x), inst_curve.get_terminal_vol(x, x), pre)
                self.assertAlmostEqual(term_curve.get_instantaneous_vol(x), inst_curve.get_instantaneous_vol(x), pre)

    def test_terminal2_curve(self):
        domain = [self.today, self.today + '2y', self.today + '3y', self.today + '4y']
        data = [0.15, 0.2, 0.2, 0.15]
        term_curve = TerminalVolatilityCurve(domain, data)
        start = self.today + '3y'
        stop = self.today + '4y'
        self.assertRaises(ZeroDivisionError, term_curve.get_terminal_vol, start, stop)

    def test_inst_curve(self):
        pre = 1  # some interpolation artifacts may occur
        domain = [self.today, self.today + '2y', self.today + '3y', self.today + '4y']
        data = [0.15, 0.2, 0.2, 0.19]
        inst_curve = InstantaneousVolatilityCurve(domain, data)
        term_curve = TerminalVolatilityCurve(inst_curve)
        for t in self.domain:
            for p in self.periods:
                x = t + p
                self.assertAlmostEqual(term_curve.get_terminal_vol(x), inst_curve.get_terminal_vol(x), pre)
                self.assertAlmostEqual(term_curve.get_terminal_vol(x, x), inst_curve.get_terminal_vol(x, x), pre)
                self.assertAlmostEqual(term_curve.get_instantaneous_vol(x), inst_curve.get_instantaneous_vol(x), pre)
