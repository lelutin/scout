# -*- coding: utf-8 -*-
"""Utility classes for communicating with Tomboy over dbus"""
import dbus
import datetime
import time
import sys
import os

class ConnectionError(Exception):
    """Simple exception representing an error contacting Tomboy via dbus"""
    pass

class NoteNotFound(Exception):
    """Simple exception raised when searching for a specific note that does not exist"""
    pass
        
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

    def search_for_text(self, search_pattern, note_names=[]):
        """Get concerned noted and search for the pattern in them"""
        notes = self.tomboy_communicator.get_notes(names=note_names)
        search_results = []

        import re
        for note in notes:
            content = self.tomboy_communicator.get_note_content(note)
            lines = content.split(os.linesep)[1:]
            for index, line in enumerate(lines):
                # Perform case-independant search of each word on each line
                if re.search("(?i)%s" % (search_pattern, ), line):
                    search_results.append({
                        "title": note.title,
                        "line": index,
                        "text": line,
                    })

        return search_results

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

    def get_uris_for_n_notes(self, count_max):
        """Get a list of notes and limit it to the `count_max` latest ones"""
        uris = self.comm.ListAllNotes()

        if count_max != None:
            uris = uris[:count_max]

        return [(u, None) for u in uris]

    def get_uris_by_name(self, names):
        """Search for all the notes with the given names"""
        uris = []

        for name in names:
            uri = self.comm.FindNote(name)
            if uri == dbus.String(""):
                raise NoteNotFound(name)

            uris.append( (uri, name) )

        return uris

    def get_notes(self, count_limit=None, names=[]):
        """
        Get a list of notes from Tomboy.
        `count_limit` can limit the number of notes returned. Set it to None (default value) to get all notes
        If `names` is given a list of note names, it will restrict the search to only those notes
        """
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

    def get_note_content(self, note):
        """Takes a TomboyNote object and returns its contents"""
        lines = self.comm.GetNoteContents(note.uri).split(os.linesep)
        #TODO Oddly (but it is good), splitting the lines makes the indentation bullets appear.. come up with a test for this to stay
        if note.tags:
            lines[0] = "%s  (%s)" % ( lines[0], ", ".join(note.tags) )

        return os.linesep.join(lines)

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

