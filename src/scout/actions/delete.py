# -*- coding: utf-8 -*-
"""Delete notes by name or by other criteria.

The "delete" action does what its name implies. It removes notes from the notes
application. Notes that are deleted can be specified by name as positional
arguments to the action, by a filter with arguments or both. Notes are deleted
permanently and, once it is done, their content is lost.

"""
import os
import sys
import optparse

from scout import plugins
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class DeleteAction(plugins.ActionPlugin):
    """Plugin object for deleting notes"""

    short_description = __doc__.splitlines()[0]

    usage = ''.join([
        "%prog delete -h\n",
        "       %prog delete [filter ...] [note_name ...]",
    ])

    def init_options(self):
        """Set action's options."""
        self.add_option(
            "--dry-run",
            dest="dry_run", action="store_true", default=False,
            help="Simulate the action. The notes that are selected for """
                """deletion will be printed out to the screen but no note """
                """will really be deleted."""
        )

        filter_group = plugins.FilteringGroup("Delete")

        book_help_appendix = (""" By default, template notes are included """ +
            """so that the entire book is deleted.""")

        book_opt = filter_group.get_option("-b")
        book_opt.help = book_opt.help + book_help_appendix

        # Replace --with-templates by --spare-templates to inverse the meaning
        filter_group.remove_option("--with-templates")
        filter_group.add_options([
            optparse.Option(
                "--spare-templates",
                dest="templates", action="store_false", default=True,
                help="""Do not delete template notes that get caught with a """
                    """tag or book name."""
            ),
            optparse.Option(
                "--all-notes",
                dest="erase_all", action="store_true", default=False,
                help="""Delete all notes. Once this is done, there is no """
                    """turning back. To make sure that it is doing what you """
                    """want, you could use the --dry-run option first."""
            ),
        ])

        self.add_option_library( filter_group )

    def perform_action(self, config, options, positional):
        """Use the scout object to delete one or more notes.

        This action deletes the requested notes from the application.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments

        """
        # Nothing was requested, so do nothing.
        if not (positional or options.tags or options.erase_all):
            msg = '\n\n'.join([
                """error: No filters or note names given.""",
                """To delete notes, you must specify a filtering option, """
                    """note names, or both.""",
                """Use option -h or --help to learn more about filters."""
            ])
            print msg

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
            print msg.encode('utf-8')

        for note in notes:
            if options.dry_run:
                print ("  %s" % note.title).encode('utf-8')
            else:
                self.interface.comm.DeleteNote(note.uri)
