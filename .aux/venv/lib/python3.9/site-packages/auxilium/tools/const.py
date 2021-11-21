# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from os import name as os_name
from os.path import basename, join, normpath
from sys import executable

PYTHON = basename(executable)
REPLACE = ":()-*.#/\\'?!<>" + '"'
DEMO_PATH = "auxilium_demo"
PROFILE_PATH = "dev.py"
TEST_PATH = normpath('test/')

AUX_PATH = '.aux'
LAST_M_FILE = join(AUX_PATH, 'last.json')
CONFIG_PATH = join(AUX_PATH, 'config')
VENV_PATH = join(AUX_PATH, 'venv')

FREEZE_FILE = join(AUX_PATH, '.freeze')
TEMP_REMOVE_FILE = join(AUX_PATH, '.site_packages_to_remove')

GIT_PATH = '.git'

if os_name == 'nt':
    VENV_TAIL = join('Scripts', PYTHON)
    VENV = join(VENV_PATH, VENV_TAIL)
elif os_name == 'posix':
    VENV_TAIL = join('bin', PYTHON)
    VENV = join(VENV_PATH, VENV_TAIL)
else:
    VENV_TAIL = ''
    VENV = PYTHON

DETAIL_FORMATTER = '%(levelname)-7.7s  %(message)s'
MINIMAL_FORMATTER = ' %(message)s'
TEST_LOG_FORMATTER = '•' + MINIMAL_FORMATTER

VERBOSITY_LEVELS = (
    (20, MINIMAL_FORMATTER),
    (0, MINIMAL_FORMATTER),
    (10, MINIMAL_FORMATTER),
    (20, DETAIL_FORMATTER),
    (30, DETAIL_FORMATTER),
    (40, DETAIL_FORMATTER),
    (50, DETAIL_FORMATTER)
    )

SUB_FORMATTER_PREFIX = '|'


_ICONS = {
    # basic
    'ok': '✅',
    'cancel': '❌',
    # log level
    'debug': '🪲',
    'info': 'ℹ️',
    'warn': '✋',
    'warning': '✋',
    'error': '🚫',
    # git
    'init': '🐣',
    'clone': '🧪',
    'branch': '📦',
    'checkout': '🔘',
    'add': '➕',
    'missing': '🤷',
    'status': '🔄',
    'commit': '📌',
    'tag': '🏷',
    'pull': '📥',
    'push': '📤',
    # commands
    'python': '🐍',
    'run': '👟',
    'demo': '🍹',
    'uninstall': '💔',
    'clean': '🧹',
    'finish': '🏁',
    # create
    'create': '🪚',
    'setup': '🧰',  # '⚙️',
    'install': '🗜',
    'venv': '👻',
    # update
    'maintenance': '🛠',
    'upgrade': '🏅',
    # test
    'test': '⛑',
    'quality': '🔍',
    'security': '🚨',
    'inspect': '🕶',
    'coverage': '📑',
    'profile': '⏱',
    # doc
    'apidoc': '✏️',
    'html': '🌐',
    'single': '🪧',
    'epub': '📕',
    'latex': '📒',
    'pdf': '📗',
    'show': '💡',
    # build
    'build': '🏗',
    'deploy': '🛫',
}


class IconContainer(dict):
    none = ''
    default = '*'
    length = 3, 1

    def __getitem__(self, item):
        item = item.lower()
        if super(IconContainer, self).__contains__(item):
            value = super(IconContainer, self).__getitem__(item)
            if value is None:
                value = ''
        elif not item:
            value = ''
        else:
            value = '*'
        length, pre = self.__class__.length
        value = value.ljust(length if len(value.encode()) < 4 else length-1)
        return ' ' * pre + value


ICONS = IconContainer(_ICONS)
