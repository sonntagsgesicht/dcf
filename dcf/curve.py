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


from math import exp, log
import interpolation
import compounding


def _day_count(start, end):
    if hasattr(start, 'diff_in_years'):
        # duck typing businessdate.BusinessDate.diff_in_years
        return start.diff_in_years(end)
    else:
        d = end - start
        if hasattr(d, 'days'):
            # assume datetime.date or finance.BusinessDate (else days as float)
            d = d.days
        return float(d) / 365.25


DAY_COUNT = _day_count
FORWARD_RATE_TENOR = '3M'
FORWARD_CREDIT_TENOR = '1Y'
TIME_SHIFT = '1D'


class Curve(object):
    def __init__(self, x_list=None, y_list=None, y_inter=None):
        r"""
        Curve object to build function

        :param list(float) x_list: source values
        :param list(float) y_list: target values
        :param list(interpolation.interpolation) y_inter: interpolation function on x_list (optional)
            or triple of (left, mid, right) interpolation functions with
            left for x < x_list[0] (as default triple.right is used)
            right for x > x_list][-1] (as default interpolation.constant is used)
            mid else (as default interpolation.linear is used)

        Curve object to build function :math:`f:R \rightarrow R, x \mapsto y`
        from finite point vectors :math:`x` and :math:`y`
        using piecewise various interpolation functions.
        """
        if not y_inter:
            y_inter = interpolation.linear()

        y_left, y_mid, y_right = interpolation.constant(), interpolation.linear(), interpolation.constant()
        if isinstance(y_inter, (tuple, list)):
            if len(y_inter) == 3:
                y_left, y_mid, y_right = y_inter
            elif len(y_inter) == 2:
                y_mid, y_right = y_inter
                y_left = y_right
            elif len(y_inter) == 1:
                y_mid = y_inter[0]
            else:
                raise ValueError
        elif isinstance(y_inter, interpolation.base_interpolation):
            y_mid = y_inter
        else:
            raise (AttributeError, str(y_inter) + " is not a proper interpolation.")
        assert len(x_list) == len(y_list)
        assert len(x_list) == len(set(x_list))

        #: Interpolation:
        self._y_mid = type(y_mid)(x_list, y_list)
        self._y_right = type(y_right)(x_list, y_list)
        self._y_left = type(y_left)(x_list, y_list)

    @property
    def domain(self):
        return self._y_mid.x_list

    def __call__(self, x):
        if isinstance(x, (tuple, list)):
            return [self(xx) for xx in x]
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

    def __add__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) + other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __sub__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) - other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __mul__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) * other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __div__(self, other):
        x_list = sorted(set(self.domain + other.domain))
        y_list = [self(x) / other(x) for x in x_list]
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def __str__(self):
        return str([z for z in zip(self.domain, self(self.domain))])

    def __repr__(self):
        return self.__class__.__name__ + '(' + self.__str__() + ')'

    def update(self, x_list=list(), y_list=list()):
        self._y_left.update(x_list, y_list)
        self._y_mid.update(x_list, y_list)
        self._y_right.update(x_list, y_list)

    def shifted(self, delta=0.0):
        if delta:
            x_list = [x + delta for x in self.domain]
        else:
            x_list = self.domain
        y_list = self(self.domain)
        return self.__class__(x_list, y_list, (self._y_left, self._y_mid, self._y_right))


class DateCurve(Curve):
    def __init__(self, x_list, y_list, y_inter=None, origin=None, day_count=None):
        if origin is not None:
            self.origin = origin
        else:
            self.origin = x_list[0]

        if day_count is not None:
            self.day_count = day_count
        else:
            self.day_count = DAY_COUNT

        super(DateCurve, self).__init__([self.day_count(self.origin, x) for x in x_list], y_list, y_inter)

        self._domain = x_list

    @property
    def domain(self):
        return self._domain

    def __call__(self, x):
        if isinstance(x, (list, tuple)):
            return [self(xx) for xx in x]

        return super(DateCurve, self).__call__(self.day_count(self.origin, x))

    def __add__(self, other):
        new = super(DateCurve, self).__add__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def __sub__(self, other):
        new = super(DateCurve, self).__sub__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def __mul__(self, other):
        new = super(DateCurve, self).__mul__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def __div__(self, other):
        new = super(DateCurve, self).__div__(other.shifted(self.origin - other.origin))
        new.origin = self.origin
        return new

    def to_curve(self):
        x_list = self.domain

        y_list = self([self.day_count(self.origin, x) for x in x_list])

        return Curve(x_list, y_list, (self._y_left, self._y_mid, self._y_right))

    def update(self, x_list=list(), y_list=list()):
        if y_list:
            for x in x_list:
                if x not in self._domain:
                    self._domain.append(x)
            self._domain = sorted(self._domain)

            super(DateCurve, self).update([self.day_count(self.origin, x) for x in x_list], y_list)


class RateCurve(DateCurve):
    @classmethod
    def cast(cls, other):
        new = cls(other.domain,
                  [other.get_storage_type(x) for x in other.domain],
                  (other._y_left, other._y_mid, other._y_right),
                  other.origin,
                  other.day_count,
                  other.forward_tenor)
        return new

    def __init__(self, x_list, y_list, y_inter=None, origin=None, day_count=None, forward_tenor=None):
        super(RateCurve, self).__init__(x_list, y_list, y_inter, origin, day_count)
        if forward_tenor is not None:
            self.forward_tenor = forward_tenor
        else:
            self.forward_tenor = FORWARD_RATE_TENOR

    def __add__(self, other):
        casted = self.__class__.cast(other)
        new = super(RateCurve, self).__add__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def __sub__(self, other):
        casted = self.__class__.cast(other)
        new = super(RateCurve, self).__sub__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def __mul__(self, other):
        casted = self.__class__.cast(other)
        new = super(RateCurve, self).__mul__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def __div__(self, other):
        casted = self.__class__.cast(other)
        new = super(RateCurve, self).__div__(casted)
        new.forward_tenor = self.forward_tenor
        return new

    def get_storage_type(self, x):
        raise NotImplementedError

    def get_discount_factor(self, start, stop):
        ir = self.get_zero_rate(start, stop)
        t = self.day_count(start, stop)
        return compounding.continuous_compounding(ir, t)

    def get_zero_rate(self, start, stop):
        if start == stop:
            stop += TIME_SHIFT
        df = self.get_discount_factor(start, stop)
        t = self.day_count(start, stop)
        return compounding.continuous_rate(df, t)

    def get_short_rate(self, start, shift=TIME_SHIFT):
        up = self.get_zero_rate(self.origin, start + shift)
        dn = self.get_zero_rate(self.origin, start - shift)
        t = self.day_count(start - shift, start + shift)
        return (up - dn) / t

    def get_cash_rate(self, start, stop=None, step=None):
        if stop is None:
            if step is None:
                stop = start + self.forward_tenor
            else:
                stop = start + step
        df = self.get_discount_factor(start, stop)
        t = self.day_count(start, stop)
        return compounding.simple_rate(df, t)

    def get_swap_annuity(self, date_list):
        return sum([self.get_discount_factor(self.origin, t) for t in date_list])

    def get_swap_leg_valuation(self, date_list, flow_list):
        if isinstance(flow_list, float):
            return flow_list * self.get_swap_annuity(date_list)
        else:
            return sum([self.get_discount_factor(self.origin, t) * r for t, r in zip(date_list, flow_list)])


class DiscountFactorCurve(RateCurve):
    def get_storage_type(self, x):
        return self.get_discount_factor(self.origin, x)

    def get_discount_factor(self, start, stop):
        if stop is None or stop is self.origin:
            return self(start)
        else:
            return self(start) / self(stop)


class ZeroRateCurve(RateCurve):
    def get_storage_type(self, x):
        return self.get_zero_rate(self.origin, x)

    def get_zero_rate(self, start, stop):
        if stop is None or stop is self.origin or start == stop:
            return self(start)
        else:
            df = exp(self(start) * self.day_count(self.origin, start)
                     - self(stop) * self.day_count(self.origin, stop))
            t = self.day_count(start, stop)
            return compounding.continuous_rate(df, t)


class CashRateCurve(RateCurve):
    def get_storage_type(self, x):
        return self.get_cash_rate(x)

    def get_discount_factor(self, start, stop):
        df = 1.0
        current = start
        while current < stop:
            t = self.day_count(current, current + self.forward_tenor)
            df *= compounding.simple_compounding(self(current), t)
            current += self.forward_tenor
        t = self.day_count(current, stop)
        df *= compounding.simple_compounding(self(current), t)
        return df

    def get_cash_rate(self, start, stop=None, step=None):
        if step is not None and stop is not None:
            raise TypeError, "one argument (stop or step) must be None."

        if stop is None:
            if step is None or step is self.forward_tenor:
                return self(start)
            else:
                return super(CashRateCurve, self).get_cash_rate(start, step=step)
        else:
            return super(CashRateCurve, self).get_cash_rate(start, stop)


class ShortRateCurve(RateCurve):
    def get_storage_type(self, x):
        return self.get_short_rate(x)

    def get_zero_rate(self, start, stop):
        # integrate from start to stop
        ir = 0.0
        current = start
        while current < stop:
            t = self.day_count(current, current + TIME_SHIFT)
            ir = self(current) * t
            current += TIME_SHIFT
        t = self.day_count(current, stop)
        ir = self(current) * t
        return ir

    def get_short_rate(self, start, shift=None):
        return self(start)


class CreditCurve(RateCurve):
    """
        generic curve for default probabilities (under construction)
    """
    _inner_curve = RateCurve

    def __init__(self, x_list, y_list, y_inter=None, origin=None, day_count=None, forward_tenor=None):
        if forward_tenor is None:
            forward_tenor = FORWARD_CREDIT_TENOR
        super(self.__class__, self).__init__(x_list, y_list, y_inter, origin, day_count, forward_tenor)

    def get_survival_prob(self, start, stop):
        return self.get_discount_factor(start, stop)

    def get_flat_intensity(self, start, stop):
        return self.get_zero_rate(start, stop)

    def get_forward_survival_rate(self, start, stop=None, step=None):
        if step is not None and stop is not None:
            raise TypeError, "one argument (stop or step) must be None."
        if stop is None:
            return self.get_cash_rate(start, step=step)
        else:
            return self.get_cash_rate(start, stop)

    def get_hazard_rate(self, start, shift=None):
        return self.get_short_rate(start, shift)


class SurvivalProbabilityCurve(DiscountFactorCurve, CreditCurve):
    pass


class FlatIntensityCurve(CreditCurve):
    pass


class ForwardSurvivalRate(CreditCurve):
    pass


class HazardRateCurve(CreditCurve):
    pass
