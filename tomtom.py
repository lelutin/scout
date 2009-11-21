#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Inspired by : http://arstechnica.com/open-source/news/2007/09/using-the-tomboy-d-bus-interface.ars
#
import sys
import os
import optparse

from tomboy_utils import *

#FIXME once the app is done, flush this import
from test import test_data

class Tomtom(object):
    """Application class for Tomtom. Lists, prints or searches for notes in Tomboy via dbus."""
    def __init__(self):
        super(Tomtom, self).__init__()
        self.tomboy_communicator = TomboyCommunicator()

    def list_notes(self, count_limit=None):
        """Entry point to listing notes. If specified, can limit the number of displayed notes"""
        return self.listing(self.tomboy_communicator.get_notes(count_limit))

    def listing(self, notes):
        """Receives a list of notes and returns information about them"""
        return os.linesep.join( [note.listing() for note in notes] )

    def get_display_for_notes(self, names):
        """Receives a list of note names and returns their contents"""
        notes = self.tomboy_communicator.get_notes(names=names)

        separator = os.linesep + "==========================" + os.linesep
        return separator.join( [self.tomboy_communicator.get_note_content(note) for note in notes] )

def action_list_notes(args):
    """ Use the tomtom object to list notes """
    parser = optparse.OptionParser(usage="%prog list [-h|-a]")
    parser.add_option("-a", "--all",
        dest="full_list", default=False, action="store_true",
        help="List all the notes")

    (options, file_names) = parser.parse_args(args)

    tomboy_interface = Tomtom()

    if options.full_list:
        print tomboy_interface.list_notes()
    else:
        print tomboy_interface.list_notes(count_limit=10)

def action_print_notes(args):
    """ Use the tomtom object to print the content of one or more notes """
    parser = optparse.OptionParser(usage="%prog display [-h] [note_name ...]")
    #parser.add_option("-a", "--all",
    #    dest="full_list", default=False, action="store_true",
    #    help="Display all the notes")

    (options, file_names) = parser.parse_args(args)

    if len(file_names) <= 0:
        print >> sys.stderr, "Error: You need to specify a note name to display it"
        return

    tomboy_interface = Tomtom()

    try:
        print tomboy_interface.get_display_for_notes(file_names)
    except NoteNotFound, e:
        print >> sys.stderr, """Note named "%s" not found.""" % e

def action_search_in_notes(args):
    """ Use the tomtom object to search some text within notes """
    parser = optparse.OptionParser(usage="%prog search [-h] <search_pattern> [note_name ...]")

    (options, file_names) = parser.parse_args(args)

    if len(file_names) < 1:
        print >> sys.stderr, "Error: You must specify a pattern to perform a search"
        return

    tomboy_interface = Tomtom()

    search_pattern = file_names[0]
    note_names = file_names[1:]

    if note_names:
        print test_data.specific_search_results
    else:
        print test_data.search_results

# This dictionary is used to dispatch the actions and to list them for the -h option
available_actions = {
    "list": action_list_notes,
    "display": action_print_notes,
    "search": action_search_in_notes,
}

def main():
    usage = """Usage: %(app_name)s (-h|--help) [action]
       %(app_name)s <action> [-h|--help] [options]""" % {"app_name": os.path.basename(sys.argv[0])}

    if len(sys.argv) < 2:
        usage_output =  os.linesep.join([
            usage,
            "",
            "For more details, use option -h"])
        print usage_output
        return

    action = sys.argv[1]
    arguments = sys.argv[2:]

    if action in ["-h", "--help"]:
        if sys.argv[2:]:
            # Switch -h and action name and continue as normal
            arguments = [sys.argv[2], action] + sys.argv[3:]
            action = sys.argv[2]
        else:
            print os.linesep.join([
                usage,
                "",
                """Options depend on what action you are taking. To obtain details on options for a particular action, combine -h or --help and the action name.

Here is a list of all the available actions:
  list
  display
  search""",
            ])
            return

    if action not in available_actions:
        print >> sys.stderr, "%s: %s is not a valid action. Use option -h for a list of available actions." % (sys.argv[0], action)
        return

    perform_with = available_actions[action]
    perform_with(arguments)

if __name__ == "__main__":
    main()

