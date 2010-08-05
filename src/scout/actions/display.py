# -*- coding: utf-8 -*-
"""Display the content of one or more notes at a time.

This is the "display" action. Its role is to display the contents of one or
more notes to the standard output stream. A list of note names can be specified
to display all of them. Mulitiple notes that are displayed by separating them
with a special separator line. If one of the specified notes does not exist, it
will give an error message on the standard error stream.

"""
import sys
import os

from scout.plugins import ActionPlugin
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class DisplayAction(ActionPlugin):
    """Plugin object for displaying notes' contents"""

    short_description = __doc__.splitlines()[0]

    usage = ''.join([
        "%prog display (-h|--help)\n",
        "       %prog display [note_name ...]",
    ])

    note_separator = "\n==========================\n"

    def perform_action(self, config, options, positional):
        """Use the scout object to print the content of one or more notes.

        This action fetches note contents and displays them to the screen.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments

        """
        if len(positional) <= 0:
            print >> sys.stderr, \
                "Error: You need to specify a note name to display it"
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        notes = self.interface.get_notes(names=positional)

        #FIXME this _will_ bust the memory if too much notes are required
        print self.format_display_for_notes(notes).encode('utf-8')

    def format_display_for_notes(self, notes):
        """Get contents of a list of notes.

        Given a list of note names, this method retrieves the notes' contents
        and returns them. It applies a separator between each notes displayed.

        Arguments:
            notes -- list of notes to display

        """
        return self.note_separator.join(
            [self.interface.get_note_content(note) for note in notes]
        )
