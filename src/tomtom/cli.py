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
"""Usage: %(tomtom)s <action> [-h|--help] [options]
       %(tomtom)s (-h|--help) [action]
       %(tomtom)s (-v|--version)

Tomtom is a command line interface to the Tomboy note taking application.

Options depend on what action you are taking. To obtain details on options
for a particular action, combine -h or --help and the action name.

Here is a list of all the available actions:

"""
import sys
import os
import pkg_resources
import optparse

from tomtom import core
from tomtom.core import tomtom_version, NoteNotFound, ConnectionError
from tomtom.plugins import ActionPlugin

# Return codes sent on errors.
# Codes between 100 and 199 are fatal errors
# Codes between 200 and 254 are minor errors
ACTION_NOT_FOUND_RETURN_CODE = 100
MALFORMED_ACTION_RETURN_CODE = 101
DBUS_CONNECTION_ERROR_RETURN_CODE = 102
ACTION_OPTION_TYPE_ERROR_RETURN_CODE = 103
TOO_FEW_ARGUMENTS_ERROR_RETURN_CODE = 200
NOTE_NOT_FOUND_RETURN_CODE   = 201

class CommandLineInterface(object):
    """Main entry point for Tomtom."""

    def load_action(self, action_name):
        """Load the action named <action_name>.

        Load an action by specifying its name. Returns an instance of the
        action's plugin object.

        Arguments:
            action_name -- String representing the name of the action.

        """
        action_class = [
            ac for ac in self.list_of_actions()
            if ac.name == action_name
        ]

        if not action_class:
            app_name = os.path.basename( sys.argv[0] )

            print >> sys.stderr, \
                """%s: %s is not a valid """ % (app_name, action_name) + \
                """action. Use option -h for a list of available actions."""

            sys.exit(ACTION_NOT_FOUND_RETURN_CODE)

        return action_class[0]()

    def retrieve_options(self, parser, action):
        """Get a list of options from an action and append default options.

        Get an action's list of options and groups. Flat out options from the
        special "None" group and instantiate optparse.OptionGroup objects out of
        tomtom.plugins.OptionGroup objects.

        Arguments:
            parser -- The optparse.OptionParser needed to instantiate groups
            action -- A subclass of tomtom.plugins.ActionPlugin

        """
        options = []

        # Retrieve the special "non-group" group and remove it from the list
        no_group_list = [g for g in action.option_groups if g.name is None]
        if len(no_group_list):
            no_group = no_group_list[0]
            for base_option in no_group.options:
                options.append(base_option)

        groups = [g for g in action.option_groups if g.name is not None]

        for group in groups:
            group_object = optparse.OptionGroup(
                parser,
                group.name,
                group.description
            )
            for option in group.options:
                group_object.add_option(option)

            options.append(group_object)

        return options

    def parse_options(self, action, arguments):
        """Parse the command line arguments before launching an action.

        Retrieve options from the action. Then, parse them. Finally, return the
        resulting optparse.Values and list of positional arguments.

        Arguments:
            action -- A sub-class of tomtom.plugins.ActionPlugin
            arguments -- The list of string arguments from the command line.

        """
        option_parser = optparse.OptionParser(usage=action.usage)

        action.init_options()
        action_options = self.retrieve_options(option_parser, action)

        for option in action_options:
            if isinstance(option, optparse.Option):
                option_parser.add_option(option)
            else:
                option_parser.add_option_group(option)

        return option_parser.parse_args(arguments)

    def dispatch(self, action_name, arguments):
        """Call upon a requested action.

        This function is responsible for importing the right module for the
        required actiion and triggering its entry point. If the function
        "perform_action" is not present in the imported module, it prints an
        error message on the standard error stream and exits.

        Arguments:
            action_name -- A string representing the requested action
            arguments   -- A list of all the other arguments from the cli

        """
        action = self.load_action(action_name)

        try:
            options, positional_arguments = self.parse_options(
                action,
                arguments
            )
        except TypeError, e:
            print >> sys.stderr, e
            exit(ACTION_OPTION_TYPE_ERROR_RETURN_CODE)

        action.tomboy_interface = core.Tomtom()
        try:
            action.perform_action(options, positional_arguments)

        except (SystemExit, KeyboardInterrupt):
            # Let the application exit if it wants to, and KeyboardInterrupt is
            # handled on an upper level so that interrupting execution with
            # Ctrl-C always exits cleanly.
            raise

        except ConnectionError, e:
            print >> sys.stderr, "%s: Error: %s" % (
                os.path.basename(sys.argv[0]),
                e
            )
            sys.exit(DBUS_CONNECTION_ERROR_RETURN_CODE)

        except NoteNotFound, e:
            msg = """%s: Error: Note named "%s" was not found."""
            error_map = ( os.path.basename( sys.argv[0] ), e )
            print >> sys.stderr, msg % error_map
            sys.exit(NOTE_NOT_FOUND_RETURN_CODE)

        except:
            import traceback

            app_name = os.path.basename( sys.argv[0] )

            print >> sys.stderr, \
                """%s: the "%s" action is """ % (app_name, action_name) + \
                """malformed: An uncaught exception was raised while """ \
                """executing its "perform_action" function:""" + os.linesep
            traceback.print_exc()

            # This is pretty annoying when running acceptance tests. Comment it
            # out if you have a failing test that shows this as being the
            # error.
            sys.exit(MALFORMED_ACTION_RETURN_CODE)

    def list_of_actions(self):
        """Retrieve a list of all registered actions.

        Return a list of classes corresponding to all the plugins.

        """
        group = "tomtom.actions"
        action_list = []

        for entrypoint in pkg_resources.iter_entry_points(group=group):
            plugin_class = entrypoint.load()
            plugin_class.name = entrypoint.name
            if issubclass(plugin_class, ActionPlugin):
                action_list.append(plugin_class)

        return action_list

    def action_short_summaries(self):
        """Retrieve a list of available actions.

        Get descriptions from the first line of the actions' docstring and
        format them as a list of output lines for the help message. The names
        of the modules will be listed as the action names.

        """
        actions = self.list_of_actions()

        # Get longest name's length. We'll use this value to align descriptions.
        pad_up_to = reduce(
            lambda x,y : max(x, y),
            [len(a.name) for a in actions]
        )

        descriptions = []
        for action in actions:
            if action.short_description:
                description_text = action.short_description
            else:
                description_text = "No description available."

            descriptions.append(
                """  %s""" % action.name +
                """%s """ % ( " " * (pad_up_to - len(action.name) ) ) +
                """: %s""" % description_text
            )

        return descriptions

    def main(self):
        """Application entry point.

        Checks the first parameters for general help argument and dispatches the
        actions.

        """
        if len(sys.argv) < 2:
            app_name_map = { "tomtom": os.path.basename(sys.argv[0]) }

            # Use the docstring's first [significant] lines to display usage
            usage_output =  (os.linesep * 2).join([
                os.linesep.join( __doc__.splitlines()[:3] ) % app_name_map,
                "For more details, use option -h"
            ])
            print >> sys.stderr, usage_output
            sys.exit(TOO_FEW_ARGUMENTS_ERROR_RETURN_CODE)

        action = sys.argv[1]
        # Convert the rest of the arguments to unicode objects so that they are
        # handled correctly afterwards. This expects to receive arguments in
        # UTF-8 format from the command line.
        arguments = [arg.decode("utf-8") for arg in sys.argv[2:] ]

        if action in ["-h", "--help"]:
            if sys.argv[2:]:
                # Switch -h and action name and continue as normal
                arguments = [sys.argv[2], action] + sys.argv[3:]
                action = sys.argv[2]
            else:
                # Use the script's docstring for the basic help message. Also
                # get a list of available actions and display it.
                msg_map = {"tomtom": os.path.basename(sys.argv[0]) }
                help_msg = __doc__[:-1] % msg_map
                action_list = os.linesep.join( self.action_short_summaries() )

                print help_msg + action_list

                sys.exit(0)

        elif action in ["-v", "--version"]:
            version_info =  os.linesep.join([
                """Tomtom version %s""" % tomtom_version,
                """Copyright © 2010 Gabriel Filion""",
                """License: BSD""",
                """This is free software: you are free to change and """
                    """redistribute it.""",
                """There is NO WARRANTY, to the extent permitted by law."""
            ])

            print version_info
            sys.exit(0)

        self.dispatch(action, arguments)

def exception_wrapped_main():
    """Wrap around main function to handle general exceptions."""
    tomtom_cli = CommandLineInterface()

    try:
        tomtom_cli.main()
    # Default handling.
    # If it goes this far up, it probably means it is not such a big deal.
    except KeyboardInterrupt:
        pass
