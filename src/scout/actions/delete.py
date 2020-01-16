# -*- coding: utf-8 -*-
import sys
import optparse

from scout import plugins
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class DeleteAction(plugins.ActionPlugin):
    """Delete notes by name or by other criteria.

    The "delete" action removes notes from the note-taking application. Notes
    are deleted permanently and, once it is done, their content is lost.

    Notes that are deleted can be specified by name as positional arguments to
    the action, by a filter with arguments or both.

    If a tag filter is selected for removal, templates that have this tag are
    also deleted. To keep templates in place when requesting a tag for
    deletion, the --spare-templates command-line argument should be used.

    Books are a special kind of tag, so requesting to delete notes of a
    particular book deletes templates of that particular book. To keep
    templates, the same argument as above should be used.

    """

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join([
        "%prog delete (-h|--help)",
        "       %prog delete [filter ...] [note_name ...]",
    ])

    def init_options(self):
        """Set action's options."""
        self.add_option(
            "--dry-run",
            dest="dry_run", action="store_true", default=False,
            help=''.join(["Simulate the action. The notes that are selected ",
                          "for deletion will be printed out to the screen but ",
                          "no note will really be deleted."])
        )

        filter_group = plugins.FilteringGroup("Delete")

        book_help_appendix = ''.join([" By default, template notes are ",
                                      "included so that the entire book is ",
                                      "deleted."])

        book_opt = filter_group.get_option("-b")
        book_opt.help = book_opt.help + book_help_appendix

        # Replace --with-templates by --spare-templates to inverse the meaning
        filter_group.remove_option("--with-templates")
        filter_group.add_options([
            optparse.Option(
                "--spare-templates",
                dest="templates", action="store_false", default=True,
                help=''.join(["Do not delete template notes that get caught ",
                              "with a tag or book name."])
            ),
            optparse.Option(
                "--all-notes",
                dest="erase_all", action="store_true", default=False,
                help=''.join(["Delete all notes. Once this is done, there is ",
                              "no turning back. To make sure that it is doing ",
                              "what you want, you could use the --dry-run ",
                              "option first."])
            ),
        ])

        self.add_option_library(filter_group)

    def perform_action(self, config, options, positional):
        """Delete one or more notes."""
        # Nothing was requested, so do nothing.
        if not (positional or options.tags or options.erase_all):
            msg = '\n\n'.join([
                "Error: No filters or note names given.",
                "To delete notes, you must specify a filtering option, "
                    "note names, or both.",
                "Use option -h or --help to learn more about filters."
            ])
            print(msg, file=sys.stderr)

            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        # All notes requested for deletion. Force no filters.
        if options.erase_all:
            options.tags = []
            positional = []

        notes = self.interface.get_notes(
            names=positional,
            tags=options.tags,
            exclude_templates=not options.templates
        )

        if options.dry_run:
            msg = "The following notes are selected for deletion:"
            print(msg)

        for note in notes:
            if options.dry_run:
                print("  %s" % note.title)
            else:
                self.interface.comm.DeleteNote(note.uri)
