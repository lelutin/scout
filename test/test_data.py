# -*- coding: utf-8 -*-
"""test data for tomtom"""
import dbus
from tomboy_utils import TomboyNote

# To obtain modification dates for notes and corresponding real dates:
# With tomboy being a dbus interface to the Tomboy application:
# >>> [(datetime.fromtimestamp(tomboy.GetNoteChangeDate(url)),tomboy.GetNoteChangeDate(url)) for url in l]
expected_list = \
"""2009-11-9 | addressbook  (pim)
2009-11-2 | TODO-list  (reminders)
2009-11-2 | Bash  (reminders)
2009-10-22 | dell 750  (projects)
2009-10-22 | python-work
2009-10-18 | TDD
2009-10-18 | OpenSource Conference X
2009-10-3 | business contacts  (pim)
2009-10-1 | japanese  (reminders)
2009-9-19 | Webpidgin  (projects)"""

list_appendix = \
"""2009-9-19 | conquer the world  (projects)
2009-9-19 | recipies
2009-9-19 | R&D  (reminders)"""

search_results = \
"""addressbook : 35 : John Doe (cell) - 555-5512
business contacts : 21 : John Doe Sr. (office) - 555-5534"""

specific_search_results = \
"""dell 750 : 12 : Install python 2.5
python-work : 2 : to use a python buildbot for automatic bundling
OpenSource Conference X : 120 : Presentation: Python by all means"""

expected_note_content = \
"""TODO-list

Build unit tests for tomtom
Chew up some gum
Play pool with the queen of england"""

full_list_of_notes = [
    TomboyNote(
        uri="note://tomboy/b332eb31-8139-4351-9f5d-738bf64ce172",
        title="addressbook",
        date=dbus.Int64(1257805144L),
        tags=["pim", ]
    ),
    TomboyNote(
        uri="note://tomboy/30ae533a-2789-4789-a409-16a6f65edf54",
        title="TODO-list",
        date=dbus.Int64(1257140572L),
        tags=["reminders", ]
    ),
    TomboyNote(
        uri="note://tomboy/4652f914-85dd-487d-b614-188242f52241",
        title="Bash",
        date=dbus.Int64(1257138697L),
        tags=["reminders", ]
    ),
    TomboyNote(
        uri="note://tomboy/5815160c-7143-4c56-9c5f-007acca375ad",
        title="dell 750",
        date=dbus.Int64(1256265529L),
        tags=["projects", ]
    ),
    TomboyNote(
        uri="note://tomboy/89277e3b-bdb7-4cfe-a42c-7c8b207370fd",
        title="python-work",
        date=dbus.Int64(1256257835L),
        tags=[]
    ),
    TomboyNote(
        uri="note://tomboy/bece0d43-19ba-41cf-92b5-7b30a5411a0c",
        title="TDD",
        date=dbus.Int64(1255898778L),
        tags=[]
    ),
    TomboyNote(
        uri="note://tomboy/1a1994da-1b98-41d2-8eab-26e8581fc391",
        title="OpenSource Conference X",
        date=dbus.Int64(1255890996L),
        tags=[]
    ),
    TomboyNote(
        uri="note://tomboy/21612e71-e2ec-4afb-82bb-7e663e58e88c",
        title="business contacts",
        date=dbus.Int64(1254553804L),
        tags=["pim", ]
    ),
    TomboyNote(
        uri="note://tomboy/8dd14cf8-4766-4122-8178-192cdc0e99dc",
        title="japanese",
        date=dbus.Int64(1254384931L),
        tags=["reminders", ]
    ),
    TomboyNote(
        uri="note://tomboy/c0263232-c3b8-45a8-bfdc-7cb8ee4b2a5d",
        title="Webpidgin",
        date=dbus.Int64(1253378270L),
        tags=["projects", ]
    ),
    TomboyNote(
        uri="note://tomboy/ea6f4c7f-1b82-4835-9aa2-2df002d788f4",
        title="conquer the world",
        date=dbus.Int64(1253342190L),
        tags=["projects", ]
    ),
    TomboyNote(
        uri="note://tomboy/461fb1a2-1e02-4447-8891-c3c6fcbb26eb",
        title="recipies",
        date=dbus.Int64(1253340981L),
        tags=[]
    ),
    TomboyNote(
        uri="note://tomboy/5df0fd74-cbdd-4cf3-bb08-7a7f09997afd",
        title="R&D",
        date=dbus.Int64(1253340600L),
        tags=["reminders", ]
    ),
]
