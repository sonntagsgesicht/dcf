# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from logging import log, DEBUG, INFO, ERROR
from os import getcwd

from .const import ICONS
from .setup_tools import EXT
from .system_tools import script, shell

LEVEL = DEBUG
BRANCH = 'master'
IMP = "from sys import exit", \
      "from dulwich.repo import Repo", \
      "from dulwich.porcelain import *"


def init_git(path=getcwd(), venv=None):
    log(INFO, ICONS["init"] + "init local `git` repo")
    return script("Repo.init('.')",
                  imports=IMP, path=path, venv=venv)


def clone_git(remote, path=getcwd(), venv=None):
    log(INFO, ICONS["clone"] + "clone remote `git` repo")
    log(DEBUG, ICONS[""] + clean_url(remote))
    return script("clone(%r, '.')" % remote,
                  imports=IMP, path=path, venv=venv)


def branch_git(branch, path=getcwd(), venv=None):
    log(INFO, ICONS["branch"] + "create branch for local `git` repo")
    return script("branch_create('.', %r)" % branch,
                  imports=IMP, path=path, venv=venv)


def checkout_git(branch, path=getcwd(), venv=None):
    log(INFO, ICONS["checkout"] + "checkout %r from local `git` repo" % branch)
    return shell("git checkout %r" % branch,
                 path=path, venv=venv)


def add_git(path=getcwd(), venv=None):
    """add files to local `git` repo"""
    log(INFO, ICONS["add"] + "add/stage files to local `git` repo")
    code = False
    code = code or script("exit(Repo('.').stage(status().unstaged))",
                          imports=IMP, path=path, venv=venv)
    code = code or script("exit(Repo('.').stage(status().untracked))",
                          imports=IMP, path=path, venv=venv)
    return code


def status_git(level=INFO, path=getcwd(), venv=None):
    """check status of local `git` repo"""
    log(INFO, ICONS["status"] + "check file status in local `git` repo")
    code = False
    code = code or script(
        "print('add       : ' + "
        "', '.join(p.decode() for p in status().staged['add']))",
        imports=IMP, level=level, path=path, venv=venv)
    code = code or script(
        "print('delete    : ' + "
        "', '.join(p.decode() for p in status().staged['delete']))",
        imports=IMP, level=level, path=path, venv=venv)
    code = code or script(
        "print('modify    : ' + "
        "', '.join(p.decode() for p in status().staged['modify']))",
        imports=IMP, level=level, path=path, venv=venv)
    code = code or script(
        "print('unstaged  : ' + "
        "', '.join(p.decode() for p in  status().unstaged))",
        imports=IMP, level=level, path=path, venv=venv)
    code = code or script(
        "print('untracked : ' + "
        "', '.join(p for p in  status().untracked))",
        imports=IMP, level=level, path=path, venv=venv)
    return code


def commit_git(msg='', level=LEVEL, path=getcwd(), venv=None):
    """commit changes to local `git` repo"""
    msg = (msg if msg else 'Commit') + EXT
    log(INFO, ICONS["commit"] + "commit changes to local `git` repo")
    return script("print('[' + (commit(message=%r)).decode()[:6] + '] ' + %r)"
                  % (msg, msg), imports=IMP, level=level, path=path, venv=venv)


def has_status_git(path=getcwd(), venv=None):
    return script("exit(any(tuple(status().staged.values()) + "
                  "(status().unstaged, status().untracked)))",
                  imports=IMP, path=path, venv=venv)


def has_staged_git(path=getcwd(), venv=None):
    return script("exit(any(tuple(status().staged.values())))",
                  imports=IMP, path=path, venv=venv)


def has_unstaged_git(path=getcwd(), venv=None):
    return script("exit(any((status().unstaged, status().untracked)))",
                  imports=IMP, path=path, venv=venv)


def add_and_commit_git(msg='', level=LEVEL, path=getcwd(), venv=None):
    code = False
    if has_unstaged_git(path=path, venv=venv):
        code = code or add_git(path=path, venv=venv)
    if not has_staged_git(path=path, venv=venv):
        log(INFO, ICONS["missing"] + "no changes to commit")
        return code
    code = code or commit_git(msg, level=level, path=path, venv=venv)
    return code


def tag_git(tag, msg='few', level=LEVEL, path=getcwd(), venv=None):
    """tag current branch of local `git` repo"""
    tag_exists = script("exit(%r in tag_list('.'))" % bytearray(tag.encode()),
                        imports=IMP, path=path, venv=venv)
    if tag_exists:
        log(ERROR, ICONS["error"] +
            "tag %r exists in current branch of local `git` repo" % tag)
        return 1
    log(INFO, ICONS["tag"] + "tagging last commit")

    script("print('tag:    %s')" % tag,
           imports=IMP, level=level, path=path, venv=venv)
    if msg:
        script("print('message: %s')" % msg,
               imports=IMP, level=level, path=path, venv=venv)
    script("print(log(max_entries=1))",
           imports=IMP, level=level, path=path, venv=venv)
    return script("exit(tag_create('.', tag=%r, message=%r))" % (tag, msg),
                  imports=IMP, path=path, venv=venv)


def build_url(url, usr='', pwd='None'):  # nosec
    pwd = ':' + str(pwd) if pwd and pwd != 'None' else ''
    usr = str(usr) if usr else 'token-user' if pwd else ''
    remote = \
        'https://' + usr + pwd + '@' + url.replace('https://', '')
    return remote


def clean_url(url):
    if '@' not in url:
        return url
    http, last = url.split('//', 1)
    usr_pwd, url = last.split('@', 1)
    usr, _ = usr_pwd.split(':', 1) if ':' in usr_pwd else (usr_pwd, '')
    return http + '//' + usr + '@' + url


def push_git(remote='None', branch=BRANCH, path=getcwd(), venv=None):
    """push to given branch of remote `git` repo"""
    log(INFO, ICONS["push"] + "push to %r to remote `git` repo" % branch)
    log(DEBUG, ICONS[""] + clean_url(remote))
    return script("push('.', %r, %r)" % (remote, branch),
                  imports=IMP, path=path, venv=venv)


def fetch_git(remote='None', path=getcwd(), venv=None):
    """fetch from remote `git` repo"""
    log(INFO, ICONS["pull"] + "fetch from remote `git` repo")
    log(DEBUG, ICONS[""] + clean_url(remote))
    return script("fetch('.', %r)" % remote,
                  imports=IMP, path=path, venv=venv)


def pull_git(remote='None', path=getcwd(), venv=None):
    """pull from remote `git` repo"""
    log(INFO, ICONS["pull"] + "pull from remote `git` repo")
    log(DEBUG, ICONS[""] + clean_url(remote))
    return script("pull('.', %r)" % remote,
                  imports=IMP, path=path, venv=venv)
