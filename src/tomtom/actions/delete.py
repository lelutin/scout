# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (c) 2009, Gabriel Filion
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice,
#     * this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
###############################################################################
#
# This is an action module. Action modules are subclasses of
# tomtom.plugins.ActionPlugin. Their entry point is the object's
# "perform_action" method. It can import tomtom classes and any other packages
# to help in its task. An action should use tomtom to get or send information
# from or to Tomboy and use the standard input, output and error streams as its
# interface with the user.
#
# Actions are listed dynamically in tomtom's basic help message. Actions'
# descriptions are taken from the first line of the action module's docstring.
# Make sure to keep it short but precise, the entire line (two spaces for
# indentation, the action's name and its description) should fit in less than
# 80 characters.
#
# KeyboardInterrupt exceptions are handled by the main script. If an action is
# currently doing work on data that could impact its integrity if the process
# is stopped right away should handle this exception to finish work in a
# consistant state. The user should be warned right away that the application
# is trying to stop its work. After the state is safe, the action should raise
# the same exception again so that the application exits cleanly.
#
"""Delete notes by name or by other criteria.

The "delete" action does what its name implies. It removes notes from the notes
application. Notes that are deleted can be specified by name as positional
arguments to the action, by a filter with arguments or both. Notes are deleted
permanently and, once it is done, their content is lost.

"""
import os
import optparse

from tomtom import plugins

DESC = __doc__.splitlines()[0]

class DeleteAction(plugins.ActionPlugin):
    """Plugin object for deleting notes"""

    short_description = DESC
    usage = os.linesep.join([
        "%prog delete -h",
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

        book_help_appendix = """ By default, template notes are included """ + \
            """so that the entire book is deleted."""

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
        ])

        self.add_option_library( filter_group )

    def perform_action(self, config, options, positional):
        """Use the tomtom object to delete one or more notes.

        This action deletes the requested notes from the application.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments

        """
        notes = self.tomboy_interface.get_notes(
            names=positional,
            tags=options.tags,
            exclude_templates=not options.templates
        )

        self.delete_notes(notes, options.dry_run)

    def delete_notes(self, notes, dry_run=True):
        """Delete each note in a list of notes."""
        if dry_run:
            msg = "The following notes are selected for deletion:"
            print msg.encode('utf-8')

        for note in notes:
            if dry_run:
                print ("  %s" % note.title).encode('utf-8')
            else:
                self.tomboy_interface.comm.DeleteNote(note.uri)
