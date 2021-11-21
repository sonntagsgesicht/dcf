# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.5, copyright Thursday, 28 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from os import getcwd
from os.path import basename

from ..tools.build_tools import build as _build, cleanup as _cleanup
from ..tools.docmaintain_tools import docmaintain
from ..tools.dulwich_tools import add_and_commit_git, tag_git, push_git, \
    build_url
from ..tools.pypi_tools import deploy as _deploy

DID_NOT_COMMIT = 'build missing or failed - did not commit'


def do(pkg=basename(getcwd()), commit=None, tag=None, header=None,
       push=None, remote=None, remote_usr=None, remote_pwd=None,
       deploy=None, pypi_usr=None, pypi_pwd=None, cleanup=None,
       path=None, env=None, **kwargs):
    """run deploy process"""

    _cleanup()
    if cleanup:
        return

    code = False
    if header:
        code = code or docmaintain(pkg, path=path)

    code = code or _build(path=path, venv=env)
    if commit:
        code = code or add_and_commit_git(commit, path=path, venv=env)
    if tag:
        code = code or tag_git(tag, path=path)
    if push:
        remote = build_url(remote, remote_usr, remote_pwd)
        code = code or push_git(remote=remote, branch=push, path=path)
    if deploy:
        code = code or _deploy(pypi_usr, pypi_pwd, path=path, venv=env)
    return code
