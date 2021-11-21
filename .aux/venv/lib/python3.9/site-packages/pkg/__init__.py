# -*- coding: utf-8 -*-


import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

__doc__ = '<doc>'
__license__ = 'Apache License 2.0'

__author__ = '<author>'
__email__ = '<email>'
__url__ = '<url>'

__date__ = '<date>'
__version__ = '0.1'
__dev_status__ = '3 - Alpha'  # '4 - Beta'  or '5 - Production/Stable'

__dependencies__ = ()
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()
__theme__ = ''

# this is just an example to demonstrate the auxilium workflow
# it can be removed safely


class Line(object):
    r""" This a example class (by auxilium)

    The |Line| objects implements a straight line,
    i.e. a function $y = f(x)$ with

    $$  f(x) = a + b \\cdot x  $$

    where $a$ and $b$ are numbers.

    >>> from <name> import Line
    >>> a, b = 1, 2
    >>> line = Line(a, b)
    >>> line.y(x=3)
    7
    >>> line(3)  # Line objects are callable
    7
    >>> line.a
    1
    >>> line.b
    2

    """
    def __init__(self, a=0, b=1):
        self._a = a
        self._b = b

    @property
    def a(self):
        """ a value """
        return self._a

    @property
    def b(self):
        """ b value """
        return self._b

    def y(self, x=1):
        """ gives y value depending on x value argument

        :param x: x value
        :return: $a + b * x$

        """
        return self._a + self._b * x

    def __call__(self, x=1):
        return self.y(x)
