
.. py:module:: dcf

-----------------
API Documentation
-----------------

.. toctree::


Interpolation
=============


Interpolation Types
-------------------

.. automodule:: dcf.interpolation


Interpolation Scheme
--------------------

.. automodule:: dcf.interpolationscheme


Compounding
===========

.. automodule:: dcf.compounding


Curves
======

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

.. py:currentmodule:: dcf.cashflow

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: dcf.cashflow
    :parts: 1

.. automodule:: dcf.cashflow
    :members:


