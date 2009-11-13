# -*- coding: utf-8 -*-
"""Application tests"""
import unittest
import mox

from tomtom import Tomtom, TomboyCommunicator
import test_data

class TestListing(unittest.TestCase):
    """Tests in relation to code that handles the notes and lists them"""
    def setUp(self):
        """setup a mox factory"""
        self.m = mox.Mox()

    def test_list_notes(self):
        """Listing receives a list of notes"""
        tt = Tomtom()
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
        self.assertTrue( isinstance(Tomtom().tomboy_communicator, TomboyCommunicator) )

    def test_TomboyCommunicator_constructor(self):
        """Communicator must be initialized upon instatiation"""
        #TODO test TomboyCommunicator.__init__
        pass

    def test_get_notes(self):
        """Get a list of all the notes"""
        tomboy_communicator = self.m.CreateMock(TomboyCommunicator)
        #What does it need to use?

        self.m.ReplayAll()

        #TODO this needs to be done
        #self.assertEquals( test_data.full_list_of_notes, tomboy_communicator.get_notes() )

        self.m.VerifyAll()
    
    def test_note_listing(self):
        """Listing of a list of notes"""
        #TODO test Tomtom.listing
        pass

