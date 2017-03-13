#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scout's installation script.
It compiles files that are not usable as-is into a form that is usable by
setuptools' setup function.

It creates entry points for actions to use, and generates the "scout" script.

"""
import sys
from subprocess import Popen
from setuptools import setup, find_packages
from glob import glob

# This needs to be generated before we include it
out = open("src/scout/version.py", "w")
genr = Popen(["./format-subst.pl", "src/scout/version.py.pre"], stdout=out)
genr.wait()
out.close()
from src.scout.version import SCOUT_VERSION


command = None
if len(sys.argv) > 1:
    command = sys.argv[1]

if command:
    # Compile documentation
    Popen(["make", command ], cwd="doc")

    if command in ["develop", "test"]:
        # while developing, we don't want to call 'setup.py develop' after each
        # commit because the version tag has changed.
        SCOUT_VERSION = "%s-dev" % SCOUT_VERSION.split('-',1)[0]


DESCRIPTION = """\
Scout is an interface to Tomboy notes or Gnote that uses DBus to
communicate. It presents a command-line interface and
tries to be as simple to use as possible. Different actions
can be taken to interact with Tomboy or Gnote. Actions are simple
to create, making the application easily extensible.
"""

DATA_LIST = [
    ('/usr/share/man/man1/', glob('doc/*.1.gz'))
]

setup(
    # General information
    name = "scout",
    version = SCOUT_VERSION,
    author = "Gabriel Filion",
    author_email = "lelutin@gmail.com",
    description = "CLI interface to Tomboy or Gnote via DBus",
    long_description = DESCRIPTION,
    license = "BSD",
    keywords = "cli tomboy gnote note dbus",
    url = "http://github.com/lelutin/scout",

    # Package structure information
    packages = find_packages("src", exclude=["test", "test.*"]),
    package_dir = {"": "src"},
    entry_points = {
        "console_scripts": [
            "scout = scout.cli:main",
        ],
        "scout.actions": [
            "list = scout.actions.list:ListAction",
            "delete = scout.actions.delete:DeleteAction",
            "display = scout.actions.display:DisplayAction",
            "search = scout.actions.search:SearchAction",
            "tag = scout.actions.tag:TagAction",
            "version = scout.actions.version:VersionAction",
        ],
    },

    # Non-code data files
    data_files = DATA_LIST,

    # Dependencies
    install_requires = [
        "setuptools",
        "dbus-python",
    ],
    tests_require = [
        "nose",
        "mox >= 0.5.1",
    ],

    # To run tests via this file
    test_suite = "nose.collector",
)

