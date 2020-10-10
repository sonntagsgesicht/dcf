# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import bisect
import math


class base_interpolation(object):
    """
    Basic class to interpolate given data.
    """

    def __init__(self, x_list=list(), y_list=list()):
        self.x_list = list()
        self.y_list = list()
        self._update(x_list, y_list)

    def __call__(self, x):
        raise NotImplementedError

    def __contains__(self, item):
        return item in self.x_list

    def _update(self, x_list=list(), y_list=list()):
        """
        _update interpolation data
        :param list(float) x_list: x values
        :param list(float) y_list: y values
        """
        if not y_list:
            for x in x_list:
                if x in self.x_list:
                    i = self.x_list.index(float(x))
                    self.x_list.pop(i)
                    self.y_list.pop(i)
        else:
            x_list = list(map(float, x_list))
            y_list = list(map(float, y_list))
            data = [(x, y) for x, y in zip(self.x_list, self.y_list) if x not in x_list]
            data.extend(list(zip(x_list, y_list)))
            data = sorted(data)
            self.x_list = [float(x) for (x, y) in data]
            self.y_list = [float(y) for (x, y) in data]

    @classmethod
    def from_dict(cls, xy_dict):
        return cls(sorted(xy_dict), (xy_dict[k] for k in sorted(xy_dict)))


class flat(base_interpolation):
    def __init__(self, y=0.0):
        super(flat, self).__init__([0.0], [y])

    def __call__(self, x):
        return self.y_list[0]


class no(base_interpolation):
    def __call__(self, x):
        return self.y_list[self.x_list.index(x)]


class zero(base_interpolation):
    """
    interpolates by filling with zeros
    """

    def __call__(self, x):
        if x in self.x_list:
            return self.y_list[self.x_list.index(x)]
        else:
            return .0


class left(base_interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect.bisect_left(self.x_list, float(x), 1, len(self.x_list)) - 1
        return self.y_list[i]


class constant(left):  # why is is this derived from class left and not from interpolation itself
    pass


class right(base_interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect.bisect_right(self.x_list, float(x), 0, len(self.x_list) - 1)
        return self.y_list[i]


class nearest(base_interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError
        if len(self.y_list) == 1:
            return self.y_list[0]
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect.bisect_left(self.x_list, float(x), 1, len(self.x_list) - 1)
            if (self.x_list[i - 1] - x) / (self.x_list[i - 1] - self.x_list[i]) < 0.5:
                i -= 1
        return self.y_list[i]


class linear(base_interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise OverflowError
        if len(self.y_list) == 1:
            return self.y_list[0]
        i = bisect.bisect_left(self.x_list, float(x), 1, len(self.x_list) - 1)
        return self.y_list[i - 1] + (self.y_list[i] - self.y_list[i - 1]) * \
                                    (self.x_list[i - 1] - x) / (self.x_list[i - 1] - self.x_list[i])


class loglinear(linear):
    def __init__(self, x_list=list(), y_list=list()):
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values.')
        log_y_list = [math.log(y) for y in y_list]
        super(loglinear, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        log_y = super(loglinear, self).__call__(x)
        return math.exp(log_y)


class negloglinear(linear):
    def __init__(self, x_list=list(), y_list=list()):
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values.')
        log_y_list = [-math.log(y) for y in y_list]
        super(negloglinear, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        log_y = super(negloglinear, self).__call__(x)
        return math.exp(-log_y)


class logconstant(constant):
    def __init__(self, x_list=list(), y_list=list()):
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values.')
        log_y_list = [math.log(y) for y in y_list]
        super(logconstant, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        log_y = super(logconstant, self).__call__(x)
        return math.exp(log_y)


class neglogconstant(constant):
    def __init__(self, x_list=list(), y_list=list()):
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values.')
        log_y_list = [-math.log(y) for y in y_list]
        super(neglogconstant, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        log_y = super(neglogconstant, self).__call__(x)
        return math.exp(-log_y)


class loglinearrate(linear):
    def __init__(self, x_list=list(), y_list=list()):
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values. Got %s' % str(y_list))
        z = [x for x in x_list if not x]
        self._y_at_zero = y_list[x_list.index(z[0])] if z else None
        log_y_list = [-math.log(y) / x for x, y in zip(x_list, y_list) if x]
        x_list = [x for x in x_list if x]
        super(loglinearrate, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        if not x:
            return self._y_at_zero
        log_y = super(loglinearrate, self).__call__(x)
        return math.exp(-log_y * x)


class logconstantrate(constant):
    def __init__(self, x_list=list(), y_list=list()):
        if not all(0. < y for y in y_list):
            raise ValueError('log interpolation requires positive values.')
        z = [x for x in x_list if not x]
        self._y_at_zero = y_list[x_list.index(z[0])] if z else None
        log_y_list = [-math.log(y) / x for x, y in zip(x_list, y_list) if x]
        x_list = [x for x in x_list if x]
        super(logconstantrate, self).__init__(x_list, log_y_list)

    def __call__(self, x):
        if not x:
            return self._y_at_zero
        log_y = super(logconstantrate, self).__call__(x)
        return math.exp(-log_y * x)


class squaredconst(constant):
    def __init__(self, x_list=list(), y_list=list()):
        sqrd_y_list = [y * y for y in y_list]
        super(squaredconst, self).__init__(x_list, sqrd_y_list)

    def __call__(self, x):
        sqrd_y = super(squaredconst, self).__call__(x)
        return math.sqrt(sqrd_y)


class squaredlinear(linear):
    def __init__(self, x_list=list(), y_list=list()):
        sqrd_y_list = [y * y for y in y_list]
        super(squaredlinear, self).__init__(x_list, sqrd_y_list)

    def __call__(self, x):
        sqrd_y = super(squaredlinear, self).__call__(x)
        return math.sqrt(sqrd_y)


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
