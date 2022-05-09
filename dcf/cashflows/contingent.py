# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from ..daycount import day_count as default_day_count
from ..plans import DEFAULT_AMOUNT
from .cashflow import CashFlowList as _CashFlowList


DEFAULT_PAYOFF = DEFAULT_PAYOFF_MODEL = (lambda *_: 0.)


class ContingentCashFlowList(_CashFlowList):
    """ list of contingent cashflows """

    @property
    def table(self):
        # todo: contigent cashflow tbl
        raise NotImplementedError()

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

    @property
    def forward_curve(self):
        return self.payoff_model.forward_curve

    @forward_curve.setter
    def forward_curve(self, value):
        self.payoff_model.forward_curve = value


class OptionCashflowList(ContingentCashFlowList):
    """ list of option cashflows """

    class OptionCashFlowPayOff(object):

        def __init__(self, expiry, amount=DEFAULT_AMOUNT,
                     strike=None, is_call=True):
            self.expiry = expiry
            self.amount = amount
            self.strike = strike
            self.is_call = is_call

        def __call__(self, model):
            if self.is_call:
                return self.amount * \
                       model.get_call_value(self.expiry, self.strike)
            else:
                return self.amount * \
                       model.get_put_value(self.expiry, self.strike)

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 strike_list=(), is_call_list=True,
                 fixing_offset=None, pay_offset=None,
                 origin=None, payoff_model=DEFAULT_PAYOFF_MODEL):
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)
        if isinstance(strike_list, (int, float)):
            strike_list = [strike_list] * len(payment_date_list)
        if isinstance(is_call_list, (bool, int, float)):
            is_call_list = [is_call_list] * len(payment_date_list)

        payoff_list = list()
        cls = OptionCashflowList.OptionCashFlowPayOff
        for expiry, amount, strike, is_call in \
                zip(payment_date_list, amount_list, strike_list, is_call_list):
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            option = cls(expiry, amount, strike, is_call)
            payoff_list.append(option)
        super().__init__(payment_date_list, payoff_list, origin, payoff_model)


class OptionStrategyCashflowList(ContingentCashFlowList):
    """ list of option strategy cashflows """

    class OptionStrategyCashFlowPayOff(object):

        def __init__(self, expiry,
                     call_amount_list=DEFAULT_AMOUNT, call_strike_list=(),
                     put_amount_list=DEFAULT_AMOUNT, put_strike_list=()):
            if isinstance(call_amount_list, (int, float)):
                call_amount_list = [call_amount_list] * len(call_strike_list)
            if isinstance(put_amount_list, (int, float)):
                put_amount_list = [put_amount_list] * len(put_strike_list)

            self._options = list()
            cls = OptionCashflowList.OptionCashFlowPayOff
            for amount, strike in zip(call_amount_list, call_strike_list):
                option = cls(expiry, amount, strike, is_call=True)
                self._options.append(option)
            for amount, strike in zip(put_amount_list, put_strike_list):
                option = cls(expiry, amount, strike, is_call=False)
                self._options.append(option)

        def __call__(self, model):
            return sum(option(model) for option in self._options)

    def __init__(self, payment_date_list,
                 call_amount_list=DEFAULT_AMOUNT, call_strike_list=(),
                 put_amount_list=DEFAULT_AMOUNT, put_strike_list=(),
                 fixing_offset=None, pay_offset=None,
                 origin=None, payoff_model=DEFAULT_PAYOFF_MODEL):
        payoff_list = list()
        cls = OptionStrategyCashflowList.OptionStrategyCashFlowPayOff
        for expiry in payment_date_list:
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            strategy = cls(expiry,
                           call_amount_list, call_strike_list,
                           put_amount_list, put_strike_list)
            payoff_list.append(strategy)
        super().__init__(payment_date_list, payoff_list, origin, payoff_model)


class ContingentRateCashFlowList(ContingentCashFlowList):
    """ list of cashflows by interest rate payments """

    class ContingentRateCashFlowPayOff(object):

        def __init__(self, start, end=None, amount=DEFAULT_AMOUNT,
                     day_count=None, fixing_offset=None, fixed_rate=0.0,
                     cap_strike=None, floor_strike=None):
            self.start = start
            self.end = end
            self.day_count = day_count or default_day_count
            self.fixing_offset = fixing_offset
            self.amount = amount
            self.fixed_rate = fixed_rate
            self.cap_strike = cap_strike
            self.floor_strike = floor_strike

        def __call__(self, model):
            fixing_date = self.start
            if self.fixing_offset:
                fixing_date -= self.fixing_offset

            rate = self.fixed_rate
            if hasattr(model.forward_curve, 'get_cash_rate'):
                rate += model.forward_curve.get_cash_rate(fixing_date)
            else:
                rate += model.forward_curve(fixing_date)
            if self.cap_strike:
                rate -= model.get_call_value(fixing_date, self.cap_strike)
            if self.floor_strike:
                rate += model.get_put_value(fixing_date, self.floor_strike)
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
        cls = ContingentRateCashFlowList.ContingentRateCashFlowPayOff

        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)

        self.day_count = day_count or default_day_count

        payoff_list = list()
        if origin:
            start_dates = [origin]
            start_dates.extend(payment_date_list[:-1])
        elif origin is None and len(payment_date_list) > 1:
            step = payment_date_list[1] - payment_date_list[0]
            start_dates = [payment_date_list[0] - step]
            start_dates.extend(payment_date_list[:-1])
        elif payment_date_list:
            start_dates = payment_date_list

        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            if pay_offset:
                e -= pay_offset
                s -= pay_offset

            payoff = cls(
                start=s, end=e, day_count=day_count,
                fixing_offset=fixing_offset, amount=a, fixed_rate=fixed_rate,
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
