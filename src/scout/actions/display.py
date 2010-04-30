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
"""Display the content of one or more notes at a time.

This is the "display" action. Its role is to display the contents of one or
more notes to the standard output stream. A list of note names can be specified
to display all of them. Mulitiple notes that are displayed by separating them
with a special separator line. If one of the specified notes does not exist, it
will give an error message on the standard error stream.

"""
import sys
import os

from scout.plugins import ActionPlugin
from scout.cli import TOO_FEW_ARGUMENTS_ERROR

DESC = __doc__.splitlines()[0]

class DisplayAction(ActionPlugin):
    """Plugin object for displaying notes' contents"""
    short_description = DESC
    usage = os.linesep.join([
        "%prog display (-h|--help)",
        "       %prog display [note_name ...]",
    ])
    note_separator = "=========================="

    def perform_action(self, config, options, positional):
        """Use the scout object to print the content of one or more notes.

        This action fetches note contents and displays them to the screen.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments

        """
        if len(positional) <= 0:
            print >> sys.stderr, \
                "Error: You need to specify a note name to display it"
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        notes = self.tomboy_interface.get_notes(names=positional)

        print self.format_display_for_notes(notes).encode('utf-8')

    def format_display_for_notes(self, notes):
        """Get contents of a list of notes.

        Given a list of note names, this method retrieves the notes' contents
        and returns them. It applies a separator between each notes displayed.

        Arguments:
            notes -- list of notes to display

        """
        separator = os.linesep + self.note_separator + os.linesep

        return separator.join(
            [self.tomboy_interface.get_note_content(note) for note in notes]
        )
