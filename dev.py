import numpy
import matplotlib.pyplot as plt

from businessdate import BusinessDate, BusinessPeriod, BusinessRange

from dcf import DiscountFactorCurve, ZeroRateCurve, CashRateCurve, ShortRateCurve, \
    MarginalDefaultProbabilityCurve, MarginalSurvivalProbabilityCurve, \
    TerminalVolatilityCurve, InstantaneousVolatilityCurve, \
    continuous_rate, continuous_compounding, RatingClass, SHORT_MASTER_SCALE


def plot_curve(curves, x=None):
    if not isinstance(curves, (tuple, list)):
        curves = curves,

    fig, axs = plt.subplots(1, len(curves))

    if not isinstance(axs, (tuple, list)):
        axs = axs,

    for ax, curve in zip(axs[0], curves):
        today = curve.origin

        if x is None:
            if curve.domain[-1] < today + '1y':
                x = BusinessRange(today - '3m', curve.domain[-1] + '3m', step='1d')
            elif curve.domain[-1] < today + '2y':
                x = BusinessRange(today - '6m', curve.domain[-1] + '6m', step='1w')
            else:
                x = BusinessRange(today - '1y', curve.domain[-1] + '1y', step='1m')

        z = [today.diff_in_days(_) for _ in x]

        ax2 = ax.twinx()

        y = [curve.get_discount_factor(today, _) for _ in x]
        ax2.plot(z, y, label='get_discount_factor(time)', color='k')

        y = [curve.get_short_rate(_) for _ in x]
        ax.plot(z, y, label='get_short_rate(time)')

        y = [curve.get_zero_rate(today, _) for _ in x]
        ax.plot(z, y, label='get_zero_rate(time)')

        y = [curve.get_cash_rate(_, step='1M') for _ in x]
        ax.plot(z, y, label='get_cash_rate(time, 1m)')

        y = [curve.get_cash_rate(_, step='3M') for _ in x]
        ax.plot(z, y, label='get_cash_rate(time, 3m)')

        y = [curve.get_cash_rate(_, step='6M') for _ in x]
        ax.plot(z, y, label='get_cash_rate(time, 6m)')

        ax.set_xlabel('time (d)')
        ax.set_ylabel('rate')
        ax.set_ylim(.01, .025)
        ax2.set_ylabel('factor')

        ax.legend(loc='lower left', frameon=False)
        ax2.legend(loc='upper right', frameon=False)
        ax.set_title(curve.__class__.__name__)

    fig.tight_layout()
    plt.show()


def plot_vol(curves, x=None):
    if not isinstance(curves, (tuple, list)):
        curves = curves,

    fig, axs = plt.subplots(1, len(curves))

    if not isinstance(axs, (tuple, list, numpy.ndarray)):
        axs = [axs]

    for ax, curve in zip(axs, curves):
        today = curve.origin
        if x is None:
            if curve.domain[-1] < today + '1y':
                x = BusinessRange(today - '3m', curve.domain[-1] + '3m', step='1d', rolling=curve.origin)
            elif curve.domain[-1] < today + '2y':
                x = BusinessRange(today - '6m', curve.domain[-1] + '6m', step='1w', rolling=curve.origin)
            else:
                x = BusinessRange(today - '1y', curve.domain[-1] + '1y', step='1m', rolling=curve.origin)

        z = [today.diff_in_days(_) for _ in x]

        y = [curve.get_terminal_vol(_) for _ in x]
        ax.plot(z, y, label='get_terminal_vol(time)')

        y = [curve.get_terminal_vol(_, _ + '1d') for _ in x]
        ax.plot(z, y, label='get_terminal_vol(time, time+1d)')

        y = [curve.get_terminal_vol(_, _ + '3m') for _ in x]
        ax.plot(z, y, label='get_terminal_vol(time, time+3m)')

        y = [curve.get_terminal_vol(_, _ + '6m') for _ in x]
        ax.plot(z, y, label='get_terminal_vol(time, time+6m)')

        y = [curve.get_terminal_vol(_, _ + '1y') for _ in x]
        ax.plot(z, y, label='get_terminal_vol(time, time+1y)')

        y = [curve.get_instantaneous_vol(_) for _ in x]
        ax.plot(z, y, label='get_instantaneous_vol(time)')

        ax.set_xlabel('time (d)')
        ax.set_ylabel('vol')
        #ax.set_ylim(.01, .025)

        ax.legend(loc='lower left', frameon=False)
        ax.set_title(curve.__class__.__name__)

    fig.tight_layout()
    plt.show()


def plot_cast(curve, x=None):
    today = curve.origin

    if x is None:
        if curve.domain[-1] < today + '1y':
            x = BusinessRange(today - '3m', curve.domain[-1] + '3m', step='1d')
        elif curve.domain[-1] < today + '2y':
            x = BusinessRange(today - '6m', curve.domain[-1] + '6m', step='1w')
        else:
            x = BusinessRange(today - '1y', curve.domain[-1] + '1y', step='1m')

    fig, ax = plt.subplots(1, 1)

    ax2 = ax.twinx()
    y = [curve.__class__.get_storage_type(curve, _) for _ in x]
    z = [today.diff_in_days(_) for _ in x]
    ax.plot(z, y, label='original', color='k')

    y = [curve.__class__.get_storage_type(curve.cast(ZeroRateCurve), _) for _ in x]
    ax.plot(z, y, label='zero rate')

    y = [curve.__class__.get_storage_type(curve.cast(DiscountFactorCurve), _) for _ in x]
    ax.plot(z, y, label='discount factor')

    y = [curve.__class__.get_storage_type(curve.cast(ShortRateCurve), _) for _ in x]
    ax.plot(z, y, label='short rate')

    y = [curve.__class__.get_storage_type(curve.cast(CashRateCurve, forward_tenor='1m'), _) for _ in x]
    ax.plot(z, y, label='cash rate 1m ')

    y = [curve.__class__.get_storage_type(curve.cast(CashRateCurve, forward_tenor='3m'), _) for _ in x]
    ax.plot(z, y, label='cash rate 3m ')

    ax.set_xlabel('time (d)')
    ax.set_ylabel('rate')
    ax2.set_ylabel('factor')

    ax.legend(loc='lower left', frameon=False)
    ax2.legend(loc='lower right', frameon=False)

    fig.tight_layout()
    plt.title(curve.__class__.__name__ + '.get_storage_rate(time)')
    plt.show()


if 1:
    today = BusinessDate()
    rng = BusinessRange(today, today + '5y', '3m')

    grid = [today, today + '2y',today + '3y', today + '4y']
    vols = [0.15, 0.2, 0.2, 0.18]

    i = InstantaneousVolatilityCurve(grid, vols)
    t = i.cast(TerminalVolatilityCurve)
    #t = TerminalVolatilityCurve(grid, vols)
    #i = t.cast(InstantaneousVolatilityCurve)
    v = i, t
    plot_vol(v)

if 0:
    today = BusinessDate()
    rng = BusinessRange(today, today + '5y', '3m')

    grid = [today, today + '2y', today + '4y']
    vols = [0.1, 0.2, 0.17]

    p = '%0.4f, %0.4f, %0.4f'
    w = lambda v, b: (v.get_instantaneous_vol(b), v.get_terminal_vol(b), v.get_terminal_vol(b, b + '1y'))

    v = InstantaneousVolatilityCurve(grid, vols)
    for b in rng:
        print v.__class__.__name__.ljust(24), b, p % w(v, b)
    print ''

    v = TerminalVolatilityCurve(grid, vols)
    for b in rng:
        print v.__class__.__name__.ljust(24), b, p % w(v, b)

if 0:
    RatingClass.SLOPPY = True
    r = RatingClass(-0.001, masterscale=('A', 'B', 'C', 'D'))
    print list(r), float(r)

    r = RatingClass(0.0, masterscale=('A', 'B', 'C', 'D'))
    print list(r), float(r)

    r = RatingClass(0.000001, masterscale=('A', 'B', 'C', 'D'))
    print list(r), float(r)

    r = RatingClass(0.5, masterscale=('A', 'B', 'C', 'D'))
    print list(r), float(r)

    r = RatingClass(2.0, masterscale=('A', 'B', 'C', 'D'))
    print list(r), float(r)
    for c in r.masterscale.rating_classes():
        print list(c), float(c)
        pass

if 0:
    today = BusinessDate()
    grid = ['0D', '1M', '2M', '3M', '4M', '5M', '6M', '9m']
    grid = tuple(BusinessPeriod().add_months(i) for i in range(48))
    pd_value = 0.1
    curve = MarginalSurvivalProbabilityCurve([today], [pd_value])
    other = MarginalSurvivalProbabilityCurve([today], [pd_value])
    print curve + other
    print curve - other
    print curve * other
    print curve / other

if 0:
    rcls = RatingClass(0.02, masterscale=SHORT_MASTER_SCALE)
    print rcls
    print repr(rcls)
    print rcls.masterscale
    print repr(rcls.masterscale)

if 0:
    today = BusinessDate()
    grid = ['0D', '1M', '2M', '3M', '4M', '5M', '6M', '9m']
    grid = tuple(BusinessPeriod().add_months(i) for i in range(48))
    pd_value = 0.01
    curve = MarginalDefaultProbabilityCurve([today], [pd_value])

    print curve
    for p in grid:
        t = curve.day_count(today, today + p)
        y = curve.day_count(today, today + '1y')
        hz = continuous_rate(1.0 - pd_value, 1.0015)
        s = continuous_compounding(hz, t)

        print p,
        print t,
        print 1. - curve.get_survival_prob((today + p)),
        print 1. - s

if 0:
    today = BusinessDate()
    curve = CashRateCurve([today, today + '3M'], [0.02, 0.01], forward_tenor='1M')
    plot_curve(curve)

if 0:
    today = BusinessDate()

    curve_type = CashRateCurve
    cast_type = ZeroRateCurve

    grid = ['0D', '1M', '2M', '3M', '4M', '5M', '6M', '9m']
    points = [0.02, 0.018, 0.0186, 0.018, 0.0167, 0.0155, 0.015, 0.015]

    curve = curve_type([today + p for p in grid], points, forward_tenor='1m')
    cast = curve.cast(cast_type, domain=curve.domain, forward_tenor='1m')
    re = cast.cast(curve_type, domain=curve.domain, forward_tenor='1m')

    print curve.domain, curve(curve.domain)
    print cast.domain, cast(cast.domain)
    print re.domain, re(re.domain)
    print ''
    for d in curve.domain:
        print d, curve(d), re(d)
    print ''
    for d in BusinessRange(curve.origin, curve.domain[-1] + '1m', '1m', curve.origin):
        # print d, cast.get_zero_rate(d), curve.get_zero_rate(d)
        print d, curve.get_cash_rate(d), curve.get_cash_rate(d, step='3m'), cast.get_cash_rate(d)

    x = BusinessRange(curve.origin - '6m', curve.domain[-1] + '1y', '1d', curve.origin)
    x = BusinessRange(curve.origin, curve.domain[-1] + '1m', '1m', curve.origin)
    # plot_curve((curve, cast), x)
    plot_curve((curve, cast), x)
    # plot_curve(cast, x)
    # plot_cast(curve, x)

if 0:
    x, y = ['0D', '6m', '2y'], [0.02, 0.01, 0.015]
    # x, y = ['0D', '3m'], [0.01, 0.02]

    x = [BusinessDate() + _ for _ in x]

    curve = ZeroRateCurve(x, y)
    # curve = ShortRateCurve(x, y)
    # curve = CashRateCurve(x, y, forward_tenor='1M')
    # curve = DiscountFactorCurve(x, [1., .9, .7])


    plot_curve(curve)
    # plot_curve(CashRateCurve.cast(curve, '3m'))

    plot_cast(curve)

    '''
            cash = CashRateCurve.cast(zero, '1M')
            for d in zero.domain:
                if zero.origin < d:
                    domain = cash.domain
                    for s, e in zip(domain[:-1], domain[1:]):
                        zdf = zero.get_zero_rate(s, e)
                        cdf = compounding.simple_compounding(cash(s), cash.day_count(s, e))
                        cdf = compounding.continuous_rate(cdf, zero.day_count(s, e))
                        print abs(zdf-cdf) < 1e-7, s, e, zdf, cdf

                print d, zero(d) == cast(d), zero(d), cast(d)
    '''
