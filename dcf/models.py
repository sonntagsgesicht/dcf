
class RateCashFlowOptionPayOffModel(object):

    def __init__(self, forward_curve=None, valuation_date=None):
        self.forward_curve = forward_curve
        self.valuation_date = valuation_date

    def get_forward_value(self, date):
        return self.forward_curve(date)

    def get_call_value(self, date, strike, rate=None):
        if rate is None:
            rate = self.get_forward_value(date)
        return max(rate - strike, 0.0)

    def get_put_value(self, date, strike, rate=None):
        if rate is None:
            rate = self.get_forward_value(date)
        call = self.get_call_value(date, strike, rate)
        return strike - rate + call

    def get_binary_call_value(self, date, strike, rate=None):
        if rate is None:
            rate = self.get_forward_value(date)
        return 0.0 if rate < strike else 1.0

    def get_binary_put_value(self, date, strike, rate=None):
        return 1.0 - self.get_binary_call_value(date, strike, rate)
