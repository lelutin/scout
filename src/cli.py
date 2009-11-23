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
#
# Inspired by : http://arstechnica.com/open-source/news/2007/09/using-the-tomboy-d-bus-interface.ars
#
"""Usage: tomtom.py (-h|--help) [action]
       tomtom.py <action> [-h|--help] [options]

Tomtom is a command line interface to the Tomboy note taking application.

Options depend on what action you are taking. To obtain details on options
for a particular action, combine -h or --help and the action name.

Here is a list of all the available actions:

"""
import sys
import os

# Return codes sent on errors
ACTION_NOT_FOUND_RETURN_CODE = 100
MALFORMED_ACTION_RETURN_CODE = 101

def action_dynamic_load(name):
    """Load an action with an arbitrary name.

    This function loads a module in the "actions" package that has the same
    name as the action called. If no module correspond to the required action,
    an error message is printed on the standard error stream and the program
    exits.

    Arguments:
        name -- A string representing the name of the action to load

    """
    _temp = __import__(
        "tomtom.actions",
        globals(),
        locals(),
        [name, ]
    )

    try:
        action = getattr(_temp, name)
    except AttributeError:
        print >> sys.stderr, \
            """%s: %s is not a valid """ % (sys.argv[0], name) + \
            """action. Use option -h for a list of available actions."""
        sys.exit(ACTION_NOT_FOUND_RETURN_CODE)

    return action

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
    action = action_dynamic_load(action_name)

    try:
        action.perform_action(arguments)
    except AttributeError:
        print >> sys.stderr, \
            """%s: the %s action is """ % (sys.argv[0], action_name) + \
            """malformed: the function "perform_action" could not be """ + \
            """found within the action's module."""
        sys.exit(MALFORMED_ACTION_RETURN_CODE)

def action_names():
    """Retrieve a list of available actions.

    Find the modules in the "actions" package and get their description from
    the first line of their docstring. The names of the modules will be listed
    as the action names.

    """
    from tomtom import actions

    files = os.listdir( actions.__path__[0] )

    list_of_actions = []

    # Build a list of files that are of interest in the "actions" directory
    for file_name in files:
        name_parts = file_name.split(".")
        extension = name_parts[-1]
        name = ".".join( name_parts[:-1] )

        if extension == "py" and name.find("_") != 0:
            list_of_actions.append(name)

    # Get longest name's length. We will use this value to align descriptions.
    pad_up_to = reduce(
        lambda x,y : max(x, y),
        [len(a) for a in list_of_actions]
    )

    # Finally, build the list of output lines for all the actions.
    results = []
    for name in list_of_actions:
            module = action_dynamic_load(name)
            description = getattr(module, "__doc__")
            if description is None:
                description = "No description available."

            lines = description.splitlines()

            if len( lines ):
                description = lines[0]

            results.append(
                """  %s%s """ % (name, " " * (pad_up_to - len(name) ) ) + \
                """: %s""" % (description, )
            )

    return results

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
    arguments = sys.argv[2:]

    if action in ["-h", "--help"]:
        if sys.argv[2:]:
            # Switch -h and action name and continue as normal
            arguments = [sys.argv[2], action] + sys.argv[3:]
            action = sys.argv[2]
        else:
            # Use the script's docstring for the basic help message. Also get a
            # list of available actions and display it.
            print __doc__[:-1] + os.linesep.join( action_names() )
            return

    dispatch(action, arguments)

if __name__ == "__main__":
    main()

