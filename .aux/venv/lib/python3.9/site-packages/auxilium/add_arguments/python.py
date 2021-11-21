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


def add_arguments(parser=None, config=ConfigParser()):
    parser = ArgumentParser() if parser is None else parser
    invoke_opts = parser.add_mutually_exclusive_group()
    invoke_opts.set_defaults(mode='default')
    invoke_opts.add_argument(
        '-c',
        metavar='cmd',
        help='program passed in as string (terminates option list)')
    invoke_opts.add_argument(
        '-m',
        metavar='mod',
        help='run library module as a script (terminates option list)')
    invoke_opts.add_argument(
        '-f',
        metavar='file',
        help='program read from script file')
    invoke_opts.add_argument(
        '-',
        dest='stdin',
        action='store_const',
        const=True,
        help='program read from stdin (default; interactive mode if a tty)')
    arg = parser.add_argument_group()

    arg.add_argument(
        'arg',
        nargs='*',
        help='arguments passed to program in sys.argv[1:]')
    return parser
