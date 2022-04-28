
class RateCashFlowOptionPayOffModel(object):

    def __init__(self, forward_curve=None, valuation_date=None):
        self.forward_curve = forward_curve
        self.valuation_date = valuation_date

    def get_cash_rate(self, date):
        return self.forward_curve.get_cash_rate(date)

    def get_call_value(self, date, strike):
        rate = self.get_cash_rate(date)
        return max(rate - strike, 0.0)

    def get_put_value(self, date, strike):
        rate = self.get_cash_rate(date)
        return max(strike - rate, 0.0)

    def get_binary_call_value(self, date, strike):
        rate = self.get_cash_rate(date)
        return 0.0 if rate < strike else 1.0

    def get_binary_call_value(self, date, strike):
        rate = self.get_cash_rate(date)
        return 1.0 if rate < strike else 0.0


