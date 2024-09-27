# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from functools import partial
from math import exp
from typing import Callable, Tuple, Iterable, Dict, Any as DateType

from .cashflowlist import CashFlowList
from .payoffs import CashFlowPayOff, RateCashFlowPayOff
from .payoffmodels import PayOffModel

from .tools.dc import day_count as _default_day_count
from .tools.nx import simple_bracketing
from .tools.pl import piecewise_linear


def ecf(cashflow_list: CashFlowPayOff | CashFlowList,
        valuation_date: DateType,
        payoff_model: PayOffModel | None = None):
    r"""expected cashflow payoffs

        :param cashflow_list: list of cashflows
        :param valuation_date: date to discount to
        :param payoff_model: payoff model
            (optional; default: **None**, i.e. model attached to **cashflow_list**)
        :return: `dict` of expected cashflow payoffs with **pay_date** keys
        
        >>> from dcf import ecf, CashFlowList
        
        >>> cf_list = CashFlowList.from_fixed_cashflows([0., 3.], amount_list=[-100., 100.])
        >>> cf_list += CashFlowList.from_rate_cashflows([0., 1., 2., 3.], amount_list=100., fixed_rate=0.05)
        >>> ecf(cf_list, valuation_date=0.0)
        {0.0: -95.0, 1.0: 5.0, 2.0: 5.0, 3.0: 105.0}
        
    """   # noqa 501
    payoff_model = payoff_model or PayOffModel(lambda *_: 0.0)
    if isinstance(cashflow_list, CashFlowPayOff):
        cashflow_list = CashFlowList([cashflow_list])
    details_list = payoff_model(cashflow_list[valuation_date:], valuation_date)
    r = {}
    for d in details_list:
        r[d.__ts__] = r.get(d.__ts__, 0.0) + float(d)
    return dict(sorted(r.items()))


def pv(cashflow_list: CashFlowPayOff | CashFlowList,
       discount_curve: Callable | float,
       valuation_date: DateType,
       payoff_model: PayOffModel | None = None):
    r""" calculates the present value by discounting cashflows

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param payoff_model: payoff model
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

    >>> curve = YieldCurve.from_interpolation([0.0], [0.05]).df
    >>> cf_list = CashFlowList.from_fixed_cashflows([0, 1, 2, 3], [100, 100, 100, 100])

    >>> sod = pv(cf_list, curve, valuation_date=0.0)
    >>> sod  
    371.677...

    >>> eod = sod - ecf(cf_list, 0.0)[0.0]
    >>> eod  
    271.677...

    """  # noqa 501
    ecf_dict = ecf(cashflow_list, valuation_date, payoff_model)
    df, vd = discount_curve, valuation_date
    if isinstance(discount_curve, float):
        # todo: review discount_curve as float
        df = lambda s, t: exp(-float(t - s) * discount_curve)
    return sum(df(vd, t) * float(cf) for t, cf in ecf_dict.items())


def ytm(cashflow_list: CashFlowList,
        valuation_date: DateType,
        present_value: float = 0.0,
        payoff_model: PayOffModel | None = None,
        precision: float = 1e-7,
        bounds: Tuple[float, float] = (-0.1, 0.2)):
    r""" yield-to-maturity or effective interest rate

    :param cashflow_list: list of cashflows
    :param valuation_date: date to discount to
        (optional; default: **cashflow_list.origin**)
    :param present_value: price to meet by discounting
        (optional; default: 0.0)
    :param payoff_model: payoff model
        (optional; default: **None**, i.e. model attached to **cashflow_list**)
    :param precision: max distance of present value to par
        (optional: default is 1e-7)
    :param bounds: tuple of lower and upper bound of yield to maturity
        (optional: default is -0.1 and .2)
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

    >>> from tabulate import tabulate
    >>> from yieldcurves import YieldCurve
    >>> from yieldcurves.interpolation import linear
    >>> from dcf import CashFlowList
    >>> from dcf import pv, ytm

    >>> curve = YieldCurve.from_interpolation([0.0], [0.05]).df
    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0.0, fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    bond with cashflow tables

    >>> coupon_leg.print()
      pay date    cashflow    notional  pay rec      fixed rate    start date    end date    year fraction
    ----------  ----------  ----------  ---------  ------------  ------------  ----------  ---------------
           1.0     1_000.0   1_000_000  pay               0.001           0.0         1.0              1.0
           2.0     1_000.0   1_000_000  pay               0.001           1.0         2.0              1.0
           3.0     1_000.0   1_000_000  pay               0.001           2.0         3.0              1.0
           4.0     1_000.0   1_000_000  pay               0.001           3.0         4.0              1.0
           5.0     1_000.0   1_000_000  pay               0.001           4.0         5.0              1.0

    >>> redemption_leg.print()
      pay date    cashflow
    ----------  ----------
           5.0   1_000_000 

    get yield-to-maturity at par (gives coupon rate)

    >>> ytm(bond, valuation_date=0, present_value=n)  
    0.0009...

    get current yield-to-maturity as given by 1.5% risk free rate (gives risk free rate)

    >>> present_value = pv(bond, curve, valuation_date=0.0)
    >>> present_value  
    783115.0894...

    >>> ytm(bond, valuation_date=0, present_value=present_value)  
    0.0499...

    """  # noqa 501

    # set error function
    def err(current):
        _pv = pv(cashflow_list, current, valuation_date, payoff_model)
        return _pv - present_value

    # run bracketing
    return simple_bracketing(err, *bounds, precision)


def iac(cashflow_list: CashFlowList,
        valuation_date: DateType,
        payoff_model: PayOffModel | None = None):
    r""" calculates interest accrued for rate cashflows

        :param cashflow_list: requires a `day_count` property
        :param valuation_date: calculation date
        :param payoff_model: payoff model
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

    >>> from tabulate import tabulate
    >>> from dcf import iac, CashFlowList

    setup 5y coupon bond

    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0., fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    bond with cashflow tables

    >>> coupon_leg.print()
      pay date    cashflow    notional  pay rec      fixed rate    start date    end date    year fraction
    ----------  ----------  ----------  ---------  ------------  ------------  ----------  ---------------
           1.0     1_000.0   1_000_000  pay               0.001           0.0         1.0              1.0
           2.0     1_000.0   1_000_000  pay               0.001           1.0         2.0              1.0
           3.0     1_000.0   1_000_000  pay               0.001           2.0         3.0              1.0
           4.0     1_000.0   1_000_000  pay               0.001           3.0         4.0              1.0
           5.0     1_000.0   1_000_000  pay               0.001           4.0         5.0              1.0


    >>> redemption_leg.print()
      pay date    cashflow
    ----------  ----------
           5.0   1_000_000


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
    payoff_model = payoff_model or cashflow_list.payoff_model
    ac = 0.0
    for cf in cashflow_list:
        if isinstance(cf, RateCashFlowPayOff):
            # only interest cash flows entitle to accrued interest
            if cf.start < valuation_date <= cf.end:
                day_count = cf.day_count or _default_day_count
                remaining = day_count(valuation_date, cf.end)
                total = day_count(cf.start, cf.end)
                flow = float(cf(payoff_model))
                ac += flow * (1. - remaining / total)
    return ac


def fair(cashflow_list: CashFlowList,
         discount_curve: Callable | float,
         valuation_date: DateType,
         present_value: float = 0.0,
         payoff_model: PayOffModel | None = None,
         precision: float = 1e-7,
         bounds: Tuple[float, float] = (-0.1, 0.2)):
    r""" coupon rate to meet given value

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param present_value: price to meet by discounting
        (optional: default: 0.0)
    :param payoff_model: payoff model
        (optional; default: **None**, i.e. model attached to **cashflow_list**)
    :param precision: max distance of present value to par
        (optional: default is 1e-7)
    :param bounds: tuple of lower and upper bound of fair rate
        (optional: default is -0.1 and .2)
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

    >>> present_value = pv(redemption_leg, curve, 0.0)
    >>> fair_rate = fair(coupon_leg, curve, 0.0, present_value=n-present_value)
    >>> fair_rate  
    0.0151...

    check it's a par bond (pv=notional)

    >>> for cf in coupon_leg: 
    ...     cf.fixed_rate = fair_rate
    >>> pv(bond, curve, 0.0)  
    999999.9999...

    """  # noqa 501

    # store fixed rate
    _fixed_rates = [cf.fixed_rate for cf in cashflow_list]

    # set error function
    def err(current):
        for cf in cashflow_list:
            cf.fixed_rate = current
        _pv = pv(cashflow_list, discount_curve, valuation_date, payoff_model)
        return _pv - present_value

    # run bracketing
    par = simple_bracketing(err, *bounds, precision)

    # restore fixed rate
    for cf, _fixed_rate in zip(cashflow_list, _fixed_rates):
        cf.fixed_rate = _fixed_rate

    return par


def bpv(cashflow_list: CashFlowList,
        discount_curve: Callable | float,
        valuation_date: DateType,
        payoff_model: PayOffModel | None = None,
        delta_curve: Callable | Iterable[Callable] | None = None,
        shift: float = 0.0001):
    r""" basis point value (bpv),
    i.e. value change by one interest rate shifted one basis point

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param payoff_model: payoff model
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

    >>> from yieldcurves import YieldCurve, AlgebraCurve
    >>> from dcf import pv, bpv, CashFlowList

    setup 5y coupon bond

    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0., fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg
    
    together with a flat yield curve
    
    >>> curve = YieldCurve(0.015)
    >>> pv(bond, curve.df, 0.0)
    932524.5493034504
    
    calculate bpv as bond delta

    >>> yc = YieldCurve(AlgebraCurve(curve, inplace=True))
    >>> bpv(bond, yc.df, 0.0, delta_curve=yc.curve)  
    -465.1755...

    double check by direct valuation

    >>> present_value = pv(bond, curve.df, 0.0)
    >>> shifted = YieldCurve(0.015 + 0.0001)
    >>> pv(bond, shifted.df, 0.0) - present_value  
    -465.1755...

    """  # noqa 501
    _pv = pv(cashflow_list, discount_curve, valuation_date, payoff_model)

    delta_curve = discount_curve if delta_curve is None else delta_curve
    if not isinstance(delta_curve, (list, tuple)):
        delta_curve = delta_curve,

    for d in delta_curve:
        d += shift

    sh = pv(cashflow_list, discount_curve, valuation_date, payoff_model)

    for d in delta_curve:
        d -= shift

    return (sh - _pv) / shift * .0001


def delta(cashflow_list: CashFlowList,
          discount_curve: Callable | float,
          valuation_date: DateType,
          payoff_model: PayOffModel | None = None,
          delta_curve: Callable | Iterable[Callable] | None = None,
          delta_grid: Iterable[DateType] | None = None,
          shift: float = .0001):
    r""" list of bpv delta for partly (bucketed) shifted interest rate curve

    :param cashflow_list: list of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
        (optional; default is **discount_curve.origin**)
    :param payoff_model: payoff model
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

    >>> from yieldcurves import YieldCurve, AlgebraCurve
    >>> from dcf import pv, bpv, delta, CashFlowList

    setup 5y coupon bond

    >>> curve = YieldCurve.from_interpolation([0.,1.,2.,3.,4.,5.], [0.01, 0.011, 0.014, 0.012, 0.01, 0.013])
    >>> n = 1_000_000
    >>> coupon_leg = CashFlowList.from_rate_cashflows([1.,2.,3.,4.,5.], amount_list=n, origin=0., fixed_rate=0.001)
    >>> redemption_leg = CashFlowList.from_fixed_cashflows([5.], amount_list=n)
    >>> bond = coupon_leg + redemption_leg

    calculate bpv as bond delta

    >>> yc = YieldCurve(AlgebraCurve(curve, inplace=True))
    >>> bucked_bpv = delta(bond, yc.df, 0.0, delta_curve=yc.curve, delta_grid=[0.,1.,2.,3.,4.,5.])  
    >>> bucked_bpv
    (0.0, -0.098901..., -0.194458..., -0.289348..., -0.384238..., -468.885034...)

    check by summing up (should give flat bpv)

    >>> sum(bucked_bpv)  
    -469.851981...
    
    >>> bpv(bond, yc.df, 0.0, delta_curve=yc.curve)  
    -469.851981...

    """  # noqa 501
    _pv = pv(cashflow_list, discount_curve, valuation_date, payoff_model)

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
        mids = list(map(list, zip(delta_grid[0: -2], delta_grid[1: -1], delta_grid[2:])))
        last = [delta_grid[-2], delta_grid[-1]]
        grids = [first] + mids + [last]
        shifts = [[shift, 0.]] + [[0., shift, 0.]] * len(mids) + [[0., shift]]

    buckets = list()
    for g, s in zip(grids, shifts):
        sh = piecewise_linear(g, s)
        for d in delta_curve:
            d += sh
        sh_pv = pv(cashflow_list, discount_curve, valuation_date, payoff_model)
        for d in delta_curve:
            d -= sh
        buckets.append((sh_pv - _pv) / shift * .0001)

    return tuple(buckets)


def fit(cashflow_list: Iterable[CashFlowList],
        discount_curve: Callable | float,
        valuation_date: DateType,
        payoff_model: PayOffModel | None = None,
        price_list: Iterable[float] | None = None,
        fitting_curve: Callable | None = None,
        fitting_grid: Iterable[float] | None = None,
        interpolation_type: str | Callable | None = None,
        method: str = 'secant_method',
        bounds: Tuple[float, float] = (-0.1, 0.2),
        tolerance: float = 1e-10
        ) -> Dict[float, float]:
    """fit interpolated curve to prices

    :param cashflow_list: list of cashflows instruments,
        i.e. list of lists of cashflows
    :param discount_curve: discount factors are obtained from this curve
    :param valuation_date: date to discount to
    :param payoff_model: payoff model
        (optional; default: **None**, i.e. model attached to **cashflow_list**)
    :param price_list: list of prices to match
        (optional; default assumes all prices to be 0.0)
    :param fitting_curve: curve to fit by inplace adding another curve,
        e.g. see `yieldcurves.AlgebraCurve()`
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
    >>> from yieldcurves import YieldCurve, AlgebraCurve, DateCurve

    build cashflow instruments

    >>> today = 0.0
    >>> schedule = [1., 2., 3., 4., 5. ]
    >>> cashflow_list = []
    >>> for d in schedule:
    ...     pay_dates = [s for s in schedule if s <= d]
    ...     cashflow_list.append(CashFlowList.from_fixed_cashflows(pay_dates))

    setup curve to derive target values and generate data for calibration

    >>> curve = YieldCurve.from_interpolation(schedule, [0.01, 0.009, 0.012, 0.014, 0.011])
    >>> targets = [pv(c, curve.df, 0.0) for c in cashflow_list]  # target values to match

    invoke curve fitting

    >>> fit(cashflow_list, 1.0, today, price_list=targets)
    {1.0: 0.009999999999989299, 2.0: 0.008999999998175629, 3.0: 0.011999999986343402, 4.0: 0.013999999946028392, 5.0: 0.011000000052247317}

    or

    >>> yc = YieldCurve(AlgebraCurve(0.0, inplace=True))  # curve to calibrate to
    >>> rates = fit(cashflow_list, yc.df, today, price_list=targets)  # curve fitting
    >>> rates
    {1.0: 0.009999999999989299, 2.0: 0.008999999998175629, 3.0: 0.011999999986343402, 4.0: 0.013999999946028392, 5.0: 0.011000000052247317}

    setup new curve

    >>> yc2 = YieldCurve.from_interpolation(rates.keys(), rates.values())
    >>> yc2
    YieldCurve(piecewise_linear([1.0, 2.0, 3.0, 4.0, 5.0], [0.009999999999989299, 0.008999999998175629, 0.011999999986343402, 0.013999999946028392, 0.011000000052247317]))

    double check results

    >>> err = [abs(pv(cf, yc2.df, 0.0) - v) for cf, v in zip(cashflow_list, targets)]
    >>> max(err) < 1e-7
    True

    The abouve is acctually the same as

    >>> yc = DateCurve(YieldCurve(AlgebraCurve(0.0, inplace=True)), origin=0.0)
    >>> grid = [yc.year_fraction(max(cf.domain)) for cf in cashflow_list]
    >>> fit(cashflow_list, yc.df, today, price_list=targets, fitting_curve=yc.curve.curve, fitting_grid=grid)
    {1.0: 0.009999999999989299, 2.0: 0.008999999998175629, 3.0: 0.011999999986343402, 4.0: 0.013999999946028392, 5.0: 0.011000000052247317}

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
    >>> targets = [pv(c, curve.df, today) for c in cashflow_list]

    invoke curve fitting

    >>> yc = DateCurve(YieldCurve(AlgebraCurve(0.0, inplace=True)), origin=today)
    >>> fit(cashflow_list, yc.df, today, price_list=targets)
    {1.002053388090349: 0.009261635865832207, 2.001368925393566: 0.011213039013339773, 3.0006844626967832: 0.013473990408407546, 4.0: 0.011791067769224518, 5.002053388090349: 0.011000000000002251}

    The abouve is acctually the same as

    >>> yc = DateCurve(YieldCurve(AlgebraCurve(0.0, inplace=True)), origin=today)
    >>> grid = [yc.year_fraction(max(cf.domain)) for cf in cashflow_list]
    >>> fit(cashflow_list, yc.df, today, price_list=targets, fitting_curve=yc.curve.curve, fitting_grid=grid)
    {1.002053388090349: 0.009261635865832207, 2.001368925393566: 0.011213039013339773, 3.0006844626967832: 0.013473990408407546, 4.0: 0.011791067769224518, 5.002053388090349: 0.011000000000002251}


    """
    try:
        from yieldcurves import YieldCurve, AlgebraCurve, DateCurve
        from yieldcurves.interpolation import fit as _fit
    except ImportError:
        raise ImportError("fit() requires yieldcurves package. "
                          "try `pip install yieldcurves`")

    if fitting_grid is None:
        if isinstance(getattr(discount_curve, '__self__', ''), DateCurve):
            yf = discount_curve.__self__.year_fraction
        else:
            origin = getattr(discount_curve, 'origin', valuation_date)
            yf = lambda x: _default_day_count(origin, x)
        fitting_grid = [yf(max(cf.domain)) for cf in cashflow_list]

    if fitting_curve is None:
        if isinstance(discount_curve, (int, float)):
            if discount_curve - 1:
                raise ValueError(f"constant discount_curve be 1.0 as"
                                 f"a value of {discount_curve} is ambiguous")

            fitting_curve = AlgebraCurve(0.0, inplace=True)
            discount_curve = YieldCurve(fitting_curve).df
        elif isinstance(getattr(discount_curve, '__self__', ''), DateCurve):
            date_curve = discount_curve.__self__
            fitting_curve = AlgebraCurve(date_curve.curve, inplace=True)
            origin = date_curve.origin
            discount_curve = \
                DateCurve(YieldCurve(fitting_curve), origin=origin).df
        else:
            fitting_curve = \
                AlgebraCurve(YieldCurve.from_df(discount_curve), inplace=True)
            discount_curve = YieldCurve(fitting_curve).df

    args = discount_curve, valuation_date, payoff_model
    err_funcs = [partial(pv, cf, *args) for cf in cashflow_list]
    if price_list is None:
        price_list = [0.0] * len(fitting_grid)
    return _fit(fitting_curve, fitting_grid, err_funcs, price_list,
                interpolation_type=interpolation_type,
                method=method, bounds=bounds, tolerance=tolerance)
