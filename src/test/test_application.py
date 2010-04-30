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
"""
Application tests.

These are unit tests for the application's classes and methods.

The docstrings on the test methods are displayed as labels for the tests by the
test runner, so it should be a short but precise one-line description of what
is being tested. There should also be the test case's second word followed by a
colon to classify tests. Having this classification makes looking for failing
tests a lot easier.

"""
import os
import sys
import datetime
import time
import dbus
import pkg_resources
import traceback
import optparse
import ConfigParser as configparser

from scout import core, cli, plugins
# Import the list action under a different name to avoid overwriting the list()
# builtin function.
from scout.actions import display, list as _list, delete, search, version

from . import data as test_data
from . import bases

class TestMain(bases.BasicMocking, bases.CLIMocking):
    """Tests for functions in the main script.

    This test case verifies that functions in the main script behave as
    expected.

    """
    def test_KeyboardInterrupt_is_handled(self):
        """Main: KeyboardInterrupt doesn't come out of the application."""
        cli_mock = self.m.CreateMock(cli.CommandLine)

        self.m.StubOutWithMock(
            cli,
            "CommandLine",
            use_mock_anything=True
        )

        cli.CommandLine()\
            .AndReturn( cli_mock )

        cli_mock.main().AndRaise(KeyboardInterrupt)

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.exception_wrapped_main
        )

        self.m.VerifyAll()

    def test_arguments_converted_to_unicode(self):
        """Main: Arguments to action are converted to unicode objects."""
        """This is the default main() behaviour."""
        command_line = self.wrap_subject(cli.CommandLine, "main")

        arguments = ["arg1", "arg2"]
        sys.argv = ["app_name", "action"] + arguments

        command_line.dispatch("action", [unicode(arg) for arg in arguments] )

        self.m.ReplayAll()

        command_line.main()

        self.m.VerifyAll()

    def verify_exit_from_main(self,
            arguments, expected_text, output_stream):

        command_line = self.wrap_subject(cli.CommandLine, "main")

        sys.argv = ["app_name"] + arguments

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            command_line.main
        )

        self.m.VerifyAll()

        self.assertEqual(
            expected_text + os.linesep,
            output_stream.getvalue()
        )

    def test_not_enough_arguments(self):
        """Main: main() called with too few arguments gives an error."""
        self.verify_exit_from_main(
            [],
            test_data.too_few_arguments_error,
            output_stream=sys.stderr
        )

    def verify_main_help(self, argument):
        """Test that help exits and displays the main help."""
        command_line = self.wrap_subject(cli.CommandLine, "main")

        sys.argv = ["app_name", argument]

        command_line.action_short_summaries()\
            .AndReturn(test_data.module_descriptions)

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            command_line.main
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.main_help +
                os.linesep.join(test_data.module_descriptions) +
                os.linesep,
            sys.stdout.getvalue()
        )

    def test_main_help(self):
        """Main: using only -h prints help and list of actions."""
        self.verify_main_help("-h")

    def test_main_help_from_help_pseudo_action(self):
        """Main: "help" pseudo-action alone should display main help."""
        self.verify_main_help("help")

    def verify_help_argument_reversing(self, argument):
        """Test reversal of arguments and conversion of "help" to "-h"."""
        command_line = self.wrap_subject(cli.CommandLine, "main")

        sys.argv = ["app_name", argument, "action"]

        processed_arguments = [ sys.argv[0], sys.argv[2], "-h" ]

        command_line.dispatch(
            "action",
            [unicode(arg) for arg in processed_arguments[1:] ]
        )

        self.m.ReplayAll()

        command_line.main()

        self.m.VerifyAll()

    def test_help_before_action(self):
        """Main: -h before action gets switched to normal help call."""
        self.verify_help_argument_reversing("-h")

    def test_help_pseudo_action_before_action(self):
        """Main: "help" pseudo-action displays details about an action."""
        self.verify_help_argument_reversing("help")

    def test_display_scout_version(self):
        """Main: -v option displays Scout's version and license information."""
        self.verify_exit_from_main(
            ["-v"],
            test_data.version_and_license_info,
            output_stream=sys.stdout
        )

    def test_list_of_actions(self):
        """Main: list_of_actions returns classes of action plugins."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "list_of_actions"
        )
        self.m.StubOutWithMock(pkg_resources, "iter_entry_points")

        # Entry points as returned by pkg_resources
        entry_points = [
            self.m.CreateMock(pkg_resources.EntryPoint),
            self.m.CreateMock(pkg_resources.EntryPoint),
            self.m.CreateMock(pkg_resources.EntryPoint),
            self.m.CreateMock(pkg_resources.EntryPoint),
        ]

        # Force the entry point names
        for (index, entry_point) in enumerate(entry_points):
            entry_point.name = "action%d" % index

        # Plugin classes as returned by EntryPoint.load()
        plugin_classes = [
            plugins.ActionPlugin,
            plugins.ActionPlugin,
            plugins.ActionPlugin,
            # The last one on the list is not a subclass of ActionPlugin and
            # should get discarded
            core.Scout,
        ]

        pkg_resources.iter_entry_points(group="scout.actions")\
            .AndReturn(entry_points)

        for (index, entry_point) in enumerate(entry_points):
            entry_point.load()\
                .AndReturn( plugin_classes[index] )

        self.m.ReplayAll()

        # "name" attributes are irrelevant here as 3 classes are the same
        self.assertEqual(
            plugin_classes[:-1],
            command_line.list_of_actions()
        )

        self.m.VerifyAll()

    def test_load_action(self):
        """Main: Initialize an action plugin instance."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "load_action"
        )

        action1 = self.m.CreateMockAnything()
        action1.name = "action1"
        action2 = self.m.CreateMockAnything()
        action2.name = "action2"

        mock_class = self.m.CreateMockAnything()

        command_line.list_of_actions()\
            .AndReturn( [action1, action2] )

        action2()\
            .AndReturn( mock_class )

        self.m.ReplayAll()

        self.assertEqual(
            mock_class,
            command_line.load_action("action2")
        )

        self.m.VerifyAll()

    def test_load_unknown_action(self):
        """Main: Requested action name is invalid."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "load_action"
        )

        self.m.StubOutWithMock(os.path, "basename")

        sys.argv = ["app_name"]

        command_line.list_of_actions()\
            .AndReturn( [] )

        os.path.basename("app_name")\
            .AndReturn("app_name")

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            command_line.load_action, "unexistant_action"
        )

        self.assertEqual(
            test_data.unknown_action + os.linesep,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_action_short_summaries(self):
        """Main: Extract short summaries from action plugins."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "action_short_summaries"
        )

        action1 = self.m.CreateMockAnything()
        action1.name = "action1"
        action1.short_description = test_data.module1_description
        action2 = self.m.CreateMockAnything()
        action2.name = "otheraction"
        action2.short_description = None

        command_line.list_of_actions()\
            .AndReturn( [action1, action2] )

        self.m.ReplayAll()

        self.assertEqual(
            test_data.module_descriptions,
            command_line.action_short_summaries()
        )

        self.m.VerifyAll()

    def mock_out_dispatch(self, exception_class, exception_argument,
            app_name="Tomboy"):
        """Mock out calls in dispatch that we go through in all cases."""
        command_line = self.wrap_subject(cli.CommandLine, "dispatch")

        fake_scout = self.m.CreateMock(core.Scout)

        self.m.StubOutWithMock(core, "Scout", use_mock_anything=True)

        action_name = "some_action"
        fake_action = self.m.CreateMock(plugins.ActionPlugin)
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)
        arguments = self.m.CreateMock(list)
        positional_arguments = self.m.CreateMock(list)
        options = self.m.CreateMock(optparse.Values)
        options.gnote = False

        command_line.load_action(action_name)\
            .AndReturn(fake_action)

        command_line.get_config()\
            .AndReturn( fake_config )

        command_line.parse_options(fake_action, arguments)\
            .AndReturn( (options, positional_arguments) )

        command_line.determine_connection_app(fake_config, options)\
            .AndReturn(app_name)

        if exception_class in [core.ConnectionError, core.AutoDetectionError]:
            core.Scout(app_name)\
                .AndRaise( exception_class(exception_argument) )
            return (command_line, action_name, fake_action, arguments)
        else:
            core.Scout(app_name)\
                .AndReturn( fake_scout )

        if exception_class:
            fake_action.perform_action(
                fake_config,
                options,
                positional_arguments
            ).AndRaise( exception_class(exception_argument) )
        else:
            fake_action.perform_action(
                fake_config,
                options,
                positional_arguments
            ).AndReturn(None)

        return (command_line, action_name, fake_action, arguments)

    def test_dispatch(self):
        """Main: Action calls are dispatched to the right action."""
        command_line, action_name, fake_action, arguments = \
            self.mock_out_dispatch(None, None)

        self.m.ReplayAll()

        command_line.dispatch(action_name, arguments)

        self.m.VerifyAll()

    def test_dispatch_with_gnote(self):
        """Main: Dispatch instantiates Scout for Gnote."""
        command_line, action_name, fake_action, arguments = \
            self.mock_out_dispatch(None, None, "Gnote")

        self.m.ReplayAll()

        command_line.dispatch(action_name, arguments)

        self.m.VerifyAll()

    def verify_dispatch_exception(self, exception_class,
            exception_out=None, exception_argument="",
            expected_text=""):
        """Verify that dispatch lets a specific exception go through.

        dispatch should let some exceptions stay unhandled. They are handled on
        a higher level so that their processing stays the most global possible.
        The rest of the exceptions coming from the action call should be
        handled.

        By default, exception expected in output is the same. This can be
        changed by passing in another exception to the argument exception_out.
        By default, it also expects to have no output on stderr. To expect
        somee text in stderr, pass the string to the argument expected_text.

        An argument can be given to the exception upon instanciation with the
        argument exception_argument.

        Arguments:
            exception_class -- Class of the exception that goes through
            exception_out -- If defined, exception expected to come out
            expected_text -- String of text that is expected on stderr

        """
        # Raise catch same exception by default
        if not exception_out:
            exception_out = exception_class

        command_line, action_name, fake_action, arguments = \
            self.mock_out_dispatch(exception_class, exception_argument)

        self.m.ReplayAll()

        self.assertRaises(
            exception_out,
            command_line.dispatch, action_name, arguments
        )
        self.assertEqual(
            expected_text,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_dispatch_SystemExit_goes_through(self):
        """Main: SystemExit exceptions pass through dispatch."""
        self.verify_dispatch_exception(SystemExit)

    def test_dispatch_KeyboardInterrupt_goes_through(self):
        """Main: KeyboardInterrupt exceptions pass through dispatch."""
        self.verify_dispatch_exception(KeyboardInterrupt)

    def test_dispatch_handles_ConnectionError(self):
        """Main: ConnectionError should print an error message."""
        sys.argv = ["app_name"]
        self.verify_dispatch_exception(
            core.ConnectionError,
            exception_out=SystemExit,
            exception_argument="there was a problem",
            expected_text=test_data.connection_error_message + os.linesep
        )

    def test_dispatch_handles_NoteNotFound(self):
        """Main: NoteNotFound exceptions dont't go unhandled."""
        sys.argv = ["app_name"]
        self.verify_dispatch_exception(
            core.NoteNotFound,
            exception_out=SystemExit,
            exception_argument="unexistant",
            expected_text=test_data.unexistant_note_error + os.linesep
        )

    def test_dispatch_handles_AutoDetectionError(self):
        """Main: No sensible application choice was identified."""
        sys.argv = ["app_name"]
        self.verify_dispatch_exception(
            core.AutoDetectionError,
            exception_out=SystemExit,
            exception_argument="autodetection failed for some reason",
            expected_text=test_data.autodetection_error + os.linesep
        )

    def print_traceback(self):
        """Fake an output of an arbitrary traceback on sys.stderr"""
        print >> sys.stderr, test_data.fake_traceback

    def test_dispatch_handles_action_exceptions(self):
        """Main: All unknown exceptions from actions are handled."""
        command_line, action_name, fake_action, arguments = \
            self.mock_out_dispatch(Exception, "something happened")

        sys.argv = ["app_name"]

        self.m.StubOutWithMock(os.path, "basename")
        self.m.StubOutWithMock(traceback, "print_exc")

        os.path.basename(sys.argv[0])\
            .AndReturn(sys.argv[0])

        traceback.print_exc()

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            command_line.dispatch, action_name, arguments
        )

        self.m.VerifyAll()


    def test_dispatch_handles_option_type_exceptions(self):
        """Main: dispatch prints an error if an option is of the wrong type."""
        command_line = self.wrap_subject(cli.CommandLine, "dispatch")

        action_name = "some_action"
        fake_action = self.m.CreateMock(plugins.ActionPlugin)
        fake_action.name = action_name
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)
        arguments = self.m.CreateMock(list)

        command_line.load_action(action_name)\
            .AndReturn(fake_action)

        command_line.get_config()\
            .AndReturn(fake_config)

        command_line.parse_options(fake_action, arguments)\
            .AndRaise( TypeError(test_data.option_type_error_message) )

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            command_line.dispatch, action_name, arguments
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.option_type_error_message + os.linesep,
            sys.stderr.getvalue()
        )

    def test_parse_options(self):
        """Main: Parse an action's options and return them"""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "parse_options"
        )

        option_parser = self.m.CreateMock(optparse.OptionParser)
        self.m.StubOutWithMock(optparse, "OptionParser", use_mock_anything=True)

        fake_action = self.m.CreateMock(plugins.ActionPlugin)
        fake_action.usage = "%prog [options]"
        option_list = [
            self.m.CreateMock(optparse.Option),
            self.m.CreateMock(optparse.Option),
            self.m.CreateMock(optparse.OptionGroup),
        ]
        fake_values = self.m.CreateMock(optparse.Values)
        arguments = ["--meuh", "arg1"]
        positional_arguments = ["arg1"]

        command_line.retrieve_options(option_parser, fake_action)\
            .AndReturn(option_list)

        optparse.OptionParser(usage="%prog [options]")\
            .AndReturn( option_parser )

        fake_action.init_options()

        option_parser.add_option(option_list[0])
        option_parser.add_option(option_list[1])
        option_parser.add_option_group(option_list[2])

        option_parser.parse_args(arguments)\
            .AndReturn( (fake_values, positional_arguments) )

        self.m.ReplayAll()

        result = command_line.parse_options(fake_action, arguments)

        self.m.VerifyAll()

        self.assertEqual(
            (fake_values, positional_arguments),
            result
        )

    def test_retrieve_options(self):
        """Main: Get a list of options from an action plugin."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "retrieve_options"
        )

        fake_group = self.m.CreateMock(optparse.OptionGroup)

        self.m.StubOutWithMock(optparse, "OptionGroup", use_mock_anything=True)

        fake_action = self.m.CreateMock(plugins.ActionPlugin)
        fake_option_parser = self.m.CreateMock(optparse.OptionParser)

        option1 = self.m.CreateMock(optparse.Option)
        option2 = self.m.CreateMock(optparse.Option)
        option3 = self.m.CreateMock(optparse.Option)

        group1 = self.m.CreateMock(plugins.OptionGroup)
        group1.name = None
        group1.options = [option1]
        group2 = self.m.CreateMock(plugins.OptionGroup)
        group2.name = "Group2"
        group2.description = "dummy"

        group2.options = [option1, option2]

        fake_action.option_groups = [group1, group2]

        command_line.default_options()\
            .AndReturn([])

        optparse.OptionGroup(
            fake_option_parser,
            "Group2",
            "dummy"
        ).AndReturn(fake_group)

        fake_group.add_option(option1)
        fake_group.add_option(option2)

        list_of_options = [option1, fake_group]

        self.m.ReplayAll()

        result = command_line.retrieve_options(fake_option_parser, fake_action)

        self.m.VerifyAll()

        self.assertEqual(
            list_of_options,
            result
        )

    def test_default_options(self):
        """Main: List of default options."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "default_options"
        )
        self.m.StubOutWithMock(optparse, "Option", use_mock_anything=True)

        gnote_option = self.m.CreateMock(optparse.Option)

        options = [
            gnote_option,
        ]

        optparse.Option(
            "--application", dest="application", choices=["Tomboy", "Gnote"],
            help="""Choose the application to connect to. """
                """APPLICATION must be one of Tomboy or Gnote."""
        ).AndReturn(gnote_option)

        self.m.ReplayAll()

        self.assertEqual(
            options,
            command_line.default_options()
        )

        self.m.VerifyAll()

    def test_determine_connection_app_cli_argument(self):
        """Main: Application specified on command line."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "determine_connection_app"
        )

        fake_opt_values = self.m.CreateMock(optparse.Values)
        fake_opt_values.application = "Gnote"
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        self.m.ReplayAll()

        self.assertEqual(
            "Gnote",
            command_line.determine_connection_app(fake_config, fake_opt_values)
        )

        self.m.VerifyAll()

    def test_determine_connection_app_configuration(self):
        """Main: No user choice of application."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "determine_connection_app"
        )
        command_line.core_config_section = "core_section"

        fake_opt_values = self.m.CreateMock(optparse.Values)
        fake_opt_values.application = None
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        fake_config.has_option("core_section", "application")\
            .AndReturn(True)

        fake_config.get("core_section", "application")\
            .AndReturn("this_one")

        self.m.ReplayAll()

        self.assertEqual(
            "this_one",
            command_line.determine_connection_app(fake_config, fake_opt_values)
        )

        self.m.VerifyAll()

    def test_determine_connection_app_undecided(self):
        """Main: No user choice of application."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "determine_connection_app"
        )
        command_line.core_config_section = "core_section"

        fake_opt_values = self.m.CreateMock(optparse.Values)
        fake_opt_values.application = None
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        fake_config.has_option("core_section", "application")\
            .AndReturn(False)

        self.m.ReplayAll()

        self.assertEqual(
            None,
            command_line.determine_connection_app(fake_config, fake_opt_values)
        )

        self.m.VerifyAll()

    def test_get_config(self):
        """Main: Retrieve configuration values from a file."""
        command_line = self.wrap_subject(cli.CommandLine, "get_config")

        fake_parser = self.m.CreateMock(configparser.SafeConfigParser)
        self.m.StubOutWithMock(
            configparser,
            "SafeConfigParser",
            use_mock_anything=True
        )

        self.m.StubOutWithMock(os.path, "expanduser")

        fake_sanitized = self.m.CreateMockAnything()

        configparser.SafeConfigParser()\
            .AndReturn(fake_parser)

        os.path.expanduser("~/.scout/config")\
            .AndReturn("/home/borg/.scout/config")
        os.path.expanduser("~/.config/scout/config")\
            .AndReturn("/home/borg/.config/scout/config")

        fake_parser.read([
            "/etc/scout.cfg",
            "/home/borg/.scout/config",
            "/home/borg/.config/scout/config",
        ])

        command_line.sanitized_config(fake_parser)\
            .AndReturn( fake_sanitized )

        self.m.ReplayAll()

        self.assertEqual(
            fake_sanitized,
            command_line.get_config()
        )

        self.m.VerifyAll()

    def verify_sanitized_config(self, section_is_present):
        """Test the configuration sanitization process."""
        command_line = self.wrap_subject(cli.CommandLine, "sanitized_config")

        command_line.core_config_section = "this"
        command_line.core_options = ["option1", "bobby-tables"]

        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        fake_config.has_section("this")\
            .AndReturn(section_is_present)

        if not section_is_present:
            fake_config.add_section("this")

        fake_config.options("this")\
            .AndReturn(["option1", "unwanted", "bobby-tables"])

        fake_config.remove_option("this", "unwanted")

        self.m.ReplayAll()

        command_line.sanitized_config(fake_config)

        self.m.VerifyAll()

    def test_sanitized_config(self):
        """Main: Core configuration retains only values that are known."""
        self.verify_sanitized_config(True)

    def test_sanitized_config_missing_section(self):
        """Main: Core configuration section is not present."""
        self.verify_sanitized_config(False)

class TestCore(bases.BasicMocking):
    """Tests for general code."""

    def verify_Scout_constructor(self, application):
        """Test Scout's constructor."""
        tt = self.wrap_subject(core.Scout, "__init__")

        session_bus = self.m.CreateMock(dbus.SessionBus)
        dbus_interface = self.m.CreateMock(dbus.Interface)

        self.m.StubOutWithMock(dbus, "SessionBus", use_mock_anything=True)
        self.m.StubOutWithMock(dbus, "Interface", use_mock_anything=True)

        dbus_object = self.m.CreateMock(dbus.proxies.ProxyObject)

        dbus.SessionBus()\
            .AndReturn(session_bus)

        app_name = application

        if application is None:
            tt._autodetect_app(session_bus)\
                .AndReturn( tuple(["Tomboy", dbus_object]) )
            app_name = "Tomboy"
        else:
            if application == "fail_app":
                session_bus.get_object(
                    "org.gnome.%s" % app_name,
                    "/org/gnome/%s/RemoteControl" % app_name
                ).AndRaise(dbus.DBusException)
            else:
                session_bus.get_object(
                    "org.gnome.%s" % app_name,
                    "/org/gnome/%s/RemoteControl" % app_name
                ).AndReturn(dbus_object)

        if application != "fail_app":
            dbus.Interface(
                dbus_object,
                "org.gnome.%s.RemoteControl" % app_name
            ).AndReturn(dbus_interface)

        self.m.ReplayAll()

        if application == "fail_app":
            self.assertRaises(
                core.ConnectionError,
                tt.__init__, application
            )
        else:
            tt.__init__(application)

        self.m.VerifyAll()

        if application != "fail_app":
            self.assertEqual(dbus_interface, tt.comm)
            self.assertEqual(app_name, tt.application)

    def test_Scout_constructor(self):
        """Core: Scout's dbus interface is initialized."""
        self.verify_Scout_constructor("the_application")

    def test_Scout_constructor_with_autodetection(self):
        """Core: Scout's dbus interface is autodetected and initialized."""
        self.verify_Scout_constructor(None)

    def test_Scout_constructor_application_fails(self):
        """Core: Scout's dbus interface is unavailable."""
        self.verify_Scout_constructor("fail_app")

    def test_dbus_Tomboy_communication_problem(self):
        """Core: Raise an exception if linking dbus with Tomboy failed."""
        tt = self.wrap_subject(core.Scout, "__init__")

        session_bus = self.m.CreateMock(dbus.SessionBus)

        self.m.StubOutWithMock(dbus, "SessionBus", use_mock_anything=True)

        dbus.SessionBus()\
            .AndRaise( dbus.DBusException("cosmos error") )

        self.m.ReplayAll()

        self.assertRaises(core.ConnectionError, tt.__init__, "Tomboy")

        self.m.VerifyAll()

    def verify_TomboyNote_constructor(self, **kwargs):
        """Build a TomboyNote mock and make __init__ its test subject."""
        tn = self.wrap_subject(core.TomboyNote, "__init__")

        self.m.ReplayAll()

        tn.__init__(**kwargs)

        self.m.VerifyAll()

        return tn

    def test_TomboyNote_constructor_all_args_int64(self):
        """Core: TomboyNote initializes its instance variables. case 1."""
        uri1 = "note://something-like-this"
        title = "Name"
        date_int64 = dbus.Int64()
        tags = ["tag1", "tag2"]

        # case 1: Construct with all data and a dbus.Int64 date
        tn = self.verify_TomboyNote_constructor(
            uri=uri1,
            title=title,
            date=date_int64,
            tags=tags
        )

        self.assertEqual(uri1, tn.uri)
        self.assertEqual(title, tn.title)
        self.assertEqual(date_int64, tn.date)
        # Order is not important
        self.assertEqual( set(tags), set(tn.tags) )

    def test_TomboyNote_constructor_all_defaults(self):
        """Core: TomboyNote initializes its instance variables. case 2."""
        uri2 = "note://another-false-uri"

        tn = self.verify_TomboyNote_constructor(uri=uri2)

        # case 2: Construct with only uri, rest is default
        self.assertEqual(tn.uri, uri2)
        self.assertEqual(tn.title, "")
        self.assertEqual(tn.date, dbus.Int64() )
        self.assertEqual(tn.tags, [])

    def test_TomboyNote_constructor_datetetime(self):
        """Core: TomboyNote initializes its instance variables. case 2."""
        datetime_date = datetime.datetime(2009, 11, 13, 18, 42, 23)

        # case 3: the date can be entered with a datetime.datetime
        tn = self.verify_TomboyNote_constructor(
            uri="not important",
            date=datetime_date
        )

        self.assertEqual(
            dbus.Int64(
                time.mktime( datetime_date.timetuple() )
            ),
            tn.date
        )

    def verify_get_notes(self, tags=None, names=None, exclude=True, count=0):
        """Test note retrieval."""
        if tags is None:
            expected_tags = []
        else:
            expected_tags = tags
        if names is None:
            expected_names = []
        else:
            expected_names = names

        if tags is not None and "system:template" in tags:
            should_exclude = False
        else:
            should_exclude = exclude

        tt = self.wrap_subject(core.Scout, "get_notes")

        notes = test_data.full_list_of_notes(self.m)

        fake_filtered_list = [
            self.m.CreateMockAnything(),
            self.m.CreateMockAnything(),
            self.m.CreateMockAnything(),
            self.m.CreateMockAnything(),
            self.m.CreateMockAnything(),
        ]

        tt.build_note_list()\
            .AndReturn(notes)

        tt.filter_notes(
            notes,
            names=expected_names,
            tags=expected_tags,
            exclude_templates=should_exclude
        ).AndReturn(fake_filtered_list)

        self.m.ReplayAll()

        result = tt.get_notes(
            tags=tags,
            names=names,
            exclude_templates=exclude,
            count_limit=count
        )

        self.m.VerifyAll()

        return result

    def test_get_notes(self):
        """Core: No filtering but templates removed."""
        self.verify_get_notes()

    def test_get_notes_number_limited(self):
        """Core: No filtering but templates removed."""
        list_of_notes = self.verify_get_notes(count=3)

        self.assertEqual(
            3,
            len(list_of_notes)
        )

    def test_get_notes_with_templates(self):
        """Core: Filtered notes but templates included."""
        self.verify_get_notes(
            tags=["sometag", "othertag"],
            names=["note1", "note2"],
            exclude=False
        )

    def test_get_notes_template_as_a_tag(self):
        """Core: Specifying templates as a tag should include them."""
        self.verify_get_notes( tags=["system:template", "someothertag"] )

    def verify_filter_notes(self, tags, names, exclude=True):
        """Test note filtering."""
        tt = self.wrap_subject(core.Scout, "filter_notes")

        notes = test_data.full_list_of_notes(self.m)

        if tags or names:
            expected_list = [
                n for n in notes
                if set(n.tags).intersection( set(tags) )
                   or n.title == "addressbook"
            ]
        else:
            expected_list = notes

        if exclude:
            expected_list = [
                n for n in expected_list
                if "system:template" not in n.tags
            ]

        self.m.ReplayAll()

        result = tt.filter_notes(
            notes,
            tags=tags,
            names=names,
            exclude_templates=exclude
        )

        self.m.VerifyAll()

        self.assertEqual(
            expected_list,
            result
        )

    def test_filter_notes(self):
        """Core: Note filtering."""
        self.verify_filter_notes(
            tags=["system:notebook:projects"],
            names=["addressbook"]
        )

    def test_fiter_notes_with_templates(self):
        """Core: Do not exclude templates."""
        self.verify_filter_notes(
            tags=["system:notebook:projects"],
            names=["addressbook"],
            exclude=False
        )

    def test_filter_notes_no_filtering(self):
        """Core: No filtering gives the full list of notes."""
        self.verify_filter_notes(
            tags=[],
            names=[],
            exclude=False
        )

    def test_filter_notes_unknown_note(self):
        """Core: Filtering encounters an unknown note name."""
        tt = self.wrap_subject(core.Scout, "filter_notes")

        notes = test_data.full_list_of_notes(self.m)

        self.m.ReplayAll()

        self.assertRaises(
            core.NoteNotFound,
            tt.filter_notes, notes, tags=[], names=["unknown"]
        )

        self.m.VerifyAll()

    def verify_note_list(self, tt, notes, note_names=[]):
        """Verify the outcome of Scout.get_notes().

        This function verifies if notes received from calling
        Scout.get_notes are what we expect them to be. It provokes
        the unit test to fail in case of discordance.

        TomboyNotes are unhashable so we need to convert them to dictionaries
        and check for list membership.

        Arguments:
            self       -- The TestCase instance
            tt         -- Scout mock object instance
            notes      -- list of TomboyNote objects
            note_names -- list of note names to pass to get_notes

        """
        expectation = [{
            "uri":n.uri,
            "title":n.title,
            "date":n.date,
            "tags":n.tags,
        } for n in notes]

        # Order is not important
        for note in tt.build_note_list():
            note_as_dict = {
                "uri":note.uri,
                "title":note.title,
                "date":note.date,
                "tags":note.tags
            }

            if note_as_dict not in expectation:
                self.fail(
                    """Note named %s dated %s """ % (note.title, note.date) + \
                    """with uri %s and """ % (note.uri, ) + \
                    """tags [%s] not found in """ % (",".join(note.tags), ) + \
                    """expectation: [%s]""" % (",".join(expectation), )
                )

    def test_build_note_list(self):
        """Core: Scout gets a full list of notes."""
        tt = self.wrap_subject(core.Scout, "build_note_list")

        tt.comm = self.m.CreateMockAnything()

        list_of_notes = test_data.full_list_of_notes(self.m)

        list_of_uris = dbus.Array(
            [note.uri for note in list_of_notes]
        )

        tt.comm.ListAllNotes()\
            .AndReturn(list_of_uris)

        for note in list_of_notes:
            tt.comm.GetNoteTitle(note.uri)\
                .AndReturn(note.title)
            tt.comm.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            tt.comm.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

        self.m.ReplayAll()

        self.verify_note_list(tt, list_of_notes)

        self.m.VerifyAll()

    def verify_autodetect_app(self, expected_apps):
        """Test autodetection of the dbus application to use."""
        tt = self.wrap_subject(core.Scout, "_autodetect_app")

        fake_bus = self.m.CreateMock(dbus.SessionBus)
        fake_object = self.m.CreateMock(dbus.proxies.ProxyObject)

        for app in ["Tomboy", "Gnote"]:
            if app in expected_apps:
                fake_bus.get_object(
                    "org.gnome.%s" % app,
                    "/org/gnome/%s/RemoteControl" % app
                ).AndReturn(fake_object)
            else:
                fake_bus.get_object(
                    "org.gnome.%s" % app,
                    "/org/gnome/%s/RemoteControl" % app
                ).AndRaise(dbus.DBusException)

        self.m.ReplayAll()

        if len(expected_apps) == 1:
            self.assertEqual(
                (expected_apps[0], fake_object),
                tt._autodetect_app(fake_bus)
            )
        else:
            self.assertRaises(
                core.AutoDetectionError,
                tt._autodetect_app, fake_bus
            )

        self.m.VerifyAll()

    def test_autodetect_app(self):
        """Core: Autodetect, only one application is running."""
        self.verify_autodetect_app( ["Tomboy"] )

    def test_autodetect_app_none(self):
        """Core: Autodetection fails to find any application."""
        self.verify_autodetect_app( [] )

    def test_autodetect_app_too_much(self):
        """Core: Autodetection fails to find any application."""
        self.verify_autodetect_app( ["Tomboy", "Gnote"] )

class TestList(bases.BasicMocking, bases.CLIMocking):
    """Tests for code that handles the notes and lists them."""

    def test_listing(self):
        """List: Format information of a list of notes."""
        lst_ap = self.wrap_subject(_list.ListAction, "listing")

        list_of_notes = test_data.full_list_of_notes(self.m)
        # Forget about the last note (a template)
        list_of_notes = list_of_notes[:-1]

        for note in list_of_notes:
            tag_text = ""
            if len(note.tags):
                tag_text = "  (" + ", ".join(note.tags) + ")"

            note.listing()\
                .AndReturn("%(date)s | %(title)s%(tags)s" %
                    {
                        "date": datetime.datetime.fromtimestamp(note.date)\
                                    .isoformat()[:10],
                        "title": note.title,
                        "tags": tag_text
                    }
                )

        self.m.ReplayAll()

        self.assertEqual(
            test_data.expected_list + os.linesep + test_data.list_appendix,
            lst_ap.listing(list_of_notes)
        )

        self.m.VerifyAll()

    def verify_note_listing(self, title, tags, new_title, expected_tag_text):
        """Test note listing with a given set of title and tags.

        This verifies the results of calling TomboyNote.listing to get its
        information for listing.

        Arguments:
            title             -- The title returned by dbus
            tags              -- list of tag names returned by dbus
            new_title         -- The expected title generated by the function
            expected_tag_text -- The expected format of tags from get_notes

        """
        note = self.wrap_subject(core.TomboyNote, "listing")

        date_64 = dbus.Int64(1254553804L)

        note.title = title
        note.date = date_64
        note.tags = tags

        expected_listing = "2009-10-03 | %(title)s%(tags)s" % {
            "title": new_title,
            "tags": expected_tag_text
        }

        self.m.ReplayAll()

        self.assertEqual( expected_listing, note.listing() )

        self.m.VerifyAll()

    def test_TomboyNote_listing(self):
        """List: Print one note's information."""
        self.verify_note_listing(
            "Test",
            ["tag1", "tag2"],
            "Test",
            "  (tag1, tag2)"
        )

    def test_TomboyNote_listing_no_title_no_tags(self):
        """List: Verify listing format with no title and no tags."""
        self.verify_note_listing(
            "",
            [],
            "_note doesn't have a name_",
            ""
        )

    def test_init_options(self):
        """List: options are initialized correctly."""
        lst_ap = self.wrap_subject(_list.ListAction, "init_options")
        self.m.StubOutWithMock(
            plugins,
            "FilteringGroup",
            use_mock_anything=True
        )

        lst_ap.add_option(
            "-n", type="int",
            dest="max_notes", default=None,
            help="Limit the number of notes listed."
        )

        fake_filtering = self.m.CreateMock(plugins.FilteringGroup)

        plugins.FilteringGroup("List")\
            .AndReturn(fake_filtering)

        lst_ap.add_option_library(fake_filtering)

        self.m.ReplayAll()

        lst_ap.init_options()

        self.m.VerifyAll()

    def verify_perform_action(self, with_templates):
        """Verify execution of ListAction.perform_action

        Verify that perform_action does what is expected given a set of options.

        Arguments:
            with_templates -- boolean, request templates in the listing

        """
        lst_ap = self.wrap_subject(_list.ListAction, "perform_action")
        lst_ap.tomboy_interface = self.m.CreateMock(core.Scout)

        tags = ["whatever"]

        fake_options = self.m.CreateMock(optparse.Values)
        # Duplicate the list to avoid modification by later for loop
        fake_options.tags = list(tags)
        fake_options.templates = with_templates
        fake_options.max_notes = 5
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        list_of_notes = test_data.full_list_of_notes(self.m)

        lst_ap.tomboy_interface.get_notes(
            count_limit=5,
            tags=tags,
            exclude_templates=not with_templates
        ).AndReturn(list_of_notes)

        lst_ap.listing(list_of_notes)\
            .AndReturn(test_data.expected_list)

        self.m.ReplayAll()

        lst_ap.perform_action(fake_config, fake_options, [])

        self.m.VerifyAll()

        self.assertEqual(
            test_data.expected_list + os.linesep,
            sys.stdout.getvalue()
        )

    def test_perform_action(self):
        """List: perform_action called without arguments."""
        self.verify_perform_action(with_templates=False)

    def test_perform_action_templates(self):
        """List: perform_action called with a tag as filter."""
        self.verify_perform_action(with_templates=True)

class TestDisplay(bases.BasicMocking, bases.CLIMocking):
    """Tests for code that display notes' content."""
    def test_get_display_for_notes(self):
        """Display: Scout returns notes' contents, separated a marker."""
        dsp_ap = self.wrap_subject(
            display.DisplayAction,
            "format_display_for_notes"
        )
        dsp_ap.tomboy_interface = self.m.CreateMock(core.Scout)

        list_of_notes = test_data.full_list_of_notes(self.m)

        notes = [
            list_of_notes[10],
            list_of_notes[8]
        ]
        note_names = [n.title for n in notes]
        note1_content = test_data.note_contents_from_dbus[ notes[0].title ]
        note2_content = test_data.note_contents_from_dbus[ notes[1].title ]

        dsp_ap.tomboy_interface.get_note_content(notes[0])\
            .AndReturn(note1_content)
        dsp_ap.tomboy_interface.get_note_content(notes[1])\
            .AndReturn(note2_content)

        self.m.ReplayAll()

        self.assertEqual(
            os.linesep.join([
                note1_content,
                test_data.display_separator,
                note2_content,
            ]),
            dsp_ap.format_display_for_notes(notes)
        )

        self.m.VerifyAll()

    def test_Scout_get_note_content(self):
        """Display: Using the communicator, get one note's content."""
        tt = self.wrap_subject(core.Scout, "get_note_content")

        tt.comm = self.m.CreateMockAnything()

        list_of_notes = test_data.full_list_of_notes(self.m)

        note = list_of_notes[12]
        raw_content = test_data.note_contents_from_dbus[note.title]
        lines = raw_content.splitlines()
        lines[0] = "%s%s" % (
            lines[0],
            "  (system:notebook:reminders, training)"
        )
        expected_result = os.linesep.join(lines)

        tt.comm.GetNoteContents(note.uri)\
            .AndReturn( raw_content )

        self.m.ReplayAll()

        self.assertEqual( expected_result, tt.get_note_content(note) )

        self.m.VerifyAll()

    def test_perform_action(self):
        """Display: perform_action executes successfully."""
        dsp_ap = self.wrap_subject(display.DisplayAction, "perform_action")
        dsp_ap.tomboy_interface = self.m.CreateMock(core.Scout)

        fake_options = self.m.CreateMock(optparse.Values)
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)
        notes = [ self.m.CreateMock(core.TomboyNote) ]

        dsp_ap.tomboy_interface.get_notes(names=["addressbook"])\
            .AndReturn(notes)

        dsp_ap.format_display_for_notes(notes)\
            .AndReturn(
                test_data.note_contents_from_dbus["addressbook"].decode("utf-8")
            )

        self.m.ReplayAll()

        dsp_ap.perform_action(fake_config, fake_options, ["addressbook"])

        self.m.VerifyAll()

        self.assertEqual(
            test_data.note_contents_from_dbus["addressbook"] + os.linesep,
            sys.stdout.getvalue()
        )

    def test_perform_action_too_few_arguments(self):
        """Display: perform_action without any argument displays an error."""
        dsp_ap = self.wrap_subject(display.DisplayAction, "perform_action")

        fake_options = self.m.CreateMock(optparse.Values)
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        self.m.ReplayAll()
        self.assertRaises(
            SystemExit,
            dsp_ap.perform_action, fake_config, fake_options, []
        )
        self.m.VerifyAll()

        self.assertEqual(
            test_data.display_no_note_name_error + os.linesep,
            sys.stderr.getvalue()
        )

class TestDelete(bases.BasicMocking, bases.CLIMocking):
    """Tests for code that delete notes."""

    def verify_perform_action(self, tags, names, all_notes):
        """Test delete's entry point."""
        del_ap = self.wrap_subject(delete.DeleteAction, "perform_action")
        del_ap.tomboy_interface = self.m.CreateMock(core.Scout)

        fake_options = self.m.CreateMock(optparse.Values)
        fake_options.tags = tags
        fake_options.templates = True
        fake_options.dry_run = False
        fake_options.erase_all = all_notes

        fake_config = self.m.CreateMock(configparser.SafeConfigParser)
        notes = [ self.m.CreateMock(core.TomboyNote) ]

        if all_notes:
            del_ap.tomboy_interface.get_notes(
                names=[],
                tags=[],
                exclude_templates=False
            ).AndReturn(notes)

            del_ap.delete_notes(notes, False)
        elif names or tags:
            del_ap.tomboy_interface.get_notes(
                names=names,
                tags=tags,
                exclude_templates=False
            ).AndReturn(notes)

            del_ap.delete_notes(notes, False)

        self.m.ReplayAll()

        if all_notes or names or tags:
            del_ap.perform_action(fake_config, fake_options, names)
        else:
            self.assertRaises(
                SystemExit,
                del_ap.perform_action, fake_config, fake_options, names
            )

        self.m.VerifyAll()

        if not names and not tags and not all_notes:
            self.assertEqual(
                test_data.delete_no_argument_msg + os.linesep,
                sys.stdout.getvalue()
            )

    def test_perform_action(self):
        """Delete: perform_action executes successfully."""
        self.verify_perform_action(
            tags=["tag1", "tag2"],
            names=["note1"],
            all_notes=False
        )

    def test_perform_action_no_argument(self):
        """Delete: No filtering or note names given."""
        self.verify_perform_action( tags=[], names=[], all_notes=False )

    def test_perform_action_all_notes(self):
        """Delete: All notes requested for deletion."""
        self.verify_perform_action( tags=[], names=[], all_notes=True )

    def verify_delete_notes(self, dry_run):
        """Test note deletion."""
        del_ap = self.wrap_subject(delete.DeleteAction, "delete_notes")
        del_ap.tomboy_interface = self.m.CreateMock(core.Scout)
        del_ap.tomboy_interface.comm = self.m.CreateMockAnything()

        notes = [
            n for n in test_data.full_list_of_notes(self.m)
            if "system:notebook:pim" in n.tags
               or n.title == "TDD"
        ]

        if not dry_run:
            for note in notes:
                del_ap.tomboy_interface.comm.DeleteNote(note.uri)

        self.m.ReplayAll()

        del_ap.delete_notes(notes, dry_run=dry_run)

        self.m.VerifyAll()

        if dry_run:
            self.assertEqual(
                test_data.delete_dry_run_list + os.linesep,
                sys.stdout.getvalue()
            )

    def test_delete_notes(self):
        """Delete: Delete all notes found in a list."""
        self.verify_delete_notes(False)

    def test_delete_notes_dry_run(self):
        """Delete: Dry run for note deletion."""
        self.verify_delete_notes(True)

    def test_init_options(self):
        """Delete: Delete's options initialization."""
        del_ap = self.wrap_subject(delete.DeleteAction, "init_options")

        fake_filtering_group = self.m.CreateMock(plugins.FilteringGroup)

        self.m.StubOutWithMock(
            plugins,
            "FilteringGroup",
            use_mock_anything=True
        )
        self.m.StubOutWithMock(optparse, "Option", use_mock_anything=True)

        fake_option = self.m.CreateMock(optparse.Option)
        fake_option.help = "Help me out!"

        new_template_option = self.m.CreateMock(optparse.Option)
        new_all_notes_option = self.m.CreateMock(optparse.Option)

        del_ap.add_option(
            "--dry-run",
            dest="dry_run", action="store_true", default=False,
            help="Simulate the action. The notes that are selected for """
                """deletion will be printed out to the screen but no note """
                """will really be deleted."""
        )

        plugins.FilteringGroup("Delete")\
            .AndReturn(fake_filtering_group)

        fake_filtering_group.get_option("-b")\
            .AndReturn(fake_option)

        fake_filtering_group.remove_option("--with-templates")

        optparse.Option(
            "--spare-templates",
            dest="templates", action="store_false", default=True,
            help="""Do not delete template notes that get caught with a """
                """tag or book name."""
        ).AndReturn(new_template_option)

        optparse.Option(
            "--all-notes",
            dest="erase_all", action="store_true", default=False,
            help="""Delete all notes. Once this is done, there is no turning """
                """back. To make sure that it is doing what you want, you """
                """could use the --dry-run option first."""
        ).AndReturn(new_all_notes_option)

        fake_filtering_group.add_options([
            new_template_option,
            new_all_notes_option
        ])

        del_ap.add_option_library(fake_filtering_group)

        self.m.ReplayAll()

        del_ap.init_options()

        self.m.VerifyAll()

        self.assertEqual(
            test_data.book_help_delete,
            fake_option.help
        )

class TestSearch(bases.BasicMocking, bases.CLIMocking):
    """Tests for code that perform a textual search within notes."""
    def test_search_for_text(self):
        """Search: Scout triggers a search through requested notes."""
        srch_ap = self.wrap_subject(search.SearchAction, "search_for_text")
        srch_ap.tomboy_interface = self.m.CreateMock(core.Scout)

        note_contents = {}

        list_of_notes = test_data.full_list_of_notes(self.m)
        # Forget about the last note (a template)
        list_of_notes = list_of_notes[:-1]

        for note in list_of_notes:
            content = test_data.note_contents_from_dbus[note.title]

            if note.tags:
                lines = content.splitlines()
                lines[0] =  "%s  (%s)" % (lines[0], ", ".join(note.tags) )
                content = os.linesep.join(lines)

            note_contents[note.title] = content

        expected_result = test_data.search_structure

        for note in list_of_notes:
            srch_ap.tomboy_interface.get_note_content(note)\
                .AndReturn(note_contents[note.title])

        self.m.ReplayAll()

        self.assertEqual(
            expected_result,
            srch_ap.search_for_text("john doe", list_of_notes)
        )

        self.m.VerifyAll()

    def test_init_options(self):
        """Search: Search options are initialized correctly."""
        fake_filtering_group = self.m.CreateMock(plugins.FilteringGroup)

        srch_ap = self.wrap_subject(search.SearchAction, "init_options")
        self.m.StubOutWithMock(
            plugins,
            "FilteringGroup",
            use_mock_anything=True
        )

        plugins.FilteringGroup("Search")\
            .AndReturn(fake_filtering_group)

        srch_ap.add_option_library(fake_filtering_group)

        self.m.ReplayAll()

        srch_ap.init_options()

        self.m.VerifyAll()

    def verify_perform_action(self, with_templates):
        """Test output from SearchAction.perform_action.

        Arguments:
            with_templates -- boolean, whether or not to include templates.

        """
        pass
        srch_ap = self.wrap_subject(search.SearchAction, "perform_action")
        srch_ap.tomboy_interface = self.m.CreateMock(core.Scout)

        tags = ["something"]

        list_of_notes = test_data.full_list_of_notes(self.m)
        # Forget about the last note (a template)
        list_of_notes = list_of_notes[:-1]

        fake_options = self.m.CreateMock(optparse.Values)
        fake_options.tags = list(tags)
        fake_options.templates = with_templates
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        srch_ap.tomboy_interface.get_notes(
            names=["note1", "note2"],
            tags=["something"],
            exclude_templates=not with_templates
        ).AndReturn(list_of_notes)

        srch_ap.search_for_text("findme", list_of_notes)\
            .AndReturn(test_data.search_structure)

        self.m.ReplayAll()

        srch_ap.perform_action(
            fake_config,
            fake_options,
            ["findme", "note1", "note2"]
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.search_results + os.linesep,
            sys.stdout.getvalue()
        )

    def test_perform_action(self):
        """Search: perform_action without filters."""
        self.verify_perform_action(with_templates=False)

    def test_perform_action_templates(self):
        """Search: perform_action with templates included."""
        self.verify_perform_action(with_templates=True)

    def test_perform_action_too_few_arguments(self):
        """Search: perform_action, without any arguments."""
        srch_ap = self.wrap_subject(search.SearchAction, "perform_action")

        fake_options = self.m.CreateMock(optparse.Values)
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            srch_ap.perform_action, fake_config, fake_options, []
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.search_no_argument_error + os.linesep,
            sys.stderr.getvalue()
        )

class TestVersion(bases.BasicMocking, bases.CLIMocking):
    """Tests for code that show Tomboy's version."""
    def test_perform_action(self):
        """Version: perform_action prints out Tomboy's version."""
        vrsn_ap = self.wrap_subject(version.VersionAction, "perform_action")
        vrsn_ap.tomboy_interface = self.m.CreateMock(core.Scout)
        vrsn_ap.tomboy_interface.comm = self.m.CreateMockAnything()
        vrsn_ap.tomboy_interface.application = "some_app"

        fake_options = self.m.CreateMock(optparse.Values)
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        vrsn_ap.tomboy_interface.comm.Version()\
            .AndReturn("1.0.1")

        self.m.ReplayAll()

        vrsn_ap.perform_action(fake_config, fake_options, [])

        self.m.VerifyAll()

        self.assertEqual(
            test_data.tomboy_version_output % "some_app" + os.linesep,
            sys.stdout.getvalue()
        )

class TestPlugins(bases.BasicMocking):
    """Tests for the basis of plugins."""
    def test_ActionPlugin_constructor(self):
        """Plugins: ActionPlugin's constructor sets initial values."""
        action = self.wrap_subject(plugins.ActionPlugin, "__init__")

        action.add_group(None)

        self.m.ReplayAll()

        action.__init__()

        self.m.VerifyAll()

        # add_option has been mocked out: this list should still be empty
        self.assertEqual(
            [],
            action.option_groups
        )

    def test_add_option(self):
        """Plugins: ActionPlugin.add_option inserts an option in a group."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option")
        self.m.StubOutWithMock(optparse, "Option", use_mock_anything=True)

        fake_group = self.m.CreateMock(plugins.OptionGroup)
        fake_group.name = None

        ap.option_groups = [fake_group]

        fake_option = self.m.CreateMock(optparse.Option)

        optparse.Option("-e", type="int", dest="eeee", help="eeehhh")\
            .AndReturn(fake_option)

        fake_group.add_options( [fake_option] )

        self.m.ReplayAll()

        ap.add_option("-e", type="int", dest="eeee", help="eeehhh")

        self.m.VerifyAll()

    def test_add_option_unexistant_group(self):
        """Plugins: KeyError is raised if requested group does not exist."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option")

        fake_group = self.m.CreateMock(plugins.OptionGroup)
        fake_group.name = None

        ap.option_groups = [fake_group]

        self.m.ReplayAll()

        self.assertRaises(
            KeyError,
            ap.add_option, "-s", group="group1", dest="sss"
        )

        self.m.VerifyAll()

    def test_add_group(self):
        """Plugins: A scout.plugins.OptionGroup object is inserted."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_group")
        self.m.StubOutWithMock(plugins, "OptionGroup", use_mock_anything=True)

        ap.option_groups = []

        fake_opt_group = self.m.CreateMock(plugins.OptionGroup)

        plugins.OptionGroup("group1", "describe group1")\
            .AndReturn(fake_opt_group)

        self.m.ReplayAll()

        ap.add_group("group1", "describe group1")

        self.m.VerifyAll()

        self.assertEqual(
            [fake_opt_group],
            ap.option_groups
        )

    def test_add_group_already_exists(self):
        """Plugins: Group added to a plugin already exists."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_group")

        fake_opt_group = self.m.CreateMock(plugins.OptionGroup)
        fake_opt_group.name = "group1"

        ap.option_groups = [fake_opt_group]

        self.m.ReplayAll()

        ap.add_group("group1", "describe group1")

        self.m.VerifyAll()

        self.assertEqual(
            [fake_opt_group],
            ap.option_groups
        )

    def test_add_option_library(self):
        """Plugins: Option library is inserted in an action's groups."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option_library")

        ap.option_groups = []

        group = self.m.CreateMock(plugins.OptionGroup)
        group.name = "some_group"

        self.m.ReplayAll()

        ap.add_option_library(group)

        self.m.VerifyAll()

        self.assertEqual(
            [group],
            ap.option_groups
        )

    def test_option_library_already_inserted(self):
        """Plugins: Group name of option library is already present."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option_library")

        group = self.m.CreateMock(plugins.OptionGroup)
        group.name = "some_group"

        ap.option_groups = [group]

        self.m.ReplayAll()

        ap.add_option_library(group)

        self.m.VerifyAll()

        self.assertEqual(
            [group],
            ap.option_groups
        )

    def test_option_library_TypeError(self):
        """Plugins: Option library is not a scout.plugins.OptionGroup."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option_library")

        wrong_object = self.m.CreateMock(optparse.OptionGroup)

        self.m.ReplayAll()

        self.assertRaises(
            TypeError,
            ap.add_option_library, wrong_object
        )

        self.m.VerifyAll()

    def verify_method_does_nothing(self, cls, method_name, *args, **kwargs):
        """Simple test to verify that a method does nothing.

        Arguments:
            cls -- object class that contains the method
            method_name -- string, name of the method to stub out
            *args -- passed on to verified method
            **kwargs -- passed on to verified method

        """
        obj = self.wrap_subject(cls, method_name)
        func = getattr(obj, method_name)

        self.m.ReplayAll()

        self.assertEqual(
            None,
            func(*args, **kwargs)
        )

        self.m.VerifyAll()

    def test_init_options(self):
        """Plugins: Default init_options does nothing."""
        self.verify_method_does_nothing(plugins.ActionPlugin, "init_options")

    def test_perform_action(self):
        """Plugins: Default perform_action does nothing."""
        self.verify_method_does_nothing(
            plugins.ActionPlugin,
            "perform_action",
            self.m.CreateMockAnything(),
            self.m.CreateMockAnything(),
            self.m.CreateMockAnything()
        )

    def test_OptionGroup_constructor(self):
        """Plugins: OptionGroup's constructor sets default values."""
        group = self.wrap_subject(plugins.OptionGroup, "__init__")

        self.m.ReplayAll()

        group.__init__("some_group", "description")

        self.m.VerifyAll()

        self.assertEqual(
            "some_group",
            group.name
        )
        self.assertEqual(
            "description",
            group.description
        )
        self.assertEqual(
            [],
            group.options
        )

    def test_group_add_options(self):
        """Plugins: A group of options are added to an OptionGroup."""
        group = self.wrap_subject(plugins.OptionGroup, "add_options")

        some_option = self.m.CreateMock(optparse.Option)
        group.options = [some_option]

        option_list = [
            self.m.CreateMock(optparse.Option),
            self.m.CreateMock(optparse.Option)
        ]

        self.m.ReplayAll()

        group.add_options(option_list)

        self.m.VerifyAll()

        self.assertEqual(
            [some_option] + option_list,
            group.options
        )

    def test_group_add_options_TypeError(self):
        """Plugins: Not all options added are optparse.Option objects."""
        group = self.wrap_subject(plugins.OptionGroup, "add_options")

        group.options = []

        option_list = [
            self.m.CreateMock(optparse.Option),
            self.m.CreateMock(dict)
        ]

        self.m.ReplayAll()

        self.assertRaises(
            TypeError,
            group.add_options, option_list
        )

        self.m.VerifyAll()

    def test_FilteringGroup_initialization(self):
        """Plugins: A new FilteringGroup contains all of its options."""
        filter_group = self.wrap_subject(plugins.FilteringGroup, "__init__")
        book_callback = filter_group.book_callback

        self.m.StubOutWithMock(optparse, "Option", use_mock_anything=True)
        self.m.StubOutWithMock(plugins.OptionGroup, "__init__")

        plugins.OptionGroup.__init__(
            "Filtering",
            "Filter notes by different criteria."
        )

        option_list = [
            self.m.CreateMock(optparse.Option),
            self.m.CreateMock(optparse.Option),
            self.m.CreateMock(optparse.Option),
        ]

        optparse.Option(
            "-b", action="callback", dest="books", metavar="BOOK",
            callback=book_callback, type="string",
            help="""Murder notes belonging to """ + \
            """specified notebooks. It is a shortcut to option "-t" to """
            """specify notebooks more easily. For example, use"""
            """ "-b HGTTG" instead of "-t system:notebook:HGTTG". Use """
            """this option once for each desired book."""
        ).AndReturn( option_list[0] )

        optparse.Option(
            "-t",
            dest="tags", action="append", default=[], metavar="TAG",
            help="""Murder notes with """ + \
            """specified tags. Use this option once for each desired """
            """tag. This option selects raw tags and could be useful for """
            """user-assigned tags."""
        ).AndReturn( option_list[2] )

        optparse.Option(
            "--with-templates",
            dest="templates", action="store_true", default=False,
            help="""Include template notes. This option is """
            """different from using "-t system:template" in that the """
            """latter used alone will only include the templates, while """
            """"using "--with-templates" without specifying tags for """
            """selection will include all notes and templates."""
        ).AndReturn( option_list[1] )

        filter_group.add_options(option_list)

        self.m.ReplayAll()

        filter_group.__init__("Murder")

        self.m.VerifyAll()

    def test_book_callback(self):
        """Plugins: callback for book option adds an entry in tags."""
        filter_group = self.wrap_subject(
            plugins.FilteringGroup,
            "book_callback"
        )

        fake_option = self.m.CreateMock(optparse.Option)
        fake_parser = self.m.CreateMock(optparse.OptionParser)
        fake_parser.values = self.m.CreateMock(optparse.Values)
        fake_parser.values.tags = ["already_here"]

        self.m.ReplayAll()

        filter_group.book_callback(fake_option, "-b", "book1", fake_parser)

        self.m.VerifyAll()

        self.assertEqual(
            ["already_here", "system:notebook:book1"],
            fake_parser.values.tags
        )

    def verify_remove_option(self, option_found):
        """Test option removal from a group."""
        og = self.wrap_subject(plugins.OptionGroup, "remove_option")

        fake_option1 = self.m.CreateMock(optparse.Option)
        fake_option2 = self.m.CreateMock(optparse.Option)

        og.options = [fake_option1, fake_option2]

        if option_found:
            expected_list = [fake_option1]
            og.get_option("--some-option")\
                .AndReturn(fake_option2)
        else:
            expected_list = [fake_option1, fake_option2]
            og.get_option("--some-option")\
                .AndReturn(None)

        self.m.ReplayAll()

        og.remove_option("--some-option")

        self.m.VerifyAll()

        self.assertEqual(
            expected_list,
            og.options
        )

    def test_remove_option(self):
        """Plugins: Remove an option from an option group."""
        self.verify_remove_option(True)

    def test_remove_option_not_found(self):
        """Plugins: Remove an option from an option group."""
        self.verify_remove_option(False)

    def verify_get_option(self, found):
        """Test option retrieval from a group."""
        og = self.wrap_subject(plugins.OptionGroup, "get_option")

        fake_option1 = self.m.CreateMock(optparse.Option)
        fake_option1._short_opts = ["-a"]
        fake_option1._long_opts = []
        fake_option2 = self.m.CreateMock(optparse.Option)
        fake_option2._short_opts = []
        if found:
            fake_option2._long_opts = ["--some-option", "--useless-string"]
        else:
            fake_option2._long_opts = ["--useless-string"]

        og.options = [fake_option1, fake_option2]

        if found:
            expected_result = fake_option2
        else:
            expected_result = None

        self.m.ReplayAll()

        self.assertEqual(
            expected_result,
            og.get_option("--some-option")
        )

        self.m.VerifyAll()

    def test_get_option(self):
        """Plugins: Get an option by its option strings."""
        self.verify_get_option(True)

    def test_get_option_not_found(self):
        """Plugins: Requested option is not found."""
        self.verify_get_option(False)
