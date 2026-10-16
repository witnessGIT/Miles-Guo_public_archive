import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.cloud_asr_batch import attempt_is_cooling_down


class CloudAsrBatchTests(unittest.TestCase):
    def write_attempt(self, repo: Path, generated_at: str) -> None:
        path = repo / "data/current/asr_attempts/cloud_live_20260101_001.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps({"generated_at": generated_at}) + "\n", encoding="utf-8"
        )

    def test_recent_attempt_is_cooled_down(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self.write_attempt(repo, generated_at)
            self.assertTrue(attempt_is_cooling_down(repo, "LIVE_20260101_001", 24))

    def test_old_or_disabled_attempt_is_not_cooled_down(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_attempt(repo, "2000-01-01T00:00:00Z")
            self.assertFalse(attempt_is_cooling_down(repo, "LIVE_20260101_001", 24))
            self.assertFalse(attempt_is_cooling_down(repo, "LIVE_20260101_001", 0))


if __name__ == "__main__":
    unittest.main()
