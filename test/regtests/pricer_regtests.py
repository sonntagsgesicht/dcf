# -*- coding: utf-8 -*-

# auxilium
# --------
# A Python project for an automated test and deploy toolkit - 100%
# reusable.
#
# Author:   sonntagsgesicht
# Version:  0.1.4, copyright Sunday, 11 October 2020
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from os import getcwd
from os.path import basename, split
from regtest import RegressionTestCase
from businessdate import BusinessDate, BusinessPeriod, BusinessSchedule
from dcf import ZeroRateCurve, CashRateCurve
from dcf import CashFlowLegList, FixedCashFlowList, RateCashFlowList
from dcf import get_present_value, get_fair_rate


pkg = __import__(basename(getcwd()))


# first run will build reference values (stored in files)
# second run will test against those reference values
# to update reference values simply remove the according files

term = '1y', '2y', '5y', '10y', '15y', '20y', '30y'
zeros = -0.0084, -0.0079, -0.0057, -0.0024, -0.0008, -0.0001, 0.0003

fwd_term = '2d', '3m', '6m', '1y', '2y', '5y', '10y'
fwd_1m = -0.0057, -0.0057, -0.0053, -0.0036, -0.0010, 0.0014, 0.0066
fwd_3m = -0.0056, -0.0054, -0.0048, -0.0033, -0.0002, 0.0018, 0.0066
fwd_6m = -0.0053, -0.0048, -0.0042, -0.0022, 0.0002, 0.0022, 0.0065

start = BusinessDate(20211201)

zero_curve = ZeroRateCurve([start + t for t in term], zeros)
fwd_curve_1m = CashRateCurve([start + t for t in fwd_term], fwd_1m,
                             forward_tenor=BusinessPeriod('1m'))
fwd_curve_3m = CashRateCurve([start + t for t in fwd_term], fwd_3m,
                             forward_tenor=BusinessPeriod('3m'))
fwd_curve_6m = CashRateCurve([start + t for t in fwd_term], fwd_6m,
                             forward_tenor=BusinessPeriod('6m'))

notional = 1.0
maturities = '2y', '5y', '10y', '20y'


class PricerRegTests(RegressionTestCase):

    def cashflow_details(self):
        for maturity in maturities:
            end = start + maturity
            schedule = BusinessSchedule(start, end, '1y', end)
            schedule_3m = BusinessSchedule(start, end, '3m', end)
            float_leg = RateCashFlowList(schedule, notional, forward_curve=fwd_curve_3m)
            float_pv = get_present_value(float_leg, zero_curve, start)
            fixed_leg = RateCashFlowList(schedule, -notional, fixed_rate=0.01)
            par_rate = get_fair_rate(fixed_leg, zero_curve, start, -float_pv)
            fixed_leg.fixed_rate = par_rate
            swap = CashFlowLegList([float_leg, fixed_leg], start)

            self.assertAlmostRegressiveEqual(par_rate)
            self.assertAlmostEqual(0.0, get_present_value(swap, zero_curve, start))
            self.assertAlmostRegressiveEqual(pkg.get_basis_point_value(swap, zero_curve, zero_curve, start))

    def test_bond_bpv(self):
        for maturity in maturities:
            end = start + maturity
            schedule = BusinessSchedule(start, end, '1y', end)
            rate_flows = RateCashFlowList(schedule, notional, fixed_rate=0.01)
            redemption_flows = FixedCashFlowList([end], [notional])
            zero_pv = get_present_value(redemption_flows, zero_curve, start)
            par_rate = get_fair_rate(rate_flows, zero_curve, start, notional - zero_pv)
            rate_flows.fixed_rate = par_rate
            bond = CashFlowLegList([rate_flows, redemption_flows])

            self.assertAlmostRegressiveEqual(par_rate)
            self.assertAlmostEqual(notional, get_present_value(bond, zero_curve, start))
            self.assertAlmostRegressiveEqual(pkg.get_basis_point_value(bond, zero_curve, start))

    def test_swap_x_bpv(self):
        for maturity in maturities:
            end = start + maturity
            schedule = BusinessSchedule(start, end, '1y', end)
            schedule_3m = BusinessSchedule(start, end, '3m', end)
            float_leg = RateCashFlowList(schedule, notional, forward_curve=fwd_curve_3m)
            float_pv = get_present_value(float_leg, zero_curve, start)
            fixed_leg = RateCashFlowList(schedule, -notional, fixed_rate=0.01)
            par_rate = get_fair_rate(fixed_leg, zero_curve, start, -float_pv)
            fixed_leg.fixed_rate = par_rate
            swap = CashFlowLegList([float_leg, fixed_leg])

            self.assertAlmostRegressiveEqual(par_rate)
            self.assertAlmostEqual(0.0, get_present_value(swap, zero_curve, start))
            self.assertAlmostRegressiveEqual(pkg.get_basis_point_value(swap, zero_curve, start))
