
.. py:module:: dcf

-----------------
API Documentation
-----------------

.. toctree::

Curve Objects
=============

Basic Curves
------------

.. module:: dcf.curve

.. autosummary::
    :nosignatures:

    Curve
    DateCurve
    RateCurve

.. inheritance-diagram:: dcf.curve
    :parts: 1

.. autoclass:: Curve
.. autoclass:: DateCurve
.. autoclass:: RateCurve


Interest Rate Curves
--------------------

.. module:: dcf.interestratecurve

.. autosummary::
    :nosignatures:

    InterestRateCurve
    ZeroRateCurve
    DiscountFactorCurve
    CashRateCurve
    ShortRateCurve

.. inheritance-diagram:: dcf.interestratecurve
    :parts: 1
    :top-classes: dcf.curve.RateCurve

.. autoclass:: InterestRateCurve
.. autoclass:: ZeroRateCurve
.. autoclass:: DiscountFactorCurve
.. autoclass:: CashRateCurve
.. autoclass:: ShortRateCurve


Credit Curves
-------------

.. module:: dcf.creditcurve

.. autosummary::
    :nosignatures:

    CreditCurve
    SurvivalProbabilityCurve
    FlatIntensityCurve
    HazardRateCurve
    MarginalSurvivalProbabilityCurve
    MarginalDefaultProbabilityCurve

.. inheritance-diagram:: dcf.creditcurve
    :parts: 1
    :top-classes: dcf.curve.RateCurve

.. autoclass:: CreditCurve
.. autoclass:: SurvivalProbabilityCurve
.. autoclass:: DefaultProbabilityCurve
.. autoclass:: FlatIntensityCurve
.. autoclass:: HazardRateCurve
.. autoclass:: MarginalSurvivalProbabilityCurve
.. autoclass:: MarginalDefaultProbabilityCurve


Fx Curve
--------

.. module:: dcf.fx

.. autosummary::
    :nosignatures:

    FxCurve

.. inheritance-diagram:: dcf.fx.FxCurve
    :parts: 1
    :top-classes: dcf.curve.DateCurve

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


.. py:currentmodule:: dcf.cashflow

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: dcf.cashflow
    :parts: 1

.. automodule:: dcf.cashflow
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


Basis Point Value (BPV)
-----------------------

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

.. automodule:: dcf.day_count


Rating Classes
--------------

.. automodule:: dcf.ratingclass

