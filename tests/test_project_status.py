import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import project_status  # noqa: E402


class ProjectStatusDecisionTest(unittest.TestCase):
    def test_missing_decision_does_not_authorize(self):
        self.assertIsNone(project_status.normalize_full_archive_decision(None))
        self.assertIsNone(project_status.normalize_full_archive_decision({}))
        self.assertIsNone(
            project_status.normalize_full_archive_decision({"status": "completed"})
        )

    def test_only_explicit_yes_or_no_are_accepted(self):
        self.assertEqual(
            project_status.normalize_full_archive_decision(
                {"full_archive_decision": "YES"}
            ),
            "YES",
        )
        self.assertEqual(
            project_status.normalize_full_archive_decision(
                {"full_archive_decision": " no "}
            ),
            "NO",
        )
        self.assertIsNone(
            project_status.normalize_full_archive_decision(
                {"full_archive_decision": "PASS"}
            )
        )

    def test_boolean_values_are_normalized_but_not_inferred_from_completion(self):
        self.assertEqual(
            project_status.normalize_full_archive_decision(
                {"full_archive_decision": True}
            ),
            "YES",
        )
        self.assertEqual(
            project_status.normalize_full_archive_decision(
                {"full_archive_decision": False}
            ),
            "NO",
        )


if __name__ == "__main__":
    unittest.main()
