# -*- coding: utf-8 -*-
import sys

from scout.plugins import ActionPlugin
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class DisplayAction(ActionPlugin):
    """Display the content of one or more notes at a time.

    A list of note names can be specified to display them one after the other.
    Mulitiple notes that are displayed by separating them with a special
    separator line. If one of the specified notes does not exist, it will give
    an error message on the standard error stream.

    """

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join([
        "%prog display (-h|--help)",
        "       %prog display [note_name ...]",
    ])

    note_separator = "\n==========================\n"

    def perform_action(self, config, options, positional):
        """Print the content of one or more notes to stdout."""
        if len(positional) <= 0:
            print("Error: You need to specify a note name to display it", file=sys.stderr)
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        notes = self.interface.get_notes(names=positional)

        display_sep = False
        for n in notes:
            if display_sep:
                print(self.note_separator)
            else:
                display_sep = True
            content = self.interface.get_note_content(n)
            print(content)
