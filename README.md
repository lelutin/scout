# Scout

Scout : A CLI interface to Tomboy notes and Gnote

Scout is an interface to Tomboy notes or Gnote that uses DBus to
communicate. It presents a command-line interface and
tries to be as simple to use as possible. Different actions
can be taken to interact with Tomboy or Gnote. Actions are simple
to create, making the application easily extensible.

Current actions make it possible to list note names, display note contents,
search for text inside notes and to delete notes.

## Use

To use scout the first argument must be an action name. For example, say you
want to get a list of all non-template notes. You can call the following:

    scout list

Arguments can be given to actions. The arguments available differ from one
action to the other. For example,
the "search" action requires an element to search for:

    scout search "text to search for"

You can obtain help on how to execute scout by giving it a "-h" or "--help"
argument. This will list the currently available actions you can use with
scout. To obtain more detail on what arguments can be used with an action, use
the option "-h" or "--help" and specify an action name at the same time. Both
of the two following commands call the detailed help for the action "display":

    scout --help display
    # or:
    scout display -h

### Choosing the note application

Scout can be used with either Tomboy or Gnote. Scout detects which one of
them is currently installed. If only one of them is present, it will
automatically connect to it.

However, in a context where both Tomboy and Gnote are installed, Scout cannot
determine which one to use unless it is specified as an argument to the command
line or in a configuration file.

A system-wide configuration file can be placed in `/etc/scout.cfg`. Each
user can also create a configuration file in their home directory (e.g. either
`~/.scout/config` or `~/.config/scout/config`). Values in the user
configuration file will override those set in the system-wide configuration.
The configuration file should follow the Windows INI file format. To select the
application, the "application" option in the "scout" section should be set to
either Tomboy or Gnote. Ex. (Tomboy):

    [scout]
    application: Tomboy

The command line argument takes precedence over the value set in the
configuration file. Here's how to list notes from Gnote:

    scout list --application=Gnote

## Requirements

You need to have `libdbus` installed in order for the `dbus-python` library to
be useful. In theory, though if you have already installed Tomboy or Gnote
beforehand you should already have this library on your system.

You also need your note application to be running, otherwise you might be
getting errors about the dbus interface not existing.

Also, for pip to be able to install `dbus-python`, you need dev libraries to be
present on your system. In debian you can install them with:

    sudo apt install libdbus-1-dev libdbus-glib-1-dev

## Installing from source

This project is setup to be used with `pip` so you can install it and/or build
a wheel as you would normally do with that tool.

To see a short summary of what has changed between versions, consult the
[changelog wiki page][ChangeLog].

## Contributing

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

## Development environment

The recommended way to have a development environement is to create a python
virtualenv as shown below:

    python3 -m venv ve
    source ve/bin/activate

Then in the venv install scout in "develop" mode and its dependencies with pip
so that you can test it while developing:

    pip install -e .[test]

## Tests

To run tests, call the `nosetests` script (which comes with nose). From the
base directory, with the venv activated:

    nostests -c nose.cfg

You can specify any of `nose.cfg`, `nose.unit.cfg` and `nose.functional.cfg` to
chose which tests will run, respectively all tests, only unit tests, and only
functional tests. Only the file `nose.unit.cfg` shows test coverage since this
measure is only relevant with those tests alone.

# License

Scout can be used, distributed and modified. All files are under a BSD-4-clause
license.

A copy of the BSD license should be available with the source code. Also, a
short license notice can be found in all files.

[Github]: https://github.com/lelutin/scout
[ChangeLog]:https://github.com/lelutin/scout/wiki/ChangeLog
