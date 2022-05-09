# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Friday, 14 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import matplotlib.pyplot as plt

'''
term = 1, 2, 5, 10, 15, 20, 30
zeros = -0.0084, -0.0079, -0.0057, -0.0024, -0.0008, -0.0001, 0.0003
c = Curve(term, zeros)
fwd_term = 14/365.25, .25, .5, 1, 2, 5, 10
fwd_1m = -0.0057, -0.0057, -0.0053, -0.0036, -0.0010, 0.0014, 0.0066
f1 = Curve(fwd_term, fwd_1m)
fwd_3m = -0.0056, -0.0054, -0.0048, -0.0033, -0.0002, 0.0018, 0.0066
f3 = Curve(fwd_term, fwd_3m)
fwd_6m = -0.0053, -0.0048, -0.0042, -0.0022, 0.0002, 0.0022, 0.0065
f6 = Curve(fwd_term, fwd_6m)
'''


def get_step(diff, nums=10):
    try:
        step = diff / nums
    except TypeError:
        d, _ = diff.days, diff.years
        step = type(diff)(days=int(d / nums), years=(d / nums))
    return step


def rate_table(curve, x_grid=None, y_grid=None):
    if x_grid is None:
        if curve.origin in curve.domain:
            x_grid = curve.domain
        else:
            x_grid = [curve.origin] + curve.domain

    if y_grid is None:
        se_grid = tuple(zip(x_grid[:-1], x_grid[1:]))
        step = min(e - s for s, e in se_grid)
        ticks = list()
        for s, e in se_grid:
            line = [s]
            if s < s + step:
                while line[-1] + step < e:
                    line.append(line[-1] + step)
            ticks.append(line)
        ticks.append([(x_grid[-1],)])
        max_ticks = max(len(t) for t in ticks)
        y_grid = [step * i for i in range(max_ticks)]

    grid = list()
    grid.append(('',) + tuple(y_grid))
    for i, x in enumerate(x_grid):
        lst = x_grid[i + 1] if i < len(x_grid) - 1 \
            else x_grid[-1] + y_grid[-1] + y_grid[-1]
        grid.append(
            ((x,) + tuple(curve(x + y) for y in y_grid if x + y < lst)))
    return grid


def make_grid(curve, step=None, nums=10):
    domain = curve.domain
    grid = list()
    for start, stop in zip(domain[:-1], domain[1:]):
        grid.append(start)
        if step:
            s = step
        else:
            try:
                diff = stop - start
                s = diff / nums
            except TypeError:
                d = curve.day_count(start, stop) * 365.25
                s = type(diff)(days=int(d / nums))
        if s:
            while grid[-1] < stop:
                grid.append(grid[-1] + s)
    grid.append(domain[-1])
    return grid


def ax_plot_curve(ax, curve, func='get_zero_rate', grid=None, *args, **kwargs):
    if grid is None:
        step = kwargs.get('step', None)
        nums = kwargs.get('nums', 10)
        grid = make_grid(curve, step, nums)

    if not isinstance(func, (list, tuple)):
        func = [func]

    for f in func:
        if hasattr(curve, f):
            foo = getattr(curve, f)
            vals = [foo(t) for t in grid]
            ax.plot(grid, vals, label='curve.' + f + r'($t$)')

    return ax


def plot(curve, func='get_zero_rate', step=None, nums=10, *args, **kwargs):
    fig, ax = plt.subplots(figsize=(10, 5))
    grid = make_grid(curve, step, nums)
    ax_plot_curve(ax, curve, func, grid, step=step, nums=nums)
    ax.set_title('dcf curve plot')
    ax.set_xlabel(r'time $t$')
    ax.set_ylabel(r'$r(t)$')
    ax.legend()
    plt.show()


if __name__ == '__main__':
    from businessdate import BusinessDate, BusinessPeriod
    from dcf import ZeroRateCurve

    dates = [-1, 0, 1, 2, 3, 7, 10]
    dates = list(BusinessDate() + BusinessPeriod(years=d) for d in dates)
    rates = -0.01, -0.005, -0.001, 0.001, 0.005, 0.01, 0.005
    curve = ZeroRateCurve(dates, rates)
    curve.forward_tenor = '3M'
    func = 'get_zero_rate', 'get_cash_rate', 'get_short_rate'
    plot(curve, func, step='1m')
