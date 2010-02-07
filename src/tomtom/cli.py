#!/usr/bin/env python
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
"""Usage: tomtom.py <action> [-h|--help] [options]
       tomtom.py (-h|--help) [action]
       tomtom.py (-v|--version)

Tomtom is a command line interface to the Tomboy note taking application.

Options depend on what action you are taking. To obtain details on options
for a particular action, combine -h or --help and the action name.

Here is a list of all the available actions:

"""
import sys
import os
import pkg_resources

from tomtom.core import tomtom_version, NoteNotFound, ConnectionError
from tomtom.plugins import ActionPlugin

# Return codes sent on errors.
# Codes between 100 and 199 are fatal errors
# Codes between 200 and 255 are minor errors
ACTION_NOT_FOUND_RETURN_CODE = 100
MALFORMED_ACTION_RETURN_CODE = 101
DBUS_CONNECTION_ERROR_RETURN_CODE = 102
ACTION_SYNTAX_ERROR_RETURN_CODE = 102
NOTE_NOT_FOUND_RETURN_CODE   = 200

def load_action(action_name):
    """Load the action named <action_name>.

    Load an action by specifying its name. Returns an instance of the action's
    plugin object.

    Arguments:
        action_name -- String representing the name of the action.

    """
    action_class = [
        ac for ac in list_of_actions()
        if ac.name == action_name
    ]

    if not action_class:
        app_name = os.path.basename( sys.argv[0] )

        print >> sys.stderr, \
            """%s: %s is not a valid """ % (app_name, action_name) + \
            """action. Use option -h for a list of available actions."""

        sys.exit(ACTION_NOT_FOUND_RETURN_CODE)

    return action_class[0]()

def dispatch(action_name, arguments):
    """Call upon a requested action.

    This function is responsible for importing the right module for the
    required actiion and triggering its entry point. If the function
    "perform_action" is not present in the imported module, it prints an error
    message on the standard error stream and exits.

    Arguments:
        action_name -- A string representing the requested action
        arguments   -- A list of all the other arguments from the command line

    """
    # Perform a dynamic `from actions import "action_name"`. This gives the
    # functionality of adding actions by simply dropping a new python module
    # that has a function "perform_action" in the actions package. Action
    # modules in the actions package must have the same name as the action
    # asked on the command line. For example, the command "tomtom list ..."
    # will import the list.py module from the actions package.
    action = load_action(action_name)

    try:
        #FIXME arguments to this function must be the parsed options and the
        #positional args
        action.perform_action(arguments, [])

    except (SystemExit, KeyboardInterrupt):
        # Let the application exit if it wants to, and KeyboardInterrupt is
        # handled on an upper level so that interrupting execution with Ctrl-C
        # always exits cleanly.
        raise

    except ConnectionError, e:
        print >> sys.stderr, "%s: Error: %s" % (
            os.path.basename(sys.argv[0]),
            e
        )
        sys.exit(DBUS_CONNECTION_ERROR_RETURN_CODE)

    except NoteNotFound, e:
        print >> sys.stderr, """%s: Error: Note named "%s" was not found.""" %\
            (
                os.path.basename( sys.argv[0] ),
                e
            )
        sys.exit(NOTE_NOT_FOUND_RETURN_CODE)

    except:
        import traceback

        app_name = os.path.basename( sys.argv[0] )

        print >> sys.stderr, \
            """%s: the "%s" action is """ % (app_name, action_name) + \
            """malformed: An uncaught exception was raised while """ \
            """executing its "perform_action" function:""" + os.linesep
        traceback.print_exc()

        sys.exit(MALFORMED_ACTION_RETURN_CODE)

def list_of_actions():
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

def action_short_summaries():
    """Retrieve a list of available actions.

    Get descriptions from the first line of the actions' docstring and format
    them as a list of output lines for the help message. The names of the
    modules will be listed as the action names.

    """
    actions = list_of_actions()

    # Get longest name's length. We will use this value to align descriptions.
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

def main():
    """Application entry point.

    Checks the first parameters for general help argument and dispatches the
    actions.

    """
    if len(sys.argv) < 2:
        # Use the docstring's first [significant] lines to display usage
        usage_output =  (os.linesep * 2).join([
            os.linesep.join( __doc__.splitlines()[:3] ),
            "For more details, use option -h"
        ])
        print usage_output
        return

    action = sys.argv[1]
    # Convert the rest of the arguments to unicode objects so that they are
    # handled correctly afterwards. This expects to receive arguments in UTF-8
    # format from the command line.
    arguments = [arg.decode("utf-8") for arg in sys.argv[2:] ]

    if action in ["-h", "--help"]:
        if sys.argv[2:]:
            # Switch -h and action name and continue as normal
            arguments = [sys.argv[2], action] + sys.argv[3:]
            action = sys.argv[2]
        else:
            # Use the script's docstring for the basic help message. Also get a
            # list of available actions and display it.
            print __doc__[:-1] + os.linesep.join( action_short_summaries() )
            return
    elif action in ["-v", "--version"]:
        print """Tomtom version %s""" % tomtom_version + os.linesep + \
            """Copyright © 2010 Gabriel Filion""" + os.linesep + \
            """License: BSD""" + os.linesep + """This is free software: """ \
            """you are free to change and redistribute it.""" + os.linesep + \
            """There is NO WARRANTY, to the extent permitted by law."""
        return

    dispatch(action, arguments)

def exception_wrapped_main():
    """Wrap around main function to handle general exceptions."""
    try:
        main()
    # Default handling.
    # If it goes this far up, it probably means it is not such a big deal.
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    exception_wrapped_main()
