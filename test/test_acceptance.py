# -*- coding: utf-8 -*-
"""Acceptance tests for Tomtom. This defines the use cases and expected results"""
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
    Acceptance tests: what is the expected behaviour from the
    user point of view.
    """
    def setUp(self):
        self.old_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
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
        sys.stdout = self.old_stdout
        sys.argv = self.old_argv
        dbus.SessionBus = self.old_SessionBus
        dbus.Interface = self.old_Interface
        self.m.UnsetStubs()

    def test_no_argument(self):
        """ Acceptance: Application called without arguments should print a list of the last 10 notes """
        # Mock out dbus interaction for note listing
        #TODO really mock things out
        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", ]
        tomtom.main()
        self.assertEquals(test_data.expected_list + "\n", sys.stdout.getvalue())

    def test_only_note_name(self):
        """ Acceptance: Only note name is passed as argument : display the note """
        # Mock out dbus interaction for note fetching
        #TODO really mock things out
        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "TODO-list"]
        tomtom.main()
        self.assertEquals(test_data.expected_note_content + "\n", sys.stdout.getvalue())

    def test_note_does_not_exist(self):
        """ Acceptance: Specified note non-existant should display an error message """
        # Mock out dbus interaction for note fetching
        #TODO really mock things out
        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "unexistant"]
        tomtom.main()
        self.assertEquals("Note named \"unexistant\" not found.\n", sys.stdout.getvalue())

    def test_full_list(self):
        """ Acceptance: -l argument should produce a list of all articles """
        # Mock out dbus note list fetching:
        self.dbus_interface.ListAllNotes().AndReturn([n.uri for n in test_data.full_list_of_notes])
        for note in test_data.full_list_of_notes:
            self.dbus_interface.GetNoteTitle(note.uri).AndReturn(note.title)
            self.dbus_interface.GetNoteChangeDate(note.uri).AndReturn(note.date)
            self.dbus_interface.GetTagsForNote(note.uri).AndReturn(note.tags)

        self.m.ReplayAll()

        # Now test the application
        sys.argv = ["unused_prog_name", "-l"]
        tomtom.main()
        self.assertEquals( os.linesep.join([test_data.expected_list, test_data.list_appendix]) + os.linesep, sys.stdout.getvalue() )

    def test_search(self):
        """ Acceptance: -s argument should execute a case independant search within all notes """
        # Mock out dbus interaction for searching in notes
        #TODO really mock things out
        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "-s", "john doe"]
        tomtom.main()
        self.assertEquals(test_data.search_results + "\n", sys.stdout.getvalue())

    def test_search_specific_notes(self):
        """ Acceptance: Giving a space separated list of note names should restrict search within those notes """
        # Mock out dbus interaction for searching in notes
        #TODO really mock things out
        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "-s", "python", "dell 750", "python-work", "OpenSource Conference X"]
        tomtom.main()
        self.assertEquals(test_data.specific_search_results + "\n", sys.stdout.getvalue())

