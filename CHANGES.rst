
These changes are listed in decreasing version number order.

Release 0.7
===========

Release date was |today|

* added |Curve().kwargs| to clone and persist object
* added |ForwardCurve()| for asset forwards like stocks or commodities
* added |FxForwardCurve()| for fx forwards rates
* added |CashFlowList().kwargs| to clone and persist object
* added |dcf.cashflows.contingent| for option pricing
* added various standard option pricing formulas |dcf.models|
  incl. digital or binary versions like

  * *Bachelier* as |NormalOptionPayOffModel()|
  * *Black-Scholes* resp. *Black76* as |LogNormalOptionPayOffModel()|
  * *displaced Black76* as |DisplacedLogNormalOptionPayOffModel()|
  * as well as an intrinsic version |IntrinsicOptionPayOffModel()|

* modified |get_present_value()| to word with |OptionPayOffModel()|
* removed |get_fair_rate()| alias *get_par_rate()*
* removed submodules *dcf.data*
* added submodules |dcf.cashflows.payoffs|
* added pricer routine |get_curve_fit()|
* added |RateCurve().spread|

Release 0.6
===========

Release date was Friday, 14 January 2022

* added |FixedCashFlowList().table| and |RateCashFlowList().table|

* added new module |dcf.daycount| and updated |day_count()|
    to default to year fractions in case of simple float inputs

* added |get_bucketed_delta()|

* added submodules *dcf.data*, *dcf.cashflows.products* and *dcf.curves.plot*
  (under construction)


Release 0.5
===========

Release date was November 22, 2021

* added |get_basis_point_value()|


Release 0.4
===========

Release date was October 11, 2020

* dropping support for python 2 incl. 2.7

* new casting concept for curves, old `curve_instance.cast(TypeToCastTo)` is replaced by `TypeToCastTo(curve_instance)`

* restructuring cashflow lists, see |dcf.cashflows.cashflow|

* adding payment plans, see |dcf.plans|

* adding pricing functions, e.g. |get_present_value()|, |get_yield_to_maturity()|, *get_par_rate()*, ...

* more docs

* more tests


Release 0.3
===========

Release date was September 18, 2019


* migration to python 3.4, 3.5, 3.6 and 3.7

* automated code review

* more docs

* supporting third party (e.g.) interpolation

* adding travis ci

* update for auxilium tools

* replaced `assert stmt` by `if not stmt: raise AssertionError()` (bandit recommendation)


Release 0.2
===========

Release date was March 3, 2017


Release 0.1
===========

Release date was December 31, 2016