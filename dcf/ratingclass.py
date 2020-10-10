# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from math import exp, log
import logging

_logger = logging.getLogger('dcf')


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
    SLOPPY = False

    class master_scale(dict):
        @classmethod
        def fromkeys(cls, iterable, value=None):
            iterable = tuple(iterable)
            value = exp(-(len(iterable) - 1) * log(10)) if value is None else value
            ms = (lambda x, n: list(map(exp, (log(x) - log(x) * i / (n - 1) for i in range(n)))))
            return RatingClass.master_scale(list(zip(iterable, ms(value, len(iterable)))))

        def rating_classes(self):
            return list(RatingClass(f, self) for f in list(self.values()))

        def keys(self):
            return list(str(i) for i, _ in list(self.items()))

        def values(self):
            return list(float(i) for _, i in list(self.items()))

        def items(self):
            i = list(super(RatingClass.master_scale, self).items())
            return list((k, float(v)) for k, v in sorted(i, key=lambda x: x[1]))

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
        if not isinstance(masterscale, RatingClass.master_scale):
            if isinstance(masterscale, dict):
                masterscale = self.__class__.master_scale(masterscale)
            elif isinstance(masterscale, (tuple, list)) or hasattr(masterscale, '__iter__'):
                masterscale = self.__class__.master_scale.fromkeys(masterscale)

        if masterscale:
            value = masterscale[value] if value in masterscale else value

        if not isinstance(value, float):
            raise TypeError('value argument must be key in masterscale or have type float not %s' % value.__class__)

        self._value = value
        self._masterscale = masterscale

    def __repr__(self):
        if self.masterscale:
            return "[%s]-%s(%0.7f)" % (str(self), self.__class__.__name__, float(self))
        else:
            return str(self)

    def __str__(self):
        if self.masterscale:
            # check for base class item
            for k in self.masterscale:
                if round(float(self), 7) == round(float(self.masterscale[k]), 7):
                    return k
            # build linear combination of base classes
            pairs = list(zip(list(self.masterscale.keys()), list(self)))
            pairs = ('%.7f %s' % (f, s) for s, f in pairs if f)
            return ' + '.join(pairs)

        return "%s(%0.7f)" % (self.__class__.__name__, float(self))

    def __float__(self):
        return float(self._value)

    def __iter__(self):
        if self._masterscale:
            value = round(float(self), 7)
            value_list = [round(x, 7) for x in list(self.masterscale.values())]

            if not min(value_list) <= value <= max(value_list):
                msg = 'masterscale does not embrace %.7f' % float(self)  # + '\n %s' % repr(self.masterscale)
                if self.__class__.SLOPPY:
                    _logger.warning(msg)
                else:
                    raise ValueError(msg)

            if value < min(value_list):
                for i, v in enumerate(value_list):
                    yield round(value/v, 7) if i == 0 else 0.

            elif max(value_list) < value:
                l = len(value_list)-1
                for i, v in enumerate(value_list):
                    yield round(value/v, 7) if i == l else 0.

            else:
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
