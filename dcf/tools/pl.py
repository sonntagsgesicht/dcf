

from .dc import day_count as _default_day_count


class _matmul_dict(dict):
    """"""

    def __init__(self, seq, at=None, /, **kwargs):
        self._at = at
        super(_matmul_dict, self).__init__(**kwargs)

    def at(self, item):
        if self._at is None:
            return item
        if callable(self._at):
            return self._at(item)
        return self._at.get(item, item)

    def __matmul__(self, other):
        if other is None:
            self._at = None
            return self
        self._at = self._at @ other if self._at else other
        return self

    def __setitem__(self, item, value):
        super().__setitem__(self.at(item), value)

    def __getitem__(self, item):
        return super().__getitem__(self.at(item))

    def __delitem__(self, item):
        super().__delitem__(self.at(item))

    def __contains__(self, item):
        super().__contains__(self.at(item))

    def setdefault(self, item, value=None):
        return super().setdefault(self.at(item), value)

    def get(self, item, default=None):
        return super().get(self.at(item), default)

    def update(self, other, **kwargs):
        other = ((self.at(k), v) for k, v in other.items())
        kwargs = {self.at(k): v for k, v in kwargs.items()}
        super().update(other, **kwargs)

    def pop(self, item, default=None):
        super().pop(self.at(item), default)


class _piecewise_linear(dict):

    def __init__(self, x_list=(0.0,), y_list=(0.0,)):
        r"""piecewise linear curve

        :param x_list: points $x_1 \dots x_n$
        :param y_list: values $y_1 \dots y_n$

        A |piecewise_linear()| object is a function $f$
        returning at $x$ the linear interpolated float of
        $y_i$ and $y_{i+1}$ when $x_i \leq x < x_{i+1}$, i.e.
        $$f(x)=(y_{i+1}-y_i) \cdot \frac{x-x_i}{x_{i+1}-x_i}$$

        and

        $y_1$ if $x \leq x_1$

        as well as

        $y_n$ if $x_n <x$.


        >>> from dcf.tools.pl import piecewise_linear
        >>> c = piecewise_linear([1.,2.,3.], [2.,3.,4.])
        >>> c
        piecewise_linear([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])

        >>> c(0.)
        2.0
        >>> c(1.)
        2.0
        >>> c(1.5)
        2.5
        >>> c(1.51)
        2.51
        >>> c(2.)
        3.0
        >>> c(3.)
        4.0
        >>> c(4)
        4.0
        """
        super().__init__(sorted(zip(map(float, x_list), map(float, y_list))))

    def __call__(self, x):
        if not self:
            cls = self.__class__.__name__
            raise ValueError(f"{cls} must conain at least one point")

        x = float(x)
        if len(self) == 1 or x <= min(self.keys()):
            return next(iter(self.values()))
        if max(self.keys()) <= x:
            return next(reversed(self.values()))

        _x = max(_x for _x in self.keys() if _x <= x)
        _y = self[_x]
        x_ = min(x_ for x_ in self.keys() if x < x_)
        y_ = self[x_]
        return _y + (y_ - _y) * (x - _x) / (x_ - _x)

    def __repr__(self):
        cls = self.__class__.__name__
        return f"{cls}({list(self.keys())}, {list(self.values())})"


class piecewise_linear(_piecewise_linear):

    def __init__(self, x_list=(0.0,), y_list=(0.0,), *,
                 origin=None, day_count=None):
        self.origin = origin
        self.day_count = day_count
        x_list = (self._yf(x) for x in x_list)
        super().__init__(x_list, y_list)

    def _yf(self, x):
        dc = self.day_count or _default_day_count
        if self.origin is None:
            return x
        return dc(self.origin, x)

    def __call__(self, x):
        return super().__call__(self._yf(x))

    # -- dict methods ---

    def __repr__(self):
        cls = self.__class__.__name__
        x, y = list(self.keys()), list(self.values())
        o, d = self.origin, self.day_count
        kw = ''
        if o:
            kw += f", origin={0}"
        if d:
            d = getattr(d, '__qualname__', str(d))
            kw += f", day_count={d}"
        return f"{cls}({x}, {y}{kw})"

    def __setitem__(self, item, value):
        super().__setitem__(self._yf(item), value)

    def __getitem__(self, item):
        return super().__getitem__(self._yf(item))

    def __delitem__(self, item):
        super().__delitem__(self._yf(item))

    def __contains__(self, item):
        super().__contains__(self._yf(item))

    def setdefault(self, item, value=None):
        return super().setdefault(self._yf(item), value)

    def get(self, item, default=None):
        return super().get(self._yf(item), default)

    def update(self, other, **kwargs):
        other = ((self._yf(k), v) for k, v in other.items())
        kwargs = {self._yf(k): v for k, v in kwargs.items()}
        super().update(other, **kwargs)

    def pop(self, item, default=None):
        super().pop(self._yf(item), default)

