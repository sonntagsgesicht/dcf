# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.5, copyright Thursday, 28 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from io import open as _open
from logging import log, DEBUG, INFO, ERROR
from os import linesep as _linesep, getcwd, name as os_name, remove
from os.path import basename, exists, isdir, join
from shutil import rmtree
from subprocess import run, Popen, PIPE, STDOUT  # nosec

from .const import PYTHON, VENV_PATH, VENV_TAIL, ICONS, SUB_FORMATTER_PREFIX

LEVEL = DEBUG
linesep = '\n'


def open(name, mode='r'):
    return _open(name, mode, encoding='utf-8', newline=linesep)


def create_venv(pkg=basename(getcwd()),
                venv_path=VENV_PATH,
                path=getcwd(),
                venv=None):
    """create virtual python environment"""
    # strip potential executable from venv_path
    venv_path = venv_path.replace(VENV_TAIL, '')
    if venv and venv.startswith(venv_path):
        venv = None
    log(INFO, ICONS["venv"] + "create virtual environment")
    module('venv', "--clear --prompt %s %s" % (pkg, venv_path),
           path=path, venv=venv)
    return join(venv_path, VENV_TAIL)


def activate_venv(venv_path=VENV_PATH):
    """activate virtual python environment"""
    # strip potential executable from venv_path
    venv_path = venv_path.replace(VENV_TAIL, '')
    if os_name == 'nt':
        log(LEVEL-1, ICONS[""] + "in virtual environment at %s" % venv_path)
        return "%s && " % join(venv_path, 'Scripts', 'activate.bat')
    elif os_name == 'posix':
        log(LEVEL-1, ICONS[""] + "in virtual environment at %s" % venv_path)
        return ". %s; " % join(venv_path, 'bin', 'activate')
    else:
        log(ERROR,
            "    unable to activate virtual environment for os %s" % os_name)


def shell(command, level=LEVEL, path=getcwd(), venv=None,
          capture_output=True):
    if venv:
        command = activate_venv(venv) + ' ' + command
    log(LEVEL - 1, ICONS[""] + ">>> %s" % command)
    log(LEVEL - 1, ICONS[""] + "in %s" % path)
    return _popen(command, level, path, capture_output)


def _popen(command, level=LEVEL, path=getcwd(), capture_output=True):  # nosec
    if not capture_output:
        return _run(command, level, path, capture_output)
    proc = Popen(
        command,
        stdout=PIPE,
        stderr=STDOUT,
        universal_newlines=True,
        cwd=path, shell=True, text=True)
    stderr = list()
    for stdout_line in iter(proc.stdout.readline, ""):
        stderr.append(stdout_line)
        log(level, ICONS[""] +
            SUB_FORMATTER_PREFIX + ' ' + stdout_line.rstrip())
    proc.stdout.close()
    exit_status = proc.wait()
    if exit_status:
        for stderr_line in stderr:
            log(ERROR, ICONS["error"] +
                SUB_FORMATTER_PREFIX + ' ' + stderr_line.rstrip())
    return exit_status


def _run(command, level=LEVEL, path=getcwd(), capture_output=False):  # nosec
    proc = run(command, cwd=path, shell=True,
               capture_output=capture_output, text=True)
    log_level = ERROR if proc.returncode else level
    if proc.stdout:
        for line in str(proc.stdout).split(_linesep):
            if line:
                log(log_level, line)
    if proc.stderr:
        for line in str(proc.stderr).split(_linesep):
            if line:
                log(log_level, line)
    return proc.returncode


def python(command, level=LEVEL, path=getcwd(), venv=None,
           capture_output=True):
    venv = venv if venv else PYTHON
    return shell(venv + ' ' + command, level=level, path=path,
                 capture_output=capture_output)


def module(mdl, command='', level=LEVEL, path=getcwd(), venv=None):
    mdl = getattr(mdl, '__name__', str(mdl))
    return python('-m ' + mdl + ' ' + command,
                  level=level, path=path, venv=venv)


def script(cmd, imports=(), level=LEVEL, path=getcwd(), venv=None):
    if not isinstance(imports, (list, tuple)):
        imports = (imports,)
    cmd = '; '.join(tuple(imports) + (cmd,))
    return python('-c "' + cmd + '"',
                  level=level, path=path, venv=venv)


def del_tree(*paths, level=LEVEL):
    for f in paths:
        if exists(f):
            if isdir(f):
                log(level, 'remove tree below %s' % f)
                rmtree(f)
            else:
                log(level, 'remove file %s' % f)
                remove(f)
    return 0
