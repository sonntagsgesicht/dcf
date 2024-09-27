
.. py:module:: dcf

-----------------
API Documentation
-----------------

.. toctree::

Cashflow Objects
================

Build Functions
---------------

.. automodule:: dcf.plans


Cashflow Payoffs
----------------

.. py:currentmodule:: dcf.payoffs

.. autosummary::
    :nosignatures:

    FixedCashFlowPayOff
    RateCashFlowPayOff
    ContingentRateCashFlowPayOff

    OptionCashFlowPayOff
    OptionStrategyCashFlowPayOff

.. autoclass:: FixedCashFlowPayOff

.. autoclass:: RateCashFlowPayOff

.. autoclass:: ContingentRateCashFlowPayOff

.. autoclass:: OptionCashFlowPayOff

.. autoclass:: OptionStrategyCashFlowPayOff

.. autoclass:: CashFlowPayOff


CashFlowList
------------

.. py:currentmodule:: dcf.cashflowlist

.. autosummary::
    :nosignatures:

.. autoclass:: CashFlowList


PayOff Models and Option Pricing
================================

PayOff Models
-------------

.. py:currentmodule:: dcf.payoffmodels

.. autosummary::
    :nosignatures:

    PayOffModel
    OptionPayOffModel

.. autoclass:: PayOffModel

.. autoclass:: OptionPayOffModel



Option Pricing Formulas
-----------------------

.. py:currentmodule:: dcf.optionpricing

.. autosummary::
    :nosignatures:

    Intrinsic
    Bachelier
    Black76
    DisplacedBlack76

.. autoclass:: Intrinsic

.. autoclass:: Bachelier

.. autoclass:: Black76

.. autoclass:: DisplacedBlack76


Basics on Option Pricing Formulas
---------------------------------

.. py:currentmodule:: dcf.optionpricing.base

.. autosummary::
    :nosignatures:

    OptionPricingFormula
    FunctionalOptionPricingFormula
    DisplacedOptionPricingFormula

.. autoclass:: OptionPricingFormula

.. autoclass:: FunctionalOptionPricingFormula

.. autoclass:: DisplacedOptionPricingFormula


Valuation Routines
==================

Expected Payoff
---------------

.. autofunction:: dcf.pricer.ecf

Present Value
-------------

.. autofunction:: dcf.pricer.pv

Yield To Maturity
-----------------

.. autofunction:: dcf.pricer.ytm

Fair Rate
---------

.. autofunction:: dcf.pricer.fair

Interest Accrued
----------------

.. autofunction:: dcf.pricer.iac


Basis Point Value
-----------------

.. autofunction:: dcf.pricer.bpv


Bucketed Delta
--------------

.. autofunction:: dcf.pricer.delta


Curve Bootstrapping
-------------------

.. autoclass:: dcf.pricer.fit


Fundamentals
============

DayCount
--------

.. automodule:: dcf.daycount
