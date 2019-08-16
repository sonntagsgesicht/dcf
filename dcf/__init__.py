# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Tuesday 13 August 2019
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from datetime import datetime

__doc__ = 'A Python library for generating discounted cashflows.'
__version__ = '0.3'
__date__ = datetime.today().strftime('%A %d %B %Y')
__author__ = 'sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__packages__ = (__name__,)
__dependencies__ = ()

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .interpolation import *
from .compounding import *
from .curve import *
from .interestratecurve import *
from .fx import *
from .creditcurve import *
from .ratingclass import *
from .cashflow import *
from .volatilitycurve import *
