
from pprint import pformat


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
