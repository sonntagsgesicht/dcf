# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .cashflows.cashflow import CashFlowLegList
from .cashflows.payoffs import RateCashFlowPayOff
from .curves.curve import DateCurve
from .curves.interestratecurve import ZeroRateCurve


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


def get_present_value(
        cashflow_list, discount_curve, valuation_date=None):
    r""" calculates the present value by discounting cashflows

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
        (optional; default: **discount_curve.origin**)
    :return: `float` - as the sum of all discounted future cashflows

    Let $cf_1 \dots cf_n$ be the list of cashflows
    with payment dates $t_1, \dots, t_n$.

    Moreover, let $t$ be the valuation date
    and $T=\{t_i \mid t \leq t_i \}$.

    Then the present value is given as

    $$v(t) = \sum_{t_i \in T} df(t, t_i) \cdot cf_i$$

    with $df(t, t_i)$, the discount factor discounting form $t_i$ to $t$.

    Note, **get_present_value** includes cashflows at valuation date.
    Therefor it represents a *start-of-day* valuation
    than a *end-of-day* valuation.

    >>> from dcf import CashFlowList, ZeroRateCurve, get_present_value
    >>> cfs = CashFlowList([0, 1, 2, 3],[100, 100, 100, 100])
    >>> curve = ZeroRateCurve([0], [0.05])
    >>> valuation_date = 0
    >>> sod = get_present_value(cfs, curve, valuation_date)
    >>> sod
    371.67748189617316
    >>> eod = sod - cfs[valuation_date]
    >>> eod
    271.67748189617316

    """
    if valuation_date is None:
        valuation_date = discount_curve.origin

    if isinstance(cashflow_list, CashFlowLegList):
        return sum(get_present_value(
            leg, discount_curve, valuation_date) for leg in cashflow_list.legs)

    # store and set valuation date to payoff_model
    model_valuation_date = valuation_date
    if hasattr(cashflow_list, 'payoff_model'):
        model_valuation_date = cashflow_list.payoff_model.valuation_date
        cashflow_list.payoff_model.valuation_date = valuation_date

    # filter flows
    pay_dates = list(d for d in cashflow_list.domain if valuation_date <= d)

    # discount flows
    value_flows = zip(pay_dates, cashflow_list[pay_dates])
    values = (discount_curve.get_discount_factor(valuation_date, t) * float(a)
              for t, a in value_flows)

    # re-store model_valuation_date
    if hasattr(cashflow_list, 'payoff_model'):
        cashflow_list.payoff_model.valuation_date = model_valuation_date
    return sum(values)


def get_yield_to_maturity(cashflow_list, valuation_date=None, present_value=0.,
                          precision=1e-7, bounds=(-0.1, .2), **kwargs):
    r""" yield-to-maturity or effective interest rate

    :param cashflow_list: list of cashflows
    :param valuation_date: date to discount to
        (optional; default: **cashflow_list.origin**)
    :param present_value: price to meet by discounting
        (optional; default: 0.0)
    :param precision: max distance of present value to par
        (optional: default is 1e-7)
    :param bounds: tuple of lower and upper bound of yield to maturity
        (optional: default is -0.1 and .2)
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

    Example
    -------

    yield-to-matrurity of 5y fixed coupon bond

    >>> from dcf import RateCashFlowList, FixedCashFlowList, CashFlowLegList
    >>> from dcf import get_present_value, get_yield_to_maturity
    >>> from dcf import ZeroRateCurve

    >>> n, df = 1e6, ZeroRateCurve([0], [0.015])
    >>> coupon_leg = RateCashFlowList([1,2,3,4,5], amount_list=n, origin=0, fixed_rate=0.001)
    >>> redemption_leg = FixedCashFlowList([5], amount_list=n)
    >>> bond = CashFlowLegList((redemption_leg, coupon_leg))

    bond with cashflow tables

    >>> print(tabulate(coupon_leg.table, headers='firstrow'))
      cashflow    pay date    notional    start date    end date    year fraction    fixed rate
    ----------  ----------  ----------  ------------  ----------  ---------------  ------------
          1000           1       1e+06             0           1                1         0.001
          1000           2       1e+06             1           2                1         0.001
          1000           3       1e+06             2           3                1         0.001
          1000           4       1e+06             3           4                1         0.001
          1000           5       1e+06             4           5                1         0.001

    >>> print(tabulate(redemption_leg.table, headers='firstrow'))
      cashflow    pay date
    ----------  ----------
         1e+06           5

    get yield-to-maturity at par (gives coupon rate)

    >>> ytm = get_yield_to_maturity(bond, valuation_date=0, present_value=n)
    >>> round(ytm, 6)
    0.001

    get current yield-to-maturity as given by 1.5% risk free rate (gives risk free rate)

    >>> pv = get_present_value(bond, df, valuation_date=0)
    >>> pv
    932524.5493034503
    >>>
    >>> ytm = get_yield_to_maturity(bond, valuation_date=0, present_value=pv)
    >>> round(ytm, 6)
    0.015

    """  # noqa 501
    if valuation_date is None:
        valuation_date = cashflow_list.origin

    discount_curve = ZeroRateCurve([valuation_date], [0.0], **kwargs)

    # set error function
    def err(current):
        discount_curve[valuation_date] = current
        pv = get_present_value(cashflow_list, discount_curve, valuation_date)
        return pv - present_value

    # run bracketing
    _, ytm, _ = _simple_bracketing(err, *bounds, precision)
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

    Note, this function takes even expected payoffs of options
    incl. caplets and floorlets into account
    which probably should be excluded.

    Example
    -------

    >>> from dcf import RateCashFlowList, FixedCashFlowList, CashFlowLegList
    >>> from dcf import get_interest_accrued

    setup 5y coupon bond

    >>> n = 1e6
    >>> coupon_leg = RateCashFlowList([1,2,3,4,5], amount_list=n, origin=0, fixed_rate=0.001)
    >>> redemption_leg = FixedCashFlowList([5], amount_list=n)
    >>> bond = CashFlowLegList((redemption_leg, coupon_leg))

    bond with cashflow tables

    >>> print(tabulate(coupon_leg.table, headers='firstrow'))
      cashflow    pay date    notional    start date    end date    year fraction    fixed rate
    ----------  ----------  ----------  ------------  ----------  ---------------  ------------
          1000           1       1e+06             0           1                1         0.001
          1000           2       1e+06             1           2                1         0.001
          1000           3       1e+06             2           3                1         0.001
          1000           4       1e+06             3           4                1         0.001
          1000           5       1e+06             4           5                1         0.001

    >>> print(tabulate(redemption_leg.table, headers='firstrow'))
      cashflow    pay date
    ----------  ----------
         1e+06           5

    calculate accrued interest

    >>> get_interest_accrued(bond, valuation_date=3.25)
    250.0

    >>> get_interest_accrued(bond, valuation_date=3.5)
    500.0

    >>> # doesn't take fixed cashflows into account
    >>> get_interest_accrued(bond, valuation_date=4.5)
    500.0

    """  # noqa 501
    if isinstance(cashflow_list, CashFlowLegList):
        return sum(get_interest_accrued(leg, valuation_date)
                   for leg in cashflow_list.legs)
    # only interest cash flows entitle to accrued interest
    ac = 0.0
    for pay_date in cashflow_list.domain:
        if valuation_date <= pay_date:
            cf = cashflow_list.payoff(pay_date)
            if isinstance(cf, RateCashFlowPayOff):
                if cf.start < valuation_date:
                    remaining = cf.day_count(valuation_date, cf.end)
                    total = cf.day_count(cf.start, cf.end)
                    flow = cf(cashflow_list.forward_curve)
                    ac += flow * (1. - remaining / total)
    return ac


def get_fair_rate(cashflow_list, discount_curve,
                  valuation_date=None, present_value=0.,
                  precision=1e-7, bounds=(-0.1, .2)):
    r""" coupon rate to meet given value

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param present_value: price to meet by discounting
    :param precision: max distance of present value to par
        (optional: default is 1e-7)
    :param bounds: tuple of lower and upper bound of fair rate
        (optional: default is -0.1 and .2)
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

    Example
    -------

    >>> from dcf import RateCashFlowList, FixedCashFlowList, CashFlowLegList
    >>> from dcf import get_present_value, get_fair_rate
    >>> from dcf import ZeroRateCurve

    setup 5y coupon bond

    >>> n, df = 1e6, ZeroRateCurve([0], [0.015])
    >>> coupon_leg = RateCashFlowList([1,2,3,4,5], amount_list=n, origin=0, fixed_rate=0.001)
    >>> redemption_leg = FixedCashFlowList([5], amount_list=n)
    >>> bond = CashFlowLegList((redemption_leg, coupon_leg))

    find fair rate to give par bond

    >>> pv = get_present_value(redemption_leg, df)
    >>> fair_rate = get_fair_rate(coupon_leg, df, present_value=n-pv)
    >>> fair_rate
    0.015113064615715653

    check it's a par bond (pv=notional)

    >>> coupon_leg.fixed_rate = fair_rate
    >>> pv = get_present_value(bond, df)
    >>> round(pv, 6)
    1000000.0

    """  # noqa 501
    # store fixed rate
    fixed_rate = cashflow_list.fixed_rate

    # set error function
    def err(current):
        cashflow_list.fixed_rate = current
        pv = get_present_value(cashflow_list, discount_curve, valuation_date)
        return pv - present_value

    # run bracketing
    _, par, _ = _simple_bracketing(err, *bounds, precision)

    # restore fixed rate
    cashflow_list.fixed_rate = fixed_rate
    return par


def get_basis_point_value(cashflow_list, discount_curve, valuation_date=None,
                          delta_curve=None, shift=.0001):
    r""" basis point value (bpv),
    i.e. value change by one interest rate shifted one basis point

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param delta_curve: curve (or list of curves) which will be shifted
    :param shift: shift size to derive bpv
    :return: `float` - basis point value (bpv)

    Let $v(t, r)$ be the present value of the given **cashflow_list**
    depending on interest rate curve $r$
    which can be used as forward curve to estimate float rates
    or as zero rate curve to derive discount factors (or both).

    Then, with **shift_size** $s$, the bpv is given as

    $$\Delta(t) = 0.0001 \cdot \frac{v(t, r + s) - v(t, r)}{s}$$

    Example
    -------

    >>> from dcf import RateCashFlowList, FixedCashFlowList, CashFlowLegList
    >>> from dcf import get_present_value, get_basis_point_value
    >>> from dcf import ZeroRateCurve

    setup 5y coupon bond

    >>> n, df = 1e6, ZeroRateCurve([0], [0.015])
    >>> coupon_leg = RateCashFlowList([1,2,3,4,5], amount_list=n, origin=0, fixed_rate=0.001)
    >>> redemption_leg = FixedCashFlowList([5], amount_list=n)
    >>> bond = CashFlowLegList((redemption_leg, coupon_leg))

    calculate bpv as bond delta

    >>> bpv = get_basis_point_value(bond, df)
    >>> bpv
    -465.1755130274687

    check by direct valuation

    >>> pv = get_present_value(bond, df)
    >>> df[0] += 0.0001
    >>> shifted = get_present_value(bond, df)
    >>> shifted-pv
    -465.1755130274687

    """  # noqa 501
    pv = get_present_value(cashflow_list, discount_curve, valuation_date)
    delta_curve = discount_curve if delta_curve is None else delta_curve

    if not isinstance(delta_curve, (list, tuple)):
        delta_curve = delta_curve,

    for d in delta_curve:
        d.spread = DateCurve([d.origin], [shift])
    sh = get_present_value(cashflow_list, discount_curve, valuation_date)
    for d in delta_curve:
        d.spread = None

    return (sh - pv) / shift * .0001


def get_bucketed_delta(cashflow_list, discount_curve, valuation_date=None,
                       delta_curve=None, delta_grid=None, shift=.0001):
    r""" list of bpv delta for partly shifted interest rate curve

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
        (optional; default is **discount_curve.origin**)
    :param delta_curve: curve (or list of curves) which will be shifted
        (optional; default is **discount_curve**)
    :param delta_grid: grid dates to build partly shifts
        (optional; default is **delta_curve.domain**)
    :param shift: shift size to derive bpv
        (optional: default is a basis point i.e. `0.0001`)
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

    Example
    -------

    same example as |get_basis_point_value()| but with buckets

    >>> from dcf import RateCashFlowList, FixedCashFlowList, CashFlowLegList
    >>> from dcf import get_present_value, get_bucketed_delta, get_basis_point_value
    >>> from dcf import ZeroRateCurve

    setup 5y coupon bond

    >>> n, df = 1e6, ZeroRateCurve([0,1,2,3,4,5], [0.01, 0.011, 0.014, 0.012, 0.01, 0.013])
    >>> coupon_leg = RateCashFlowList([1,2,3,4,5], amount_list=n, origin=0, fixed_rate=0.001)
    >>> redemption_leg = FixedCashFlowList([5], amount_list=n)
    >>> bond = CashFlowLegList((redemption_leg, coupon_leg))

    calculate bpv as bond delta

    >>> bpv = get_bucketed_delta(bond, df)
    >>> bpv
    (0.0, -0.09890108276158571, -0.19445822690613568, -0.2893486835528165, -0.38423892273567617, -468.88503439340275)

    check by summing up (should give flat bpv)

    >>> sum(bpv)
    -469.85198130935896
    >>> get_basis_point_value(bond, df)
    -469.85198130935896

    """  # noqa 501

    pv = get_present_value(cashflow_list, discount_curve, valuation_date)
    delta_curve = discount_curve if delta_curve is None else delta_curve
    delta_grid = delta_grid if delta_grid else discount_curve.domain

    if len(delta_grid) == 1:
        grids = (delta_grid,)
        shifts = ([shift],)
    elif len(delta_grid) == 2:
        grids = (delta_grid, delta_grid)
        shifts = ([shift, 0.], [0., shift])
    else:
        first = [delta_grid[0], delta_grid[1]]
        mids = list(map(
            list, zip(delta_grid[0: -2], delta_grid[1: -1], delta_grid[2:])))
        last = [delta_grid[-2], delta_grid[-1]]
        grids = [first] + mids + [last]
        shifts = [[shift, 0.]] + [[0., shift, 0.]] * len(mids) + [[0., shift]]

    if not isinstance(delta_curve, (list, tuple)):
        delta_curve = delta_curve,

    buckets = list()
    for g, s in zip(grids, shifts):
        for d in delta_curve:
            d.spread = DateCurve(g, s)
        sh = get_present_value(cashflow_list, discount_curve, valuation_date)
        for d in delta_curve:
            d.spread = None

        buckets.append((sh - pv) / shift * .0001)
    return tuple(buckets)


def get_curve_fit(cashflow_list, discount_curve, valuation_date=None,
                  fitting_curve=None, fitting_grid=None, present_value=0.0,
                  precision=1e-7, bounds=(-0.1, .2)):
    r"""fit curve to cashflow_list prices (bootstrapping)

    :param cashflow_list: list (!) of cashflow_list. products to match prices
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param fitting_curve: curve to fit to match prices
        (optional; default is **discount_curve**)
    :param fitting_grid: domain to fit prices to
        (optional; default **fitting_curve.domain**)
    :param present_value: list (!) of prices of products in **cashflow_list**,
        each one to be met by discounting
        (optional; default is list of 0.0)
    :param precision: max distance of present value to par
        (optional; default is 1e-7)
    :param bounds: tuple of lower and upper bound of fair rate
        (optional; default is -0.1 and .2)
    :return: tuple(float) **fitting_data** as curve values to build curve
        together with curve points from **fitting_grid**

    Bootstrapping is a sequential approach to set curve values $y_i$
    in order to match present values of cashflow products $X_j$
    to given prices $p_j$.

    This is done sequentially, i.e. for a
    consecutive sequence of curve points $t_i$, $i=1 \dots n$.

    Starting at $i=1$ at curve point $t_1$ the value $y_1$
    is varied by
    `simple bracketing <https://en.wikipedia.org/wiki/Nested_intervals>`_
    such that the present value
    $$v_0(X_j) = p_j \text{ for $X_j$ maturing before or at $t_j$.}$$

    Here, the **fitting_curve** can be the discount curve
    but also any forward curve or even a volatility curve.

    Once $y_1$ is found the next dated $t_2$ in **fitting_grid** is handled.
    This is kept going on until all prices $p_j$ and all points $t_i$ match.

    Note, in order to conclude successfully,
    the valuations $v_0(X_j)$ must be sensitive
    to changes of curve value $y_i$, i.e. at least one $j$ must hold
    $$\frac{d}{dy_i}v_0(X_j) \neq 0$$
    with in the bracketing bounds of $y_i$ as set by **bounds**.

    Example
    -------

    Yield curve calibration.

    First, setup dates and schedule

    >>> from businessdate import BusinessDate, BusinessSchedule
    >>> today = BusinessDate(20161231)
    >>> schedule = BusinessSchedule(today + '1y', today + '5y', '1y')

    of products

    >>> from dcf import RateCashFlowList, get_present_value
    >>> cashflow_list = [RateCashFlowList([s for s in schedule if s <= d], 1e6, origin=today, fixed_rate=0.01) for d in schedule]

    and prices to match to.

    >>> from dcf import ZeroRateCurve
    >>> rates = [0.01, 0.009, 0.012, 0.014, 0.011]
    >>> curve = ZeroRateCurve(schedule, rates)
    >>> present_value = [get_present_value(cfs, curve, today) for cfs in cashflow_list]

    Then fit a plain curve

    >>> from dcf import get_curve_fit
    >>> target = ZeroRateCurve(schedule, [0.01, 0.01, 0.01, 0.01, 0.01])
    >>> data = get_curve_fit(cashflow_list, target, today, fitting_curve=target, present_value=present_value)
    >>> [round(d, 6) for d in data]
    [0.01, 0.009, 0.012, 0.014, 0.011]

    Example
    -------

    Option implied volatility calibration.

    First, setup dates and schedule

    >>> from businessdate import BusinessDate, BusinessSchedule
    >>> today = BusinessDate(20161231)
    >>> expiry = today + '3m'

    curves

    >>> from dcf import ZeroRateCurve, ForwardCurve, TerminalVolatilityCurve
    >>> c = ZeroRateCurve([today], [0.05])   # risk free rate of 5%
    >>> f = ForwardCurve([today], [100.0], yield_curve=c)  # spot price 100 and yield of 5%
    >>> v = TerminalVolatilityCurve([today], [0.1])  # flat volatility of 10%

    and model with parameters

    >>> from dcf.models import LogNormalOptionPayOffModel
    >>> m = LogNormalOptionPayOffModel(valuation_date=today, forward_curve=f, volatility_curve=v)

    of call option products

    >>> from dcf import OptionCashflowList, get_present_value
    >>> cashflow_list = OptionCashflowList([expiry], strike_list=110., origin=today, payoff_model=m)
    >>> cashflow_list[expiry]
    0.1025451675720177
    >>> get_present_value(cashflow_list, curve, today)
    0.1022928005931384

    and fit volatility by

    >>> from dcf import get_curve_fit
    >>> pv = 0.25
    >>> data = get_curve_fit([cashflow_list], curve, today, fitting_curve=v, fitting_grid=[expiry], present_value=[pv])
    >>> data
    (0.12207840979099276,)

    check result

    >>> v[expiry] = data[0]
    >>> pv = get_present_value(cashflow_list, curve, today)
    >>> round(pv, 6)
    0.25

    """  # noqa 501
    if isinstance(present_value, (int, float)):
        present_value = [present_value] * len(cashflow_list)

    fitting_curve = discount_curve if fitting_curve is None else fitting_curve
    fitting_grid = \
        fitting_curve.domain if fitting_grid is None else fitting_grid

    # copy fitting_curve but set al values to 0.0
    fitting_curve.spread = fitting_curve.__class__(fitting_grid, fitting_curve)
    for d in fitting_curve.spread.domain:
        fitting_curve.spread[d] = 0.0

    pp_list = tuple(zip(cashflow_list, present_value))
    for d in fitting_curve.spread.domain:
        # prepare products and prices
        # todo: better use sensitivity to current curve point than maturity
        filtered_pp_list = list(p for p in pp_list if max(p[0].domain) <= d)

        # set error function
        def err(current):
            fitting_curve.spread[d] = current
            pvs = list()
            for cf, pv in filtered_pp_list:
                p = get_present_value(cf, discount_curve, valuation_date)
                pvs.append(p - pv)
            return sum(pvs)

        # run bracketing
        _simple_bracketing(err, *bounds, precision)

    data = fitting_curve(fitting_curve.spread.domain)
    fitting_curve.spread = None
    return data
