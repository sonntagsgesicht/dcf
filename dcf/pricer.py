# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.6.1, copyright Tuesday, 11 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .interestratecurve import ZeroRateCurve, CashRateCurve
from .cashflow import CashFlowLegList


def _simple_bracketing(func, a, b, precision=1e-13):
    """ find root by _simple_bracketing an interval

    :param callable func: function to find root
    :param float a: lower interval boundary
    :param float b: upper interval boundary
    :param float precision: max accepted error
    :rtype: tuple
    :return: :code:`(a, m, b)` of last recursion step
        with :code:`m = a + (b-a) *.5`

    """
    fa, fb = func(a), func(b)
    if fb < fa:
        f = (lambda x: -func(x))
        fa, fb = fb, fa
    else:
        f = func

    if not fa <= 0. <= fb:
        msg = "_simple_bracketing function must be loc monotone " \
              "between %0.4f and %0.4f \n" % (a, b)
        msg += "and _simple_bracketing 0. between  %0.4f and %0.4f." % (fa, fb)
        raise AssertionError(msg)

    m = a + (b - a) * 0.5
    if abs(b - a) < precision and abs(fb - fa) < precision:
        return a, m, b

    a, b = (m, b) if f(m) < 0 else (a, m)
    return _simple_bracketing(f, a, b, precision)


def get_present_value(cashflow_list, discount_curve,
                      valuation_date=None, include_value_date=True):
    r""" calculates the present value by discounting cashflows

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param include_value_date: (bool) to decide if cashflows
        at **valuation_date** are included,
        (optional with default *True*)
    :return: `float` - as the sum of all discounted future cashflows

    Let $cf_1 \dots cf_n$ be the list of cashflows
    with payment dates $t_1, \dots, t_n$.

    Moreover, let $t$ be the valuation date
    and $T=\{t_i \mid t \leq t_i \}$ if **include_value_date** is *True*
    else $T=\{t_i \mid t < t_i \}$.

    Then the present value is given as

    $$v(t) = \sum_{t_i \in T} df(t, t_i) \cdot cf_i$$

    with $df(t, t_i)$, the discount factor discounting form $t_i$ to $t$.

    """
    if valuation_date is None:
        valuation_date = cashflow_list.origin

    # filter flows
    if include_value_date:
        pay_dates = \
            list(d for d in cashflow_list.domain if valuation_date <= d)
    else:
        pay_dates = list(d for d in cashflow_list.domain if valuation_date < d)

    # discount flows
    value_flows = zip(pay_dates, cashflow_list[pay_dates])
    values = (discount_curve.get_discount_factor(valuation_date, t) * a
              for t, a in value_flows)
    return sum(values)


def get_yield_to_maturity(cashflow_list,
                          valuation_date=None, present_value=0., **kwargs):
    r""" yield-to-maturity or effective interest rate

    :param cashflow_list: list of cashflows
    :param valuation_date: date to discount to
    :param present_value: price to meet by discounting
    :param kwargs: additional keyword used for constructing |ZeroRateCurve()|
    :return: `float` - as flat interest rate to discount all future cashflows
        in order to meet given **present_value**

    Let $cf_1 \dots cf_n$ be the list of cashflows
    with payment dates $t_1, \dots, t_n$.

    Moreover, let $t$ be the valuation date
    and $T=\{t_i \mid t \leq t_i \}$.

    Then the yield-to-maturity is the interest rate $y$ such that
    the **present_value** $\hat{v}$ is given as

    $$\hat{v} = \sum_{t_i \in T} df(t, t_i) \cdot cf_i$$

    with $df(t, t_i) = \exp(-y \cdot (t_i-t))$,
    the discount factor discounting form $t_i$ to $t$.

    """
    if valuation_date is None:
        valuation_date = cashflow_list.origin

    # set error function
    def err(current):
        discount_curve = ZeroRateCurve([valuation_date], [current], **kwargs)
        pv = get_present_value(cashflow_list, discount_curve, valuation_date)
        return pv - present_value

    # run bracketing
    _, ytm, _ = _simple_bracketing(err, -0.1, .2, 1e-2)
    return ytm


def get_interest_accrued(cashflow_list, valuation_date):
    r""" calculates interest accrued for rate cashflows

    :param cashflow_list: requires a `day_count` property
    :param valuation_date: calculation date
    :return: `float` - proportion of interest in current interest period

    Let $t$ be the valuation date
    and $s, e$ start resp. end date of current rate period,
    i.e. $s \leq t < e$.

    Let $\tau$ be the day count function to calculate year fractions.

    Finally, let $cf$ be the next interest rate cashflow.

    The accrued interest until $t$ is given as
    $$cf_{accrued} =  cf \cdot \frac{\tau(s, t)}{\tau(s, e)}.$$

    """
    if cashflow_list.origin < valuation_date < cashflow_list.domain[-1]:
        if isinstance(cashflow_list, CashFlowLegList):
            return sum(get_interest_accrued(leg, valuation_date)
                       for leg in cashflow_list.legs)
        # only interest cash flows entitle to accrued interest
        if hasattr(cashflow_list, 'day_count'):
            last = max((d for d in cashflow_list.domain if valuation_date > d),
                       default=cashflow_list.origin)
            next = list(d for d in cashflow_list.domain
                        if valuation_date <= d)[0]

            # use start and end rather than pay dates
            if cashflow_list.pay_offset:
                if not last == cashflow_list.origin:
                    last -= cashflow_list.pay_offset
                next -= cashflow_list.pay_offset

            # calculate remaining rate period proportion
            remaining = cashflow_list.day_count(valuation_date, next)
            total = cashflow_list.day_count(last, next)
            return cashflow_list[next] * (1. - remaining / total)
    return 0.


def get_fair_rate(cashflow_list, discount_curve,
                  valuation_date=None, present_value=0., precision=1e-7):
    r""" coupon rate to meet given value

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param present_value: price to meet by discounting
    :param precision: max distance of present value to par
    :return: `float` - the fair coupon rate as
        **fixed_rate** of a |RateCashFlowList()|

    Let $cf_i(c) = N_i \cdot \tau(s_i,e_i) \cdot (c + f(d_i))$
    be the $i$-th cashflow in the **cashflow_list**.

    Here, the fair rate is the fixed_rate $c=\hat{c}$ such that
    the **present_value** $\hat{v}$ is given as

    $$\hat{v} = \sum_{t_i \in T} df(t, t_i) \cdot cf_i(\hat{c})$$

    with $df(t, t_i)$, the discount factor discounting form $t_i$ to $t$.

    Note, **get_fair_rate** requires the **cashflow_list**
    to have an attribute **fixed_rate**
    which is perturbed to find the solution for $\hat{c}$.

    """
    if valuation_date is None:
        valuation_date = cashflow_list.origin

    # todo: cashflow_list.payoff.fixed_rate
    fixed_rate = cashflow_list.fixed_rate

    # set error function
    def err(current):
        cashflow_list.fixed_rate = current
        pv = get_present_value(cashflow_list, discount_curve, valuation_date)
        return pv - present_value

    # run bracketing
    _, par, _ = _simple_bracketing(err, -0.1, .2, precision)

    # restore fixed rate
    cashflow_list.fixed_rate = fixed_rate
    return par


def get_par_rate(cashflow_list, discount_curve,
                 valuation_date=None, present_value=0., precision=1e-7):
    """ same as |get_fair_rate()| """
    return get_fair_rate(cashflow_list, discount_curve, valuation_date,
                         present_value, precision)


def get_basis_point_value(cashflow_list, discount_curve, valuation_date=None,
                          delta_curve=None, shift=.0001):
    r""" basis point value (bpv),
    i.e. value change by one interest rate shifted one basis point

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param delta_curve: curve which will be shifted
    :param shift: shift size to derive bpv
    :return: `float` - basis point value (bpv)

    Let $v(t, r)$ be the present value of the given **cashflow_list**
    depending on interest rate curve $r$
    which can be used as forward curve to estimate float rates
    or as zero rate curve to derive discount factors (or both).

    Then, with **shift_size** $s$, the bpv is given as

    $$\Delta(t) = 0.0001 \cdot \frac{v(t, r + s) - v(t, r)}{s}$$

    """
    if isinstance(cashflow_list, CashFlowLegList):
        return sum(get_basis_point_value(
            leg, discount_curve, valuation_date, delta_curve, shift)
                   for leg in cashflow_list.legs)
    buckets = get_bucketed_delta(cashflow_list, discount_curve, valuation_date,
                                 delta_curve, None, shift)
    return sum(buckets)


def get_bucketed_delta(cashflow_list, discount_curve, valuation_date=None,
                       delta_curve=None, delta_grid=None,
                       shift=.0001):
    r""" list of bpv delta for partly shifted interest rate curve

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param delta_curve: curve which will be shifted
    :param delta_grid: grid dates to build partly shifts
    :param shift: shift size to derive bpv
    :return: `list(float)` - basis point value for each **delta_grid** point

    Let $v(t, r)$ be the present value of the given **cashflow_list**
    depending on interest rate curve $r$
    which can be used as forward curve to estimate float rates
    or as zero rate curve to derive discount factors (or both).

    Then, with **shift_size** $s$ and shifting $s_j$,

    $$\Delta_j(t) = 0.0001 \cdot \frac{v(t, r + s_j) - v(t, r)}{s}$$

    and the full bucketed delta vector is
    $\big(\Delta_1(t), \Delta_2(t), \dots, \Delta_{m-1}(t) \Delta_m(t)\big)$.

    Overall the shifting $s_1, \dots s_n$ is a partition of the unity,
    i.e. $\sum_{j=1}^m s_j = s$.

    Each $s_j$ for $i=2, \dots, m-1$ is a function of the form of an triangle,
    i.e. for a **delta_grid** $t_1, \dots, t_m$

    .. math::
        :nowrap:

        \[
        s_j(t) =
        \left\{
        \begin{array}{cl}
            0 & \text{ for } t < t_{j-1} \\
            s \cdot \frac{t-t_{j-1}}{t_j-t_{j-1}}
                & \text{ for } t_{j-1} \leq t < t_j \\
            s \cdot \frac{t_{j+1}-t}{t_{j+1}-t_j}
                & \text{ for } t_j \leq t < t_{j+1} \\
            0 & \text{ for } t_{j+1} \leq t \\
        \end{array}
        \right.
        \]

    while

    .. math::
        :nowrap:

        \[
        s_1(t) =
        \left\{
        \begin{array}{cl}
            s & \text{ for } t < t_1 \\
            s \cdot \frac{t_2-t}{t_2-t_1} & \text{ for } t_1 \leq t < t_2 \\
            0 & \text{ for } t_2 \leq t \\
        \end{array}
        \right.
        \]

    and

    .. math::
        :nowrap:

        \[
        s_m(t) =
        \left\{
        \begin{array}{cl}
            0 & \text{ for } t < t_{m-1} \\
            s \cdot \frac{t-t_{m-1}}{t_m-t_{m-1}}
                & \text{ for } t_{m-1} \leq t < t_m \\
            s & \text{ for } t_m \leq t \\
        \end{array}
        \right.
        \]

    """
    if isinstance(cashflow_list, CashFlowLegList):
        buckets = tuple(get_bucketed_delta(
            leg, discount_curve, valuation_date, delta_curve, delta_grid, shift
        ) for leg in cashflow_list.legs)
        buckets = tuple(map(tuple, zip(*buckets)))
        return tuple(sum(b) for b in buckets)

    pv = get_present_value(cashflow_list, discount_curve, valuation_date)
    delta_curve = discount_curve if delta_curve is None else delta_curve

    # check if curve is CashRateCurve
    basis_point_curve_type = CashRateCurve \
        if isinstance(delta_curve, CashRateCurve) else ZeroRateCurve

    if delta_grid:
        if len(delta_grid) == 1:
            grid = (delta_grid,)
            shifts = ([shift],)
        elif len(delta_grid) == 2:
            grid = (delta_grid, delta_grid)
            shifts = ([shift, 0.], [0., shift])
        else:
            first = [delta_grid[0], delta_grid[1]]
            mids = list(map(list, zip(
                delta_grid[0: -2], delta_grid[1: -1], delta_grid[2:])))
            last = [delta_grid[-2], delta_grid[-1]]

            grid = [first] + mids + [last]
            shifts = [[shift, 0.]] + \
                     [[0., shift, 0.]] * len(mids) + [[0., shift]]
    else:
        grid = ([delta_curve.origin],)
        shifts = ([shift],)

    buckets = list()
    for g, s in zip(grid, shifts):
        shifted_curve = delta_curve + basis_point_curve_type(
            g, s, forward_tenor=delta_curve.forward_tenor)
        # todo: cashflow_list.payoff_model.forward_curve
        fwd_curve = getattr(cashflow_list, 'forward_curve', None)
        if fwd_curve == delta_curve:
            # replace delta_curve by shifted_curve
            cashflow_list.forward_curve = shifted_curve
        if delta_curve == discount_curve:
            sh = get_present_value(cashflow_list, shifted_curve,
                                   valuation_date)
        else:
            sh = get_present_value(cashflow_list, discount_curve,
                                   valuation_date)

        if fwd_curve == delta_curve:
            # restore delta_curve by shifted_curve
            cashflow_list.forward_curve = delta_curve

        buckets.append((sh - pv) / shift * .0001)
    return buckets
