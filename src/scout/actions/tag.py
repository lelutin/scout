# -*- coding: utf-8 -*-
"""Modify notes' contents or their attributes.

The "edit" action gives you the possibility to modify a note's contents. It can
also let you change only the set of its affected tags and rename the note.

"""
import sys

from scout import plugins
from scout.cli import (
    TOO_FEW_ARGUMENTS_ERROR, NOTE_MODIFICATION_ERROR
)


class TagAction(plugins.ActionPlugin):
    """The 'tag' sub-command."""

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join([
        "%prog tag (-h|--help)",
        "       %prog tag [options] <tag_name> [filtering options|<note_name>...]",
        "       %prog tag [options] --remove-all [filtering options|<note_name>...]",
    ])

    def init_options(self):
        """Set the action's options."""
        self.add_option(
            "--remove", action="store_true", default=False,
            help="Remove a tag from the requested notes.")

        self.add_option(
            "--remove-all", action="store_true", default=False,
            help="Remove all tags from the requested notes.")

        self.add_option_library(plugins.FilteringGroup("Modify"))

    def perform_action(self, config, options, positional):
        """Modify one note."""
        if not (positional or options.tags):
            # You can't edit _nothing_. Need a note to be selected
            msg = '\n\n'.join([
                "Error: No filters or note names given.",
                ''.join(["You must specify the notes you want to modify with ",
                         "a filtering option, note names, or both."]),
                "Use option -h or --help to learn more about filters."
            ])
            print >> sys.stderr, msg

            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        if options.remove_all:
            options.remove = True
            tag_name = None
            note_names = positional
        else:
            tag_name = positional[0]
            note_names = positional[1:]

        notes = self.interface.get_notes(
            names=note_names,
            tags=options.tags,
            exclude_templates=not options.templates
        )

        if options.remove:
            for note in notes:
                if options.remove_all:
                    note.tags = []
                    continue

                if tag_name not in note.tags:
                    msg = "Error: Tag '%s' not found on note '%s'."
                    print >> sys.stderr, msg % (tag_name, note.title)
                    sys.exit(NOTE_MODIFICATION_ERROR)
                note.tags.remove(tag_name)
        else:
            for note in notes:
                note.tags.append(tag_name)

        self.interface.commit_notes(notes)
