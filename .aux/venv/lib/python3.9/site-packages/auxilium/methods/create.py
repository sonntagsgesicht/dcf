# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.5, copyright Thursday, 28 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from os import getcwd, chdir
from os.path import basename, join, exists
from sys import path as sys_path

from ..tools.const import GIT_PATH
from ..tools.docmaintain_tools import docmaintain
from ..tools.dulwich_tools import add_and_commit_git, init_git
from ..tools.pip_tools import upgrade, install, requirements, uninstall, \
    rollback
from ..tools.setup_tools import create_project, create_finish
from ..tools.system_tools import create_venv, del_tree


def do(name=None, slogan=None, author=None, email=None, url=None,
       commit=None, path=getcwd(), venv=None, update=None, env=None,
       cleanup=None, **kwargs):
    env = env if env and exists(env) else None
    project_path = join(path, name) if name else path
    pkg = basename(project_path)

    if cleanup:
        return uninstall(pkg, venv=env) or rollback(path=path, venv=env)

    code = False
    if not update:
        # creat project
        project_path = \
            create_project(name, slogan, author, email, url, path=path)
        pkg = basename(project_path)
        code = not project_path.endswith(name) if name else False

        chdir(project_path)
        sys_path.append(project_path)
        code = code or docmaintain(pkg, path=project_path)

    #
    # chdir(project_path)
    if venv:
        # clear virtual environment folder
        del_tree(venv)
        # create virtual environment
        env = create_venv(pkg, venv_path=venv, path=project_path, venv=env)
        # run default update command
        code = code or upgrade(path=project_path, venv=env)
        code = code or install(path=project_path, venv=env)
        code = code or requirements(
            path=project_path, freeze_file='', venv=env)
    else:
        # run default update command (without pip upgrade with .freeze)
        code = code or install(path=project_path, venv=env)
        code = code or requirements(path=project_path, venv=env)

    if commit:
        # init git repo with initial commit
        if not exists(join(project_path, GIT_PATH)):
            code = code or init_git(path=project_path, venv=env)
        code = code or add_and_commit_git(commit, path=project_path, venv=env)

    if not update:
        code = code or create_finish(pkg)
    return code
