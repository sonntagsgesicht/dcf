from businessdate.daycount import get_act_act

from dcf import ZeroRateCurve, CashRateCurve
from dcf import bond, interest_rate_swap, asset_swap
from dcf.pricer import get_present_value, get_basis_point_value, get_bucketed_delta

from regtest import RegressionTestCase

# -*- codi

from businessdate import BusinessDate, BusinessPeriod

today = BusinessDate(20211201)
b = BusinessPeriod('1b')
d = BusinessPeriod('1d')
m = BusinessPeriod('1m')
y = BusinessPeriod('1y')

tenor_1m = 1 * m
tenor_3m = 3 * m
tenor_6m = 6 * m

zeros_term = 1 * y, 2 * y, 5 * y, 10 * y, 15 * y, 20 * y, 30 * y
fwd_term = 2 * b, 3 * m, 6 * m, 1 * y, 2 * y, 5 * y, 10 * y

zeros = -0.0084, -0.0079, -0.0057, -0.0024, -0.0008, -0.0001, 0.0003

fwd_1m = -0.0057, -0.0057, -0.0053, -0.0036, -0.0010, 0.0014, 0.0066
fwd_3m = -0.0056, -0.0054, -0.0048, -0.0033, -0.0002, 0.0018, 0.0066
fwd_6m = -0.0053, -0.0048, -0.0042, -0.0022, 0.0002, 0.0022, 0.0065

zero_curve = ZeroRateCurve([today + t for t in zeros_term], zeros,
                           origin=today)
fwd_curve_1m = CashRateCurve([today + t for t in fwd_term], fwd_1m,
                             origin=today, forward_tenor=tenor_1m)
fwd_curve_3m = CashRateCurve([today + t for t in fwd_term], fwd_3m,
                             origin=today, forward_tenor=tenor_3m)
fwd_curve_6m = CashRateCurve([today + t for t in fwd_term], fwd_6m,
                             origin=today, forward_tenor=tenor_6m)

today = zero_curve.origin
maturities = '1y6m', '5y', '10y', '20y'
tenor = '1y'

zero_curve = ZeroRateCurve([today, today + '1y', today + '2y'], [0.01, 0.01, 0.01])


class ProductRegTests(RegressionTestCase):
    compression = False
    def test_bond_bpv(self):
        for maturity in maturities[:1]:
            b = bond(today, today + maturity, tenor, day_count=get_act_act, fixed_rate=0.01)
            self.assertAlmostRegressiveEqual(get_present_value(b, zero_curve, today))

            bpv = get_basis_point_value(b, zero_curve, today)
            self.assertAlmostRegressiveEqual(bpv)

            buckets = get_bucketed_delta(b, zero_curve, today, delta_grid=zero_curve.domain)
            # self.assertAlmostEqual(bpv, sum(buckets))

            for b in buckets:
                self.assertAlmostRegressiveEqual(b)
