

from businessdate import BusinessDate, BusinessSchedule, BusinessPeriod
from dcf import pv, fair, CashFlowList
from dcf.plans import amortize, outstanding, DEFAULT_AMOUNT
from yieldcurves import DateCurve


def par_swap(start=20212223, maturity='10y', discount_curve=0.01, forward_curve=0.01, step='6m'):
    start = BusinessDate(start)
    schedule = \
        BusinessSchedule(start, start + maturity, step=BusinessPeriod(step))

    float_leg = CashFlowList.from_rate_cashflows(schedule, forward_curve=forward_curve)
    fixed_leg = CashFlowList.from_rate_cashflows(schedule[::2], fixed_rate=0.01)

    float_pv = pv(float_leg, discount_curve, start)
    par_rate = fair(fixed_leg, discount_curve, start, float_pv, precision=1e-12)
    fixed_leg.fixed_rate = par_rate

    return fixed_leg - float_leg


def par_bond(start=20212223, maturity='10y', discount_curve=0.01, step='1y'):
    start = BusinessDate(start)
    schedule = \
        BusinessSchedule(start, start + maturity, step=BusinessPeriod(step))
    start_date, payment_dates = schedule[0], schedule[1:]

    principal = CashFlowList.from_fixed_cashflows([start_date])
    redemption = CashFlowList.from_fixed_cashflows(payment_dates[-1:])
    interest = CashFlowList.from_rate_cashflows(payment_dates, fixed_rate=0.01)

    zero_pv = pv(principal - redemption, discount_curve, start)
    par_rate = fair(interest, discount_curve, start, zero_pv, precision=1e-12)
    interest.fixed_rate = par_rate
    return interest + redemption - principal


def par_loan(start=20212223, maturity='10y', discount_curve=0.01, step='1m'):
    start = BusinessDate(start)
    schedule = \
        BusinessSchedule(start, start + maturity, step=BusinessPeriod(step))
    start_date, payment_dates = schedule[0], schedule[1:]

    amount = DEFAULT_AMOUNT
    plan = amortize(len(payment_dates), amount=amount)
    out = outstanding(plan, amount=amount)

    principal = CashFlowList.from_fixed_cashflows([start_date],
                                                  amount_list=amount)
    redemption = CashFlowList.from_fixed_cashflows(payment_dates, plan)
    interest = CashFlowList.from_rate_cashflows(payment_dates, out,
                                                fixed_rate=0.01)

    zero_pv = pv(principal - redemption, discount_curve, start)
    par_rate = fair(interest, discount_curve, start, zero_pv, precision=1e-12)
    interest.fixed_rate = par_rate
    return interest + redemption - principal


def swap_curves(start=20212223):
    term = '1y', '2y', '5y', '10y', '15y', '20y', '30y'
    zeros = 0.0084, 0.0079, 0.0057, 0.0024, 0.0008, 0.0001, 0.0003

    fwd_term = '2d', '3m', '6m', '1y', '2y', '5y', '10y'
    fwd_1m = 0.0057, 0.0057, 0.0053, 0.0036, 0.0010, 0.0014, 0.0066
    fwd_3m = 0.0056, 0.0054, 0.0048, 0.0033, 0.0002, 0.0018, 0.0066
    fwd_6m = 0.0053, 0.0048, 0.0042, 0.0022, 0.0002, 0.0022, 0.0065

    start = BusinessDate(start)
    yc = DateCurve.from_interpolation(term, zeros, origin=start)
    fwd_1m = DateCurve.from_interpolation(fwd_term, fwd_1m, cash_frequency=12, origin=start)
    fwd_3m = DateCurve.from_interpolation(fwd_term, fwd_3m, cash_frequency=4, origin=start)
    fwd_6m = DateCurve.from_interpolation(fwd_term, fwd_6m, cash_frequency=2, origin=start)
    return yc, fwd_1m, fwd_3m, fwd_6m
