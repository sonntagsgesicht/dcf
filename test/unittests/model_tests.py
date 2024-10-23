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

from dcf.daycount import day_count
from dcf import OptionPricingCurve


class BaseModelUnitTests(TestCase):
    def setUp(self):
        self.notional = 1e3
        self.dates = 0.1, 1.0, 2.3, 10.0
        self.strikes = 0.003, 0.01, 0.05
        self.displacements = 0.0, 0.003, 0.03, 0.1

        self.val_date = 0.0
        self.day_count = day_count
        self.forward_curve = lambda *_: 0.005
        self.vol_curve = lambda *_: 0.1

        self.kwargs = {
            'origin': self.val_date,
            'curve': self.forward_curve,
            'volatility': self.vol_curve,
            'day_count': self.day_count
        }

    def _run_tests(self, first, second, places=7, strikes=(), binary=False):
        self._run_vanilla_tests(first, second, places, strikes)
        if binary:
            self._run_binary_tests(first, second, places, strikes)

    def _run_vanilla_tests(self, first, second, places=7, strikes=()):
        for d in self.dates:
            for s in strikes or self.strikes:
                # price
                x = first.call(d, strike=s) * self.notional
                y = second.call(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.put(d, strike=s) * self.notional
                y = second.put(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # delta
                x = first.call_delta(d, strike=s) * self.notional
                y = second.call_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.put_delta(d, strike=s) * self.notional
                y = second.put_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # gamma
                x = first.call_delta(d, strike=s) * self.notional
                y = second.call_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.put_delta(d, strike=s) * self.notional
                y = second.put_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # vega
                x = first.call_vega(d, strike=s) * self.notional
                y = second.call_vega(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.put_vega(d, strike=s) * self.notional
                y = second.put_vega(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # theta
                x = first.call_theta(d, strike=s) * self.notional
                y = second.call_theta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.put_theta(d, strike=s) * self.notional
                y = second.put_theta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)

    def _run_binary_tests(self, first, second, places=7, strikes=()):
        for d in self.dates:
            for s in strikes or self.strikes:
                # price
                x = first.binary_call(d, strike=s) * self.notional
                y = second.binary_call(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.binary_put(d, strike=s) * self.notional
                y = second.binary_put(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # delta
                x = first.binary_call_delta(d, strike=s) * self.notional
                y = second.binary_call_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.binary_put_delta(d, strike=s) * self.notional
                y = second.binary_put_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # gamma
                x = first.binary_call_delta(d, strike=s) * self.notional
                y = second.binary_call_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.binary_put_delta(d, strike=s) * self.notional
                y = second.binary_put_delta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # vega
                x = first.binary_call_vega(d, strike=s) * self.notional
                y = second.binary_call_vega(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.binary_put_vega(d, strike=s) * self.notional
                y = second.binary_put_vega(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # theta
                x = first.binary_call_theta(d, strike=s) * self.notional
                y = second.binary_call_theta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.binary_put_theta(d, strike=s) * self.notional
                y = second.binary_put_theta(d, strike=s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)



class IntrinsicModelUnitTests(BaseModelUnitTests):
    def test_bachelier(self):
        first = OptionPricingCurve.intrinsic(**self.kwargs)
        kwargs = dict(self.kwargs)
        kwargs['volatility'] = lambda *_: 0.0
        second = OptionPricingCurve.bachelier(**kwargs)
        self._run_tests(first, second)

    def test_black76(self):
        first = OptionPricingCurve.intrinsic(**self.kwargs)
        kwargs = dict(self.kwargs)
        kwargs['volatility'] = lambda *_: 0.0
        second = OptionPricingCurve.black76(**kwargs)
        self._run_tests(first, second)

    def test_displaced_black76(self):
        first = OptionPricingCurve.intrinsic(**self.kwargs)
        kwargs = dict(self.kwargs)
        for d in self.displacements:
            kwargs['displacement'] = d
            kwargs['volatility'] = lambda *_: 0.0
            second = OptionPricingCurve.displaced_black76(**kwargs)
            self._run_tests(first, second)



class BumpGreeksModelUnitTests(BaseModelUnitTests):
    def test_bachelier(self):
        first = OptionPricingCurve.bachelier(**self.kwargs)
        second = OptionPricingCurve.bachelier(**self.kwargs)
        second.bump_greeks = True
        second.DELTA_SHIFT = 1e-10
        # self._run_tests(first, second)

    def test_black76(self):
        first = OptionPricingCurve.black76(**self.kwargs)
        second = OptionPricingCurve.black76(**self.kwargs)
        second.bump_greeks = True
        second.DELTA_SHIFT = 1e-10
        # self._run_tests(first, second)

    def test_displaced_black76(self):
        kwargs = self.kwargs
        for d in self.displacements:
            kwargs['displacement'] = d
            first = OptionPricingCurve.displaced_black76(**kwargs)
            second = OptionPricingCurve.displaced_black76(**kwargs)
            second.bump_greeks = True
            second.DELTA_SHIFT = 1e-10
            # self._run_tests(first, second)
