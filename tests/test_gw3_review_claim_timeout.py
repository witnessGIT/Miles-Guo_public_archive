"""Regression checks for the resumed GW3 batch's effective scheduler leases."""
from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import next_task

BATCH_ID = "REVIEW-BATCH-20261004T125231Z-chat-gw3"


class Gw3ReviewClaimTimeoutTests(unittest.TestCase):
    def pending_members(self) -> list[dict]:
        members = []
        for path in sorted(next_task.CLAIMS.glob("*.json")):
            claim = json.loads(path.read_text(encoding="utf-8"))
            if claim.get("review_batch_id") != BATCH_ID:
                continue
            if claim.get("status") != "in_progress":
                continue
            if next_task.task_completed(str(claim["task_id"])):
                continue
            members.append(claim)
        if not members:
            self.skipTest("No unfinished GW3 members remain; completed history is not mutated.")
        return members

    def test_pending_members_have_effective_ten_hour_metadata(self):
        for claim in self.pending_members():
            with self.subTest(task=claim["task_id"]):
                self.assertEqual(claim["review_claim_timeout_hours"], 10)
                self.assertEqual(claim.get("static_claim_lease_hours"), 10)

    def test_pending_members_expire_at_exact_ten_hour_boundary(self):
        for claim in self.pending_members():
            with self.subTest(task=claim["task_id"]):
                start = next_task.parse_timestamp(claim["claimed_at"])
                self.assertIsNotNone(start)
                deadline = start + timedelta(hours=10)
                self.assertFalse(next_task.claim_expired(claim, now=deadline-timedelta(microseconds=1)))
                self.assertTrue(next_task.claim_expired(claim, now=deadline))
                self.assertTrue(next_task.claim_expired(claim, now=deadline+timedelta(microseconds=1)))
                self.assertTrue(next_task.claim_expired(claim, now=start+timedelta(hours=12)))


if __name__ == "__main__":
    unittest.main()
