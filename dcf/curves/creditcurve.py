# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from sys import float_info

from .curve import RateCurve
from dcf.compounding import continuous_compounding, continuous_rate
from dcf.interpolation import constant, linear_scheme, log_linear_scheme, \
    log_linear_rate_scheme


class CreditCurve(RateCurve):
    r"""Base class of credit curve classes

    All credit curves share the same three fundamental methodological methods

    * |CreditCurve().get_survival_prob()|

    * |CreditCurve().get_flat_intensity()|

    * |CreditCurve().get_hazard_rate()|

    All subclasses differ only in data types for storage and interpolation.

    """
    _FORWARD_TENOR = '1Y'

    @staticmethod
    def _get_storage_value(curve, x):
        raise NotImplementedError()

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        if isinstance(domain, RateCurve):
            # if argument is a curve add extra curve points to domain
            # for better approximation
            if data:
                raise TypeError("If first argument is %s, "
                                "data argument must not be given." %
                                domain.__class__.__name__)
            data = domain
            domain = sorted(set(list(data.domain) + [max(data.domain) + '1y']))
        super(CreditCurve, self).__init__(domain, data, interpolation, origin,
                                          day_count, forward_tenor)

    def get_survival_prob(self, start, stop=None):
        r"""survival probability of credit curve

        :param start: start point in time $t_0$ of period
        :param stop: end point $t_1$ of period
            (optional, if not given $t_0$ will be **origin**
            and $t_1$ taken from **start**)
        :return: survival probability $sv(t_0, t_1)$
            for period $t_0$ to $t_1$

        Assume an uncertain event $\chi$,
        e.g. occurrence of a credit default event
        such as a loan borrower failing to fulfill the obligation
        to pay back interest or redemption.

        Let $\iota_\chi$ be the point in time when the event $\chi$ happens.

        Then the survival probability $sv(t_0, t_1)$
        is the probability of not occurring $\chi$ until $t_1$ if
        $\chi$ didn't happen until $t_0$, i.e.

        $$sv(t_0, t_1) = 1 - P(t_0 < \iota_\chi \leq t_1)$$

        * similar to |InterestRateCurve().get_discount_factor()|

        """
        if stop is None:
            return self.get_survival_prob(self.origin, start)
        return self._get_compounding_factor(start, stop)

    def get_flat_intensity(self, start, stop=None):
        r"""intensity value of credit curve

        :param start: start point in time $t_0$ of intensity
        :param stop: end point $t_1$  of intensity
            (optional, if not given $t_0$ will be **origin**
            and $t_1$ taken from **start**)
        :return: intensity $\lambda(t_0, t_1)$

        The intensity $\lambda(t_0, t_1)$ relates to survival probabilities by

        $$sv(t_0, t_1) = exp(-\lambda(t_0, t_1) \cdot \tau(t_0, t_1)).$$

        * similar to |InterestRateCurve().get_zero_rate()|

        """
        if stop is None:
            return self.get_flat_intensity(self.origin, start)
        return self._get_compounding_rate(start, stop)

    def get_hazard_rate(self, start):
        r"""hazard rate of credit curve

        :param start: point in time $t$ of hazard rate
        :return: hazard rate $hz(t)$

        The hazard rate $hz(t)$ relates to intensities by

        $$\lambda(t_0, t_1) = \int_{t_0}^{t_1} hz(t)\ dt.$$

        * similar to |InterestRateCurve().get_short_rate()|

        """

        return self._get_hazard_rate(start)

    def _get_hazard_rate(self, start):  # aka get_short_rate

        if start < min(self.domain):
            return self.get_hazard_rate(min(self.domain))
        if max(self.domain) <= start:
            return self.get_hazard_rate(
                max(self.domain) - self._TIME_SHIFT)

        previous = max(d for d in self.domain if d <= start)
        follow = min(d for d in self.domain if start < d)
        if not previous <= start <= follow:
            raise AssertionError()
        if not previous < follow:
            raise AssertionError(list(map(str, (previous, start, follow))))
        return self.get_flat_intensity(previous, follow)


class ProbabilityCurve(CreditCurve):
    r"""base class of probability based credit curve classes"""

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        # validate probabilities
        if not isinstance(data, RateCurve):
            data = [max(float_info.min, min(d, 1. - float_info.min)) for d in
                    data]
            if not all(data):
                raise ValueError('Found non positive survival probabilities.')
        # if argument is a curve add extra curve points to domain
        # for better approximation
        if isinstance(domain, RateCurve):
            if data:
                raise TypeError("If first argument is %s, "
                                "data argument must not be given." %
                                domain.__class__.__name__)
            data = domain
            origin = data.origin if origin is None else origin
            domain = sorted(set(list(data.domain) + [origin + '1d',
                                                     max(data.domain) + '1y']))
        super(ProbabilityCurve, self).__init__(domain, data, interpolation,
                                               origin, day_count,
                                               forward_tenor)


class SurvivalProbabilityCurve(ProbabilityCurve):
    r"""Interest rate curve storing and interpolating data as discount factor

    $$sv(0, t)=y_t$$

    """
    _INTERPOLATION = log_linear_rate_scheme

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(curve.origin, x)

    def _get_compounding_factor(self, start, stop):
        if start is self.origin:
            return self(stop)
        if start == stop:
            return 1. if 2 * float_info.min <= self(start) else 0.
        return self(stop) / self(start)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            # intensity proxi at origin
            stop = min(d for d in self.domain if self.origin < d)
            # todo:
            #  calc left extrapolation (for linear zero rate interpolation)
        return super(SurvivalProbabilityCurve, self)._get_compounding_rate(
            start, stop)


class DefaultProbabilityCurve(SurvivalProbabilityCurve):
    r"""Credit curve storing and interpolating data as default probability

    $$pd(0, t)=1-sv(0, t)=y_t$$

    """
    _INTERPOLATION = log_linear_rate_scheme

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(curve.origin, x)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        if not isinstance(data, RateCurve):
            data = [1. - d for d in data]
        super(DefaultProbabilityCurve, self).__init__(domain, data,
                                                      interpolation, origin,
                                                      day_count, forward_tenor)


class FlatIntensityCurve(CreditCurve):
    r"""Credit curve storing and interpolating data as intensities

    $$\lambda(t)=y_t$$

    """
    _INTERPOLATION = linear_scheme

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_flat_intensity(curve.origin, x)

    def _get_compounding_rate(self, start, stop):
        if start == stop == self.origin:
            return self(self.origin)
        if start is self.origin:
            return self(stop)
        if start == stop:
            return self._get_compounding_rate(
                start, start + self.__class__._time_shift)

        s = self(start) * self.day_count(self.origin, start)
        e = self(stop) * self.day_count(self.origin, stop)
        t = self.day_count(start, stop)
        return (e - s) / t


class HazardRateCurve(CreditCurve):
    r"""Credit curve storing and interpolating data as hazard rate

    $$hz(t)=y_t$$

    """
    _INTERPOLATION = constant

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_hazard_rate(x)

    def _get_compounding_rate(self, start, stop):
        if start == stop:
            return self(start)

        current = start
        rate = 0.0
        step = self._TIME_SHIFT

        while current + step < stop:
            rate += self(current) * self.day_count(current, current + step)
            current += step

        rate += self(current) * self.day_count(current, stop)
        return rate / self.day_count(start, stop)

    def _get_hazard_rate(self, start):  # aka get_short_rate
        return self(start)


class MarginalSurvivalProbabilityCurve(ProbabilityCurve):
    r"""Credit curve storing and interpolating data as intensities

    $$sv(t, t+\tau^*)=y_t$$

    """
    _INTERPOLATION = log_linear_scheme

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(x, x + curve.forward_tenor)

    def _get_compounding_factor(self, start, stop):
        if start == stop:
            return 1. if 2 * float_info.min <= self(start) else 0.

        current = start
        df = 1.0
        step = self.forward_tenor
        while current + step < stop:
            df *= self(current) if 2 * float_info.min <= self(current) else 0.
            current += step

        if 2 * float_info.min <= self(current):
            r = continuous_rate(self(current),
                                self.day_count(current, current + step))
            df *= continuous_compounding(r, self.day_count(current, stop))
        else:
            df *= 0.
        return df

    def _get_hazard_rate(self, start):  # aka get_short_rate
        if start < min(self.domain):
            return self.get_hazard_rate(min(self.domain))
        if max(self.domain) <= start:
            return self.get_flat_intensity(
                max(self.domain),
                max(self.domain) + self._TIME_SHIFT)

        previous = max(d for d in self.domain if d <= start)
        follow = min(d for d in self.domain if start < d)
        if not previous < follow:
            raise AssertionError(list(map(str, (previous, start, follow))))
        if not previous <= start <= follow:
            raise AssertionError(list(map(str, (previous, start, follow))))

        return self.get_flat_intensity(previous, follow)


class MarginalDefaultProbabilityCurve(MarginalSurvivalProbabilityCurve):
    r"""Credit curve storing and interpolating data
    as marginal default probability

    $$pd(t, t+\tau^*)=1-sv(t, t+\tau^*)=y_t$$

    """
    _INTERPOLATION = log_linear_scheme

    @staticmethod
    def _get_storage_value(curve, x):
        return curve.get_survival_prob(x, x + curve.forward_tenor)

    def __init__(self, domain=(), data=(), interpolation=None, origin=None,
                 day_count=None, forward_tenor=None):
        if not isinstance(data, RateCurve):
            data = [1. - d for d in data]
        super(MarginalDefaultProbabilityCurve, self).__init__(
            domain, data, interpolation, origin, day_count, forward_tenor)
