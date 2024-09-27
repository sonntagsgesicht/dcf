# -*- coding: utf-8 -*-

# yieldcurves
# -----------
# A Python library for financial yield curves.
#
# Author:   sonntagsgesicht
# Version:  0.2.1, copyright Tuesday, 16 July 2024
# Website:  https://github.com/sonntagsgesicht/yieldcurves
# License:  Apache License 2.0 (see LICENSE file)


from inspect import stack, signature
from json import loads, dumps


def _bound_arguments(self):
    # scan attributes used as arguments
    s = signature(self.__class__)
    kpv = ((k, p, getattr(self, k, p.default))
           for k, p in s.parameters.items())
    kv = {k: v for k, p, v in kpv if not v == p.default}
    # use function name rather than repr string
    # kv = {k: getattr(v, '__qualname__', v) for k, v in kv.items()}
    return s.bind(**kv)


def _args(self):
    return _bound_arguments(self).args


def _kwargs(self):
    return _bound_arguments(self).kwargs


def _default(self):
    return  self.__json__() if hasattr(self, '__json__') else repr(self)


def _dumps(self):
    b = _bound_arguments(self)
    args = [getattr(a, '__qualname__', a) for a in b.args]
    kwargs = {k: getattr(v, '__qualname__', v) for k, v in b.kwargs.items()}
    d = {'type': self.__class__.__qualname__, 'args': args, 'kwargs': kwargs}
    return dumps(list(d.values()), indent=2, default=_default)


def _loads(obj, objs=()):
    objs = objs or globals()
    d = loads(obj)
    if isinstance(d, dict):
        cls = d.get('type')
        args = d.get('args', [])
        kwargs = d.get('kwargs', {})
    elif len(d) == 3:
        cls, args, kwargs = d
    elif len(d) == 2:
        cls, args = d
        kwargs = {}
        if isinstance(args, dict):
            args, kwargs = (), args
    else:
        return

    cls = objs.get(cls)
    for a in args:
        if isinstance(a, str) and a in objs:
            args[a] = objs.get(a)
    for k, v in kwargs.items():
        if isinstance(v, str) and v in objs:
            kwargs[k] = objs.get(v)

    return cls(*args, **kwargs)


def _from_json(cls, obj=()):
    objs = globals()
    objs[cls.__qualname__] = cls
    return _loads(obj or {}, objs=objs)


def _copy(self):
    b = _bound_arguments(self)
    return self.__class__(*b.args, **b.kwargs)


def _prepr(self, *, r=None, sep=', '):
    if r is None:
        r = str if any(f.function == '__str__' for f in stack()) else repr
    b = _bound_arguments(self)
    args, kwargs = b.args, b.kwargs
    args = [getattr(a, '__qualname__', r(a)) for a in args]
    kwargs = {k: getattr(v, '__qualname__', r(v)) for k, v in kwargs.items()}
    # build repr string
    params = [f"{a}" for a in args] + [f"{k}={v}" for k, v in kwargs.items()]
    return f"{self.__class__.__qualname__}({sep.join(params)})"


def _repr(self):
    return _prepr(self, r=repr)


def _str(self):
    return _prepr(self, r=str)


def prepr(self, *args, clsmethod='', sep=', ', **kwargs):
    # select repr function
    r = str if any(f.function == '__str__' for f in stack()) else repr

    # repr args
    if not args and not kwargs:
        b = bound_arguments(self)
        args, kwargs = b.args, b.kwargs

    args = [getattr(a, '__qualname__', r(a)) for a in args]
    kwargs = {k: getattr(v, '__qualname__', r(v)) for k, v in kwargs.items()}

    # build repr string
    params = tuple(f"{a}" for a in args) + \
        tuple(f"{k}={v}" for k, v in kwargs.items())
    clsmethod = '.' + clsmethod if clsmethod else ''
    return f"{self.__class__.__qualname__}{clsmethod}({sep.join(params)})"


class Pretty:

    def __init__(self, clsmethod='', sep=', ', args=(), kwargs=()):
        self.clsmethod = clsmethod
        self.sep = sep
        self.args = args
        self.kwargs = kwargs

    def __call__(self, obj, *args, clsmethod='', sep=', ', **kwargs):
        return prepr(obj, *args, clsmethod=clsmethod, sep=sep, **kwargs)


def pretty(cls):
    setattr(cls, '__str__', _str)
    setattr(cls, '__repr__', _repr)
    if not hasattr(cls, '__args__'):
        setattr(cls, '__args__', _args)
    if not hasattr(cls, '__kwargs__'):
        setattr(cls, '__kwargs__', _kwargs)
    if not hasattr(cls, '__copy__'):
        setattr(cls, '__copy__', _copy)
    if not hasattr(cls, '__json__'):
        setattr(cls, '__json__', _dumps)
    if not hasattr(cls, 'from_json'):
        setattr(cls, 'from_json', classmethod(_from_json))
    return cls


def pp(clsmethod='', sep=', ', args=(), kwargs=()):
    return Pretty(clsmethod, sep, args, kwargs)
