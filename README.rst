
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

A Python library for generating discounted cashflows *(dcf)*.
Typical banking business methods are provided like interpolation, compounding,
discounting and fx.


Example Usage
-------------

.. code-block:: python

    from datetime import date
    from dcf import ZeroRateCurve

    >>> start = date(2014,1,1)
    >>> mid = date(2015,1,1)
    >>> end = date(2016,1,1)

    >>> ZeroRateCurve([start, end], [.03, .05]).get_zero_rate(start, mid)
    0.04

    >>> ZeroRateCurve([start, end], [.03, .05]).get_discount_factor(start, mid)
    0.9607894392


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


