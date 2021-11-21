# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from logging import log, INFO
from os import getcwd
from os.path import basename

from .const import ICONS
from .system_tools import module


def quality(pkg=basename(getcwd()), path=getcwd(), venv=None):
    """evaluate quality of source code"""
    log(INFO, ICONS["quality"] + 'evaluate quality of source code')
    return quality_flake8(pkg, path=path, venv=venv)


def quality_pylint(pkg=basename(getcwd()), path=getcwd(), venv=None):
    """evaluate quality of source code with pylint"""
    return module('pylint', pkg, path=path, venv=venv)


def quality_flake8(pkg=basename(getcwd()), path=getcwd(), venv=None):
    """evaluate quality of source code with flake8"""
    return module('flake8', pkg, path=path, venv=venv)


def quality_pep8(pkg=basename(getcwd()), path=getcwd(), venv=None):
    """evaluate quality of source code with pep8/pep257"""
    exit_status = module('pycodestyle', pkg, venv=venv)
    return exit_status or module('pydocstyle', pkg, path=path, venv=venv)
