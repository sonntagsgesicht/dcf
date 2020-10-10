
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

CashFlowList Objects
--------------------

Valuation
---------

