% scout-plugins(1) Scout %SCOUT_VERSION%
% Gabriel Filion <gabster@lelutin.ca>
% %SCOUT_DATE%

# NAME

scout-plugins - How to write plugins for Scout

# DESCRIPTION

Sub-commands to Scout are called actions. A sub-command should represent an
action that the user performs on notes.

Action modules are subclasses of `scout.plugins.ActionPlugin`. The
`perform_action` is the action's entry point -- so the main program will call
this method to delegate control -- and this method must be overridden. It can
import scout classes and any other packages to help in its task. An action
should use scout to get or send information from or to Tomboy or Gnote and use
the standard input, output and error streams as its interface with the user.

Actions are listed dynamically in scout's basic help message and will appear as
soon as  `setuptools` knows about the subscriptiong to the entry point. Their
descriptions are taken from the first line of the action module's docstring.
Make sure to keep the docstring's first line short but precise. The entire line
(with two leading spaces for indentation, the action's name and its
description) should fit in less than 80 characters.

Subscribing an action to the `setuptools` entry point is done via a `setup.py`
script. For example, let's subscribe a new action named `backup` that is
defined in the module `scout-backup` in the class named `BackupAction`:

    from setuptools import setup
    setup(
        name="scout-backup",
        # ...
        entry_points = {
            "scout.actions": [
                "backup = scout-backup::BackupAction",
            ],
        }
    )

`KeyboardInterrupt` exceptions are handled by the main application. An action
can intercept this exception if it needs to rollback an operation in order to
finish its work in a consistant state. The user should be warned right away
that the application is trying to stop its work. After the state is safe, the
action should re-raise the `KeyboardInterrupt` exception so that the
application exits cleanly.

# SEE ALSO

https://github.com/lelutin/scout/wiki/Plugins

# SCOUT

Part of the `scout`(1) project.
