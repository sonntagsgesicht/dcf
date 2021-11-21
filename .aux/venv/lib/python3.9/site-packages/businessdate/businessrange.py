# -*- coding: utf-8 -*-

# businessdate
# ------------
# Python library for generating business dates for fast date operations
# and rich functionality.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.5, copyright Wednesday, 18 September 2019
# Website:  https://github.com/sonntagsgesicht/businessdate
# License:  Apache License 2.0 (see LICENSE file)


from .businessperiod import BusinessPeriod
from .businessdate import BusinessDate


class BusinessRange(list):
    def __init__(self, start, stop=None, step=None, rolling=None):
        """ class to build list of business days

        :param BusinessDate start: date to begin schedule,
         if stop not given, start will be used as stop and
         default in rolling to :class:`BusinessDate() <BusinessDate>`
        :param BusinessDate stop: date to stop before,
         if not given, start will be used for stop instead
        :param BusinessPeriod step: period to step schedule,
         if not given 1 day is default
        :param BusinessDate rolling: date to roll on
         (forward and backward) between start and stop,
         if not given default will be start

        **Ansatz** First, `rolling` and `step`
        defines a infinite grid of dates.
        Second, this grid is sliced by `start` (included ,
        if meeting the grid) and `end` (excluded).

        """

        # set default args and build range grid
        start, stop, step, rolling = self._default_args(start, stop, step, rolling)
        schedule = self._build_grid(start, stop, step, rolling)

        # push to super and sort
        super(BusinessRange, self).__init__(set(schedule))
        self.sort()

    @staticmethod
    def _default_args(start, stop, step, rolling):
        if stop is None:
            stop = start
            start = BusinessDate()
        if step is None:
            step = BusinessPeriod(days=1)
        if rolling is None:
            rolling = start
        # make proper businessdate objects
        start = BusinessDate(start)
        rolling = BusinessDate(rolling)
        stop = BusinessDate(stop)
        step = BusinessPeriod(step)
        return BusinessDate(start), BusinessDate(stop), BusinessPeriod(step), BusinessDate(rolling)

    @staticmethod
    def _build_grid(start, stop, step, rolling):
        # setup grid and turn step into positive direction
        grid = list()
        step = step if rolling <= rolling + step else -1 * step

        # roll backward before start
        i = 0
        while start <= rolling + step * i:
            i -= 1

        # fill grid from start until end
        current = rolling + step * i
        while current < stop:
            if start <= current < stop:
                grid.append(current)
            i += 1
            current = rolling + step * i

        return grid

    def adjust(self, convention='', holidays=None):
        """ returns adjusted :class:`BusinessRange` following given convention

        For details of adjusting :class:`BusinessDate` see :meth:`BusinessDate.adjust`.

        For possible conventions invoke :meth:`BusinessDate().adjust() <BusinessDate.adjust>`

        For more details on the conventions see module :mod:`conventions <businessdate.conventions>`)
        """

        adj_list = [d.adjust(convention, holidays) for d in self]
        del self[:]
        super(BusinessRange, self).extend(adj_list)
        return self
