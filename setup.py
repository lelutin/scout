#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script is Tomtom's installation script. It compiles files that are not
usable as-is into a form that is usable by setuptools' setup function.

It creates entry points for actions to use, and generates the "tomtom" script.

"""
import sys, os
from subprocess import Popen

command = None
if len(sys.argv) > 1:
    command = sys.argv[1]

# Create the version.py module
out = open("src/tomtom/version.py", "w")
Popen(["./format-subst.pl", "src/tomtom/version.py.pre"], stdout=out)
out.close()

if command:
    # Compile documentation
    Popen(["make", command ], cwd="doc")

from setuptools import setup, find_packages
from glob import glob
from src.tomtom.version import TOMTOM_VERSION

DESCRIPTION = """
Tomtom is an interface to Tomboy notes or Gnote that uses DBus to
communicate. It presents a command-line interface and
tries to be as simple to use as possible. Different actions
can be taken to interact with Tomboy or Gnote. Actions are simple
to create, making the application easily extensible.
"""

DATA_LIST = [
    ('/usr/share/man/man1/', glob('doc/*.1.gz') )
]

setup(
    # General information
    name = "tomtom",
    version = TOMTOM_VERSION,
    author = "Gabriel Filion",
    author_email = "lelutin@gmail.com",
    description = "CLI interface to Tomboy or Gnote via DBus",
    long_description = DESCRIPTION,
    license = "BSD",
    keywords = "cli tomboy gnote note dbus",
    url = "http://github.com/lelutin/tomtom",

    # Package structure information
    packages = find_packages("src", exclude=["test", "test.*"]),
    package_dir = {"": "src"},
    entry_points = {
        "console_scripts": [
            "tomtom = tomtom.cli:exception_wrapped_main",
        ],
        "tomtom.actions": [
            "list = tomtom.actions.list:ListAction",
            "display = tomtom.actions.display:DisplayAction",
            "search = tomtom.actions.search:SearchAction",
            "delete = tomtom.actions.delete:DeleteAction",
            "version = tomtom.actions.version:VersionAction",
        ],
    },

    # Non-code data files
    data_files = DATA_LIST,

    # Dependencies
    install_requires = [
        "setuptools",
    ],
    tests_require = [
        "nose",
        "mox >= 0.5.1",
    ],

    # To run tests via this file
    test_suite = "nose.collector",
)

