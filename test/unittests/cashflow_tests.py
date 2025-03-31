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
from dcf import CashFlowList


class CashflowListUnitTests(TestCase):
    def setUp(self):
        self.today = BusinessDate(20161231)
        self.schedule = BusinessSchedule(self.today, self.today + '5y', '1m')

        self.cf_list = (
            CashFlowList.from_fixed_cashflows(self.schedule),
            CashFlowList.from_rate_cashflows(self.schedule),
            CashFlowList.from_option_cashflows(self.schedule),
            CashFlowList.from_contingent_rate_cashflows(self.schedule),
        )

    def test_str_repr(self):
        for cf in self.cf_list:

            self.assertIsInstance(cf, CashFlowList)
            # self.assertEqual(len(self.schedule), len(cf), msg=repr(cf))

            str_cf = str(cf)
            repr_cf = repr(cf)

            self.assertNotIn(CashFlowList.__name__, str_cf)
            self.assertIn(CashFlowList.__name__, repr_cf)

            self.assertNotIn(repr(cf[0]), str_cf)
            self.assertIn(repr(cf[0]), repr_cf)

    def test_float_cashflow(self):
        domain = self.schedule[:3]
        cf_list = (
            CashFlowList.from_fixed_cashflows(domain),
            CashFlowList.from_rate_cashflows(domain),
            CashFlowList.from_option_cashflows(domain),
            CashFlowList.from_contingent_rate_cashflows(domain),
        )
        for cf in cf_list:
            map(float, cf)
            self.assertTrue(True)
