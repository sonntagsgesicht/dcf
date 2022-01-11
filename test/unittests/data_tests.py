
from unittest import TestCase

from businessdate import BusinessDate, BusinessPeriod, BusinessRange

from dcf import ZeroRateCurve, CashRateCurve, data


term = '1y', '2y', '5y', '10y', '15y', '20y', '30y'
zeros = -0.0084, -0.0079, -0.0057, -0.0024, -0.0008, -0.0001, 0.0003

fwd_term = '2d', '3m', '6m', '1y', '2y', '5y', '10y'
fwd_1m = -0.0057, -0.0057, -0.0053, -0.0036, -0.0010, 0.0014, 0.0066
fwd_3m = -0.0056, -0.0054, -0.0048, -0.0033, -0.0002, 0.0018, 0.0066
fwd_6m = -0.0053, -0.0048, -0.0042, -0.0022, 0.0002, 0.0022, 0.0065

start = BusinessDate(20211201)

zero_curve = ZeroRateCurve([start + t for t in term], zeros,
                           origin=start)
fwd_curve_1m = CashRateCurve([start + t for t in fwd_term], fwd_1m,
                             origin=start, forward_tenor=BusinessPeriod('1m'))
fwd_curve_3m = CashRateCurve([start + t for t in fwd_term], fwd_3m,
                             origin=start, forward_tenor=BusinessPeriod('3m'))
fwd_curve_6m = CashRateCurve([start + t for t in fwd_term], fwd_6m,
                             origin=start, forward_tenor=BusinessPeriod('6m'))


class CurveDataUnitTest(TestCase):

    def assert_curve(self, curve_a, curve_b):
        a = curve_a.origin
        b = curve_b.origin
        self.assertEqual(a, b)
        a = curve_a.domain
        b = curve_b.domain
        self.assertEqual(a, b)

        for e in BusinessRange(start, curve_a.domain[-1], step=BusinessPeriod('1m')):
            a = curve_a.get_zero_rate(e)
            b = curve_b.get_zero_rate(e)
            self.assertAlmostEqual(a, b)

            a = curve_a.get_zero_rate(e, e - curve_a.forward_tenor)
            b = curve_b.get_zero_rate(e, e - curve_a.forward_tenor)
            self.assertAlmostEqual(a, b)

            a = curve_a.get_discount_factor(e)
            b = curve_b.get_discount_factor(e)
            self.assertAlmostEqual(a, b)

            a = curve_a.get_cash_rate(e)
            b = curve_b.get_cash_rate(e)
            self.assertAlmostEqual(a, b)

    def test_zero_curve(self):
        self.assert_curve(zero_curve, data.zero_curve)

    def test_fwd_curve_1m(self):
        self.assert_curve(fwd_curve_1m, data.fwd_curve_1m)

    def test_fwd_curve_3m(self):
        self.assert_curve(fwd_curve_3m, data.fwd_curve_3m)

    def test_fwd_curve_6m(self):
        self.assert_curve(fwd_curve_6m, data.fwd_curve_6m)
