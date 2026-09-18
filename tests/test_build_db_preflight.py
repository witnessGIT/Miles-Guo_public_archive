from pathlib import Path
import unittest

from scripts.build_db import record_preflight_errors


class BuildDbPreflightTests(unittest.TestCase):
    def test_reports_duplicate_ids_before_sqlite_insert(self):
        records = [
            (Path("a.jsonl"), 1, {"id": "SC_DUP", "source_site": "A"}),
            (Path("b.jsonl"), 2, {"id": "SC_DUP", "source_site": "A"}),
        ]

        errors = record_preflight_errors(
            "source_candidates",
            {"id", "source_site"},
            records,
        )

        self.assertTrue(any("duplicate id SC_DUP" in error for error in errors))

    def test_reports_unknown_columns_with_source_location(self):
        records = [
            (Path("bad.json"), 1, {"id": "SC_1", "extra": True}),
        ]

        errors = record_preflight_errors(
            "source_candidates",
            {"id", "source_site"},
            records,
        )

        self.assertEqual(
            errors,
            ["bad.json record 1: unknown columns for source_candidates: ['extra']"],
        )


if __name__ == "__main__":
    unittest.main()
