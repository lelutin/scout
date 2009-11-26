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
"""List information about all or the 10 latest notes.

This is the "list" action. Its role is to display quick information about notes
on the standard output stream. By default (if no argument is given), it will
list only the 10 latest notes. With the "-a" option, it will list all the
notes.

"""
import optparse
import sys

from tomtom import Tomtom

def perform_action(args):
    """Use the tomtom object to list notes.

    This action prints modification date, title and tags of notes to the
    screen.

    Arguments:
        args -- A list composed of action and file names

    """
    parser = optparse.OptionParser(usage="%prog list [-h|-a]")
    parser.add_option("-a", "--all",
        dest="full_list", default=False, action="store_true",
        help="List all the notes")

    (options, file_names) = parser.parse_args(args)

    tomboy_interface = Tomtom()

    if options.full_list:
        print tomboy_interface.list_notes()
    else:
        print tomboy_interface.list_notes(count_limit=10)

