# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from logging import INFO, log

from ..tools.const import ICONS, PYTHON
from ..tools.system_tools import python as _python


def do(c='', m='', f='', stdin='', arg=(), env=None, **kwargs):
    cmd = ''
    if c:
        cmd = '-c "' + c + '"'
    if m:
        cmd = '-m ' + m
    if f:
        cmd = f
    if stdin:
        cmd = '-'
    if arg:
        cmd += ' ' + ' '.join(arg)
    print(env)
    venv = env if env else PYTHON
    log(INFO, ICONS["python"] + 'running %s' % venv)
    return _python(cmd, level=INFO, venv=env, capture_output=False)
