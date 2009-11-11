#!/bin/env python
# -*- coding: utf-8 -*-
import unittest
import sys
import StringIO

import tomtom

expected_list = \
"""2009-10-20 | addressbook  (pim)
2009-10-20 | TODO-list  (reminders)
2009-10-14 | Bash  (reminders)
2009-10-11 | dell 750  (projects)
2009-10-07 | python-work  (projects)
2009-10-05 | TDD  (reminders)
2009-10-04 | OpenSource Conference X  (conferences)
2009-10-04 | business cards  (pim)
2009-10-03 | japanese  (reminders)
2009-10-02 | Webpidgin  (projects)"""

list_appendix = \
"""2009-09-27 | conquer the world  (projects)
2009-09-21 | recipies  (pim)
2009-09-20 | R&D  (reminders)"""

search_results = \
"""addressbook : 35 : John Doe (cell) - 555-5512
business cards : 21 : John Doe Sr. (office) - 555-5534"""

specific_search_results = \
"""dell 750 : 12 : Install python 2.5
python-work : 2 : to use a python buildbot for automatic bundling
OpenSource Conference X : 120 : Presentation: Python by all means"""

expected_note_content = \
"""TODO

Build unit tests for tomtom
Chew up some gum
Play pool with the queen of england"""

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
        self.assertEquals(expected_list + "\n", sys.stdout.getvalue())

    def test_only_note_name(self):
        """ Acceptance: Only note name is passed as argument : display the note """
        sys.argv = ["unused_prog_name", "TODO"]
        tomtom.main()
        self.assertEquals(expected_note_content + "\n", sys.stdout.getvalue())

    def test_note_does_not_exist(self):
        """ Acceptance: Specified note non-existant should display an error message """
        sys.argv = ["unused_prog_name", "unexistant"]
        tomtom.main()
        self.assertEquals("Note named \"unexistant\" not found.\n", sys.stdout.getvalue())

    def test_full_list(self):
        """ Acceptance: -l argument should produce a list of all articles """
        sys.argv = ["unused_prog_name", "-l"]
        tomtom.main()
        self.assertEquals(expected_list + list_appendix + "\n", sys.stdout.getvalue())

    def test_search(self):
        """ Acceptance: -s argument should execute a case independant search within all notes """
        sys.argv = ["unused_prog_name", "-s", "john doe"]
        tomtom.main()
        self.assertEquals(search_results + "\n", sys.stdout.getvalue())

    def test_search_specific_notes(self):
        """ Acceptance: Giving a space separated list of note names should restrict search within those notes """
        sys.argv = ["unused_prog_name", "-s", "python", "dell 750", "python-work", "OpenSource Conference X"]
        tomtom.main()
        self.assertEquals(specific_search_results + "\n", sys.stdout.getvalue())

class TestListing(unittest.TestCase):
    """
    Tests in relation to code that handles the notes and lists them.
    """
    def test_list_notes(self):
        self.assertTrue(False)

if __name__ == "__main__":
    unittest.main()

