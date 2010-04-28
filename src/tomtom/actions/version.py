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
"""Display Tomboy's version.

This is the "version" action. Its role is very simple: to display Tomboy's
version number. It uses dbus to get the information from Tomboy.

"""
from tomtom.version import TOMTOM_VERSION
from tomtom.plugins import ActionPlugin

DESC = __doc__.splitlines()[0]

class VersionAction(ActionPlugin):
    """Action plugin that prints out Tomboy's version information."""
    short_description = DESC
    usage = "%prog version [-h|--help]"

    def perform_action(self, config, options, positional):
        """Display Tomboy's version information.

        This action gets Tomboy's version via dbus and prints it out.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments

        """
        msg = """Tomtom version %s using %s version %s"""
        dbus_communicator = self.tomboy_interface.comm
        version_map = (
            TOMTOM_VERSION,
            self.tomboy_interface.application,
            dbus_communicator.Version()
        )

        print (msg % version_map).encode('utf-8')

