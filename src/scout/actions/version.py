# -*- coding: utf-8 -*-
"""Display Tomboy's version.

This is the "version" action. Its role is very simple: to display Tomboy's
version number. It uses dbus to get the information from Tomboy.

"""
from scout.version import SCOUT_VERSION
from scout.plugins import ActionPlugin


class VersionAction(ActionPlugin):
    """Action plugin that prints out Tomboy's version information."""

    short_description = __doc__.splitlines()[0]

    usage = "%prog version [-h|--help]"

    def perform_action(self, config, options, positional):
        """Display Tomboy's version information.

        This action gets Tomboy's version via dbus and prints it out.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments

        """
        msg = """Scout version %s using %s version %s"""
        version_map = (
            SCOUT_VERSION,
            self.interface.application,
            self.interface.comm.Version()
        )

        print (msg % version_map).encode('utf-8')
