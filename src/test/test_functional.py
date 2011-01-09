# -*- coding: utf-8 -*-
"""Acceptance tests for Scout.

Define what the expected behaviour is from the user's point of view; so: use
cases and expected interaction with users.

Those tests are meant to verify correct functionality of the whole
application, so they mock out external library dependencies only.

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


class FunctionalTests(BasicMocking, CLIMocking):
    """Common behaviour for all functional tests."""

    def setUp(self):
        # Nearly all tests need to mock out Scout's initialization
        super(FunctionalTests, self).setUp()

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
            .AndReturn([])

        fake_parser.has_option("scout", "application")\
            .AndReturn(False)

        fake_parser.has_option("scout", "display")\
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

    def verify_help_text(self, args, text):
        """Mock out printing a help text before exiting."""
        # No DBus interaction should occur if we get a help text.
        self.remove_mocks()

        sys.argv = args

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            text,
            sys.stdout.getvalue()
        )


class MainTests(FunctionalTests):
    """Tests that verify the main program's behaviour."""

    def test_no_argument(self):
        """F Main: scout called without arguments must print usage."""
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
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        # Test that usage comes from the script's docstring.
        self.assertEqual(
            "\n\n".join([
                "\n".join(cli.__doc__.splitlines()[:3]),
                data("help_more_details")
            ]),
            sys.stderr.getvalue()
        )

        cli.__doc__ = old_docstring

    def test_unknown_action(self):
        """F Main: Giving an unknown action name must print an error."""
        # No dbus interaction for this test
        self.remove_mocks()
        sys.argv = ["app_name", "unexistant_action"]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEqual(
            data("unknown_action"),
            sys.stderr.getvalue()
        )

    def test_using_gnote(self):
        """F Main: Specifying --application forces connection."""
        # Reset stubs and mocks. We need to mock out dbus differently.
        self.remove_mocks()

        self.mock_out_dbus("Gnote")
        list_of_notes = self.full_list_of_notes()
        self.mock_out_listing(list_of_notes[:10])

        sys.argv = [
            "unused_prog_name",
            "list",
            "-n", "10",
            "--application", "Gnote"
        ]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            data("expected_list"),
            sys.stdout.getvalue()
        )

    def verify_main_help(self, argument):
        """Test that we actually get the main help."""
        # Remove stubs and reset mocks for DBus that the setUp method
        # constructed as there will be no DBus interaction.
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
            fake_class.__bases__ = (plugins.ActionPlugin, )

        pkg_resources.iter_entry_points(group="scout.actions")\
            .AndReturn((x for x in fake_plugin_list))

        for index, entry_point in enumerate(fake_plugin_list):
            fake_class = fake_classes[index]
            entry_point.load()\
                .AndReturn(fake_class)

        sys.argv = ["app_name", argument]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        # The help should be displayed using scout's docstring.
        self.assertEquals(
            "%s%s\n" % (cli.__doc__[:-1], "\n".join(fake_list)),
            sys.stdout.getvalue()
        )

        cli.__doc__ = old_docstring

    def test_help_on_base_level(self):
        """F main: Using "-h" or "--help" alone prints basic help."""
        self.verify_main_help("-h")

    def test_help_action(self):
        """F Main: "help" as an action name."""
        self.verify_main_help("help")

    def test_help_before_action_name(self):
        """F Main: Using "-h" before an action displays detailed help."""
        self.verify_help_text(
            ["app_name", "-h", "list"],
            data("help_details_list") % {"action": "List"}
        )

    def test_help_pseudo_action_before_action_name(self):
        """F Main: Using "-h" before an action displays detailed help."""
        self.verify_help_text(
            ["app_name", "help", "version"],
            data("help_details_version")
        )


class ListTests(FunctionalTests):
    """Tests for the 'list' action."""

    def test_action_list(self):
        """F List: Action "list -n" prints a list of the last n notes."""
        list_of_notes = self.full_list_of_notes()
        self.mock_out_listing(list_of_notes[:10])
        sys.argv = ["unused_prog_name", "list", "-n", "10"]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            data("expected_list"),
            sys.stdout.getvalue()
        )

    def test_full_list(self):
        """F List: Action "list" alone produces a list of all notes."""
        list_of_notes = self.full_list_of_notes()
        self.mock_out_listing(list_of_notes)
        sys.argv = ["unused_prog_name", "list"]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            ''.join([data("expected_list"), data("list_appendix")]),
            sys.stdout.getvalue()
        )

    def test_help_list_specific(self):
        """F List: Detailed help using "-h" after "list" action."""
        self.verify_help_text(
            ["app_name", "list", "--help"],
            data("help_details_list") % {"action": "List"}
        )


class DisplayTests(FunctionalTests):
    """Tests for the 'display' action."""

    def test_notes_displaying(self):
        """F Display: Action "display" prints the content given note names."""
        list_of_notes = self.full_list_of_notes()

        todo = list_of_notes[1]
        python_work = list_of_notes[4]
        note_lines = data("notes/TODO-list").splitlines()
        note_lines[0] = (
            "%s  (system:notebook:reminders, system:notebook:pim)" % (
                note_lines[0],
            )
        )
        note1_content = "%s\n" % "\n".join(note_lines)
        note2_content = data("notes/python-work")
        sys.argv = ["unused_prog_name", "display", "TODO-list", "python-work"]

        self.mock_out_listing(list_of_notes)

        self.dbus_interface.GetNoteContents(todo.uri)\
            .AndReturn(data("notes/TODO-list")[:-1])
        self.dbus_interface.GetNoteContents(python_work.uri)\
            .AndReturn(data("notes/python-work")[:-1])

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            "\n".join([
                note1_content,
                data("display_separator"),
                note2_content,
            ]),
            sys.stdout.getvalue()
        )

    def test_note_does_not_exist(self):
        """F Display: Specified note non-existant: display an error."""
        list_of_notes = self.full_list_of_notes()
        self.mock_out_listing(list_of_notes)
        sys.argv = ["app_name", "display", "unexistant"]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            data("unexistant_note_error"),
            sys.stderr.getvalue()
        )

    def test_display_zero_argument(self):
        """F Display: Action "display" with no argument prints an error."""
        sys.argv = ["app_name", "display"]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            data("display_no_note_name_error"),
            sys.stderr.getvalue()
        )

    def test_help_display_specific(self):
        """F Display: Detailed help using "-h" after "display" action."""
        self.verify_help_text(
            ["app_name", "display", "--help"],
            data("help_details_display")
        )


class SearchTests(FunctionalTests):
    """Tests for the 'search' action."""

    def test_search(self):
        """F Search: Action "search" searches in all notes, case-indep."""
        list_of_notes = self.full_list_of_notes()
        self.mock_out_listing(list_of_notes)
        sys.argv = ["unused_prog_name", "search", "john doe"]

        # Forget about the last note (a template)
        for note in list_of_notes[:-1]:
            self.dbus_interface.GetNoteContents(note.uri)\
                .AndReturn(data("notes/%s" % note.title))

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            data("search_results"),
            sys.stdout.getvalue()
        )

    def test_search_specific_notes(self):
        """F Search: Action "search" restricts the search to given notes."""
        list_of_notes = self.full_list_of_notes()
        requested_notes = [
            list_of_notes[3],
            list_of_notes[4],
            list_of_notes[6],
        ]
        sys.argv = (["unused_prog_name", "search", "python"] +
                [n.title for n in requested_notes])

        self.mock_out_listing(list_of_notes)

        for note in requested_notes:
            self.dbus_interface.GetNoteContents(note.uri)\
                .AndReturn(data("notes/%s" % note.title))

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            data("specific_search_results"),
            sys.stdout.getvalue()
        )

    def test_search_zero_arguments(self):
        """F Search: Action "search" with no argument prints an error."""
        sys.argv = ["unused_prog_name", "search"]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEquals(
            data("search_no_argument_error"),
            sys.stderr.getvalue()
        )

    def test_help_search_specific(self):
        """F Search: Detailed help using "-h" after "search" action."""
        self.verify_help_text(
            ["app_name", "search", "--help"],
            data("help_details_search") % {"action": "Search"}
        )


class VersionTests(FunctionalTests):
    """Tests for the 'version' action."""

    def test_tomboy_version(self):
        """F Version: Get Tomboy's version."""
        self.dbus_interface.Version()\
            .AndReturn(u'1.0.1')

        sys.argv = ["app_name", "version"]

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEqual(
            data("tomboy_version_output") % (SCOUT_VERSION, "Tomboy"),
            sys.stdout.getvalue()
        )

    def test_help_version_specific(self):
        """F Version: Detailed help using "-h" after "version" action."""
        self.verify_help_text(
            ["app_name", "version", "--help"],
            data("help_details_version")
        )


class DeleteTests(FunctionalTests):
    """Tests for the 'delete' action."""

    def verify_delete_notes(self, tags, names, all_notes, dry_run):
        """Test note deletion."""
        list_of_notes = self.full_list_of_notes()
        sys.argv = ["unused_prog_name", "delete"]

        if all_notes or tags or names:
            self.mock_out_listing(list_of_notes)

        if all_notes:
            expected_notes = list_of_notes
            sys.argv.append("--all-notes")
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
        else:
            sys.argv.append("--dry-run")

        for tag in tags:
            sys.argv.extend([
                "-t",
                tag,
            ])

        for name in names:
            sys.argv.append(name)

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

    def test_delete_notes(self):
        """F Delete: Delete a list of notes."""
        self.verify_delete_notes(
            tags=["system:notebook:pim"],
            names=["TDD"],
            all_notes=False,
            dry_run=False
        )

    def test_delete_notes_dry_run(self):
        """F Delete: Dry run of note deletion."""
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
        """F Delete: Delete without argument prints a message."""
        self.verify_delete_notes(
            tags=[],
            names=[],
            all_notes=False,
            dry_run=False
        )

        self.assertEqual(
            data("delete_no_argument_msg"),
            sys.stderr.getvalue()
        )

    def test_delete_notes_all_notes(self):
        """F Delete: Delete all notes."""
        self.verify_delete_notes(
            tags=[],
            names=[],
            all_notes=True,
            dry_run=False
        )

    def test_help_delete_specific(self):
        """F Delete: Detailed help using "-h" after "version" action."""
        self.verify_help_text(
            ["app_name", "delete", "--help"],
            data("help_details_delete")
        )


class EditTests(FunctionalTests):
    """Tests for the 'edit' action."""

    def test_add_tag(self):
        """F Edit: Add a tag to a single note."""
        list_of_notes = self.full_list_of_notes()

        todo = list_of_notes[1]
        sys.argv = ["unused_prog_name", "edit", "--add-tag", "new_tag", "TODO-list"]

        self.mock_out_listing(list_of_notes)

        self.dbus_interface.AddTagToNote(todo.uri, "new_tag")

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

    def test_help_edit_specific(self):
        """F Edit: Detailed help using "-h" after "edit" action."""
        self.verify_help_text(
            ["app_name", "edit", "--help"],
            data("help_details_edit") % {"action": "Edit"}
        )


class FilteringTests(FunctionalTests):
    """Tests about note filtering."""

    def verify_list_filtering(self, args, output):
        """Test that listing notes with 'args' give 'output'.

        Call Scout's main function and give it arguments as if they were given
        on the command line. Verify output on stdout against a given value.

        """
        list_of_notes = self.full_list_of_notes()
        self.mock_out_listing(list_of_notes)
        sys.argv = args

        self.m.ReplayAll()
        self.assertRaises(SystemExit, cli.main)
        self.m.VerifyAll()

        self.assertEqual(output, sys.stdout.getvalue())

    def test_filter_notes_with_templates(self):
        """F Filter: Using "--with-templates" lists notes and templates."""
        self.verify_list_filtering(
            ["app_name", "list", "--with-templates"],
            ''.join([data("expected_list"),
                     data("list_appendix"),
                     data("normally_hidden_template")])
        )

    def test_filter_notes_by_tags(self):
        """F Filter: Using "-t" limits the notes by tags."""
        self.verify_list_filtering(
            ["app_name", "list", "-t", "system:notebook:pim", "-t", "projects"],
            data("tag_limited_list")
        )

    def test_filter_notes_by_books(self):
        """F Filter: Using "-b" limits the notes by notebooks."""
        self.verify_list_filtering(
            ["app_name", "list", "-b", "pim", "-b", "reminders"],
            data("book_limited_list")
        )

    def test_filter_untagged_notes(self):
        """F Filter: Using "-T" selects untagged notes."""
        self.verify_list_filtering(
            ["app_name", "list", "-T"],
            data("untagged_notes")
        )

    def test_filter_unbooked_notes(self):
        """F Filter: Using "-B" selects notes that are not in a book."""
        self.verify_list_filtering(
            ["app_name", "list", "-B"],
            data("unbooked_notes")
        )
