# -*- coding: utf-8 -*-
"""Application tests"""
import unittest
import mox

import test_data

class TestListing(unittest.TestCase):
    """
    Tests in relation to code that handles the notes and lists them.
    """
    def setUp(self):
        """setup a mox factory"""
        self.m = mox.Mox()

    def test_list_notes(self):
        """Listing receives a list of notes"""
        tt = Tomtom()
        fake_list = self.m.CreateMock(list)

        self.m.StubOutWithMock(tt, "listing")
        self.m.StubOutWithMock(tt, "get_all_notes")
        tt.get_all_notes().AndReturn(fake_list)
        tt.listing(fake_list)
        
        self.m.ReplayAll()

        tt.list_all_notes()

        self.m.VerifyAll()


