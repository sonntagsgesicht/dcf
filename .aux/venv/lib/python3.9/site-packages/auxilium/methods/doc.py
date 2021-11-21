# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from logging import log, WARN
from os import getcwd
from os.path import basename

from ..tools.const import ICONS
from ..tools.dulwich_tools import add_and_commit_git
from ..tools.sphinx_tools import api as _api, doctest as _doctest, \
    html, latex, epub, single, \
    pdf as _pdf, show as _show, cleanup as _cleanup, coverage as _coverage


def do(pkg=basename(getcwd()), commit=None, fail_fast=None, pdf=None,
       api=None, doctest=None, show=None, cleanup=None, coverage=None,
       path=None, env=None, **kwargs):
    if cleanup:
        return _cleanup(venv=env)

    code = False
    if api:
        code = code or _cleanup(path=path, venv=env)
        code = code or _api(pkg=pkg, path=path, venv=env)
    if doctest:
        code = code or _doctest(fail_fast=fail_fast, path=path, venv=env)
    if coverage:
        code = code or _coverage(fail_fast=fail_fast, path=path, venv=env)
    code = code or html(fail_fast=fail_fast, path=path, venv=env)
    if show:
        code = code or _show(env)
    code = code or single(fail_fast=fail_fast, path=path, venv=env)
    code = code or epub(fail_fast=fail_fast, path=path, venv=env)
    code = code or latex(fail_fast=fail_fast, path=path, venv=env)
    if pdf:
        code = code or _pdf(fail_fast=fail_fast, path=path, venv=env)
    if commit:
        if doctest:
            code = code or add_and_commit_git(commit, path=path, venv=env)
        else:
            log(WARN, ICONS["warn"] +
                'doctest or build missing - did not commit')
            code = True
    return code
