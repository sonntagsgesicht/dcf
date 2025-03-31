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

from dcf import ecf, pv, iac, ytm, fair, bpv, delta, fit, CashFlowList
from yieldcurves import DateCurve

from .data import par_swap, par_bond, par_loan, par_frn, swap_curve, fwd_curve


class PricerUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.yc = swap_curve(self.today)
        self.fwd1 = fwd_curve(self.today, cash_frequency=12)
        self.fwd3 = fwd_curve(self.today, cash_frequency=4)
        self.fwd6 = fwd_curve(self.today, cash_frequency=2)
        self.swaps = []
        self.bonds = []
        self.loans = []
        self.frns = []
        for maturity in ('2y', '3y', '5y', '10y', '20y'):
            swap = par_swap(self.today, maturity, discount_curve=self.yc.df)
            self.swaps.append(swap)

            bond = par_bond(self.today, maturity, discount_curve=self.yc.df)
            self.bonds.append(bond)

            frn = par_frn(self.today, maturity, discount_curve=self.yc.df)
            self.frns.append(frn)

            loan = par_loan(self.today, maturity, discount_curve=self.yc.df)
            self.loans.append(loan)

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
            _pv = pv(swap, self.today, self.yc.df)
            self.assertAlmostEqual(0., _pv)
        for bond in self.bonds:
            _pv = pv(bond, self.today, self.yc.df)
            self.assertAlmostEqual(0., _pv)
        for loan in self.loans:
            _pv = pv(loan, self.today, self.yc.df)
            self.assertAlmostEqual(0., _pv)

    def test_iac(self):
        for bond in self.bonds:
            cfs = CashFlowList.from_fixed_cashflows(bond.domain, 1.)
            self.assertAlmostEqual(0.0, iac(cfs, self.today + '2w2d'))
            self.assertLess(0.0, iac(bond, self.today + '2w2d'))
        for frn in self.frns:
            cfs = CashFlowList.from_fixed_cashflows(frn.domain, 1.)
            self.assertAlmostEqual(0.0, iac(cfs, self.today + '2w2d'))
            self.assertLess(0.0, iac(frn, self.today + '2w2d'))

    def test_ytm(self):
        rate = 0.01
        df = DateCurve.from_interpolation([self.today], [rate],
                                          origin=self.today)
        for bond in self.bonds:
            bond.fixed_rate = rate
            _pv = pv(bond, self.today, df)
            _ytm = ytm(bond, self.today, present_value=_pv)
            self.assertAlmostEqual(0.0, abs(_ytm - rate), places=5)
        for loan in self.loans:
            _pv = pv(loan, self.today, df)
            _ytm = ytm(loan, self.today, present_value=_pv)
            self.assertAlmostEqual(0.0, abs(_ytm - rate), places=5)

    def test_fair(self):
        for swap in self.swaps:
            _fair = fair(swap, self.today, self.yc)
            self.assertAlmostEqual(_fair, swap.fixed_rate)
        for bond in self.bonds:
            _fair = fair(bond, self.today, self.yc)
            self.assertAlmostEqual(_fair, bond.fixed_rate)
        for loan in self.loans:
            _fair = fair(loan, self.today, self.yc)
            self.assertAlmostEqual(_fair, loan.fixed_rate)

    def test_bpv(self):

        for bond, frn in zip(self.bonds, self.frns):
            swap = frn[:-2] - bond[:-2]
            _bpv_swap = bpv(swap, self.today, self.yc, delta_curve=self.yc.curve.curve, forward_curve=self.yc)
            _bpv_bond = bpv(bond, self.today, self.yc, delta_curve=self.yc.curve.curve, forward_curve=self.yc)
            _bpv_frn = bpv(frn, self.today, self.yc, delta_curve=self.yc.curve.curve, forward_curve=self.yc)
            self.assertAlmostEqual(_bpv_swap + _bpv_bond, _bpv_frn)

    def _test_delta(self):
        ...

    def _test_fit(self):
        ...
