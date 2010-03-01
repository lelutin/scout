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

These are unit tests for the applications classes and methods.

The docstrings on the test methods are displayed by the unittest.main()
routine, so it should be a short but precise description of what is being
tested. There should also be the test case's second word followed by a colon
to classify tests. Having this classification makes looking for failing
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

from tomtom import core, cli, plugins
# Import the list action under a different name to avoid overwriting the list()
# builtin function.
from tomtom.actions import display, list as _list, search, version

import test_data
from test_utils import *

class TestMain(BasicMocking, CLIMocking):
    """Tests for functions in the main script.

    This test case verifies that functions in the main script behave as
    expected.

    """
    def test_KeyboardInterrupt_is_handled(self):
        """Main: KeyboardInterrupt doesn't come out of the application."""
        self.m.StubOutWithMock(cli, "main")

        cli.main().AndRaise(KeyboardInterrupt)

        self.m.ReplayAll()

        # No output is expected, simply check if an exception goes through.
        try:
            cli.exception_wrapped_main()
        except KeyboardInterrupt:
            self.fail("KeyboardInterrupt got out of the program")

        self.m.VerifyAll()

    def test_arguments_converted_to_unicode(self):
        """Main: Arguments to action are converted to unicode objects."""
        """This is the default main() behaviour."""
        self.m.StubOutWithMock(cli, "dispatch")

        arguments = ["arg1", "arg2"]
        sys.argv = ["app_name", "action"] + arguments

        cli.dispatch("action", [unicode(arg) for arg in arguments] )

        self.m.ReplayAll()

        cli.main()

        self.m.VerifyAll()

    def verify_exit_from_main(self,
            arguments, expected_text, output_stream):
        sys.argv = ["app_name"] + arguments

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.main
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

    def test_main_help(self):
        """Main: using only -h prints help and list of actions."""
        self.m.StubOutWithMock(cli, "action_short_summaries")

        sys.argv = ["app_name", "-h"]

        cli.action_short_summaries()\
            .AndReturn(test_data.module_descriptions)

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.main
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.main_help +
                os.linesep.join(test_data.module_descriptions) +
                os.linesep,
            sys.stdout.getvalue()
        )

    def test_help_before_action(self):
        """Main: -h before action gets switched to normal help call."""
        self.m.StubOutWithMock(cli, "dispatch")

        sys.argv = ["app_name", "-h", "action"]

        processed_arguments = [ sys.argv[0], sys.argv[2], sys.argv[1] ]

        cli.dispatch(
            "action",
            [unicode(arg) for arg in processed_arguments[1:] ]
        )

        self.m.ReplayAll()

        cli.main()

        self.m.VerifyAll()

    def test_display_tomtom_version(self):
        """Main: -v option displays Tomtom's version and license information."""
        self.verify_exit_from_main(
            ["-v"],
            test_data.version_and_license_info,
            output_stream=sys.stdout
        )

    def test_list_of_actions(self):
        """Main: list_of_actions returns classes of action plugins."""
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
            core.Tomtom,
        ]

        pkg_resources.iter_entry_points(group="tomtom.actions")\
            .AndReturn(entry_points)

        for (index, entry_point) in enumerate(entry_points):
            entry_point.load()\
                .AndReturn( plugin_classes[index] )

        self.m.ReplayAll()

        # "name" attributes are irrelevant here as 3 classes are the same
        self.assertEqual(
            plugin_classes[:-1],
            cli.list_of_actions()
        )

        self.m.VerifyAll()

    def test_load_action(self):
        """Main: Initialize an action plugin instance."""
        self.m.StubOutWithMock(cli, "list_of_actions")

        action1 = self.m.CreateMockAnything()
        action1.name = "action1"
        action2 = self.m.CreateMockAnything()
        action2.name = "action2"

        mock_class = self.m.CreateMockAnything()

        cli.list_of_actions()\
            .AndReturn( [action1, action2] )

        action2()\
            .AndReturn( mock_class )

        self.m.ReplayAll()

        self.assertEqual(
            mock_class,
            cli.load_action("action2")
        )

        self.m.VerifyAll()

    def test_load_unknown_action(self):
        """Main: Requested action name is invalid."""
        self.m.StubOutWithMock(cli, "list_of_actions")
        self.m.StubOutWithMock(os.path, "basename")

        sys.argv = ["app_name"]

        cli.list_of_actions()\
            .AndReturn( [] )

        os.path.basename("app_name")\
            .AndReturn("app_name")

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.load_action, "unexistant_action"
        )

        self.assertEqual(
            test_data.unknown_action + os.linesep,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_action_short_summaries(self):
        """Main: Extract short summaries from action plugins."""
        self.m.StubOutWithMock(cli, "list_of_actions")

        action1 = self.m.CreateMockAnything()
        action1.name = "action1"
        action1.short_description = test_data.module1_description
        action2 = self.m.CreateMockAnything()
        action2.name = "otheraction"
        action2.short_description = None

        cli.list_of_actions()\
            .AndReturn( [action1, action2] )

        self.m.ReplayAll()

        self.assertEqual(
            test_data.module_descriptions,
            cli.action_short_summaries()
        )

        self.m.VerifyAll()

    def mock_out_dispatch(self, exception_class, exception_argument):
        """Mock out calls in dispatch that we go through in all cases."""
        fake_tomtom = self.m.CreateMock(core.Tomtom)

        self.m.StubOutWithMock(cli, "load_action")
        self.m.StubOutWithMock(cli, "parse_options")
        self.m.StubOutWithMock(core, "Tomtom", use_mock_anything=True)

        action_name = "some_action"
        fake_action = self.m.CreateMock(plugins.ActionPlugin)
        arguments = self.m.CreateMock(list)
        positional_arguments = self.m.CreateMock(list)
        options = self.m.CreateMock(optparse.Values)

        cli.load_action(action_name)\
            .AndReturn(fake_action)

        cli.parse_options(fake_action, arguments)\
            .AndReturn( (options, positional_arguments) )

        core.Tomtom()\
            .AndReturn( fake_tomtom )

        if exception_class:
            fake_action.perform_action(options, positional_arguments)\
                .AndRaise( exception_class(exception_argument) )
        else:
            fake_action.perform_action(options, positional_arguments)\
                .AndReturn(None)

        return (action_name, fake_action, arguments)

    def test_dispatch(self):
        """Main: Action calls are dispatched to the right action."""
        action_name, fake_action, arguments = \
            self.mock_out_dispatch(None, None)

        self.m.ReplayAll()

        cli.dispatch(action_name, arguments)

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

        action_name, fake_action, arguments = \
            self.mock_out_dispatch(exception_class, exception_argument)

        self.m.ReplayAll()

        self.assertRaises(
            exception_out,
            cli.dispatch, action_name, arguments
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

    def print_traceback(self):
        """Fake an output of an arbitrary traceback on sys.stderr"""
        print >> sys.stderr, test_data.fake_traceback

    def test_dispatch_handles_action_exceptions(self):
        """Main: All unknown exceptions from actions are handled."""
        action_name, fake_action, arguments = \
            self.mock_out_dispatch(Exception, "something happened")

        sys.argv = ["app_name"]

        old_print_exc = traceback.print_exc
        traceback.print_exc = self.print_traceback

        self.m.StubOutWithMock(os.path, "basename")

        os.path.basename(sys.argv[0])\
            .AndReturn(sys.argv[0])

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.dispatch, action_name, arguments
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.unhandled_action_exception_error_message + os.linesep,
            sys.stderr.getvalue()
        )

        traceback.print_exc = old_print_exc

    def test_dispatch_handles_option_type_exceptions(self):
        """Main: dispatch prints an error if an option is of the wrong type."""
        self.m.StubOutWithMock(cli, "load_action")
        self.m.StubOutWithMock(cli, "parse_options")

        action_name = "some_action"
        fake_action = self.m.CreateMock(plugins.ActionPlugin)
        fake_action.name = action_name
        arguments = self.m.CreateMock(list)

        cli.load_action(action_name)\
            .AndReturn(fake_action)

        cli.parse_options(fake_action, arguments)\
            .AndRaise( TypeError(test_data.option_type_error_message) )

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.dispatch, action_name, arguments
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.option_type_error_message + os.linesep,
            sys.stderr.getvalue()
        )

    def test_parse_options(self):
        """Main: Parse an action's options and return them"""
        self.m.StubOutWithMock(cli, "retrieve_options")

        option_parser = self.m.CreateMock(optparse.OptionParser)
        self.m.StubOutWithMock(
            optparse, "OptionParser", use_mock_anything=True
        )

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

        cli.retrieve_options(option_parser, fake_action)\
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

        result = cli.parse_options(fake_action, arguments)

        self.m.VerifyAll()

        self.assertEqual(
            (fake_values, positional_arguments),
            result
        )

    def test_retrieve_options(self):
        """Main: Get a list of options from an action plugin."""
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

        result = cli.retrieve_options(fake_option_parser, fake_action)

        self.m.VerifyAll()

        self.assertEqual(
            list_of_options,
            result
        )

class TestCore(BasicMocking):

    """Tests for general code."""

    def test_Tomtom_constructor(self):
        """Core: Tomtom's dbus interface is initialized."""
        tt = self.wrap_subject(core.Tomtom, "__init__")

        old_SessionBus = dbus.SessionBus
        old_Interface = dbus.Interface

        dbus.SessionBus = self.m.CreateMockAnything()
        dbus.Interface = self.m.CreateMockAnything()
        session_bus = self.m.CreateMockAnything()
        dbus_object = self.m.CreateMockAnything()
        dbus_interface = self.m.CreateMockAnything()

        dbus.SessionBus()\
            .AndReturn(session_bus)
        session_bus.get_object(
            "org.gnome.Tomboy",
            "/org/gnome/Tomboy/RemoteControl"
        ).AndReturn(dbus_object)
        dbus.Interface(
            dbus_object,
            "org.gnome.Tomboy.RemoteControl"
        ).AndReturn(dbus_interface)

        self.m.ReplayAll()

        tt.__init__()
        self.assertEqual( dbus_interface, tt.comm )

        self.m.VerifyAll()
        dbus.SessionBus = old_SessionBus
        dbus.Interface = old_Interface

    def mock_out_TomboyNote_and_verify_constructor(self, **kwargs):
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
        tn = self.mock_out_TomboyNote_and_verify_constructor(
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

        tn = self.mock_out_TomboyNote_and_verify_constructor(uri=uri2)

        # case 2: Construct with only uri, rest is default
        self.assertEqual(tn.uri, uri2)
        self.assertEqual(tn.title, "")
        self.assertEqual(tn.date, dbus.Int64() )
        self.assertEqual(tn.tags, [])

    def test_TomboyNote_constructor_datetetime(self):
        """Core: TomboyNote initializes its instance variables. case 2."""
        datetime_date = datetime.datetime(2009, 11, 13, 18, 42, 23)

        # case 3: the date can be entered with a datetime.datetime
        tn = self.mock_out_TomboyNote_and_verify_constructor(
            uri="not important",
            date=datetime_date
        )

        self.assertEqual(
            dbus.Int64(
                time.mktime( datetime_date.timetuple() )
            ),
            tn.date
        )

    def test_get_notes(self):
        """Core: Note fetching entry point builds and filters a list."""
        tt = self.wrap_subject(core.Tomtom, "get_notes")

        # Only verify calls here, results are tested separately
        tt.build_note_list()\
            .AndReturn(test_data.full_list_of_notes)
        tt.filter_notes(test_data.full_list_of_notes)

        self.m.ReplayAll()

        tt.get_notes()

        self.m.VerifyAll()

    def test_filter_notes(self):
        """Core: Note filtering."""
        tt = self.wrap_subject(core.Tomtom, "filter_notes")

        notes = [self.m.CreateMockAnything(), self.m.CreateMockAnything()]
        tags = [self.m.CreateMockAnything()]
        fake_filtered_list = self.m.CreateMockAnything()

        # Only test calls here, results are tested elsewhere
        tt.filter_by_tags(notes, tags)\
            .AndReturn(fake_filtered_list)
        tt.filter_out_templates(fake_filtered_list)

        self.m.ReplayAll()

        tt.filter_notes(notes, tags=tags)

        self.m.VerifyAll()

    def test_filter_notes_by_names(self):
        """Core: Filter notes by names."""
        """No template filtering should occur if names were given.

        If names were given, the user will expect to see templates if they were
        explicitly named. Thus, filtering should not happen in this case.

        """
        tt = self.wrap_subject(core.Tomtom, "filter_notes")

        notes = [
            test_data.full_list_of_notes[4],
            # A template is requested: it should be returned
            test_data.full_list_of_notes[13],
        ]

        names = ["python-work", "New note template"]

        self.m.ReplayAll()

        self.assertEqual(
            notes,
            tt.filter_notes(notes, names=names)
        )

        self.m.VerifyAll()

    def test_fiter_notes_template_as_a_tag(self):
        """Core: Specifying templates as a tag should include them."""
        tt = self.wrap_subject(core.Tomtom, "filter_notes")

        notes = [self.m.CreateMockAnything(), self.m.CreateMockAnything()]
        tags = ["system:template", "someothertag"]

        fake_filtered_list = self.m.CreateMockAnything()

        # Only test calls here, results are tested elsewhere
        tt.filter_by_tags(notes, tags)\
            .AndReturn(fake_filtered_list)

        self.m.ReplayAll()

        tt.filter_notes(notes, tags=tags)

        self.m.VerifyAll()

    def test_fiter_notes_with_templates(self):
        """Core: Do not exclude templates."""
        tt = self.wrap_subject(core.Tomtom, "filter_notes")

        notes = [self.m.CreateMockAnything(), self.m.CreateMockAnything()]
        tags = []

        fake_filtered_list = self.m.CreateMockAnything()

        self.m.ReplayAll()

        tt.filter_notes(notes, tags=tags, exclude_templates=False)

        self.m.VerifyAll()

    def test_filter_by_tags(self):
        """Core: Filter notes by tags."""
        tt = self.wrap_subject(core.Tomtom, "filter_by_tags")

        notes = [
            test_data.full_list_of_notes[0],
            test_data.full_list_of_notes[1],
            test_data.full_list_of_notes[10],
            # Doesn't have the tags
            test_data.full_list_of_notes[12],
        ]
        tag_list = ["system:notebook:pim", "projects"]

        expected_result = notes[:-1]

        self.m.ReplayAll()

        self.assertEqual(
            expected_result,
            tt.filter_by_tags(notes, tag_list=tag_list)
        )

        self.m.VerifyAll()

    def test_filter_out_templates(self):
        """Core: Remove templates from a list of notes."""
        tt = self.wrap_subject(core.Tomtom, "filter_out_templates")

        notes = [
            test_data.full_list_of_notes[9],
            test_data.full_list_of_notes[10],
            # This one is a template
            test_data.full_list_of_notes[13],
        ]

        expected_result = notes[:-1]

        self.m.ReplayAll()

        self.assertEqual(
            expected_result,
            tt.filter_out_templates(notes)
        )

        self.m.VerifyAll()

    def verify_note_list(self, tt, notes, note_names=[]):
        """Verify the outcome of Tomtom.get_notes().

        This function verifies if notes received from calling
        Tomtom.get_notes are what we expect them to be. It provokes
        the unit test to fail in case of discordance.

        TomboyNotes are unhashable so we need to convert them to dictionaries
        and check for list membership.

        Arguments:
            self       -- The TestCase instance
            tt         -- Tomtom mock object instance
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
        for note in tt.build_note_list(names=note_names):
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

    def test_build_note_list_by_names(self):
        """Core: Tomtom gets a list of given named notes."""
        tt = self.wrap_subject(core.Tomtom, "build_note_list")

        tt.comm = self.m.CreateMockAnything()

        todo = test_data.full_list_of_notes[1]
        recipes = test_data.full_list_of_notes[11]
        notes = [todo, recipes]
        names = [n.title for n in notes]

        tt.get_uris_by_name(names)\
            .AndReturn( [(n.uri, n.title) for n in notes] )

        for note in notes:
            tt.comm.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            tt.comm.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

        self.m.ReplayAll()

        self.verify_note_list(tt, notes, note_names=names)

        self.m.VerifyAll()

    def test_build_note_list(self):
        """Core: Tomtom gets a full list of notes."""
        tt = self.wrap_subject(core.Tomtom, "build_note_list")

        tt.comm = self.m.CreateMockAnything()

        list_of_uris = dbus.Array(
            [note.uri for note in test_data.full_list_of_notes]
        )

        tt.get_uris_for_n_notes(None)\
            .AndReturn( [(u, None) for u in list_of_uris] )

        for note in test_data.full_list_of_notes:
            tt.comm.GetNoteTitle(note.uri)\
                .AndReturn(note.title)
            tt.comm.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            tt.comm.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

        self.m.ReplayAll()

        self.verify_note_list(tt, test_data.full_list_of_notes)

        self.m.VerifyAll()

    def test_get_uris_by_name(self):
        """Core: Tomtom determines uris by names."""
        tt = self.wrap_subject(core.Tomtom, "get_uris_by_name")

        tt.comm = self.m.CreateMockAnything()

        r_n_d = test_data.full_list_of_notes[12]
        webpidgin = test_data.full_list_of_notes[9]
        names = [r_n_d.title, webpidgin.title]

        tt.comm.FindNote(r_n_d.title)\
            .AndReturn(r_n_d.uri)
        tt.comm.FindNote(webpidgin.title)\
            .AndReturn(webpidgin.uri)

        self.m.ReplayAll()

        self.assertEqual(
            [(r_n_d.uri, r_n_d.title), (webpidgin.uri, webpidgin.title)],
            tt.get_uris_by_name(names)
        )

        self.m.VerifyAll()

    def test_get_uris_by_name_unexistant(self):
        """Core: Tomtom raises a NoteNotFound exception."""
        tt = self.wrap_subject(core.Tomtom, "get_uris_by_name")

        tt.comm = self.m.CreateMockAnything()

        tt.comm.FindNote("unexistant")\
            .AndReturn(dbus.String(""))

        self.m.ReplayAll()

        self.assertRaises(
            core.NoteNotFound,
            tt.get_uris_by_name,
            ["unexistant"]
        )

        self.m.VerifyAll()

    def test_dbus_Tomboy_communication_problem(self):
        """Core: Raise an exception if linking dbus with Tomboy failed."""
        tt = self.wrap_subject(core.Tomtom, "__init__")

        old_SessionBus = dbus.SessionBus
        old_Interface = dbus.Interface

        dbus.SessionBus = self.m.CreateMockAnything()
        dbus.Interface = self.m.CreateMockAnything()
        session_bus = self.m.CreateMockAnything()
        dbus_object = self.m.CreateMockAnything()
        dbus_interface = self.m.CreateMockAnything()

        dbus.SessionBus()\
            .AndReturn(session_bus)
        session_bus.get_object(
            "org.gnome.Tomboy",
            "/org/gnome/Tomboy/RemoteControl"
        ).AndReturn(dbus_object)
        dbus.Interface(
            dbus_object,
            "org.gnome.Tomboy.RemoteControl"
        ).AndRaise( dbus.DBusException("cosmos error") )

        self.m.ReplayAll()

        self.assertRaises(core.ConnectionError, tt.__init__)

        self.m.VerifyAll()

        dbus.SessionBus = old_SessionBus
        dbus.Interface = old_Interface

class TestList(BasicMocking, CLIMocking):
    """Tests for code that handles the notes and lists them."""
    def test_get_uris_for_n_notes_no_limit(self):
        """List: Given no limit, get all the notes' uris."""
        tt = self.wrap_subject(core.Tomtom, "get_uris_for_n_notes")

        tt.comm = self.m.CreateMockAnything()

        list_of_uris = dbus.Array(
            [note.uri for note in test_data.full_list_of_notes]
        )

        tt.comm.ListAllNotes()\
            .AndReturn( list_of_uris )

        self.m.ReplayAll()

        self.assertEqual(
            [(uri, None) for uri in list_of_uris],
            tt.get_uris_for_n_notes(None)
        )

        self.m.VerifyAll()

    def test_get_uris_for_n_notes(self):
        """List: Given a numerical limit, get the n latest notes' uris."""
        tt = self.wrap_subject(core.Tomtom, "get_uris_for_n_notes")

        tt.comm = self.m.CreateMockAnything()

        list_of_uris = dbus.Array(
            [note.uri for note in test_data.full_list_of_notes]
        )

        tt.comm.ListAllNotes()\
            .AndReturn( list_of_uris )

        self.m.ReplayAll()

        self.assertEqual(
            [(uri, None) for uri in list_of_uris[:6] ],
            tt.get_uris_for_n_notes(6)
        )

        self.m.VerifyAll()

    def test_listing(self):
        """List: Format information of a list of notes."""
        lst_ap = self.wrap_subject(_list.ListAction, "listing")

        # Forget about the last note (a template)
        list_of_notes = test_data.full_list_of_notes[:-1]

        for note in list_of_notes:
            # XXX transform the list into mocks to avoid this
            self.m.StubOutWithMock(note, "listing")
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
        lst_ap.tomboy_interface = self.m.CreateMock(core.Tomtom)

        tags = ["whatever"]

        fake_options = self.m.CreateMock(optparse.Values)
        # Duplicate the list to avoid modification by later for loop
        fake_options.tags = list(tags)
        fake_options.templates = with_templates
        fake_options.max_notes = 5

        lst_ap.tomboy_interface.get_notes(
            count_limit=5,
            tags=tags,
            exclude_templates=not with_templates
        ).AndReturn(test_data.full_list_of_notes)

        lst_ap.listing(test_data.full_list_of_notes)\
            .AndReturn(test_data.expected_list)

        self.m.ReplayAll()

        lst_ap.perform_action(fake_options, [])

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

class TestDisplay(BasicMocking, CLIMocking):
    """Tests for code that display notes' content."""
    def test_get_display_for_notes(self):
        """Display: Tomtom returns notes' contents, separated a marker."""
        dsp_ap = self.wrap_subject(
            display.DisplayAction,
            "format_display_for_notes"
        )
        dsp_ap.tomboy_interface = self.m.CreateMock(core.Tomtom)

        notes = [
            test_data.full_list_of_notes[10],
            test_data.full_list_of_notes[8]
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

    def test_Tomtom_get_note_content(self):
        """Display: Using the communicator, get one note's content."""
        tt = self.wrap_subject(core.Tomtom, "get_note_content")

        tt.comm = self.m.CreateMockAnything()

        note = test_data.full_list_of_notes[12]
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
        dsp_ap.tomboy_interface = self.m.CreateMock(core.Tomtom)

        fake_options = self.m.CreateMock(optparse.Values)
        notes = [ self.m.CreateMock(core.TomboyNote) ]

        dsp_ap.tomboy_interface.get_notes(names=["addressbook"])\
            .AndReturn(notes)

        dsp_ap.format_display_for_notes(notes)\
            .AndReturn(
                test_data.note_contents_from_dbus["addressbook"].decode("utf-8")
            )

        self.m.ReplayAll()

        dsp_ap.perform_action(fake_options, ["addressbook"])

        self.m.VerifyAll()

        self.assertEqual(
            test_data.note_contents_from_dbus["addressbook"] + os.linesep,
            sys.stdout.getvalue()
        )

    def test_perform_action_too_few_arguments(self):
        """Display: perform_action without any argument displays an error."""
        dsp_ap = self.wrap_subject(display.DisplayAction, "perform_action")

        fake_options = self.m.CreateMock(optparse.Values)

        self.m.ReplayAll()
        self.assertRaises(
            SystemExit,
            dsp_ap.perform_action, fake_options, []
        )
        self.m.VerifyAll()

        self.assertEqual(
            test_data.display_no_note_name_error + os.linesep,
            sys.stderr.getvalue()
        )

class TestSearch(BasicMocking, CLIMocking):
    """Tests for code that perform a textual search within notes."""
    def test_search_for_text(self):
        """Search: Tomtom triggers a search through requested notes."""
        srch_ap = self.wrap_subject(search.SearchAction, "search_for_text")
        srch_ap.tomboy_interface = self.m.CreateMock(core.Tomtom)

        note_contents = {}
        # Forget about last note (a template)
        list_of_notes = test_data.full_list_of_notes[:-1]

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
        srch_ap.tomboy_interface = self.m.CreateMock(core.Tomtom)

        tags = ["something"]
        list_of_notes = test_data.full_list_of_notes[:-1]

        fake_options = self.m.CreateMock(optparse.Values)
        fake_options.tags = list(tags)
        fake_options.templates = with_templates

        srch_ap.tomboy_interface.get_notes(
            names=["note1", "note2"],
            tags=["something"],
            exclude_templates=not with_templates
        ).AndReturn(list_of_notes)

        srch_ap.search_for_text("findme", list_of_notes)\
            .AndReturn(test_data.search_structure)

        self.m.ReplayAll()

        srch_ap.perform_action(fake_options, ["findme", "note1", "note2"])

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

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            srch_ap.perform_action, fake_options, []
        )

        self.m.VerifyAll()

        self.assertEqual(
            test_data.search_no_argument_error + os.linesep,
            sys.stderr.getvalue()
        )

class TestVersion(BasicMocking, CLIMocking):
    """Tests for code that show Tomboy's version."""
    def test_perform_action(self):
        """Version: perform_action prints out Tomboy's version."""
        vrsn_ap = self.wrap_subject(version.VersionAction, "perform_action")
        vrsn_ap.tomboy_interface = self.m.CreateMock(core.Tomtom)
        vrsn_ap.tomboy_interface.comm = self.m.CreateMockAnything()

        fake_options = self.m.CreateMock(optparse.Values)

        vrsn_ap.tomboy_interface.comm.Version()\
            .AndReturn("1.0.1")

        self.m.ReplayAll()

        vrsn_ap.perform_action(fake_options, [])

        self.m.VerifyAll()

        self.assertEqual(
            test_data.tomboy_version_output + os.linesep,
            sys.stdout.getvalue()
        )

class TestPlugins(BasicMocking):
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
        """Plugins: A tomtom.plugins.OptionGroup object is inserted."""
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
        """Plugins: Option library is not a tomtom.plugins.OptionGroup."""
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
            "-b", action="callback", dest="books",
            callback=book_callback, type="string",
            help="""Murder only notes belonging to """ + \
            """specified notebooks. It is a shortcut to option "-t" to """
            """specify notebooks more easily. For example, use"""
            """ "-b HGTTG" instead of "-t system:notebook:HGTTG". Use """
            """this option once for each desired book."""
        ).AndReturn( option_list[0] )

        optparse.Option(
            "--with-templates",
            dest="templates", action="store_true", default=False,
            help="""Include template notes. This option is """
            """different from using "-t system:template" in that the """
            """latter used alone will only include the templates, while """
            """"using "--with-templates" without specifying tags for """
            """selection will include all notes and templates."""
        ).AndReturn( option_list[1] )

        optparse.Option(
            "-t",
            dest="tags", action="append", default=[],
            help="""Murder only notes with """ + \
            """specified tags. Use this option once for each desired """
            """tag. This option selects raw tags and could be useful for """
            """user-assigned tags."""
        ).AndReturn( option_list[2] )

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
