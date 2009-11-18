# -*- coding: utf-8 -*-
"""Utility classes for communicating with Tomboy over dbus"""
import dbus
import datetime
import time
import sys

class ConnectionError(Exception):
    """Simple exception representing an error contacting Tomboy via dbus"""
    pass
        
class TomboyCommunicator(object):
    """Interface between the application and Tomboy's dbus link"""
    def __init__(self):
        """Create a link to the Tomboy application upon instanciation"""
        try:
            tb_bus = dbus.SessionBus()
        except:
            (dummy1, error, dummy2) = sys.exc_info()
            raise ConnectionError("Could not connect to dbus session: %s" % (error, ) )

        try:
            tb_object = tb_bus.get_object("org.gnome.Tomboy", "/org/gnome/Tomboy/RemoteControl")
            self.comm = dbus.Interface(tb_object, "org.gnome.Tomboy.RemoteControl")
        except:
            (dummy1, error, dummy2) = sys.exc_info()
            raise ConnectionError("Could not establish connection with Tomboy. Is it running?: %s" % (error, ) )

    def get_notes(self, count_limit=None):
        """Get a list of `count_limit` notes from Tomboy. If count_limit is null, get all notes"""
        list_of_notes = []
        uris = self.comm.ListAllNotes()

        if count_limit != None:
            uris = uris[:count_limit]

        for uri in uris:
            list_of_notes.append(
                TomboyNote(
                    uri=uri,
                    title=self.comm.GetNoteTitle(uri),
                    date=self.comm.GetNoteChangeDate(uri),
                    tags=self.comm.GetTagsForNote(uri)
                )
            )

        return list_of_notes

class TomboyNote(object):
    """Object corresponding to a Tomboy note coming from dbus"""
    def __init__(self, uri, title="", date=dbus.Int64(), tags=[]):
        super(TomboyNote, self).__init__()
        self.uri = uri
        self.title = title
        self.tags = tags

        if isinstance(date, datetime.datetime):
            self.date = dbus.Int64( time.mktime(date.timetuple()) )
        else:
            self.date = date

    def listing(self):
        """Return a listing for this note"""
        printable_title = self.title
        if not self.title:
            printable_title = "_note doesn't have a name_"

        printable_tags = ""
        if len(self.tags):
            printable_tags = "  (" + ", ".join(self.tags) + ")"

        return "%(date)s | %(title)s%(tags)s" % \
            {
                "date": datetime.datetime.fromtimestamp(self.date).isoformat()[:10],
                "title": printable_title,
                "tags": printable_tags,
            }

