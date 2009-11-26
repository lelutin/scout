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
# This is an action module. Action modules need to have a function named
# "perform_action". It can import tomtom classes and any other packages to help
# in its task. An action should use tomtom to get or send information from or
# to Tomboy and use the standard input, output and error streams as its
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
"""Search for text in all notes or a specific list of notes.

This is the "search" action. Its role is to search for some text in either
all notes or a specialized set of notes. It returns nothing on stdout if it
finds nothing. If it finds results from the search, it will report every
occurence by citing the note's name, the line number of the occurrence and
the content of the line on which the text is appearing.

"""
import optparse
import sys

from tomtom import Tomtom

def perform_action(args):
    """Use the tomtom object to search for some text within notes.

    This action performs a textual search within notes and reports the results
    to the screen.

    Arguments:
        args -- list of arguments decomposed into action and file names

    """
    parser = optparse.OptionParser(
        usage="%prog search [-h] <search_pattern> [note_name ...]"
    )

    (options, file_names) = parser.parse_args(args)

    if len(file_names) < 1:
        print >> sys.stderr, \
            "Error: You must specify a pattern to perform a search"
        return

    tomboy_interface = Tomtom()

    search_pattern = file_names[0]
    note_names = file_names[1:]

    results = tomboy_interface.search_for_text(
        search_pattern=search_pattern,
        note_names=note_names
    )

    for result in results:
        print "%s : %s : %s" % \
            ( result["title"], result["line"], result["text"] )

