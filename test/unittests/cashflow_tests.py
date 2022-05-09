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
from businessdate.daycount import get_30_360
from dcf import CashRateCurve
from dcf import FixedCashFlowList, RateCashFlowList, CashFlowLegList
from dcf.plans import DEFAULT_AMOUNT


class CashflowListUnitTests(TestCase):
    def setUp(self):
        self.cls = FixedCashFlowList
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')
        self.amount = 111

    def test_str(self):
        cf = self.cls(self.schedule[:3])

        self.assertIn(self.cls.__name__, str(cf))
        self.assertIn(repr(cf.domain[0]), str(cf))
        self.assertIn(repr(cf.domain[-1]), str(cf))

        self.assertIn(self.cls.__name__, repr(cf))
        self.assertIn(str(cf.domain), repr(cf))

        fx = FixedCashFlowList(cf)

        self.assertEqual(cf.domain, fx.domain)
        self.assertIn(str(cf.domain), repr(fx))
        self.assertIn(str(cf[cf.domain]), repr(fx))

        cf = self.cls(self.schedule, self.amount)

        self.assertIn(repr(self.amount), str(cf))
        self.assertIn(repr(self.amount), repr(cf))


class FixedCashflowListUnitTests(CashflowListUnitTests):

    def test_init(self):
        cf = self.cls(self.schedule)

        for d in cf.domain:
            self.assertEqual(DEFAULT_AMOUNT, cf[d])
            self.assertIn(d, cf.domain)

        cf = self.cls(self.schedule, self.amount)
        for d in cf.domain:
            self.assertEqual(self.amount, cf[d])
            self.assertIn(d, cf.domain)


class RateCashflowListUnitTests(CashflowListUnitTests):

    def setUp(self):
        super(RateCashflowListUnitTests, self).setUp()
        self.cls = RateCashFlowList

    def test_init(self):
        rate = 0.1
        cf = self.cls(self.schedule, day_count=get_30_360, fixed_rate=rate, origin=self.today-'1m')

        for d in cf.domain:
            self.assertIn(d, cf.domain)
            if d.month == 2:
                self.assertTrue(rate * DEFAULT_AMOUNT / 12 > cf[d])
            elif d.month == 3:
                self.assertTrue(rate * DEFAULT_AMOUNT / 12 < cf[d])
            else:
                self.assertAlmostEqual(rate * DEFAULT_AMOUNT/12, cf[d])

    def test_forward_rate(self):
        leg1 = RateCashFlowList(self.schedule, 100., fixed_rate=1.)
        curve = CashRateCurve([self.today], [.1])
        leg2 = RateCashFlowList(self.schedule, 1000., forward_curve=curve)
        for d in self.schedule:
            self.assertAlmostEqual(leg1[d], leg2[d])


class CashflowLegListUnitTests(TestCase):

    def setUp(self):
        self.cls = CashFlowLegList
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')
        self.amount = 111

    def test_init(self):
        leg1 = RateCashFlowList(self.schedule, 100., fixed_rate=1.)
        curve = CashRateCurve([self.today], [.1])
        leg2 = RateCashFlowList(self.schedule, -1000., forward_curve=curve)

        cf = self.cls((leg1, leg2))
        for d in self.schedule:
            self.assertIn(d, cf.domain)
            self.assertAlmostEqual(0., cf[d])
