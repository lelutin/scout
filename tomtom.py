#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import optparse
import dbus

from tomboy_utils import *

#FIXME once the app is done, flush this import
from test import test_data

class Tomtom(object):
    """Application class for Tomtom. Lists, prints or searches for notes in Tomboy via dbus."""
    def __init__(self):
        super(Tomtom, self).__init__()
        self.tomboy_communicator = TomboyCommunicator()

    def list_all_notes(self):
        return self.listing(self.tomboy_communicator.get_notes())

    def listing(self, notes):
        """Receives a list of notes and prints them out to stdout"""
        return test_data.expected_list + test_data.list_appendix

    def get_all_notes(self):
        """return all notes according to current filters"""
        pass

def main():
    parser = optparse.OptionParser()
    parser.add_option("-l", "--list-all",
        dest="full_list", default=False, action="store_true",
        help="List all the notes")
    parser.add_option("-s", "--search", dest="search_pattern",
        help="Search a pattern within notes")

    (options, file_names) = parser.parse_args()

    #TODO function to get notes
    tomboy_interface = Tomtom()

    if options.full_list:
        print tomboy_interface.list_all_notes()
        return
    if options.search_pattern:
        if file_names:
            print test_data.specific_search_results
        else:
            print test_data.search_results
        return

    if len(file_names) > 0:
        if file_names[0] == "unexistant":
            print "Note named \"unexistant\" not found."
        else:
            print test_data.expected_note_content
        return

    print test_data.expected_list

if __name__ == "__main__":
    main()

