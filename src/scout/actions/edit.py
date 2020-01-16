# -*- coding: utf-8 -*-
"""Edit the centent of a note.

Specify. If one of the specified notes does not exist, it will give an error
message on the standard error stream.

"""
import os
import sys
import tempfile

from scout.plugins import ActionPlugin
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class EditAction(ActionPlugin):
    """The 'edit' sub-command."""

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join([
        "%prog edit (-h|--help)",
        "       %prog edit [note_name]",
    ])

    def perform_action(self, config, options, positional):
        """Edit the content of one note in $EDITOR."""
        if len(positional) != 1:
            print("Error: You need to specify a single note name to edit it", file=sys.stderr)
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        # TODO: if the note doesn't exist, it should be added
        notes = self.interface.get_notes(names=positional)

        # If we get this far, we found the note, and there's only one note

        old_content = self.interface.get_note_content(notes[0])

        (fd, temp_filename) = tempfile.mkstemp()

        with open(fd, 'w') as f:
            f.write(old_content)

        editor = os.environ.get("EDITOR")
        # Backup/default editor
        if not (editor):
            editor = "vi"

        os.system(editor + " " + temp_filename)

        with open(temp_filename, 'r') as f:
            contents = f.read()

        self.interface.set_note_content(notes[0], contents)


