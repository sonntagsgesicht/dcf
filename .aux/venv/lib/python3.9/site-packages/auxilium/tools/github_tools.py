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
from os import path, getcwd

from requests import post


def create(usr, pwd, pkg=path.basename(getcwd())):
    """create repo on github.com"""
    log(INFO, '*** create repo on github.com')
    try:
        _pkg = __import__(pkg) if isinstance(pkg, str) else pkg
        pkg = _pkg.__name__
        slogan = _pkg.__doc__
    except ImportError:
        pkg = str(pkg)
        slogan = ''
    repos = "https://api.github.com/%s/repos" % usr
    remote = "https://github.com/%s/%s" % (usr, pkg)
    json = {
        "name": pkg,
        "description": slogan,
        "homepage": remote,
        "private": False,
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    }
    post(repos)
    post(remote, auth=(usr, pwd), data=json)
    # system('git fetch %s' % remote)
    # system('git push')


def release(usr, pwd, pkg=path.basename(getcwd())):
    """draft release on github.com"""
    log(INFO, '*** draft release on github.com')

    pkg = __import__(pkg) if isinstance(pkg, str) else pkg
    name = pkg.__name__
    version = 'v' + pkg.__version__
    msg = "update for release %s" % version

    # draft new GitHub release;
    data = {
        "tag_name": "'%s'" % version,
        "target_commitish": "master",
        "name": "'%s'" % version,
        "body": "'%s'" % msg,
        "draft": False,
        "prerelease": False
    }
    url = "https://api.github.com/repos/%s/%s/releases" % (usr, name)
    post(url, data=data, auth=(usr, pwd))
