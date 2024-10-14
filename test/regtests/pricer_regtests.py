# -*- coding: utf-8 -*-

# auxilium
# --------
# A Python project for an automated test and deploy toolkit - 100%
# reusable.
#
# Author:   sonntagsgesicht
# Version:  0.1.4, copyright Sunday, 11 October 2020
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from regtest import RegressionTestCase


# first run will build reference values (stored in files)
# second run will test against those reference values
# to update reference values simply remove the according files


class PricerRegTests(RegressionTestCase):

    ...
