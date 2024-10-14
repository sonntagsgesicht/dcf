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

from dcf.optionpricing import Bachelier, Black76, DisplacedBlack76, Intrinsic


class OptionPricingRegTests(RegressionTestCase):
    def setUp(self):
        self.taus = 0.1, 1.0, 2.3, 10.0
        self.strikes = 100, 120, 130
        self.forwards = self.strikes
        self.vols = 0.001, 0.01, 0.02, 0.05, 0.1, 0.2

    def _run_tests(self, model):
        for t in self.taus:
            for s in self.strikes:
                for f in self.forwards:
                    for v in self.vols:
                        if hasattr(model, '__call__'):
                            x = model(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'delta'):
                            x = model.delta(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'gamma'):
                            x = model.gamma(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'vega'):
                            x = model.vega(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'theta'):
                            x = model.theta(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'binary'):
                            x = model.binary(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'binary_delta'):
                            x = model.binary_delta(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'binary_gamma'):
                            x = model.binary_gamma(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'binary_vega'):
                            x = model.binary_vega(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, 'binary_theta'):
                            x = model.binary_theta(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)

    def test_intrinsic(self):
        self._run_tests(Intrinsic())

    def test_bachelier(self):
        self._run_tests(Bachelier())

    def test_black76(self):
        self._run_tests(Black76())

    def test_displaced_black76(self):
        for d in (0.0, 0.003, 0.03, 0.1):
            self._run_tests(DisplacedBlack76(displacement=d))
