.. currentmodule:: dcf

To start with import the package.

Cashflow Objects and Valuation
==============================

Payment Plans
-------------

    >>> from businessdate import BusinessDate, BusinessSchedule

    >>> today = BusinessDate(20201031)

    >>> schedule = BusinessSchedule(today, today + "8q", step="1q")
    >>> schedule
    [BusinessDate(20201031), BusinessDate(20210131), BusinessDate(20210430), BusinessDate(20210731), BusinessDate(20211031), BusinessDate(20220131), BusinessDate(20220430), BusinessDate(20220731), BusinessDate(20221031)]

To build payment plans for, e.g. annuity loans, pick a plan function
and generate an redemption amount list for paying back the loan notional amount.

.. doctest::

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

CashFlowList Objects
--------------------

Putting all together and feeding the plan into a `CashFlowList
and the list of outstanding into a `CashflowList` gives the legs of a loan.

.. doctest::

    >>> from businessdate import BusinessDate, BusinessSchedule
    >>> from dcf.plans import amortize, outstanding
    >>> from dcf import CashFlowList

Again, build a date schedule.

.. doctest::

    >>> today = BusinessDate(20201031)

    >>> schedule = BusinessSchedule(today, today + "8q", step="1q")

    >>> start_date, payment_dates = schedule[0], schedule[1:]

Fixing the properties of the product and rolling out the payment plan and list of notional outstanding.

.. doctest::

    >>> number_of_payments = 8
    >>> interest_rate = 0.01
    >>> notional = 1000.

    >>> plan = amortize(number_of_payments, amount=notional)
    >>> out = outstanding(plan, amount=notional)

Finally, create for each leg a |CashFlowList|.

.. doctest::

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

Valuation
---------

Add those legs to |CashFlowList| provides a smart container for valuation.

.. doctest::

    >>> from yieldcurves import YieldCurve, DateCurve
    >>> from dcf import pv

    >>> loan = -principal + redemption + interest
    >>> yield_curve = YieldCurve.from_interpolation([0.0, 5.0], [0.01, 0.005])
    >>> curve = DateCurve(yield_curve, origin=today)
    >>> pv(cashflow_list=loan, discount_curve=curve.df, valuation_date=today)
    1.562873826...

    >>> print(loan)
    pay date         cashflow    notional  is rec      fixed rate  start date    end date      year fraction
    ----------  -------------  ----------  --------  ------------  ------------  ----------  ---------------
    20201031    -1_000.0
    20210131       125.0
    20210430       125.0
    20210731       125.0
    20211031       125.0
    20220131       125.0
    20220430       125.0
    20220731       125.0
    20221031       125.0
    20210131         2.518892     1_000.0  True              0.01  20201031      20210131           0.251889
    20210430         2.13216        875.0  True              0.01  20210131      20210430           0.243675
    20210731         1.889169       750.0  True              0.01  20210430      20210731           0.251889
    20211031         1.574307       625.0  True              0.01  20210731      20211031           0.251889
    20220131         1.259446       500.0  True              0.01  20211031      20220131           0.251889
    20220430         0.913783       375.0  True              0.01  20220131      20220430           0.243675
    20220731         0.629723       250.0  True              0.01  20220430      20220731           0.251889
    20221031         0.314861       125.0  True              0.01  20220731      20221031           0.251889
