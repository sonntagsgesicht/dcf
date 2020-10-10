
Python library *dcf*
--------------------

.. image:: https://img.shields.io/codeship/a10d1dd0-a1a0-0137-f00d-1a3bc2cae4aa/master.svg
   :target: https://codeship.com//projects/359976
   :alt: Codeship

.. image:: https://travis-ci.org/sonntagsgesicht/dcf.svg?branch=master
   :target: https://travis-ci.org/sonntagsgesicht/dcf
   :alt: Travis ci

.. image:: https://img.shields.io/readthedocs/dcf
   :target: http://dcf.readthedocs.io
   :alt: Read the Docs

.. image:: https://img.shields.io/codefactor/grade/github/sonntagsgesicht/dcf/master
   :target: https://www.codefactor.io/repository/github/sonntagsgesicht/dcf
   :alt: CodeFactor Grade

.. image:: https://img.shields.io/codeclimate/maintainability/sonntagsgesicht/dcf
   :target: https://codeclimate.com/github/sonntagsgesicht/dcf/maintainability
   :alt: Code Climate maintainability

.. image:: https://img.shields.io/codecov/c/github/sonntagsgesicht/dcf
   :target: https://codecov.io/gh/sonntagsgesicht/dcf
   :alt: Codecov

.. image:: https://img.shields.io/lgtm/grade/python/g/sonntagsgesicht/dcf.svg
   :target: https://lgtm.com/projects/g/sonntagsgesicht/dcf/context:python/
   :alt: lgtm grade

.. image:: https://img.shields.io/lgtm/alerts/g/sonntagsgesicht/dcf.svg
   :target: https://lgtm.com/projects/g/sonntagsgesicht/dcf/alerts/
   :alt: total lgtm alerts

.. image:: https://img.shields.io/github/license/sonntagsgesicht/dcf
   :target: https://github.com/sonntagsgesicht/dcf/raw/master/LICENSE
   :alt: GitHub

.. image:: https://img.shields.io/github/release/sonntagsgesicht/dcf?label=github
   :target: https://github.com/sonntagsgesicht/dcf/releases
   :alt: GitHub release

.. image:: https://img.shields.io/pypi/v/dcf
   :target: https://pypi.org/project/dcf/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/dcf
   :target: https://pypi.org/project/dcf/
   :alt: PyPI - Python Version

.. image:: https://img.shields.io/pypi/dm/dcf
   :target: https://pypi.org/project/dcf/
   :alt: PyPI Downloads

.. image:: https://pepy.tech/badge/dcf
   :target: https://pypi.org/project/dcf/
   :alt: PyPI Downloads

A Python library for generating discounted cashflows *(dcf)*.
Typical banking business methods are provided like interpolation, compounding,
discounting and fx.


Example Usage
-------------

.. code-block:: python

    >>> from datetime import date
    >>> from dcf import ZeroRateCurve

    >>> start = date(2014,1,1)
    >>> mid = date(2015,1,1)
    >>> end = date(2016,1,1)

    >>> ZeroRateCurve([start, end], [.03, .05]).get_zero_rate(start, mid)
    0.04

    >>> ZeroRateCurve([start, end], [.03, .05]).get_discount_factor(start, mid)
    0.9608157444936446


The framework works fine with native `datetime <https://docs.python.org/3/library/datetime.html>`_
but we recommend `businessdate <https://pypi.org/project/businessdate/>`_ package
for more convenient functionality to roll out date schedules.

.. code-block:: python

    >>> from businessdate import BusinessDate, BusinessSchedule

    >>> today = BusinessDate(20201031)

    >>> schedule = BusinessSchedule(today, today + "8q", step="1q")
    >>> schedule
    [BusinessDate(20201031), BusinessDate(20210131), BusinessDate(20210430), BusinessDate(20210731), BusinessDate(20211031), BusinessDate(20220131), BusinessDate(20220430), BusinessDate(20220731), BusinessDate(20221031)]

To build payment plans for, e.g. annuity loans, pick a plan function
and generate an redemption amount list for paying back the loan notional amount.

.. code-block:: python

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


Putting all together and feeding the plan into a `FixedCashFlowList`
and the list of outstanding into a `RateCashflowList` gives the legs of a loan.

.. code-block:: python

    >>> from businessdate import BusinessDate, BusinessSchedule
    >>> from dcf import amortize, outstanding
    >>> from dcf import FixedCashFlowList, RateCashFlowList

Again, build a date schedule.

.. code-block:: python

    >>> today = BusinessDate(20201031)

    >>> schedule = BusinessSchedule(today, today + "8q", step="1q")

    >>> start_date, payment_dates = schedule[0], schedule[1:]

Fixing the properties of the product and rolling out the payment plan and list of notional outstanding.

.. code-block:: python

    >>> number_of_payments = 8
    >>> interest_rate = 0.01
    >>> notional = 1000.

    >>> plan = amortize(number_of_payments, amount=notional)
    >>> out = outstanding(plan, amount=notional)

Finally, create for each leg a `CashFlowList`.

.. code-block:: python

    >>> principal = FixedCashFlowList([start_date], [-notional], origin=start_date)
    >>> print(principal)
    FixedCashFlowList([BusinessDate(20201031) ... BusinessDate(20201031)], [-1000.0 ... -1000.0], origin=BusinessDate(20201031), day_count=day_count)

    >>> redemption = FixedCashFlowList(payment_dates, plan, origin=start_date)
    >>> print(redemption)
    FixedCashFlowList([BusinessDate(20210131) ... BusinessDate(20221031)], [125.0 ... 125.0], origin=BusinessDate(20201031), day_count=day_count)

    >>> interest = RateCashFlowList(payment_dates, out, origin=start_date, fixed_rate=interest_rate)
    >>> print(interest)
    RateCashFlowList([BusinessDate(20210131) ... BusinessDate(20221031)], [1000.0 ... 125.0], origin=BusinessDate(20201031), day_count=day_count)

Add those legs to `CashFlowLegList` provides a smart container for valuation (`get_present_value()`).

.. code-block:: python

    >>> from dcf import CashFlowLegList, ZeroRateCurve, get_present_value

    >>> loan = CashFlowLegList([principal, redemption, interest])
    >>> curve = ZeroRateCurve([today, today + '2y'], [-.005, .01])
    >>> pv = get_present_value(cashflow_list=loan, discount_curve=curve, valuation_date=today)
    >>> pv
    4.935421637918779

Install
-------

The latest stable version can always be installed or updated via pip:

.. code-block:: bash

    $ pip install dcf



Development Version
-------------------

The latest development version can be installed directly from GitHub:

.. code-block:: bash

    $ pip install --upgrade git+https://github.com/sonntagsgesicht/dcf.git


Contributions
-------------

.. _issues: https://github.com/sonntagsgesicht/dcf/issues
.. __: https://github.com/sonntagsgesicht/dcf/pulls

Issues_ and `Pull Requests`__ are always welcome.


License
-------

.. __: https://github.com/sonntagsgesicht/dcf/raw/master/LICENSE

Code and documentation are available according to the Apache Software License (see LICENSE__).


