import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import playback_retry_guard as guard  # noqa: E402


class PlaybackRetryGuardTests(unittest.TestCase):
    def setUp(self):
        self.previous_root = guard.ROOT
        self.previous_guard_root = guard.GUARD_ROOT
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        guard.ROOT = root
        guard.GUARD_ROOT = root / "coordination" / "playback_retry_guards"
        guard.GUARD_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        guard.ROOT = self.previous_root
        guard.GUARD_ROOT = self.previous_guard_root
        self.tmp.cleanup()

    def test_guard_blocks_only_while_recorded_environment_is_unchanged(self):
        tracked = guard.ROOT / "scripts" / "audit_media.py"
        tracked.parent.mkdir(parents=True, exist_ok=True)
        tracked.write_text("version-one\n", encoding="utf-8")
        payload = {
            "case_id": "PILOT-X",
            "retry_policy": guard.POLICY,
            "environment_files": {
                "scripts/audit_media.py": guard.git_blob_sha(tracked),
            },
        }
        (guard.GUARD_ROOT / "PILOT-X.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        self.assertTrue(guard.guard_is_active("PILOT-X"))

        tracked.write_text("version-two\n", encoding="utf-8")
        self.assertFalse(guard.guard_is_active("PILOT-X"))

    def test_filter_candidates_preserves_order_and_skips_guarded_case(self):
        tracked = guard.ROOT / "data" / "sources" / "x.json"
        tracked.parent.mkdir(parents=True, exist_ok=True)
        tracked.write_text("{}\n", encoding="utf-8")
        (guard.GUARD_ROOT / "PILOT-A.json").write_text(
            json.dumps(
                {
                    "case_id": "PILOT-A",
                    "retry_policy": guard.POLICY,
                    "environment_files": {
                        "data/sources/x.json": guard.git_blob_sha(tracked),
                    },
                }
            ),
            encoding="utf-8",
        )
        rows = [
            {"case_id": "PILOT-A", "task_id": "P9-PLAYBACK-PILOT-A"},
            {"case_id": "PILOT-B", "task_id": "P9-PLAYBACK-PILOT-B"},
        ]
        eligible, guarded = guard.filter_candidates(rows)
        self.assertEqual([row["case_id"] for row in eligible], ["PILOT-B"])
        self.assertEqual([row["case_id"] for row in guarded], ["PILOT-A"])


if __name__ == "__main__":
    unittest.main()
