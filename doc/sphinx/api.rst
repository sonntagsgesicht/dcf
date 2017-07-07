
-----------------
API Documentation
-----------------

.. toctree::


Interpolation
=============

.. autosummary::
    :nosignatures:

    interpolation.base_interpolation
    interpolation.no
    interpolation.left
    interpolation.constant
    interpolation.flat
    interpolation.right
    interpolation.flat
    interpolation.nearest
    interpolation.zero

.. inheritance-diagram:: interpolation

.. automodule:: interpolation


Curve
=====

.. autosummary::
    :nosignatures:

    curve.Curve
    curve.DateCurve

    curve.RateCurve
    curve.DiscountFactorCurve
    curve.ZeroRateCurve
    curve.CashRateCurve
    curve.ShortRateCurve

    curve.CreditCurve
    curve.SurvivalProbabilityCurve
    curve.FlatIntensityCurve
    curve.ForwardSurvivalRate
    curve.HazardRateCurve

.. inheritance-diagram:: curve

.. automodule:: curve


Fx Objects
==========

.. autosummary::
    :nosignatures:

    fx.FxCurve
    fx.FxContainer

.. inheritance-diagram:: fx

.. automodule:: fx


Compounding
===========

.. automodule:: compounding


Cashflow
========

.. autosummary::
    :nosignatures:

    cashflow.CashFlowList
    cashflow.AmortizingCashFlowList
    cashflow.AnnuityCashFlowList
    cashflow.RateCashFlowList
    cashflow.MultiCashFlowList
    cashflow.FixedLoan
    cashflow.FloatLoan
    cashflow.FixedFloatSwap

.. inheritance-diagram:: cashflow

.. automodule:: cashflow
