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

from businessdate import BusinessDate
from dcf import ecf, pv, ytm, fair, iac, bpv, delta, fit, CashFlowList
from yieldcurves import DateCurve

from .data import swap_curves, par_swap, par_bond, par_loan


class PricerUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.yc, self.fwd1, self.fwd3, self.fwd6 = swap_curves(self.today)
        self.swaps = []
        self.bonds = []
        self.loans = []
        self.frns = []
        for maturity in ('2y', '3y', '5y', '10y', '20y'):
            swap = par_swap(self.today, maturity, discount_curve=self.yc.df)
            self.swaps.append(swap)

            bond = par_bond(self.today, maturity, discount_curve=self.yc.df)
            self.swaps.append(bond)

            loan = par_loan(self.today, maturity, discount_curve=self.yc.df)
            self.swaps.append(loan)

    def test_ecf(self):
        for swap in self.swaps:
            self.assertLess(0., max(ecf(swap, self.today).values()))
        for bond in self.bonds:
            bond = CashFlowList(cf for cf in bond if 0.0 < float(cf()))
            self.assertLess(0., max(ecf(bond, self.today).values()))
        for frn in self.frns:
            frn = CashFlowList(cf for cf in frn if 0.0 < float(cf()))
            self.assertLess(0., max(ecf(frn, self.today).values()))
        for loan in self.loans:
            loan = CashFlowList(cf for cf in loan if 0.0 < float(cf()))
            self.assertLess(0., max(ecf(loan, self.today).values()))

    def test_pv(self):
        for swap in self.swaps:
            self.assertAlmostEqual(0., pv(swap, self.yc.df, self.today))
        for bond in self.bonds:
            self.assertAlmostEqual(0., pv(bond, self.yc.df, self.today))
        for loan in self.loans:
            self.assertAlmostEqual(0., pv(loan, self.yc.df, self.today))

    def _test_ytm(self):
        rate = 0.01
        DateCurve.from_interpolation([self.today], [rate])

        for swap in self.swaps:
            self.assertAlmostEqual(0., pv(swap, self.yc.df, self.today))
            self.assertAlmostEqual(rate, ytm(swap, self.today))
        for bond in self.bonds:
            self.assertAlmostEqual(0., pv(bond, self.yc.df, self.today))
            self.assertAlmostEqual(rate, ytm(bond, self.today))
        for loan in self.loans:
            self.assertAlmostEqual(0., pv(loan, self.yc.df, self.today))
            self.assertAlmostEqual(rate, ytm(loan, self.today))

    def _test_fair(self):
        rate = 0.01
        DateCurve.from_interpolation([self.today], [rate])

        for swap in self.swaps:
            self.assertAlmostEqual(0., pv(swap, self.yc.df, self.today))
            self.assertAlmostEqual(rate, swap.fixed_rate)
        for bond in self.bonds:
            self.assertAlmostEqual(0., pv(bond, self.yc.df, self.today))
            self.assertAlmostEqual(rate, bond.fixed_rate)
        for loan in self.loans:
            self.assertAlmostEqual(0., pv(loan, self.yc.df, self.today))
            self.assertAlmostEqual(rate, loan.fixed_rate)

    def test_iac(self):
        for bond in self.bonds:
            cfs = CashFlowList.from_fixed_cashflows(bond.domain, 1.)
            self.assertAlmostEqual(0.0, iac(cfs, self.today + '2w2d'))
            self.assertLess(0.0, iac(bond, self.today + '2w2d'))
        for frn in self.frns:
            cfs = CashFlowList.from_fixed_cashflows(frn.domain, 1.)
            self.assertAlmostEqual(0.0, iac(cfs, self.today + '2w2d'))
            self.assertLess(0.0, iac(frn, self.today + '2w2d'))

    def _test_bpv(self):
        notional = 1e6
        fix1 = CashFlowList.from_fixed_cashflows([max(self.schedule)], notional)
        fix2 = CashFlowList.from_fixed_cashflows([max(self.schedule)], notional)
        leg1 = CashFlowList.from_rate_cashflows(self.schedule, notional, fixed_rate=self.rate)
        leg2 = CashFlowList.from_rate_cashflows(self.schedule, notional, forward_curve=self.curve)

        swp = leg2 - leg1
        bnd = fix1 + leg1
        frn = fix2 + leg2

        total = sum(swp[swp.domain])
        self.assertAlmostEqual(0.0, total)

        bpv1 = bpv(leg1, self.df, self.today, self.df)
        bpv2 = bpv(leg2, self.df, self.today, self.df)
        self.assertAlmostEqual(bpv1, -bpv2)

        # swap bpv

        bpv3 = bpv(swp, self.df, self.today, self.df)
        self.assertAlmostEqual(0.0, bpv3)

        bpv4 = bpv(swp, self.df, self.today, self.curve)
        self.assertAlmostEqual(585.4121890466267, bpv4)

        bpv5 = bpv(swp, self.curve, self.today, self.curve)
        self.assertAlmostEqual(585.2860029102303, bpv5)

        # bond bpv

        bpv6 = bpv(bnd, self.df, self.today, self.curve)
        self.assertAlmostEqual(0.0, bpv6)

        bpv7 = bpv(bnd, self.df, self.today)
        self.assertAlmostEqual(489.8885466804495, bpv7)

        bpv8 = bpv(bnd, self.curve, self.today)
        self.assertAlmostEqual(488.69274930632673, bpv8)

        # frn bpv

        bpv9 = bpv(frn, self.df, self.today, self.curve)
        bucket = delta(
            frn, self.df, self.today, self.curve, self.schedule)
        self.assertAlmostEqual(585.4121890466267, bpv9)
        self.assertAlmostEqual(sum(bucket), bpv9)

        bpv10 = bpv(frn, self.df, self.today)
        bucket = delta(
            frn, self.df, self.today, delta_grid=self.schedule)
        self.assertAlmostEqual(-489.8885466804495, bpv10)
        self.assertAlmostEqual(sum(bucket), bpv10)

        bpv11 = bpv(frn, self.curve, self.today)
        bucket = delta(
            frn, self.curve, self.today, delta_grid=self.schedule)
        self.assertAlmostEqual(96.59325360390358, bpv11)
        self.assertAlmostEqual(sum(bucket), bpv11, 2)

        bpv12 = bpv(
            frn, self.df, self.today, (self.curve, self.df))
        self.assertAlmostEqual(95.37909696914721, bpv12)
        bucket = delta(
            frn, self.df, self.today, (self.curve, self.df), self.schedule)
        self.assertAlmostEqual(sum(bucket), bpv12, 0)

    def _test_discount_curve_fitting(self):
        ...
