# -*- coding: utf-8 -*-
"""Plugin library for Scout."""
import optparse


class ActionPlugin(object):
    """Base class for action plugins

    An empty group with no name is automatically created so that it can recieve
    options that aren't added to a group.

    The "interface" attribute is an important one: it is the interface to the
    note application (i.e. it is a Scout object). To avoid some cases where a
    DBus connection is not useful, it is not instantiated in the plugin's
    constructor but rather in the main script, just before calling the plugin's
    perform_action() method.

    """
    short_description = None
    usage = "%prog [options] <arguments>"

    def __init__(self):
        super(ActionPlugin, self).__init__()

        self.option_groups = []
        self.add_group(None)

    def add_option(self, *args, **kwargs):
        """Add a single option to the action's list of options.

        All arguments except one, the "group" keyword argument, are passed on
        to optparse.Option's constructor so the same options must be used.

        A group name can be specified with the keyword argument "group". If no
        "group" argument is present, the option will be added to the "None"
        group (e.g. the option will not be part of a group). If the group
        specified does not exists, a KeyError exception is raised.

        """
        group_name = kwargs.pop("group", None)

        if group_name not in [g.name for g in self.option_groups]:
            raise KeyError, "Option group '%s' does not exist yet."

        group = [g for g in self.option_groups if g.name == group_name][0]

        group.add_options([
            optparse.Option(*args, **kwargs)
        ])

    def add_group(self, name, description=""):
        """Create the 'name' option with an optional 'description'.

        If a group with the supplied name already exists, nothing is done.

        """
        group_names = [g.name for g in self.option_groups]

        if name not in group_names:
            self.option_groups.append(
                OptionGroup(name, description)
            )

    def add_option_library(self, library):
        """Add an option library to the option parser.

        An option library is a group of predefined options. The library must of
        a subclass of scout.plugins.OptionGroup, else a TypeError is raised.

        If the name of the library is already present in option groups, no
        action is taken.

        """
        if not isinstance(library, OptionGroup):
            msg = "Librairies must be of type scout.plugins.OptionGroup"
            raise TypeError, msg

        if library.name not in [g.name for g in self.option_groups]:
            self.option_groups.append(library)

    def init_options(self):
        """Initialize this action's options.

        Add options and option groups ready to be parsed. Default action
        behaviour is to have no option.

        """
        pass

    def perform_action(self, config, options, positional):
        """This is the entry point for running actions.

        This method should be redefined in plugin subclasses.

        Values parsed from the configuration file are assed in as 'options'.

        Parsed options and positional arguments are passed in from the main
        script as 'options' and 'positional', respectively.

        This method should print useful information to user, and interact with
        the user if necessary, but sing options from the command line is
        preferred to interaction in most cases.

        """
        pass


class OptionGroup(object):
    """An optparse.OptionGroup without attachement to a parser."""
    def __init__(self, name, description):
        super(OptionGroup, self).__init__()
        self.name = name
        self.description = description
        self.options = []

    def add_options(self, options):
        """Add a list of options to the group.

        The options must be of type optparse.Option or a TypeError exception is
        raised.

        """
        for option in options:
            if not isinstance(option, optparse.Option):
                msg = ''.join(["Options added to the group must be ",
                               "optparse.Option objects."])
                raise TypeError, msg

            self.options.append(option)

    def get_option(self, opt_string):
        """Get the option that uses the supplied string.

        Returns None if the option string is not found.

        """
        for option in self.options:
            if opt_string in option._short_opts \
                    or opt_string in option._long_opts:
                return option

        return None

    def remove_option(self, opt_string):
        """Remove the option that uses the supplied string."""
        option = self.get_option(opt_string)
        if option is not None:
            self.options.remove(option)


class FilteringGroup(OptionGroup):
    """A library of all command-line options for filtering notes."""
    def __init__(self, action_name):
        super(FilteringGroup, self).__init__(
            "Filtering",
            "Filter notes by different criteria."
        )

        action_map = {"action": action_name}

        options = [
            optparse.Option(
                "-b", action="callback", dest="books", metavar="BOOK",
                callback=self.book_callback, type="string",
                help=''.join(["%(action)s notes belonging to specified ",
                              "notebooks. It is a shortcut to option \"-t\" ",
                              "to specify notebooks more easily. For example, ",
                              "use \"-b HGTTG\" instead of ",
                              "\"-t system:notebook:HGTTG\". Use this option ",
                              "once for each desired book."]) % action_map
            ),
            optparse.Option(
                "-t",
                dest="tags", metavar="TAG", action="append", default=[],
                help=''.join(["%(action)s notes with specified tags. Use this ",
                              "option once for each desired tag. This option ",
                              "selects raw tags and could be useful for ",
                              "user-assigned tags."]) % action_map
            ),
            optparse.Option(
                "--with-templates",
                dest="templates", action="store_true", default=False,
                help=''.join(["Include template notes. This option is ",
                              "different from using \"-t system:template\" ",
                              "in that the latter used alone will only ",
                              "include the templates, while using ",
                              "\"--with-templates\" without specifying tags ",
                              "for selection will include all notes and ",
                              "templates."])
            ),
        ]

        self.add_options(options)

    def book_callback(self, dummy1, dummy2, value, parser):
        """Add a book to the requested tags to filter by."""
        tags = parser.values.tags

        tags.append("system:notebook:" + value)
