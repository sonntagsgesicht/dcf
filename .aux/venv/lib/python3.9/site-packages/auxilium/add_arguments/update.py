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


from ..tools.docmaintain_tools import docmaintain, get_url, get_author
from ..tools.dulwich_tools import commit_git, pull_git, status_git
from ..tools.pip_tools import requirements, install, rollback, upgrade, \
    uninstall


def add_arguments(parser=None, config=ConfigParser()):
    parser = ArgumentParser() if parser is None else parser
    parser.add_argument(
        '--upgrade',
        metavar='PKG',
        nargs='?',
        const=config.getboolean('update', 'upgrade', fallback='pip'),
        help=upgrade.__doc__)
    parser.add_argument(
        '--install',
        action='store_const',
        const=not config.getboolean('update', 'install', fallback=False),
        default=config.getboolean('update', 'install', fallback=False),
        help=install.__doc__)
    parser.add_argument(
        '--requirements',
        action='store_const',
        const=not config.getboolean('update', 'requirements', fallback=False),
        default=config.getboolean('update', 'requirements', fallback=False),
        help=requirements.__doc__)
    parser.add_argument(
        '--header',
        action='store_const',
        const=not config.getboolean('update', 'header', fallback=True),
        default=config.getboolean('update', 'header', fallback=True),
        help=docmaintain.__doc__)
    parser.add_argument(
        '--status',
        action='store_const',
        const=not config.getboolean('update', 'status', fallback=False),
        default=config.getboolean('update', 'status', fallback=False),
        help=status_git.__doc__)
    parser.add_argument(
        '--commit',
        nargs='?',
        metavar='MSG',
        const=config.get('update', 'commit', fallback='Commit'),
        help=commit_git.__doc__)
    parser.add_argument(
        '--pull',
        nargs='?',
        metavar='BRANCH',
        const=config.get('update', 'pull', fallback='master'),
        help=pull_git.__doc__ + ' (requires REMOTE)')
    parser.add_argument(
        '--remote',
        default=config.get('build', 'remote', fallback=get_url()),
        help='remote `git` repo')
    parser.add_argument(
        '--remote_usr',
        metavar='USR',
        default=config.get('build', 'remote_usr', fallback=get_author()),
        help='user on remote `git` repo')
    parser.add_argument(
        '--remote_pwd',
        metavar='PWD',
        default=config.get('build', 'remote_pwd', fallback='None'),
        help='password/token on remote `git` repo')
    ignore = ' (ignores other input)'
    parser.add_argument(
        '--cleanup',
        action='store_const',
        const=not config.getboolean('update', 'cleanup', fallback=False),
        default=config.getboolean('update', 'cleanup', fallback=False),
        help=uninstall.__doc__ + ' and ' + rollback.__doc__ + ignore)
    return parser
