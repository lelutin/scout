# -*- coding: utf-8 -*-
"""Utility classes for communicating with Tomboy or Gnote over dbus.

These classes abstract all interaction with DBus.

"""
import dbus
import time
import os
from datetime import datetime


class ConnectionError(Exception):
    """A dbus connection problem occured."""
    pass

class NoteNotFound(Exception):
    """A note searched by name was not found."""
    pass

class AutoDetectionError(Exception):
    """Autodetection of available applications failed."""
    pass


class Scout(object):
    """An interface to Tomboy or Gnote.

    A DBus connection is established with the application as soon as an
    instance of this class is created.

    """
    def __init__(self, application):
        super(Scout, self).__init__()

        try:
            tb_bus = dbus.SessionBus()
        except dbus.DBusException, exc:
            msg = '\n'.join([
                "Could not establish connection with %s\n",
                "%s",
                "If you are not in an X session, did you forget to set",
                "the DISLAY environment variable?"
            ])
            msg_map = (application, exc)
            raise ConnectionError(msg % msg_map)

        if not application:
            (application, tb_object) = self._autodetect_app(tb_bus)
        else:
            try:
                tb_object = tb_bus.get_object(
                    "org.gnome.%s" % application,
                    "/org/gnome/%s/RemoteControl" % application
                )
            except dbus.DBusException, exc:
                msg = ''.join(["Application %s is not publishing any dbus ",
                               "object. It is possibly not installed."])
                raise ConnectionError(msg % application)

        self.application = application

        self.comm = dbus.Interface(
            tb_object,
            "org.gnome.%s.RemoteControl" % application
        )

    def _autodetect_app(self, bus):
        """Return a DBus object if one of Tomboy and Gnote is present.

        If none or both are present, raise an AutoDetectionError exception

        """
        success_list = []

        #FIXME this has the tendancy to start applications if they are installed
        for app in ["Tomboy", "Gnote"]:
            try:
                obj = bus.get_object(
                    "org.gnome.%s" % app,
                    "/org/gnome/%s/RemoteControl" % app
                )
                success_list.append( (app, obj) )
            except dbus.DBusException:
                pass

        if not success_list:
            error_message = ''.join(["No applications were found. Verify that ",
                                     "one of Tomboy or Gnote are installed."])
            raise AutoDetectionError(error_message)
        elif len(success_list) > 1:
            error_message = ''.join(["More than one application is currently ",
                                     "installed on your system. Scout could ",
                                     "not decide on which one to favor."])
            raise AutoDetectionError(error_message)

        return success_list[0]

    def get_notes(self, names=None, count_limit=0, tags=None,
                  exclude_templates=True):
        """Get a list of notes from the application.

        Notes are automatically filtered when necessary. (see filter_notes())

        """
        notes = self.build_note_list()

        if names is None:
            names = []
        if tags is None:
            tags = []

        # Force templates to be included in listing if the tag is requested.
        if "system:template" in tags:
            exclude_templates = False

        notes = self.filter_notes(
            notes,
            names=names,
            tags=tags,
            exclude_templates=exclude_templates
        )

        if count_limit > 0:
            return notes[:count_limit]

        return notes

    def get_note_content(self, note):
        """Get the content of 'note'.

        The note must be a Note instance. The list of tags in 'note' is
        displayed after the note name in the returned string.

        """
        lines = self.comm.GetNoteContents(note.uri).splitlines()
        # Oddly (but it is good), splitting the lines makes the indentation
        # bullets appear..
        if note.tags:
            lines[0] = "%s  (%s)" % ( lines[0], ", ".join(note.tags) )

        return os.linesep.join(lines)

    def build_note_list(self):
        """Return a list of all notes found in the application.

        Returns a list of Note objects.

        """
        list_of_notes = []
        for uri in self.comm.ListAllNotes():
            note_title = self.comm.GetNoteTitle(uri)

            list_of_notes.append(
                Note(
                    uri=uri,
                    title=note_title,
                    date=self.comm.GetNoteChangeDate(uri),
                    tags=self.comm.GetTagsForNote(uri)
                )
            )

        return list_of_notes

    def filter_notes(self, notes, tags, names,
                     exclude_templates=True):
        """Filter a list of notes accordingly.

        The list of notes can be narrowed down to only those whose names are
        found in  'names'.

        A maximum of 'count_limit' notes is returned, or all if 0.

        When non-empty, notes that do not have one of the tags in 'tags' are
        filtered out. Also, templates (notes with the special tag
        "system:template") are included or not based on 'exclude_templates'.

        """
        if tags or names:
            # Create the checker methods
            name_was_required = lambda x: x.title in names
            has_required_tag = lambda x: set(x.tags).intersection( set(tags) )

            # Verify if an unknown note was requested
            note_names = [n.title for n in notes]
            for name in names:
                if name not in note_names:
                    raise NoteNotFound(name)

            list_of_notes = [
                n for n in notes
                if name_was_required(n)
                   or has_required_tag(n)
            ]
        else:
            # Nothing to filter, keep list intact
            list_of_notes = notes

        if exclude_templates:
            # Keep templates that were requested by name
            list_of_notes = [
                n for n in list_of_notes
                if "system:template" not in n.tags
                   or n.title in names
            ]

        return list_of_notes


class Note(object):
    """A Tomboy or Gnote note.

    A note's date attribute can either be a dbus.Int64 object or a datetime
    object.

    """
    def __init__(self, uri, title="", date=dbus.Int64(), tags=None):
        super(Note, self).__init__()

        if tags is None:
            tags = []

        self.uri = uri
        self.title = title
        self.tags = tags

        if isinstance(date, datetime):
            self.date = dbus.Int64(time.mktime(date.timetuple()))
        else:
            self.date = date

    def __repr__(self):
        if not self.title:
            title = "_note doesn't have a name_"
        else:
            title = self.title

        if self.tags:
            tags = "  (%s)" % ", ".join(self.tags)
        else:
            tags = ""

        date = datetime.fromtimestamp(self.date).isoformat()[:10]

        return "%s | %s%s" % (date, title, tags)
