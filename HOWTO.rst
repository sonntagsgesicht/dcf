
.. currentmodule:: dcf

To start with import the package.

.. doctest::

    >>> from dcf import Curve, DateCurve, RateCurve


Interest Rate Curve Objects
===========================

Curves Types
------------

Interest rate curves can be expressed in various  ways.
Each for different type of storing rate information and purpose.

There are four different types of interest rate curves:

    |ZeroRateCurve|, |DiscountfactorCurve|, |CashRateCurve| and |ShortRateCurve|.

They meet all the same interface, i.e. have the same properties and methods.
They differ only in data which can be given for constructing the curves.
This sets how rates are stored and interpolated.
Moreover an large list of interpolation methods are provided |interpolation|.

As the names indicate, these curves take either

* `zero (bond) rates <https://en.wikipedia.org/wiki/Zero-coupon_bond>`_,
* `discount factors <https://en.wikipedia.org/wiki/Discounting>`_,
* `forward cash interest rates <https://en.wikipedia.org/wiki/Libor>`_ or
* `instantaneous interest rates aka. short rates <https://en.wikipedia.org/wiki/Short-rate_model>`_

Getting Curve Values
--------------------

From each class offers teh same methods to calculate each of those four types of rate by

    |InterestRateCurve().get_zero_rate()|,
    |InterestRateCurve().get_discount_factor()|,
    |InterestRateCurve().get_cash_rate()|,
    |InterestRateCurve().get_short_rate()|

Casting Curves
--------------

Even casting one type to another is as easy as

.. doctest::

    >>> from businessdate import BusinessDate
    >>> from dcf import ZeroRateCurve, DiscountFactorCurve

    >>> today = BusinessDate(20201031)
    >>> date = today + '1m'

    >>> zr_curve = ZeroRateCurve([today, today + '2y'], [-.005, .01])
    >>> df_curve = DiscountFactorCurve(zr_curve)
    >>> re_curve = ZeroRateCurve(df_curve)

    >>> zr_curve(date), df_curve(date), re_curve(date)
    (-0.004383561643835616, 1.0003601109552978, -0.004383561643827753)


Credit Curve Objects
====================

Similar to |InterestRateCurve| |CreditCurve| come in different (storage) types.

Curves Types
------------

These are

    |SurvivalProbabilityCurve|, |DefaultProbabilityCurve|, |FlatIntensityCurve|,
    |HazardRateCurve|, |MarginalSurvivalProbabilityCurve|, |MarginalDefaultProbabilityCurve|


Getting Curve Values
--------------------

From each class offers teh same methods to calculate each of those four types of rate by

    |CreditCurve().get_flat_intensity()|,
    |CreditCurve().get_hazard_rate()|,
    |CreditCurve().get_survival_prob()|


Casting Curves
--------------

Even casting works the same way it does for interest rate curves.


Basic Curve Objects and Attributes
==================================

All of the mentioned curve classes inherit from these base classes.


Curve
-----

Most fundamental is the |Curve| which sets the interpolation method.
But note, even domain data (*x*-values),
accessed by |Curve().domain|, are assume to be float.

The *x*-values can be shifted *left* or *right*
by add in a *negative* or *positive* float via |Curve().shifted()|.


Operations
----------


DateCurve
---------

Different is |DateCurve|. Here are *x*-values given by date.
But also easily casted

.. doctest::

    >>> from businessdate import BusinessDate
    >>> from dcf import Curve, DateCurve

    >>> today = BusinessDate(20200915)

    >>> date_curve = DateCurve([today, today + '4y'], [0.1, 0.3])

    >>> curve = Curve(date_curve)

    >>> x =  date_curve.day_count(date_curve.origin, today + '2y')
    >>> curve(x), date_curve(today + '2y')
    (0.19993155373032168, 0.19993155373032168)

Already use was the domain property |Curve().domain| or |DateCurve().domain|
which reveals the *x*-values of the curve.

As we have to measure distances by a day counting method (aka. year fraction) |DateCurve().day_count()|,
which is mainly turning days into |float|.

See `wikipedia <https://en.wikipedia.org/wiki/Day_count_convention>`_ for details and
also `businessdate <https://businessdate.readthedocs.io/en/latest/doc.html#module-businessdate.daycount>`_
for an implementation.

Moreover a date |DateCurve().origin| is marking the origin of the *x*-axis

Finally, many curves can be integrated as well as the derivative can be derived.
Same works for |DateCurve()|:

    |DateCurve().integrate()|, |DateCurve().derivative()|


Cashflow Objects and Valuation
==============================

Payment Plans
-------------

    >>> from businessdate import BusinessDate, BusinessSchedule

    >>> today = BusinessDate(20201031)

    >>> schedule = BusinessSchedule(today, today + "8q", step="1q")
    >>> schedule
    [BusinessDate(20201031), BusinessDate(20210131), BusinessDate(20210430), BusinessDate(20210731), BusinessDate(20211031), BusinessDate(20220131), BusinessDate(20220430), BusinessDate(20220731), BusinessDate(20221031)]

To build payment plans for, e.g. annuity loans, pick a plan function
and generate an redemption amount list for paying back the loan notional amount.

.. doctest::

    >>> from dcf import annuity, outstanding

    >>> number_of_payments = 8
    >>> interest_rate = 0.02
    >>> notional = 1000.

    >>> plan = annuity(number_of_payments, amount=notional, fixed_rate=interest_rate)
    >>> plan
    [116.50979913376267, 118.83999511643792, 121.21679501876667, 123.64113091914203, 126.11395353752485, 128.63623260827535, 131.20895726044085, 133.83313640564967]


    >>> sum(plan)
    1000.0

    >>> out = outstanding(plan, amount=notional)
    >>> out
    [1000.0, 883.4902008662373, 764.6502057497994, 643.4334107310327, 519.7922798118907, 393.6783262743659, 265.0420936660905, 133.83313640564967]

    >>> compound = [o * interest_rate + p for o, p in zip(out, plan)]
    >>> compound
    [136.50979913376267, 136.50979913376267, 136.50979913376267, 136.50979913376267, 136.50979913376267, 136.50979913376267, 136.50979913376267, 136.50979913376267]

CashFlowList Objects
--------------------

Putting all together and feeding the plan into a `FixedCashFlowList
and the list of outstanding into a `RateCashflowList` gives the legs of a loan.

.. doctest::

    >>> from businessdate import BusinessDate, BusinessSchedule
    >>> from dcf import amortize, outstanding
    >>> from dcf import FixedCashFlowList, RateCashFlowList

Again, build a date schedule.

.. doctest::

    >>> today = BusinessDate(20201031)

    >>> schedule = BusinessSchedule(today, today + "8q", step="1q")

    >>> start_date, payment_dates = schedule[0], schedule[1:]

Fixing the properties of the product and rolling out the payment plan and list of notional outstanding.

.. doctest::

    >>> number_of_payments = 8
    >>> interest_rate = 0.01
    >>> notional = 1000.

    >>> plan = amortize(number_of_payments, amount=notional)
    >>> out = outstanding(plan, amount=notional)

Finally, create for each leg a |CashFlowList|.

.. doctest::

    >>> principal = FixedCashFlowList([start_date], [-notional], origin=start_date)
    >>> print(principal)
    FixedCashFlowList([BusinessDate(20201031) ... BusinessDate(20201031)], [-1000.0 ... -1000.0], origin=BusinessDate(20201031), day_count=day_count)

    >>> redemption = FixedCashFlowList(payment_dates, plan, origin=start_date)
    >>> print(redemption)
    FixedCashFlowList([BusinessDate(20210131) ... BusinessDate(20221031)], [125.0 ... 125.0], origin=BusinessDate(20201031), day_count=day_count)

    >>> interest = RateCashFlowList(payment_dates, out, origin=start_date, fixed_rate=interest_rate)
    >>> print(interest)
    RateCashFlowList([BusinessDate(20210131) ... BusinessDate(20221031)], [1000.0 ... 125.0], origin=BusinessDate(20201031), day_count=day_count)

Valuation
---------

Add those legs to |CashFlowLegList| provides a smart container for valuation (|get_present_value()|).

.. doctest::

    >>> from dcf import CashFlowLegList, ZeroRateCurve, get_present_value

    >>> loan = CashFlowLegList([principal, redemption, interest])
    >>> curve = ZeroRateCurve([today, today + '2y'], [-.005, .01])
    >>> pv = get_present_value(cashflow_list=loan, discount_curve=curve, valuation_date=today)
    >>> pv
    4.935421637918779