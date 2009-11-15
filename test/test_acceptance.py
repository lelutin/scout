# -*- coding: utf-8 -*-
"""Acceptance tests for Tomtom. This defines the use cases and expected results"""
import unittest
import sys
import StringIO

import tomtom
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

    def tearDown(self):
        sys.stdout = self.old_stdout
        sys.argv = self.old_argv

    def test_no_argument(self):
        """ Acceptance: Application called without arguments should print a list of the last 10 notes """
        sys.argv = ["unused_prog_name", ]
        tomtom.main()
        self.assertEquals(test_data.expected_list + "\n", sys.stdout.getvalue())

    def test_only_note_name(self):
        """ Acceptance: Only note name is passed as argument : display the note """
        sys.argv = ["unused_prog_name", "TODO-list"]
        tomtom.main()
        self.assertEquals(test_data.expected_note_content + "\n", sys.stdout.getvalue())

    def test_note_does_not_exist(self):
        """ Acceptance: Specified note non-existant should display an error message """
        sys.argv = ["unused_prog_name", "unexistant"]
        tomtom.main()
        self.assertEquals("Note named \"unexistant\" not found.\n", sys.stdout.getvalue())

    def test_full_list(self):
        """ Acceptance: -l argument should produce a list of all articles """
        sys.argv = ["unused_prog_name", "-l"]
        tomtom.main()
        self.assertEquals(test_data.expected_list + test_data.list_appendix + "\n", sys.stdout.getvalue())

    def test_search(self):
        """ Acceptance: -s argument should execute a case independant search within all notes """
        sys.argv = ["unused_prog_name", "-s", "john doe"]
        tomtom.main()
        self.assertEquals(test_data.search_results + "\n", sys.stdout.getvalue())

    def test_search_specific_notes(self):
        """ Acceptance: Giving a space separated list of note names should restrict search within those notes """
        sys.argv = ["unused_prog_name", "-s", "python", "dell 750", "python-work", "OpenSource Conference X"]
        tomtom.main()
        self.assertEquals(test_data.specific_search_results + "\n", sys.stdout.getvalue())

