tomtom : A CLI interface to Tomboy

Installing
==========

From source
-----------

To install tomtom from the source archive, use the setuptools installer:

    $ sudo python setup.py install

Requirements
------------

To run tomtom, you need to have dbus-python installed. On Debian or Ubuntu, use
the following command:

    $ sudo apt-get install python-dbus

On Fedora or Centos, use the following:

    $ sudo yum install dbus-python

Use
===

To use tomtom the first argument must be an action name. For example, say you
want to get a list of all non-template notes. You can call the following:

    $ tomtom list

Arguments can be given to actions. The arguments available differ from one
action to the other. For example,
the "search" action requires an element to search for:

    $ tomtom search "text to search"

You can obtain help on how to execute tomtom by giving it a "-h" or "--help"
argument. This will list the currently available actions you can use with
tomtom. To obtain more detail on what arguments can be used with an action, use
the option "-h" or "--help" and specify an action name at the same time. Both
of the two following commands call the detailed help for the action "display":

    $ tomtom --help display
    $ tomtom display -h

Contributing
============

All contributions to the code are welcome. Contributed code should come with
unit tests for added functions and acceptance tests for command line interface
modifications. The main repository is on [GitHub]. Feel free to either fork the
repository and send pull requests, or simply to generate patches and send them
by e-mail to lelutin@gmail.com.

Tests
-----

To be able to run the unit or acceptance tests, you will need to have pymox
and nose installed. On Debian or Ubuntu, use the following command to install
them:

    $ apt-get install python-mox python-nose

The tests can be run by one of to methods. The first one is through setup.py
like following:

    tomtom$ python setup.py test

The second method, being the fastest and most flexible one, is by calling
nose's nosetests script. A configuration file is included in the base directory
to make running the unit tests easier. From the base directory:

    tomtom$ nostests -c nose.cfg

See the configuration file for some configuration lines that can be uncommented.

One useful trick with git to make running tests easier is to set an alias in
the following manner (make sure to use single quotes, the !  and $ characters
are interpreted by bash if it is inside double quotes):

    $ git config --global alias.test '!nosetests -c $(git rev-parse --show-toplevel)/nose.cfg'

You can then run tests in the following manner:

    $ git test

And finally, to rerun only the tests that failed during the last run, you can
use the following:

    $ git test --failed

License
=======

Tomtom is licensed under the BSD license as mentioned in all source code files.
A copy of the license should be available with the source code.

[Github]: http://github.com/lelutin/tomtom
