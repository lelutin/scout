# -*- coding: utf-8 -*-
"""Modify notes' contents or their attributes.

The "edit" action gives you the possibility to modify a note's contents. It can
also let you change only the set of its affected tags and rename the note.

"""
import sys

from scout import plugins
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class EditAction(plugins.ActionPlugin):
    """The 'edit' sub-command."""

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join([
        "%prog edit (-h|--help)",
        "       %prog edit [options] <note_name>",
    ])

    def init_options(self):
        """Set the action's options."""
        self.add_option(
            "--add-tag", dest="added_tags", action="append", metavar="TAG",
            help=''.join(["Add a tag to the requested notes. ",
                          "Can be specified more than once."]))

        self.add_option_library(plugins.FilteringGroup("Edit"))

    def perform_action(self, config, options, positional):
        """Modify one note."""
        # Nothing was requested, so do nothing.
        if not (positional or options.tags):
            msg = '\n\n'.join([
                "Error: No filters or note names given.",
                ''.join(["You must specify the notes you want to edit with ",
                         "a filtering option, note names, or both."]),
                "Use option -h or --help to learn more about filters."
            ])
            print >> sys.stdout, msg

            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        note_names = positional

        notes = self.interface.get_notes(
            names=note_names,
            tags=options.tags,
            exclude_templates=not options.templates
        )

        if options.added_tags:
            for note in notes:
                for tag in [t for t in options.added_tags
                            if t not in note.tags]:
                    note.tags.append(tag)

        self.interface.commit_notes(notes)
