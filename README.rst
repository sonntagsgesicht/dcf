
Python library *dcf*
--------------------

.. image:: https://github.com/sonntagsgesicht/dcf/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/sonntagsgesicht/dcf/actions/workflows/python-package.yml
    :alt: GitHubWorkflow

.. image:: https://img.shields.io/readthedocs/dcf
   :target: http://dcf.readthedocs.io
   :alt: Read the Docs

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

.. image:: https://pepy.tech/badge/dcf
   :target: https://pypi.org/project/dcf/
   :alt: PyPI Downloads

A Python library for generating discounted cashflows *(dcf)*.
Typical banking business methods are provided like interpolation, compounding,
discounting and fx.


Example Usage
-------------

>>> from businessdate import BusinessDate, BusinessSchedule

>>> today = BusinessDate(20201031)
>>> schedule = BusinessSchedule(today, today + "8q", step="1q")
>>> schedule
[BusinessDate(20201031), BusinessDate(20210131), BusinessDate(20210430), BusinessDate(20210731), BusinessDate(20211031), BusinessDate(20220131), BusinessDate(20220430), BusinessDate(20220731), BusinessDate(20221031)]

To build payment plans for, e.g. annuity loans, pick a plan function
and generate an redemption amount list for paying back the loan notional amount.


>>> from dcf.plans import annuity, outstanding

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


Putting all together and feeding the plan into a list of `CashFlowPayOff`
and the list of outstanding into a `CashflowList` gives the legs of a loan.


>>> from businessdate import BusinessDate, BusinessSchedule
>>> from dcf import CashFlowList
>>> from dcf.plans import amortize, outstanding

Again, build a date schedule.


>>> today = BusinessDate(20201031)
>>> schedule = BusinessSchedule(today, today + "8q", step="1q")
>>> start_date, payment_dates = schedule[0], schedule[1:]

Fixing the properties of the product and rolling out
the payment plan and list of notional outstanding.



>>> number_of_payments = 8
>>> interest_rate = 0.01
>>> notional = 1000.

>>> plan = amortize(number_of_payments, amount=notional)
>>> out = outstanding(plan, amount=notional)

Finally, create for each leg a `CashFlowList`.


>>> principal = CashFlowList.from_fixed_cashflows([start_date], [notional])
>>> print(principal)
pay date      cashflow
----------  ----------
20201031       1_000.0

>>> redemption = CashFlowList.from_fixed_cashflows(payment_dates, plan)
>>> print(redemption)
pay date      cashflow
----------  ----------
20210131         125.0
20210430         125.0
20210731         125.0
20211031         125.0
20220131         125.0
20220430         125.0
20220731         125.0
20221031         125.0

>>> interest = CashFlowList.from_rate_cashflows(payment_dates, out, fixed_rate=interest_rate)
>>> print(interest)
pay date      cashflow    notional  is rec      fixed rate  start date    end date      year fraction
----------  ----------  ----------  --------  ------------  ------------  ----------  ---------------
20210131      2.518892     1_000.0  True              0.01  20201031      20210131           0.251889
20210430      2.13216        875.0  True              0.01  20210131      20210430           0.243675
20210731      1.889169       750.0  True              0.01  20210430      20210731           0.251889
20211031      1.574307       625.0  True              0.01  20210731      20211031           0.251889
20220131      1.259446       500.0  True              0.01  20211031      20220131           0.251889
20220430      0.913783       375.0  True              0.01  20220131      20220430           0.243675
20220731      0.629723       250.0  True              0.01  20220430      20220731           0.251889
20221031      0.314861       125.0  True              0.01  20220731      20221031           0.251889


Add those legs to one `CashFlowList` provides a common container for valuation (`pv()`).

>>> loan = -principal + redemption + interest

We are using the `yieldcurves <http://yieldcurves.readthedocs.io>`_
package for convenient yield curve construction.
It can be found on `pypi <https://pypi.org/project/yieldcurves/>`_
and installed via :code:`$ pip install yieldcurves`.

>>> from dcf import pv
>>> from yieldcurves import YieldCurve, DateCurve

>>> yield_curve = YieldCurve.from_interpolation([0.0, 5.0], [0.01, 0.005])
>>> curve = DateCurve(yield_curve, origin=today)

>>> pv(cashflow_list=loan, discount_curve=curve.df, valuation_date=today)
1.562873...

Moreover, variable interest derived from float rates as given
by a forward rate curve, e.g. a `curve.cash`, are possible, too.

>>> fwd = YieldCurve.from_cash_rates.from_interpolation([today, today + '2y'], [-.005, .007])
>>> fwd = DateCurve(fwd, origin=today)
>>> spread = .001
>>> float_interest = CashFlowList.from_rate_cashflows(payment_dates, out, fixed_rate=spread, forward_curve=fwd.cash, pay_offset='2b', fixing_offset='2b')
>>> pv(cashflow_list=float_interest, discount_curve=curve.df, valuation_date=today)
8.900765...

>>> print(float_interest)
pay date      cashflow    notional  is rec      fixed rate  start date    end date      year fraction    forward rate  fixing date    forward-curve-id
----------  ----------  ----------  --------  ------------  ------------  ----------  ---------------  --------------  -------------  ------------------
20210131      1.99321      1_000.0  True             0.001  20201029      20210128           0.249151           0.007  20201027       ...
20210430      1.724893       875.0  True             0.001  20210128      20210428           0.246413           0.007  20210126       ...
20210731      1.511335       750.0  True             0.001  20210428      20210729           0.251889           0.007  20210426       ...
20211031      1.245756       625.0  True             0.001  20210729      20211028           0.249151           0.007  20210727       ...
20220131      0.996605       500.0  True             0.001  20211028      20220127           0.249151           0.007  20211026       ...
20220430      0.747454       375.0  True             0.001  20220127      20220428           0.249151           0.007  20220125       ...
20220731      0.498302       250.0  True             0.001  20220428      20220728           0.249151           0.007  20220426       ...
20221031      0.249151       125.0  True             0.001  20220728      20221027           0.249151           0.007  20220726       ...


Documentation
-------------

More docs can be found on `https://dcf.readthedocs.io <https://dcf.readthedocs.io>`_


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


