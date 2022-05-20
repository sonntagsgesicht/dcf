
from regtest import RegressionTestCase

from dcf.daycount import day_count
from dcf.cashflows.contingent import ContingentCashFlowList, \
    ContingentRateCashFlowList, OptionCashflowList, OptionStrategyCashflowList
from dcf.curves.interestratecurve import ZeroRateCurve, CashRateCurve
from dcf.curves.curve import ForwardCurve
from dcf.models.bachelier import NormalOptionPayOffModel
from dcf.models.black76 import LogNormalOptionPayOffModel
from dcf.pricer import get_present_value


class ContingentCashFlowRegTests(RegressionTestCase):
    def setUp(self):
        self.origin = 0.0
        self.zero_rate = 0.02

        self.kwargs = {
            'valuation_date': self.origin,
            'forward_curve': ForwardCurve([0.0], [100.0], yield_curve=0.05),
            'volatility_curve': lambda *_: 0.1,
            'day_count': day_count
        }

        self.taus = 0.1, 1.0, 2.3, 10.0
        self.strikes = 100, 120, 130

    def test_option_cashflow_list(self):
        model = LogNormalOptionPayOffModel(**self.kwargs)
        for tau in self.taus:
            for strike in self.strikes:
                flows = OptionCashflowList([tau],
                                           strike_list=strike,
                                           payoff_model=model)
                for d in flows.domain:
                    self.assertAlmostRegressiveEqual(flows[d])
                curve = ZeroRateCurve([self.origin], [self.zero_rate])
                pv = get_present_value(flows, curve)
                self.assertAlmostRegressiveEqual(pv)

    def test_option_strategy_cashflow_list(self):
        model = LogNormalOptionPayOffModel(**self.kwargs)
        for tau in self.taus:
            call_amount_list = 1., 1.
            call_strike_list = 90., 110.,
            put_amount_list = -2.,
            put_strike_list = 100.,
            flows = OptionStrategyCashflowList([tau],
                                               call_amount_list=call_amount_list,
                                               call_strike_list=call_strike_list,
                                               put_amount_list=put_amount_list,
                                               put_strike_list=put_strike_list,
                                               payoff_model=model)
            for d in flows.domain:
                self.assertAlmostRegressiveEqual(flows[d])

            curve = ZeroRateCurve([self.origin], [self.zero_rate])
            pv = get_present_value(flows, curve)
            self.assertAlmostRegressiveEqual(pv)

    def test_contingent_rate_cashflow_list(self):
        kwargs = dict(**self.kwargs)
        kwargs['forward_curve'] = \
            CashRateCurve([1, 5], [-0.001, 0.015])
        model = NormalOptionPayOffModel(**self.kwargs)
        flows = ContingentRateCashFlowList(list(range(1,6)),
                                           origin=0,
                                           fixed_rate=0.01,
                                           cap_strike=0.013,
                                           floor_strike=0.001,
                                           payoff_model=model)

        for d in flows.domain:
            self.assertAlmostRegressiveEqual(flows[d])

        curve = ZeroRateCurve([self.origin], [self.zero_rate])
        pv = get_present_value(flows, curve)
        self.assertAlmostRegressiveEqual(pv)
