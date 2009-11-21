# -*- coding: utf-8 -*-
"""Acceptance tests for Tomtom. This defines the use cases and expected results."""
import unittest
import sys
import os
import StringIO
import mox

import tomtom
import dbus
import test_data

class AcceptanceTests(unittest.TestCase):
    """
    Acceptance tests.

    What is the expected behaviour from the user point of view.
    """
    def setUp(self):
        self.old_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        self.old_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()
        self.old_argv = sys.argv
        self.m = mox.Mox()

        # Mock out the entire dbus interaction so that acceptance tests don't depend on
        # external code.
        self.old_SessionBus = dbus.SessionBus
        self.old_Interface = dbus.Interface
        dbus.SessionBus = self.m.CreateMockAnything()
        dbus.Interface = self.m.CreateMockAnything()
        session_bus = self.m.CreateMockAnything()
        dbus_object = self.m.CreateMockAnything()
        self.dbus_interface = self.m.CreateMockAnything()

        dbus.SessionBus().AndReturn(session_bus)
        session_bus.get_object("org.gnome.Tomboy", "/org/gnome/Tomboy/RemoteControl").AndReturn(dbus_object)
        dbus.Interface(dbus_object, "org.gnome.Tomboy.RemoteControl").AndReturn(self.dbus_interface)

    def tearDown(self):
        sys.stderr = self.old_stderr
        sys.stdout = self.old_stdout
        sys.argv = self.old_argv
        dbus.SessionBus = self.old_SessionBus
        dbus.Interface = self.old_Interface
        self.m.UnsetStubs()

    def mock_out_listing(self, notes):
        """Create mocks for note listing via dbus."""
        self.dbus_interface.ListAllNotes().AndReturn([n.uri for n in notes])
        for note in notes:
            self.dbus_interface.GetNoteTitle(note.uri).AndReturn(note.title)
            self.dbus_interface.GetNoteChangeDate(note.uri).AndReturn(note.date)
            self.dbus_interface.GetTagsForNote(note.uri).AndReturn(note.tags)

    def mock_out_get_notes_by_names(self, notes):
        """Create mocks for searching for notes by their names."""
        for note in notes:
            self.dbus_interface.FindNote(note.title).AndReturn(note.uri)

        for note in notes:
            self.dbus_interface.GetNoteChangeDate(note.uri).AndReturn(note.date)
            self.dbus_interface.GetTagsForNote(note.uri).AndReturn(note.tags)

    def test_no_argument(self):
        """Acceptance: Application called without arguments must print usage."""
        sys.argv = ["app_name", ]
        tomtom.main()
        self.assertEqual(
            os.linesep.join([
                test_data.help_usage,
                "",
                test_data.help_more_details,
            ]) + os.linesep,
            sys.stdout.getvalue()
        )

    def test_unknown_action(self):
        """Acceptance: Giving an unknown action name must print an error."""
        sys.argv = ["app_name", "unexistant_action"]
        tomtom.main()
        self.assertEqual(
            "app_name: unexistant_action is not a valid action. Use option -h for a list of available actions." + os.linesep,
            sys.stderr.getvalue()
        )

    def test_action_list(self):
        """Acceptance: Action "list" should print a list of the last 10 notes."""
        self.mock_out_listing(test_data.full_list_of_notes[:10])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "list"]
        tomtom.main()
        self.assertEquals(test_data.expected_list + os.linesep, sys.stdout.getvalue())

        self.m.VerifyAll()

    def test_full_list(self):
        """Acceptance: Action "list" with "-a" argument should produce a list of all notes."""
        self.mock_out_listing(test_data.full_list_of_notes)

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "list", "-a"]
        tomtom.main()
        self.assertEquals( os.linesep.join([test_data.expected_list, test_data.list_appendix]) + os.linesep, sys.stdout.getvalue() )

        self.m.VerifyAll()

    def test_notes_displaying(self):
        """Acceptance: Action "display" should print the content of the notes which names are given as arguments."""
        todo = test_data.full_list_of_notes[1]
        python_work = test_data.full_list_of_notes[4]
        separator = os.linesep + "==========================" + os.linesep
        note_lines = test_data.note_contents_from_dbus["TODO-list"].split(os.linesep)
        note_lines[0] = "%s  (reminders, pim)" % note_lines[0]
        expected_result_list = [ os.linesep.join(note_lines), test_data.note_contents_from_dbus["python-work"] ]

        self.mock_out_get_notes_by_names([todo, python_work])

        self.dbus_interface.GetNoteContents(todo.uri).AndReturn(test_data.note_contents_from_dbus["TODO-list"])
        self.dbus_interface.GetNoteContents(python_work.uri).AndReturn(test_data.note_contents_from_dbus["python-work"])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "display", "TODO-list", "python-work"]
        tomtom.main()
        self.assertEquals(separator.join(expected_result_list) + os.linesep, sys.stdout.getvalue())

        self.m.VerifyAll()

    def test_note_does_not_exist(self):
        """Acceptance: Specified note non-existant should display an error message."""
        self.dbus_interface.FindNote("unexistant").AndReturn(dbus.String(""))

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "display", "unexistant"]
        tomtom.main()
        self.assertEquals("""Note named "unexistant" not found.""" + os.linesep, sys.stderr.getvalue())

        self.m.VerifyAll()

    def test_display_zero_argument(self):
        """Acceptance: Action "display" with no argument should print an error."""
        sys.argv = ["app_name", "display"]
        tomtom.main()
        self.assertEquals(
            test_data.display_no_note_name_error + os.linesep,
            sys.stderr.getvalue()
        )

    def test_search(self):
        """Acceptance: Action "search" should execute a case independant search within all notes."""
        self.mock_out_listing(test_data.full_list_of_notes)
        for note in test_data.full_list_of_notes:
            self.dbus_interface.GetNoteContents(note.uri).AndReturn(test_data.note_contents_from_dbus[note.title])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "search", "john doe"]
        tomtom.main()
        self.assertEquals(test_data.search_results + os.linesep, sys.stdout.getvalue())

        self.m.VerifyAll()

    def test_search_specific_notes(self):
        """Acceptance: Giving a list of note names to action "search" should restrict the search within those notes."""
        requested_notes = [
            test_data.full_list_of_notes[3],
            test_data.full_list_of_notes[4],
            test_data.full_list_of_notes[6],
        ]

        self.mock_out_get_notes_by_names(requested_notes)
        for note in requested_notes:
            self.dbus_interface.GetNoteContents(note.uri).AndReturn(test_data.note_contents_from_dbus[note.title])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "search", "python"] + [n.title for n in requested_notes]
        tomtom.main()
        self.assertEquals(test_data.specific_search_results + os.linesep, sys.stdout.getvalue())

        self.m.VerifyAll()

    def test_search_zero_arguments(self):
        """Acceptance: Action "search" with no argument must print an error."""
        sys.argv = ["unused_prog_name", "search"]
        tomtom.main()
        self.assertEquals(
            test_data.search_no_argument_error + os.linesep,
            sys.stderr.getvalue()
        )

    def test_help_on_base_level(self):
        """Acceptance: Using "-h" or "--help" alone should print basic help and list actions."""
        sys.argv = ["app_name", "-h"]
        tomtom.main()
        self.assertEquals(
            test_data.help_action_list + os.linesep,
            sys.stdout.getvalue()
        )

    def verify_help_text(self, args, text):
        """Mock out things to expect the application to exit while printing a specified text."""
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
        """Acceptance: Using "-h" or "--help" before an action name should display detailed help for this action."""
        self.verify_help_text(["app_name", "-h", "list"], test_data.help_details_list)

    def test_help_display_specific(self):
        """Acceptance: Detailed help using "-h" or "--help" after "display" action."""
        self.verify_help_text(["app_name", "display", "--help"], test_data.help_details_display)

    def test_help_list_specific(self):
        """Acceptance: Detailed help using "-h" or "--help" after "list" action."""
        self.verify_help_text(["app_name", "list", "--help"], test_data.help_details_list)

    def test_help_search_specific(self):
        """Acceptance: Detailed help using "-h" or "--help" after "search" action."""
        self.verify_help_text(["app_name", "search", "--help"], test_data.help_details_search)

