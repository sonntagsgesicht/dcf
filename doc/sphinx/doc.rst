
.. py:module:: dcf

-----------------
API Documentation
-----------------

.. toctree::


Cashflow Objects
================


Cashflow Payoffs
----------------

.. py:currentmodule:: dcf.payoffs

.. autosummary::
    :nosignatures:

    FixedCashFlowPayOff
    RateCashFlowPayOff
    OptionCashFlowPayOff

.. autoclass:: FixedCashFlowPayOff

.. autoclass:: RateCashFlowPayOff

.. autoclass:: OptionCashFlowPayOff


CashFlow List
-------------

.. autosummary::
    :nosignatures:

.. autoclass:: CashFlowList


Valuation Routines
==================

Expected Payoff
---------------

.. autofunction:: dcf.pricer.ecf


Present Value
-------------

.. autofunction:: dcf.pricer.pv


Interest Accrued
----------------

.. autofunction:: dcf.pricer.iac


Yield To Maturity
-----------------

.. autofunction:: dcf.pricer.ytm


Fair Rate
---------

.. autofunction:: dcf.pricer.fair


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

Build Functions
---------------

.. automodule:: dcf.plans


DayCount
--------

.. automodule:: dcf.daycount
