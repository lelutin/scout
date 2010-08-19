# -*- coding: utf-8 -*-
"""Acceptance tests for Scout.

This defines the use cases and expected interaction with users.

"""
import sys
import os
import dbus
import pkg_resources
import ConfigParser as configparser

from .utils import BasicMocking, CLIMocking, data

from scout import cli
from scout import plugins
from scout.version import SCOUT_VERSION

#TODO split this up in smaller classes
class AcceptanceTests(BasicMocking, CLIMocking):
    """Acceptance tests.

    Define what the expected behaviour is from the user's point of view.

    Those tests are meant to verify correct functionality of the whole
    application, so they mock out external library dependencies only.

    """
    def setUp(self):
        # Nearly all tests need to mock out Scout's initialization
        super(AcceptanceTests, self).setUp()

        self.mock_out_app_config()
        self.mock_out_dbus()

    def mock_out_app_config(self):
        """Mock out configuration parsing."""
        fake_parser = self.m.CreateMock(configparser.SafeConfigParser)

        self.m.StubOutWithMock(
            configparser,
            "SafeConfigParser",
            use_mock_anything=True
        )

        self.m.StubOutWithMock(os.path, "expanduser")

        configparser.SafeConfigParser()\
            .AndReturn(fake_parser)

        os.path.expanduser("~/.scout/config")\
            .AndReturn("/home/bobby/.scout/config")
        os.path.expanduser("~/.config/scout/config")\
            .AndReturn("/home/bobby/.config/scout/config")

        fake_parser.read([
            "/etc/scout.cfg",
            "/home/bobby/.scout/config",
            "/home/bobby/.config/scout/config",
        ])

        fake_parser.has_section("scout")\
            .AndReturn(False)

        fake_parser.add_section("scout")

        fake_parser.options("scout")\
            .AndReturn( [] )

        fake_parser.has_option("scout", "application")\
            .AndReturn(False)

    def mock_out_dbus(self, application=None):
        """Mock out DBus interaction with the specified application."""
        self.m.StubOutWithMock(dbus, "SessionBus", use_mock_anything=True)
        self.m.StubOutWithMock(dbus, "Interface", use_mock_anything=True)
        session_bus = self.m.CreateMockAnything()
        dbus_object = self.m.CreateMockAnything()
        self.dbus_interface = self.m.CreateMockAnything()

        dbus.SessionBus()\
            .AndReturn(session_bus)

        if application is not None:
            # choice of application forced
            session_bus.get_object(
                "org.gnome.%s" % application,
                "/org/gnome/%s/RemoteControl" % application
            ).AndReturn(dbus_object)
        else:
            application = "Tomboy"

            session_bus.get_object(
                "org.gnome.Tomboy",
                "/org/gnome/Tomboy/RemoteControl"
            ).AndReturn(dbus_object)
            session_bus.get_object(
                "org.gnome.Gnote",
                "/org/gnome/Gnote/RemoteControl"
            ).AndRaise(dbus.DBusException)

        dbus.Interface(
            dbus_object,
            "org.gnome.%s.RemoteControl" % application
        ).AndReturn(self.dbus_interface)

    def mock_out_listing(self, notes):
        """Mock out retrieval of 'notes' from DBus."""
        self.dbus_interface.ListAllNotes()\
            .AndReturn([n.uri for n in notes])
        for note in notes:
            self.dbus_interface.GetNoteTitle(note.uri)\
                .AndReturn(note.title)
            self.dbus_interface.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            self.dbus_interface.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

    def mock_out_get_notes_by_names(self, notes):
        """Mock out searching for 'notes' by their names."""
        for note in notes:
            self.dbus_interface.FindNote(note.title)\
                .AndReturn(note.uri)

        for note in notes:
            self.dbus_interface.GetNoteChangeDate(note.uri)\
                .AndReturn(note.date)
            self.dbus_interface.GetTagsForNote(note.uri)\
                .AndReturn(note.tags)

    def test_no_argument(self):
        """Acceptance: scout called without arguments must print usage."""
        # No dbus interaction for this test
        self.remove_mocks()

        sys.argv = ["app_name", ]
        old_docstring = cli.__doc__
        cli.__doc__ = "\n".join([
            "command -h",
            "command action",
            "",
            "unused",
            "but fake",
            "help text"
        ])

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.exception_wrapped_main
        )

        self.m.VerifyAll()

        # Test that usage comes from the script's docstring.
        self.assertEqual(
            ("\n" * 2).join([
                "\n".join(cli.__doc__.splitlines()[:3]),
                data("help_more_details")
            ]),
            sys.stderr.getvalue()
        )

        cli.__doc__ = old_docstring

    def test_unknown_action(self):
        """Acceptance: Giving an unknown action name must print an error."""
        # No dbus interaction for this test
        self.remove_mocks()

        self.m.ReplayAll()

        sys.argv = ["app_name", "unexistant_action"]
        self.assertRaises( SystemExit, cli.exception_wrapped_main )

        self.m.VerifyAll()

        self.assertEqual(
            data("unknown_action"),
            sys.stderr.getvalue()
        )

    def test_action_list(self):
        """Acceptance: Action "list -n" prints a list of the last n notes."""
        list_of_notes = self.full_list_of_notes()

        self.mock_out_listing(list_of_notes[:10])

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "list", "-n", "10"]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEquals(
            data("expected_list"),
            sys.stdout.getvalue()
        )

    def test_full_list(self):
        """Acceptance: Action "list" alone produces a list of all notes."""
        list_of_notes = self.full_list_of_notes()

        self.mock_out_listing(list_of_notes)

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "list"]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEquals(
            ''.join([data("expected_list"), data("list_appendix")]),
            sys.stdout.getvalue()
        )

    def test_notes_displaying(self):
        """Acceptance: Action "display" prints the content given note names."""
        list_of_notes = self.full_list_of_notes()

        todo = list_of_notes[1]
        python_work = list_of_notes[4]
        separator = "\n==========================\n"
        note_lines = data("notes/TODO-list").splitlines()

        note_lines[0] = \
            "%s  (system:notebook:reminders, system:notebook:pim)" % (
                note_lines[0],
            )

        expected_result_list = [
            "\n".join(note_lines),
            data("notes/python-work")[:-1]
        ]

        self.mock_out_listing(list_of_notes)

        self.dbus_interface.GetNoteContents(todo.uri)\
            .AndReturn(data("notes/TODO-list"))
        self.dbus_interface.GetNoteContents(python_work.uri)\
            .AndReturn(data("notes/python-work"))

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "display", "TODO-list", "python-work"]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEquals(
            "%s\n" % separator.join(expected_result_list),
            sys.stdout.getvalue()
        )

    def test_note_does_not_exist(self):
        """Acceptance: Specified note non-existant: display an error."""
        list_of_notes = self.full_list_of_notes()
        self.mock_out_listing(list_of_notes)

        self.m.ReplayAll()

        sys.argv = ["app_name", "display", "unexistant"]
        self.assertRaises(SystemExit, cli.exception_wrapped_main)

        self.assertEquals(
            data("unexistant_note_error"),
            sys.stderr.getvalue()
        )

        self.m.VerifyAll()

    def test_display_zero_argument(self):
        """Acceptance: Action "display" with no argument prints an error."""
        sys.argv = ["app_name", "display"]

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.exception_wrapped_main
        )

        self.m.VerifyAll()

        self.assertEquals(
            data("display_no_note_name_error"),
            sys.stderr.getvalue()
        )

    def test_search(self):
        """Acceptance: Action "search" searches in all notes, case-indep."""
        list_of_notes = self.full_list_of_notes()

        self.mock_out_listing(list_of_notes)

        # Forget about the last note (a template)
        for note in list_of_notes[:-1]:
            self.dbus_interface.GetNoteContents(note.uri)\
                .AndReturn(data("notes/%s" % note.title))

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "search", "john doe"]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEquals(
            data("search_results"),
            sys.stdout.getvalue()
        )

    def test_search_specific_notes(self):
        """Acceptance: Action "search" restricts the search to given notes."""
        list_of_notes = self.full_list_of_notes()

        requested_notes = [
            list_of_notes[3],
            list_of_notes[4],
            list_of_notes[6],
        ]

        self.mock_out_listing(list_of_notes)

        for note in requested_notes:
            self.dbus_interface.GetNoteContents(note.uri)\
                .AndReturn(data("notes/%s" % note.title))

        self.m.ReplayAll()

        sys.argv = ["unused_prog_name", "search", "python"] + \
                [n.title for n in requested_notes]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEquals(
            data("specific_search_results"),
            sys.stdout.getvalue()
        )

    def test_search_zero_arguments(self):
        """Acceptance: Action "search" with no argument prints an error."""
        sys.argv = ["unused_prog_name", "search"]

        self.m.ReplayAll()

        self.assertRaises(
            SystemExit,
            cli.exception_wrapped_main
        )

        self.m.VerifyAll()

        self.assertEquals(
            data("search_no_argument_error"),
            sys.stderr.getvalue()
        )

    def verify_main_help(self, argument):
        """Test that we actually get the main help."""
        # Remove stubs and reset mocks for dbus that the setUp method
        # constructed as there will be no dbus interaction.
        self.remove_mocks()

        self.m.StubOutWithMock(pkg_resources, "iter_entry_points")

        old_docstring = cli.__doc__
        cli.__doc__ = "\n".join([
            "some",
            "non-",
            "useful",
            "but fake",
            "help text "
        ])

        fake_list = [
            "  action1 : this action does something",
            "  action2 : this one too",
            "  action3 : No description available.",
        ]

        fake_plugin_list = self.n_mocks(3)
        fake_plugin_list[0].name = "action1"
        fake_plugin_list[1].name = "action2"
        fake_plugin_list[2].name = "action3"

        fake_classes = self.n_mocks(3, plugins.ActionPlugin)
        fake_classes[0].short_description = "this action does something"
        fake_classes[1].short_description = "this one too"
        for fake_class in fake_classes:
            fake_class.__bases__ = ( plugins.ActionPlugin, )

        pkg_resources.iter_entry_points(group="scout.actions")\
            .AndReturn( (x for x in fake_plugin_list) )

        for index, entry_point in enumerate(fake_plugin_list):
            fake_class = fake_classes[index]
            entry_point.load()\
                .AndReturn(fake_class)

        self.m.ReplayAll()

        sys.argv = ["app_name", argument]
        self.assertRaises(
            SystemExit,
            cli.exception_wrapped_main
        )

        self.m.VerifyAll()

        # The help should be displayed using scout's docstring.
        self.assertEquals(
            "%s%s\n" % (cli.__doc__[:-1], "\n".join(fake_list)),
            sys.stdout.getvalue()
        )

        cli.__doc__ = old_docstring

    def test_help_on_base_level(self):
        """Acceptance: Using "-h" or "--help" alone prints basic help."""
        self.verify_main_help("-h")

    def test_help_action(self):
        """Acceptance: "help" as an action name."""
        self.verify_main_help("help")

    def test_filter_notes_with_templates(self):
        """Acceptance: Using "--with-templates" lists notes and templates."""
        list_of_notes = self.full_list_of_notes()

        self.mock_out_listing(list_of_notes)

        self.m.ReplayAll()

        sys.argv = [
            "app_name", "list",
            "--with-templates"
        ]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEqual(
            ''.join([data("expected_list"),
                     data("list_appendix"),
                     data("normally_hidden_template")]),
            sys.stdout.getvalue()
        )

    def test_filter_notes_by_tags(self):
        """Acceptance: Using "-t" limits the notes by tags."""
        list_of_notes = self.full_list_of_notes()

        self.mock_out_listing(list_of_notes)

        self.m.ReplayAll()

        sys.argv = [
            "app_name", "list",
            "-t", "system:notebook:pim",
            "-t", "projects"
        ]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEqual(
            data("tag_limited_list"),
            sys.stdout.getvalue()
        )

    def test_filter_notes_by_books(self):
        """Acceptance: Using "-b" limits the notes by notebooks."""
        list_of_notes = self.full_list_of_notes()

        self.mock_out_listing(list_of_notes)

        self.m.ReplayAll()

        sys.argv = ["app_name", "list", "-b", "pim", "-b", "reminders"]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEqual(
            data("book_limited_list"),
            sys.stdout.getvalue()
        )

    def verify_help_text(self, args, text):
        """Mock out printing a help text before exiting."""
        # No DBus interaction should occur if we get a help text.
        self.remove_mocks()

        sys.argv = args

        # Mock out sys.exit : optparse calls this when help is displayed
        self.m.StubOutWithMock(sys, "exit")
        sys.exit(0).AndRaise(SystemExit)

        self.m.ReplayAll()

        self.assertRaises(SystemExit, cli.exception_wrapped_main)
        self.assertEquals(
            text,
            sys.stdout.getvalue()
        )

        self.m.VerifyAll()

    def test_help_before_action_name(self):
        """Acceptance: Using "-h" before an action displays detailed help."""
        self.verify_help_text(
            [
                "app_name",
                "-h",
                "list"
            ],
            data("help_details_list") % {"action": "List"}
        )

    def test_help_pseudo_action_before_action_name(self):
        """Acceptance: Using "-h" before an action displays detailed help."""
        self.verify_help_text(
            [
                "app_name",
                "help",
                "version"
            ],
            data("help_details_version")
        )

    def test_help_display_specific(self):
        """Acceptance: Detailed help using "-h" after "display" action."""
        self.verify_help_text(
            [
                "app_name",
                "display",
                "--help"
            ],
            data("help_details_display")
        )

    def test_help_list_specific(self):
        """Acceptance: Detailed help using "-h" after "list" action."""
        self.verify_help_text(
            [
                "app_name",
                "list",
                "--help"
            ],
            data("help_details_list") % {"action": "List"}
        )

    def test_help_search_specific(self):
        """Acceptance: Detailed help using "-h" after "search" action."""
        self.verify_help_text(
            [
                "app_name",
                "search",
                "--help"
            ],
            data("help_details_search") % {"action": "Search"}
        )

    def test_tomboy_version(self):
        """Acceptance: Get Tomboy's version."""
        self.dbus_interface.Version()\
            .AndReturn(u'1.0.1')

        sys.argv = ["app_name", "version"]

        self.m.ReplayAll()
        cli.exception_wrapped_main()
        self.m.VerifyAll()

        self.assertEqual(
            data("tomboy_version_output") % (SCOUT_VERSION, "Tomboy"),
            sys.stdout.getvalue()
        )

    def test_help_version_specific(self):
        """Acceptance: Detailed help using "-h" after "version" action."""
        self.verify_help_text(
            [
                "app_name",
                "version",
                "--help"
            ],
            data("help_details_version")
        )

    def test_list_using_gnote(self):
        """Acceptance: Specifying --application forces connection."""
        # Reset stubs and mocks. We need to mock out dbus differently.
        self.remove_mocks()

        self.mock_out_dbus("Gnote")

        list_of_notes = self.full_list_of_notes()

        self.mock_out_listing(list_of_notes[:10])

        self.m.ReplayAll()

        sys.argv = [
            "unused_prog_name",
            "list",
            "-n", "10",
            "--application", "Gnote"
        ]
        cli.exception_wrapped_main()

        self.m.VerifyAll()

        self.assertEquals(
            data("expected_list"),
            sys.stdout.getvalue()
        )

    def verify_delete_notes(self, tags, names, all_notes, dry_run):
        """Test note deletion."""
        list_of_notes = self.full_list_of_notes()

        if all_notes or tags or names:
            self.mock_out_listing(list_of_notes)

        if all_notes:
            expected_notes = list_of_notes
        elif tags or names:
            expected_notes = [
                n for n in list_of_notes
                if set(n.tags).intersection(tags)
                   or n.title in names
            ]
        else:
            expected_notes = []

        if not dry_run:
            for note in expected_notes:
                self.dbus_interface.DeleteNote(note.uri)

        self.m.ReplayAll()

        sys.argv = [
            "unused_prog_name",
            "delete",
        ]
        if dry_run:
            sys.argv.append("--dry-run")
        if all_notes:
            sys.argv.append("--all-notes")

        for tag in tags:
            sys.argv.extend([
                "-t",
                tag,
            ])

        for name in names:
            sys.argv.append(name)

        if not all_notes and not tags and not names:
            self.assertRaises(
                SystemExit,
                cli.exception_wrapped_main
            )
        else:
            cli.exception_wrapped_main()

        self.m.VerifyAll()

    def test_delete_notes(self):
        """Acceptance: Delete a list of notes."""
        self.verify_delete_notes(
            tags=["system:notebook:pim"],
            names=["TDD"],
            all_notes=False,
            dry_run=False
        )

    def test_delete_notes_dry_run(self):
        """Acceptance: Dry run of note deletion."""
        self.verify_delete_notes(
            tags=["system:notebook:pim"],
            names=["TDD"],
            all_notes=False,
            dry_run=True
        )

        self.assertEqual(
            data("delete_dry_run_list"),
            sys.stdout.getvalue()
        )

    def test_delete_notes_no_argument(self):
        """Acceptance: Delete without argument prints a message."""
        self.verify_delete_notes(
            tags=[],
            names=[],
            all_notes=False,
            dry_run=False
        )

        self.assertEqual(
            data("delete_no_argument_msg"),
            sys.stdout.getvalue()
        )

    def test_delete_notes_all_notes(self):
        """Acceptance: Delete all notes."""
        self.verify_delete_notes(
            tags=[],
            names=[],
            all_notes=True,
            dry_run=False
        )

    def test_help_delete_specific(self):
        """Acceptance: Detailed help using "-h" after "version" action."""
        self.verify_help_text(
            [
                "app_name",
                "delete",
                "--help"
            ],
            data("help_details_delete")
        )
