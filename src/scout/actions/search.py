# -*- coding: utf-8 -*-
import sys
import re

from scout import plugins
from scout.cli import TOO_FEW_ARGUMENTS_ERROR


class SearchAction(plugins.ActionPlugin):
    """Search for text in all or a specific list of notes.

    If nothing is found, nothing is shown on the terminal, but the action
    returns with an exit code of 1.

    If it finds results from the search, it will report every occurence by
    citing the note's name, the line number of the occurrence and the content
    of the line on which the text is appearing. The return code when a search
    has at least one result is 0.

    """

    short_description = __doc__.splitlines()[0]

    usage = '\n'.join(["%prog search (-h|--help)",
                       "       %prog search [filter ...] <search_pattern> "
                       "[note_name ...]"])

    def init_options(self):
        """Set action's options."""
        self.add_option_library(plugins.FilteringGroup("Search"))

    def perform_action(self, config, options, positional):
        """Search for some text within notes."""
        if len(positional) < 1:
            print >> sys.stderr, \
                "Error: You must specify a pattern to perform a search"
            sys.exit(TOO_FEW_ARGUMENTS_ERROR)

        search_pattern = positional[0]
        note_names = positional[1:]

        notes = self.interface.get_notes(
            names=note_names,
            tags=options.tags,
            exclude_templates=not options.templates
        )

        ret = 1
        for n in notes:
            content = self.interface.get_note_content(n)
            lines = content.splitlines()[1:]
            for ln_num, line in enumerate(lines):
                # regex-based search is probably not the fastest way.
                if re.search("(?i)%s" % (search_pattern, ), line):
                    ret = 0
                    result_map = (n.title, ln_num, line)
                    print ("%s : %s : %s" % result_map).encode('utf-8')

        return ret
