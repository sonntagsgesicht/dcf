# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.6, copyright Sunday, 19 December 2021
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .cashflow import CashFlowList as _CashFlowList, \
    RateCashFlowList as _RateCashFlowList
from .plans import DEFAULT_AMOUNT


DEFAULT_PAYOFF = DEFAULT_PAYOFF_MODEL = (lambda *_: 0.)


class ContingentCashFlowList(_CashFlowList):
    """ list of contingent cashflows """

    def __init__(self, payment_date_list, payoff_list=DEFAULT_PAYOFF,
                 origin=None, payoff_model=DEFAULT_PAYOFF_MODEL):
        """

        :param payment_date_list: pay dates, assuming that pay dates
            agree with end dates of interest accrued period
        :param payoff_list: list of payoffs
        :param origin: start date of first interest accrued period
        :param payoff_model: payoff model to derive the expected payoff
        """
        self.payoff_model = payoff_model
        super().__init__(payment_date_list, payoff_list, origin=origin)

    def __getitem__(self, item):
        """ getitem does re-calc contingent cashflows """
        if isinstance(item, (tuple, list)):
            return tuple(self[i] for i in item)
        else:
            payoff = self._flows.get(item, 0.)
            return payoff(item, self.payoff_model)


class ContingentRateCashFlowList(ContingentCashFlowList):
    """ list of cashflows by interest rate payments """

    class RateCashFlowPayOff(object):

        def __init__(self, start, end=None, day_count=None,
                     amount=1.0, fixed_rate=0.0):
            self.start = start
            self.end = end
            if day_count is None:
                day_count = _RateCashFlowList.DAY_COUNT
            self.day_count = day_count
            self.amount = amount
            self.fixed_rate = fixed_rate

        def __call__(self, date, model=None):
            yf = self.day_count(self.start, self.end or date)
            rate = self.fixed_rate
            if hasattr(model, 'get_cash_rate'):
                rate += model.get_cash_rate(self.start)
            # add caplet/floorlet here
            #     rate -= model.get_call_value(self.start, self.cap_strike)
            #     rate += model.get_put_value(self.start, self.floor_strike)
            return rate * yf * self.amount

    class RateCashFlowPayOffModel(object):

        def __init__(self, forward_curve=None):
            self.forward_curve = forward_curve

        def get_cash_rate(self, date):
            return self.forward_curve.get_cash_rate(date)

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 day_count=None, origin=None,
                 fixed_rate=0., forward_curve=None):
        """

        :param payment_date_list: pay dates, assuming that pay dates agree
            with end dates of interest accrued period
        :param amount_list: notional amounts
        :param origin: start date of first interest accrued period
        :param day_count: day count convention
        :param fixed_rate: agreed fixed rate
        :param forward_curve:
        """

        if day_count is None:
            day_count = _RateCashFlowList.DAY_COUNT
        self.day_count = day_count

        payoff_list = list()
        if origin is None and payment_date_list:
            origin = payment_date_list[0]
        start_dates = [origin]
        start_dates.extend(payment_date_list[:-1])
        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            payoff = self.RateCashFlowPayOff(
                start=s, end=e, day_count=day_count,
                amount=a, fixed_rate=fixed_rate)
            payoff_list.append(payoff)

        model = self.RateCashFlowPayOffModel(forward_curve)
        super().__init__(payment_date_list, payoff_list,
                         origin=origin, payoff_model=model)

    @property
    def fixed_rate(self):
        return self._flows[self.domain[0]].fixed_rate

    @fixed_rate.setter
    def fixed_rate(self, value):
        for date in self.domain:
            self._flows[date].fixed_rate = value

    @property
    def forward_curve(self):
        return self.payoff_model.forward_curve

    @forward_curve.setter
    def forward_curve(self, value):
        self.payoff_model.forward_curve = value
