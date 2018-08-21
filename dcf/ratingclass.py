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


LONG_MASTER_SCALE = ('AAA+', 'AAA', 'AAA-', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-',
                     'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-',
                     'CCC+', 'CCC', 'CCC-', 'CC+', 'CC', 'CC-', 'C+', 'C', 'C-',
                     'D')
MASTER_SCALE = ('AAA', 'AA', 'A',
                'BBB', 'BB', 'B',
                'CCC', 'CC', 'C',
                'D')
SHORT_MASTER_SCALE = ('A',
                      'B',
                      'C',
                      'D')


class RatingClass(object):
    class master_scale(dict):
        @classmethod
        def fromkeys(cls, iterable, value=None):
            iterable = tuple(iterable)
            value = exp(-(len(iterable) - 1) * log(10)) if value is None else value
            ms = (lambda x, n: map(exp, (log(x) - log(x) * i / (n - 1) for i in range(n))))
            return RatingClass.master_scale(zip(iterable, ms(value, len(iterable))))

        def rating_classes(self):
            return list(RatingClass(f, self) for f in self.values())

        def keys(self):
            return list(str(i) for i, _ in self.items())

        def values(self):
            return list(float(i) for _, i in self.items())

        def _items(self):
            i = super(RatingClass.master_scale, self).items()
            return list(self.get(k) for k, _ in sorted(i, key=lambda x: x[1]))

        def items(self):
            i = super(RatingClass.master_scale, self).items()
            return list((k, v) for k, v in sorted(i, key=lambda x: x[1]))

        def get(self, k, d=None):
            return RatingClass(self[k], self) if k in self else d

        def __repr__(self):
            return self.__class__.__name__ + '(' + str(self)[1:-1] + ')'

        def __str__(self):
            return str(self.rating_classes())

    @property
    def masterscale(self):
        return self._masterscale

    @property
    def name(self):
        return str(self)

    @property
    def value(self):
        return float(self)

    @property
    def vector(self):
        return list(self)

    def __init__(self, value=0., masterscale=None):
        if not isinstance(value, float):
            raise TypeError('value argument must have type float not %s' % value.__class__)

        if not isinstance(masterscale, RatingClass.master_scale):
            if isinstance(masterscale, dict):
                masterscale = self.__class__.master_scale(masterscale)
            elif isinstance(masterscale, (tuple, list)) or hasattr(masterscale, '__iter__'):
                masterscale = self.__class__.master_scale.fromkeys(masterscale)

        self._value = value
        self._masterscale = masterscale

    def __repr__(self):
        if self.masterscale:
            return "%s-%s(%0.7f)" % (str(self), self.__class__.__name__, float(self))
        else:
            return str(self)

    def __str__(self):
        if self.masterscale:
            # check for base class item
            for k in self.masterscale:
                if round(float(self), 7) == round(float(self.masterscale[k]), 7):
                    return k
            # build linear combination of base classes
            pairs = zip(self.masterscale.keys(), list(self))
            pairs = ('%.7f %s' % (f, s) for s, f in pairs if f)
            return ' + '.join(pairs)

        return "%s(%0.7f)" % (self.__class__.__name__, float(self))

    def __float__(self):
        return float(self._value)

    def __iter__(self):
        if self._masterscale:
            value, value_list = round(float(self), 7), self.masterscale.values()

            if not min(value_list) <= value <= max(value_list):
                raise ValueError('masterscale does not embrace %.7f\n %s' % (float(self), repr(self.masterscale)))

            ceiling_index = [x < value for x in value_list].index(False)
            floor_index = ceiling_index - 1

            pd_cap, pd_floor = value_list[ceiling_index], value_list[floor_index]
            alpha = (value - pd_cap) / (pd_floor - pd_cap)

            for i, _ in enumerate(value_list):
                if i == floor_index:
                    yield max(0., min(round(alpha, 7), 1.))
                elif i == ceiling_index:
                    yield max(0., min(round(1. - alpha, 7), 1.))
                else:
                    yield 0.
