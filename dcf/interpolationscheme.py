# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from .interpolation import base_interpolation, constant, linear


class interpolation_scheme(object):

    _interpolation = constant, linear, constant

    def __init__(self, domain, data, interpolation=None):
        r"""
        Curve object to build function

        :param list(float) domain: source values
        :param list(float) data: target values
        :param function interpolation: interpolation function on x_list (optional)
            or triple of (left, mid, right) interpolation functions with
            left for x < x_list[0] (as default triple.right is used)
            right for x > x_list][-1] (as default constant is used)
            mid else (as default linear is used)

        Curve object to build function :math:`f:R \rightarrow R, x \mapsto y`
        from finite point vectors :math:`x` and :math:`y`
        using piecewise various interpolation functions.
        """

        if not interpolation:
            interpolation = self.__class__._interpolation

        y_left, y_mid, y_right = self.__class__._interpolation
        if isinstance(interpolation, (tuple, list)):
            if len(interpolation) == 3:
                y_left, y_mid, y_right = interpolation
            elif len(interpolation) == 2:
                y_mid, y_right = interpolation
                y_left = y_right
            elif len(interpolation) == 1:
                y_mid, = interpolation
            else:
                raise ValueError
        elif issubclass(interpolation, base_interpolation):
            y_mid = interpolation
        else:
            raise AttributeError

        if not len(domain) == len(data):
            raise AssertionError()
        if not len(domain) == len(set(domain)):
            raise AssertionError()

        #: Interpolation:
        self._y_mid = y_mid(domain, data)
        self._y_right = y_right(domain, data)
        self._y_left = y_left(domain, data)

    def __call__(self, x):
        y = 0.0
        if x < self._y_left.x_list[0]:
            # extrapolate to left
            y = self._y_left(x)
        elif x > self._y_right.x_list[-1]:
            # extrapolate to right
            y = self._y_right(x)
        else:
            # interpolate in the middle
            y = self._y_mid(x)
        return y

def dyn_scheme(left, mid, right):
    name = left.__name__ + '_' + mid.__name__ + '_' + right.__name__
    return type(name, (interpolation_scheme,), {'_interpolation': (left, mid, right)})
