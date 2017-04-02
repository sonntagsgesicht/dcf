# -*- coding: utf-8 -*-

#  dcf (discounted cashflow)
#  -------------------------
#  A Python library for generating discounted cashflows.
#  Typical banking business methods are provided like interpolation, compounding,
#  discounting and fx.
#
#  Author:  pbrisk <pbrisk@icloud.com>
#  Copyright: 2016, 2017 Deutsche Postbank AG
#  Website: https://github.com/pbrisk/dcf
#  License: APACHE Version 2 License (see LICENSE file)


import bisect


class interpolation(object):
    def __init__(self, x_list=list(), y_list=list()):
        self.x_list = list()
        self.y_list = list()
        self.update(x_list, y_list)

    def __call__(self, x):
        raise NotImplementedError

    def __contains__(self, item):
        return item in self.x_list

    def update(self, x_list=list(), y_list=list()):
        """
        update interpolation data
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
            x_list = map(float, x_list)
            y_list = map(float, y_list)
            data = [(x, y) for x, y in zip(self.x_list, self.y_list) if x not in x_list]
            data.extend(zip(x_list, y_list))
            data = sorted(data)
            self.x_list = [float(x) for (x, y) in data]
            self.y_list = [float(y) for (x, y) in data]

    @classmethod
    def from_dict(cls, xy_dict):
        return cls(xy_dict.keys(), xy_dict.values())


class flat(interpolation):
    def __init__(self, y=0.0):
        super(flat, self).__init__([0.0], [y])

    def __call__(self, x):
        return self.y_list[0]


class no(interpolation):
    def __call__(self, x):
        return self.y_list[self.x_list.index(x)]


class zero(interpolation):
    def __call__(self, x):
        if x in self.x_list:
            return self.y_list[self.x_list.index(x)]
        else:
            return .0


class left(interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise (OverflowError, "No data points for interpolation provided.")
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect.bisect_left(self.x_list, float(x), 1, len(self.x_list)) - 1
        return self.y_list[i]


class constant(left):
    pass


class right(interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise (OverflowError, "No data points for interpolation provided.")
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect.bisect_right(self.x_list, float(x), 0, len(self.x_list) - 1)
        return self.y_list[i]


class nearest(interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise (OverflowError, "No data points for interpolation provided.")
        if len(self.y_list) == 1:
            return self.y_list[0]
        if x in self.x_list:
            i = self.x_list.index(x)
        else:
            i = bisect.bisect_left(self.x_list, float(x), 1, len(self.x_list) - 1)
            if (self.x_list[i - 1] - x) / (self.x_list[i - 1] - self.x_list[i]) < 0.5:
                i -= 1
        return self.y_list[i]


class linear(interpolation):
    def __call__(self, x):
        if len(self.y_list) == 0:
            raise (OverflowError, "No data points for interpolation provided.")
        if len(self.y_list) == 1:
            return self.y_list[0]
        i = bisect.bisect_left(self.x_list, float(x), 1, len(self.x_list) - 1)
        return self.y_list[i - 1] + (self.y_list[i] - self.y_list[i - 1]) * \
                                    (self.x_list[i - 1] - x) / (self.x_list[i - 1] - self.x_list[i])


'''

# cubic spline interpolation

import numpy as np


class Interpolator:
    def __init__(self, name, func, points, deriv=None):
        self.name = name  # used for naming the C function
        self.intervals = intervals = [ ]
        # Generate a cubic spline for each interpolation interval.
        for u, v in map(None, points[:-1], points[1:]):
            FU, FV = func(u), func(v)
            # adjust h as needed, or pass in a derivative function
            if deriv == None:
                h = 0.01
                DU = (func(u + h) - FU) / h
                DV = (func(v + h) - FV) / h
            else:
                DU = deriv(u)
                DV = deriv(v)
            denom = (u - v)**3
            A = ((-DV - DU) * v + (DV + DU) * u +
                 2 * FV - 2 * FU) / denom
            B = -((-DV - 2 * DU) * v**2  +
                  u * ((DU - DV) * v + 3 * FV - 3 * FU) +
                  3 * FV * v - 3 * FU * v +
                  (2 * DV + DU) * u**2) / denom
            C = (- DU * v**3  +
                 u * ((- 2 * DV - DU) * v**2  + 6 * FV * v
                                    - 6 * FU * v) +
                 (DV + 2 * DU) * u**2 * v + DV * u**3) / denom
            D = -(u *(-DU * v**3  - 3 * FU * v**2) +
                  FU * v**3 + u**2 * ((DU - DV) * v**2 + 3 * FV * v) +
                  u**3 * (DV * v - FV)) / denom
            intervals.append((u, A, B, C, D))

    def __call__(self, x):
        def getInterval(x, intervalList):
            # run-time proportional to the log of the length
            # of the interval list
            n = len(intervalList)
            if n < 2:
                return intervalList[0]
            n2 = n / 2
            if x < intervalList[n2][0]:
                return getInterval(x, intervalList[:n2])
            else:
                return getInterval(x, intervalList[n2:])
        # Tree-search the intervals to get coefficients.
        u, A, B, C, D = getInterval(x, self.intervals)
        # Plug coefficients into polynomial.
        return ((A * x + B) * x + C) * x + D

    def c_code(self):
        """Generate C code to efficiently implement this
        interpolator. Run the C code through 'indent' if you
        need it to be legible."""
        def codeChoice(intervalList):
            n = len(intervalList)
            if n < 2:
                return ("A=%.10e;B=%.10e;C=%.10e;D=%.10e;"
                        % intervalList[0][1:])
            n2 = n / 2
            return ("if (x < %.10e) {%s} else {%s}"
                    % (intervalList[n2][0],
                       codeChoice(intervalList[:n2]),
                       codeChoice(intervalList[n2:])))
        return ("double interpolator_%s(double x) {" % self.name +
                "double A,B,C,D;%s" % codeChoice(self.intervals) +
                "return ((A * x + B) * x + C) * x + D;}")



def Splines(data):
    np1 = len(data)
    n = np1 - 1
    X, Y = zip(*data)
    X = [float(x) for x in X]
    Y = [float(y) for y in Y]
    a = Y[:]
    b = [0.0] * (n)
    d = [0.0] * (n)
    h = [X[i + 1] - X[i] for i in xrange(n)]
    alpha = [0.0] * n
    for i in xrange(1, n):
        alpha[i] = 3 / h[i] * (a[i + 1] - a[i]) - 3 / h[i - 1] * (a[i] - a[i - 1])
    c = [0.0] * np1
    L = [0.0] * np1
    u = [0.0] * np1
    z = [0.0] * np1
    L[0] = 1.0;
    u[0] = z[0] = 0.0
    for i in xrange(1, n):
        L[i] = 2 * (X[i + 1] - X[i - 1]) - h[i - 1] * u[i - 1]
        u[i] = h[i] / L[i]
        z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / L[i]
    L[n] = 1.0;
    z[n] = c[n] = 0.0
    for j in xrange(n - 1, -1, -1):
        c[j] = z[j] - u[j] * c[j + 1]
        b[j] = (a[j + 1] - a[j]) / h[j] - (h[j] * (c[j + 1] + 2 * c[j])) / 3
        d[j] = (c[j + 1] - c[j]) / (3 * h[j])
    splines = []
    for i in xrange(n):
        splines.append((a[i], b[i], c[i], d[i], X[i]))
    return splines, X[n]


def splinesToPlot(splines, xn, res):
    n = len(splines)
    perSpline = int(res / n)
    if perSpline < 3: perSpline = 3
    X = []
    Y = []
    for i in xrange(n - 1):
        S = splines[i]
        x0 = S[4]
        x1 = splines[i + 1][4]
        x = np.linspace(x0, x1, perSpline)
        for xi in x:
            X.append(xi)
            h = (xi - S[4])
            Y.append(S[0] + S[1] * h + S[2] * h ** 2 + S[3] * h ** 3)
    S = splines[n - 1]
    x = np.linspace(S[4], xn, perSpline)
    for xi in x:
        X.append(xi)
        h = (xi - S[4])
        Y.append(S[0] + S[1] * h + S[2] * h ** 2 + S[3] * h ** 3)

    return X, Y


if '__main__' in __name__:
    x = lambda n: np.linspace(-1, 1, n)
    f = lambda x: np.cos(np.sin(np.pi * x))
    n = 5
    E = 200
    data = zip(x(n), f(x(n)))
    splines, xn = Splines(data)
    X, Y = splinesToPlot(splines, xn, E)
    import matplotlib as mpl

    mpl.use("TkAgg")
    import matplotlib.pylab as plt

    plt.ion()
    plt.plot(X, Y, 'r--')
    plt.plot(x(300), f(x(300)), 'k')

    import time
    time.sleep(10)

'''
