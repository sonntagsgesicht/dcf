
.. py:module:: dcf

-----------------
API Documentation
-----------------

.. toctree::

Curve Objects
=============

Basic Curves
------------

.. module:: dcf.curves.curve

.. autosummary::
    :nosignatures:

    Curve
    DateCurve
    RateCurve

.. inheritance-diagram:: dcf.curves.curve
    :parts: 1

.. autoclass:: Curve
.. autoclass:: DateCurve
.. autoclass:: RateCurve

.. autofunction:: rate_table

Interest Rate Curves
--------------------

.. module:: dcf.curves.interestratecurve

.. autosummary::
    :nosignatures:

    InterestRateCurve
    ZeroRateCurve
    DiscountFactorCurve
    CashRateCurve
    ShortRateCurve

.. inheritance-diagram:: dcf.curves.interestratecurve
    :parts: 1
    :top-classes: dcf.curves.curve.RateCurve

.. autoclass:: InterestRateCurve
.. autoclass:: ZeroRateCurve
.. autoclass:: DiscountFactorCurve
.. autoclass:: CashRateCurve
.. autoclass:: ShortRateCurve


Credit Curves
-------------

.. module:: dcf.curves.creditcurve

.. autosummary::
    :nosignatures:

    CreditCurve
    SurvivalProbabilityCurve
    FlatIntensityCurve
    HazardRateCurve
    MarginalSurvivalProbabilityCurve
    MarginalDefaultProbabilityCurve

.. inheritance-diagram:: dcf.curves.creditcurve
    :parts: 1
    :top-classes: dcf.curves.curve.RateCurve

.. autoclass:: CreditCurve
.. autoclass:: SurvivalProbabilityCurve
.. autoclass:: DefaultProbabilityCurve
.. autoclass:: FlatIntensityCurve
.. autoclass:: HazardRateCurve
.. autoclass:: MarginalSurvivalProbabilityCurve
.. autoclass:: MarginalDefaultProbabilityCurve


Fx Curve
--------

.. module:: dcf.curves.fx

.. autosummary::
    :nosignatures:

    FxCurve

.. inheritance-diagram:: dcf.curves.fx.FxCurve
    :parts: 1
    :top-classes: dcf.curves.curve.DateCurve

.. autoclass:: FxRate
    :inherited-members:

.. autoclass:: FxCurve


Cashflow Objects
================

Build Functions
---------------

.. automodule:: dcf.plans


Cashflow Objects
----------------


.. py:currentmodule:: dcf.cashflows.cashflow

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: dcf.cashflows.cashflow
    :parts: 1

.. automodule:: dcf.cashflows.cashflow
    :members:


Valuation Routines
==================

Present Value
-------------

.. autofunction:: dcf.pricer.get_present_value

Yield To Maturity
-----------------

.. autofunction:: dcf.pricer.get_yield_to_maturity

Fair/Par Rate
-------------

.. autofunction:: dcf.pricer.get_fair_rate
.. autofunction:: dcf.pricer.get_par_rate

Interest Accrued
----------------

.. autofunction:: dcf.pricer.get_interest_accrued


Basis Point Value
-----------------

.. autofunction:: dcf.pricer.get_basis_point_value


Bucketed Delta
--------------

.. autofunction:: dcf.pricer.get_bucketed_delta


Fundamentals
============

Interpolation
-------------

.. automodule:: dcf.interpolation


Compounding
-----------

.. automodule:: dcf.compounding


DayCount
--------

.. automodule:: dcf.daycount


Rating Classes
--------------

.. automodule:: dcf.ratingclass

