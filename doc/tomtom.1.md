% tomtom(1) Tomtom %TOMTOM_VERSION%
% Gabriel Filion <lelutin@gmail.com>
% 2010-03-25

# NAME

tomtom - CLI interface to Tomboy or Gnote via DBus

# SYNOPSIS

tomtom (h|--help) [command]

tomtom \<command\> [options...]

# DESCRIPTION

`tomtom` is an interface to note-taking applications `Tomboy notes` and `Gnote`
that uses DBus to communicate with them. It presents a command-line interface
and tries to be as simple to use as possible. Different actions can be taken to
interact with Tomboy or Gnote. Actions are simple to create, making the
application easily extensible.

To obtain details about how to invoke subcommands, use the "-h" option followed
by the subcommand name.

# SUBCOMMANDS

`list`
:   List note names and other useful information about them.
`display`
:   Show the contents of one or more notes.
`search`
:   Perform a textual search on your notes' contents.
`delete`
:   Delete one or more notes, or an entire book.
`version`
:   Show version tags from Tomtom and the application it connects to.

# EXAMPLES

List the 10 notes last modified
:   tomtom list -n 10
Display the contents of note "thing X"
:   tomtom display "thing X"
Search for "needle" in notes of the "haystack" book
:   tomtom search -b haystack needle
Delete notes with the tag "old_and_busted"
:   tomtom delete -t old_and_busted

# SEE ALSO

See the *README.markdown* file for more information.

The project's page is situated at <http://github.com/lelutin/tomtom>.

# BUGS

To report issues, go to the "issues" section of the projet's page:
<http://github.com/lelutin/tomtom/issues>.
