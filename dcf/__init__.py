# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Tuesday, 31 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


__doc__ = 'A Python library for generating discounted cashflows.'
__version__ = '0.8'
__dev_status__ = '4 - Beta'
__date__ = 'Thursday, 02 June 2022'
__author__ = 'sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__dependencies__ = ()
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()
__theme__ = 'sphinx_rtd_theme'

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


# todo:
#  [ ] fix test and qa
#  [ ] doc with full coverage and updated README / HOWTO
#  [X] add ts() to day_count to handle date/datetime __ts__ in TS list
#  [X] TSList[s:e:-1] := TSList[s:e][::-1]
#  [ ] pricer default arguments (valuation_date, payoff_model, ...)
#  [ ] add FxContainer for currency (or move to yieldcurves ?)
#  [ ] add products (Bond, Swap, Cap, Floor, Collar, Option, Swaption)
#  [ ] better BumpGreeksModelUnitTests and BinaryModelUnitTests
#  [ ] add sabr model


from . import plans, optionpricing  # noqa E401 E402
from .tools.dc import day_count  # noqa E401 E402
from .tools.ts import TS, TSList  # noqa E401 E402

from .cashflowlist import CashFlowList  # noqa E401 E402
from .payoffs import (CashFlowPayOff, FixedCashFlowPayOff, RateCashFlowPayOff, # noqa E401 E402
                      OptionCashFlowPayOff, OptionStrategyCashFlowPayOff, # noqa E401 E402
                      ContingentRateCashFlowPayOff)  # noqa E401 E402
from .payoffmodels import PayOffModel, OptionPayOffModel  # noqa E401 E402
from .pricer import ecf, pv, ytm, iac, fair, bpv, delta, fit  # noqa E401 E402

from .ratingclass import RatingClass  # noqa E401 E402
