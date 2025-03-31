
from regtest import RegressionTestCase

from dcf.daycount import day_count
from dcf import pv, CashFlowList, OptionCashFlowPayOff
from yieldcurves import YieldCurve, OptionPricingCurve, DateCurve


class ContingentCashFlowRegTests(RegressionTestCase):
    def setUp(self):
        self.origin = 0.0
        self.zero_rate = 0.02

        self.taus = 0.1, 1.0, 2.3, 10.0
        self.strikes = 100, 120, 130
        self.df = YieldCurve(0.02)
        fwd = YieldCurve(0.05, spot_price=100.)
        self.black76 = OptionPricingCurve.black76(fwd.price, 0.1)
        fwd = YieldCurve.from_interpolation([1, 5], [-0.001, 0.015])
        self.bachelier = OptionPricingCurve.black76(fwd.cash, 0.1)


    def test_option_cashflow_list(self):
        model = self.black76
        for tau in self.taus:
            for strike in self.strikes:
                flows = CashFlowList.from_option_cashflows(
                    [tau], strike_list=strike, forward_curve=model)
                for cf in flows:
                    self.assertAlmostRegressiveEqual(cf(forward_curve=model))
                self.assertAlmostRegressiveEqual(
                    pv(flows, self.origin, self.df))

    def test_option_strategy_cashflow_list(self):
        model = self.black76
        flows = CashFlowList()
        for tau in self.taus:
            flows.append(OptionCashFlowPayOff(tau, strike=90.))
            flows.append(OptionCashFlowPayOff(tau, strike=110.))
            flows.append(OptionCashFlowPayOff(
                tau, amount=-2, strike=90., option_type='put'))
            for cf in flows:
                self.assertAlmostRegressiveEqual(cf(forward_curve=model))
            self.assertAlmostRegressiveEqual(pv(flows, self.origin, self.df))

    def test_contingent_rate_cashflow_list(self):
        model = self.bachelier
        flows = CashFlowList.from_contingent_rate_cashflows(
            list(range(1,6)), origin=0, fixed_rate=0.01,
            cap_strike=0.013, floor_strike=0.001, forward_curve=model)

        for cf in flows:
            self.assertAlmostRegressiveEqual(float(cf(model)))
        self.assertAlmostRegressiveEqual(pv(flows, self.origin, self.df))
