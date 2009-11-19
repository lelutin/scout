# -*- coding: utf-8 -*-
"""Application tests"""
import unittest
import mox

import os
from tomtom import *
import datetime
import time
import dbus
import test_data

def stub_constructor(self):
    """Dummy function used to stub out constructors"""
    pass

def without_constructor(cls):
    """Stub out the constructor of a class to remove external dependancy to its __init__ function"""
    old_constructor = cls.__init__
    cls.__init__ = stub_constructor
    instance = cls()
    cls.__init__ = old_constructor
    return instance

class TestApplication(unittest.TestCase):
    """Tests for code not directly related to one particular feature"""
    def setUp(self):
        """setup a mox factory"""
        self.m = mox.Mox()

    def tearDown(self):
        """Remove stubs"""
        self.m.UnsetStubs()

    def test_tomboy_communicator_is_initialized(self):
        """Tomtom: A fresh Tommtom instance should have its Tomboy communicator initiated"""
        # Avoid calling the Communicator's constructor as it creates a dbus connection
        old_constructor = TomboyCommunicator.__init__
        TomboyCommunicator.__init__ = stub_constructor
        self.assertTrue( isinstance(Tomtom().tomboy_communicator, TomboyCommunicator) )
        TomboyCommunicator.__init__ = old_constructor

    def test_TomboyCommunicator_constructor(self):
        """TomboyCommunicator: Communicator must be initialized upon instatiation"""
        old_SessionBus = dbus.SessionBus
        dbus.SessionBus = self.m.CreateMockAnything()
        old_Interface = dbus.Interface
        dbus.Interface = self.m.CreateMockAnything()
        session_bus = self.m.CreateMockAnything()
        dbus_object = self.m.CreateMockAnything()
        dbus_interface = self.m.CreateMockAnything()

        dbus.SessionBus().AndReturn(session_bus)
        session_bus.get_object("org.gnome.Tomboy", "/org/gnome/Tomboy/RemoteControl").AndReturn(dbus_object)
        dbus.Interface(dbus_object, "org.gnome.Tomboy.RemoteControl").AndReturn(dbus_interface)

        self.m.ReplayAll()

        self.assertEqual( dbus_interface, TomboyCommunicator().comm )

        self.m.VerifyAll()
        dbus.SessionBus = old_SessionBus
        dbus.Interface = old_Interface

    def test_TomboyNote_constructor(self):
        """TomboyNote: A new note should initialize its instance variables"""
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

        self.assertEqual(dbus.Int64(time.mktime(datetime_date.timetuple())), tn.date )

    def test_get_notes_by_name(self):
        """TomboyCommunicator: Get a list of notes specified by names"""
        tc = without_constructor(TomboyCommunicator)
        todo = test_data.full_list_of_notes[1]
        recipes = test_data.full_list_of_notes[11]
        notes = [todo, recipes]
        names = [n.title for n in notes]

        self.m.StubOutWithMock(tc, "get_uris_by_name")
        tc.get_uris_by_name(names).AndReturn([(todo.uri,todo.title), (recipes.uri, recipes.title)])
        tc.comm = self.m.CreateMockAnything()
        tc.comm.GetNoteChangeDate(todo.uri).AndReturn(todo.date)
        tc.comm.GetTagsForNote(todo.uri).AndReturn(todo.tags)
        tc.comm.GetNoteChangeDate(recipes.uri).AndReturn(recipes.date)
        tc.comm.GetTagsForNote(recipes.uri).AndReturn(recipes.tags)

        self.m.ReplayAll()

        # TomboyNotes are unhashable so convert to dictionaries and check for list membership
        expectation = [{"uri":n.uri, "title":n.title, "date":n.date, "tags":n.tags} for n in notes]
        # Order is not important
        for note in tc.get_notes(names=names):
            if not {"uri":note.uri, "title":note.title, "date":note.date, "tags":note.tags} in expectation:
                self.fail("Note named %(title)s dated %(date)s with uri %(uri)s and tags [%(tags)s] not found in expectation: [%(expectation)s]" % {"title": note.title, "date": note.date, "uri": note.uri, "tags": ",".join(note.tags), "expectation": ",".join(expectation)})

        self.m.VerifyAll()

    def test_get_uris_by_name(self):
        """TomboyCommunicator: Get a list of uris by note names"""
        tc = without_constructor(TomboyCommunicator)
        r_n_d = test_data.full_list_of_notes[12]
        webpidgin = test_data.full_list_of_notes[9]
        names = [r_n_d.title, webpidgin.title]

        tc.comm = self.m.CreateMockAnything()
        tc.comm.FindNote(r_n_d.title).AndReturn(r_n_d.uri)
        tc.comm.FindNote(webpidgin.title).AndReturn(webpidgin.uri)

        self.m.ReplayAll()

        self.assertEqual( [(r_n_d.uri, r_n_d.title), (webpidgin.uri, webpidgin.title)], tc.get_uris_by_name(names) )

        self.m.VerifyAll()

    def test_get_uris_by_name_unexistant(self):
        """TomboyCommunicator: If no URI is returned from dbus while searching for a note name, raise an exception"""
        tc = without_constructor(TomboyCommunicator)
        tc.comm = self.m.CreateMockAnything()

        tc.comm.FindNote("unexistant").AndReturn(dbus.String(""))

        self.m.ReplayAll()

        self.assertRaises(NoteNotFound, tc.get_uris_by_name, ["unexistant"] )

        self.m.VerifyAll()

class TestListing(unittest.TestCase):
    """Tests in relation to code that handles the notes and lists them"""
    def setUp(self):
        """setup a mox factory"""
        self.m = mox.Mox()

    def tearDown(self):
        """Remove stubs"""
        self.m.UnsetStubs()

    def test_list_all_notes(self):
        """Listing: Retrieve a list of all notes"""
        tt = without_constructor(Tomtom)
        tt.tomboy_communicator = self.m.CreateMock(TomboyCommunicator)
        fake_list = self.m.CreateMock(list)
        self.m.StubOutWithMock(tt, "listing")
        self.m.StubOutWithMock(tt.tomboy_communicator, "get_notes")

        tt.tomboy_communicator.get_notes(None).AndReturn(fake_list)
        tt.listing(fake_list)
        
        self.m.ReplayAll()

        tt.list_notes()

        self.m.VerifyAll()

    def test_get_uris_for_n_notes_no_limit(self):
        """Listing: Given no limit, get all the notes' uris"""
        tc = without_constructor(TomboyCommunicator)

        list_of_uris = dbus.Array([note.uri for note in test_data.full_list_of_notes])
        tc.comm = self.m.CreateMockAnything()
        tc.comm.ListAllNotes().AndReturn( list_of_uris )

        self.m.ReplayAll()

        self.assertEqual( [(uri, None) for uri in list_of_uris], tc.get_uris_for_n_notes(None) )

        self.m.VerifyAll()

    def test_get_uris_for_n_notes(self):
        """Listing: Given a numerical limit, get the n latest notes' uris"""
        tc = without_constructor(TomboyCommunicator)

        list_of_uris = dbus.Array([note.uri for note in test_data.full_list_of_notes])
        tc.comm = self.m.CreateMockAnything()
        tc.comm.ListAllNotes().AndReturn( list_of_uris )

        self.m.ReplayAll()

        self.assertEqual( [(uri, None) for uri in list_of_uris[:6] ], tc.get_uris_for_n_notes(6) )

        self.m.VerifyAll()

    def test_get_notes(self):
        """Listing: Get listing information for all the notes from Tomboy"""
        tomboy_communicator = without_constructor(TomboyCommunicator)

        tomboy_communicator.comm = self.m.CreateMockAnything()
        self.m.StubOutWithMock(tomboy_communicator, "get_uris_for_n_notes")
        self.m.StubOutWithMock(tomboy_communicator.comm, "ListAllNotes")
        self.m.StubOutWithMock(tomboy_communicator.comm, "GetNoteTitle")
        self.m.StubOutWithMock(tomboy_communicator.comm, "GetNoteChangeDate")
        self.m.StubOutWithMock(tomboy_communicator.comm, "GetTagsForNote")
        list_of_uris = dbus.Array([note.uri for note in test_data.full_list_of_notes])

        tomboy_communicator.get_uris_for_n_notes(None).AndReturn( [(u, None) for u in list_of_uris] )
        for note in test_data.full_list_of_notes:
            tomboy_communicator.comm.GetNoteTitle(note.uri).AndReturn(note.title)
            tomboy_communicator.comm.GetNoteChangeDate(note.uri).AndReturn(note.date)
            tomboy_communicator.comm.GetTagsForNote(note.uri).AndReturn(note.tags)

        self.m.ReplayAll()

        # TomboyNotes are unhashable so convert to dictionaries and check for list membership
        expectation = [{"uri":n.uri, "title":n.title, "date":n.date, "tags":n.tags} for n in test_data.full_list_of_notes]
        # Order is not important
        for note in tomboy_communicator.get_notes():
            if not {"uri":note.uri, "title":note.title, "date":note.date, "tags":note.tags} in expectation:
                self.fail("Note named %(title)s dated %(date)s with uri %(uri)s and tags [%(tags)s] not found in expectation: [%(expectation)s]" % {"title": note.title, "date": note.date, "uri": note.uri, "tags": ",".join(note.tags), "expectation": ",".join(expectation)})

        self.m.VerifyAll()

    def test_note_listing(self):
        """Listing: Printing information on a list of notes"""
        tt = without_constructor(Tomtom)
        for note in test_data.full_list_of_notes:
            self.m.StubOutWithMock(note, "listing")
            tag_text = ""
            if len(note.tags):
                tag_text = "  (" + ", ".join(note.tags) + ")"

            note.listing().AndReturn("%(date)s | %(title)s%(tags)s" %
                {
                    "date": datetime.datetime.fromtimestamp(note.date).isoformat()[:10],
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

    def verify_note_listing(self, title, tags, expected_title, expected_tag_text):
        """Test note listing with a given set of title and tags"""
        date_64 = dbus.Int64(1254553804L)
        note = TomboyNote(uri="note://tomboy/fake-uri", title=title, date=date_64, tags=tags)

        self.m.ReplayAll()

        expected_listing = "2009-10-03 | %(title)s%(tags)s" % {"title": expected_title, "tags": expected_tag_text}
        self.assertEqual( expected_listing, note.listing() )

        self.m.VerifyAll()

    def test_TomboyNote_listing(self):
        """Listing: Print one note's information"""
        self.verify_note_listing("Test", ["tag1", "tag2"], "Test", "  (tag1, tag2)")

    def test_TomboyNote_listing_no_title_no_tags(self):
        """Listing: Print one note's information for special cases: no title, no tags"""
        self.verify_note_listing("", [], "_note doesn't have a name_", "")

class TestDisplay(unittest.TestCase):
    """Tests for code in relation to displaying notes"""
    def setUp(self):
        """Setup a mox factory"""
        self.m = mox.Mox()

    def tearDown(self):
        """Remove stubs"""
        self.m.UnsetStubs()

    def test_get_display_for_notes(self):
        """Display: Tomtom.get_display_for_notes should return the contents of a list of notes separated by break lines"""
        tt = without_constructor(Tomtom)
        tt.tomboy_communicator = self.m.CreateMock(TomboyCommunicator)
        note1 = self.m.CreateMock(TomboyNote)
        note2 = self.m.CreateMock(TomboyNote)
        note_names = ["note1", "note2"]
        note1_expected_content = """note1  (tag1, tag2)

line1"""
        note2_expected_content = """note2

test
teeest
tetest"""

        tt.tomboy_communicator.get_notes(names=note_names).AndReturn([note1, note2])
        tt.tomboy_communicator.get_note_content(note1).AndReturn(note1_expected_content)
        tt.tomboy_communicator.get_note_content(note2).AndReturn(note2_expected_content)

        self.m.ReplayAll()

        self.assertEqual(
            os.linesep.join([note1_expected_content, "==========================", note2_expected_content]),
            tt.get_display_for_notes(note_names)
        )

        self.m.VerifyAll()

    def test_TomboyCommunicator_get_note_content(self):
        """Display: Using the communicator, get the contents of one note"""
        tc = without_constructor(TomboyCommunicator)
        tc.comm = self.m.CreateMockAnything()
        note = self.m.CreateMockAnything()
        note_content_lines = [
            "note_name",
            "",
            "first line of text",
            "second line",
            "and stiiiiirrrrrike!",
        ]
        expected_result = list(note_content_lines)
        expected_result[0] = "%s%s" % (note_content_lines[0], "  (tag1, tag2)")

        tc.comm.GetNoteContents(note.uri).AndReturn( os.linesep.join(note_content_lines) )
        note.tags = ["tag1", "tag2"]

        self.m.ReplayAll()

        self.assertEqual( os.linesep.join(expected_result), tc.get_note_content(note) )

        self.m.VerifyAll()

