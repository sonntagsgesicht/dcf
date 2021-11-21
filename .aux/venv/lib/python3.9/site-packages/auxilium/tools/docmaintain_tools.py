# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from datetime import date
from json import load, dump
from logging import log, INFO, DEBUG
from os import walk, sep, getcwd, linesep as _linesep, mkdir
from os.path import basename, join, getmtime, exists, split, normpath
from sys import path as sys_path
from textwrap import wrap

from .const import LAST_M_FILE, ICONS, AUX_PATH
from .system_tools import linesep, open


LEVEL = DEBUG


def get_attr(attr, pkg=basename(getcwd()), path=getcwd()):
    default = '<%s>' % attr
    try:
        if path not in sys_path:
            sys_path.append(path)
        pkg = __import__(pkg) if isinstance(pkg, str) else pkg
    except ImportError:
        return default
    return getattr(pkg, '__%s__' % attr, default)


def get_version(pkg=basename(getcwd()), path=getcwd()):
    return get_attr('version', pkg, path)


def get_author(pkg=basename(getcwd()), path=getcwd()):
    return get_attr('author', pkg, path)


def get_url(pkg=basename(getcwd()), path=getcwd()):
    return get_attr('url', pkg, path)


def set_timestamp(pkg=basename(getcwd()), path=getcwd()):
    # pkg = __import__(pkg) if isinstance(pkg, str) else pkg
    pkg = pkg if isinstance(pkg, str) else pkg.__name__
    file = join(path, pkg, '__init__.py')
    d = date.today().strftime('%A, %d %B %Y')
    a = (pkg, d, file)
    # read file lines into list
    f = open(file)
    lines = list(map(str.rstrip, f.readlines()))
    f.close()
    # make replacement
    for i, line in enumerate(lines):
        if line.startswith('__date__ = '):
            break
    old_line = lines[i]
    new_line = "__date__ = '" + d + "'"
    if old_line != new_line:
        log(LEVEL, ICONS[""] + "update %s.__date__ = %s in %s" % a)
        lines[i] = new_line
        # write file
        f = open(file, 'w')
        f.write(linesep.join(lines))
        f.write(linesep)  # last empty line
        f.close()
    return


def replace_headers(pkg=basename(getcwd()), last=None, path=getcwd()):
    last = dict() if last is None else last
    pkg = __import__(pkg) if isinstance(pkg, str) else pkg
    root, _ = split(pkg.__file__)

    new_lines = pkg.__name__,
    new_lines += '-' * len(pkg.__name__),
    new_lines += tuple(wrap(pkg.__doc__))
    new_lines += '',
    new_lines += "Author:   " + pkg.__author__,
    new_lines += "Version:  " + pkg.__version__ + \
                 ', copyright ' + pkg.__date__,
    new_lines += "Website:  " + pkg.__url__,
    new_lines += "License:  " + pkg.__license__ + " (see LICENSE file)",
    new_header = ["# -*- coding: utf-8 -*-", '']
    new_header += ['# ' + line for line in new_lines]
    new_header = [line.strip() for line in new_header]

    this = dict()
    for subdir, _, files in walk(root):
        if sep + '.' not in subdir:
            for file in files:
                if file.endswith('.py'):
                    file = join(subdir, file)
                    if last.get(file, '') == str(getmtime(file)):
                        this[file] = str(getmtime(file))
                        continue
                    log(LEVEL, ICONS[""] + "update file header of %s" % file)

                    # read file lines into list
                    f = open(file)
                    lines = list(map(str.rstrip, f.readlines()))
                    f.close()

                    # remove old header
                    removed = list()
                    while lines and \
                            (lines[0].strip() == '' or
                             lines[0].startswith('#')):
                        removed.append(lines.pop(0).strip())

                    # keep first line in script files
                    if removed and removed[0].startswith('#!'):
                        new_header[0] = removed[0]

                    # add new header
                    if lines:
                        new_lines = new_header + ['', ''] + lines
                    else:
                        new_lines = new_header

                    log(LEVEL - 1, _linesep.join(new_lines[:20]))
                    f = open(file, 'w')
                    f.write(linesep.join(new_lines))
                    if new_lines[-1].strip():
                        f.write(linesep)  # last empty line
                    f.close()
                    this[file] = str(getmtime(file))
    return this


def docmaintain(pkg=basename(getcwd()), path=getcwd()):
    """update timestamps and file header of modified files"""
    log(INFO, ICONS["maintenance"] + 'run header maintenance')
    set_timestamp(pkg, path)

    last_m_file = join(path, LAST_M_FILE)
    if exists(last_m_file):
        last_mtimes = load(open(last_m_file, 'r'))
        # add cwd
        last_mtimes = \
            dict((normpath(join(path, k)), v) for k, v in last_mtimes.items())
    else:
        last_mtimes = dict()
    last_mtimes = replace_headers(pkg, last_mtimes, path)
    if not exists(join(path, AUX_PATH)):
        mkdir(join(path, AUX_PATH))
    last_mtimes = \
        dict((k.replace(path + sep, ''), v) for k, v in last_mtimes.items())
    dump(last_mtimes, open(last_m_file, 'w'), indent=2)
    return 0
