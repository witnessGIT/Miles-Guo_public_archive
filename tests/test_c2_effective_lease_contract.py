"""C2 leases follow the fixed policy, not optional static-task metadata."""
from __future__ import annotations

from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import next_task
import validate_candidate_reviews


class C2EffectiveLeaseTests(unittest.TestCase):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def claim(self, index=1, **changes):
        candidate = f"SC_LEASE_TEST_{index:02d}"
        payload = {
            "task_id": f"C2-REVIEW-{candidate}-R001",
            "source_candidate_id": candidate,
            "kind": "candidate_promotion_review",
            "agent_id": "lease-contract-test",
            "claimed_at": self.start.isoformat(),
            "status": "in_progress",
            "review_generation": 1,
            "review_claim_timeout_hours": 10,
            "candidate_review_contract": next_task.CANDIDATE_REVIEW_CONTRACT,
            "entry_mode": "ordinary_chat",
            "review_batch_id": "REVIEW-BATCH-LEASE-TEST",
            "review_batch_target_size": 20,
            "review_batch_claimed_count": 20,
            "review_batch_position": index,
        }
        payload.update(changes)
        return payload

    def assert_boundary(self, payload, hours):
        deadline = self.start + timedelta(hours=hours)
        self.assertFalse(next_task.claim_expired(payload, now=deadline - timedelta(microseconds=1)))
        self.assertTrue(next_task.claim_expired(payload, now=deadline))
        self.assertTrue(next_task.claim_expired(payload, now=deadline + timedelta(microseconds=1)))

    def test_missing_static_field_expires_at_ten_hours(self):
        self.assert_boundary(self.claim(), 10)

    def test_conflicting_or_malformed_fields_cannot_change_c2_lease(self):
        for value in (24, 6, 0, -1, None, True, "bad", "NaN", "Infinity", [], {}):
            with self.subTest(value=value):
                payload = self.claim(static_claim_lease_hours=value, review_claim_timeout_hours=value)
                self.assertEqual(next_task.claim_lease_hours(payload), 10)
                self.assert_boundary(payload, 10)

    def test_task_prefix_identifies_legacy_c2_claim(self):
        payload = self.claim(static_claim_lease_hours=24)
        payload.pop("kind")
        payload.pop("review_claim_timeout_hours")
        self.assert_boundary(payload, 10)

    def test_kind_identifies_c2_claim(self):
        self.assert_boundary(self.claim(task_id="legacy-candidate-alias", static_claim_lease_hours=24), 10)

    def test_terminal_claims_do_not_expire(self):
        for status in ("completed", "released", "abandoned", "cancelled"):
            with self.subTest(status=status):
                self.assertFalse(next_task.claim_expired(self.claim(status=status), now=self.start + timedelta(days=20)))

    def test_timezone_offset_is_normalized(self):
        self.assert_boundary(self.claim(claimed_at="2026-01-01T09:00:00+09:00"), 10)

    def test_missing_or_invalid_timestamp_behavior_is_preserved(self):
        for value in (None, "", "not-a-date"):
            self.assertFalse(next_task.claim_expired(self.claim(claimed_at=value), now=self.start))

    def test_static_default_remains_twenty_four_hours(self):
        self.assert_boundary(self.claim(task_id="C1-TEST", kind="source_boundary_discovery"), 24)

    def test_static_explicit_custom_lease_is_preserved(self):
        for hours in (6, "6.5"):
            self.assert_boundary(self.claim(task_id="STATIC-TEST", kind="static", static_claim_lease_hours=hours), float(hours))

    def test_static_invalid_lease_fallback_is_preserved(self):
        self.assert_boundary(self.claim(task_id="STATIC-TEST", kind="static", static_claim_lease_hours="bad"), 24)

    def fixture(self, stack):
        root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        paths = {"ROOT": root, "CLAIMS": root / "coordination/claims", "COMPLETED": root / "coordination/completed", "DATA_CURRENT": root / "data/current"}
        for name, value in paths.items():
            value.mkdir(parents=True, exist_ok=True)
            stack.enter_context(patch.object(next_task, name, value))
        return root

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def test_queue_display_expiry_and_generation_agree_without_mutating_claims(self):
        for extra in ({}, {"static_claim_lease_hours": 24}, {"static_claim_lease_hours": 6}):
            with self.subTest(extra=extra), ExitStack() as stack:
                root = self.fixture(stack)
                claim = self.claim(**extra)
                self.write(root / "data/current/source_candidates/test.json", {"id": claim["source_candidate_id"], "status": "discovered"})
                path = root / "coordination/claims/test.json"
                self.write(path, claim)
                before = path.read_bytes()
                deadline = self.start + timedelta(hours=10)
                row = next_task.candidate_review_states(now=deadline - timedelta(microseconds=1))[0]
                self.assertEqual(row["state"], "in_progress")
                self.assertEqual(row["claim_expires_at"], deadline.isoformat())
                row = next_task.candidate_review_states(now=deadline)[0]
                self.assertEqual(row["state"], "unreviewed")
                self.assertEqual(row["next_generation"], 2)
                self.assertIsNone(row["active_claim"])
                self.assertEqual(path.read_bytes(), before)

    def test_valid_completion_does_not_revert_after_lease_expiry(self):
        with ExitStack() as stack:
            root = self.fixture(stack)
            claim = self.claim()
            self.write(root / "data/current/source_candidates/test.json", {"id": claim["source_candidate_id"], "status": "discovered"})
            self.write(root / "coordination/claims/test.json", claim)
            self.write(root / "coordination/completed/test.json", {**claim, "status": "completed", "completed_at": (self.start + timedelta(hours=1)).isoformat()})
            stack.enter_context(patch.object(next_task, "candidate_review_completion_is_valid", return_value=True))
            self.assertEqual(next_task.candidate_review_states(now=self.start + timedelta(days=1))[0]["state"], "reviewed")

    def run_validator(self, root, **extra):
        for index in range(1, 21):
            self.write(root / f"coordination/claims/test-{index:02d}.json", self.claim(index, **extra))
        output = io.StringIO()
        with redirect_stdout(output):
            status = validate_candidate_reviews.main()
        return status, json.loads(output.getvalue())

    def test_validator_accepts_legacy_missing_static_fields(self):
        with ExitStack() as stack:
            root = self.fixture(stack)
            status, output = self.run_validator(root)
            self.assertEqual(status, 0)
            self.assertEqual(output["lease_warnings"], [])

    def test_validator_reports_conflicting_fields_with_fixed_effective_lease(self):
        with ExitStack() as stack:
            root = self.fixture(stack)
            status, output = self.run_validator(root, static_claim_lease_hours=24, review_claim_timeout_hours=6)
            self.assertEqual(status, 0)
            self.assertEqual(len(output["lease_warnings"]), 40)
            self.assertTrue(all(row["effective_hours"] == 10 for row in output["lease_warnings"]))

    def test_validator_still_rejects_invalid_batch_mode(self):
        with ExitStack() as stack:
            root = self.fixture(stack)
            status, _ = self.run_validator(root, entry_mode="invalid")
            self.assertEqual(status, 1)

    def test_validator_still_rejects_evidence_free_completion(self):
        with ExitStack() as stack:
            root = self.fixture(stack)
            self.write(root / "coordination/completed/invalid.json", {**self.claim(), "status": "completed", "outputs": []})
            status, _ = self.run_validator(root)
            self.assertEqual(status, 1)


if __name__ == "__main__":
    unittest.main()
