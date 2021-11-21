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
from os import getcwd, name as os_name, linesep
from os.path import exists, basename, normpath, join
from shutil import rmtree

from .const import ICONS, SUB_FORMATTER_PREFIX
from .system_tools import shell, module

LEVEL = DEBUG

PATH = normpath("doc/sphinx/")
API_PATH = join(PATH, "api")
BUILD_PATH = join(PATH, "_build")
TREES_PATH = join(BUILD_PATH, "doctrees")

COVERAGE_FILE = "python.txt"
INDEX_FILE = "intro.html"


def _cmd(builder='html', fail_fast=False, warning_to_exception=True):
    tag = ' -t local'
    ff = "" if fail_fast else " --keep-going"
    warn = " -W" if warning_to_exception else ""
    doctrees = " -d " + join(BUILD_PATH, "doctrees")
    sourcedir = " " + PATH
    outputdir = " " + join(BUILD_PATH, builder)
    return tag + warn + ff + doctrees + sourcedir + outputdir


def _build(builder='html', fail_fast=False, warning_to_exception=True):
    return " -b " + builder + _cmd(builder, fail_fast, warning_to_exception)


def _make(builder='html', fail_fast=False, warning_to_exception=True):
    return " -M " + builder + _cmd(builder, fail_fast, warning_to_exception)


def api(pkg=basename(getcwd()), level=LEVEL, path=getcwd(), venv=None):
    """add api entries to docs"""
    log(INFO, ICONS["commit"] + 'run apidoc scripts')
    if exists(API_PATH):
        rmtree(API_PATH)
    cmd = "-o %s -f -E %s" % (API_PATH, pkg)
    return module('sphinx.ext.apidoc', cmd, level=level, path=path, venv=venv)


def doctest(fail_fast=False, level=LEVEL, path=getcwd(), venv=None):
    """run doctest, testing code examples in docs"""
    log(INFO, ICONS["test"] + 'run doctest scripts')
    cmd = _build('doctest', fail_fast=fail_fast)
    return module('sphinx', cmd, level=level, path=path, venv=venv)


def coverage(fail_fast=False, level=LEVEL, path=getcwd(), venv=None):
    """run doc coverage routines"""
    log(INFO, ICONS["coverage"] + 'run coverage scripts')
    cmd = _build('coverage', fail_fast=fail_fast)
    code = module('sphinx', cmd, level=level, path=path, venv=venv)
    coverage_file = join(BUILD_PATH, "coverage", COVERAGE_FILE)
    if exists(coverage_file):
        with open(coverage_file) as file:
            lines = file.read().split(linesep)
    for line in lines:
        log(INFO, ICONS[""] + SUB_FORMATTER_PREFIX + " " + line)
    return code


def html(fail_fast=False, level=LEVEL, path=getcwd(), venv=None):
    """build html documentation"""
    log(INFO, ICONS["html"] + 'build html documentation')
    cmd = _build('html', fail_fast=fail_fast)
    return module('sphinx', cmd, level=level, path=path, venv=venv)


def single(fail_fast=False, level=LEVEL, path=getcwd(), venv=None):
    """build single-html documentation"""
    log(INFO, ICONS["single"] + 'build single-html documentation')
    cmd = _build('singlehtml', fail_fast=fail_fast)
    return module('sphinx', cmd, level=level, path=path, venv=venv)


def epub(fail_fast=False, level=LEVEL, path=getcwd(), venv=None):
    """build epub documentation"""
    log(INFO, ICONS["epub"] + 'build epub documentation')
    cmd = _build('epub', fail_fast=fail_fast, warning_to_exception=False)
    return module('sphinx', cmd, level=level, path=path, venv=venv)


def latex(fail_fast=False, level=LEVEL, path=getcwd(), venv=None):
    """build latex documentation"""
    log(INFO, ICONS["latex"] + 'build latex documentation')
    cmd = _build('latex', fail_fast=fail_fast, warning_to_exception=False)
    return module('sphinx', cmd, level=level, path=path, venv=venv)


def pdf(fail_fast=False, level=LEVEL, path=getcwd(), venv=None):
    """build pdf documentation (`sphinx -M latexpdf`)"""
    log(INFO, ICONS["pdf"] + 'make latexpdf')
    cmd = _make('latexpdf', fail_fast, warning_to_exception=False)
    return module('sphinx', cmd, level=level, path=path, venv=venv)


def show(level=LEVEL, path=getcwd(), venv=None):
    """show html documentation"""
    index_file = join(BUILD_PATH, "html", INDEX_FILE)
    log(INFO, ICONS["show"] + 'find docs at %s' % join(getcwd(), index_file))
    if os_name == 'posix':
        return shell("open %s" % index_file, level=level, path=path, venv=venv)
    if os_name == 'nt':
        return shell("start %s" % index_file,
                     level=level, path=path, venv=venv)
    return 1


def cleanup(level=LEVEL, path=getcwd(), venv=None):
    """remove temporary files"""
    log(INFO, ICONS["clean"] + 'clean environment')
    cmd = "-M clean %s %s" % (PATH, BUILD_PATH)
    return module('sphinx', cmd, level=level, path=path, venv=venv)
