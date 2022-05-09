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
from dcf.models.bachelier import \
    NormalOptionPayOffModel, BinaryNormalOptionPayOffModel
from dcf.models.black76 import \
    LogNormalOptionPayOffModel, BinaryLogNormalOptionPayOffModel
from dcf.models.displaced import \
    DisplacedLogNormalOptionPayOffModel, \
    BinaryDisplacedLogNormalOptionPayOffModel
from dcf.models.intrinsic import IntrinsicOptionPayOffModel, \
    BinaryIntrinsicOptionPayOffModel


class PayOffRegTests(RegressionTestCase):
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
                        if hasattr(model, '_call_price'):
                            x = model._call_price(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, '_call_delta'):
                            x = model._call_delta(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, '_call_gamma'):
                            x = model._call_gamma(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, '_call_vega'):
                            x = model._call_vega(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)
                        if hasattr(model, '_call_theta'):
                            x = model._call_theta(t, s, f, v)
                            self.assertAlmostRegressiveEqual(x)

    def test_bachelier(self):
        self._run_tests(NormalOptionPayOffModel())

    def test_binary_bachelier(self):
        self._run_tests(BinaryNormalOptionPayOffModel())

    def test_black76(self):
        self._run_tests(LogNormalOptionPayOffModel())

    def test_binary_black76(self):
        self._run_tests(BinaryLogNormalOptionPayOffModel())

    def test_displaced_black76(self):
        for d in (0.0, 0.003, 0.03, 0.1):
            self._run_tests(
                DisplacedLogNormalOptionPayOffModel(displacement=d))

    def test_binary_displaced_black76(self):
        for d in (0.0, 0.003, 0.03, 0.1):
            self._run_tests(
                BinaryDisplacedLogNormalOptionPayOffModel(displacement=d))


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
            'valuation_date': self.val_date,
            'forward_curve': self.forward_curve,
            'volatility_curve': self.vol_curve,
            'day_count': self.day_count
        }

    def _run_tests(self, first, places=7):
        for d in self.dates:
            for s in self.strikes:
                # price
                x = first.get_call_value(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.get_put_value(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # delta
                x = first.get_call_delta(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.get_put_delta(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # gamma
                x = first.get_call_delta(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.get_put_delta(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # vega
                x = first.get_call_vega(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.get_put_vega(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                # theta
                x = first.get_call_theta(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)
                x = first.get_put_theta(d, s) * self.notional
                self.assertAlmostRegressiveEqual(x, places)

    def test_bachelier(self):
        self._run_tests(NormalOptionPayOffModel(**self.kwargs))

    def test_binary_bachelier(self):
        self._run_tests(BinaryNormalOptionPayOffModel(**self.kwargs))

    def test_black76(self):
        self._run_tests(LogNormalOptionPayOffModel(**self.kwargs))

    def test_binary_black76(self):
        self._run_tests(BinaryLogNormalOptionPayOffModel(**self.kwargs))

    def test_displaced_black76(self):
        kwargs = self.kwargs
        for d in (0.0, 0.003, 0.03, 0.1):
            kwargs['displacement'] = d
            self._run_tests(DisplacedLogNormalOptionPayOffModel(**kwargs))

    def test_binary_displaced_black76(self):
        kwargs = self.kwargs
        for d in (0.0, 0.003, 0.03, 0.1):
            kwargs['displacement'] = d
            self._run_tests(
                BinaryDisplacedLogNormalOptionPayOffModel(**kwargs))

    def test_intrinsic(self):
        self._run_tests(IntrinsicOptionPayOffModel(**self.kwargs))

    def test_binary_intrinsic(self):
        self._run_tests(BinaryIntrinsicOptionPayOffModel(**self.kwargs))
