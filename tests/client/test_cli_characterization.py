"""Characterization tests for CLI menu dispatch.

The test records the action selected for every existing menu option. It deliberately
replaces actions with mocks so presentation changes cannot alter dispatch order.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from contextlib import ExitStack

from client import cli_app


RECORD_PATH = Path(__file__).with_name("cli_characterization_record.json")

MENUS = {
    "patients": (cli_app.patient_menu, [
        "list_patients", "create_patient", "update_patient", "delete_patient",
        "search_patient", "list_patients", "view_patient_samples",
    ]),
    "samples": (cli_app.sample_menu, [
        "list_samples", "create_sample", "update_sample", "delete_sample",
        "search_sample", "view_full_sample", "filter_samples_status",
        "filter_samples_date", "manage_quality_control", "apply_protocol",
    ]),
    "staff": (cli_app.staff_menu, [
        "list_staff", "create_staff", "update_staff", "delete_staff",
        "search_staff", "assign_staff", "view_staff_assignments",
        "view_staff_protocols",
    ]),
    "projects": (cli_app.project_menu, [
        "list_projects", "create_project", "update_project", "delete_project",
        "search_project", "link_sample", "view_project_details",
        "manage_project_relations",
    ]),
    "protocols": (cli_app.protocol_menu, [
        "list_protocols", "create_protocol", "update_protocol", "delete_protocol",
        "search_protocol", "apply_protocol", "view_protocol_details",
        "remove_protocol",
    ]),
    "administration": (cli_app.admin_menu, [
        "list_containers", "create_container", "list_sample_types",
        "create_sample_type", "manage_container", "manage_sample_type",
    ]),
}


class CliCharacterizationTests(unittest.TestCase):
    def test_existing_menu_options_dispatch_in_original_order(self):
        actual = {}
        for menu_name, (menu, expected_names) in MENUS.items():
            calls = []
            patches = []
            for name in set(expected_names):
                action = Mock(side_effect=lambda *args, name=name, **kwargs: calls.append(name))
                patches.append(patch.object(cli_app, name, action))
            with ExitStack() as stack:
                for item in patches:
                    stack.enter_context(item)
                values = []
                for number in range(1, len(expected_names) + 1):
                    values.append(str(number))
                values.append("0")
                with patch("builtins.input", side_effect=values), patch.object(
                        cli_app, "clear_screen"
                    ), patch.object(cli_app, "press_any_key"):
                    menu()
            actual[menu_name] = calls

        expected = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
