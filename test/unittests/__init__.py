# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


import sys
sys.path.append('dcf/')
sys.path.append('.')
sys.path.append('..')

from .curve_tests import *
from .cashflow_tests import *
from .creditcurve_tests import *
from .compounding_tests import *
from .interestratecurve_tests import *
from .interpolation_tests import *
from .fx_tests import *
from .plans_tests import *
from .pricer_tests import *
from .rating_tests import *
from .forwardcurve_tests import *
from .model_tests import *
from .contingent_tests import *
