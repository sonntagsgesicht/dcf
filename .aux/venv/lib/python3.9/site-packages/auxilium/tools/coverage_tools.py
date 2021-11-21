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
from .system_tools import module, del_tree, join


LEVEL = INFO


def coverage(pkg=basename(getcwd()), test_dir=TEST_PATH,
             min_cov='', fail_fast=False, path=getcwd(), venv=None):
    """check code coverage of tests"""
    log(INFO, ICONS["coverage"] + 'run test coverage scripts')
    return coverage_coverage(pkg, test_dir, min_cov,
                             fail_fast=fail_fast, path=path, venv=venv)


def coverage_test(test_dir=TEST_PATH,
                  min_cov='', fail_fast=False, path=getcwd(), venv=None):
    """check code coverage of tests with native test"""
    return module('test', '--coverage -D `pwd`/coverage_data %s' % test_dir,
                  level=LEVEL, path=path, venv=venv)


def coverage_pytest(test_dir=TEST_PATH,
                    min_cov='', fail_fast=False, path=getcwd(), venv=None):
    """check code coverage of tests with pytest"""
    ff = " --exitfirst" if fail_fast else ''
    mc = " --cov-fail-under=%s" % min_cov if min_cov else ''
    return module('pytest', '-q --cov %s%s%s' % (test_dir, ff, mc),
                  level=LEVEL, path=path, venv=venv)


def coverage_coverage(pkg=basename(getcwd()), test_dir=TEST_PATH,
                      min_cov='', fail_fast=False, path=getcwd(), venv=None):
    """check code coverage of tests with coverage"""
    # COVERAGE_FILE = join(AUX_PATH, '.coverage')
    ff = ' --failfast' if fail_fast else ''
    cmd = 'run --include="%s*"  --module' \
          ' unittest discover %s%s -v -p "*.py"' % (pkg, test_dir, ff)
    exit_code = module('coverage', cmd, path=path, venv=venv)
    if exit_code:
        return exit_code
    mc = " --fail-under=%s" % min_cov if min_cov else ''
    cmd = 'report -m %s' % mc
    return module('coverage', cmd, level=LEVEL, path=path, venv=venv)


def cleanup(test_dir=TEST_PATH):
    """remove temporary files"""
    log(INFO, ICONS["clean"] + 'clean coverage')
    # removed coverage data files incl. files in test dir
    files = ".coverage", "coverage.xml", "htmlcov"
    del_tree(*files)
    del_tree(*(join(test_dir, f) for f in files))
    return 0
