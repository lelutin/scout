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

from tomtom import *
import cli

import test_data
from test_utils import *

def stub_constructor(self):
    """Dummy function used to stub out constructors."""
    pass

def without_constructor(cls):
    """Stub out the constructor of a class.

    Remove external dependencies wihin a class' __init__ function.

    Arguments:
        cls -- The class to be instantiated without constructor

    """
    old_constructor = cls.__init__
    cls.__init__ = stub_constructor
    instance = cls()
    cls.__init__ = old_constructor
    return instance

def verify_get_notes(self, tc, notes, note_names=[]):
    """Verify the outcome of TomboyCommunicator.get_notes().

    This function verifies if notes received from calling
    TomboyCommunicator.get_notes are what we expect them to be. It provokes the
    unit test to fail in case of discordance.

    TomboyNotes are unhashable so we need to convert them to dictionaries
    and check for list membership.

    Arguments:
        self       -- The TestCase instance
        tc         -- TomboyCommunicator mock object instance
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
    for note in tc.get_notes(names=note_names):
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

class TestMain(BasicMocking, CLIMocking):
    """Tests for functions in the main script.

    This test case verifies that functions in the main script behave as
    expected.

    """
    def test_NoteNotFound_exceptions_are_handled(self):
        """Main: NoteNotFound exceptions dont't go unhandled."""
        """This code resembles the acceptance test...

        Yes, the test is very similar in nature to the acceptance test named
        "test_note_does_not_exist". So, why have it repeated? The other test is
        a use case, meant to define that an error message is expected when a
        note is note found, while this one is a unit test meant to verify that
        the code in charge of handling the NoteNotFound exception does so.

        Plus, testing that the exception is handled in this function makes sure
        that it will always be handled without requiring implicitly that the
        actions to do so.

        """
        self.m.StubOutWithMock(cli, "dispatch")

        cli.dispatch("action", [])\
            .AndRaise( NoteNotFound("unexistant") )

        self.m.ReplayAll()

        sys.argv = ["app_name", "action"]
        self.assertRaises(SystemExit, cli.main)
        self.assertEqual(
            test_data.unexistant_note_error + os.linesep,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_dispatch_handles_lack_of_perform_action(self):
        """Main: Warn the user if perform_action is not found in a module."""
        """Call dispatch and verify that it prints an error and exits.

        Dispatch must fail in a gracious manner. It should print an error
        message to the standard output and exit with an error code when
        something goes wrong.

        """
        self.m.StubOutWithMock(cli, "action_dynamic_load")
        module = self.m.CreateMockAnything()
        arguments = self.m.CreateMockAnything()
        action = "action"

        # Mock out the module
        cli.action_dynamic_load(action)\
            .AndReturn(module)

        # Make the action call raise the exception we want to observe.
        module.perform_action(arguments)\
            .AndRaise(AttributeError)

        self.m.ReplayAll()

        # Fake a value for sys.argv[0] (the application name)
        sys.argv = ["app_name", ]

        # And make sure that we get a well formatted error message, and that
        # the exception does not come out of dispatch.
        self.assertRaises(SystemExit, cli.dispatch, action, arguments )
        self.assertEqual(
            test_data.malformed_action_module_error + os.linesep,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_action_dynamic_load_handles_SyntaxError(self):
        """Main: Warn the user that an action has a syntax error."""
        action_name = "action"

        import __builtin__
        self.m.StubOutWithMock(__builtin__, "__import__")
        self.m.StubOutWithMock(__builtin__, "globals")
        self.m.StubOutWithMock(__builtin__, "locals")

        global_vars = __builtin__.globals()\
                        .AndReturn( self.m.CreateMockAnything() )
        local_vars = __builtin__.locals()\
                        .AndReturn( self.m.CreateMockAnything() )

        __builtin__.__import__(
            "tomtom.actions",
            global_vars,
            local_vars,
            [action_name, ]
        ).AndRaise(SyntaxError)

        self.m.ReplayAll()

        # Fake a value for sys.argv[0] (the application name)
        sys.argv = ["app_name", ]

        self.assertRaises(SystemExit, cli.action_dynamic_load, action_name)
        self.assertEqual(
            test_data.syntax_error_message + os.linesep,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_arguments_converted_to_unicode(self):
        """Main: Arguments to action are converted to unicode objects."""
        arguments = ["arg1", "arg2"]
        sys.argv = ["app_name", "action"] + arguments

        self.m.StubOutWithMock(cli, "dispatch")

        cli.dispatch("action", [unicode(arg) for arg in arguments] )

        self.m.ReplayAll()

        cli.main()

        self.m.VerifyAll()

    def test_ConnectionError_is_handled(self):
        """Main: ConnectionError should print an error message."""
        self.m.StubOutWithMock(cli, "dispatch")

        cli.dispatch("action", [])\
            .AndRaise( ConnectionError("there was a problem") )

        self.m.ReplayAll()

        sys.argv = ["app_name", "action"]
        self.assertRaises(SystemExit, cli.main)
        self.assertEqual(
            test_data.connection_error_message + os.linesep,
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

class TestUtilities(BasicMocking):
    """Tests for general code.

    This test case must containt tests for code that is not directly linked
    with one particular feature.

    """
    def test_tomboy_communicator_is_initialized(self):
        """Utilities: Tommtom constructor instatiates TomboyCommunicator."""
        """Avoid calling TomboyCommunicator's constructor.

        TomboyCommunicator's constructor creates a dbus connection and it must
        be abstracted to testing purposes.

        "without_constructor" cannot be used here to replace the constructor
        because we are testing whether Tomtom's constructor instantiates a
        TomboyCommunicator

        """
        old_constructor = TomboyCommunicator.__init__
        TomboyCommunicator.__init__ = stub_constructor
        self.assertTrue( isinstance(
            Tomtom().tomboy_communicator,
            TomboyCommunicator
        ) )
        TomboyCommunicator.__init__ = old_constructor

    def test_TomboyCommunicator_constructor(self):
        """Utilities: TomboyCommunicator's dbus interface is initialized."""
        old_SessionBus = dbus.SessionBus
        dbus.SessionBus = self.m.CreateMockAnything()
        old_Interface = dbus.Interface
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

        self.assertEqual( dbus_interface, TomboyCommunicator().comm )

        self.m.VerifyAll()
        dbus.SessionBus = old_SessionBus
        dbus.Interface = old_Interface

    def test_TomboyNote_constructor(self):
        """Utilities: TomboyNote initializes its instance variables."""
        uri1 = "note://something-like-this"
        title = "Name"
        date_int64 = dbus.Int64()
        tags = ["tag1", "tag2"]
        # Construct with all data and a dbus.Int64 date
        tn = TomboyNote(uri=uri1, title=title, date=date_int64, tags=tags)

        self.assertEqual(uri1, tn.uri)
        self.assertEqual(title, tn.title)
        self.assertEqual(date_int64, tn.date)
        # Order is not important
        self.assertEqual( set(tags), set(tn.tags) )

        # Construct with only uri, rest is default
        uri2 = "note://another-false-uri"
        tn = TomboyNote(uri=uri2)
        self.assertEqual(tn.uri, uri2)
        self.assertEqual(tn.title, "")
        self.assertEqual(tn.date, dbus.Int64() )
        self.assertEqual(tn.tags, [])

        # One more thing: the date can be entered with a datetime.datetime
        datetime_date = datetime.datetime(2009, 11, 13, 18, 42, 23)
        tn = TomboyNote(uri="not important", date=datetime_date)

        self.assertEqual(
            dbus.Int64(
                time.mktime( datetime_date.timetuple() )
            ),
            tn.date
        )

    def test_get_notes_by_name(self):
        """Utilities: TomboyCommunicator gets a list of given named notes."""
        tc = without_constructor(TomboyCommunicator)
        todo = test_data.full_list_of_notes[1]
        recipes = test_data.full_list_of_notes[11]
        notes = [todo, recipes]
        names = [n.title for n in notes]

        self.m.StubOutWithMock(tc, "get_uris_by_name")
        tc.get_uris_by_name(names)\
            .AndReturn([(todo.uri,todo.title), (recipes.uri, recipes.title)])
        tc.comm = self.m.CreateMockAnything()
        tc.comm.GetNoteChangeDate(todo.uri)\
            .AndReturn(todo.date)
        tc.comm.GetTagsForNote(todo.uri)\
            .AndReturn(todo.tags)
        tc.comm.GetNoteChangeDate(recipes.uri)\
            .AndReturn(recipes.date)
        tc.comm.GetTagsForNote(recipes.uri)\
            .AndReturn(recipes.tags)

        self.m.ReplayAll()

        verify_get_notes(self, tc, notes, note_names=names)

        self.m.VerifyAll()

    def test_get_uris_by_name(self):
        """Utilities: TomboyCommunicator determines uris by names."""
        tc = without_constructor(TomboyCommunicator)
        r_n_d = test_data.full_list_of_notes[12]
        webpidgin = test_data.full_list_of_notes[9]
        names = [r_n_d.title, webpidgin.title]

        tc.comm = self.m.CreateMockAnything()
        tc.comm.FindNote(r_n_d.title)\
            .AndReturn(r_n_d.uri)
        tc.comm.FindNote(webpidgin.title)\
            .AndReturn(webpidgin.uri)

        self.m.ReplayAll()

        self.assertEqual(
            [(r_n_d.uri, r_n_d.title), (webpidgin.uri, webpidgin.title)],
            tc.get_uris_by_name(names)
        )

        self.m.VerifyAll()

    def test_get_uris_by_name_unexistant(self):
        """Utilities: TomboyCommunicator raises a NoteNotFound exception."""
        tc = without_constructor(TomboyCommunicator)
        tc.comm = self.m.CreateMockAnything()

        tc.comm.FindNote("unexistant")\
            .AndReturn(dbus.String(""))

        self.m.ReplayAll()

        self.assertRaises(NoteNotFound, tc.get_uris_by_name, ["unexistant"] )

        self.m.VerifyAll()

    def test_dbus_session_not_available(self):
        """Utilities: Raise an exception on dbus session creation problem."""
        old_SessionBus = dbus.SessionBus
        dbus.SessionBus = self.m.CreateMockAnything()

        dbus.SessionBus()\
            .AndRaise( Exception("something happened") )

        self.m.ReplayAll()

        # Do this one by hand. It is a tricky test: if the first try block
        # doesn't raise the proper exception, it will still get raised on the
        # second try block because it was not mocked out. We need to make sure
        # that the content of the exception is the right one.
        try:
            tc = TomboyCommunicator()
        except ConnectionError, e:
            self.assertEqual(
                test_data.dbus_session_exception_text,
                e.__str__()
            )
        else:
            # Make sure the second call was setup correctly
            self.fail("Exception ConnectionError was never raised")

        self.m.VerifyAll()
        dbus.SessionBus = old_SessionBus

    def test_dbus_Tomboy_communication_problem(self):
        """Utilities: Raise an exception if linking dbus with Tomboy failed."""
        old_SessionBus = dbus.SessionBus
        dbus.SessionBus = self.m.CreateMockAnything()
        old_Interface = dbus.Interface
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
        ).AndRaise( Exception("cosmos error") )

        self.m.ReplayAll()

        try:
            tc = TomboyCommunicator()
        except ConnectionError, e:
            self.assertEqual(
                test_data.dbus_interface_exception_text,
                e.__str__()
            )
        else:
            self.fail("Exception ConnectionError was never raised")

        self.m.VerifyAll()
        dbus.SessionBus = old_SessionBus
        dbus.Interface = old_Interface

class TestListing(BasicMocking):
    """Tests for code that handles the notes and lists them."""
    def test_list_all_notes(self):
        """Listing: Retrieve a list of all notes."""
        tt = without_constructor(Tomtom)
        tt.tomboy_communicator = self.m.CreateMock(TomboyCommunicator)
        fake_list = self.m.CreateMock(list)
        self.m.StubOutWithMock(tt, "listing")
        self.m.StubOutWithMock(tt.tomboy_communicator, "get_notes")

        tt.tomboy_communicator.get_notes(None)\
            .AndReturn(fake_list)
        tt.listing(fake_list)

        self.m.ReplayAll()

        tt.list_notes()

        self.m.VerifyAll()

    def test_get_uris_for_n_notes_no_limit(self):
        """Listing: Given no limit, get all the notes' uris."""
        tc = without_constructor(TomboyCommunicator)
        tc.comm = self.m.CreateMockAnything()

        list_of_uris = dbus.Array(
            [note.uri for note in test_data.full_list_of_notes]
        )

        tc.comm.ListAllNotes()\
            .AndReturn( list_of_uris )

        self.m.ReplayAll()

        self.assertEqual(
            [(uri, None) for uri in list_of_uris],
            tc.get_uris_for_n_notes(None)
        )

        self.m.VerifyAll()

    def test_get_uris_for_n_notes(self):
        """Listing: Given a numerical limit, get the n latest notes' uris."""
        tc = without_constructor(TomboyCommunicator)

        list_of_uris = dbus.Array(
            [note.uri for note in test_data.full_list_of_notes]
        )
        tc.comm = self.m.CreateMockAnything()
        tc.comm.ListAllNotes()\
            .AndReturn( list_of_uris )

        self.m.ReplayAll()

        self.assertEqual(
            [(uri, None) for uri in list_of_uris[:6] ],
            tc.get_uris_for_n_notes(6)
        )

        self.m.VerifyAll()

    def test_get_notes(self):
        """Listing: Get listing information for all the notes from Tomboy."""
        tc = without_constructor(TomboyCommunicator)

        tc.comm = self.m.CreateMockAnything()
        self.m.StubOutWithMock(tc, "get_uris_for_n_notes")
        self.m.StubOutWithMock(tc.comm, "ListAllNotes")
        self.m.StubOutWithMock(tc.comm, "GetNoteTitle")
        self.m.StubOutWithMock(tc.comm, "GetNoteChangeDate")
        self.m.StubOutWithMock(tc.comm, "GetTagsForNote")
        list_of_uris = dbus.Array(
            [note.uri for note in test_data.full_list_of_notes]
        )

        tc.get_uris_for_n_notes(None)\
            .AndReturn( [(u, None) for u in list_of_uris] )
        for note in test_data.full_list_of_notes:
            tc.comm.GetNoteTitle(note.uri)\
                .AndReturn(note.title)
            tc.comm.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            tc.comm.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

        self.m.ReplayAll()

        verify_get_notes(self, tc, test_data.full_list_of_notes)

        self.m.VerifyAll()

    def test_note_listing(self):
        """Listing: Get the information on a list of notes."""
        tt = without_constructor(Tomtom)
        for note in test_data.full_list_of_notes:
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
            tt.listing(test_data.full_list_of_notes)
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
        date_64 = dbus.Int64(1254553804L)
        note = TomboyNote(
            uri="note://tomboy/fake-uri",
            title=title,
            date=date_64,
            tags=tags
        )
        expected_listing = "2009-10-03 | %(title)s%(tags)s" % {
            "title": new_title,
            "tags": expected_tag_text
        }

        self.m.ReplayAll()

        self.assertEqual( expected_listing, note.listing() )

        self.m.VerifyAll()

    def test_TomboyNote_listing(self):
        """Listing: Print one note's information."""
        self.verify_note_listing(
            "Test",
            ["tag1", "tag2"],
            "Test",
            "  (tag1, tag2)"
        )

    def test_TomboyNote_listing_no_title_no_tags(self):
        """Listing: Verify listing format with no title and no tags."""
        self.verify_note_listing(
            "",
            [],
            "_note doesn't have a name_",
            ""
        )

class TestDisplay(BasicMocking):
    """Tests for code that display notes' content."""
    def test_get_display_for_notes(self):
        """Display: Tomtom returns notes' contents, separated a marker."""
        tt = without_constructor(Tomtom)
        tt.tomboy_communicator = self.m.CreateMock(TomboyCommunicator)
        notes = [
            test_data.full_list_of_notes[10],
            test_data.full_list_of_notes[8]
        ]
        note_names = [n.title for n in notes]
        note1_content = test_data.note_contents_from_dbus[ notes[0].title ]
        note2_content = test_data.note_contents_from_dbus[ notes[1].title ]

        tt.tomboy_communicator.get_notes(names=note_names)\
            .AndReturn(notes)
        tt.tomboy_communicator.get_note_content(notes[0])\
            .AndReturn(note1_content)
        tt.tomboy_communicator.get_note_content(notes[1])\
            .AndReturn(note2_content)

        self.m.ReplayAll()

        self.assertEqual(
            os.linesep.join([
                note1_content,
                test_data.display_separator,
                note2_content,
            ]),
            tt.get_display_for_notes(note_names)
        )

        self.m.VerifyAll()

    def test_TomboyCommunicator_get_note_content(self):
        """Display: Using the communicator, get one note's content."""
        tc = without_constructor(TomboyCommunicator)
        tc.comm = self.m.CreateMockAnything()

        note = test_data.full_list_of_notes[12]
        raw_content = test_data.note_contents_from_dbus[note.title]
        lines = raw_content.splitlines()
        lines[0] = "%s%s" % (lines[0], "  (reminders, training)")
        expected_result = os.linesep.join(lines)

        tc.comm.GetNoteContents(note.uri)\
            .AndReturn( raw_content )

        self.m.ReplayAll()

        self.assertEqual( expected_result, tc.get_note_content(note) )

        self.m.VerifyAll()

class TestSearch(BasicMocking):
    """Tests for code that perform a textual search within notes."""
    def test_search_for_text(self):
        """Search: Tomtom triggers a search through requested notes."""
        tt = without_constructor(Tomtom)
        tt.tomboy_communicator = self.m.CreateMockAnything()

        note_contents = {}
        for note in test_data.full_list_of_notes:
            content = test_data.note_contents_from_dbus[note.title]

            if note.tags:
                lines = content.splitlines()
                lines[0] =  "%s  (%s)" % (lines[0], ", ".join(note.tags) )
                content = os.linesep.join(lines)

            note_contents[note.title] = content

        expected_result = [
            {
                "title": "addressbook",
                "line": 5,
                "text": "John Doe (cell) - 555-5512",
            },
            {
                "title": "business contacts",
                "line": 7,
                "text": "John Doe Sr. (office) - 555-5534",
            },
        ]

        tt.tomboy_communicator.get_notes(names=[])\
            .AndReturn(test_data.full_list_of_notes)
        for note in test_data.full_list_of_notes:
            tt.tomboy_communicator.get_note_content(note)\
                .AndReturn(note_contents[note.title])

        self.m.ReplayAll()

        self.assertEqual(
            expected_result,
            tt.search_for_text(search_pattern="john doe")
        )

        self.m.VerifyAll()

