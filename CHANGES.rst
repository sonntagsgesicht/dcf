
These changes are listed in decreasing version number order.

Release 0.4
===========

Release date was |today|

# dropping support for python 2 incl. 2.7

# new casting concept for curves, old `curve_instance.cast(TypeToCastTo)` is replaced by `TypeToCastTo(curve_instance)`

# restructuring cashflow lists, see |cashflow|

# adding payment plans, see |plans|

# adding pricing functions, e.g. |get_present_value()|, |get_yield_to_maturity()|, |get_par_rate()|, ...

# more docs

# more tests


Release 0.3
===========

Release date was September 18, 2019


# migration to python 3.4, 3.5, 3.6 and 3.7

# automated code review

# more docs

# supporting third party (e.g.) interpolation

# adding travis ci

# update for auxilium tools

# replaced `assert stmt` by `if not stmt: raise AssertionError()` (bandit recommendation)


Release 0.2
===========

Release date was March 3, 2017


Release 0.1
===========

Release date was December 31, 2016