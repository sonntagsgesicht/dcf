
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

.. currentmodule:: dcf

Basic Curves

.. autosummary::
    :nosignatures:

    Curve
    DateCurve
    RateCurve

Interest Rate Curves

.. autosummary::
    :nosignatures:

    InterestRateCurve
    ZeroRateCurve
    DiscountFactorCurve
    CashRateCurve
    ShortRateCurve

Credit Curves

.. autosummary::
    :nosignatures:

    CreditCurve
    SurvivalProbabilityCurve
    FlatIntensityCurve
    HazardRateCurve
    MarginalSurvivalProbabilityCurve
    MarginalDefaultProbabilityCurve

Fx Curves

.. autosummary::
    :nosignatures:

    FxCurve

Basic Curves
------------

.. inheritance-diagram:: curve
    :parts: 1

.. autoclass:: Curve
.. autoclass:: DateCurve
.. autoclass:: RateCurve


Interest Rate Curves
--------------------

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: interestratecurve
    :parts: 1
    :top-classes: dcf.curve.RateCurve

.. autoclass:: InterestRateCurve
.. autoclass:: ZeroRateCurve
.. autoclass:: DiscountFactorCurve
.. autoclass:: CashRateCurve
.. autoclass:: ShortRateCurve


Credit Curves
-------------

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: creditcurve
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

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: dcf.fx.FxCurve
    :parts: 1
    :top-classes: dcf.curve.DateCurve

.. autoclass:: FxRate
    :inherited-members:

.. autoclass:: FxCurve


Cashflow Objects
================

.. autosummary::
    :nosignatures:

.. inheritance-diagram:: dcf.cashflow
    :parts: 1

.. automodule:: dcf.cashflow
    :members:


