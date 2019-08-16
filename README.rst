=========================
dcf (discounted cashflow)
=========================

.. image:: https://img.shields.io/codeship/a10d1dd0-a1a0-0137-f00d-1a3bc2cae4aa/master.svg
   :target: https://codeship.com//projects/359976
   :alt: Codechip

.. image:: https://img.shields.io/readthedocs/dcf
   :target: http://dcf.readthedocs.io
   :alt: Read the Docs

.. image:: https://img.shields.io/codefactor/grade/github/sonntagsgesicht/dcf/master
   :target: https://www.codefactor.io/repository/github/sonntagsgesicht/dcf
   :alt: CodeFactor Grade

.. image:: https://img.shields.io/codeclimate/maintainability/sonntagsgesicht/dcf
   :target: https://codeclimate.com/github/sonntagsgesicht/dcf/maintainability
   :alt: Code Climate maintainability

.. image:: https://img.shields.io/codeclimate/coverage/sonntagsgesicht/dcf
   :target: https://codeclimate.com/github/sonntagsgesicht/dcf/test_coverage
   :alt: Code Climate Coverage

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

A Python library for generating discounted cashflows.
Typical banking business methods are provided like interpolation, compounding,
discounting and fx.


Example Usage
-------------

.. code-block:: python

    from dcf import ZeroRateCurve

    >>> ZeroRateCurve([20140101, 20160101], [.03, .05]).get_zero_rate(20140101, 20150101)
    0.04


Install
-------

The latest stable version can always be installed or updated via pip:

.. code-block:: bash

    $ pip install dcf


Examples
--------

.. code-block:: python

    # Simplest example possible


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


