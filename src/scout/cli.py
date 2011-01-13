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
import sys
import os
import pkg_resources
import optparse
import ConfigParser as configparser

from scout import core
from scout.version import SCOUT_VERSION
from scout.core import NoteNotFound, ConnectionError, AutoDetectionError
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
NOTE_MODIFICATION_ERROR = 203

oldhook = sys.excepthook
def newhook(exctype, value, traceback):
    if exctype != KeyboardInterrupt:
        return oldhook(exctype, value, traceback)
sys.excepthook = newhook


class CommandLine(object):
    """Main entry point for Scout."""

    # config file general settings
    core_config_section = "scout"
    core_options = [
        "application",
        "display",
    ]

    default_options = [
        optparse.Option(
            "--application", dest="application",
            choices=["Tomboy", "Gnote"],
            help=''.join(["Choose the application to connect to. ",
                          "APPLICATION must be one of Tomboy or Gnote."])
        ),
        optparse.Option(
            "--display", dest="display",
            help=''.join(["Specify the X display on which the note ",
                          "application is running."])
        ),
    ]

    def load_action(self, action_name):
        """Load the 'action_name' action.

        Returns an instance of the action's plugin object.

        """
        action_class = [
            ac for ac in self.list_of_actions()
            if ac.name == action_name
        ]

        if not action_class:
            app_name = os.path.basename(sys.argv[0])

            print >> sys.stderr, ''.join([
                "%s: %s is not a valid action. Use option -h for a list of ",
                "available actions."]) % (app_name, action_name)

            sys.exit(ACTION_NOT_FOUND)

        return action_class[0]()

    def retrieve_options(self, parser, action):
        """Get a list of options from an action and prepend default options.

        Flat out options from the special "None" group and instantiate
        optparse.OptionGroup objects out of scout.plugins.OptionGroup objects.

        """
        options = list(self.default_options)

        # Retrieve the special "non-group" group and remove it from the list
        no_group_list = [g for g in action.option_groups if g.name is None]
        if no_group_list:
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
        """Parse the command line arguments.

        Retrieve options from the action. Then, parse them. Then, return the
        resulting optparse.Values and list of positional arguments.

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

        if options.display:
            os.environ['DISPLAY'] = options.display
        elif configuration.has_option(self.core_config_section, "display") and (
                not os.environ.get('DISPLAY')):
            os.environ['DISPLAY'] = configuration.get(self.core_config_section,
                                                      "display")

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
            prog = os.path.basename(sys.argv[0])
            msg = ("\n" * 2).join([
                "%s: failed to determine which application to use.",
                exc.__str__(),
                '\n'.join(["Use the command line argument \"--application\" to "
                                "specify it manually or use the",
                           "\"application\" configuration option."]),
            ])
            print >> sys.stderr, msg % prog
            sys.exit(AUTODETECTION_FAILED)

        # Run the action
        try:
            return action.perform_action(configuration, options,
                                         positional_arguments)
        except (SystemExit, KeyboardInterrupt):
            # Let the application exit if it wants to, and KeyboardInterrupt is
            # handled on an upper level so that interrupting execution with
            # Ctrl-C always exits cleanly.
            raise
        except NoteNotFound, exc:
            msg = "%s: Error: Note named \"%s\" was not found."
            error_map = (os.path.basename(sys.argv[0]), exc)
            print >> sys.stderr, msg % error_map
            sys.exit(NOTE_NOT_FOUND)
        except:
            import traceback

            app_name = os.path.basename(sys.argv[0])

            print >> sys.stderr, ''.join([
                "%s: the \"%s\" action is malformed: An uncaught exception ",
                "was raised while executing its \"perform_action\" ",
                "function:\n"]) % (app_name, action_name)
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

        # If the core section is not there, add an empty one.
        if not config_parser.has_section(self.core_config_section):
            config_parser.add_section(self.core_config_section)

        # Keep only the options that we know of, thrash the rest
        for option in config_parser.options(self.core_config_section):
            if option not in self.core_options:
                config_parser.remove_option(self.core_config_section, option)

        return config_parser

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
        pad_up_to = max([len(a.name) for a in actions])

        descriptions = []
        for action in actions:
            if action.short_description:
                description_text = action.short_description
            else:
                description_text = "No description available."

            descriptions.append(
                "  %s%s : %s" % (action.name,
                    " " * (pad_up_to - len(action.name)),
                    description_text)
            )

        return descriptions


def main():
    """Application entry point.

    Checks the first parameters for general help argument and dispatches the
    actions.

    """
    if len(sys.argv) < 2:
        app_name_map = {"scout": os.path.basename(sys.argv[0])}

        # Use the docstring's first [significant] lines to display usage
        usage_output =  ("\n" * 2).join([
            "\n".join(__doc__.splitlines()[:3]) % app_name_map,
            "For more details, use one of \"-h\", \"--help\" or \"help\"."
        ])
        print >> sys.stderr, usage_output
        sys.exit(TOO_FEW_ARGUMENTS_ERROR)

    cli = CommandLine()

    action = sys.argv[1]
    # Convert the rest of the arguments to unicode objects so that they are
    # handled correctly afterwards. This expects to receive arguments in
    # UTF-8 format from the command line.
    arguments = [arg.decode("utf-8") for arg in sys.argv[2:]]

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
            msg_map = {"scout": os.path.basename(sys.argv[0])}
            help_msg = __doc__[:-1] % msg_map
            action_list = "\n".join(cli.action_short_summaries())

            print help_msg + action_list

            sys.exit(0)

    elif action in ["-v", "--version"]:
        version_info =  '\n'.join([
            "Scout version %s" % SCOUT_VERSION,
            "Copyright © 2010 Gabriel Filion",
            "License: BSD",
            "This is free software: you are free to change and redistribute "
                "it.",
            "There is NO WARRANTY, to the extent permitted by law."
        ])

        print version_info
        sys.exit(0)

    sys.exit(cli.dispatch(action, arguments))
