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
"""Acceptance tests for Tomtom.

This defines the use cases and expected results.

"""
import unittest
import sys
import os
import StringIO
import mox

import tomtom
import dbus
import test_data

class AcceptanceTests(unittest.TestCase):
    """Acceptance tests.

    Define what the expected behaviour is from the user's point of view.

    Those tests are meant to verify correct functionality of the whole
    application, so they mock out external library dependencies only.

    """
    def setUp(self):
        """Unit test preparation.

        Mock out the default dbus interaction: that of creating an object that
        establishes contact with Tomboy via dbus.

        """
        self.old_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        self.old_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()
        self.old_argv = sys.argv
        self.m = mox.Mox()

        # Mock out the entire dbus interaction so that acceptance tests don't
        # depend on external code.
        self.old_SessionBus = dbus.SessionBus
        self.old_Interface = dbus.Interface
        dbus.SessionBus = self.m.CreateMockAnything()
        dbus.Interface = self.m.CreateMockAnything()
        session_bus = self.m.CreateMockAnything()
        dbus_object = self.m.CreateMockAnything()
        self.dbus_interface = self.m.CreateMockAnything()

        dbus.SessionBus()\
            .AndReturn(session_bus)
        session_bus.get_object(
            "org.gnome.Tomboy",
            "/org/gnome/Tomboy/RemoteControl"
        ).AndReturn(dbus_object)
        dbus.Interface(
            dbus_object,
            "org.gnome.Tomboy.RemoteControl"
        ).AndReturn(self.dbus_interface)

    def tearDown(self):
        """Unit test breakdown.

        Remove mocks and replace what was disturbed so that it doesn't affect
        other tests.

        """
        sys.stderr = self.old_stderr
        sys.stdout = self.old_stdout
        sys.argv = self.old_argv
        dbus.SessionBus = self.old_SessionBus
        dbus.Interface = self.old_Interface
        self.m.UnsetStubs()

    def mock_out_listing(self, notes):
        """Create mocks for note listing via dbus.

        Arguments:
            notes -- a list of TomboyNote objects

        """
        self.dbus_interface.ListAllNotes()\
            .AndReturn([n.uri for n in notes])
        for note in notes:
            self.dbus_interface.GetNoteTitle(note.uri)\
                .AndReturn(note.title)
            self.dbus_interface.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            self.dbus_interface.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

    def mock_out_get_notes_by_names(self, notes):
        """Create mocks for searching for notes by their names.

        Arguments:
            notes -- a list of TomboyNote objects

        """
        for note in notes:
            self.dbus_interface.FindNote(note.title)\
                .AndReturn(note.uri)

        for note in notes:
            self.dbus_interface.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            self.dbus_interface.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

    def test_no_argument(self):
        """Acceptance: tomtom called without arguments must print usage."""
        sys.argv = ["app_name", ]
        old_docstring = tomtom.__doc__
        tomtom.__doc__ = os.linesep.join([
            "command -h",
            "command action",
            "",
            "unused",
            "but fake",
            "help text"
        ])

        # Test that usage comes from the script's docstring.
        tomtom.main()

        # This test is not very flexible. Change this if more lines are
        # added to the usage description in the docstring.
        self.assertEqual(
            (os.linesep * 2).join([
                os.linesep.join( tomtom.__doc__.splitlines()[:3]),
                test_data.help_more_details
            ]) + os.linesep,
            sys.stdout.getvalue()
        )

        tomtom.__doc__ = old_docstring

    def test_unknown_action(self):
        """Acceptance: Giving an unknown action name must print an error."""
        sys.argv = ["app_name", "unexistant_action"]
        tomtom.main()
        self.assertEqual(
            test_data.unknown_action + os.linesep,
            sys.stderr.getvalue()
        )

    def test_action_list(self):
        """Acceptance: Action "list" prints a list of the last 10 notes."""
        self.mock_out_listing(test_data.full_list_of_notes[:10])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "list"]
        tomtom.main()
        self.assertEquals(
            test_data.expected_list + os.linesep,
            sys.stdout.getvalue()
        )

        self.m.VerifyAll()

    def test_full_list(self):
        """Acceptance: Action "list" with "-a" produces a list of all notes."""
        self.mock_out_listing(test_data.full_list_of_notes)

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "list", "-a"]
        tomtom.main()
        self.assertEquals(
            os.linesep.join([
                test_data.expected_list,
                test_data.list_appendix
            ]) + os.linesep,
            sys.stdout.getvalue()
        )

        self.m.VerifyAll()

    def test_notes_displaying(self):
        """Acceptance: Action "display" prints the content given note names."""
        todo = test_data.full_list_of_notes[1]
        python_work = test_data.full_list_of_notes[4]
        separator = os.linesep + "==========================" + os.linesep
        note_lines = test_data.note_contents_from_dbus["TODO-list"]\
                        .splitlines()
        note_lines[0] = "%s  (reminders, pim)" % note_lines[0]
        expected_result_list = [
            os.linesep.join(note_lines),
            test_data.note_contents_from_dbus["python-work"]
        ]

        self.mock_out_get_notes_by_names([todo, python_work])

        self.dbus_interface.GetNoteContents(todo.uri)\
            .AndReturn(test_data.note_contents_from_dbus["TODO-list"])
        self.dbus_interface.GetNoteContents(python_work.uri)\
            .AndReturn(test_data.note_contents_from_dbus["python-work"])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "display", "TODO-list", "python-work"]
        tomtom.main()
        self.assertEquals(
            separator.join(expected_result_list) + os.linesep,
            sys.stdout.getvalue()
        )

        self.m.VerifyAll()

    def test_note_does_not_exist(self):
        """Acceptance: Specified note non-existant: display an error."""
        self.dbus_interface.FindNote("unexistant")\
            .AndReturn(dbus.String(""))

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "display", "unexistant"]
        tomtom.main()
        self.assertEquals(
            """Note named "unexistant" not found.""" + os.linesep,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_display_zero_argument(self):
        """Acceptance: Action "display" with no argument prints an error."""
        sys.argv = ["app_name", "display"]
        tomtom.main()
        self.assertEquals(
            test_data.display_no_note_name_error + os.linesep,
            sys.stderr.getvalue()
        )

    def test_search(self):
        """Acceptance: Action "search" searches in all notes, case-indep."""
        self.mock_out_listing(test_data.full_list_of_notes)
        for note in test_data.full_list_of_notes:
            self.dbus_interface.GetNoteContents(note.uri)\
                .AndReturn(test_data.note_contents_from_dbus[note.title])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "search", "john doe"]
        tomtom.main()
        self.assertEquals(
            test_data.search_results + os.linesep,
            sys.stdout.getvalue()
        )

        self.m.VerifyAll()

    def test_search_specific_notes(self):
        """Acceptance: Action "search" restricts the search to given notes."""
        requested_notes = [
            test_data.full_list_of_notes[3],
            test_data.full_list_of_notes[4],
            test_data.full_list_of_notes[6],
        ]

        self.mock_out_get_notes_by_names(requested_notes)
        for note in requested_notes:
            self.dbus_interface.GetNoteContents(note.uri)\
                .AndReturn(test_data.note_contents_from_dbus[note.title])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "search", "python"] + \
                [n.title for n in requested_notes]
        tomtom.main()
        self.assertEquals(
            test_data.specific_search_results + os.linesep,
            sys.stdout.getvalue()
        )

        self.m.VerifyAll()

    def test_search_zero_arguments(self):
        """Acceptance: Action "search" with no argument prints an error."""
        sys.argv = ["unused_prog_name", "search"]
        tomtom.main()
        self.assertEquals(
            test_data.search_no_argument_error + os.linesep,
            sys.stderr.getvalue()
        )

    def test_help_on_base_level(self):
        """Acceptance: Using "-h" or "--help" alone prints basic help."""
        sys.argv = ["app_name", "-h"]
        old_docstring = tomtom.__doc__
        tomtom.__doc__ = os.linesep.join([
            "some",
            "non-",
            "useful",
            "but fake",
            "help text"
        ])

        tomtom.main()

        # The help should be displayed using tomtom's docstring.
        self.assertEquals(
            tomtom.__doc__[:-1] + os.linesep,
            sys.stdout.getvalue()
        )

        tomtom.__doc__ = old_docstring

    def verify_help_text(self, args, text):
        """Mock out help messages.

        Mimic things to expect the application to exit while printing a
        specified help text.

        Arguments:
            args -- a list of meuh
            text -- the text to verify against

        """
        sys.argv = args

        # Mock out sys.exit : optparse calls this when help is displayed
        self.m.StubOutWithMock(sys, "exit")
        sys.exit(0).AndRaise(SystemExit)

        self.m.ReplayAll()

        self.assertRaises(SystemExit, tomtom.main)
        self.assertEquals(
            text + os.linesep,
            sys.stdout.getvalue()
        )

    def test_help_before_action_name(self):
        """Acceptance: Using "-h" before an action displays detailed help."""
        self.verify_help_text(
            [
                "app_name",
                "-h",
                "list"
            ],
            test_data.help_details_list
        )

    def test_help_display_specific(self):
        """Acceptance: Detailed help using "-h" after "display" action."""
        self.verify_help_text(
            [
                "app_name",
                "display",
                "--help"
            ],
            test_data.help_details_display
        )

    def test_help_list_specific(self):
        """Acceptance: Detailed help using "-h" after "list" action."""
        self.verify_help_text(
            [
                "app_name",
                "list",
                "--help"
            ],
            test_data.help_details_list
        )

    def test_help_search_specific(self):
        """Acceptance: Detailed help using "-h" after "search" action."""
        self.verify_help_text(
            [
                "app_name",
                "search",
                "--help"
            ],
            test_data.help_details_search
        )

