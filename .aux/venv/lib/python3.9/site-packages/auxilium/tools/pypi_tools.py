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

from auxilium.tools.const import ICONS
from auxilium.tools.system_tools import module

LEVEL = DEBUG


def deploy(usr, pwd, path=getcwd(), venv=None):
    """release on `pypi.org`"""
    log(INFO, ICONS["deploy"] + 'deploy release on `pypi.org`')
    # check dist
    module('twine', 'check --strict dist/*', path=path, venv=venv)
    # push to pypi.org
    return module("twine", "upload -u %s -p %s dist/*" % (usr, pwd),
                  level=LEVEL, path=path, venv=venv)
