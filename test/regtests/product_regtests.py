from businessdate.daycount import get_act_act

from dcf import ZeroRateCurve
from dcf import bond, interest_rate_swap, asset_swap
from dcf.pricer import get_present_value, get_basis_point_value, get_bucketed_delta
from dcf.data import zero_curve, fwd_curve_3m

from regtest import RegressionTestCase

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


