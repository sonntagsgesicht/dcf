# -*- coding: utf-8 -*-

# auxilium
# --------
# Python project for an automated test and deploy toolkit.
#
# Author:   sonntagsgesicht
# Version:  0.2.4, copyright Wednesday, 20 October 2021
# Website:  https://github.com/sonntagsgesicht/auxilium
# License:  Apache License 2.0 (see LICENSE file)


from argparse import ArgumentParser
from configparser import ConfigParser

from .. import add_arguments
from ..add_arguments import ArgumentDefaultsAndConstsHelpFormatter
from ..tools.const import CONFIG_PATH


def add_parser(config=ConfigParser()):
    # ===========================
    # === add argument parser ===
    # ===========================

    epilog = """
    if (default: True) a given flag turns its value to False.
    default behavior may depend on current path and project.
    set default behavior in `~/%s` and `./%s`."
    """ % (CONFIG_PATH, CONFIG_PATH)

    description = """
    creates and manages boilerplate python development workflow.
     [ create > exit_status > test > build > deploy ]
    """

    parser = ArgumentParser(
        epilog=epilog,
        description=description,
        formatter_class=ArgumentDefaultsAndConstsHelpFormatter)

    sub_parser = parser.add_subparsers(dest='command')

    # === create ===
    _help = "creates a new project, repo and virtual environment"
    description = """
    creates a new project, repo and virtual environment
      with project file structure from templates which sets up
    a `venv` virtual python environment to run and test projects isolated,
    a `git` source code repository for tracking source exit_status changes,
    a `unittest` suite of tests to ensure the project works as intended and
    a already-to-use documentation structure made to be build with `sphinx`.
    """

    sub_parser.add_parser(
        'create',
        epilog=epilog,
        description=description,
        formatter_class=ArgumentDefaultsAndConstsHelpFormatter,
        help=_help)

    # === update ===
    description = "keeps project, repo and dependencies up-to-date"
    sub_parser.add_parser(
        'update',
        epilog=epilog,
        description=description,
        formatter_class=ArgumentDefaultsAndConstsHelpFormatter,
        help=description)

    # === test ==
    description = "checks project integrity " \
                  "by testing using `unittest` framework"
    sub_parser.add_parser(
        'test',
        epilog=epilog,
        description=description,
        formatter_class=ArgumentDefaultsAndConstsHelpFormatter,
        help=description)

    # === documentation ==
    description = "builds project documentation using `sphinx`"
    sub_parser.add_parser(
        'doc',
        epilog=epilog,
        description=description,
        formatter_class=ArgumentDefaultsAndConstsHelpFormatter,
        help=description)

    # === deploy ==
    description = "builds project distribution " \
                  "and deploy releases to `pypi.org`"
    sub_parser.add_parser(
        'build',
        epilog=epilog,
        description=description,
        formatter_class=ArgumentDefaultsAndConstsHelpFormatter,
        help=description)

    # === invoke python ==
    description = "invokes python in virtual environment"
    sub_parser.add_parser(
        'python',
        epilog='Call python interpreter of virtual environment '
               '(Note: only some standard optional arguments are implemented)',
        description=description,
        formatter_class=ArgumentDefaultsAndConstsHelpFormatter,
        help=description)

    # ===============================
    # === add arguments to parser ===
    # ===============================

    method = getattr(add_arguments, 'root', None)
    method(parser, config) if method else None

    for k, v in sub_parser.choices.items():
        method = getattr(add_arguments, k, None)
        method(v, config) if method else None

    return parser
