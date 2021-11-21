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

from auxilium.tools.sphinx_tools import api, doctest, show, pdf, cleanup


def add_arguments(parser=None, config=ConfigParser()):
    parser = ArgumentParser() if parser is None else parser
    parser.add_argument(
        '-ff', '--fail-fast',
        action='store_const',
        const=not config.getboolean('doc', 'fail-fast', fallback=False),
        default=config.getboolean('doc', 'fail-fast', fallback=False),
        help='stop on first fail or error')
    parser.add_argument(
        '--commit',
        nargs='?',
        metavar='MSG',
        const=config.get('doc', 'commit', fallback='Commit doc build'),
        help='auto commit on successful doc build run (incl. doctest)')
    parser.add_argument(
        '--api',
        action='store_const',
        const=not config.getboolean('doc', 'api', fallback=False),
        default=config.getboolean('doc', 'api', fallback=False),
        help=api.__doc__)
    parser.add_argument(
        '--doctest',
        action='store_const',
        const=not config.getboolean('doc', 'doctest', fallback=True),
        default=config.getboolean('doc', 'doctest', fallback=True),
        help=doctest.__doc__)
    parser.add_argument(
        '--coverage',
        action='store_const',
        const=not config.getboolean('doc', 'coverage', fallback=True),
        default=config.getboolean('doc', 'coverage', fallback=True),
        help=doctest.__doc__)
    parser.add_argument(
        '--pdf',
        action='store_const',
        const=not config.getboolean('doc', 'pdf', fallback=False),
        default=config.getboolean('doc', 'pdf', fallback=False),
        help=pdf.__doc__)
    parser.add_argument(
        '--show',
        action='store_const',
        const=not config.getboolean('doc', 'show', fallback=False),
        default=config.getboolean('doc', 'show', fallback=False),
        help=show.__doc__)
    parser.add_argument(
        '--cleanup',
        action='store_const',
        const=not config.getboolean('doc', 'cleanup', fallback=False),
        default=config.getboolean('doc', 'cleanup', fallback=False),
        help=cleanup.__doc__)
    return parser
