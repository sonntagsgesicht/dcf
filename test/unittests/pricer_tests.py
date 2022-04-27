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

from businessdate import BusinessDate, BusinessSchedule

from dcf import DiscountFactorCurve, CashRateCurve, ZeroRateCurve
from dcf.base.interpolation import interpolation_scheme
from dcf import FixedCashFlowList, RateCashFlowList, CashFlowLegList
from dcf.pricer import get_present_value, get_yield_to_maturity, get_par_rate, get_interest_accrued


class PresentValueUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')
        self.df = DiscountFactorCurve([self.today], [1.], interpolation=interpolation_scheme)
        self.df2 = DiscountFactorCurve([self.today], [.2], interpolation=interpolation_scheme)
        self.curve = CashRateCurve([self.today], [.1])

    def test_present_value(self):
        leg1 = RateCashFlowList(self.schedule, 100., fixed_rate=1.)
        leg2 = RateCashFlowList(self.schedule, -100. / self.curve(self.today), forward_curve=self.curve)
        swap = CashFlowLegList((leg1, leg2))

        pv1 = get_present_value(leg1, self.df)
        pv2 = get_present_value(leg2, self.df)
        self.assertAlmostEqual(pv1, -pv2)

        pv = get_present_value(swap, self.df)
        self.assertAlmostEqual(pv1 + pv2, pv)

        cf = sum(swap[swap.domain])
        self.assertAlmostEqual(pv, cf)

        pv_df2 = get_present_value(swap, self.df2)
        self.assertAlmostEqual(pv_df2, pv * self.df2(self.today))


class YTMUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')
        self.rate = 0.01
        self.df = DiscountFactorCurve(ZeroRateCurve([self.today], [self.rate]))
        self.curve = CashRateCurve([self.today], [.1])

    def test_ytm(self):
        cfs = FixedCashFlowList(self.schedule)
        total = sum(cfs[cfs.domain])

        ytm = get_yield_to_maturity(cfs, present_value=total)
        self.assertAlmostEqual(0., ytm, 4)

        ytm = get_yield_to_maturity(cfs, present_value=total*0.95)
        self.assertAlmostEqual(0.020725590840447707, ytm, 4)

        ytm = get_yield_to_maturity(cfs, present_value=total*0.8)
        self.assertAlmostEqual(0.09308670969912783, ytm, 4)

        ytm = get_yield_to_maturity(cfs, present_value=total * 1.2)
        self.assertAlmostEqual(-0.07084882935159839, ytm, 4)

        pv = get_present_value(cfs, self.df)
        ytm = get_yield_to_maturity(cfs, present_value=pv)
        self.assertAlmostEqual(self.rate, ytm, 4)


class ParRateUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')
        self.rate = 0.01
        self.df = DiscountFactorCurve(ZeroRateCurve([self.today], [self.rate]))
        self.curve = CashRateCurve([self.today], [self.rate])

    def test_(self):
        leg1 = RateCashFlowList(self.schedule, 100., fixed_rate=1.)
        leg2 = RateCashFlowList(self.schedule, 100., forward_curve=self.curve)
        pv2 = get_present_value(leg2, self.df)
        par = get_par_rate(leg1, self.df, present_value=pv2)
        self.assertAlmostEqual(self.rate, par)
        self.assertAlmostEqual(1., leg1.fixed_rate)
        leg1.fixed_rate = par
        pv1 = get_present_value(leg1, self.df)
        self.assertAlmostEqual(pv1, pv2)


class InterestAccruedUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')
        self.rate = 0.01
        self.df = DiscountFactorCurve(ZeroRateCurve([self.today], [self.rate]))
        self.curve = CashRateCurve([self.today], [.1])

    def test_ir_acc_fixed(self):
        cfs = FixedCashFlowList(self.schedule, 1.)
        ac = get_interest_accrued(cfs, self.today + '2w2d')
        self.assertAlmostEqual(0.0, ac)

    def test_ir_acc_rate(self):
        cfs = RateCashFlowList(self.schedule[1:], 1.,
                               origin=self.today, fixed_rate=0.01)
        ac = get_interest_accrued(cfs, self.today + '2w2d')
        self.assertAlmostEqual(0.0004380561259411362, ac)

        cfs = RateCashFlowList(self.schedule, 1.,
                               origin=self.today-'1m', fixed_rate=0.01)
        ac = get_interest_accrued(cfs, self.today + '2w2d')
        self.assertAlmostEqual(0.0004380561259411362, ac)
