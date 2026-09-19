import json
import sys
import tempfile
import unittest
import subprocess
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

    def test_pr_selection_skips_tasks_reserved_by_open_pull_requests(self):
        tasks = [
            {"id": "C1-A", "priority": 100},
            {"id": "C1-B", "priority": 100},
        ]
        with patch.object(agent_entry.next_task, "eligible_tasks", return_value=tasks), patch.object(
            agent_entry.next_task,
            "candidate_order",
            side_effect=lambda eligible, agent_id, requested: eligible,
        ):
            selected = agent_entry.select_pr_task("agent-test", {"C1-A"})
        self.assertEqual(selected, "C1-B")

    def test_automatic_entry_publishes_direct_claim_when_push_is_available(self):
        with patch.object(agent_entry, "refresh_main") as refresh, patch.object(
            agent_entry, "direct_push_available", return_value=True
        ), patch.object(agent_entry, "publish_direct_claim", return_value=0) as publish:
            result = agent_entry.automatic_entry("agent-test", 7, "origin")
        self.assertEqual(result, 0)
        refresh.assert_called_once_with("origin")
        publish.assert_called_once_with("agent-test", 7, "origin")

    def test_refresh_rejects_unpublished_local_main_commit(self):
        def fake_git(*args, check=True):
            outputs = {
                ("status", "--porcelain=v1"): "",
                ("branch", "--show-current"): "main\n",
                ("pull", "--ff-only", "origin", "main"): "Already up to date.\n",
                ("rev-parse", "HEAD"): "local123\n",
                ("rev-parse", "origin/main"): "remote456\n",
            }
            return subprocess.CompletedProcess(args, 0, outputs[args], "")

        with patch.object(agent_entry, "run_git", side_effect=fake_git):
            with self.assertRaisesRegex(RuntimeError, "not identical"):
                agent_entry.refresh_main("origin")

    def test_automatic_entry_falls_back_to_pr_when_direct_push_is_unavailable(self):
        with patch.object(agent_entry, "refresh_main"), patch.object(
            agent_entry, "direct_push_available", return_value=False
        ), patch.object(agent_entry, "publish_pr_reservation", return_value=0) as publish:
            result = agent_entry.automatic_entry("agent-test", 10, "origin")
        self.assertEqual(result, 0)
        publish.assert_called_once_with("agent-test", "origin")

    def test_automatic_entry_retries_after_pr_reservation_race(self):
        with patch.object(agent_entry, "refresh_main"), patch.object(
            agent_entry, "direct_push_available", return_value=False
        ), patch.object(
            agent_entry, "publish_pr_reservation", side_effect=[3, 0]
        ) as publish:
            result = agent_entry.automatic_entry("agent-test", 10, "origin")
        self.assertEqual(result, 0)
        self.assertEqual(publish.call_count, 2)

    def test_pr_publish_blocks_safely_without_authenticated_github_cli(self):
        with patch.object(agent_entry, "gh_available", return_value=False):
            result = agent_entry.publish_pr_reservation("agent-test", "origin")
        self.assertEqual(result, 2)

    def test_manual_pr_entry_fails_closed_when_open_prs_cannot_be_read(self):
        with patch.object(
            agent_entry, "open_pr_reservations", side_effect=RuntimeError("no GitHub access")
        ), patch.object(agent_entry, "select_pr_task") as select:
            result = agent_entry.pr_entry("agent-test")
        self.assertEqual(result, 2)
        select.assert_not_called()

    def test_direct_publish_stages_only_claim_paths_and_pushes_main(self):
        calls = []
        statuses = iter(["", "?? coordination/claims/C1-A.json\n"])

        def fake_git(*args, check=True):
            calls.append(args)
            if args[:2] == ("status", "--porcelain=v1"):
                return subprocess.CompletedProcess(args, 0, next(statuses), "")
            if args[:2] == ("push", "origin"):
                return subprocess.CompletedProcess(args, 0, "", "")
            if args[:2] == ("rev-parse", "HEAD"):
                return subprocess.CompletedProcess(args, 0, "abc123\n", "")
            return subprocess.CompletedProcess(args, 0, "", "")

        with patch.object(agent_entry, "run_git", side_effect=fake_git), patch.object(
            agent_entry, "direct_entry", return_value=0
        ):
            result = agent_entry.publish_direct_claim("agent-test", 10, "origin")

        self.assertEqual(result, 0)
        self.assertIn(("add", "--", "coordination/claims/C1-A.json"), calls)
        self.assertIn(("push", "origin", "HEAD:main"), calls)

    def test_github_repository_slug_supports_https_and_ssh_remotes(self):
        for remote_url in (
            "https://github.com/witnessGIT/Miles-Guo_public_archive.git",
            "git@github.com:witnessGIT/Miles-Guo_public_archive.git",
        ):
            with self.subTest(remote_url=remote_url), patch.object(
                agent_entry,
                "run_git",
                return_value=subprocess.CompletedProcess([], 0, remote_url + "\n", ""),
            ):
                self.assertEqual(
                    agent_entry.github_repository_slug("origin"),
                    "witnessGIT/Miles-Guo_public_archive",
                )


if __name__ == "__main__":
    unittest.main()
