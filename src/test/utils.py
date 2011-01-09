# -*- coding: utf-8 -*-
"""General test utility classes and functions."""
import unittest
import mox
import sys
import os
import re
from cStringIO import StringIO
import dbus

from scout.core import Note


_data_cache = {}
_include_re = re.compile(r"^\{% +include +([^ ]+) +%\}$", re.MULTILINE)
def data(file_name):
    """Get the contents of the test data file data/'file_name'."""
    dat = _data_cache.get(file_name)
    if not dat:
        base_path = os.path.dirname(__file__)
        f =  open(os.path.join(base_path, "data", file_name), "r")
        # Cache temporarily to ensure we don't fall in infinite include loops.
        _data_cache[file_name] = dat = f.read()
        f.close()

        def _fetch_include(matchobj):
            d = data(matchobj.group(1))
            if d.endswith("\n"):
                d = d[:-1]
            return d
        dat = _include_re.sub(_fetch_include, dat)

        if dat != _data_cache[file_name]:
            _data_cache[file_name] = dat

    return dat


_full_list_of_notes = None

class BasicMocking(unittest.TestCase):
    """Base class for unit tests.

    Automates mox initialization and destruction.

    Is able to create a mock object with one genuine method, so that tests are
    ensured to run only the concerned methods.

    It is also possible to create a list of mocks from the same class.

    It can return a list of Note objects or mocks to make tests a little closer
    to reality.

    """
    def setUp(self):
        """Setup a mox factory to be able to use mocks in tests."""
        super(BasicMocking, self).setUp()

        self.m = mox.Mox()

    def tearDown(self):
        """Remove stubs so that they don't interfere with other tests."""
        super(BasicMocking, self).tearDown()

        self.remove_mocks()

    def remove_mocks(self):
        """Remove stubs and reset mocks.

        This can be called at the beginning of a test to clear out function
        calls and stubs that were automatically set up.

        """
        self.m.UnsetStubs()
        self.m.ResetAll()

    def wrap_subject(self, cls, attr):
        """Create a mock of 'cls' with the class's 'attr' method wrapped in.

        The subject function ('attr') is the one that your test is going to
        call.

        With this modified mock, you can run the subject function and make sure
        that no other methods from the same class are called withtout you
        explicitly recording it with mox beforehand in the "record" phase of
        the test.

        """
        mock = self.m.CreateMock(cls)

        func = getattr(cls, attr)
        setattr(mock, attr, lambda *x, **y: func(mock, *x, **y))

        return mock

    def n_mocks(self, num, cls=None):
        """Return a list of 'num' mocks of 'cls' or MockAnything if no class."""
        L = []
        for i in range(num):
            if cls:
                mock = self.m.CreateMock(cls)
            else:
                mock = self.m.CreateMockAnything()
            L.append(mock)
        return L

    def full_list_of_notes(self, real=False):
        """Parse data file and create a set of Notes.

        If 'real' is True, create real Note objects. Else, create Note mocks.

        The data file shouldn't change while running the tests, so cache the
        resulting lists to avoid repeating work. At most, the file will be
        parsed twice.

        """
        global _full_list_of_notes

        # return a copy of the list so that the original isn't modified
        if real and _full_list_of_notes:
            return list(_full_list_of_notes)

        notes = []
        raw = data("full_list_of_notes").splitlines()

        info = {"tags": []}
        def new_note():
            if real:
                n = Note(info["uri"])
            else:
                n = self.m.CreateMock(Note)
                n.uri = info["uri"]

            n.title = info["title"]
            n.date = info["date"]
            n._orig_tags = info["tags"]
            n.tags = list(info["tags"])

            return n

        for line in raw:
            if not line:
                notes.append(new_note())
                info = {"tags": []}
                continue

            pair = line.split(':', 1)
            assert(len(pair) == 2)
            token = pair[0].strip()
            value = pair[1].strip()

            if token == "tags":
                t = map(lambda x: x.strip(), value.split(','))
                info[token].extend(t)
            elif token == "date":
                info[token] = dbus.Int64(int(value))
            else:
                info[token] = value

        # last note probably doesn't have a blank line after it
        notes.append(new_note())

        if real:
            _full_list_of_notes = notes
        return list(notes)  # Same comment as first 'return'


class CLIMocking(unittest.TestCase):
    """Automatic mocking of standard streams.

    For parts of the code that interact with stdout and stderr, it should be
    interesting to test what is being output.

    Also save the value of sys.argv to be able to fake a command-line call.

    """
    def setUp(self):
        """Monkey patch stdout, stderr and argv."""
        super(CLIMocking, self).setUp()

        self.old_stdout = sys.stdout
        sys.stdout = StringIO()
        self.old_stderr = sys.stderr
        sys.stderr = StringIO()

        self.old_argv = sys.argv

    def tearDown(self):
        """Replace everything as it was before the test."""
        super(CLIMocking, self).tearDown()

        sys.argv = self.old_argv

        sys.stderr = self.old_stderr
        sys.stdout = self.old_stdout
