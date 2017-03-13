# -*- coding: utf-8 -*-
from scout import plugins


class ListAction(plugins.ActionPlugin):
    """List information about notes.

    Display quick information about notes on the standard output stream. By
    default (if no argument is given), it will list all the notes. With the "-n"
    argument, the list of notes can be limited in number.

    """

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join(["%prog list (-h|--help)",
                       "       %prog list [-n <num>] [filter ...]"])

    def init_options(self):
        """Set the action's options."""
        self.add_option(
            "-n", type="int",
            dest="max_notes", default=None,
            help="Limit the number of notes listed."
        )

        self.add_option_library(plugins.FilteringGroup("List"))

    def perform_action(self, config, options, positional):
        """Print a list of notes to stdout."""
        notes = self.interface.get_notes(
            names=positional,
            count_limit=options.max_notes,
            tags=options.tags,
            exclude_templates=not options.templates
        )

        for n in notes:
            print ("%s" % n).encode('utf-8')
