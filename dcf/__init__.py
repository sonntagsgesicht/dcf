# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht
# Version:  0.99, copyright Monday, 31 March 2025
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


__doc__ = 'A Python library for generating discounted cashflows.'
__version__ = '0.99'
__dev_status__ = '4 - Beta'
__date__ = 'Monday, 31 March 2025'
__author__ = 'sonntagsgesicht'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__dependencies__ = 'prettyclass', 'curves', 'yieldcurves', 'tslist'
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()
__theme__ = 'sphinx_rtd_theme'

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


# todo:
#  [ ] test and doc with full coverage and updated README / HOWTO
#  [x] take numerics for curves
#  [x] make solver in ytm, fair, fit optional w/- default (yc.nx)
#  [x] pricer default arguments (valuation_date, payoff_model, ...)
#  [ ] better ModelUnitTests w/- bumps
#  [ ] add products: Bond, Mortgage, Swap, Cap, Floor, Collar, Option, Swaption
#  [ ] add sabr model
#  [x] CashFlow algebra CF + CF = CFList
#  [x] replace discount_curve by yield_curve
#  [x] rework/remove PayOffModel
#  [ ] rethink CashFlowPayOff as cf.amount() curve
#  [ ] better curve-id (str if len < 10 else id?)
#  [x] move optionpricing to yieldcurves as optioncurve


from . import plans  # noqa E401 E402

from .daycount import day_count  # noqa E401 E402
from .payoffs import (CashFlowPayOff, # noqa E401 E402
                      FixedCashFlowPayOff, # noqa E401 E402
                      RateCashFlowPayOff, # noqa E401 E402
                      OptionCashFlowPayOff, # noqa E401 E402
                      DigitalOptionCashFlowPayOff, # noqa E401 E402
                      CashFlowList)  # noqa E401 E402
from .pricer import ecf, pv, ytm, iac, fair, bpv, delta, fit  # noqa E401 E402

from .ratingclass import RatingClass  # noqa E401 E402
