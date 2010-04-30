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
"""Plugin library for Scout.

This module defines base code for Scout plugins. The actions use the classes
present here to simplify their work.

Classes:
    ActionPlugin -- base class for plugins. defines basic functionality
    OptionGroup -- a group containing options, a name and a description.
    FilteringGroup -- OptionGroup library. defines common options for filtering.

"""
import optparse

class ActionPlugin(object):
    """Base class for action plugins"""
    short_description = None
    usage = "%prog [options] <arguments>"

    def __init__(self):
        """Setup the Tomboy interface.

        Initialize the list of option groups and create a group with name=None
        automatically so that action can be placed in no group without having
        to actually create a group (which would feel paradoxal).

        The attribute "tomboy_interface" is not instantiated here. Some
        situations require that we do not instantiate a Scout object (thus
        opening a DBus connection to the Tomboy application). One such example
        is displaying an action's help text. Instantiation occurs just before
        the action's "perform_action" method is called.

        """
        super(ActionPlugin, self).__init__()

        self.option_groups = []
        self.add_group(None)

    def add_option(self, *args, **kwargs):
        """Add a single option to the action's list of options.

        Add an option to the right group. The group name must be specified by
        the keyword argument "group". If no "group" argument is present, the
        option will be added to the "None" group (e.g. the option will not be
        part of a group). If the group specified does not exists, a SyntaxError
        exception is raised.

        Arguments:
            group -- The name of the group. None for no group.
            *args -- Will be passed to the Option constructor
            **kwargs -- Will be passed to the Option constructor (not "group")

        """
        group_name = kwargs.pop("group", None)

        group_names = [g.name for g in self.option_groups]

        if group_name not in group_names:
            raise KeyError, "Option group '%s' does not exist yet."

        group = [g for g in self.option_groups if g.name == group_name][0]

        group.add_options([
            optparse.Option(*args, **kwargs)
        ])

    def add_group(self, name, description=""):
        """Create an option group in the action's list of options.

        Create an empty group of options. The group will be named according the
        name argument. A description can be given to the description arguement.
        If a group with the supplied name already exists, nothing is done.

        ActionPlugin automatically creates a group with name=None. This group
        collects options that should not be part of a group.

        Arguments:
            name -- string representing the name of the group.
            description -- string printed under the group name in help output.

        """
        group_names = [g.name for g in self.option_groups]

        # If the group already exists, nothing to do.
        if name not in group_names:
            self.option_groups.append(
                OptionGroup(name, description)
            )

    def add_option_library(self, library):
        """Add an option library to the option parser.

        Add an option library (a group of predefined options) in the list of
        groups of options. The library must of a subclass of
        scout.plugins.OptionGroup. If the name of the library is already
        present in option groups, no action is taken.

        Arguments:
            library -- An instance of a subclass of scout.plugins.OptionGroup

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

        This method is the starting point in performing the action. Once this
        method is called, optparse will have done its job. It receives an
        object with the options parsed as attributes and a list of positional
        arguments. This method should print useful information to user, and
        interact with the user if necessary. Using options from the command
        line is preferred to interaction in most cases.

        This method should be redifined in plugin subclasses.

        Arguments:
            options -- An object from optparse containing options as attributes
            positional -- A list of positional arguments

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

        Add multiple options from a list to the option group. The options must
        be of type optparse.Option or a TypeError exception is raised.

        Arguments:
            options -- A list that should contain only optparse.Option objects.

        """
        for option in options:
            if not isinstance(option, optparse.Option):
                msg = "Options added to the group must be " + \
                    "optparse.Option objects."
                raise TypeError, msg

            self.options.append(option)

    def get_option(self, opt_string):
        """Get the option that uses the supplied string."""
        for option in self.options:
            if opt_string in option._short_opts \
                    or opt_string in option._long_opts:
                return option

        return None

    def remove_option(self, opt_string):
        """Remove the option that uses the supplied string."""
        option = self.get_option(opt_string)
        if option is not None:
            self.options.remove( option )

class FilteringGroup(OptionGroup):
    """An option group with all options for filtering notes."""
    def __init__(self, action_name):
        super(FilteringGroup, self).__init__(
            "Filtering",
            "Filter notes by different criteria."
        )

        action_map = { "action": action_name }

        options = [
            optparse.Option(
                "-b", action="callback", dest="books", metavar="BOOK",
                callback=self.book_callback, type="string",
                help="""%(action)s notes belonging to """ % action_map + \
                """specified notebooks. It is a shortcut to option "-t" to """
                """specify notebooks more easily. For example, use"""
                """ "-b HGTTG" instead of "-t system:notebook:HGTTG". Use """
                """this option once for each desired book."""
            ),
            optparse.Option(
                "-t",
                dest="tags", metavar="TAG", action="append", default=[],
                help="""%(action)s notes with """ % action_map + \
                """specified tags. Use this option once for each desired """
                """tag. This option selects raw tags and could be useful for """
                """user-assigned tags."""
            ),
            optparse.Option(
                "--with-templates",
                dest="templates", action="store_true", default=False,
                help="""Include template notes. This option is """
                """different from using "-t system:template" in that the """
                """latter used alone will only include the templates, while """
                """"using "--with-templates" without specifying tags for """
                """selection will include all notes and templates."""
            ),
        ]

        self.add_options(options)

    def book_callback(self, dummy1, dummy2, value, parser):
        """Add a book to the requested tags to filter by."""
        tags = parser.values.tags

        tags.append("system:notebook:" + value)
