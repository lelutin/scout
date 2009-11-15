# -*- coding: utf-8 -*-
"""Utility classes for communicating with Tomboy over dbus"""
import dbus
import datetime
import time

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

