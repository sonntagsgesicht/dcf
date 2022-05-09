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

# test vs option pricing formulas
# test diff model with same price


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
