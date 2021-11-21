# -*- coding: utf-8 -*-

# sphinx_pytype_substitution
# --------------------------
# auto substitution for python types like modules, classes and functions
# (created by auxilium)
#
# Author:   sonntagsgesicht
# Version:  0.1, copyright Sunday, 10 October 2021
# Website:  https://github.com/sonntagsgesicht/sphinx-pytype-substitution
# License:  Apache License 2.0 (see LICENSE file)


import logging

from os import linesep

from .substitution_collection import SubstitutionCollection

logging.getLogger(__name__).addHandler(logging.NullHandler())

__doc__ = 'auto substitution for python types like ' \
          'modules, classes and functions (created by auxilium)'
__license__ = 'Apache License 2.0'

__author__ = 'sonntagsgesicht'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/sphinx-pytype-substitution'

__date__ = 'Sunday, 10 October 2021'
__version__ = '0.1'
__dev_status__ = '3 - Alpha'  # '4 - Beta'  or '5 - Production/Stable'

__dependencies__ = ()
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()


def config_inited(app, config):
    coll = SubstitutionCollection(
        *config.pytype_substitutions,
        match_pattern=config.pytype_match_pattern,
        exclude_pattern=config.pytype_exclude_pattern,
        short=config.pytype_short_ref)
    if config.rst_epilog is None:
        config.rst_epilog = ''
    config.rst_epilog += linesep + str(coll)


def setup(app):

    app.connect('config-inited', config_inited)

    app.add_config_value('pytype_substitutions', (), False)
    app.add_config_value('pytype_buildins', False, False, (bool,))
    app.add_config_value('pytype_short_ref', False, False, (bool,))
    app.add_config_value('pytype_match_pattern', '', False, (str,))
    app.add_config_value('pytype_exclude_pattern', '', False, (str,))

    return {'parallel_read_safe': True, 'parallel_write_safe': True}
