import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import agent_entry


class AgentEntryTests(unittest.TestCase):
    def test_new_agent_id_is_unique_and_uses_worker_format(self):
        first = agent_entry.new_agent_id()
        second = agent_entry.new_agent_id()
        self.assertTrue(first.startswith("agent-"))
        self.assertNotEqual(first, second)

    def test_session_reuses_the_same_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = agent_entry.SESSION
            try:
                agent_entry.SESSION = Path(tmp) / ".agent_session.json"
                first = agent_entry.load_or_create_agent_id(None)
                second = agent_entry.load_or_create_agent_id(None)
                saved = json.loads(agent_entry.SESSION.read_text(encoding="utf-8"))
            finally:
                agent_entry.SESSION = previous
        self.assertEqual(first, second)
        self.assertEqual(saved["agent_id"], first)

    def test_playback_entry_candidates_include_expired_claims_but_not_active_claims(self):
        rows = [
            {
                "task_id": "P9-PLAYBACK-PILOT-A",
                "case_id": "PILOT-A",
                "missing_segment_ids": ["SEG-A"],
                "claim_exists": True,
                "claim_expired": False,
                "completed": False,
            },
            {
                "task_id": "P9-PLAYBACK-PILOT-B",
                "case_id": "PILOT-B",
                "missing_segment_ids": ["SEG-B"],
                "claim_exists": True,
                "claim_expired": True,
                "completed": False,
            },
            {
                "task_id": "P9-PLAYBACK-PILOT-C",
                "case_id": "PILOT-C",
                "missing_segment_ids": ["SEG-C"],
                "claim_exists": False,
                "claim_expired": False,
                "completed": False,
            },
        ]
        with patch.object(agent_entry.playback_queue, "case_statuses", return_value=rows), patch.object(
            agent_entry.playback_retry_guard,
            "filter_candidates",
            side_effect=lambda candidates: (candidates, []),
        ):
            eligible, guarded = agent_entry.playback_entry_candidates("agent-test")
        self.assertEqual(guarded, [])
        self.assertEqual({row["case_id"] for row in eligible}, {"PILOT-B", "PILOT-C"})

    def test_direct_entry_reclaims_expired_playback_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claim_path = root / "coordination" / "claims" / "P9-PLAYBACK-PILOT-X.json"
            claim_path.parent.mkdir(parents=True, exist_ok=True)
            claim_path.write_text(
                json.dumps(
                    {
                        "task_id": "P9-PLAYBACK-PILOT-X",
                        "case_id": "PILOT-X",
                        "agent_id": "agent-new",
                    }
                ),
                encoding="utf-8",
            )
            expired = {
                "task_id": "P9-PLAYBACK-PILOT-X",
                "case_id": "PILOT-X",
                "missing_segment_ids": ["SEG-X"],
                "claim_exists": True,
                "claim_expired": True,
                "completed": False,
            }
            previous_root = agent_entry.ROOT
            try:
                agent_entry.ROOT = root
                with patch.object(agent_entry.next_task, "eligible_tasks", return_value=[]), patch.object(
                    agent_entry.next_task,
                    "load_workflow",
                    return_value={"current_major_phase": "PHASE_2_VERIFICATION"},
                ), patch.object(
                    agent_entry, "playback_entry_candidates", return_value=([expired], [])
                ), patch.object(
                    agent_entry.playback_queue,
                    "reclaim_expired_claim",
                    return_value=claim_path,
                ) as reclaim:
                    result = agent_entry.direct_entry("agent-new", 10)
            finally:
                agent_entry.ROOT = previous_root
        self.assertEqual(result, 0)
        reclaim.assert_called_once_with(
            "agent-new", "PILOT-X", content_inspection_capable=False
        )

    def test_direct_entry_does_not_fall_back_to_playback_during_phase1(self):
        with patch.object(agent_entry.next_task, "eligible_tasks", return_value=[]), patch.object(
            agent_entry.next_task,
            "load_workflow",
            return_value={"current_major_phase": "PHASE_1_COLLECTION"},
        ), patch.object(agent_entry, "playback_entry_candidates") as playback_candidates:
            result = agent_entry.direct_entry("agent-new", 10)

        self.assertEqual(result, 1)
        playback_candidates.assert_not_called()


if __name__ == "__main__":
    unittest.main()
