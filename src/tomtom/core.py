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
"""Utility classes for communicating with Tomboy or Gnote over dbus.

Exceptions:
    ConnectionError -- A dbus connection problem occured.
    NoteNotFound    -- A note searched by name was not found.

Classes:
    Tomtom             -- Communication object to Tomboy or Gnote
    TomboyNote         -- Object representation of a Tomboy or Gnote note.

"""
import dbus
import datetime
import time
import os

# This must be modified with all version bumps!
TOMTOM_VERSION = "0.2"

class ConnectionError(Exception):
    """Simple exception raised dbus connection fails."""
    pass

class NoteNotFound(Exception):
    """Simple exception raised when a specific note does not exist."""
    pass

class AutoDetectionError(Exception):
    """Raised when autodetection of available applications failed."""
    pass

class Tomtom(object):
    """Application class for Tomtom.

    This class holds the dbus contact object and the methods to fetch
    information from it. The most useful methods are get_notes and
    get_note_contents which get a list of notes according to a series of
    criteria, and get the contents of one note, respectively.

    """
    def __init__(self, application):
        """Create a link to Tomboy or Gnote upon instantiation.

        Arguments:
            application -- string name of either Tomboy or Gnote.

        """
        super(Tomtom, self).__init__()

        try:
            tb_bus = dbus.SessionBus()
        except dbus.DBusException, exc:
            msg = os.linesep.join([
                """Could not establish connection with %s""" + os.linesep,
                """%s""",
                """If you are not in an X session, did you forget to set """,
                """the DISLAY environment variable?"""
            ])
            msg_map = (application, exc)
            raise ConnectionError(msg % msg_map)

        if application is None:
            (application, tb_object) = self._autodetect_app(tb_bus)
        else:
            try:
                tb_object = tb_bus.get_object(
                    "org.gnome.%s" % application,
                    "/org/gnome/%s/RemoteControl" % application
                )
            except dbus.DBusException, exc:
                msg = """Application %s is not publishing any dbus """ + \
                      """object. It is possibly not installed."""
                raise ConnectionError(msg % application)

        self.application = application

        self.comm = dbus.Interface(
            tb_object,
            "org.gnome.%s.RemoteControl" % application
        )

    def _autodetect_app(self, bus):
        """Determine only one of Tomboy and Gnote is present."""
        success_list = []

        for app in ["Tomboy", "Gnote"]:
            try:
                obj = bus.get_object(
                    "org.gnome.%s" % app,
                    "/org/gnome/%s/RemoteControl" % app
                )
                success_list.append( (app, obj) )
            except dbus.DBusException:
                pass

        if len(success_list) != 1:
            if len(success_list) == 0:
                error_message = \
                    """No applications were found. Verify that one of """ + \
                    """Tomboy or Gnote are installed."""

            if len(success_list) > 1:
                error_message = \
                    """More than one application is currently """ + \
                    """installed on your system. Tomtom could not """ + \
                    """decide on which one to favor."""

            raise AutoDetectionError(error_message)

        return success_list[0]

    def get_notes(self, **kwargs):
        """Get a list of notes from the application.

        This function gets a list of notes that match the given selection
        options. Notes are automatically filtered. Keyword arguments used in
        the note building part are "names" and  "count_limit". The rest of the
        arguments will be useful to the filtering method.

        Arguments:
            **kwargs -- Map of arguments used for getting and filtering notes.

        """
        # Consumes "count_limit" and uses "names".
        notes = self.build_note_list(**kwargs)
        kwargs.pop("count_limit", 0)

        # "names" is still needed for filter_notes
        return self.filter_notes(notes, **kwargs)

    def get_note_content(self, note):
        """Get the content of a note.

        This method returns the content of one note. The note must be a
        TomboyNote object. Tags are added after the note name in the returned
        content.

        Arguments:
            note -- A TomboyNote object

        """
        lines = self.comm.GetNoteContents(note.uri).splitlines()
        # Oddly (but it is good), splitting the lines makes the indentation
        # bullets appear..
        if note.tags:
            lines[0] = "%s  (%s)" % ( lines[0], ", ".join(note.tags) )

        return os.linesep.join(lines)

    def get_uris_for_n_notes(self, count_max):
        """Find the URIs for the `count_max` latest notes.

        This method retrieves URIs of notes. If count_max is None, it gets URIs
        for all notes. Otherwise, it gets `count_max` number of URIs.

        Arguments:
            count_max -- Maximum number of notes to lookup

        """
        uris = self.comm.ListAllNotes()

        if count_max != None:
            uris = uris[:count_max]

        return [(u, None) for u in uris]

    def get_uris_by_name(self, names):
        """Search for all the notes with the given names.

        This method retreives URIs of notes by searching for them by names. It
        searches for all names that are in the `names` list.

        Arguments:
            names -- a list of note names

        """
        uris = []

        for name in names:
            uri = self.comm.FindNote(name)
            if uri == dbus.String(""):
                raise NoteNotFound(name)

            uris.append( (uri, name) )

        return uris

    def filter_by_tags(self, notes, tag_list):
        """Remove notes from the list if they have no tags from the list."""
        tags = set(tag_list)

        return [
            note for note in notes
            if tags.intersection( set(note.tags) )
        ]

    def filter_out_templates(self, notes):
        """Take out those annoying templates from display."""
        return [n for n in notes if "system:template" not in n.tags]

    def build_note_list(self, **kwargs):
        """Find notes and build a list of TomboyNote objects.

        This method gets a list of notes from the application and converts them
        to TomboyNote objects. It then returns the notes in a list.

        """
        names = kwargs.pop("names", [])
        count_limit = kwargs.pop("count_limit", None)

        if names:
            pairs = self.get_uris_by_name(names)
        else:
            pairs = self.get_uris_for_n_notes(count_limit)

        list_of_notes = []
        for pair in pairs:
            uri = pair[0]
            note_title = pair[1]

            if note_title is None:
                note_title = self.comm.GetNoteTitle(uri)

            list_of_notes.append(
                TomboyNote(
                    uri=uri,
                    title=note_title,
                    date=self.comm.GetNoteChangeDate(uri),
                    tags=self.comm.GetTagsForNote(uri)
                )
            )

        return list_of_notes

    def filter_notes(self, notes, tags=[], names=[],
            exclude_templates=True):
        """Filter a list of notes according to some criteria.

        Filter a list of TomboyNote objects according to a list of filtering
        options. "names" will filter out any notes but those whose names are in
        the list.

        Arguments:
            notes -- list of note objects
            tags -- list of tag strings to filter by
            names -- list of the only names to include
            exclude_templates -- Boolean, exclude templates (default: True)

        """
        if tags:
            notes = self.filter_by_tags(notes, tags)

        # Force templates to be included in listing if the tag is requested.
        if "system:template" in tags:
            exclude_templates = False

        # Avoid filtering if names are specified. This makes it possible to
        # select a template by name. Also avoid if template tag is specified.
        if not names and exclude_templates:
            return self.filter_out_templates(notes)

        return notes

class TomboyNote(object):
    """Object corresponding to a Tomboy or Gnote note coming from dbus."""
    def __init__(self, uri, title="", date=dbus.Int64(), tags=[]):
        """Constructor.

        This makes sure that instance attributes are set upon the note's
        instantiation. The date can either be a dbus.Int64 object or a datetime
        object.

        Arguments:
            uri -- A string representing the note's URI
            title -- A string representing the note's title
            date -- Can either be a dbus.Int64 or datetime object
            tags -- A list of strings that represent tags

        """
        super(TomboyNote, self).__init__()
        self.uri = uri
        self.title = title
        self.tags = tags

        if isinstance(date, datetime.datetime):
            self.date = dbus.Int64( time.mktime(date.timetuple()) )
        else:
            self.date = date

    def listing(self):
        """Get a listing for this note.

        This method returns listing information about the note represented by
        this object.

        """
        printable_title = self.title
        if not self.title:
            printable_title = "_note doesn't have a name_"

        printable_tags = ""
        if len(self.tags):
            printable_tags = "  (" + ", ".join(self.tags) + ")"

        return "%(date)s | %(title)s%(tags)s" % \
            {
                "date": datetime.datetime.fromtimestamp(self.date)\
                            .isoformat()[:10],
                "title": printable_title,
                "tags": printable_tags,
            }

