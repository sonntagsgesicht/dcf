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
from dcf.interpolation import interpolation_scheme
from dcf import FixedCashFlowList, RateCashFlowList, CashFlowLegList
from dcf.pricer import get_present_value, get_yield_to_maturity, \
    get_fair_rate, get_interest_accrued, get_basis_point_value, \
    get_bucketed_delta, get_curve_fit


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
        cfs = FixedCashFlowList(self.schedule[1:])
        total = sum(cfs[cfs.domain])
        self.assertAlmostEqual(60.0, total, 4)

        ytm = get_yield_to_maturity(cfs,
                                    valuation_date=self.today,
                                    present_value=total)
        self.assertAlmostEqual(0.0, ytm)
        curve = ZeroRateCurve([self.today], [ytm])
        pv = get_present_value(cfs, curve, self.today)
        self.assertAlmostEqual(total, pv, 4)

        ytm = get_yield_to_maturity(cfs, present_value=total*0.95)
        self.assertGreater(ytm, 0.01, 4)

        ytm = get_yield_to_maturity(cfs, present_value=total*0.8)
        self.assertGreater(ytm, 0.05, 4)

        ytm = get_yield_to_maturity(cfs, present_value=total * 1.2)
        self.assertGreater(-0.05, ytm, 4)

        pv = get_present_value(cfs, self.df, valuation_date=self.today)
        ytm = get_yield_to_maturity(
            cfs, present_value=pv, valuation_date=self.today)
        self.assertAlmostEqual(self.rate, ytm, 4)


class FairRateUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')
        self.rate = 0.01
        self.df = DiscountFactorCurve(ZeroRateCurve([self.today], [self.rate]))
        self.curve = CashRateCurve([self.today], [self.rate])

    def test_fair_rate(self):
        leg1 = RateCashFlowList(self.schedule, 100., fixed_rate=1.)
        leg2 = RateCashFlowList(self.schedule, 100., forward_curve=self.curve)
        pv2 = get_present_value(leg2, self.df)
        par = get_fair_rate(leg1, self.df, present_value=pv2)
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


class BPVTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1y')
        self.rate = 0.01
        self.df = ZeroRateCurve([self.today], [self.rate])
        self.curve = CashRateCurve([self.today], [self.rate])

    def test_bpv(self):
        notional = 1e6
        fix1 = FixedCashFlowList([max(self.schedule)], -notional)
        fix2 = FixedCashFlowList([max(self.schedule)], notional)
        leg1 = RateCashFlowList(self.schedule, -notional, fixed_rate=self.rate)
        leg2 = RateCashFlowList(self.schedule, notional, forward_curve=self.curve)

        swp = CashFlowLegList((leg1, leg2))
        bnd = CashFlowLegList((fix1, leg1))
        frn = CashFlowLegList((fix2, leg2))

        total = sum(swp[swp.domain])
        self.assertAlmostEqual(0.0, total)

        bpv1 = get_basis_point_value(leg1, self.df, self.today, self.df)
        bpv2 = get_basis_point_value(leg2, self.df, self.today, self.df)
        self.assertAlmostEqual(bpv1, -bpv2)

        # swap bpv

        bpv = get_basis_point_value(swp, self.df, self.today, self.df)
        self.assertAlmostEqual(0.0, bpv)

        bpv = get_basis_point_value(swp, self.df, self.today, self.curve)
        self.assertAlmostEqual(585.4121890466267, bpv)

        bpv = get_basis_point_value(swp, self.curve, self.today, self.curve)
        self.assertAlmostEqual(585.2860029102303, bpv)

        # bond bpv

        bpv = get_basis_point_value(bnd, self.df, self.today, self.curve)
        self.assertAlmostEqual(0.0, bpv)

        bpv = get_basis_point_value(bnd, self.df, self.today)
        self.assertAlmostEqual(489.8885466804495, bpv)

        bpv = get_basis_point_value(bnd, self.curve, self.today)
        self.assertAlmostEqual(488.69274930632673, bpv)

        # frn bpv

        bpv = get_basis_point_value(frn, self.df, self.today, self.curve)
        bucket = get_bucketed_delta(
            frn, self.df, self.today, self.curve, self.schedule)
        self.assertAlmostEqual(585.4121890466267, bpv)
        self.assertAlmostEqual(sum(bucket), bpv)

        bpv = get_basis_point_value(frn, self.df, self.today)
        bucket = get_bucketed_delta(
            frn, self.df, self.today, delta_grid=self.schedule)
        self.assertAlmostEqual(-489.8885466804495, bpv)
        self.assertAlmostEqual(sum(bucket), bpv)

        bpv = get_basis_point_value(frn, self.curve, self.today)
        bucket = get_bucketed_delta(
            frn, self.curve, self.today, delta_grid=self.schedule)
        self.assertAlmostEqual(96.59325360390358, bpv)
        self.assertAlmostEqual(sum(bucket), bpv, 2)

        bpv = get_basis_point_value(
            frn, self.df, self.today, (self.curve, self.df))
        self.assertAlmostEqual(95.37909696914721, bpv)
        bucket = get_bucketed_delta(
            frn, self.df, self.today, (self.curve, self.df), self.schedule)
        self.assertAlmostEqual(sum(bucket), bpv, 0)


class CurveFittingTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today + '1y', self.today + '5y', '1y')
        lens = len(self.schedule)
        self.rate = 0.01
        rates = [(self.rate + 0.001 * i * (-1)**i) for i in range(lens)]
        self.df = ZeroRateCurve(self.schedule, rates)

    def test_discount_curve_fitting(self):
        notional = 1e6
        products = list()
        pvs = list()
        for d in self.schedule:
            schedule = tuple(s for s in self.schedule if s <= d)
            leg1 = RateCashFlowList(schedule, -notional, origin=self.today, fixed_rate=self.rate)
            leg2 = RateCashFlowList(schedule, notional, origin=self.today, forward_curve=self.df)
            swp = CashFlowLegList((leg1, leg2))
            pv = get_present_value(swp, self.df, self.today)
            products.append(swp)
            pvs.append(pv)

        curve = ZeroRateCurve(self.schedule, [self.rate] * len(self.schedule))
        data = get_curve_fit(products, curve, self.today, present_value=pvs)
        # curve = ZeroRateCurve([self.today], [self.rate])
        # data = get_curve_fit(products, curve, self.today, curve, self.schedule, pvs)
        for p, q in zip(data, self.df(self.df.domain)):
            self.assertAlmostEqual(p, q)
