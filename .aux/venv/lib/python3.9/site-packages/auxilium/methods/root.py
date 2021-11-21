# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.5, copyright Thursday, 28 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


import logging
import sys

from datetime import datetime
from os import getcwd
from os.path import basename, join, exists

from .. import methods
from ..tools.const import VERBOSITY_LEVELS, ICONS, DEMO_PATH
from ..tools.system_tools import module, del_tree, shell

LEVEL = logging.DEBUG
Failure = Exception


def init_logging(verbosity=None, **kwargs):
    item = min(verbosity, len(VERBOSITY_LEVELS) - 1)
    verbosity, formatter = VERBOSITY_LEVELS[item]
    logging.basicConfig(level=verbosity, format=formatter)


def check_env(env=None, **kwargs):
    if env and not exists(env):
        msg = ICONS["warn"] + \
              'did not find a virtual environment at %s. ' % env
        logging.log(logging.WARN, msg)
        msg = ICONS[""] + \
            'consider creating one with ' \
            '`auxilium create --update` ' \
            'or use `auxilium -e command [options]`'
        logging.log(logging.WARN, msg)
        return True


def start_demo(demo=DEMO_PATH, verbosity=0, exit_status=0, env=None, **kwargs):
    logging.log(logging.INFO, ICONS["demo"] + 'relax, just starting a demo')
    if exists(demo):
        yn = input(" " + ICONS["warn"] +
                   "demo path exists. "
                   "unicum will remove and overwrite existing files. "
                   "continue? [y/n] ")
        if yn.lower() in ('y', 'yes'):
            del_tree(demo)
        else:
            return True
    v = '-' + 'v' * verbosity if verbosity else ''
    z = '-' + 'x' * exit_status if exit_status else ''
    e = '-e=' + env if env else ''
    if demo == 'unicorn':
        slogan = 'Always be a unicorn.'
        author = 'dreamer'
        email = 'dreamer@home'
        url = 'www.dreamer.home/unicorn'
    else:
        slogan = "a demo by auxilium"
        author = "auxilium"
        email = "sonntagsgesicht@icould.com"
        url = "https://github.com/sonntagsgesicht/auxilium"
    cmd = (' %s %s %s create '
           '--name="%s" '
           '--slogan="%s" '
           '--author="%s" '
           '--email="%s" '
           '--url="%s"') % \
          (v, z, e, demo, slogan, author, email, url)
    return module('auxilium', cmd, level=logging.INFO)


def check_project_path(pkg=basename(getcwd()), path=getcwd(), **kwargs):
    full_path = join(path, pkg)
    if exists(full_path):
        # add project path to sys.path
        if path not in sys.path:
            sys.path.append(path)
        return

    msg = ICONS["warn"] + 'no maintainable project found at %s ' % path
    logging.log(logging.WARN, msg)
    msg = ICONS[""] + \
        'consider creating one with `auxilium create` ' \
        '(or did you mean `auxilium python`?)'
    logging.log(logging.WARN, msg)
    return True


def failure_exit(exit_status, command='unknown', **kwargs):
    msg = 'non-zero exit status (failure in `%s`)' % command
    logging.log(logging.ERROR, ICONS['error'] + msg)
    if exit_status < 0:
        return not None
    elif exit_status > 2:
        raise Failure(msg)
    elif exit_status == 1:
        sys.exit(0)
    else:
        sys.exit(1)


def pre_run(cmd='', level=LEVEL, path=getcwd(), venv=None):
    if cmd:
        logging.log(logging.INFO, ICONS["run"] + "running %r" % cmd)
        return shell(cmd, level=level, path=path, venv=venv)


def do(command=None, demo=None, verbosity=None, exit_status=None, env=None,
       pre=None, pkg=None, path=None, **kwargs):
    exit = int if exit_status < 0 else sys.exit
    # check demo
    if demo:
        if start_demo(demo, verbosity, exit_status, env):
            return failure_exit(exit_status, 'demo')
        exit()

    # check virtual environment
    if command not in ('create',) and check_env(env):
        return failure_exit(exit_status, command)
    # if command in ('create',) and not check_env(env):
    #     env = ''
    #     # return failure_exit(exit_status, command)

    # check project path
    if command not in ('create', 'python') and check_project_path(pkg, path):
        return failure_exit(exit_status, command)

    # check project path
    if command not in ('create', 'python') and pre_run(pre):
        return failure_exit(exit_status, 'in pre run before ' + command)

    # retrieve command/method
    method = getattr(methods, str(command), None)

    # track execution timing
    start = datetime.now()

    # invoke command/method
    if method(env=env, pkg=pkg, path=path, **kwargs):
        return failure_exit(exit_status, command)

    # track execution timing
    exec_time = (datetime.now() - start)

    logging.log(logging.INFO, ICONS['OK'] +
                'finished in %0.3fs' % exec_time.total_seconds())
    exit()
