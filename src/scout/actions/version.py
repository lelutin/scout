# -*- coding: utf-8 -*-
from scout.version import SCOUT_VERSION
from scout.plugins import ActionPlugin


class VersionAction(ActionPlugin):
    """Display the note-taking application's version.

    In order, it displays Scout's version, the name of the note-taking
    application and its version.

    """

    short_description = __doc__.splitlines()[0]

    usage = "%prog version [-h|--help]"

    def perform_action(self, config, options, positional):
        """Display Tomboy's or Gnote's version information."""
        msg = "Scout version %s using %s version %s"
        version_map = (
            SCOUT_VERSION,
            self.interface.application,
            self.interface.comm.Version()
        )

        print(msg % version_map)
