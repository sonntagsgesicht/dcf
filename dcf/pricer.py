# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht
# Version:  0.99, copyright Monday, 31 March 2025
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from functools import partial
from math import exp
from typing import Callable, Iterable, Dict, Any as DateType

from curves.interpolation import piecewise_linear, fit as _fit
from curves.numerics import solve as _solve
from yieldcurves import YieldCurve, DateCurve

from .daycount import (day_count as _default_day_count,
                       year_fraction as _default_year_fraction)
from .payoffs import CashFlowPayOff, RateCashFlowPayOff, CashFlowList


TOL = 1e-10


def ecf(cashflow_list: CashFlowPayOff | CashFlowList,
        valuation_date: DateType,
        *, forward_curve: Callable | float | dict | None = None):
    r"""expected cashflow payoffs

        :param cashflow_list: list of cashflows
        :param valuation_date: date to discount to
        :param forward_curve: payoff model
            (optional; default: **None**, i.e. model attached to **cashflow_list**)
        :return: `dict` of expected cashflow payoffs with **pay_date** keys

        >>> from dcf import ecf, CashFlowList

        >>> cf_list = CashFlowList.from_fixed_cashflows([0., 3.], amount_list=[-100., 100.])
        >>> cf_list += CashFlowList.from_rate_cashflows([0., 1., 2., 3.], amount_list=100., fixed_rate=0.05)
        >>> ecf(cf_list, valuation_date=0.0)
        {0.0: -95.0, 1.0: 5.0, 2.0: 5.0, 3.0: 105.0}

    """   # noqa 501
    if isinstance(cashflow_list, CashFlowPayOff):
        cashflow_list = [cashflow_list]
    if hasattr(forward_curve, 'get'):
        option_curve = forward_curve.get('option_curve', None)
        forward_curve = forward_curve.get('forward_curve', forward_curve)
    else:
        option_curve = None
    kw = {
        'valuation_date': valuation_date,
        'forward_curve': forward_curve,
        'option_curve': option_curve
    }
    r = {}
    for cf in cashflow_list:
        ts = cf.__ts__
        # only for cashflows with remaining payments matter
        if valuation_date <= ts:
            # calc expected payoff cashflow
            # and aggregate multiple cf values with same ts
            r[ts] = r.get(ts, 0.0) + float(cf(**kw) or 0)
    return dict(sorted(r.items()))


def pv(cashflow_list: CashFlowPayOff | CashFlowList,
       valuation_date: DateType | None = None,
       discount_curve: Callable | float = 0.0,
       *, forward_curve: Callable | float | dict | None = None):
    r""" calculates the present value by discounting cashflows

    :param cashflow_list: list of cashflows
    :param valuation_date: date to discount to
    :param discount_curve: discount factors are obtained from this curve
    :param forward_curve: payoff model
        (optional; default: **None**, i.e. model attached to **cashflow_list**)
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

    >>> from yieldcurves import YieldCurve
    >>> from dcf import ecf, pv, CashFlowList

    >>> curve = YieldCurve.from_interpolation([0.0], [0.05])
    >>> cf_list = CashFlowList.from_fixed_cashflows([0, 1, 2, 3], [100, 100, 100, 100])

    >>> sod = pv(cf_list, 0.0, discount_curve=curve)
    >>> sod
    371.677...

    >>> eod = sod - ecf(cf_list, 0.0)[0.0]
    >>> eod
    271.677...

    """  # noqa 501
    ecf_dict = ecf(cashflow_list, valuation_date, forward_curve=forward_curve)
    ecf_items = ((t, float(cf or 0.0)) for t, cf in ecf_dict.items())
    if isinstance(discount_curve, float):
        # use float discount_curve as spot rate for discounting
        r, dc = discount_curve, _default_day_count
        return sum(exp(-dc(valuation_date, t) * r) * cf for t, cf in ecf_items)
    if hasattr(discount_curve, 'discount_factor'):
        # use 'discount_factor' method for discounting
        discount_curve = discount_curve.discount_factor
    elif hasattr(discount_curve, 'df'):
        # use 'df' method for discounting
        discount_curve = discount_curve.df
    df = discount_curve(valuation_date)
    return sum(discount_curve(t) / df * cf for t, cf in ecf_items)


def iac(cashflow_list: CashFlowList,
        valuation_date: DateType,
        *, forward_curve: Callable | float | dict | None = None):
    r""" calculates interest accrued for rate cashflows

        :param cashflow_list: requires a `day_count` property
        :param valuation_date: calculation date
        :param forward_curve: payoff model
            (optional; default: **None**, i.e. model attached to **cashflow_list**)
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

    >>> from dcf import iac, CashFlowList

    setup 5y coupon bond

    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0., fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    bond with cashflow tables

    >>> print(coupon_leg)
      pay date    cashflow    notional  is rec      fixed rate    start date    end date    year fraction
    ----------  ----------  ----------  --------  ------------  ------------  ----------  ---------------
           1.0     1_000.0   1_000_000  True             0.001           0.0         1.0              1.0
           2.0     1_000.0   1_000_000  True             0.001           1.0         2.0              1.0
           3.0     1_000.0   1_000_000  True             0.001           2.0         3.0              1.0
           4.0     1_000.0   1_000_000  True             0.001           3.0         4.0              1.0
           5.0     1_000.0   1_000_000  True             0.001           4.0         5.0              1.0



    >>> print(redemption_leg)
      pay date     cashflow
    ----------  -----------
           5.0  1_000_000.0


    >>> iac(bond, valuation_date=3.25)
    250.0

    >>> iac(bond, valuation_date=3.5)
    500.0

    >>> iac(bond, valuation_date=4.5)
    500.0

    >>> # doesn't take fixed cashflows into account
    >>> iac(redemption_leg, valuation_date=3.25)
    0.0

    """  # noqa 501
    ac = 0.0
    for cf in cashflow_list:
        if isinstance(cf, RateCashFlowPayOff):
            # only interest cash flows entitle to accrued interest
            if cf.start < valuation_date <= cf.end:
                ecf_dict = ecf(cf, valuation_date, forward_curve=forward_curve)
                flow = sum(map(float, ecf_dict.values()))
                day_count = cf.day_count or _default_day_count
                remaining = day_count(valuation_date, cf.end)
                total = day_count(cf.start, cf.end)
                ac += flow * (1. - remaining / total)
    return ac


def ytm(cashflow_list: CashFlowList,
        valuation_date: DateType,
        *, forward_curve: Callable | float | dict | None = None,
        present_value: float = 0.0,
        method: str | Callable = 'secant_method',
        **kwargs):
    r""" yield-to-maturity or effective interest rate

    :param cashflow_list: list of cashflows
    :param valuation_date: date to discount to
        (optional; default: **cashflow_list.origin**)
    :param forward_curve: payoff model
        (optional; default: **None**, i.e. model attached to **cashflow_list**)
    :param present_value: price to meet by discounting
        (optional; default: 0.0)
    :param method: solver method
        If given as string invokes a method from
        `curves.numerics <https://curves.readthedocs.io/en/latest/doc.html#module-curves.numerics.solve>`_  # noqa E501
        otherwise **method** should be a solver impelementing
        :code:`method(err, **kwargs)` return float result and
        where :code:`err` is the error function to be solved.
        **kwargs** provide arguments for **method**.
        (optional: default is **secant_method**
        with lower and upper guess of 0.01 and 0.05 and tolerance of 1e-10)
    :param args: arguments for **method**
    :param kwargs: keyword arguments for **method**
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

    >>> from yieldcurves import YieldCurve
    >>> from dcf import CashFlowList
    >>> from dcf import pv, ytm

    >>> curve = YieldCurve.from_interpolation([0.0], [0.05]).df
    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0.0, fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    bond with cashflow tables

    >>> print(coupon_leg)
      pay date    cashflow    notional  is rec      fixed rate    start date    end date    year fraction
    ----------  ----------  ----------  --------  ------------  ------------  ----------  ---------------
           1.0     1_000.0   1_000_000  True             0.001           0.0         1.0              1.0
           2.0     1_000.0   1_000_000  True             0.001           1.0         2.0              1.0
           3.0     1_000.0   1_000_000  True             0.001           2.0         3.0              1.0
           4.0     1_000.0   1_000_000  True             0.001           3.0         4.0              1.0
           5.0     1_000.0   1_000_000  True             0.001           4.0         5.0              1.0

    >>> print(redemption_leg)
      pay date     cashflow
    ----------  -----------
           5.0  1_000_000.0

    get yield-to-maturity at par (gives coupon rate)

    >>> ytm(bond, 0.0, present_value=n)
    0.0009...

    get current yield-to-maturity as given by 1.5% risk free rate (gives risk free rate)

    >>> present_value = pv(bond, 0.0, curve)
    >>> present_value
    783115.0894...

    >>> ytm(bond, 0.0, present_value=present_value)
    0.049999...

    """  # noqa 501

    # set error function
    def err(x):
        _pv = pv(cashflow_list, valuation_date, x, forward_curve=forward_curve)
        return _pv - present_value

    # run bracketing
    return _solve(err, method, **kwargs)


def fair(cashflow_list: CashFlowList,
         valuation_date: DateType | None = None,
         discount_curve: Callable | float = 0.0,
         *, forward_curve: Callable | float | dict | None = None,
         present_value: float = 0.0,
         method: str | Callable = 'secant_method',
         **kwargs):
    r""" coupon rate to meet given value

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param forward_curve: payoff model
        (optional; default: **None**, i.e. model attached to **cashflow_list**)
    :param present_value: price to meet by discounting
        (optional: default: 0.0)
    :param method: solver method
        If given as string invokes a method from
        `curves.numerics`_
        otherwise **method** should be a solver impolementing
        :code:`method(err, **kwargs)` return float result and
        where :code:`err` is the error function to be solved.
        **kwargs** provide arguments for **method**.
        (optional: default is **secant_method**
        with lower and upper guess of 0.01 and 0.05 and tolerance of 1e-10)
    :param args: arguments for **method**
    :param kwargs: keyword arguments for **method**
    :return: `float` - the fair coupon rate as
        **fixed_rate** of a |RateCashFlowPayOff()|

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

    >>> from yieldcurves import YieldCurve
    >>> from dcf import pv, fair, CashFlowList

    setup 5y coupon bond

    >>> curve = YieldCurve.from_interpolation([0.], [0.015]).df
    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0., fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    find fair rate to give par bond

    >>> present_value = pv(redemption_leg, 0.0, curve)
    >>> fair_rate = fair(coupon_leg, 0.0, curve, present_value=n-present_value)
    >>> fair_rate
    0.0151...

    check it's a par bond (pv=notional)

    >>> for cf in coupon_leg:
    ...     cf.fixed_rate = fair_rate
    >>> pv(bond, 0.0, curve)
    1000000.0...

    """  # noqa 501

    # store fixed rate
    _fixed_rates = [getattr(cf, 'fixed_rate', None) for cf in cashflow_list]

    # set error function
    def err(x):
        for cf in cashflow_list:
            if getattr(cf, 'fixed_rate', None) is not None:
                cf.fixed_rate = x
        _pv = pv(cashflow_list, valuation_date, discount_curve,
                 forward_curve=forward_curve)
        return _pv - present_value

    # run bracketing
    par = _solve(err, method, **kwargs)

    # restore fixed rate
    for cf, _fixed_rate in zip(cashflow_list, _fixed_rates):
        if _fixed_rate is not None:
            cf.fixed_rate = _fixed_rate

    return par


def bpv(cashflow_list: CashFlowList,
        valuation_date: DateType | None = None,
        discount_curve: Callable | float = 0.0,
        *, forward_curve: Callable | float | dict | None = None,
        delta_curve: Callable | Iterable[Callable] | None = None,
        shift: float = 0.0001):
    r""" basis point value (bpv),
    i.e. value change by one interest rate shifted one basis point

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param forward_curve: payoff model
        (optional; default: model attached to **cashflow_list**)
    :param delta_curve: curve (or list of curves) which will be shifted
        (optional; default: **default_curve**)
    :param shift: shift size to derive bpv
        (optional; default: 0.0001)
    :return: `float` - basis point value (bpv)

    Let $v(t, r)$ be the present value of the given **cashflow_list**
    depending on interest rate curve $r$
    which can be used as forward curve to estimate float rates
    or as zero rate curve to derive discount factors (or both).

    Then, with **shift_size** $s$, the bpv is given as

    $$\Delta(t) = 0.0001 \cdot \frac{v(t, r + s) - v(t, r)}{s}$$

    Example
    -------

    >>> from yieldcurves import YieldCurve
    >>> from dcf import pv, bpv, CashFlowList

    setup 5y coupon bond

    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0., fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    together with a flat yield curve

    >>> curve = YieldCurve(0.015)
    >>> pv(bond, 0.0, curve.df)
    932524.5493...

    calculate bpv as bond delta

    >>> yc = YieldCurve(curve)
    >>> bpv(bond, 0.0, yc.df, delta_curve=yc.curve)
    -465.1755...

    double check by direct valuation

    >>> present_value = pv(bond, 0.0, curve.df)
    >>> shifted = YieldCurve(0.015 + 0.0001)
    >>> pv(bond, 0.0, shifted.df) - present_value
    -465.1755...

    """  # noqa 501
    _pv = pv(cashflow_list, valuation_date, discount_curve,
             forward_curve=forward_curve)

    delta_curve = discount_curve if delta_curve is None else delta_curve
    if not isinstance(delta_curve, (list, tuple)):
        delta_curve = delta_curve,

    for d in delta_curve:
        d += shift

    sh = pv(cashflow_list, valuation_date, discount_curve,
            forward_curve=forward_curve)

    for d in delta_curve:
        d -= shift

    return (sh - _pv) / shift * .0001


def delta(cashflow_list: CashFlowList,
          valuation_date: DateType | None = None,
          discount_curve: Callable | float = 0.0,
          *, forward_curve: Callable | float | dict | None = None,
          delta_curve: Callable | Iterable[Callable] | None = None,
          delta_grid: Iterable[DateType] | None = None,
          shift: float = .0001):
    r""" list of bpv delta for partly (bucketed) shifted interest rate curve

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
        (optional; default is **discount_curve.origin**)
    :param forward_curve: payoff model
        (optional; default: model attached to **cashflow_list**)
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

    same example as |bpv()| but with buckets

    >>> from yieldcurves import YieldCurve
    >>> from dcf import pv, bpv, delta, CashFlowList

    setup 5y coupon bond

    >>> curve = YieldCurve.from_interpolation([0.,1.,2.,3.,4.,5.], [0.01, 0.011, 0.014, 0.012, 0.01, 0.013])
    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0., fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    calculate bpv as bond delta

    >>> yc = YieldCurve(curve)
    >>> bucked_bpv = delta(bond, 0.0, yc.df, delta_curve=yc.curve, delta_grid=[0.,1.,2.,3.,4.,5.])
    >>> bucked_bpv
    (0.0, -0.098901..., -0.194458..., -0.289348..., -0.384238..., -468.885034...)

    check by summing up (should give flat bpv)

    >>> sum(bucked_bpv)
    -469.851981...

    >>> bpv(bond, 0.0, yc.df, delta_curve=yc.curve)
    -469.851981...

    """  # noqa 501
    _pv = pv(cashflow_list, valuation_date, discount_curve,
             forward_curve=forward_curve)

    delta_curve = discount_curve if delta_curve is None else delta_curve
    if not isinstance(delta_curve, (list, tuple)):
        delta_curve = delta_curve,

    # todo: delta_grid from discount_curve
    delta_grid = delta_grid if delta_grid else (0., 1., 3., 5., 10., 20.)

    if len(delta_grid) == 1:
        grids = (delta_grid,)
        shifts = ([shift],)
    elif len(delta_grid) == 2:
        grids = (delta_grid, delta_grid)
        shifts = ([shift, 0.], [0., shift])
    else:
        first = [delta_grid[0], delta_grid[1]]
        mids = zip(delta_grid[0: -2], delta_grid[1: -1], delta_grid[2:])
        mids = list(map(list, mids))
        last = [delta_grid[-2], delta_grid[-1]]
        grids = [first] + mids + [last]
        shifts = [[shift, 0.]] + [[0., shift, 0.]] * len(mids) + [[0., shift]]

    buckets = list()
    for g, s in zip(grids, shifts):
        sh = piecewise_linear(g, s)
        for d in delta_curve:
            d += sh
        sh_pv = pv(cashflow_list, valuation_date, discount_curve,
                   forward_curve=forward_curve)
        for d in delta_curve:
            d -= sh
        buckets.append((sh_pv - _pv) / shift * .0001)

    return tuple(buckets)


def fit(cashflow_list: Iterable[CashFlowList],
        valuation_date: DateType | None = None,
        discount_curve: Callable | float = 0.0,
        *, forward_curve: Callable | float | dict | None = None,
        price_list: Iterable[float] | None = None,
        fitting_curve: Callable | None = None,
        fitting_grid: Iterable[float] | None = None,
        interpolation_type: str | Callable | None = None,
        method: str | Callable = 'secant_method',
        **kwargs) -> Dict[float, float]:
    """fit interpolated curve to prices

    :param cashflow_list: list of cashflows instruments,
        i.e. list of lists of cashflows
    :param valuation_date: date to discount to
    :param discount_curve: discount factors are obtained from this curve
    :param forward_curve: payoff model
        (optional; default: **None**, i.e. model attached to **cashflow_list**)
    :param price_list: list of prices to match
        (optional; default assumes all prices to be 0.0)
    :param fitting_curve: curve to fit by inplace adding another curve,
        e.g. see `curves.Curve()`
        (otional; default is a yield curve derived from **discount_curve**)
    :param fitting_grid: list of year fractions (float)
        which define the interpolation grid
        (optional; default: year fraction to last pay date
        of cashflow list in **cashflow_list**. to caluculate year fraction
        either **discount_curve** or |day_count()| is used.)
    :param interpolation_type: function used for interpolation
        (optional; default: **piecewise_linear** as defined
        in `yieldcurves.interpolation` package,
        i.e. constant extrapolation and linear interpolation)
    :param method: root finding method,
        for details see `yieldcurves.tools.numerics`.
        (optional; default: **secant_method**)
    :param bounds: inital or bounday values (depending on **method**)
        for details see `yieldcurves.tools.numerics`.
        (optional; default: (-0.1, 0.2))
    :param tolerance: zero tolerance
        for details see `yieldcurves.tools.numerics`.
        (optional; default: 1e-10)
    :return: dictionary of curve point and value

    |fit()| uses the **fit** function in `yieldcurves.interpolation`.

    Example (with Year Fractions)
    -----------------------------

    >>> from dcf import pv, fit, CashFlowList
    >>> from yieldcurves import YieldCurve, DateCurve

    build cashflow instruments

    >>> today = 0.0
    >>> schedule = [1., 2., 3., 4., 5. ]
    >>> cashflow_list = []
    >>> for d in schedule:
    ...     pay_dates = [s for s in schedule if s <= d]
    ...     cashflow_list.append(CashFlowList.from_fixed_cashflows(pay_dates))

    setup curve to derive target values and generate data for calibration

    >>> curve = YieldCurve.from_interpolation(schedule, [0.01, 0.009, 0.012, 0.014, 0.011])
    >>> targets = [pv(c, 0.0, curve.df) for c in cashflow_list]  # target values to match

    invoke curve fitting

    >>> fit(cashflow_list, today, 1.0, price_list=targets) # doctest: +SKIP
    {1.0: 0.009999999999999995, 2.0: 0.00900000082473929, 3.0: 0.011999999441079148, 4.0: 0.01400000004983385, 5.0: 0.010999999964484619}

    or

    >>> yc = YieldCurve(0.0)  # curve to calibrate to
    >>> rates = fit(cashflow_list, today, yc.df, price_list=targets)  # curve fitting  # doctest: +SKIP
    >>> rates # doctest: +SKIP
    {1.0: 0.009999999999999995, 2.0: 0.00900000082473929, 3.0: 0.011999999441079148, 4.0: 0.01400000004983385, 5.0: 0.010999999964484619}

    setup new curve

    >>> yc2 = YieldCurve.from_interpolation(rates.keys(), rates.values()) # doctest: +SKIP
    >>> yc2 # doctest: +SKIP
    YieldCurve(piecewise_linear([1.0, 2.0, 3.0, 4.0, 5.0], [0.009999999999999995, 0.00900000082473929, 0.011999999441079148, 0.01400000004983385, 0.010999999964484619]))

    double check results

    >>> err = [abs(pv(cf, 0.0, yc2.df) - v) for cf, v in zip(cashflow_list, targets)] # doctest: +SKIP
    >>> max(err) < 1e-7 # doctest: +SKIP
    True

    The above is acctually the same as

    >>> yc = DateCurve(YieldCurve(0.0), origin=0.0)
    >>> grid = [yc.year_fraction(max(cf.domain)) for cf in cashflow_list]
    >>> fit(cashflow_list, today, yc.df, price_list=targets, fitting_curve=yc.curve.curve, fitting_grid=grid) # doctest: +SKIP
    {1.0: 0.009999999999999995, 2.0: 0.00900000082473929, 3.0: 0.011999999441079148, 4.0: 0.01400000004983385, 5.0: 0.010999999964484619}

    Example (with `BusinessDate()`)
    -------------------------------

    >>> from businessdate import BusinessDate, BusinessSchedule

    build cashflow instruments

    >>> today = BusinessDate(20240101)
    >>> schedule = BusinessSchedule(today + '1y', today + '5y', step='1y')
    >>> cashflow_list = []
    >>> for i, d in enumerate(schedule):
    ...     pay_dates = [s for s in schedule if s <= d]
    ...     cashflow_list.append(CashFlowList.from_fixed_cashflows(pay_dates))

    setup curve to derive target values and generate data for calibration

    >>> curve = DateCurve(YieldCurve.from_interpolation(schedule, [0.01, 0.009, 0.012, 0.014, 0.011]), origin=today)
    >>> targets = [pv(c, today, curve.df) for c in cashflow_list]

    invoke curve fitting

    >>> yc = DateCurve(YieldCurve(0.0), origin=today)
    >>> fit(cashflow_list, today, yc.df, price_list=targets) # doctest: +SKIP
    {1.002053388090349: 0.009747946614987986, 2.001368925393566: 0.01249726670743294, 3.0006844626967832: 0.013256157081358156, 4.0: 0.010999999998261295, 5.002053388090349: 0.011000000004102856}

    The above is acctually the same as

    >>> yc = DateCurve(YieldCurve(0.0), origin=today)
    >>> grid = [yc.year_fraction(max(cf.domain)) for cf in cashflow_list]
    >>> fit(cashflow_list, today, yc.df, price_list=targets, fitting_curve=yc.curve.curve, fitting_grid=grid) # doctest: +SKIP
    {1.002053388090349: 0.009747946614987986, 2.001368925393566: 0.01249726670743294, 3.0006844626967832: 0.013256157081358156, 4.0: 0.010999999998261295, 5.002053388090349: 0.011000000004102856}


    """  # noqa E501

    _discount_curve_self = getattr(discount_curve, '__self__', None)
    if fitting_grid is None:
        yf = _default_year_fraction(_discount_curve_self)
        fitting_grid = [yf(max(cf.domain)) for cf in cashflow_list]

    if fitting_curve is None:
        if isinstance(discount_curve, (int, float)):
            if discount_curve - 1:
                raise ValueError(f"constant discount_curve be 1.0 as "
                                 f"a value of {discount_curve} is ambiguous")
            yield_curve = YieldCurve(0.0)
            discount_curve = yield_curve.df
            fitting_curve = yield_curve.curve
        elif isinstance(_discount_curve_self, DateCurve):
            # origin = _default_origin(_discount_curve_self)
            origin = _discount_curve_self.origin
            yield_curve = YieldCurve(_discount_curve_self.curve)
            discount_curve = DateCurve(yield_curve, origin=origin).df
            fitting_curve = yield_curve.curve
        else:
            yield_curve = YieldCurve(YieldCurve.from_df(discount_curve))
            discount_curve = yield_curve.df
            fitting_curve = yield_curve.curve
    kw = {
        'valuation_date': valuation_date,
        'discount_curve': discount_curve,
        'forward_curve': forward_curve
    }
    err_funcs = [partial(pv, cf, **kw) for cf in cashflow_list]

    if price_list is None:
        price_list = [0.0] * len(fitting_grid)
    return _fit(fitting_curve, fitting_grid, err_funcs, price_list,
                interpolation_type=interpolation_type, method=method, **kwargs)
