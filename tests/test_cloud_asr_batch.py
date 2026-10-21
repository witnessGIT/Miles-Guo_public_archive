import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.cloud_asr_batch import (
    DEFERRED_STATUS,
    attempt_is_cooling_down,
    attempt_is_deferred,
    claim_is_unavailable,
    eligible,
    record_failed_resume,
)


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

    def test_active_claim_blocks_reclaim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claim.json"
            path.write_text(json.dumps({
                "status": "in_progress",
                "claimed_at": datetime.now(timezone.utc).isoformat(),
                "static_claim_lease_hours": 24,
            }), encoding="utf-8")
            self.assertTrue(claim_is_unavailable(path))

    def test_released_claim_cools_down_then_can_be_reclaimed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claim.json"
            path.write_text(json.dumps({
                "status": "released",
                "released_at": datetime.now(timezone.utc).isoformat(),
            }), encoding="utf-8")
            self.assertTrue(claim_is_unavailable(path, 24))
            self.assertFalse(claim_is_unavailable(path, 0))

    def test_two_failed_checkpoint_resumes_defer_video_to_corpus_tail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_attempt(repo, "2026-10-21T00:00:00Z")
            count, deferred = record_failed_resume(repo, "LIVE_20260101_001", 0, True)
            self.assertEqual(count, 1)
            self.assertFalse(deferred)
            self.assertFalse(attempt_is_deferred(repo, "LIVE_20260101_001"))

            count, deferred = record_failed_resume(repo, "LIVE_20260101_001", count, True)
            self.assertEqual(count, 2)
            self.assertTrue(deferred)
            self.assertTrue(attempt_is_deferred(repo, "LIVE_20260101_001"))
            payload = json.loads(
                (repo / "data/current/asr_attempts/cloud_live_20260101_001.json")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(payload["status"], DEFERRED_STATUS)
            self.assertEqual(payload["retry_queue"], "corpus_tail")

    def test_source_failure_does_not_consume_checkpoint_resume_allowance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_attempt(repo, "2026-10-21T00:00:00Z")
            count, deferred = record_failed_resume(repo, "LIVE_20260101_001", 1, False)
            self.assertEqual(count, 1)
            self.assertFalse(deferred)

    def test_normal_queue_excludes_deferred_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_attempt(repo, "2026-10-21T00:00:00Z")
            record_failed_resume(repo, "LIVE_20260101_001", 1, True)
            listing = subprocess.CompletedProcess(
                [], 0, "WI_LIVE_20260101_001_transcript_import [priority=71]\n", "",
            )
            with patch("scripts.cloud_asr_batch.run", return_value=listing):
                self.assertEqual(eligible(repo, 10, 0), [])
                with self.assertRaisesRegex(RuntimeError, "deferred until corpus tail"):
                    eligible(repo, 10, 0, ["LIVE_20260101_001"])

    def test_corpus_tail_mode_can_select_deferred_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_attempt(repo, "2026-10-21T00:00:00Z")
            record_failed_resume(repo, "LIVE_20260101_001", 1, True)
            listing = subprocess.CompletedProcess(
                [], 0, "WI_LIVE_20260101_001_transcript_import [priority=71]\n", "",
            )
            with patch("scripts.cloud_asr_batch.run", return_value=listing):
                self.assertEqual(
                    eligible(
                        repo, 10, 0, ["LIVE_20260101_001"], include_deferred=True,
                    ),
                    [("WI_LIVE_20260101_001_transcript_import", "LIVE_20260101_001")],
                )


if __name__ == "__main__":
    unittest.main()
