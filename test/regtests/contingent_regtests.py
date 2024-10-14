
from regtest import RegressionTestCase

from dcf.daycount import day_count
from dcf import pv, CashFlowList, OptionPayOffModel, OptionCashFlowPayOff
from yieldcurves import YieldCurve


class ContingentCashFlowRegTests(RegressionTestCase):
    def setUp(self):
        self.origin = 0.0
        self.zero_rate = 0.02

        fwd = YieldCurve(0.05, spot_price=100.)
        self.kwargs = {
            'valuation_date': self.origin,
            'forward_curve': fwd.price,
            'volatility_curve': lambda *_: 0.1,
            'day_count': day_count
        }

        self.taus = 0.1, 1.0, 2.3, 10.0
        self.strikes = 100, 120, 130
        self.df = YieldCurve(0.02).df

    def test_option_cashflow_list(self):
        model = OptionPayOffModel.black76(**self.kwargs)
        for tau in self.taus:
            for strike in self.strikes:
                flows = CashFlowList.from_option_cashflows(
                    [tau], strike_list=strike, payoff_model=model)
                for cf in flows:
                    self.assertAlmostRegressiveEqual(float(cf.details(model)))
                self.assertAlmostRegressiveEqual(
                    pv(flows, self.df, self.origin))

    def test_option_strategy_cashflow_list(self):
        model = OptionPayOffModel.black76(**self.kwargs)
        flows = CashFlowList()
        for tau in self.taus:
            flows.append(OptionCashFlowPayOff(tau, strike=90., is_put=False))
            flows.append(OptionCashFlowPayOff(tau, strike=110., is_put=False))
            flows.append(OptionCashFlowPayOff(
                tau, amount=-2, strike=90., is_put=True))
            for cf in flows:
                self.assertAlmostRegressiveEqual(float(cf.details(model)))
            self.assertAlmostRegressiveEqual(pv(flows, self.df, self.origin))

    def test_contingent_rate_cashflow_list(self):
        fwd = YieldCurve.from_interpolation([1, 5], [-0.001, 0.015])
        kwargs = dict(**self.kwargs)
        kwargs['forward_curve'] = fwd.cash
        model = OptionPayOffModel.bachelier(**self.kwargs)
        flows = CashFlowList.from_contingent_rate_cashflows(
            list(range(1,6)), origin=0, fixed_rate=0.01,
            cap_strike=0.013, floor_strike=0.001, payoff_model=model)

        for cf in flows:
            self.assertAlmostRegressiveEqual(float(cf(model)))
        self.assertAlmostRegressiveEqual(pv(flows, self.df, self.origin))
