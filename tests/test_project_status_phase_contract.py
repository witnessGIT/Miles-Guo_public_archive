"""Isolate the phase prerequisite without changing production workflow state."""
from contextlib import ExitStack
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import project_status as ps


class ProjectStatusPhaseContractTests(unittest.TestCase):
    def fixture(self, stack, phase):
        stack.enter_context(patch.object(ps, "load_workflow", return_value={"current_major_phase": phase}))
        stack.enter_context(patch.object(ps.next_task, "eligible_tasks", return_value=[]))
        cases = stack.enter_context(patch.object(ps.playback_queue, "case_statuses", return_value=[{
            "task_id": "P9-PLAYBACK-PILOT-X001", "case_id": "PILOT-X001",
            "live_id": "LIVE_20000101_001", "missing_segment_ids": ["SEG-X"],
            "claim_exists": False, "completed": False,
        }]))
        gate = stack.enter_context(patch.object(ps.playback_queue, "gate_summary", return_value={
            "pilot60_pass": False, "qualifying_checks": 0, "required_checks": 60, "invalid_records": [],
        }))
        stack.enter_context(patch.object(ps.playback_queue, "capability_status", return_value={
            "ffmpeg": False, "ffprobe": False, "yt_dlp": False, "repository_evidence_service": True,
        }))
        stack.enter_context(patch.object(ps, "load_admin_bug_queue", return_value=([], [])))
        stack.enter_context(patch.object(ps, "exists_completed", return_value=False))
        stack.enter_context(patch.object(ps, "exists_claim", return_value=False))
        stack.enter_context(patch.object(ps, "load_completed", return_value=None))
        return cases, gate

    def test_post_collection_service_is_available_without_local_media_tools(self):
        with ExitStack() as stack:
            cases, gate = self.fixture(stack, "PHASE_2_PROCESSING")
            result = ps.build_status(False, "worker")
            self.assertEqual(result["classification"], "WORK_AVAILABLE")
            self.assertEqual(result["recommended_action"], "CLAIM_REAL_PLAYBACK_TASK_AND_REQUEST_REPOSITORY_EVIDENCE")
            self.assertTrue(result["playback_queue"]["claimable_by_this_runtime"])
            self.assertFalse(result["host_stop_for_this_runtime"])
            cases.assert_called_once_with()
            gate.assert_called_once_with()

    def test_phase_one_does_not_read_playback_targets_or_accept_a_passing_gate(self):
        with ExitStack() as stack:
            cases, gate = self.fixture(stack, "PHASE_1_COLLECTION")
            gate.return_value = {"pilot60_pass": True, "qualifying_checks": 60}
            result = ps.build_status(False, "worker")
            self.assertEqual(result["state"], "PHASE_1_COLLECTION_ACTIVE")
            self.assertEqual(result["classification"], "NO_ELIGIBLE_WORK")
            self.assertEqual(result["recommended_action"], "NO_CURRENT_ACTION")
            self.assertFalse(result["playback_queue"]["claimable_by_this_runtime"])
            self.assertFalse(result["gates"]["P9_PLAYBACK_GATE_ready_to_seal"])
            self.assertFalse(result["gates"]["full_archive_authorized"])
            cases.assert_not_called()
            gate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
