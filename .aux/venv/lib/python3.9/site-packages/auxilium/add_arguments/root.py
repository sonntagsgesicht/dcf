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

from ..tools.const import VENV, DEMO_PATH


def add_arguments(parser=None, config=ConfigParser()):
    parser = ArgumentParser() if parser is None else parser

    parser.add_argument(
        '-v', '--verbosity',
        action='count',
        default=0,
        help='set logging level '
             '(-v=ALL, -vv=DEBUG, -vvv=INFO, -vvvv=WARNING, -vvvvv=ERROR) '
             '(default: INFO)')

    parser.add_argument(
        '-V', '--version',
        action='store_true',
        help='show version and exit')

    env = config.get('DEFAULT', 'env', fallback=VENV)
    parser.add_argument(
        '-e', '--env',
        metavar='PATH',
        nargs='?',
        const=None,
        default=config.get('DEFAULT', 'env', fallback=env),
        help='set path to python executable or virtual environment. '
             'to use system interpreter just set empty flag `-e`')

    parser.add_argument(
        '-x', '--exit-status',
        action='count',
        default=0,
        help='exit status in case of failure '
             '(-x for zero,'
             ' -xx for non-zero,'
             ' -xxx for raise exception)'
             ' (default: non-zero')

    parser.add_argument(
        '-p', '--pre',
        metavar='SCRIPT',
        nargs='?',
        default=config.get('DEFAULT', 'pre', fallback=''),
        help="pre run script, "
             "which is executed before every command "
             "(except 'create' and 'python')")

    parser.add_argument(
        '-d', '--demo',
        metavar='NAME',
        nargs='?',
        const=config.get('DEFAULT', 'demo', fallback=DEMO_PATH),
        help='starts a demo in creating a repo')

    return parser
