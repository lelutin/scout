from setuptools import setup, find_packages

setup(
    # General information
    name = "Tomtom",
    version = "0.1",
    author = "Gabriel Filion",
    author_email = "lelutin@gmail.com",
    description = "A CLI interface to Tomboy via dbus",
    license = "BSD",
    keywords = "cli tomboy note",
    url = "http://github.com/lelutin/tomtom",

    # Package structure information
    packages = find_packages("src"),
    package_dir = {"": "src"},
    entry_points = {
        "console_scripts": [
            "tomtom = tomtom.cli:main",
        ],
    },
    #install_requires = [
    #    "",
    #]

    # To run tests via this file
    test_suite = "nose.collector",
)

