
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

    Price
    Curve
    DateCurve
    ForwardCurve
    RateCurve

.. inheritance-diagram:: dcf.curves.curve
    :top-classes: dcf.curves.curve.Curve
    :parts: 1

.. autoclass:: Price
.. autoclass:: Curve
.. autoclass:: DateCurve
.. autoclass:: ForwardCurve
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

    FxForwardCurve

.. inheritance-diagram:: dcf.curves.fx.FxForwardCurve
    :parts: 1
    :top-classes: dcf.curves.curve.DateCurve

.. autoclass:: FxRate
    :inherited-members:

.. autoclass:: FxForwardCurve


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


Contingent Cashflow Objects (Options)
-------------------------------------

.. py:currentmodule:: dcf.cashflows.contingent

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: dcf.cashflows.contingent
    :parts: 1

.. automodule:: dcf.cashflows.contingent
    :members:


Contingent Cashflow Models
--------------------------

.. py:currentmodule:: dcf.models

.. automodule:: dcf.models.base
    :members:

.. automodule:: dcf.models.intrinsic
    :members:

.. automodule:: dcf.models.bachelier
    :members:

.. automodule:: dcf.models.black76
    :members:

.. automodule:: dcf.models.displaced
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
