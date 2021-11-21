# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from logging import log, INFO, DEBUG
from os import getcwd
from os.path import basename

from auxilium.tools.const import ICONS
from auxilium.tools.system_tools import python as _python, module, del_tree

LEVEL = DEBUG


def build(path=getcwd(), venv=None):
    """build package distribution"""
    log(INFO, ICONS["build"] + 'build package distribution')
    code = False
    code = code or _python("setup.py build",
                           level=LEVEL, path=path, venv=venv)
    code = code or _python("setup.py sdist --formats=zip",
                           level=LEVEL, path=path, venv=venv)
    code = code or module("twine", "check --strict dist/*",
                          level=LEVEL, path=path, venv=venv)
    return code


def cleanup(pkg=basename(getcwd())):
    """remove temporary files"""
    log(INFO, ICONS["clean"] + 'cleanup build')
    # remove setuptools release files
    del_tree("build", "dist")
    return 0
