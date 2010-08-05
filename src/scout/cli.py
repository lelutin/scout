# -*- coding: utf-8 -*-
"""Usage: %(scout)s <action> [-h|--help] [options]
       %(scout)s (-h|--help|help) [action]
       %(scout)s (-v|--version)

Scout is a command line interface to the note taking applications: Tomboy and
Gnote.

Options depend on what action you are taking. To obtain details on options for
a particular action, combine one of "-h" or "--help" with the action name or
use "help" before the action name.

Here is a list of all the available actions:

"""
try:
    import sys
    import os
    import pkg_resources
    import optparse
    import ConfigParser as configparser

    from scout import core
    from scout.version import SCOUT_VERSION
    from scout.core import NoteNotFound, ConnectionError, \
            AutoDetectionError
    from scout.plugins import ActionPlugin

    # Return codes sent on errors.
    # Codes between 100 and 199 are fatal errors
    # Codes between 200 and 254 are minor errors
    ACTION_NOT_FOUND = 100
    MALFORMED_ACTION = 101
    DBUS_CONNECTION_ERROR = 102
    ACTION_OPTION_TYPE_ERROR = 103
    TOO_FEW_ARGUMENTS_ERROR = 200
    NOTE_NOT_FOUND = 201
    AUTODETECTION_FAILED = 202

# Use a hardcoded error code, since constants may not be initialized at this
# point.
except KeyboardInterrupt:
    raise SystemExit, 1

class CommandLine(object):
    """Main entry point for Scout."""

    # config file general settings
    core_config_section = "scout"
    core_options = [
        "application",
    ]

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

            sys.exit(ACTION_NOT_FOUND)

        return action_class[0]()

    def retrieve_options(self, parser, action):
        """Get a list of options from an action and prepend default options.

        Get an action's list of options and groups. Flat out options from the
        special "None" group and instantiate optparse.OptionGroup objects out of
        scout.plugins.OptionGroup objects.

        Arguments:
            parser -- The optparse.OptionParser needed to instantiate groups
            action -- A subclass of scout.plugins.ActionPlugin

        """
        options = self.default_options()

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

    def default_options(self):
        """Return a list of options common to all actions."""
        return [
            optparse.Option(
                "--application", dest="application",
                choices=["Tomboy", "Gnote"],
                help="""Choose the application to connect to. """
                    """APPLICATION must be one of Tomboy or Gnote."""
            )
        ]

    def parse_options(self, action, arguments):
        """Parse the command line arguments before launching an action.

        Retrieve options from the action. Then, parse them. Finally, return the
        resulting optparse.Values and list of positional arguments.

        Arguments:
            action -- A sub-class of scout.plugins.ActionPlugin
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
        required action and triggering its entry point. Exceptions raised in the
        action are catched and displayed to the user with an error message.

        Arguments:
            action_name -- A string representing the requested action
            arguments   -- A list of all the other arguments from the cli

        """
        action = self.load_action(action_name)

        # Get the configuration from file
        configuration = self.get_config()

        # Get the command line arguments
        try:
            options, positional_arguments = self.parse_options(
                action,
                arguments
            )
        except TypeError, exc:
            print >> sys.stderr, exc
            exit(ACTION_OPTION_TYPE_ERROR)

        # Find out which application to use
        application = self.determine_connection_app(configuration, options)

        # Create a Scout object and put a reference to it in the action
        try:
            action.interface = core.Scout(application)
        except ConnectionError, exc:
            print >> sys.stderr, "%s: Error: %s" % (
                os.path.basename(sys.argv[0]),
                exc
            )
            sys.exit(DBUS_CONNECTION_ERROR)
        except AutoDetectionError, exc:
            prog = os.path.basename( sys.argv[0] )
            msg = (os.linesep * 2).join([
                """%s: failed to determine which application to use.""",
                exc.__str__(),
                """Use the command line argument "--application" to specify """
                    """it manually or use the""" + os.linesep +
                    """"application" configuration option.""",
            ])
            print >> sys.stderr, msg % prog
            sys.exit(AUTODETECTION_FAILED)

        # Run the action
        try:
            action.perform_action(configuration, options, positional_arguments)
        except (SystemExit, KeyboardInterrupt):
            # Let the application exit if it wants to, and KeyboardInterrupt is
            # handled on an upper level so that interrupting execution with
            # Ctrl-C always exits cleanly.
            raise
        except NoteNotFound, exc:
            msg = """%s: Error: Note named "%s" was not found."""
            error_map = ( os.path.basename( sys.argv[0] ), exc )
            print >> sys.stderr, msg % error_map
            sys.exit(NOTE_NOT_FOUND)
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
            sys.exit(MALFORMED_ACTION)

    def get_config(self):
        """Load the configuration from a file."""
        config_parser = configparser.SafeConfigParser()

        config_parser.read([
            "/etc/scout.cfg",
            os.path.expanduser("~/.scout/config"),
            os.path.expanduser("~/.config/scout/config"),
        ])

        return self.sanitized_config(config_parser)

    def sanitized_config(self, parser):
        """Reject every unknown configuration in scout sectionself."""
        # If the core section is not there, add an empty one.
        if not parser.has_section(self.core_config_section):
            parser.add_section(self.core_config_section)

        # Keep only the options that we know of, thrash the rest
        for option in parser.options(self.core_config_section):
            if option not in self.core_options:
                parser.remove_option(self.core_config_section, option)

        return parser

    def determine_connection_app(self, config, options):
        """Determine if we need to force the use of one of Tomboy or Gnote."""
        # Command line option. This is the strongest user interaction. It takes
        # precedence over everything else.
        if options.application:
            return options.application

        # Configuration.
        if config.has_option(self.core_config_section, "application"):
            return config.get(self.core_config_section, "application")

        # None means to attempt autodetection
        return None

    def list_of_actions(self):
        """Retrieve a list of all registered actions.

        Return a list of classes corresponding to all the plugins.

        """
        group = "scout.actions"
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
            max,
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
            app_name_map = { "scout": os.path.basename(sys.argv[0]) }

            # Use the docstring's first [significant] lines to display usage
            usage_output =  (os.linesep * 2).join([
                os.linesep.join( __doc__.splitlines()[:3] ) % app_name_map,
                """For more details, use one of "-h", "--help" or "help"."""
            ])
            print >> sys.stderr, usage_output
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        action = sys.argv[1]
        # Convert the rest of the arguments to unicode objects so that they are
        # handled correctly afterwards. This expects to receive arguments in
        # UTF-8 format from the command line.
        arguments = [arg.decode("utf-8") for arg in sys.argv[2:] ]

        if action in ["-h", "--help", "help"]:
            if sys.argv[2:]:
                # Convert "help" into "-h" to fall into the same case.
                second_argument = action
                if action == "help":
                    second_argument = "-h"

                # Switch -h and action name and continue as normal.
                arguments = [sys.argv[2], second_argument] + sys.argv[3:]
                action = sys.argv[2]
            else:
                # Use the script's docstring for the basic help message. Also
                # get a list of available actions and display it.
                msg_map = {"scout": os.path.basename(sys.argv[0]) }
                help_msg = __doc__[:-1] % msg_map
                action_list = os.linesep.join( self.action_short_summaries() )

                print help_msg + action_list

                sys.exit(0)

        elif action in ["-v", "--version"]:
            version_info =  os.linesep.join([
                """Scout version %s""" % SCOUT_VERSION,
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
    try:
        CommandLine().main()
    # If it goes this far up, it means user asked for the program to exit.
    except KeyboardInterrupt:
        raise SystemExit, 1
