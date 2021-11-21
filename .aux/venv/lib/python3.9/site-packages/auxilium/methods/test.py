# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from os import getcwd
from os.path import basename
from logging import log, ERROR

from ..tools.const import ICONS
from ..tools.coverage_tools import coverage as _coverage, \
    cleanup as cleanup_coverage
from ..tools.dulwich_tools import add_and_commit_git
from ..tools.quality_tools import quality as _quality
from ..tools.security_tools import security as _security
from ..tools.test_tools import test as _test, cleanup as cleanup_test


def do(pkg=basename(getcwd()), testpath=None, commit=None, fail_fast=None,
       quality=None, security=None, coverage=None, cleanup=None,
       path=None, env=None, **kwargs):
    """run test process"""

    if cleanup:
        return cleanup_test(path) or cleanup_coverage(path)

    code = False
    if quality:
        code = code or _quality(pkg, path=path, venv=env)
    if security:
        code = code or _security(pkg, path=path, venv=env)
    if path:
        code = code or _test(testpath,
                             fail_fast=fail_fast, path=path, venv=env)
        if coverage:
            code = code or _coverage(pkg, testpath, min_cov=coverage,
                                     fail_fast=fail_fast, path=path, venv=env)
        if commit:
            code = code or add_and_commit_git(commit, path=path, venv=env)
    elif commit:
        log(ERROR, ICONS["error"] + 'test missing - did not commit')
        code = True
    return code
