# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from ..plans import DEFAULT_AMOUNT
from .cashflow import CashFlowList as _CashFlowList
from .payoffs import OptionCashFlowPayOff, OptionStrategyCashFlowPayOff, \
    ContingentRateCashFlowPayOff

_DEFAULT_PAYOFF = (lambda *_: 0.)


class ContingentCashFlowList(_CashFlowList):
    """ list of contingent cashflows """
    _cashflow_details = 'cashflow', 'pay date'

    def __init__(self, payment_date_list, payoff_list=None,
                 origin=None, payoff_model=None):
        r"""generic cashflow list of expected contingent cashflows
        i.e. non-deterministc cashflows like option payoffs.

        :param payment_date_list: pay dates, assuming that pay dates
            agree with end dates of interest accrued period
        :param payoff_list: list of payoffs
        :param origin: start date of first interest accrued period
        :param payoff_model: payoff model to derive the expected payoff

        Since expectation depends on probabilities
        an approbiate **payoff_model** $m$
        to estimate expectations has
        to be supplied as argument to the list
        and applied - again as argument - to payoffs.

        Therefor any item $f_i$ in **payoff_list** has to be
        either a **int** pr **float** or callable
        with optional argument of a **payoff_model**
        and will return the expected cashflow amount as float value
        depending on the state given by the **payoff_model**.

        $$f_i(m)=E\big[f_i\mid m\big]$$

        This non-sense use case demonstrates the pattern of evaluating payoffs.
        For more details who to use |ContingentCashFlowList|
        see |OptionCashflowList|, |OptionStrategyCashflowList|
        or |ContingentRateCashFlowList|.

        >>> from dcf import ContingentCashFlowList
        >>> p = lambda x: x*x
        >>> c = ContingentCashFlowList([1,2], [p, p], payoff_model=4)
        >>> c[c.domain]
        [16, 16]
        >>> c.payoff_model = 2
        >>> c[c.domain]
        [4, 4]
        """
        if payoff_list is None:
            payoff_list = [_DEFAULT_PAYOFF]
        self.payoff_model = payoff_model
        super().__init__(payment_date_list, payoff_list, origin=origin)

    def __getitem__(self, item):
        """ getitem does re-calc contingent cashflows """
        if isinstance(item, (tuple, list)):
            return list(self[i] for i in item)
        else:
            payoff = self._flows.get(item, 0.)
            if isinstance(payoff, (int, float)):
                return payoff
            return payoff(self.payoff_model)


class OptionCashflowList(ContingentCashFlowList):
    """ list of option cashflows """
    _cashflow_details = \
        'cashflow', 'pay date', 'put/call', 'long/short', \
        'notional', 'strike', 'expiry date', \
        'fixing date', 'forward', 'volatility', \
        'time to expiry', 'valuation date'

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 strike_list=(), is_put_list=False,
                 fixing_offset=None, pay_offset=None,
                 origin=None, payoff_model=None):
        r""" list of European option payoffs

        :param payment_date_list: list of cashflow payment dates $t_k$
        :param amount_list: list of option notional amounts $N_k$
        :param strike_list: list of option strike prices $K_k$
        :param is_put_list: list of boolean flags indicating
            if options are put options (optional: default is **False**)
        :param fixing_offset: offset $\delta$ between
            underlying fixing date and cashflow end date
        :param pay_offset: offset $\epsilon$ between
            cashflow end date and payment date
        :param origin: origin of object,
            i.e. start date of the cashflow list as a product
        :param payoff_model: payoff model to derive the expected payoff

        List of |OptionCashFlowPayOff()|.

        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)
        if isinstance(strike_list, (int, float)):
            strike_list = [strike_list] * len(payment_date_list)
        if isinstance(is_put_list, (bool, int, float)):
            is_put_list = [is_put_list] * len(payment_date_list)

        payoff_list = list()
        for expiry, amount, strike, is_put in \
                zip(payment_date_list, amount_list, strike_list, is_put_list):
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            option = OptionCashFlowPayOff(
                expiry=expiry,
                amount=amount,
                strike=strike,
                is_put=is_put
            )
            payoff_list.append(option)
        super().__init__(payment_date_list, payoff_list, origin, payoff_model)


class OptionStrategyCashflowList(ContingentCashFlowList):
    """ list of option strategy cashflows """
    _cashflow_details = \
        'cashflow', 'pay date', \
        '#0 put/call', '#0 long/short', '#0 notional', '#0 strike', \
        '#1 put/call', '#1 long/short', '#1 notional', '#1 strike', \
        '#2 put/call', '#2 long/short', '#2 notional', '#2 strike', \
        '#3 put/call', '#3 long/short', '#3 notional', '#3 strike', \
        '#4 put/call', '#4 long/short', '#4 notional', '#4 strike', \
        '#5 put/call', '#5 long/short', '#5 notional', '#5 strike', \
        '#6 put/call', '#6 long/short', '#6 notional', '#6 strike', \
        '#7 put/call', '#7 long/short', '#7 notional', '#7 strike', \
        '#8 put/call', '#8 long/short', '#8 notional', '#8 strike', \
        '#9 put/call', '#9 long/short', '#9 notional', '#9 strike', \
        'expiry date', 'fixing date', \
        'forward', 'volatility', \
        'time to expiry', 'valuation date'

    def __init__(self, payment_date_list,
                 call_amount_list=DEFAULT_AMOUNT, call_strike_list=(),
                 put_amount_list=DEFAULT_AMOUNT, put_strike_list=(),
                 fixing_offset=None, pay_offset=None,
                 origin=None, payoff_model=None):
        r"""series of identical option strategies

        :param payment_date_list: list of cashflow payment dates $t_k$
        :param call_amount_list: list of call option notional amounts $N_{i}$
        :param call_strike_list: list of call option strikes $K_{i}$
        :param put_amount_list: list of put option notional amounts $N_{j}$
        :param put_strike_list: list of put option strikes $L_{j}$
        :param fixing_offset: offset $\delta$ between
            underlying fixing date and cashflow end date
        :param pay_offset: offset $\epsilon$ between
            cashflow end date and payment date
        :param origin: origin of object,
            i.e. start date of the cashflow list as a product
        :param payoff_model: payoff model to derive the expected payoff

        |OptionStrategyCashflowList()| object provides a list of
        |OptionStrategyCashFlowPayOff()| $X_k$ objects
        with payment date $t_k$.

        Adjustetd by offset $X_k$ has expiry date $T_k=t_k-\delta-\epsilon$
        and for all $k$ the same $N_i$, $K_i$, $N_j$, $L_j$ are used.

        """

        if 10 < len(put_strike_list) + len(call_strike_list):
            raise KeyError('OptionStrategyCashflowList are limited '
                           'to 10 options per strategy payoff not '
                           '%d' % len(put_strike_list) + len(call_strike_list))
        payoff_list = list()
        for expiry in payment_date_list:
            if pay_offset:
                expiry -= pay_offset
            if fixing_offset:
                expiry -= fixing_offset
            strategy = OptionStrategyCashFlowPayOff(
                expiry=expiry,
                call_amount_list=call_amount_list,
                call_strike_list=call_strike_list,
                put_amount_list=put_amount_list,
                put_strike_list=put_strike_list
            )
            payoff_list.append(strategy)
        super().__init__(payment_date_list, payoff_list, origin, payoff_model)


class ContingentRateCashFlowList(ContingentCashFlowList):
    """ list of cashflows by interest rate payments """
    _cashflow_details = \
        'cashflow', 'pay date', 'notional', \
        'start date', 'end date', 'year fraction', \
        'fixed rate', 'forward rate', 'fixing date', 'tenor', \
        'floorlet', 'floorlet strike', 'floorlet volatility', \
        'caplet', 'caplet strike', 'caplet volatility', \
        'time to expiry', 'model valuation date'

    def __init__(self, payment_date_list, amount_list=DEFAULT_AMOUNT,
                 origin=None, day_count=None,
                 fixing_offset=None, pay_offset=None,
                 fixed_rate=0., cap_strike=None, floor_strike=None,
                 payoff_model=None):
        r""" list of contingend collared rate cashflows

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
        :param floor_strike: lower interest rate boundary $K$
        :param cap_strike: upper interest rate boundary $L$
        :param payoff_model: option valuation model to derive the
            expected cashflow of option payoffs

        Each object consists of a list of
        |ContingentRateCashFlowPayOff()|, i.e.
        of collared payoff functions

        $$X_i(f(T_i)) = [\max(K, \min(f(T_i), L)) + c]\ \tau(s,e)\ N$$

        with, according to a payment date $p_i$,
        $p_i-\epsilon=e_i$, $e_i=s_{i+1}$ and $s_i-\delta=T_i$.

        """
        if isinstance(amount_list, (int, float)):
            amount_list = [amount_list] * len(payment_date_list)

        if origin:
            start_dates = [origin]
            start_dates.extend(payment_date_list[:-1])
        elif origin is None and len(payment_date_list) > 1:
            step = payment_date_list[1] - payment_date_list[0]
            start_dates = [payment_date_list[0] - step]
            start_dates.extend(payment_date_list[:-1])
        elif payment_date_list:
            start_dates = payment_date_list

        payoff_list = list()
        for s, e, a in zip(start_dates, payment_date_list, amount_list):
            if pay_offset:
                e -= pay_offset
                s -= pay_offset

            payoff = ContingentRateCashFlowPayOff(
                start=s, end=e, day_count=day_count,
                fixing_offset=fixing_offset, amount=a, fixed_rate=fixed_rate,
                cap_strike=cap_strike, floor_strike=floor_strike
            )
            payoff_list.append(payoff)

        super().__init__(payment_date_list, payoff_list,
                         origin=origin, payoff_model=payoff_model)
        self.payoff_model = payoff_model
        """model to derive the expected cashflow of an option payoff"""

    @property
    def fixed_rate(self):
        fixed_rates = tuple(cf.fixed_rate for cf in self._flows.values())
        if len(set(fixed_rates)) == 1:
            return fixed_rates[0]

    @fixed_rate.setter
    def fixed_rate(self, value):
        for cf in self._flows.values():
            cf.fixed_rate = value
