# -*- coding: utf-8 -*-
"""Unit tests."""
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
from scout.version import SCOUT_VERSION
# Import the list action under a different name to avoid overwriting the list()
# builtin function.
from scout.actions import display, list as list_, delete, search, version

from .utils import BasicMocking, CLIMocking, data


class MainTests(BasicMocking, CLIMocking):
    """Tests for functions in the main script."""

    def test_arguments_converted_to_unicode(self):
        """U Main: Arguments to action are converted to unicode objects."""
        # This is the default main() behaviour.
        self.m.StubOutWithMock(cli.CommandLine, "dispatch")

        arguments = ["arg1", "arg2"]
        sys.argv = ["app_name", "action"] + arguments

        cli.CommandLine.dispatch("action", [unicode(arg) for arg in arguments])

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

    def verify_exit_from_main(self, arguments, expected_text, output_stream):
        sys.argv = ["app_name"] + arguments

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEqual(
            expected_text,
            output_stream.getvalue()
        )

    def test_not_enough_arguments(self):
        """U Main: main() called with too few arguments gives an error."""
        self.verify_exit_from_main(
            [],
            data("too_few_arguments_error"),
            output_stream=sys.stderr
        )

    def verify_main_help(self, argument):
        """Test that help exits and displays the main help."""
        self.m.StubOutWithMock(cli.CommandLine, "action_short_summaries")
        m_desc = data("module_descriptions")
        sys.argv = ["app_name", argument]

        cli.CommandLine.action_short_summaries()\
                .AndReturn(m_desc.splitlines())

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEqual(
            ''.join([data("main_help"), m_desc]),
            sys.stdout.getvalue()
        )

    def test_main_help(self):
        """U Main: using only -h prints help and list of actions."""
        self.verify_main_help("-h")

    def test_main_help_from_help_pseudo_action(self):
        """U Main: "help" pseudo-action alone should display main help."""
        self.verify_main_help("help")

    def verify_help_argument_reversing(self, argument):
        """Test reversal of arguments and conversion of "help" to "-h"."""
        self.m.StubOutWithMock(cli.CommandLine, "dispatch")
        sys.argv = ["app_name", argument, "action"]
        processed_arguments = [ sys.argv[0], sys.argv[2], "-h" ]

        cli.CommandLine.dispatch(
            "action",
            [unicode(arg) for arg in processed_arguments[1:] ]
        )

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

    def test_help_before_action(self):
        """U Main: -h before action gets switched to normal help call."""
        self.verify_help_argument_reversing("-h")

    def test_help_pseudo_action_before_action(self):
        """U Main: "help" pseudo-action displays details about an action."""
        self.verify_help_argument_reversing("help")

    def test_display_scout_version(self):
        """U Main: -v option displays Scout's version and license info."""
        self.verify_exit_from_main(
            ["-v"],
            data("version_and_license_info") % SCOUT_VERSION,
            output_stream=sys.stdout
        )

    def test_list_of_actions(self):
        """U Main: list_of_actions returns classes of action plugins."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "list_of_actions"
        )
        self.m.StubOutWithMock(pkg_resources, "iter_entry_points")

        entry_points = self.n_mocks(4, pkg_resources.EntryPoint)
        for (index, entry_point) in enumerate(entry_points):
            entry_point.name = "action%d" % index

        plugin_classes = [
            plugins.ActionPlugin,
            plugins.ActionPlugin,
            plugins.ActionPlugin,
            # The last one on the list is not a subclass of ActionPlugin and
            # should get silently discarded
            core.Scout,
        ]

        pkg_resources.iter_entry_points(group="scout.actions")\
            .AndReturn(entry_points)

        for (index, entry_point) in enumerate(entry_points):
            entry_point.load()\
                .AndReturn(plugin_classes[index])

        self.m.ReplayAll()
        self.assertEqual(
            plugin_classes[:-1],
            command_line.list_of_actions()
        )
        self.m.VerifyAll()

    def test_load_action(self):
        """U Main: Initialize an action plugin instance."""
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
            .AndReturn([action1, action2])

        action2()\
            .AndReturn(mock_class)

        self.m.ReplayAll()

        self.assertEqual(
            mock_class,
            command_line.load_action("action2")
        )

        self.m.VerifyAll()

    def test_load_unknown_action(self):
        """U Main: Requested action name is invalid."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "load_action"
        )

        self.m.StubOutWithMock(os.path, "basename")

        sys.argv = ["app_name"]

        command_line.list_of_actions()\
            .AndReturn([])

        os.path.basename("app_name")\
            .AndReturn("app_name")

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            command_line.load_action, "unexistant_action"
        )

        self.assertEqual(
            data("unknown_action"),
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_action_short_summaries(self):
        """U Main: Extract short summaries from action plugins."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "action_short_summaries"
        )

        action1 = self.m.CreateMockAnything()
        action1.name = "action1"
        action1.short_description = data("module1_description")[:-1]
        action2 = self.m.CreateMockAnything()
        action2.name = "otheraction"
        action2.short_description = None

        command_line.list_of_actions()\
            .AndReturn([action1, action2])

        self.m.ReplayAll()

        self.assertEqual(
            data("module_descriptions").splitlines(),
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
            .AndReturn(fake_config)

        command_line.parse_options(fake_action, arguments)\
            .AndReturn((options, positional_arguments))

        command_line.determine_connection_app(fake_config, options)\
            .AndReturn(app_name)

        if exception_class in [core.ConnectionError, core.AutoDetectionError]:
            core.Scout(app_name)\
                .AndRaise(exception_class(exception_argument))
            return (command_line, action_name, fake_action, arguments)
        else:
            core.Scout(app_name)\
                .AndReturn(fake_scout)

        if exception_class:
            fake_action.perform_action(
                fake_config,
                options,
                positional_arguments
            ).AndRaise(exception_class(exception_argument))
        else:
            fake_action.perform_action(
                fake_config,
                options,
                positional_arguments
            ).AndReturn(None)

        return (command_line, action_name, fake_action, arguments)

    def test_dispatch(self):
        """U Main: Action calls are dispatched to the right action."""
        command_line, action_name, fake_action, arguments = \
            self.mock_out_dispatch(None, None)

        self.m.ReplayAll()

        command_line.dispatch(action_name, arguments)

        self.m.VerifyAll()

    def test_dispatch_with_gnote(self):
        """U Main: Dispatch instantiates Scout for Gnote."""
        command_line, action_name, fake_action, arguments = \
            self.mock_out_dispatch(None, None, "Gnote")

        self.m.ReplayAll()

        command_line.dispatch(action_name, arguments)

        self.m.VerifyAll()

    def verify_dispatch_exception(self, exception_class, exception_out=None,
                                  exception_argument="", expected_text=""):
        """Verify that dispatch() lets a specific exception go through.

        dispatch() should let some exceptions stay unhandled. They are handled
        on a higher level so that their processing stays the most global
        possible. The rest of the exceptions coming from the action call
        should be handled.

        When not None, 'exception_out' is the expected exception to come out of
        display(). This should be used when it is different than
        'exception_class'.

        'expected_text' is supposed to show up on stderr. When None, no text is
        expected.

        'exception_argument' can be passed to the exception constructor.

        """
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
        """U Main: SystemExit exceptions pass through dispatch."""
        self.verify_dispatch_exception(SystemExit)

    def test_dispatch_KeyboardInterrupt_goes_through(self):
        """U Main: KeyboardInterrupt exceptions pass through dispatch."""
        self.verify_dispatch_exception(KeyboardInterrupt)

    def test_dispatch_handles_ConnectionError(self):
        """U Main: ConnectionError should print an error message."""
        sys.argv = ["app_name"]
        self.verify_dispatch_exception(
            core.ConnectionError,
            exception_out=SystemExit,
            exception_argument="there was a problem",
            expected_text=data("connection_error_message")
        )

    def test_dispatch_handles_NoteNotFound(self):
        """U Main: NoteNotFound exceptions dont't go unhandled."""
        sys.argv = ["app_name"]
        self.verify_dispatch_exception(
            core.NoteNotFound,
            exception_out=SystemExit,
            exception_argument="unexistant",
            expected_text=data("unexistant_note_error")
        )

    def test_dispatch_handles_AutoDetectionError(self):
        """U Main: No sensible application choice was identified."""
        sys.argv = ["app_name"]
        self.verify_dispatch_exception(
            core.AutoDetectionError,
            exception_out=SystemExit,
            exception_argument="autodetection failed for some reason",
            expected_text=data("autodetection_error")
        )

    def print_traceback(self):
        """Fake an output of an arbitrary traceback on sys.stderr"""
        print >> sys.stderr, data("fake_traceback")

    def test_dispatch_handles_action_exceptions(self):
        """U Main: All unknown exceptions from actions are handled."""
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
        """U Main: dispatch prints an error if an option is the wrong type."""
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
            .AndRaise(TypeError(data("option_type_error_message")[:-1]))

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            command_line.dispatch, action_name, arguments
        )

        self.m.VerifyAll()

        self.assertEqual(
            data("option_type_error_message"),
            sys.stderr.getvalue()
        )

    def test_parse_options(self):
        """U Main: Parse an action's options and return them"""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "parse_options"
        )

        option_parser = self.m.CreateMock(optparse.OptionParser)
        self.m.StubOutWithMock(optparse, "OptionParser", use_mock_anything=True)
        fake_action = self.m.CreateMock(plugins.ActionPlugin)
        fake_action.usage = "%prog [options]"
        option_list = self.n_mocks(2, optparse.Option) + [
            self.m.CreateMock(optparse.OptionGroup),
        ]
        fake_values = self.m.CreateMock(optparse.Values)

        arguments = ["--meuh", "arg1"]
        positional_arguments = ["arg1"]

        command_line.retrieve_options(option_parser, fake_action)\
            .AndReturn(option_list)

        optparse.OptionParser(usage="%prog [options]")\
            .AndReturn(option_parser)

        fake_action.init_options()

        option_parser.add_option(option_list[0])
        option_parser.add_option(option_list[1])
        option_parser.add_option_group(option_list[2])

        option_parser.parse_args(arguments)\
            .AndReturn((fake_values, positional_arguments))

        self.m.ReplayAll()

        result = command_line.parse_options(fake_action, arguments)

        self.m.VerifyAll()

        self.assertEqual(
            (fake_values, positional_arguments),
            result
        )

    def test_retrieve_options(self):
        """U Main: Get a list of options from an action plugin."""
        command_line = self.wrap_subject(
            cli.CommandLine,
            "retrieve_options"
        )
        command_line.default_options = []

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

    def test_determine_connection_app_cli_argument(self):
        """U Main: Application specified on command line."""
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
        """U Main: No user choice of application."""
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
        """U Main: No user choice of application."""
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

    def verify_get_config(self, section_present):
        """Test config retrieval and sanitization."""
        command_line = self.wrap_subject(cli.CommandLine, "get_config")
        command_line.core_config_section = 'scout'
        command_line.core_options = ["option1", "bobby-tables"]

        fake_parser = self.m.CreateMock(configparser.SafeConfigParser)
        self.m.StubOutWithMock(
            configparser,
            "SafeConfigParser",
            use_mock_anything=True
        )

        self.m.StubOutWithMock(os.path, "expanduser")

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

        fake_parser.has_section('scout')\
            .AndReturn(section_present)
        if not section_present:
            fake_parser.add_section('scout')
        fake_parser.options('scout')\
            .AndReturn(["option1", "unwanted", "bobby-tables"])

        fake_parser.remove_option('scout', "unwanted")

        self.m.ReplayAll()

        self.assertEqual(
            fake_parser,
            command_line.get_config()
        )

        self.m.VerifyAll()

    def test_get_config(self):
        """U Main: Retrieve configuration values from a file."""
        self.verify_get_config(True)

    def test_get_config_core_section_empty(self):
        """U Main: Retrieve config, core section is emtpy."""
        self.verify_get_config(False)


class CoreTests(BasicMocking):
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
                .AndReturn(tuple(["Tomboy", dbus_object]))
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
        """U Core: Scout's dbus interface is initialized."""
        self.verify_Scout_constructor("the_application")

    def test_Scout_constructor_with_autodetection(self):
        """U Core: Scout's dbus interface is autodetected and initialized."""
        self.verify_Scout_constructor(None)

    def test_Scout_constructor_application_fails(self):
        """U Core: Scout's dbus interface is unavailable."""
        self.verify_Scout_constructor("fail_app")

    def test_dbus_Tomboy_communication_problem(self):
        """U Core: Raise an exception if linking dbus with Tomboy failed."""
        tt = self.wrap_subject(core.Scout, "__init__")

        session_bus = self.m.CreateMock(dbus.SessionBus)

        self.m.StubOutWithMock(dbus, "SessionBus", use_mock_anything=True)

        dbus.SessionBus()\
            .AndRaise(dbus.DBusException("cosmos error"))

        self.m.ReplayAll()

        self.assertRaises(core.ConnectionError, tt.__init__, "Tomboy")

        self.m.VerifyAll()

    def verify_Note_constructor(self, **kwargs):
        """Test Note.__init__() and return the mock Note object."""
        tn = self.wrap_subject(core.Note, "__init__")

        self.m.ReplayAll()

        tn.__init__(**kwargs)

        self.m.VerifyAll()

        return tn

    def test_Note_constructor_all_args_int64(self):
        """U Core: Note initializes its instance variables. case 1."""
        uri1 = "note://something-like-this"
        title = "Name"
        date_int64 = dbus.Int64()
        tags = ["tag1", "tag2"]

        # case 1: Construct with all data and a dbus.Int64 date
        tn = self.verify_Note_constructor(
            uri=uri1,
            title=title,
            date=date_int64,
            tags=tags
        )

        self.assertEqual(uri1, tn.uri)
        self.assertEqual(title, tn.title)
        self.assertEqual(date_int64, tn.date)
        # Order is not important
        self.assertEqual(set(tags), set(tn.tags))

    def test_Note_constructor_all_defaults(self):
        """U Core: Note initializes its instance variables. case 2."""
        uri2 = "note://another-false-uri"

        tn = self.verify_Note_constructor(uri=uri2)

        # case 2: Construct with only uri, rest is default
        self.assertEqual(tn.uri, uri2)
        self.assertEqual(tn.title, "")
        self.assertEqual(tn.date, dbus.Int64())
        self.assertEqual(tn.tags, [])

    def test_Note_constructor_datetetime(self):
        """U Core: Note initializes its instance variables. case 3."""
        datetime_date = datetime.datetime(2009, 11, 13, 18, 42, 23)

        # case 3: the date can be entered with a datetime.datetime
        tn = self.verify_Note_constructor(
            uri="not important",
            date=datetime_date
        )

        self.assertEqual(
            dbus.Int64(
                time.mktime(datetime_date.timetuple())
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

        notes = self.full_list_of_notes()

        fake_filtered_list = self.n_mocks(5)

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
        """U Core: No filtering but templates removed."""
        self.verify_get_notes()

    def test_get_notes_number_limited(self):
        """U Core: No filtering but templates removed."""
        list_of_notes = self.verify_get_notes(count=3)

        self.assertEqual(
            3,
            len(list_of_notes)
        )

    def test_get_notes_with_templates(self):
        """U Core: Filtered notes but templates included."""
        self.verify_get_notes(
            tags=["sometag", "othertag"],
            names=["note1", "note2"],
            exclude=False
        )

    def test_get_notes_template_as_a_tag(self):
        """U Core: Specifying templates as a tag should include them."""
        self.verify_get_notes(tags=["system:template", "someothertag"])

    def verify_filter_notes(self, tags, names, exclude=True):
        """Test note filtering."""
        tt = self.wrap_subject(core.Scout, "filter_notes")

        notes = self.full_list_of_notes()

        if tags or names:
            expected_list = [
                n for n in notes
                if set(n.tags).intersection(set(tags))
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
        """U Core: Note filtering."""
        self.verify_filter_notes(
            tags=["system:notebook:projects"],
            names=["addressbook"]
        )

    def test_fiter_notes_with_templates(self):
        """U Core: Do not exclude templates."""
        self.verify_filter_notes(
            tags=["system:notebook:projects"],
            names=["addressbook"],
            exclude=False
        )

    def test_filter_notes_no_filtering(self):
        """U Core: No filtering gives the full list of notes."""
        self.verify_filter_notes(
            tags=[],
            names=[],
            exclude=False
        )

    def test_filter_notes_unknown_note(self):
        """U Core: Filtering encounters an unknown note name."""
        tt = self.wrap_subject(core.Scout, "filter_notes")

        notes = self.full_list_of_notes()

        self.m.ReplayAll()

        self.assertRaises(
            core.NoteNotFound,
            tt.filter_notes, notes, tags=[], names=["unknown"]
        )

        self.m.VerifyAll()

    def verify_note_list(self, tt, notes, note_names=[]):
        """Verify the outcome of Scout.build_note_list().

        Notes are unhashable so we need to convert them to dictionaries
        and check for list membership to be able to compare them.

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
                    ''.join([
                        "Note named %s dated %s " % (note.title, note.date),
                        "with uri %s and " % (note.uri, ),
                        "tags [%s] not found in " % (",".join(note.tags), ),
                        "expectation: [%s]" % (",".join(expectation), )
                    ])
                )

    def test_build_note_list(self):
        """U Core: Scout gets a full list of notes."""
        tt = self.wrap_subject(core.Scout, "build_note_list")

        tt.comm = self.m.CreateMockAnything()

        list_of_notes = self.full_list_of_notes()

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
        """Test DBus autodetection of the application to use."""
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
        """U Core: Autodetect, only one application is running."""
        self.verify_autodetect_app(["Tomboy"])

    def test_autodetect_app_none(self):
        """U Core: Autodetection fails to find any application."""
        self.verify_autodetect_app([])

    def test_autodetect_app_too_much(self):
        """U Core: Autodetection fails to find any application."""
        self.verify_autodetect_app(["Tomboy", "Gnote"])


class PluginsTests(BasicMocking):
    """Tests for the basis of plugins."""

    def test_ActionPlugin_constructor(self):
        """U Plugins: ActionPlugin's constructor sets initial values."""
        action = self.wrap_subject(plugins.ActionPlugin, "__init__")
        action.add_group(None)

        self.m.ReplayAll()
        action.__init__()
        self.m.VerifyAll()

        # add_option has been mocked out: this list should still be empty
        self.assertEqual([], action.option_groups)

    def test_add_option(self):
        """U Plugins: ActionPlugin.add_option() inserts an option in a group."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option")
        self.m.StubOutWithMock(optparse, "Option", use_mock_anything=True)

        fake_group = self.m.CreateMock(plugins.OptionGroup)
        fake_group.name = None
        ap.option_groups = [fake_group]

        fake_option = self.m.CreateMock(optparse.Option)

        optparse.Option("-e", type="int", dest="eeee", help="eeehhh")\
            .AndReturn(fake_option)
        fake_group.add_options([fake_option])

        self.m.ReplayAll()
        ap.add_option("-e", type="int", dest="eeee", help="eeehhh")
        self.m.VerifyAll()

    def test_add_option_unexistant_group(self):
        """U Plugins: KeyError is raised if requested group does not exist."""
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
        """U Plugins: A scout.plugins.OptionGroup object is inserted."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_group")
        self.m.StubOutWithMock(plugins, "OptionGroup", use_mock_anything=True)
        ap.option_groups = []
        fake_opt_group = self.m.CreateMock(plugins.OptionGroup)

        plugins.OptionGroup("group1", "describe group1")\
            .AndReturn(fake_opt_group)

        self.m.ReplayAll()
        ap.add_group("group1", "describe group1")
        self.m.VerifyAll()

        self.assertEqual([fake_opt_group], ap.option_groups)

    def test_add_group_already_exists(self):
        """U Plugins: Group added to a plugin already exists."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_group")
        fake_opt_group = self.m.CreateMock(plugins.OptionGroup)
        fake_opt_group.name = "group1"
        ap.option_groups = [fake_opt_group]

        self.m.ReplayAll()
        ap.add_group("group1", "describe group1")
        self.m.VerifyAll()

        self.assertEqual([fake_opt_group], ap.option_groups)

    def test_add_option_library(self):
        """U Plugins: Option library is inserted in an action's groups."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option_library")
        ap.option_groups = []
        group = self.m.CreateMock(plugins.OptionGroup)
        group.name = "some_group"

        self.m.ReplayAll()
        ap.add_option_library(group)
        self.m.VerifyAll()

        self.assertEqual([group], ap.option_groups)

    def test_option_library_already_inserted(self):
        """U Plugins: Group name of option library is already present."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option_library")
        group = self.m.CreateMock(plugins.OptionGroup)
        group.name = "some_group"
        ap.option_groups = [group]

        self.m.ReplayAll()
        ap.add_option_library(group)
        self.m.VerifyAll()

        self.assertEqual([group], ap.option_groups)

    def test_option_library_TypeError(self):
        """U Plugins: Option library is not a scout.plugins.OptionGroup."""
        ap = self.wrap_subject(plugins.ActionPlugin, "add_option_library")
        wrong_object = self.m.CreateMock(optparse.OptionGroup)

        self.m.ReplayAll()
        self.assertRaises(
            TypeError,
            ap.add_option_library, wrong_object
        )
        self.m.VerifyAll()

    def verify_method_does_nothing(self, cls, method_name, *args, **kwargs):
        """Verify that 'cls's 'method_name' does nothing with arguments."""
        obj = self.wrap_subject(cls, method_name)
        func = getattr(obj, method_name)

        self.m.ReplayAll()
        self.assertEqual(None, func(*args, **kwargs))
        self.m.VerifyAll()

    def test_init_options(self):
        """U Plugins: Default init_options does nothing."""
        self.verify_method_does_nothing(plugins.ActionPlugin, "init_options")

    def test_perform_action(self):
        """U Plugins: Default perform_action does nothing."""
        args = self.n_mocks(3)
        self.verify_method_does_nothing(plugins.ActionPlugin, "perform_action",
                                        *args)

    def test_OptionGroup_constructor(self):
        """U Plugins: OptionGroup's constructor sets default values."""
        group = self.wrap_subject(plugins.OptionGroup, "__init__")

        self.m.ReplayAll()
        group.__init__("some_group", "description")
        self.m.VerifyAll()

        self.assertEqual("some_group", group.name)
        self.assertEqual("description", group.description)
        self.assertEqual([], group.options)

    def test_group_add_options(self):
        """U Plugins: A group of options are added to an OptionGroup."""
        group = self.wrap_subject(plugins.OptionGroup, "add_options")
        some_option = self.m.CreateMock(optparse.Option)
        group.options = [some_option]

        option_list = self.n_mocks(2, optparse.Option)

        self.m.ReplayAll()
        group.add_options(option_list)
        self.m.VerifyAll()

        self.assertEqual([some_option] + option_list, group.options)

    def test_group_add_options_TypeError(self):
        """U Plugins: Not all options added are optparse.Option objects."""
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
        """U Plugins: A new FilteringGroup contains all of its options."""
        filter_group = self.wrap_subject(plugins.FilteringGroup, "__init__")
        book_callback = filter_group.book_callback

        self.m.StubOutWithMock(optparse, "Option", use_mock_anything=True)
        self.m.StubOutWithMock(plugins.OptionGroup, "__init__")

        option_list = self.n_mocks(3, optparse.Option)

        plugins.OptionGroup.__init__(
            "Filtering",
            "Filter notes by different criteria."
        )

        optparse.Option(
            "-b", action="callback", dest="books", metavar="BOOK",
            callback=book_callback, type="string",
            help=''.join(["Murder notes belonging to specified notebooks. It ",
                          "is a shortcut to option \"-t\" to specify ",
                          "notebooks more easily. For example, use ",
                          "\"-b HGTTG\" instead of ",
                          "\"-t system:notebook:HGTTG\". Use this option once ",
                          "for each desired book."])
        ).AndReturn(option_list[0])

        optparse.Option(
            "-t",
            dest="tags", action="append", default=[], metavar="TAG",
            help=''.join(["Murder notes with specified tags. Use this option ",
                          "once for each desired tag. This option selects raw ",
                          "tags and could be useful for user-assigned tags."])
        ).AndReturn(option_list[1])

        optparse.Option(
            "--with-templates",
            dest="templates", action="store_true", default=False,
            help=''.join(["Include template notes. This option is different ",
                          "from using \"-t system:template\" in that the ",
                          "latter used alone will only include the ",
                          "templates, while using \"--with-templates\" ",
                          "without specifying tags for selection will include ",
                          "all notes and templates."])
        ).AndReturn(option_list[2])

        filter_group.add_options(option_list)

        self.m.ReplayAll()
        filter_group.__init__("Murder")
        self.m.VerifyAll()

    def test_book_callback(self):
        """U Plugins: callback for book option adds an entry in tags."""
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
        """U Plugins: Remove an option from an option group."""
        self.verify_remove_option(True)

    def test_remove_option_not_found(self):
        """U Plugins: Remove an option from an option group."""
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
        """U Plugins: Get an option by its option strings."""
        self.verify_get_option(True)

    def test_get_option_not_found(self):
        """U Plugins: Requested option is not found."""
        self.verify_get_option(False)


class ListTests(BasicMocking, CLIMocking):
    """Tests for the list action."""

    def verify_note_listing(self, title, tags, new_title, expected_tag_text):
        """Test Note's string representation."""
        note = self.wrap_subject(core.Note, "__repr__")

        date_64 = dbus.Int64(1254553804L)

        note.title = title
        note.date = date_64
        note.tags = tags

        expected_listing = "2009-10-03 | %(title)s%(tags)s" % {
            "title": new_title,
            "tags": expected_tag_text
        }

        self.m.ReplayAll()
        self.assertEqual(expected_listing, note.__repr__())
        self.m.VerifyAll()

    def test_Note_listing(self):
        """U List: Print one note's information."""
        self.verify_note_listing(
            "Test",
            ["tag1", "tag2"],
            "Test",
            "  (tag1, tag2)"
        )

    def test_Note_listing_no_title_no_tags(self):
        """U List: Verify listing format with no title and no tags."""
        self.verify_note_listing(
            "",
            [],
            "_note doesn't have a name_",
            ""
        )

    def test_init_options(self):
        """U List: options are initialized correctly."""
        lst_ap = self.wrap_subject(list_.ListAction, "init_options")
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
        """Verify execution of ListAction.perform_action()"""
        lst_ap = self.wrap_subject(list_.ListAction, "perform_action")
        lst_ap.interface = self.m.CreateMock(core.Scout)

        tags = ["whatever"]

        fake_options = self.m.CreateMock(optparse.Values)
        # Duplicate the list to avoid modification by later for loop
        fake_options.tags = list(tags)
        fake_options.templates = with_templates
        fake_options.max_notes = 5  # the value doesn't really matter here
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        list_of_notes = self.full_list_of_notes(real=True)
        if not with_templates:
            # Forget about the last note (a template)
            list_of_notes = list_of_notes[:-1]

        lst_ap.interface.get_notes(
            count_limit=5,
            tags=tags,
            exclude_templates=not with_templates
        ).AndReturn(list_of_notes)

        self.m.ReplayAll()
        lst_ap.perform_action(fake_config, fake_options, [])
        self.m.VerifyAll()

        expected_result = ''.join([data("expected_list"),
                                   data("list_appendix")])
        if with_templates:
            expected_result = ''.join([expected_result,
                                       data("normally_hidden_template")])

        self.assertEqual(
            expected_result,
            sys.stdout.getvalue()
        )

    def test_perform_action(self):
        """U List: perform_action called without arguments."""
        self.verify_perform_action(with_templates=False)

    def test_perform_action_templates(self):
        """U List: perform_action called with a tag as filter."""
        self.verify_perform_action(with_templates=True)


class DisplayTests(BasicMocking, CLIMocking):
    """Tests for the display action."""

    def test_Scout_get_note_content(self):
        """U Display: Using the communicator, get one note's content."""
        tt = self.wrap_subject(core.Scout, "get_note_content")

        tt.comm = self.m.CreateMockAnything()

        list_of_notes = self.full_list_of_notes()

        note = list_of_notes[12]
        raw_content = data("notes/%s" %note.title)
        lines = raw_content.splitlines()
        lines[0] = ''.join([
            lines[0],
            "  (system:notebook:reminders, training)"
        ])
        expected_result = "\n".join(lines)

        tt.comm.GetNoteContents(note.uri)\
            .AndReturn(raw_content)

        self.m.ReplayAll()
        self.assertEqual(expected_result, tt.get_note_content(note))
        self.m.VerifyAll()

    def test_perform_action(self):
        """U Display: perform_action executes successfully."""
        dsp_ap = self.wrap_subject(display.DisplayAction, "perform_action")
        dsp_ap.interface = self.m.CreateMock(core.Scout)

        fake_options = self.m.CreateMock(optparse.Values)
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        list_of_notes = self.full_list_of_notes()

        notes = [
            list_of_notes[10],
            list_of_notes[8]
        ]
        note_names = [n.title for n in notes]
        note1_content = data("notes/%s" % notes[0].title)
        note2_content = data("notes/%s" % notes[1].title)

        dsp_ap.interface.get_notes(names=note_names)\
            .AndReturn(notes)

        dsp_ap.interface.get_note_content(notes[0])\
            .AndReturn(note1_content.decode("utf-8")[:-1])
        dsp_ap.interface.get_note_content(notes[1])\
            .AndReturn(note2_content.decode("utf-8")[:-1])

        self.m.ReplayAll()
        dsp_ap.perform_action(fake_config, fake_options, note_names)
        self.m.VerifyAll()

        self.assertEqual(
            '\n'.join([note1_content, data("display_separator"),
                       note2_content]),
            sys.stdout.getvalue()
        )

    def test_perform_action_too_few_arguments(self):
        """U Display: perform_action without any argument displays an error."""
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
            data("display_no_note_name_error"),
            sys.stderr.getvalue()
        )


class DeleteTests(BasicMocking, CLIMocking):
    """Tests for code that delete notes."""

    def verify_perform_action(self, tags, names, all_notes, dry_run):
        """Test delete's entry point."""
        del_ap = self.wrap_subject(delete.DeleteAction, "perform_action")
        del_ap.interface = self.m.CreateMock(core.Scout)
        del_ap.interface.comm = self.m.CreateMockAnything()

        fake_options = self.m.CreateMock(optparse.Values)
        fake_options.tags = tags
        fake_options.templates = True
        fake_options.dry_run = dry_run
        fake_options.erase_all = all_notes

        fake_config = self.m.CreateMock(configparser.SafeConfigParser)
        notes = [
            n for n in self.full_list_of_notes()
            if "system:notebook:pim" in n.tags
               or n.title == "TDD"
        ]

        if all_notes:
            del_ap.interface.get_notes(
                names=[],
                tags=[],
                exclude_templates=False
            ).AndReturn(notes)
        elif names or tags:
            del_ap.interface.get_notes(
                names=names,
                tags=tags,
                exclude_templates=False
            ).AndReturn(notes)

        if not dry_run and (all_notes or names or tags):
            for note in notes:
                del_ap.interface.comm.DeleteNote(note.uri)

        self.m.ReplayAll()
        if all_notes or names or tags:
            del_ap.perform_action(fake_config, fake_options, names)
        else:
            self.assertRaises(
                SystemExit,
                del_ap.perform_action, fake_config, fake_options, names
            )
        self.m.VerifyAll()

        if dry_run:
            self.assertEqual(
                data("delete_dry_run_list"),
                sys.stdout.getvalue()
            )
        if not names and not tags and not all_notes:
            self.assertEqual(
                data("delete_no_argument_msg"),
                sys.stdout.getvalue()
            )

    def test_perform_action(self):
        """U Delete: perform_action executes successfully."""
        self.verify_perform_action(
            tags=["tag1", "tag2"],
            names=["note1"],
            all_notes=False,
            dry_run=False
        )

    def test_perform_action_no_argument(self):
        """U Delete: No filtering or note names given."""
        self.verify_perform_action(tags=[], names=[], all_notes=False,
                                   dry_run=False)

    def test_perform_action_all_notes(self):
        """U Delete: All notes requested for deletion."""
        self.verify_perform_action(tags=[], names=[], all_notes=True,
                                   dry_run=False)

    def test_perform_action_dry_run(self):
        """U Delete: Dry run of deletion for all notes."""
        self.verify_perform_action(tags=[], names=[], all_notes=True,
                                   dry_run=True)

    def test_init_options(self):
        """U Delete: Delete's options initialization."""
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
            help=''.join(["Simulate the action. The notes that are selected ",
                          "for deletion will be printed out to the screen but ",
                          "no note will really be deleted."])
        )

        plugins.FilteringGroup("Delete")\
            .AndReturn(fake_filtering_group)

        fake_filtering_group.get_option("-b")\
            .AndReturn(fake_option)

        fake_filtering_group.remove_option("--with-templates")

        optparse.Option(
            "--spare-templates",
            dest="templates", action="store_false", default=True,
            help=''.join(["Do not delete template notes that get caught with ",
                          "a tag or book name."])
        ).AndReturn(new_template_option)

        optparse.Option(
            "--all-notes",
            dest="erase_all", action="store_true", default=False,
            help=''.join(["Delete all notes. Once this is done, there is no ",
                          "turning back. To make sure that it is doing what ",
                          "you want, you could use the --dry-run option ",
                          "first."])
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
            data("book_help_delete")[:-1],
            fake_option.help
        )


class SearchTests(BasicMocking, CLIMocking):
    """Tests for the search action."""

    def test_init_options(self):
        """U Search: Search options are initialized correctly."""
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
        """Test output from SearchAction.perform_action."""
        srch_ap = self.wrap_subject(search.SearchAction, "perform_action")
        srch_ap.interface = self.m.CreateMock(core.Scout)

        tags = ["something"]
        note_contents = {}

        list_of_notes = self.full_list_of_notes()
        # Forget about the last note (a template)
        list_of_notes = list_of_notes[:-1]

        fake_options = self.m.CreateMock(optparse.Values)
        fake_options.tags = list(tags)
        fake_options.templates = with_templates
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        srch_ap.interface.get_notes(
            names=["addressbook", "business contacts"],
            tags=["something"],
            exclude_templates=not with_templates
        ).AndReturn(list_of_notes)

        for note in list_of_notes:
            content = data("notes/%s" %note.title)

            if note.tags:
                lines = content.splitlines()
                lines[0] =  "%s  (%s)" % (lines[0], ", ".join(note.tags))
                content = "\n".join(lines)

            note_contents[note.title] = content

        for note in list_of_notes:
            srch_ap.interface.get_note_content(note)\
                .AndReturn(note_contents[note.title])

        self.m.ReplayAll()

        srch_ap.perform_action(
            fake_config,
            fake_options,
            ["john", "addressbook", "business contacts"]
        )

        self.m.VerifyAll()

        self.assertEqual(
            data("search_results"),
            sys.stdout.getvalue()
        )

    def test_perform_action(self):
        """U Search: perform_action without filters."""
        self.verify_perform_action(with_templates=False)

    def test_perform_action_templates(self):
        """U Search: perform_action with templates included."""
        self.verify_perform_action(with_templates=True)

    def test_perform_action_too_few_arguments(self):
        """U Search: perform_action, without any arguments."""
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
            data("search_no_argument_error"),
            sys.stderr.getvalue()
        )


class VersionTests(BasicMocking, CLIMocking):
    """Tests for the version action."""

    def test_perform_action(self):
        """U Version: perform_action prints out Tomboy's version."""
        vrsn_ap = self.wrap_subject(version.VersionAction, "perform_action")
        vrsn_ap.interface = self.m.CreateMock(core.Scout)
        vrsn_ap.interface.comm = self.m.CreateMockAnything()
        vrsn_ap.interface.application = "some_app"

        fake_options = self.m.CreateMock(optparse.Values)
        fake_config = self.m.CreateMock(configparser.SafeConfigParser)

        vrsn_ap.interface.comm.Version()\
            .AndReturn("1.0.1")

        self.m.ReplayAll()

        vrsn_ap.perform_action(fake_config, fake_options, [])

        self.m.VerifyAll()

        self.assertEqual(
            data("tomboy_version_output") % (SCOUT_VERSION, "some_app"),
            sys.stdout.getvalue()
        )
