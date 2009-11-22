#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Inspired by : http://arstechnica.com/open-source/news/2007/09/using-the-tomboy-d-bus-interface.ars
#
"""Usage: tomtom.py (-h|--help) [action]
       tomtom.py <action> [-h|--help] [options]

Tomtom is a command line interface to the Tomboy note taking application.

Options depend on what action you are taking. To obtain details on options
for a particular action, combine -h or --help and the action name.

Here is a list of all the available actions:
  list    : listing all or the 10 latest notes
  display : displaying one or more notes at a time
  search  : searching for text in all notes or a specific list of notes

"""
import sys
import os
import optparse

from tomboy_utils import *

def action_list_notes(args):
    """Use the tomtom object to list notes.

    This action prints modification date, title and tags of notes to the
    screen.

    Arguments:
        args -- A list composed of action and file names

    """
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
    """Use the tomtom object to print the content of one or more notes.

    This action fetches note contents and displays them to the screen.

    Arguments:
        args -- A list composed of action and file names

    """
    parser = optparse.OptionParser(usage="%prog display [-h] [note_name ...]")
    #parser.add_option("-a", "--all",
    #    dest="full_list", default=False, action="store_true",
    #    help="Display all the notes")

    (options, file_names) = parser.parse_args(args)

    if len(file_names) <= 0:
        print >> sys.stderr, \
            "Error: You need to specify a note name to display it"
        return

    tomboy_interface = Tomtom()

    try:
        print tomboy_interface.get_display_for_notes(file_names)
    except NoteNotFound, e:
        print >> sys.stderr, """Note named "%s" not found.""" % e

def action_search_in_notes(args):
    """Use the tomtom object to search for some text within notes.

    This action performs a textual search within notes and reports the results
    to the screen.

    Arguments:
        args -- list of arguments decomposed into action and file names

    """
    parser = optparse.OptionParser(
        usage="%prog search [-h] <search_pattern> [note_name ...]"
    )

    (options, file_names) = parser.parse_args(args)

    if len(file_names) < 1:
        print >> sys.stderr, \
            "Error: You must specify a pattern to perform a search"
        return

    tomboy_interface = Tomtom()

    search_pattern = file_names[0]
    note_names = file_names[1:]

    results = tomboy_interface.search_for_text(
        search_pattern=search_pattern,
        note_names=note_names
    )
    for result in results:
        print "%s : %s : %s" % \
            ( result["title"], result["line"], result["text"] )

# This dictionary is used to dispatch the actions and to list them for the -h
# option
#TODO find a better way to dispatch to really make implementing a new action
#simple as pie
available_actions = {
    "list": action_list_notes,
    "display": action_print_notes,
    "search": action_search_in_notes,
}

def main():
    """Application entry point.

    Checks the first parameters for general help argument and dispatches the
    actions.

    """
    if len(sys.argv) < 2:
        # Use the docstring's first [significant] lines to display usage
        usage_output =  (os.linesep * 2).join([
            os.linesep.join( __doc__.splitlines()[:3] ),
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
            # Use the script's docstring the for basic help message
            print __doc__[:-1]
            return

    if action not in available_actions:
        print >> sys.stderr, \
            """%s: %s is not a valid action. """ % (sys.argv[0], action) + \
            """Use option -h for a list of available actions."""
        return

    perform_with = available_actions[action]
    perform_with(arguments)

if __name__ == "__main__":
    main()

