# -*- coding: utf-8 -*-

#  dcf (discounted cashflow)
#  -------------------------
#  A Python library for generating discounted cashflows.
#  Typical banking business methods are provided like interpolation, compounding,
#  discounting and fx.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Copyright: 2016, 2017 Deutsche Postbank AG
#  Website: https://github.com/pbrisk/dcf
#  License: APACHE Version 2 License (see LICENSE file)


import math
import sys

'''
functions to convert hazard rate into intensity, survival probability, conditional forward survival probability
 and vica versa
'''


def forward_pd_from_hazard_rate(x_value, x_list, y_list):
    r""" calculates forward pd from hazard rate

    Parameters:
        x_value (float): time value
        x_list (list of float): list of time pillars
        y_list (list of float): list of hazard rate

    Returns:
        float: forward pd at x_value

    Calculates forward pd from hazard rate as :math:`1 - \exp( - \int_{t}^{t+1} h(x_{value}) dx )`
    and for piecewise constant :math:`h` for :math:`h(t_i) = h_i` for :math:`t_0 \dots t_n`

        .. math::
            f_i = 1 - \exp( - h_i )

    with :math:`h_0 = h_1` for :math:`t_0 = 0`.

    """

    return 1 - math.exp(-1.0 * y_list[x_list.index(x_value)])


def hazard_rate_from_forward_pd(x_value, x_list, y_list):
    r""" calculates hazard rate from forward pd

    Parameters:
        x_value (float): time value
        x_list (list of float): list of time pillars
        y_list (list of float): list of  forward pd

    Returns:
        float: hazard rate at x_value

    Calculates hazard rate from forward pd as :math:`\frac{d}{dt}-\frac{ \log(1 - f(t)) }{ t }`
    and for piecewise constant :math:`f` with :math:`f(t_i) = f_i` for :math:`t_0 \dots t_n`

        .. math::
            h_i = - \log(1 - f_i)

    with :math:`f_0 = f_1` for :math:`t_0=0`.

    """

    y = 1.0 - y_list[x_list.index(x_value)]
    if y < sys.float_info.epsilon:
        # todo better fallback in default
        return 0.0
    if y == 1.0:
        return 0.0
    return -1.0 * math.log(y)


def intensity_from_hazard_rate(x_value, x_list, y_list):
    r""" calculates intensity from hazard rate list

    Parameters:
        x_value (float): time value
        x_list (list of float): list of time pillars
        y_list (list of float): list of hazard rates

    Returns:
        float: intensity at x_value

    Calculates intensity from hazard rate list as :math:`\frac{1}{t} \int_0^{t} h(x_{value}) dx` and
    for piecewise constant

        .. math::
            \lambda_j = \frac{1}{t_j}\sum_{i < j} h_i ( t_{i+1} - t_i )

    with :math:`h_0 = h_1` for :math:`t_0=0`.

    """

    if x_value < sys.float_info.epsilon:
        return y_list[0]
    else:
        i = x_list.index(x_value)
    delta_x_list = [e - s for s, e in zip(x_list[0:i], x_list[1:i + 1])]
    y = [h * t for h, t in zip(y_list[0:i], delta_x_list)]
    return sum(y) / x_value


def hazard_rate_from_intensity(x_value, x_list, y_list):
    r""" calculates hazard rate from intensity

    Parameters:
        x_value (float): time value
        x_list (list of float): list of time pillars
        y_list (list of float): list of intensities

    Returns:
        float: hazard rate at x_value

    Calculates hazard rate from intensity as :math:`\frac{d}{dt} \lambda(t) t` and for piecewise constant

        .. math::
            h_i = \frac{ \lambda_{i+1} t_{i+1} - \lambda_i t_i }{ t_{i+1} - t_i }

    with :math:`\lambda_0 = 0` for :math:`t_0=0`.

    """

    if x_value < sys.float_info.epsilon:
        return y_list[0]
    else:
        i = x_list.index(x_value)
    if not i + 1 < len(x_list):
        i = len(x_list) - 2
    y = y_list[i + 1] * x_list[i + 1] - y_list[i] * x_list[i]
    return y / (x_list[i + 1] - x_list[i])


def survival_from_forward_pd(x_value, x_list, y_list):
    r""" calculates survival probability from forward pd

    Parameters:
        x_value (float): time value
        x_list (list of float): list of time pillars
        y_list (list of float): list of forward pd

    Returns:
        float: survival probability at x_value

    Calculates survival probability from forward pd as

        .. math::
            s_j = \prod_{i \leq j} 1 - f_i (t_{i+1} - t_i)

    with :math:`f_0 = f_1` for :math:`t_0=0`.

    """

    if x_value < sys.float_info.epsilon:
        return 1.0
    else:
        i = x_list.index(x_value)
    delta_x_list = [e - s for s, e in zip(x_list[0:i], x_list[1:i + 1])]
    y = 1.0
    for f, t in zip(y_list[0:i], delta_x_list):
        y *= (1.0 - f * t)
    return y


def forward_from_survival(x_value, x_list, y_list):
    r""" calculates forward pd from survival probability

    Parameters:
        x_value (float):            time value
        x_list (list of float):     list of time pillars
        y_list (list of float):     list of survival probabilities

    Returns:
        float: forward pd at x_value

    Calculates forward pd from survival probability as

        .. math::
             f_i = 1 - \frac{s_{i+1}}{s_i(t_{i+1}-t_i)}

    with :math:`s_0 = 1` for :math:`t_0=0`.

    """

    if x_value < sys.float_info.epsilon:
        i = 0
    else:
        i = x_list.index(x_value)
    if not i + 1 < len(x_list):
        i = len(x_list) - 2
    return (1.0 - y_list[i + 1] / y_list[i]) / (x_list[i + 1] - x_list[i])


def survival_from_intensity(x_value, x_list, y_list):
    r""" calculates survival probability from intensity

    Parameters:
        x_value (float): time value
        x_list (list of float): list of time pillars
        y_list (list of float): list of intensities

    Returns:
        float: survival probability at x_value

    Calculates survival probability from intensity as :math:`\exp( -\lambda(t) t )` and for piecewise constant

        .. math::
            s_i = \exp( -\lambda_i t_i )

    with :math:`\lambda_0 = 0` for :math:`t_0=0`.

    """

    if x_value < sys.float_info.epsilon:
        return 1.0
    else:
        i = x_list.index(x_value)
    return math.exp(-1.0 * y_list[i] * x_value)


def intensity_from_survival(x_value, x_list, y_list):
    r""" calculates intensity from survival probability

    Parameters:
        x_value (float):            time value
        x_list (list of float):     list of time pillars
        y_list (list of float):     list of survival probabilities

    Returns:
        float: intensity at x_value

    Calculates intensity from survival probability as :math:`-\frac{ \log(s(t)) }{ t }` and for piecewise constant

        .. math::
            \lambda_i = -\frac{ \log(s_i) }{ t_i }

    with :math:`s_0 = 1` for :math:`t_0=0`.

    """

    if x_value < sys.float_info.epsilon:
        if y_list[0] > sys.float_info.epsilon:
            y = 1.0 - (1.0 - y_list[1] / y_list[0]) / (x_list[1] - x_list[0])
            if y < sys.float_info.epsilon:
                return 0.0
            return -1.0 * math.log(y)
        else:
            return 1.0
    else:
        i = x_list.index(x_value)
    y = y_list[i]
    if y < sys.float_info.epsilon:
        return 1.0
    if y == 1.0:
        return 0.0
    return -1.0 * math.log(y) / x_value

