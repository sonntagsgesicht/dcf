=========================
dcf (discounted cashflow)
=========================

.. image:: https://img.shields.io/codeship/9d5f1200-9cf4-0134-bcff-6ae80fc9d0de/master.svg
    :target: https://codeship.com//projects/188495

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

    $ pip install businessdate

If the above fails, please try easy_install instead:

.. code-block:: bash

    $ easy_install businessdate


Examples
--------

.. code-block:: python

    # Simplest example possible


Development Version
-------------------

The latest development version can be installed directly from GitHub:

.. code-block:: bash

    $ pip install --upgrade git+https://github.com/pbrisk/dcf.git


Contributions
-------------

.. _issues: https://github.com/pbrisk/dcf/issues
.. __: https://github.com/pbrisk/dcf/pulls

Issues_ and `Pull Requests`__ are always welcome.


License
-------

.. __: https://github.com/pbrisk/dcf/raw/master/LICENSE

Code and documentation are available according to the Apache Software License (see LICENSE__).


