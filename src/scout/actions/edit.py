# -*- coding: utf-8 -*-
"""Edit the centent of a note.

Specify. If the specified note does not exist, a new note with this name will
be created. If --no-create is given to the command, it will give an error
message on the standard error stream instead of creating a new note if the
specified note does not exist.

"""
import os
import sys
import tempfile


from scout.core import NoteNotFound
from scout.plugins import ActionPlugin
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class EditAction(ActionPlugin):
    """The 'edit' sub-command."""

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join([
        "%prog edit (--no-create) (-h|--help)",
        "       %prog edit [note_name]",
    ])


    def init_options(self):
        """Set the action's options."""
        self.add_option(
            "--no-create", action="store_true", default=False,
            help=''.join(["By default, scout will create a new note if the ",
                          "one requested was not found. By setting this ",
                          "option scout will display an error instead of ",
                          "creating a new note."])
        )


    def perform_action(self, config, options, positional):
        """Edit the content of one note in $EDITOR."""
        if len(positional) != 1:
            print(
                "Error: You need to specify a single note name to edit it",
                file=sys.stderr
            )
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        try:
            notes = self.interface.get_notes(names=positional)
        except NoteNotFound as e:
            if options.no_create:
                raise e

            # Note doesn't exist, let's create a new one!
            new_note = self.interface.create_named_note(positional[0])
            notes = [new_note]

        # If we get this far, we found or created the note, and there's only
        # one note. So we should be able to safely get its contents.
        old_content = self.interface.get_note_content(notes[0])

        (fd, temp_filename) = tempfile.mkstemp()

        with open(fd, 'w') as f:
            f.write(old_content)

        editor = os.environ.get("EDITOR")
        # Backup/default editor
        if not editor:
            editor = "vi"

        os.system(editor + " " + temp_filename)

        with open(temp_filename, 'r') as f:
            contents = f.read()

        self.interface.set_note_content(notes[0], contents)
