# -*- coding: utf-8 -*-
"""Modify notes' contents or their attributes.

The "edit" action gives you the possibility to modify a note's contents. It can
also let you change only the set of its affected tags and rename the note.

"""
import sys

from scout import plugins
from scout.cli import (
    TOO_FEW_ARGUMENTS_ERROR, ARGUMENT_CONFLICT_ERROR, NOTE_MODIFICATION_ERROR
)


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
            "--add-tag", metavar="TAG",
            dest="added_tags", action="append", default=[],
            help=''.join(["Add a tag to the requested notes. ",
                          "Can be specified more than once."]))

        self.add_option(
            "--remove-tag", metavar="TAG",
            dest="removed_tags", action="append", default=[],
            help=''.join(["Remove a tag from the requested notes. ",
                          "Can be specified more than once."]))

        self.add_option_library(plugins.FilteringGroup("Edit"))

    def perform_action(self, config, options, positional):
        """Modify one note."""
        if not (positional or options.tags):
            # You can't edit _nothing_. Need a note to be selected
            msg = '\n\n'.join([
                "Error: No filters or note names given.",
                ''.join(["You must specify the notes you want to edit with ",
                         "a filtering option, note names, or both."]),
                "Use option -h or --help to learn more about filters."
            ])
            print >> sys.stderr, msg

            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        tag_conflicts = set(options.added_tags).intersection(
                            set(options.removed_tags))
        if tag_conflicts:
            msg = ''.join(["Error: Trying to add and remove the following ",
                           "tags in the same operation: %s"])
            print >> sys.stderr, msg % ', '.join(tag_conflicts)

            sys.exit(ARGUMENT_CONFLICT_ERROR)

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

        if options.removed_tags:
            for note in notes:
                for tag in options.removed_tags:
                    if tag not in note.tags:
                        msg = "Error: Tag '%s' not found on note '%s'."
                        print >> sys.stderr, msg % (tag, note.title)
                        sys.exit(NOTE_MODIFICATION_ERROR)
                    note.tags.remove(tag)

        self.interface.commit_notes(notes)
