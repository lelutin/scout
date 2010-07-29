# Description

Scout : A CLI interface to Tomboy notes and Gnote

Scout is an interface to Tomboy notes or Gnote that uses DBus to
communicate. It presents a command-line interface and
tries to be as simple to use as possible. Different actions
can be taken to interact with Tomboy or Gnote. Actions are simple
to create, making the application easily extensible.

Current actions make it possible to list note names, display note contents,
search for text inside notes and to delete notes.

# Installing

## From source

To install scout from the source archive, use the setuptools installer:

    scout$ sudo python setup.py install

To see a short summary of what has changed between versions, consult the
[changelog wiki page][ChangeLog].

## Requirements

To run scout, you need to have dbus-python installed. On Debian or Ubuntu, use
the following command:

    # apt-get install python-dbus

On Fedora or Centos, use the following:

    # yum install dbus-python

# Use

To use scout the first argument must be an action name. For example, say you
want to get a list of all non-template notes. You can call the following:

    $ scout list

Arguments can be given to actions. The arguments available differ from one
action to the other. For example,
the "search" action requires an element to search for:

    $ scout search "text to search for"

You can obtain help on how to execute scout by giving it a "-h" or "--help"
argument. This will list the currently available actions you can use with
scout. To obtain more detail on what arguments can be used with an action, use
the option "-h" or "--help" and specify an action name at the same time. Both
of the two following commands call the detailed help for the action "display":

    $ scout --help display
    $ scout display -h

## Choosing the application

Scout can be used with either Tomboy or Gnote. Scout detects which one of
them is currently installed. If only one of them is present, it will
automatically connect to it.

However, in a context where both Tomboy and Gnote are installed, Scout cannot
determine which one to use unless it is specified as an argument to the command
line or in a configuration file.

A system-wide configuration file can be placed in ''/etc/scout.cfg''. Each
user can also create a configuration file in their home directory (e.g. either
''~/.scout/config'' or ''~/.config/scout/config''). Values in the user
configuration file will override those set in the system-wide configuration.
The configuration file should follow the Windows INI file format. To select the
application, the "application" option in the "scout" section should be set to
either Tomboy or Gnote. Ex. (Tomboy):

    [scout]
    application: Tomboy

The command line argument takes precedence over the value set in the
configuration file. Here's how to list notes from Gnote:

    scout list --application=Gnote

# Mailing list

If you have any questions about how to use Scout, if you want to report or
discuss a problem you currently have, or if you want to contribute patches (see
below), you should subscribe to the [mailing list].

The list is public, so anyone can view the archives on the list's web page
without having to log in, but in order to send messages to the list, you must
be subscribed to it. If you want to subscribe but don't have a google account
(and don't want one), just send a message to scout-list@googlegroups.com.

# Contributing

All contributions to the code are welcome. Contributed code should come with
new unit tests for added functions and new or modified acceptance tests for
command line interface modifications. The main repository is on [GitHub]. Send
patches to the [mailing list] (See the section about the list for more
details).

Commit messages should contain a "Signed-off-by:" line with you name and e-mail
address, in the same fashion as contributions to git or the Linux kernel. This
line attests that you are willing to license your code under the same license
as the one used by the project (e.g. BSD). To add such a line with git, use the
"-s" argument to git-commit.

## Tests

To be able to run the unit or acceptance tests, you will need to have pymox
and nose installed. On Debian or Ubuntu, use the following command to install
them:

    # apt-get install python-mox python-nose

The tests can be run using one of two methods. The first one is through setup.py
like following:

    scout$ python setup.py test

The second method, being the fastest and most flexible one, is by calling
nose's nosetests script. A configuration file is included in the base directory
to make running the unit tests easier. From the base directory:

    scout$ nostests -c nose.cfg

See the configuration file for some usefull lines that can be uncommented.

One useful trick with git to make running tests easier is to set an alias in
the following manner (make sure to use single quotes, the !  and $ characters
are interpreted by bash if it is inside double quotes):

    $ git config --global alias.test '!nosetests -c $(git rev-parse --show-toplevel)/nose.cfg'

You can then run tests in the following manner:

    $ git test

And finally, to rerun only the tests that failed during the last run, you can
use the following:

    $ git test --failed

# License

Scout can be used, distributed and modified. All files are under a BSD license
with the exception of the "format-subst.pl" script which is under a GPLv2
license.  "format-subst.pl" was written by Avery Pennarun for the "bup"
project.

A copy of the BSD license should be available with the source code. Also, a
short license notice can be found in all files.

[Github]: http://github.com/lelutin/scout
[mailing list]: http://groups.google.com/group/scout-list
[ChangeLog]:http://wiki.github.com/lelutin/scout/changelog
