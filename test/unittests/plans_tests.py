from unittest.case import TestCase

from businessdate import BusinessDate, BusinessSchedule

from dcf.plans import DEFAULT_AMOUNT, FIXED_RATE, flat, bullet, amortize, annuity, consumer
from dcf import ZeroRateCurve


class AmortizationUnitTests(TestCase):

    def test_flat(self):
        n = 20
        cfs = flat(n)
        self.assertEqual(n, len(cfs))
        for cf in cfs:
            self.assertAlmostEqual(DEFAULT_AMOUNT, cf)

    def test_bullet(self):
        n = 20
        cfs = bullet(n)
        self.assertEqual(n, len(cfs))
        self.assertEqual(DEFAULT_AMOUNT, sum(cfs))
        cf = cfs.pop(-1)
        self.assertAlmostEqual(DEFAULT_AMOUNT, cf)
        for cf in cfs:
            self.assertAlmostEqual(0, cf)

    def test_amortize(self):
        n = 20
        cfs = amortize(n)
        self.assertEqual(n, len(cfs))
        self.assertEqual(DEFAULT_AMOUNT, sum(cfs))
        for cf in cfs:
            self.assertAlmostEqual(DEFAULT_AMOUNT/n, cf)

    def test_annuity(self):
        n = 20
        cfs = annuity(n)
        self.assertEqual(n, len(cfs))
        self.assertEqual(DEFAULT_AMOUNT, sum(cfs))
        a = cfs[0]
        b = cfs[-1] * (1 + FIXED_RATE)
        total = DEFAULT_AMOUNT
        for i, cf in enumerate(cfs):
            self.assertAlmostEqual(a, cf)
            a = a * (1 + FIXED_RATE)
            interest = total * FIXED_RATE
            self.assertAlmostEqual(b, cf + interest)
            total -= cf

