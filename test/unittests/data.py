
from businessdate import BusinessDate, BusinessSchedule, BusinessPeriod

from dcf import pv, fair, CashFlowList
from dcf.plans import amortize, outstanding, DEFAULT_AMOUNT
from yieldcurves import DateCurve, NelsonSiegelSvensson


def par_swap(start=20211223, maturity='10y', discount_curve=0.01, forward_curve=0.01, step='6m'):
    start = BusinessDate(start)
    start, *schedule = BusinessSchedule(start, start + maturity, step=BusinessPeriod(step))

    interest = CashFlowList.from_rate_cashflows(schedule[1::2], fixed_rate=0.01, origin=start)
    float_leg = CashFlowList.from_rate_cashflows(schedule, forward_curve=forward_curve, origin=start)

    float_pv = pv(float_leg, start, discount_curve)
    par_rate = fair(interest, start, discount_curve, present_value=float_pv, method='bisec', precision=1e-12)
    interest.fixed_rate = par_rate
    return interest - float_leg


def par_frn(start=20211223, maturity='10y', discount_curve=0.01, forward_curve=0.01, step='1y'):
    start = BusinessDate(start)
    start, *schedule = BusinessSchedule(start, start + maturity, step=BusinessPeriod(step))

    interest = CashFlowList.from_rate_cashflows(schedule, fixed_rate=0, forward_curve=forward_curve, origin=start)
    redemption = CashFlowList.from_fixed_cashflows(schedule[-1:])
    principal = CashFlowList.from_fixed_cashflows([start])

    zero_pv = pv(principal - redemption, start, discount_curve)
    par_rate = fair(interest, start, discount_curve, present_value=zero_pv, precision=1e-12)
    interest.fixed_rate = par_rate
    return interest + redemption - principal


def par_bond(start=20211223, maturity='10y', discount_curve=0.01, step='1y'):
    start = BusinessDate(start)
    start, *schedule = BusinessSchedule(start, start + maturity, step=BusinessPeriod(step))

    interest = CashFlowList.from_rate_cashflows(schedule, fixed_rate=0.01, origin=start)
    redemption = CashFlowList.from_fixed_cashflows(schedule[-1:])
    principal = CashFlowList.from_fixed_cashflows([start])

    zero_pv = pv(principal - redemption, start, discount_curve)
    par_rate = fair(interest, start, discount_curve, present_value=zero_pv, precision=1e-12)
    interest.fixed_rate = par_rate
    return interest + redemption - principal


def par_loan(start=20211223, maturity='10y', discount_curve=0.01, step='1m'):
    start = BusinessDate(start)
    start, *schedule = BusinessSchedule(start, start + maturity, step=BusinessPeriod(step))

    amount = DEFAULT_AMOUNT
    plan = amortize(len(schedule), amount=amount)
    out = outstanding(plan, amount=amount)

    interest = CashFlowList.from_rate_cashflows(schedule, out, fixed_rate=0.01, origin=start)
    redemption = CashFlowList.from_fixed_cashflows(schedule, plan)
    principal = CashFlowList.from_fixed_cashflows([start], amount_list=amount)

    zero_pv = pv(principal - redemption, start, discount_curve)
    par_rate = fair(interest, start, discount_curve, present_value=zero_pv, precision=1e-12)
    interest.fixed_rate = par_rate
    return interest + redemption - principal


def swap_curve(start=20211223):
    term = '1y', '2y', '5y', '10y', '15y', '20y', '30y'
    term = (start + p for p in term)
    zeros = 0.0084, 0.0079, 0.0057, 0.0024, 0.0008, 0.0001, 0.0003
    start = BusinessDate(start)
    return DateCurve.from_interpolation(term, zeros, origin=start)


def fwd_curve(start=20211223, cash_frequency=4):
    start = BusinessDate(start)
    fwd_term = '2d', '3m', '6m', '1y', '2y', '5y', '10y'
    fwd_term = (start + p for p in fwd_term)
    if cash_frequency == 12:
        fwd_1m = 0.0057, 0.0057, 0.0053, 0.0036, 0.0010, 0.0014, 0.0066
        return DateCurve.from_interpolation(fwd_term, fwd_1m,
                                             cash_frequency=12, origin=start)
    if cash_frequency == 4:
        fwd_3m = 0.0056, 0.0054, 0.0048, 0.0033, 0.0002, 0.0018, 0.0066
        return DateCurve.from_interpolation(fwd_term, fwd_3m,
                                            cash_frequency=4, origin=start)
    if cash_frequency == 2:
        fwd_6m = 0.0053, 0.0048, 0.0042, 0.0022, 0.0002, 0.0022, 0.0065
        return DateCurve.from_interpolation(fwd_term, fwd_6m,
                                            cash_frequency=2, origin=start)
    raise ValueError(f"no forward curve with cash_frequency of {cash_frequency}")


def nss_curve(start=20211223):
    inner = NelsonSiegelSvensson(beta0=0.7, beta1=2.5, beta2=0.0, beta3=6.5, tau1=0.8, tau2=12.5)
    return DateCurve(inner, origin=BusinessDate(start))
