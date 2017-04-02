
--------
Tutorial
--------

.. toctree::


First setup basic objects
=========================

Setup model imports

    >>> from datetime import date
    >>> from businessdate import BusinessDate, BusinessPeriod, BusinessRange, BusinessSchedule


Simplest example possible

.. code-block:: python

    >>> BusinessDate.from_date(date(2014, 1, 1)) == BusinessDate(20140101)
    True

    >>> BusinessDate(20140101) + '1y6m'
    20150701

    >>> BusinessDate(20140101).adjust_follow()
    20140102

    >>> BusinessPeriod('1Y')==BusinessPeriod(years=1)
    True

    >>> BusinessPeriod('1Y')
    1Y

    >>> BusinessPeriod('1Y').add_businessdays(3)
    1Y3B

    >>> BusinessPeriod('1Y') + '1y6m'
    1Y6M

    >>> sd = BusinessDate(20151231)
    >>> ed = BusinessDate(20201231)
    >>> BusinessRange(sd, ed, '1y', ed)
    [20151231, 20161231, 20171231, 20181231, 20191231]

    >>> BusinessSchedule(sd, ed, '1y', ed)
    [20151231, 20161231, 20171231, 20181231, 20191231, 20201231]

    >>> BusinessSchedule(sd, ed, '1y', ed).first_stub_long()
    [20151231, 20171231, 20181231, 20191231, 20201231]
