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

from ..tools.pip_tools import rollback, uninstall
from ..tools.system_tools import create_venv, VENV_PATH


def add_arguments(parser=None, config=ConfigParser()):
    parser = ArgumentParser() if parser is None else parser
    parser.add_argument(
        '--name',
        default=config.get('create', 'author', fallback=None),
        help='project name')
    parser.add_argument(
        '--slogan',
        default=config.get('create', 'slogan', fallback=None),
        help='project slogan')
    parser.add_argument(
        '--author',
        default=config.get('create', 'author', fallback=None),
        help='project author')
    parser.add_argument(
        '--email',
        default=config.get('create', 'email', fallback=None),
        help='project email')
    parser.add_argument(
        '--url',
        default=config.get('create', 'url', fallback=None),
        help='project url')
    parser.add_argument(
        '--venv',
        metavar='PATH',
        nargs='?',
        const=None,
        default=config.get('create', 'venv', fallback=VENV_PATH),
        help='PATH to ' + create_venv.__doc__)
    parser.add_argument(
        '--update',
        action='store_const',
        const=not config.get('create', 'update', fallback=False),
        default=config.get('create', 'update', fallback=False),
        help='just (re)install/update virtual environment '
             '(skip to create project as well as commit)')
    parser.add_argument(
        '--commit',
        nargs='?',
        metavar='MSG',
        const=None,
        default=config.get('create', 'commit', fallback='Initial commit'),
        help='commit on successful creation')
    ignore = ' (ignores other input)'
    parser.add_argument(
        '--cleanup',
        action='store_const',
        const=not config.getboolean('update', 'cleanup', fallback=False),
        default=config.getboolean('update', 'cleanup', fallback=False),
        help=uninstall.__doc__ + ' and ' + rollback.__doc__ + ignore)
    return parser
