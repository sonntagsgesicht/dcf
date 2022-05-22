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
from dcf.models.optionpricing import BinaryOptionPayOffModel
from dcf.models.bachelier import NormalOptionPayOffModel, \
    BinaryNormalOptionPayOffModel
from dcf.models.black76 import LogNormalOptionPayOffModel, \
    BinaryLogNormalOptionPayOffModel
from dcf.models.displaced import DisplacedLogNormalOptionPayOffModel, \
    BinaryDisplacedLogNormalOptionPayOffModel
from dcf.models.intrinsic import IntrinsicOptionPayOffModel


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
            'valuation_date': self.val_date,
            'forward_curve': self.forward_curve,
            'volatility_curve': self.vol_curve,
            'day_count': self.day_count
        }

    def _run_tests(self, first, second, places=7, strikes=()):
        for d in self.dates:
            for s in strikes or self.strikes:
                # price
                x = first.get_call_value(d, s) * self.notional
                y = second.get_call_value(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.get_put_value(d, s) * self.notional
                y = second.get_put_value(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # delta
                x = first.get_call_delta(d, s) * self.notional
                y = second.get_call_delta(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.get_put_delta(d, s) * self.notional
                y = second.get_put_delta(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # gamma
                x = first.get_call_delta(d, s) * self.notional
                y = second.get_call_delta(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.get_put_delta(d, s) * self.notional
                y = second.get_put_delta(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # vega
                x = first.get_call_vega(d, s) * self.notional
                y = second.get_call_vega(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.get_put_vega(d, s) * self.notional
                y = second.get_put_vega(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                # theta
                x = first.get_call_theta(d, s) * self.notional
                y = second.get_call_theta(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)
                x = first.get_put_theta(d, s) * self.notional
                y = second.get_put_theta(d, s) * self.notional
                if y:
                    self.assertAlmostEqual(x/y, 1., places)


class IntrinsicModelUnitTests(BaseModelUnitTests):
    def test_bachelier(self):
        kwargs = dict(self.kwargs)
        kwargs['volatility_curve'] = lambda *_: 0.0
        first = IntrinsicOptionPayOffModel(**self.kwargs)
        second = NormalOptionPayOffModel(**kwargs)
        self._run_tests(first, second)

    def test_black76(self):
        kwargs = dict(self.kwargs)
        kwargs['volatility_curve'] = lambda *_: 0.0
        first = IntrinsicOptionPayOffModel(**self.kwargs)
        second = LogNormalOptionPayOffModel(**kwargs)
        self._run_tests(first, second)

    def test_displaced_black76(self):
        kwargs = dict(self.kwargs)
        kwargs['volatility_curve'] = lambda *_: 0.0
        for d in self.displacements:
            kwargs['displacement'] = d
            first = IntrinsicOptionPayOffModel(**self.kwargs)
            second = DisplacedLogNormalOptionPayOffModel(**kwargs)
            self._run_tests(first, second)


class BumpGreeksModelUnitTests(BaseModelUnitTests):
    def _test_bachelier(self):
        first = NormalOptionPayOffModel(**self.kwargs)
        second = NormalOptionPayOffModel(**self.kwargs, bump_greeks=True)
        self._run_tests(first, second, 1)

    def _test_black76(self):
        first = LogNormalOptionPayOffModel(**self.kwargs)
        second = LogNormalOptionPayOffModel(**self.kwargs, bump_greeks=True)
        self._run_tests(first, second)

    def _test_displaced_black76(self):
        kwargs = self.kwargs
        for d in self.displacements:
            kwargs['displacement'] = d
            first = DisplacedLogNormalOptionPayOffModel(**kwargs)
            second = DisplacedLogNormalOptionPayOffModel(**kwargs,
                                                         bump_greeks=True)
            self._run_tests(first, second)


class BinaryModelUnitTests(BaseModelUnitTests):
    def _test_bachelier(self):
        model = NormalOptionPayOffModel(**self.kwargs)
        first = BinaryOptionPayOffModel(model)
        second = BinaryNormalOptionPayOffModel(**self.kwargs)
        self._run_tests(first, second, 2)

    def _test_black76(self):
        model = LogNormalOptionPayOffModel(**self.kwargs)
        first = BinaryOptionPayOffModel(model)
        second = BinaryLogNormalOptionPayOffModel(**self.kwargs)
        self._run_tests(first, second)

    def _test_displaced_black76(self):
        kwargs = self.kwargs
        for d in self.displacements:
            kwargs['displacement'] = d
            model = DisplacedLogNormalOptionPayOffModel(**kwargs)
            first = BinaryOptionPayOffModel(model)
            second = BinaryDisplacedLogNormalOptionPayOffModel(**kwargs)
            # strikes = tuple(s for s in self.strikes if 0 < s + fwd)
            self._run_tests(first, second)
