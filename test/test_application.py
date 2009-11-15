# -*- coding: utf-8 -*-
"""Application tests"""
import unittest
import mox

from tomtom import *
import datetime
import time
import dbus
import test_data

class TestListing(unittest.TestCase):
    """Tests in relation to code that handles the notes and lists them"""
    def stub_constructor(self):
        pass

    def without_constructor(self, cls):
        """Stub out the constructor of a class to remove external dependancy to its __init__ function"""
        old_constructor = cls.__init__
        cls.__init__ = self.stub_constructor
        instance = cls()
        cls.__init__ = old_constructor
        return instance

    def setUp(self):
        """setup a mox factory"""
        self.m = mox.Mox()

    def tearDown(self):
        """Remove stubs"""
        self.m.UnsetStubs()

    def test_list_notes(self):
        """Listing receives a list of notes"""
        tt = self.without_constructor(Tomtom)
        tt.tomboy_communicator = self.m.CreateMock(TomboyCommunicator)
        fake_list = self.m.CreateMock(list)
        self.m.StubOutWithMock(tt, "listing")
        self.m.StubOutWithMock(tt.tomboy_communicator, "get_notes")

        tt.tomboy_communicator.get_notes().AndReturn(fake_list)
        tt.listing(fake_list)
        
        self.m.ReplayAll()

        tt.list_all_notes()

        self.m.VerifyAll()

    def test_tomboy_communicator_is_initialized(self):
        """A fresh Tommtom instance should have its Tomboy communicator initiated"""
        # Avoid calling the Communicator's constructor as it creates a dbus connection
        old_constructor = TomboyCommunicator.__init__
        TomboyCommunicator.__init__ = self.stub_constructor
        self.assertTrue( isinstance(Tomtom().tomboy_communicator, TomboyCommunicator) )
        TomboyCommunicator.__init__ = old_constructor

    def test_TomboyCommunicator_constructor(self):
        """Communicator must be initialized upon instatiation"""
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

    def test_get_notes(self):
        """Construct a list of all the notes"""
        tomboy_communicator = self.without_constructor(TomboyCommunicator)

        tomboy_communicator.comm = self.m.CreateMockAnything()
        self.m.StubOutWithMock(tomboy_communicator.comm, "ListAllNotes")
        self.m.StubOutWithMock(tomboy_communicator.comm, "GetNoteTitle")
        self.m.StubOutWithMock(tomboy_communicator.comm, "GetNoteChangeDate")
        self.m.StubOutWithMock(tomboy_communicator.comm, "GetTagsForNote")
        list_of_uris = dbus.Array([note.uri for note in test_data.full_list_of_notes])
        tomboy_communicator.comm.ListAllNotes().AndReturn( list_of_uris )
        for note in [n for n in test_data.full_list_of_notes if "Template" not in n.title]:
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

    def test_TomboyNote_constructor(self):
        """A new note initialized with data should initialize its instance variables"""
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

    def pending_test_note_listing(self):
        """Listing of a list of notes"""
        #TODO test Tomtom.listing
        pass

