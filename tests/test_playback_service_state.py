import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import playback_service_state as state  # noqa: E402


class PlaybackServiceStateTest(unittest.TestCase):
    def setUp(self):
        self.originals = (
            state.ROOT,
            state.REQUEST_ROOT,
            state.ACCEPTANCE_ROOT,
            state.CLAIM_ROOT,
            state.EVIDENCE_ROOT,
            state.AUDIT_ROOT,
        )
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        state.ROOT = root
        state.REQUEST_ROOT = root / "coordination" / "playback_requests"
        state.ACCEPTANCE_ROOT = root / "coordination" / "playback_acceptances"
        state.CLAIM_ROOT = root / "coordination" / "claims"
        state.EVIDENCE_ROOT = root / "data" / "playback_evidence"
        state.AUDIT_ROOT = root / "data" / "playback_audits"

    def tearDown(self):
        (
            state.ROOT,
            state.REQUEST_ROOT,
            state.ACCEPTANCE_ROOT,
            state.CLAIM_ROOT,
            state.EVIDENCE_ROOT,
            state.AUDIT_ROOT,
        ) = self.originals
        self.tmp.cleanup()

    def write_json(self, path: Path, payload: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_visual_retry_with_existing_retryable_evidence_requires_runtime(self):
        request = {
            "case_id": "PILOT-X",
            "segment_id": "SEG-1",
            "request_revision": 2,
            "visual_mode": "smolvlm2_optional",
        }
        evidence = {
            "case_id": "PILOT-X",
            "segment_id": "SEG-1",
            "request_revision": 1,
            "status": "needs_manual_or_wider_review",
        }
        self.write_json(state.REQUEST_ROOT / "PILOT-X" / "SEG-1.json", request)
        self.write_json(state.EVIDENCE_ROOT / "PILOT-X" / "SEG-1" / "evidence.json", evidence)

        needed, problems = state.pending_requires_visual_runtime()

        self.assertTrue(needed)
        self.assertEqual(problems, [])

    def test_completed_revision_does_not_require_visual_runtime(self):
        request = {
            "case_id": "PILOT-X",
            "segment_id": "SEG-1",
            "request_revision": 1,
            "visual_mode": "smolvlm2_optional",
        }
        evidence = {
            "case_id": "PILOT-X",
            "segment_id": "SEG-1",
            "request_revision": 1,
            "status": "ready_for_agent_review",
        }
        self.write_json(state.REQUEST_ROOT / "PILOT-X" / "SEG-1.json", request)
        self.write_json(state.EVIDENCE_ROOT / "PILOT-X" / "SEG-1" / "evidence.json", evidence)

        needed, problems = state.pending_requires_visual_runtime()

        self.assertFalse(needed)
        self.assertEqual(problems, [])

    def test_retired_request_is_not_reenqueued(self):
        request = {
            "request_version": "playback-request-v1",
            "task_id": "P9-PLAYBACK-PILOT-X",
            "case_id": "PILOT-X",
            "live_id": "LIVE-X",
            "segment_id": "SEG-OLD",
            "requested_by": "agent-a",
        }
        claim = {
            "task_id": "P9-PLAYBACK-PILOT-X",
            "case_id": "PILOT-X",
            "live_id": "LIVE-X",
            "agent_id": "agent-a",
            "queue_generation": state.ACTIVE_QUEUE_GENERATION,
            "missing_segment_ids": ["SEG-NEW"],
        }
        self.write_json(state.REQUEST_ROOT / "PILOT-X" / "SEG-OLD.json", request)
        self.write_json(state.CLAIM_ROOT / "P9-PLAYBACK-PILOT-X.json", claim)

        pending, problems = state.pending_requests(prepare_retries=False)

        self.assertEqual(pending, [])
        self.assertEqual(problems, [])

    def test_legacy_claim_is_inactive_after_generation_reset(self):
        request = {
            "request_version": "playback-request-v1",
            "task_id": "P9-PLAYBACK-PILOT-X",
            "case_id": "PILOT-X",
            "live_id": "LIVE-X",
            "segment_id": "SEG-1",
            "requested_by": "agent-a",
        }
        claim = {
            "task_id": "P9-PLAYBACK-PILOT-X",
            "case_id": "PILOT-X",
            "live_id": "LIVE-X",
            "agent_id": "agent-a",
            "missing_segment_ids": ["SEG-1"],
        }
        self.write_json(state.REQUEST_ROOT / "PILOT-X" / "SEG-1.json", request)
        self.write_json(state.CLAIM_ROOT / "P9-PLAYBACK-PILOT-X.json", claim)

        pending, problems = state.pending_requests(prepare_retries=False)

        self.assertEqual(pending, [])
        self.assertEqual(problems, [])

    def test_active_request_without_evidence_is_pending(self):
        request = {
            "request_version": "playback-request-v1",
            "task_id": "P9-PLAYBACK-PILOT-X",
            "case_id": "PILOT-X",
            "live_id": "LIVE-X",
            "segment_id": "SEG-1",
            "requested_by": "agent-a",
        }
        claim = {
            "task_id": "P9-PLAYBACK-PILOT-X",
            "case_id": "PILOT-X",
            "live_id": "LIVE-X",
            "agent_id": "agent-a",
            "queue_generation": state.ACTIVE_QUEUE_GENERATION,
            "missing_segment_ids": ["SEG-1"],
        }
        request_path = state.REQUEST_ROOT / "PILOT-X" / "SEG-1.json"
        self.write_json(request_path, request)
        self.write_json(state.CLAIM_ROOT / "P9-PLAYBACK-PILOT-X.json", claim)

        pending, problems = state.pending_requests(prepare_retries=False)

        self.assertEqual(pending, [request_path])
        self.assertEqual(problems, [])

    def test_acceptance_from_replaced_claim_owner_is_retired(self):
        acceptance = {
            "case_id": "PILOT-X", "live_id": "LIVE-X", "segment_id": "SEG-1",
            "accepted_by": "agent-old",
        }
        claim = {
            "task_id": "P9-PLAYBACK-PILOT-X", "case_id": "PILOT-X",
            "live_id": "LIVE-X", "agent_id": "agent-new",
            "missing_segment_ids": ["SEG-1"],
        }
        self.write_json(state.ACCEPTANCE_ROOT / "PILOT-X" / "SEG-1.json", acceptance)
        self.write_json(state.CLAIM_ROOT / "P9-PLAYBACK-PILOT-X.json", claim)
        pending, problems = state.pending_acceptances()
        self.assertEqual(pending, [])
        self.assertEqual(problems, [])

    def test_acceptance_from_active_claim_owner_is_pending(self):
        acceptance = {
            "case_id": "PILOT-X", "live_id": "LIVE-X", "segment_id": "SEG-1",
            "accepted_by": "agent-a",
        }
        claim = {
            "task_id": "P9-PLAYBACK-PILOT-X", "case_id": "PILOT-X",
            "live_id": "LIVE-X", "agent_id": "agent-a",
            "missing_segment_ids": ["SEG-1"],
        }
        path = state.ACCEPTANCE_ROOT / "PILOT-X" / "SEG-1.json"
        self.write_json(path, acceptance)
        self.write_json(state.CLAIM_ROOT / "P9-PLAYBACK-PILOT-X.json", claim)
        pending, problems = state.pending_acceptances()
        self.assertEqual(pending, [path])
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
