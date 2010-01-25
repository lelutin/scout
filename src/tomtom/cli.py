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

from tomtom.core import NoteNotFound, ConnectionError

# Return codes sent on errors.
# Codes between 100 and 199 are fatal errors
# Codes between 200 and 255 are minor errors
ACTION_NOT_FOUND_RETURN_CODE = 100
MALFORMED_ACTION_RETURN_CODE = 101
DBUS_CONNECTION_ERROR_RETURN_CODE = 102
ACTION_SYNTAX_ERROR_RETURN_CODE = 102
NOTE_NOT_FOUND_RETURN_CODE   = 200

def action_dynamic_load(name):
    """Load an action with an arbitrary name.

    This function loads a module in the "actions" package that has the same
    name as the action called. If no module correspond to the required action,
    an error message is printed on the standard error stream and the program
    exits.

    Arguments:
        name -- A string representing the name of the action to load

    """
    try:
        _temp = __import__(
            "actions",
            globals(),
            locals(),
            [name, ]
        )

    except SyntaxError:
        app_name = os.path.basename( sys.argv[0] )
        print >> sys.stderr, """%s: The action module""" % app_name + \
            """ "%s" has a syntax error that prevents tomtom """ % name + \
            """from loading it. If it is not a custom module, you """ + \
            """should report how you encountered this issue along """ + \
            """with the version of python you are using and a full """ + \
            """stack trace (see below for how to generate those) at:""" + \
            (os.linesep * 2) + \
            """http://github.com/lelutin/tomtom/issues""" + os.linesep + \
            os.linesep + \
            """The following two commands will show python's version """ + \
            """number and generate a stack trace, respectively. """ + \
            """Copy-paste the output of both commands in the issue you """ + \
            """create, it will help in finding what went wrong:""" + \
            (os.linesep * 2) + \
            """python -V""" + os.linesep + \
            """python -c "from actions import %s" """ % name
        sys.exit(ACTION_SYNTAX_ERROR_RETURN_CODE)

    try:
        action = getattr(_temp, name)

    except AttributeError:
        app_name = os.path.basename( sys.argv[0] )

        print >> sys.stderr, \
            """%s: %s is not a valid """ % (app_name, name) + \
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
    app_name = os.path.basename( sys.argv[0] )

    try:
        perform_action = getattr(action, "perform_action")

    except AttributeError:
        print >> sys.stderr, \
            """%s: the "%s" action is """ % (app_name, action_name) + \
            """malformed: the function "perform_action" could not be """ + \
            """found within the action's module."""

        sys.exit(MALFORMED_ACTION_RETURN_CODE)

    try:
        perform_action(arguments)
    #WARNING: do not forget to add types here for exceptions that must be
    # handled on an upper level or they will be catched by the next except
    # block.
    except (SystemExit, KeyboardInterrupt, ConnectionError, NoteNotFound):
        # Exceptions handled at an upper level. Let them through
        raise
    except:
        import traceback

        print >> sys.stderr, \
            """%s: the "%s" action is """ % (app_name, action_name) + \
            """malformed: An uncaught exception was raised while """ \
            """executing its "perform_action" function:""" + os.linesep
        traceback.print_exc()

        sys.exit(MALFORMED_ACTION_RETURN_CODE)

def list_of_actions():
    """Retrieve a list of available action names.

    Find the modules in the "actions" package and return a list of their names.

    """
    import actions

    files = os.listdir( actions.__path__[0] )

    list_of_names = []

    # Build a list of files that are of interest in the "actions" directory
    for file_name in files:
        name_parts = file_name.split(".")
        extension = name_parts[-1]
        name = ".".join( name_parts[:-1] )

        if extension == "py" and name.find("_") != 0:
            list_of_names.append(name)

    return list_of_names

def action_names():
    """Retrieve a list of available actions.

    Get descriptions from the first line of the actions' docstring and format
    them as a list of output lines for the help message. The names of the
    modules will be listed as the action names.

    """
    action_names = list_of_actions()

    # Get longest name's length. We will use this value to align descriptions.
    pad_up_to = reduce(
        lambda x,y : max(x, y),
        [len(a) for a in action_names]
    )

    # Finally, build the list of output lines for all the actions.
    results = []
    for name in action_names:
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
            print __doc__[:-1] + os.linesep.join( action_names() )
            return

    try:
        dispatch(action, arguments)

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
