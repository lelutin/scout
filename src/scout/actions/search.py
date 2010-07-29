# -*- coding: utf-8 -*-
"""Search for text in all notes or a specific list of notes.

This is the "search" action. Its role is to search for some text in either
all notes or a specialized set of notes. It returns nothing on stdout if it
finds nothing. If it finds results from the search, it will report every
occurence by citing the note's name, the line number of the occurrence and
the content of the line on which the text is appearing.

"""
import sys
import os
import re

from scout import plugins
from scout.cli import TOO_FEW_ARGUMENTS_ERROR

DESC = __doc__.splitlines()[0]

class SearchAction(plugins.ActionPlugin):
    """Plugin object for searching text in notes"""
    short_description = DESC
    usage = """%prog search (-h|--help)""" + os.linesep + \
        """       %prog search [filter ...] <search_pattern> [note_name ...]"""

    def init_options(self):
        """Set action's options."""
        self.add_option_library( plugins.FilteringGroup("Search") )

    def perform_action(self, config, options, positional):
        """Use the scout object to search for some text within notes.

        This action performs a textual search within notes and reports the
        results to the screen.

        Arguments:
            config -- a ConfigParser.SafeParser object representing config files
            options -- an optparse.Values object containing the parsed options
            positional -- a list of strings of positional arguments

        """
        if len(positional) < 1:
            print >> sys.stderr, \
                "Error: You must specify a pattern to perform a search"
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        search_pattern = positional[0]
        note_names = positional[1:]

        notes = self.tomboy_interface.get_notes(
            names=note_names,
            tags=options.tags,
            exclude_templates=not options.templates
        )

        results = self.search_for_text(search_pattern, notes)

        for result in results:
            result_map = ( result["title"], result["line"], result["text"] )

            print ("%s : %s : %s" % result_map).encode('utf-8')

    def search_for_text(self, search_pattern, notes):
        """Get specified notes and search for a pattern in them.

        This function performs a case-independant text search on the contents
        of a list of notes.

        Arguments:
            search_pattern -- String, pattern to seach for
            notes -- List of notes to search on

        """
        search_results = []

        for note in notes:
            content = self.tomboy_interface.get_note_content(note)
            lines = content.splitlines()[1:]
            for index, line in enumerate(lines):
                # Perform case-independant search of each word on each line
                if re.search("(?i)%s" % (search_pattern, ), line):
                    search_results.append({
                        "title": note.title,
                        "line": index,
                        "text": line,
                    })

        return search_results
