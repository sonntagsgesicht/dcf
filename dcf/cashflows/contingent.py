# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.6, copyright Sunday, 19 December 2021
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from ..base.day_count import day_count as default_day_count
from ..base.plans import DEFAULT_AMOUNT
from .cashflow import CashFlowList as _CashFlowList, \
    RateCashFlowList as _RateCashFlowList


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
            if isinstance(payoff, (int, float)):
                return payoff
            return payoff(self.payoff_model)


class ContingentRateCashFlowList(ContingentCashFlowList):
    """ list of cashflows by interest rate payments """

    class RateCashFlowCollaredPayOff(object):

        def __init__(self, start, end=None, amount=1.0,
                     day_count=None, fixed_rate=0.0,
                     cap_strike=None, floor_strike=None):
            self.start = start
            self.end = end
            self.day_count = day_count or default_day_count
            self.amount = amount
            self.fixed_rate = fixed_rate
            self.cap_strike = None
            self.floor_strike = None

        def __call__(self, model=None):
            fwd = model.get_forward_value(self.start)
            rate = self.fixed_rate
            rate += fwd
            if self.cap_strike:
                rate -= model.get_call_value(self.start, self.cap_strike, fwd)
            if self.floor_strike:
                rate += model.get_put_value(self.start, self.floor_strike, fwd)
            yf = self.day_count(self.start, self.end)
            return rate * yf * self.amount


    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 origin=None, day_count=None,
                 fixing_offset=None, pay_offset=None,
                 fixed_rate=0., cap_strike=None, floor_strike=None,
                 payoff_model=DEFAULT_PAYOFF_MODEL):
        """

        :param payment_date_list: pay dates, assuming that pay dates agree
            with end dates of interest accrued period
        :param amount_list: notional amounts
        :param origin: start date of first interest accrued period
        :param day_count: day count convention
        :param fixed_rate: agreed fixed rate
        :param forward_curve:
        :param fixing_offset: time difference between
            interest rate fixing date and interest period payment date
        :param pay_offset: time difference between
            interest period end date and interest payment date
        :param cap_strike:
        :param floor_strike:

        """

        self.day_count = day_count or default_day_count

        payoff_list = list()
        if origin is None and payment_date_list:
            origin = payment_date_list[0]
        start_dates = [origin]
        start_dates.extend(payment_date_list[:-1])
        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            payoff = self.RateCashFlowPayOff(
                start=s, end=e, day_count=day_count,
                amount=a, fixed_rate=fixed_rate,
                cap_strike=cap_strike, floor_strike=floor_strike
            )
            payoff_list.append(payoff)

        super().__init__(payment_date_list, payoff_list,
                         origin=origin, payoff_model=payoff_model)

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
