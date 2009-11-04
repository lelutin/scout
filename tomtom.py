#!/bin/env python
# -*- coding: utf-8 -*-
import sys
import optparse

def main():
    formatted_list = \
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

    appendix = \
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

    note_content = \
"""TODO

Build unit tests for tomtom
Chew up some gum
Play pool with the queen of england"""

    parser = optparse.OptionParser()
    parser.add_option("-l", "--list-all",
        dest="full_list", default=False, action="store_true",
        help="List all the notes")
    parser.add_option("-s", "--search", dest="search_pattern",
        help="Search a pattern within notes")

    (options, file_names) = parser.parse_args()

    if options.full_list:
        print formatted_list + appendix
        return
    if options.search_pattern:
        if file_names:
            print specific_search_results
        else:
            print search_results
        return

    if len(file_names) > 0:
        if file_names[0] == "unexistant":
            print "Note named \"unexistant\" not found."
        else:
            print note_content
        return

    print formatted_list

if __name__ == "__main__":
    main()

