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

from dcf import FlatIntensityCurve, SurvivalProbabilityCurve, HazardRateCurve, MarginalSurvivalProbabilityCurve, \
    MarginalDefaultProbabilityCurve, DefaultProbabilityCurve


class CreditCurveUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate()
        self.domain = BusinessRange(self.today, self.today + '1Y', '3M')
        self.len = len(self.domain)
        self.periods = ('0D', '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

    def test_survival_curve(self):
        i_curve = FlatIntensityCurve([self.today, self.today + '1d'], [.02, .02])
        s_curve = SurvivalProbabilityCurve(i_curve.domain, [1., i_curve.get_survival_prob(self.today + '1d')])
        for t in self.domain:
            for p in self.periods:
                x = t + p
                self.assertAlmostEqual(s_curve.get_survival_prob(x, x), 1.)
                z = i_curve.get_flat_intensity(x)
                d = s_curve.get_flat_intensity(x)
                self.assertAlmostEqual(z, d)
                z = i_curve.get_survival_prob(x)
                d = s_curve.get_survival_prob(x)
                self.assertAlmostEqual(z, d)
                z = i_curve.get_hazard_rate(x)
                d = s_curve.get_hazard_rate(x)
                self.assertAlmostEqual(z, d)

        s_curve = SurvivalProbabilityCurve(i_curve.domain, [0., 0.])
        for p in self.periods:
            x = self.today + p
            s = s_curve.get_survival_prob(s_curve.origin, x)
            self.assertAlmostEqual(s, 0.)

    def test_intensity_curve(self):
        rate = 0.02
        curve = FlatIntensityCurve(self.domain, [rate] * self.len)
        for d in self.domain:
            for p in self.periods:
                self.assertAlmostEqual(curve.get_survival_prob(d + p, d + p), 1.)

                self.assertAlmostEqual(curve.get_flat_intensity(self.today, d + p), rate)
                self.assertAlmostEqual(curve.get_hazard_rate(d + p), rate)

    def test_hazard_rate_curve(self):
        rate = 0.02
        curve = HazardRateCurve(self.domain, [rate] * self.len)
        flat = FlatIntensityCurve(self.domain, [rate] * self.len)
        for d in self.domain:
            for p in self.periods:
                t = d + p
                self.assertAlmostEqual(curve.get_survival_prob(t, t), 1.)
                self.assertAlmostEqual(curve.get_flat_intensity(t), rate)
                self.assertAlmostEqual(curve.get_hazard_rate(t), rate)
                self.assertAlmostEqual(flat.get_flat_intensity(t), rate)
                self.assertAlmostEqual(flat.get_hazard_rate(t), rate)

        curve = HazardRateCurve([self.today, self.today + '1y'], [0.1, 0.3])
        t = curve.origin
        self.assertAlmostEqual(curve.get_hazard_rate(t), .1)

        self.assertAlmostEqual(curve.get_flat_intensity(t + '1y'), .1)
        self.assertAlmostEqual(curve.get_hazard_rate(t + '1y'), .3)

        self.assertAlmostEqual(curve.get_flat_intensity(t + '2y'), .2, 3)
        self.assertAlmostEqual(curve.get_hazard_rate(t + '2y'), .3)

    def test_marginal_curve(self):
        rate = 0.1
        i = FlatIntensityCurve([self.today], [rate])
        m = MarginalSurvivalProbabilityCurve([self.today], [i.get_survival_prob(self.today + '1y')])
        for d in self.domain:
            for p in self.periods:
                mv = m.get_flat_intensity(d + p)
                fi = i.get_flat_intensity(d + p)
                self.assertAlmostEqual(mv, fi, 3)  # precision of 3 due to day_count effects

        for q in self.periods:
            m = MarginalDefaultProbabilityCurve([self.today + q], [1.00], origin=self.today)
            for d in self.domain:
                for p in self.periods:
                    s = m.get_survival_prob(d, d + p)
                    self.assertAlmostEqual(s, 0.)


class CastIntensityCurveUnitTests(TestCase):
    def setUp(self):
        self.cast_type = FlatIntensityCurve
        self.grid = ['0D', '3M', '12M']
        self.points = [0.02, 0.01, 0.015]
        self.grid = ['0D', '1M', '2M', '3M', '4M', '5M', '6M', '1Y']
        self.points = [0.02, 0.018, 0.0186, 0.018, 0.0167, 0.0155, 0.015, 0.015]

        self.precision = 10
        self.marginal_precision = 2

        self.today = BusinessDate()
        self.today_eom = self.today == self.today.end_of_month()
        self.periods = ('0D', '1D', '2B', '8D', '2W', '14B', '1M', '1M1D', '3M', '6M', '6M2W1D', '9M', '12M')

        def pp(d, a, b):
            print((d, abs(a(d) - b(d)) < self.precision, a(d), b(d)))

        self.pp = pp

        def curve(p='0D'):
            grid = [self.today + p + _ for _ in self.grid]
            return self.cast_type(grid, self.points)

        self.curve = curve

    def test_interpolation(self):
        curve = self.curve()
        for t in (SurvivalProbabilityCurve, FlatIntensityCurve, HazardRateCurve):
            cast = t(curve)
            recast = self.cast_type(cast)
            self.assertEqual(self.cast_type._INTERPOLATION, curve._INTERPOLATION)
            self.assertEqual(t._INTERPOLATION, cast._INTERPOLATION)
            self.assertEqual(self.cast_type._INTERPOLATION, recast._INTERPOLATION)

    def test_survival_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(SurvivalProbabilityCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_intensity_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(FlatIntensityCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_hazard_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(HazardRateCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_default_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(DefaultProbabilityCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.precision)

    def test_marginal_survival_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(MarginalSurvivalProbabilityCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.marginal_precision)

    def test_marginal_default_cast(self):
        for p in self.periods:
            curve = self.curve(p)
            cast = self.cast_type(MarginalDefaultProbabilityCurve(curve))
            for d in curve.domain[1:]:
                self.assertAlmostEqual(cast(d), curve(d), self.marginal_precision)


class CastSurvivalCurveUnitTests(CastIntensityCurveUnitTests):
    def setUp(self):
        super(CastSurvivalCurveUnitTests, self).setUp()
        self.cast_type = SurvivalProbabilityCurve
        self.grid = ['0D', '3M', '12M']
        self.points = [1., 0.9999, 0.997]


class CastDefaultCurveUnitTests(CastSurvivalCurveUnitTests):
    def setUp(self):
        super(CastDefaultCurveUnitTests, self).setUp()
        self.cast_type = DefaultProbabilityCurve
        self.points = [1. - p for p in self.points]


class CastHazardRateCurveUnitTests(CastIntensityCurveUnitTests):
    def setUp(self):
        super(CastHazardRateCurveUnitTests, self).setUp()
        self.cast_type = HazardRateCurve


class CastMarginalSurvivalCurveUnitTests(CastIntensityCurveUnitTests):
    def setUp(self):
        super(CastMarginalSurvivalCurveUnitTests, self).setUp()
        self.cast_type = MarginalSurvivalProbabilityCurve
        self.grid = ['0D', '1Y', '2Y', '3Y']
        self.points = [0.02, 0.022, 0.02, 0.03]
        self.precision = 10
        self.marginal_precision = 10


class CastMarginalDefaultCurveUnitTests(CastMarginalSurvivalCurveUnitTests):
    def setUp(self):
        super(CastMarginalDefaultCurveUnitTests, self).setUp()
        self.cast_type = MarginalDefaultProbabilityCurve
        self.points = [1. - p for p in self.points]
