from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from urllib.error import URLError
from csv import reader


class currency:

    fx = 0.0
    ccy = []

    def __init__(self, value=0.0):
        """currency class (float subclass)

        :param value:
        """
        self.value = float(value)

    def __str__(self):
        return f'{self.value:.2f} {self.__class__.__name__}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.value})'

    def __float__(self):
        return self.value

    def __add__(self, other):
        if isinstance(other, currency) and not type(self) == type(other):
            s, t = type(self).__name__, type(other).__name__
            m = f"unsupported operand type(s) for +: {s!r} and {t!r}"
            raise TypeError(m)
        return type(self)(float(self) + float(other))

    def __radd__(self, other):
        if isinstance(other, currency) and not type(self) == type(other):
            s, t = type(self).__name__, type(other).__name__
            m = f"unsupported operand type(s) for +: {s!r} and {t!r}"
            raise TypeError(m)
        return type(self)(float(self) + float(other))

    def __sub__(self, other):
        if isinstance(other, currency) and not type(self) == type(other):
            s, t = type(self).__name__, type(other).__name__
            m = f"unsupported operand type(s) for -: {s!r} and {t!r}"
            raise TypeError(m)
        return type(self)(float(self) - float(other))

    def __mul__(self, other):
        if isinstance(other, type) and issubclass(other, currency):
            # eur(10) * usd = usd(9)
            return other(float(self) * self.fx / other.fx)
        if isinstance(other, currency):
            # eur(10) * usd(10) -> TypeError
            s, t = type(self).__name__, type(other).__name__
            m = f"unsupported operand type(s) for *: {s!r} and {t!r}"
            raise TypeError(m)
        # eur(10) * 10 = eur(100)
        return type(self)(float(self) * float(other))

    def __rmul__(self, other):
        if isinstance(other, currency):
            s, t = type(self).__name__, type(other).__name__
            m = f"unsupported operand type(s) for *: {s!r} and {t!r}"
            raise TypeError(m)
        return type(self)(float(self) * float(other))

    def __truediv__(self, other):
        if isinstance(other, currency):
            s, t = type(self).__name__, type(other).__name__
            m = f"unsupported operand type(s) for /: {s!r} and {t!r}"
            raise TypeError(m)
        return self * (1 / float(other))

    def __bool__(self):
        return bool(self.value)

    def __getattr__(self, item):
        # fx rate conversion
        ccy = self.__class__.get(item)
        return ccy(float(self) * self.fx / ccy.fx)

    @classmethod
    def get(cls, item, create=False):
        items = tuple(c for c in cls.ccy if item.upper() in c.__name__)
        if len(items) == 1:
            return items[0]
        if create:
            return cls.new(item)
        raise AttributeError(f'currency {item} not found')

    @classmethod
    def new(cls, item, fx=0.0):
        return type(item, (cls,), {'fx': fx})

    @classmethod
    def update(cls, verbose=False):
        url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip'
        file = 'eurofxref-hist.csv'
        url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip'
        file = 'eurofxref.csv'
        myzip = ZipFile(BytesIO(urlopen(url).read()))  #  nosec B310
        lines = tuple(myzip.open(file).readlines())
        lines = tuple(_.decode().replace(' ', '') for _ in lines)
        d = dict(zip(*reader(lines)))
        date = d.pop('Date')
        old = cls.ccy
        cls.ccy = [cls.new('EUR', 1.0)]
        cls.ccy += [cls.new(k.upper(), float(v))
                    for k, v in d.items() if k and v]
        cls.ccy += [o for o in old if o.__name__ not in d]

        if verbose:
            print('updated currencies', *d.keys(), 'as of', date, 'from', url)


try:
    currency.update()
except URLError:
    pass

EUR = currency.get('EUR', create=True)
USD = currency.get('USD', create=True)
GBP = currency.get('GBP', create=True)
CHF = currency.get('CHF', create=True)
JPY = currency.get('JYP', create=True)


if __name__ == '__main__':
    INR = currency.get('INR', create=True)

    c = EUR(20.345)
    e = EUR(1)

    print(c, repr(c))
    print(2*c*3/4 + 20 - 100)
    print(c, c.usd, c.usd.eur, e.usd)
#    EUR.fx = 2
    print(e.fx, c.fx, USD(1).eur, USD(1) * EUR)
    print(INR(12).eur)
    print(currency.new('INR', 23.0)(12).eur)
    print(USD.fx)
