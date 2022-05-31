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
__version__ = '0.7'
__dev_status__ = '4 - Beta'
__date__ = 'Tuesday, 31 May 2022'
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
#  better BumpGreeksModelUnitTests and BinaryModelUnitTests
#  add sabr model
#  add Nelson-Siegel-Svensson interest rate curve
#  add Curve.plot()
#  add global calibration using 'lmfit'
#  add compounding as property to RateCurve


from . import daycount, compounding, interpolation, plans, \
    models  # noqa E401 E402

from .curves.curve import Curve, DateCurve, RateCurve, \
    rate_table, Price, ForwardCurve  # noqa E401 E402
from .curves.creditcurve import DefaultProbabilityCurve, FlatIntensityCurve, \
    HazardRateCurve, MarginalDefaultProbabilityCurve, \
    MarginalSurvivalProbabilityCurve, SurvivalProbabilityCurve, \
    ProbabilityCurve, CreditCurve  # noqa E401 E402
from .curves.interestratecurve import InterestRateCurve, DiscountFactorCurve, \
    CashRateCurve, ZeroRateCurve, ShortRateCurve  # noqa E401 E402
from .curves.fx import FxForwardCurve, FxContainer, Price, FxRate  # noqa E401 E402
from .curves.volatilitycurve import VolatilityCurve, TerminalVolatilityCurve, \
    InstantaneousVolatilityCurve  # noqa E401 E402

from .cashflows.cashflow import CashFlowList, FixedCashFlowList, \
    RateCashFlowList, CashFlowLegList  # noqa E401 E402
from .cashflows.contingent import ContingentCashFlowList, \
    ContingentRateCashFlowList, OptionCashflowList, \
    OptionStrategyCashflowList  # noqa E401 E402
from .cashflows.payoffs import CashFlowPayOff, FixedCashFlowPayOff, \
    RateCashFlowPayOff, OptionCashFlowPayOff, OptionStrategyCashFlowPayOff, \
    ContingentRateCashFlowPayOff  # noqa E401 E402
from .cashflows.products import \
    bond, interest_rate_swap, asset_swap  # noqa E401 E402

from .ratingclass import RatingClass  # noqa E401 E402

from .pricer import get_present_value, get_fair_rate, get_interest_accrued, \
    get_yield_to_maturity, get_basis_point_value, \
    get_bucketed_delta, get_curve_fit  # noqa E401 E402
