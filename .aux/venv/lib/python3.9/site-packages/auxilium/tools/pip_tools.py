# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from logging import log, INFO, WARN
from os import getcwd
from os.path import basename, exists, join

from auxilium.tools.const import ICONS, FREEZE_FILE, TEMP_REMOVE_FILE
from auxilium.tools.system_tools import module, del_tree


def upgrade(pkg='pip', path=getcwd(), venv=None):
    """upgrade python library [PKG] via `pip`"""
    log(INFO, ICONS["upgrade"] + 'upgrade `%s`' % pkg)
    return module('pip', 'install --upgrade %s' % pkg, path=path, venv=venv)


def requirements(path=getcwd(), freeze_file=FREEZE_FILE, venv=None):
    """manage requirements (dependencies) in `requirements.txt`
        and `upgrade_requirements.txt`"""
    log(INFO, ICONS["setup"] + "setup environment requirements")

    code = False
    if freeze_file and not exists(join(path, freeze_file)):
        code = code or module('pip', "freeze > %s" % freeze_file,
                              path=path, venv=venv)

    if exists(join(path, "requirements.txt")):
        code = code or module('pip', "install -r requirements.txt",
                              path=path, venv=venv)

    if exists(join(path, "upgrade_requirements.txt")):
        code = code or module('pip',
                              "install --upgrade -r upgrade_requirements.txt",
                              path=path, venv=venv)
    return code


def install(pkg='.', path=getcwd(), venv=None):
    """(re)install current project via `pip install -e .`"""
    log(INFO, ICONS["install"] + 'install project via pip install -e')
    if exists('setup.py') or exists('setup.cfg'):
        return module('pip', "install --upgrade -e %s" % pkg,
                      path=path, venv=venv)
    log(WARN, ICONS["warn"] +
        'could not install project via pip install -e '
        '(setup.py or setup.cfg not found in %s)' % path)
    return 1


def uninstall(pkg=basename(getcwd()), path=getcwd(), venv=None):
    """uninstall current project via `pip uninstall`"""
    log(INFO, ICONS["uninstall"] + 'uninstall project via pip uninstall')
    # code = code or del_tree(basename(path) + ".egg-info", ".eggs")
    return module('pip', "uninstall -y %s" % pkg, path=path, venv=venv)


def rollback(path=getcwd(), freeze_file=FREEZE_FILE, venv=None):
    """rollback site-packages"""
    log(INFO, ICONS["clean"] + 'rollback site-packages')
    code = False
    if exists(join(path, freeze_file)):
        code = code or module('pip', "freeze --exclude-editable > %s" %
                              TEMP_REMOVE_FILE, path=path, venv=venv)
        code = code or module('pip', "uninstall -r %s -y" % TEMP_REMOVE_FILE,
                              path=path, venv=venv)
        del_tree(TEMP_REMOVE_FILE)
        code = code or module('pip', "install --upgrade -r %s" % freeze_file,
                              path=path, venv=venv)
        del_tree(join(path, freeze_file))
    return code
