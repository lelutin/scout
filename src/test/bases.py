# -*- coding: utf-8 -*-
"""Test utility classes and functions.

These classes and functions are a set of utilities used throughout tests. They
categorize unit test environments and perform common tasks needed by various
test modules.

"""
import unittest
import mox
import sys
import StringIO

class BasicMocking(unittest.TestCase):
    """Base class for unit tests.

    Includes mox initialization and destruction for unit tests.
    Test cases should be subclasses of this one.

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
        """Remove stubs and reset mocks."""
        self.m.UnsetStubs()
        self.m.ResetAll()

    def wrap_subject(self, cls, subject_name):
        """Create a mock instance of a class and wrap the subject function.

        This will instantiate a mock of the given class and enclose the subject
        function (the one supposed to be tested) in the mock instance. With
        this modified mock, you can test the subject function while making sure
        that no other methods from the same class are called withtout you
        explicitly recording it beforehand in the "record" phase of the test.

        Arguments:
            cls -- The class to be mocked.
            subject_name -- Name of the function that should be tested.

        """
        mock = self.m.CreateMock(cls)

        func = getattr(cls, subject_name)
        wrapper = lambda *x, **y: func(mock, *x, **y)
        setattr(mock, subject_name, wrapper)

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

class CLIMocking(unittest.TestCase):
    """Automatic mocking of standard streams.

    This class sets up mocking for standard streams so as to verify interaction
    with "sys.stdout" and "sys.stderr". It also saves the value of sys.argv and
    restores it after the test so that tests can modify the value of argv
    without having an impact on other tests. It does so by defining a setUp and
    a tearDown method. Subclasses should call super(...).setUp() and
    super(...).tearDown in each respective method if they get redefined by the
    subclass.

    """
    def setUp(self):
        """Monkey patch "sys.stdout" and "sys.stderr"."""
        super(CLIMocking, self).setUp()

        self.old_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        self.old_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()

        self.old_argv = sys.argv

    def tearDown(self):
        """Replace everything as it was before the test."""
        super(CLIMocking, self).tearDown()

        sys.argv = self.old_argv

        sys.stderr = self.old_stderr
        sys.stdout = self.old_stdout

