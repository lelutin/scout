# -*- coding: utf-8 -*-
"""List information about all or the 10 latest notes.

This is the "list" action. Its role is to display quick information about notes
on the standard output stream. By default (if no argument is given), it will
list all the notes. With the "-n" argument and an integer value, listed notes
will be limited in number to the value given as an argument.

"""
import os

from scout import plugins

DESC = __doc__.splitlines()[0]

class ListAction(plugins.ActionPlugin):
    """Plugin object for listing notes"""
    short_description = DESC
    usage = os.linesep.join([
        "%prog list (-h|--help)",
        "       %prog list [-n <num>] [filter ...]"
    ])

    def init_options(self):
        """Set the action's options."""
        self.add_option(
            "-n", type="int",
            dest="max_notes", default=None,
            help="Limit the number of notes listed."
        )

        self.add_option_library( plugins.FilteringGroup("List") )

    def perform_action(self, config, options, positional):
        """Use the scout object to list notes.

        This action prints modification date, title and tags of notes to the
        screen.

        The perform_action method gets processes options and hands them down
        appropriately to the list_notes method.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments. not used

        """
        tags_to_select = options.tags

        list_of_notes = self.tomboy_interface.get_notes(
            count_limit=options.max_notes,
            tags=tags_to_select,
            exclude_templates=not options.templates
        )

        print self.listing(list_of_notes).encode('utf-8')

    def listing(self, notes):
        """Format listing for a list of note objects.

        Given a list of notes, this method collects listing information for
        those notes and returns a global listing.

        Arguments:
            notes -- a list of TomboyNote objects

        """
        return os.linesep.join( [note.listing() for note in notes] )
