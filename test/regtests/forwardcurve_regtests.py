
from regtest import RegressionTestCase

from dcf.curves.curve import ForwardCurve


class ForwardCurveRegTests(RegressionTestCase):

    def setUp(self):
        self.domain = tuple(range(1,10))
        self.foo = lambda x: x*x
        self.data = tuple(map(self.foo, self.domain))
        self.rate = 0.01
        self.spot = self.data[-1]

    def test_forward(self):
        f = ForwardCurve(self.domain, self.data, yield_curve=self.rate)
        for x in range(1, 100):
            self.assertAlmostRegressiveEqual(f(x))
