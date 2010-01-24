# -*- coding: utf-8 -*-
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

from src.tomtom.core import tomtom_version

setup(
    # General information
    name = "Tomtom",
    version = tomtom_version,
    author = "Gabriel Filion",
    author_email = "lelutin@gmail.com",
    description = "A CLI interface to Tomboy via dbus",
    long_description = \
        """Tomtom is an interface to Tomboy notes that uses dbus to """
        """communicate. It presents a command-line interface and """
        """tries to be as simple to use as possible. Different actions"""
        """can be taken to interact with Tomboy. Actions are simple"""
        """to create, making the application easily extensible.""",
    license = "BSD",
    keywords = "cli tomboy note",
    url = "http://github.com/lelutin/tomtom",

    # Package structure information
    packages = find_packages("src", exclude=["test", "test.*"]),
    package_dir = {"": "src"},
    entry_points = {
        "console_scripts": [
            "tomtom = tomtom.cli:exception_wrapped_main",
        ],
    },

    # Dependencies
    #install_requires = [
    #    "",
    #],
    tests_require = [
        "nose",
    ],

    # To run tests via this file
    test_suite = "nose.collector",
)

