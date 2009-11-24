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

        self.m.UnsetStubs()
        self.m.ResetAll()

class StreamMocking(unittest.TestCase):
    """Automatic mocking of standard streams.

    This class sets up mocking for standard streams so as to verify interaction
    with "sys.stdout" and "sys.stderr". It does so by defining a setUp and a
    tearDown method. Subclasses should call super(...).setUp() and
    super(...).tearDown in each respective method if they get redefined by the
    subclass.

    """
    def setUp(self):
        """Monkey patch "sys.stdout" and "sys.stderr"."""
        super(StreamMocking, self).setUp()

        self.old_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        self.old_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()

    def tearDown(self):
        """Replace everything as it was before the test."""
        super(StreamMocking, self).tearDown()

        sys.stderr = self.old_stderr
        sys.stdout = self.old_stdout

