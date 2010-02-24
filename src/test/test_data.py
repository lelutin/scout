# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (c) 2009, Gabriel Filion
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice,
#     * this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
###############################################################################
"""Test data for tomtom.

All the uglyness of testing data should be here.
Although it is ugly by definition, it should be well organized in order to
simplify and clarify testing code, and also to make this file less painful
to look at.

"""
import os
import dbus
from tomtom.core import TomboyNote, tomtom_version

# The following few values are for testing the "list" feature.
expected_list = \
"""2009-11-09 | addressbook  (system:notebook:pim)
2009-11-02 | TODO-list  (system:notebook:reminders, system:notebook:pim)
2009-11-02 | Bash  (system:notebook:reminders)
2009-10-22 | dell 750  (projects)
2009-10-22 | python-work
2009-10-18 | TDD
2009-10-18 | OpenSource Conference X
2009-10-03 | business contacts  (system:notebook:pim)
2009-10-01 | japanese  (system:notebook:reminders)
2009-09-19 | Webpidgin  (projects)"""

list_appendix = \
"""2009-09-19 | conquer the world  (projects)
2009-09-19 | recipes
2009-09-19 | R&D  (system:notebook:reminders, training)"""

tag_limited_list = \
"""2009-11-09 | addressbook  (system:notebook:pim)
2009-11-02 | TODO-list  (system:notebook:reminders, system:notebook:pim)
2009-10-22 | dell 750  (projects)
2009-10-03 | business contacts  (system:notebook:pim)
2009-09-19 | Webpidgin  (projects)
2009-09-19 | conquer the world  (projects)"""

book_limited_list = \
"""2009-11-09 | addressbook  (system:notebook:pim)
2009-11-02 | TODO-list  (system:notebook:reminders, system:notebook:pim)
2009-11-02 | Bash  (system:notebook:reminders)
2009-10-03 | business contacts  (system:notebook:pim)
2009-10-01 | japanese  (system:notebook:reminders)
2009-09-19 | R&D  (system:notebook:reminders, training)"""

normally_hidden_template = \
"""2009-09-19 | New note template  (system:template, system:notebook:pim)"""

# Output values that are expected for the "search" feature.
search_results = \
"""addressbook : 5 : John Doe (cell) - 555-5512
business contacts : 7 : John Doe Sr. (office) - 555-5534"""

specific_search_results = \
"""dell 750 : 9 : python-libvirt - libvirt Python bindings
python-work : 2 : to use a python buildbot for automatic bundling
OpenSource Conference X : 15 : oops, and don't forget to talk about python"""

search_no_argument_error = \
    "Error: You must specify a pattern to perform a search"

# Those are values to test the "display" feature.
note_contents_from_dbus = {
    "addressbook": """addressbook

Momma Chicken - 444-1919
Père Noël - 464-6464
Nakamura Takeshi - 01-20-39-48-57
G.I. Jane (pager) - 555-1234
John Doe (cell) - 555-5512""",
    "TODO-list": """TODO-list

Build unit tests for tomtom
Chew up some gum
Play pool with the queen of england""",
    "Bash": """Bash

something""",
    "dell 750": """dell 750

$ apt-cache search lxc
libclxclient-dev - Development file for libclxclient
libclxclient3 - X Window System C++ access library
lxc - Linux containers userspace tools
libvirt-bin - the programs for the libvirt library
libvirt-dev - development files for the libvirt library
libvirt-doc - documentation for the libvirt library
libvirt0-dbg - library for interfacing with different virtualization systems
python-libvirt - libvirt Python bindings
libopencascade-ocaf-6.3.0 - OpenCASCADE CAE platform shared library""",
    "python-work": """python-work

I need to ask Shintarou to prepare things
to use a python buildbot for automatic bundling
for the project.""",
    "TDD": """TDD

something""",
    "OpenSource Conference X": """OpenSource Conference X

Lorem ipsum vix ei inermis epicurei mnesarchum, quod graeci facete vis cu, sumo
libris pro no. Quod vocibus rationibus ex mea, nam dicta tantas cetero et.
Nulla aperiam nostrud ad est, id qui exerci feugiat rationibus, in sed affert
facete eripuit. Ei nam oratio aperiri epicurei. His te kasd adipisci
dissentiunt, laudem putant fabellas nam in. Homero causae scaevola sit cu.

Mea ea puto malis mediocrem, ad dolorem expetenda iracundia vis. Cibo graece
tamquam an mel, ne qui omnes aliquid tibique, has at tale sale vidit. Solum
porro at per, usu denique officiis perfecto te. Has puto rebum impedit ex, duo
modus diceret fastidii cu.

Nibh impedit posidonium pro ea, sint quidam aperiam per ea, est laudem
accommodare eu. Eos brute deserunt eu, no sit novum ignota detraxit, duo ...

oops, and don't forget to talk about python""",
    "business contacts": """business contacts

Elvis Presley - 111-1111
Kurosaki Ichigo - 444-5555
God Himself (cell) - 999-9999
Mother Theresa - 000-0000
Pidgeon in a Box - 918-3874
Donald E. Knuth - 101-2020
John Doe Sr. (office) - 555-5534
Mister Anderson (secretary) - 123-4567
Python McClean - 777-7777""",
    "japanese": """japanese

robot = ロボット
alien = 宇宙人
invader = 侵入者
octopus = たこ""",
    "Webpidgin": """Webpidgin

something""",
    "conquer the world": """conquer the world

1. get into the whole being-a-villan thing
2. practice evil skills
3. plan something very mean
4. acquire information
5. study weaknesses
6. execute plan
7. acquire complete power over the world
8. get some rest.. all of this is going to be tiresome""",
    "recipes": """recipes

something""",
    "R&D": """R&D

I need something to get Prshan's attention to switch
over to doing that R&D stuff. He refuses to do it because
he thinks it is going nowhere.

In the training, they gave me great arguments to be
able to change his mind. He will see what I mean.

powder
refreshing
barrel of whiskey
gone fishing
and voila!""",
}

display_no_note_name_error = \
    "Error: You need to specify a note name to display it"

display_separator = "=========================="

# This is a list of false notes that are used throughout the majority of tests.
#
# To obtain modification dates for notes and corresponding real dates:
# With "tomboy" being a dbus interface to the Tomboy application:
# >>> from datetime import datetime
# >>> l = tomboy.ListAllNotes()
# >>> [(datetime.fromtimestamp(tomboy.GetNoteChangeDate(url)),
# >>>     tomboy.GetNoteChangeDate(url)) for url in l]
full_list_of_notes = [
    TomboyNote(
        uri="note://tomboy/b332eb31-8139-4351-9f5d-738bf64ce172",
        title="addressbook",
        date=dbus.Int64(1257805144L),
        tags=["system:notebook:pim", ]
    ),
    TomboyNote(
        uri="note://tomboy/30ae533a-2789-4789-a409-16a6f65edf54",
        title="TODO-list",
        date=dbus.Int64(1257140572L),
        tags=["system:notebook:reminders", "system:notebook:pim"]
    ),
    TomboyNote(
        uri="note://tomboy/4652f914-85dd-487d-b614-188242f52241",
        title="Bash",
        date=dbus.Int64(1257138697L),
        tags=["system:notebook:reminders", ]
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
        tags=["system:notebook:pim", ]
    ),
    TomboyNote(
        uri="note://tomboy/8dd14cf8-4766-4122-8178-192cdc0e99dc",
        title="japanese",
        date=dbus.Int64(1254384931L),
        tags=["system:notebook:reminders", ]
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
        title="recipes",
        date=dbus.Int64(1253340981L),
        tags=[]
    ),
    TomboyNote(
        uri="note://tomboy/5df0fd74-cbdd-4cf3-bb08-7a7f09997afd",
        title="R&D",
        date=dbus.Int64(1253340600L),
        tags=["system:notebook:reminders", "training"]
    ),
    TomboyNote(
        uri="note://tomboy/0045cd16-2977-456a-b790-9a256f5b2a71",
        title="New note template",
        date=dbus.Int64(1253340983L),
        tags=["system:template", "system:notebook:pim"]
    ),
]

# This value is the output of the "version" action
tomboy_version_output = \
    """Tomtom version %s using Tomboy version 1.0.1""" % tomtom_version

# Help text and errors occuring in the main script
help_more_details = """For more details, use option -h"""

help_details_list = \
"""Usage: app_name list [-h|-n <num>|-t <tag>[,...]|-b <book>[,...]]

Options:
  -h, --help          show this help message and exit
  -n MAX_NOTES        Limit the number of notes listed.

  Filtering:
    Filter notes by different criteria.

    -b BOOKS          List only notes belonging to specified notebooks. It is
                      a shortcut to option "-t" to specify notebooks more
                      easily. For example, use "-b HGTTG" instead of "-t
                      system:notebook:HGTTG". Use this option once for each
                      desired book.
    --with-templates  Include template notes in the list. This option is
                      different from using "-t system:template" in that the
                      latter used alone will list only the templates, while
                      "using --with-templates" without specifying tags for
                      selection will list notes including templates.
    -t TAGS           List only notes with specified tags. Use this option
                      once for each desired tag. This option selects raw tags
                      and could be useful for user-assigned tags."""

help_details_display = """Usage: app_name display [-h] [note_name ...]

Options:
  -h, --help  show this help message and exit"""

help_details_search = \
"""Usage: app_name search -h
       app_name search [-b <book name>[,...]|-t <tag>[,...]|--with-templates] <search_pattern> [note_name ...]

Options:
  -h, --help          show this help message and exit

  Filtering:
    Filter notes by different criteria.

    -b BOOKS          Search only in notes belonging to specified notebooks.
                      It is a shortcut to option "-t" to specify notebooks
                      more easily. For example, use "-b HGTTG" "instead of -t
                      system:notebook:HGTTG". Use this option once for each
                      desired book.
    --with-templates  Include template notes in the search. This option is
                      different from using "-t system:template" in that the
                      latter used alone will search only in the templates,
                      "while using --with-templates" without specifying tags
                      for selection will search in all notes including
                      templates.
    -t TAGS           Search only in notes with specified tags. Use this
                      option once for each desired tag. This option selects
                      raw tags and could be useful for user-assigned tags."""

help_details_version = \
"""Usage: app_name version [-h]

Options:
  -h, --help  show this help message and exit"""

too_few_arguments_error = \
"""Usage: app_name <action> [-h|--help] [options]
       app_name (-h|--help) [action]
       app_name (-v|--version)

For more details, use option -h"""

unexistant_note_error = \
    """app_name: Error: Note named "unexistant" was not found."""

unknown_action = """app_name: unexistant_action is not a valid action. """ + \
                 """Use option -h for a list of available actions."""

fake_traceback = \
    """Traceback (most recent call last):
  File "/home/gabster/tomtom/src/tomtom/cli.py", line 112, in dispatch
    action.perform_action(arguments, [])
  File "/home/gabster/tomtom/src/tomtom/actions/list.py", line 83, in perform_action
    raise Exception
Exception"""

unhandled_action_exception_error_message = \
    """app_name: the "some_action" action is malformed: An uncaught exception was raised while executing its "perform_action" function:

%s""" % fake_traceback

connection_error_message = \
    """app_name: Error: there was a problem"""

dbus_session_exception_text = \
    """Could not connect to dbus session: something happened"""

dbus_interface_exception_text = \
    """Could not establish connection with Tomboy. """ + \
    """Is it running?: cosmos error"""

option_type_error_message = \
    """Option <list instance> in action some_action is not of one """ + \
    """of the types optparse.Option or optparse.OptionGroup"""

version_and_license_info = \
"""Tomtom version %s
Copyright © 2010 Gabriel Filion
License: BSD
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""" % tomtom_version

module1_description = \
    """This is action1 and it does something."""

module_descriptions = [
    "  action1     : This is action1 and it does something.",
    "  otheraction : No description available.",
]

