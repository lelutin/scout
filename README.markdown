tomtom : A CLI interface to Tomboy

Installing
==========

To install tomtom, use the setuptools installer:

    $ sudo python setup.py install

Requirements
------------

To run tomtom, you need to have dbus-python installed. On Debian or Ubuntu, use
the following command:

    $ sudo apt-get install python-dbus

On Fedora or Centos, use the following:

    $ sudo yum install dbus-python

For those who would like to work on tomtom's code, to be able to run unit
tests, you will need to have pymox installed. On Debian or Ubuntu, use the
following command:

    $ apt-get install python-mox

Use
===

You can obtain help on how to execute tomtom by giving it a "-h" or "--help"
argument. This will list the currently available actions you can use with
tomtom. If you use "-h"/"--help" and specify an action name at the same time, a
detailed help will be displayed for that action.

To use tomtom the first argument must be an action name. For example, say you
want to get a list of all notes. You can call the following:

    $ tomtom list

Arguments can be given to actions. The arguments available are dependant on the
action. To obtain detail on what arguments can be used with an action, call the
detailed help on this action as described above. For example, the "search"
action requires an element to search for:

    $ tomtom search "text to search"

License
=======

tomtom is licensed under the BSD license as mentioned in all source code files.
A copy of the license note is available under the "legalese" directory in the
source code.
