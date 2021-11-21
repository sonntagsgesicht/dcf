# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from argparse import ArgumentParser
from configparser import ConfigParser

from ..tools.test_tools import cleanup as cleanup_test
from ..tools.security_tools import security
from ..tools.quality_tools import quality
from ..tools.coverage_tools import coverage

from ..tools.const import TEST_PATH


def add_arguments(parser=None, config=ConfigParser()):
    parser = ArgumentParser() if parser is None else parser
    parser.add_argument(
        'testpath',
        metavar='TESTMATH',
        nargs='?',
        default=config.get('test', 'testpath', fallback=TEST_PATH),
        help='path to directory where test are found')
    parser.add_argument(
        '-ff', '--fail-fast',
        action='store_const',
        const=not config.getboolean('test', 'fail-fast', fallback=False),
        default=config.getboolean('test', 'fail-fast', fallback=False),
        help='stop on first fail or error')
    parser.add_argument(
        '--commit',
        nargs='?',
        metavar='MSG',
        const=config.get('test', 'commit', fallback='Commit tested'),
        help='auto commit on successful test run')
    parser.add_argument(
        '--coverage',
        nargs='?',
        metavar='MIN',
        const=config.get('test', 'coverage', fallback=''),
        default=config.get('test', 'coverage', fallback='0'),
        help=coverage.__doc__ + ' - fail on total coverage less than MIN')
    parser.add_argument(
        '--quality',
        action='store_const',
        const=not config.getboolean('test', 'quality', fallback=True),
        default=config.getboolean('test', 'quality', fallback=True),
        help=quality.__doc__)
    parser.add_argument(
        '--security',
        action='store_const',
        const=not config.getboolean('test', 'security', fallback=True),
        default=config.getboolean('test', 'security', fallback=True),
        help=security.__doc__)
    parser.add_argument(
        '--cleanup',
        action='store_const',
        const=not config.getboolean('test', 'cleanup', fallback=False),
        default=config.getboolean('test', 'cleanup', fallback=False),
        help=cleanup_test.__doc__)
    return parser
