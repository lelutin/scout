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
# scout.plugins.ActionPlugin. Their entry point is the object's
# "perform_action" method. It can import scout classes and any other packages
# to help in its task. An action should use scout to get or send information
# from or to Tomboy and use the standard input, output and error streams as its
# interface with the user.
#
# Actions are listed dynamically in scout's basic help message. Actions'
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
"""List information about all or the 10 latest notes.

This is the "list" action. Its role is to display quick information about notes
on the standard output stream. By default (if no argument is given), it will
list all the notes. With the "-n" argument and an integer value, listed notes
will be limited in number to the value given as an argument.

"""
import os

from scout import plugins

DESC = __doc__.splitlines()[0]

class ListAction(plugins.ActionPlugin):
    """Plugin object for listing notes"""
    short_description = DESC
    usage = os.linesep.join([
        "%prog list (-h|--help)",
        "       %prog list [-n <num>] [filter ...]"
    ])

    def init_options(self):
        """Set the action's options."""
        self.add_option(
            "-n", type="int",
            dest="max_notes", default=None,
            help="Limit the number of notes listed."
        )

        self.add_option_library( plugins.FilteringGroup("List") )

    def perform_action(self, config, options, positional):
        """Use the scout object to list notes.

        This action prints modification date, title and tags of notes to the
        screen.

        The perform_action method gets processes options and hands them down
        appropriately to the list_notes method.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments. not used

        """
        tags_to_select = options.tags

        list_of_notes = self.tomboy_interface.get_notes(
            count_limit=options.max_notes,
            tags=tags_to_select,
            exclude_templates=not options.templates
        )

        print self.listing(list_of_notes).encode('utf-8')

    def listing(self, notes):
        """Format listing for a list of note objects.

        Given a list of notes, this method collects listing information for
        those notes and returns a global listing.

        Arguments:
            notes -- a list of TomboyNote objects

        """
        return os.linesep.join( [note.listing() for note in notes] )
