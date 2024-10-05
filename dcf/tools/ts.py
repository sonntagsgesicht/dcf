from datetime import datetime as _datetime, date as _date
from pprint import pformat
from typing import Callable, Any as DateType

try:
    from dateutil.parser import parse
except ImportError:
    parse = lambda x: _datetime.fromisoformat(repr(x))


def ts(value: DateType, cls: Callable | None = None):
    """returns timestamp in given date type"""
    cls = cls or _datetime
    value = getattr(value, '__ts__', value)
    if callable(value):
        value = value()
    if cls == _datetime:
        return _datetime.now() if value is None else parse(str(value))
    if cls == _date:
        value = _date.today() if value is None else parse(str(value))
        return value.date()
    return cls(value)


class TS:

    def __init__(self, cls: Callable | None = None):
        """returns timestamp in given date type"""
        cls = cls or _datetime
        if cls == _datetime:
            def cls(value):
                return _datetime.now() if value is None else parse(str(value))
        if cls == _date:
            def cls(value):
                value = _date.today() if value is None else parse(str(value))
                return value.date()
        self.cls = cls

    def __call__(self, value: DateType | None = None):
        value = getattr(value, '__ts__', value)
        if callable(value):
            value = value()
        return self.cls(value)


class TSList(list):

    def __getitem__(self, key):

        if isinstance(key, int):
            return super().__getitem__(key)

        cls = self.__class__
        if not isinstance(key, slice):
            # t = key.__class__
            # t = lambda v: key.__class__(getattr(v, '__ts__', v))
            t = TS(key.__class__)
            return cls(v for v in self if t(v) == key)

        if isinstance(key.start, int) or isinstance(key.stop, int):
            # use default slice behavior
            return cls(super().__getitem__(key))

        if key.start and key.stop:
            # ts = key.start.__class__
            # te = key.stop.__class__
            # ts = lambda v: key.start.__class__(getattr(v, '__ts__', v))
            # te = lambda v: key.stop.__class__(getattr(v, '__ts__', v))
            t_s = TS(key.start.__class__)
            t_e = TS(key.stop.__class__)
            r = (v for v in self if key.start <= t_s(v) and t_e(v) < key.stop)

        elif key.start:
            # t = key.start.__class__
            # t = lambda v: key.start.__class__(getattr(v, '__ts__', v))
            t = TS(key.start.__class__)
            r = (v for v in self if key.start <= t(v))

        elif key.stop:
            # t = key.stop.__class__
            # t = lambda v: key.stop.__class__(getattr(v, '__ts__', v))
            t = TS(key.stop.__class__)
            r = (v for v in self if t(v) < key.stop)

        else:
            r = self

        if isinstance(key.step, int):
            # gives TSList[start:stop:step] := TSList[start:stop][::step]
            if key.step < 0:
                return cls(r)[-1::key.step]
            else:
                return cls(r)[0::key.step]
        elif key.step:
            cls = key.step.__class__.__name__
            raise ValueError(f"slice steps of type {cls!r} do not work")

        return cls(r)

    def __repr__(self):
        c = self.__class__.__name__
        s = pformat(list(self), indent=2, sort_dicts=False)
        return f"{c}(\n{s}\n)"

    def __call__(self, *_, **__):
        return self.__class__(v(*_, **__) for v in self)

    def __neg__(self):
        return self.__class__(v.__neg__() for v in self)

    def __add__(self, other):
        if isinstance(other, list):
            return self.__class__(super().__add__(other))
        return self.__class__(v.__add__(other) for v in self)

    def __sub__(self, other):
        if isinstance(other, list):
            # lousy hack since other might just be list and not List
            return self.__neg__().__add__(other).__neg__()
        return self.__class__(v.__sub__(other) for v in self)

    def __mul__(self, other):
        return self.__class__(v.__mul__(other) for v in self)

    def __truediv__(self, other):
        return self.__class__(v.__truediv__(other) for v in self)

    def __matmul__(self, other):
        return self.__class__(v.__matmul__(other) for v in self)

    def __abs__(self):
        return self.__class__(v.__abs__() for v in self)

    def __divmod__(self, other):
        return self.__class__(v.__divmod__() for v in self)

    def __mod__(self, other):
        return self.__class__(v.__mod__() for v in self)

    def __floordiv__(self, other):
        return self.__class__(v.__floordiv__() for v in self)

    def __invert__(self):
        return self.__class__(v.__invert__() for v in self)


if __name__ == '__main__':
    from businessdate import BusinessDate


    class TSClass:
        def __init__(self, value):
            self.value = value

        def __ts__(self):
            return self.value

        def __repr__(self):
            cls = self.__class__.__name__
            return f"{cls}({self.value!r})"

    class TSPClass(TSClass):
        @property
        def __ts__(self):
            return self.value


    values = '20240101', _datetime.now(), _date.today(), BusinessDate()
    values += tuple(map(TSClass, values)) + tuple(map(TSPClass, values))

    for value in values:
        print(value, '->', ts(value, _datetime), 'as', _datetime)
        print(value, '->', ts(value, _date), 'as', _date)
        print(value, '->', ts(value, BusinessDate), 'as', BusinessDate)

        print(value, '->', TS(_datetime)(value), 'as', _datetime)
        print(value, '->', TS(_date)(value), 'as', _date)
        print(value, '->', TS(BusinessDate)(value), 'as', BusinessDate)
