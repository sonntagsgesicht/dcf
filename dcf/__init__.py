# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.6.1, copyright Tuesday, 11 January 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


__doc__ = 'A Python library for generating discounted cashflows.'
__version__ = '0.6.1'
__dev_status__ = '4 - Beta'
__date__ = 'Friday, 14 January 2022'
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

# from .interpolation import *
# from .compounding import *
from .curve import Curve, DateCurve, RateCurve, rate_table  # noqa E401 E402
from .interestratecurve import CashRateCurve, InterestRateCurve, \
    DiscountFactorCurve, ZeroRateCurve, ShortRateCurve  # noqa E401 E402
from .creditcurve import SurvivalProbabilityCurve, \
    MarginalSurvivalProbabilityCurve, MarginalDefaultProbabilityCurve, \
    CreditCurve, ProbabilityCurve, FlatIntensityCurve, \
    DefaultProbabilityCurve, HazardRateCurve  # noqa E401 E402
from .volatilitycurve import VolatilityCurve, TerminalVolatilityCurve, \
    InstantaneousVolatilityCurve  # noqa E401 E402
from .fx import FxCurve, FxContainer, Price, FxRate  # noqa E401 E402
from .cashflow import CashFlowList, FixedCashFlowList, RateCashFlowList, \
    CashFlowLegList  # noqa E401 E402
from .contingent import ContingentCashFlowList, \
    ContingentRateCashFlowList  # noqa E401 E402
from .ratingclass import RatingClass  # noqa E401 E402
from .plans import same, bullet, amortize, annuity, consumer, \
    outstanding, DEFAULT_AMOUNT  # noqa E401 E402
from .pricer import get_present_value, get_par_rate, get_interest_accrued, \
    get_yield_to_maturity, get_basis_point_value  # noqa E401 E402
from .products import bond, interest_rate_swap, asset_swap  # noqa E401 E402
