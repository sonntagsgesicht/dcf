# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht
# Version:  1.0, copyright Monday, 14 October 2024
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from pprint import pformat
from warnings import warn

try:
    from tabulate import tabulate
except ImportError:
    def tabulate(x, *_, **__):
        msg = ("tabulate not found. consider 'pip install tabulate' "
               "for more flexible table representation")
        warn(msg)
        return pformat(x, indent=2, sort_dicts=False)


def html(item=None):
    _item = getattr(item, '_repr_html_', None)
    return _item() if callable(_item) else _item


def latex(item=None):
    _item = getattr(item, '__latex__', '')
    return _item() if callable(_item) else _item


NDIGITS = 6


class Details(dict):

    def __float__(self):
        return float(self.get('cashflow', None) or 0.0)

    @property
    def __ts__(self):
        return self.get('pay date')

    def __getattr__(self, item):
        return self.get(item.replace('_', ' '))

    def __repr__(self):
        c = self.__class__.__name__
        s = pformat(dict(self.items()), indent=2, sort_dicts=False)
        return f"{c}(\n{s}\n)"

    def drop(self, value):
        return Details((k, v) for k, v in self.items() if v != value)

    def _repr_html_(self):
        return html(DetailsList([self]))

    def __latex__(self):
        return latex(DetailsList([self]))

    def __str__(self):
        return str(DetailsList([self]))


class DetailsList(list):

    def _tabulate(self, floatrnd=False, **kwargs):
        header = {}
        for d in self:
            header.update(d)
        header = list(header.keys())
        rows = [header]
        for d in self:
            r = dict.fromkeys(header)
            if floatrnd:
                for k, v in d.items():
                    if isinstance(v, float) \
                            and NDIGITS < len(str(v).split('.')[-1]):
                        d[k] = round(v, NDIGITS)
            r.update(d)
            rows.append(list(r.values()))
        return tabulate(rows, **kwargs)

    def _repr_html_(self):
        return self._tabulate(tablefmt="html", headers="firstrow")

    def __latex__(self):
        return self._tabulate(tablefmt="latex", headers="firstrow",
                              floatrnd=True, floatfmt=",", intfmt=",")

    def __str__(self):
        return self._tabulate(headers="firstrow",
                              floatrnd=True, floatfmt="_", intfmt="_")
