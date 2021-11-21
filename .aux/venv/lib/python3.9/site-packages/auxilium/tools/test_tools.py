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

from .const import TEST_PATH, ICONS
from .system_tools import python as _python, module, del_tree


LEVEL = INFO


def test(test_dir=TEST_PATH, fail_fast=False, path=getcwd(), venv=None):
    """test code by running tests"""
    log(INFO, ICONS["test"] + 'run test scripts')
    return test_unittest(test_dir, fail_fast=fail_fast, path=path, venv=venv)


def test_unittest(test_dir=TEST_PATH,
                  fail_fast=False, path=getcwd(), venv=None):
    """test code by running unittest"""
    ff = ' --failfast' if fail_fast else ''
    cmd = 'discover %s%s -v -p "*.py"' % (test_dir, ff)
    return module('unittest', cmd, level=LEVEL, path=path, venv=venv)


def test_pytest(test_dir=TEST_PATH,
                fail_fast=False, path=getcwd(), venv=None):
    """test code by running pytest"""
    ff = " --exitfirst" if fail_fast else ''
    return module('pytest', '%s%s' % (test_dir, ff), path=path, venv=venv)


def doctests(pkg=basename(getcwd()),
             fail_fast=False, path=getcwd(), venv=None):
    """test code in doc string (doctest)"""
    log(INFO, ICONS["doctest2"] + 'run doctest scripts')
    cmd = 'import doctest, %s as pkg; doctest.testmod(pkg, verbose=True)' % pkg
    return _python('-c "%s"' % cmd, path=path, venv=venv)


def cleanup(test_dir=TEST_PATH):
    """remove temporary files"""
    log(INFO, ICONS["clean"] + 'clean test results')
    # removed pytest data files
    del_tree(".pytest_cache")
    return 0
