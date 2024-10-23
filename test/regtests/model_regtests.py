# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from regtest import RegressionTestCase

from dcf.daycount import day_count
from dcf import OptionPricingCurve


class ModelRegTests(RegressionTestCase):
    def setUp(self):
        self.notional = 1e3
        self.dates = 0.1, 1.0, 2.3, 10.0
        self.strikes = 0.003, 0.01, 0.05

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

    def _run_tests(self, first, places=7):
        for d in self.dates:
            for s in self.strikes:
                # price
                x = first.call(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.put(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # delta
                x = first.call_delta(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.put_delta(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # gamma
                x = first.call_delta(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.put_delta(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # vega
                x = first.call_vega(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.put_vega(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # theta
                x = first.call_theta(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.put_theta(d, strike=s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)

    def test_bachelier(self):
        self._run_tests(OptionPricingCurve.bachelier(**self.kwargs))

    def test_black76(self):
        self._run_tests(OptionPricingCurve.black76(**self.kwargs))

    def test_displaced_black76(self):
        kwargs = self.kwargs
        for d in (0.0, 0.003, 0.03, 0.1):
            kwargs['displacement'] = d
            self._run_tests(OptionPricingCurve.displaced_black76(**kwargs))

    def test_intrinsic(self):
        self._run_tests(OptionPricingCurve.intrinsic(**self.kwargs))
