import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import next_task


class NextTaskSchedulingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.previous = {
            "ROOT": next_task.ROOT,
            "QUEUE": next_task.QUEUE,
            "CLAIMS": next_task.CLAIMS,
            "COMPLETED": next_task.COMPLETED,
            "CLAIM_ATTEMPTS": next_task.CLAIM_ATTEMPTS,
            "DATA_CURRENT": next_task.DATA_CURRENT,
            "WORKFLOW": next_task.WORKFLOW,
        }
        next_task.ROOT = self.root
        next_task.QUEUE = self.root / "coordination" / "WORK_QUEUE.jsonl"
        next_task.CLAIMS = self.root / "coordination" / "claims"
        next_task.COMPLETED = self.root / "coordination" / "completed"
        next_task.CLAIM_ATTEMPTS = self.root / "coordination" / "claim_attempts"
        next_task.DATA_CURRENT = self.root / "data" / "current"
        next_task.WORKFLOW = self.root / "coordination" / "WORKFLOW.json"
        next_task.CLAIMS.mkdir(parents=True, exist_ok=True)
        next_task.COMPLETED.mkdir(parents=True, exist_ok=True)
        next_task.DATA_CURRENT.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for name, value in self.previous.items():
            setattr(next_task, name, value)
        self.tmp.cleanup()

    def write_queue(self, *tasks):
        next_task.QUEUE.parent.mkdir(parents=True, exist_ok=True)
        next_task.QUEUE.write_text(
            "\n".join(json.dumps(task) for task in tasks) + "\n",
            encoding="utf-8",
        )

    def write_candidate(self, candidate_id="SC_GWINS_TEST"):
        candidate_dir = next_task.DATA_CURRENT / "source_candidates"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        (candidate_dir / f"{candidate_id}.json").write_text(
            json.dumps(
                {
                    "id": candidate_id,
                    "source_site": "GWINS",
                    "source_url": "https://example.invalid/source",
                    "status": "discovered",
                }
            ),
            encoding="utf-8",
        )
        return candidate_id

    def write_review_artifact(self, task_id, candidate_id, agent_id, entry_mode="work"):
        relative = f"data/current/candidate_reviews/{candidate_id}.json"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "contract_version": next_task.CANDIDATE_REVIEW_CONTRACT,
                    "task_id": task_id,
                    "source_candidate_id": candidate_id,
                    "reviewed_by": agent_id,
                    "entry_mode": entry_mode,
                    "reviewed_at": datetime.now(timezone.utc).isoformat(),
                    "decision": "linked_existing_canonical",
                    "canonical_live_id": "LIVE_20261004_001",
                    "evidence_urls": ["https://example.invalid/source"],
                    "checked_fields": sorted(next_task.CANDIDATE_REVIEW_REQUIRED_FIELDS),
                }
            ),
            encoding="utf-8",
        )
        return relative

    def mark_as_complete_work_batch_member(self, task_id, position=1):
        path = next_task.CLAIMS / f"{task_id}.json"
        claim = json.loads(path.read_text(encoding="utf-8"))
        claim.update(
            {
                "review_batch_id": "REVIEW-BATCH-TEST",
                "review_batch_target_size": 100,
                "review_batch_claimed_count": 100,
                "review_batch_position": position,
            }
        )
        path.write_text(json.dumps(claim), encoding="utf-8")

    def test_completed_ids_read_task_id_from_noncanonical_filename(self):
        self.write_queue(
            {
                "id": "C1-GHOT-SOURCE-CANDIDATES",
                "priority": 100,
                "depends_on": [],
                "kind": "source_discovery",
            }
        )
        (next_task.COMPLETED / "C1-GHOT-SOURCE-CANDIDATES-agent-test.json").write_text(
            json.dumps({"task_id": "C1-GHOT-SOURCE-CANDIDATES", "status": "completed"}),
            encoding="utf-8",
        )

        self.assertIn("C1-GHOT-SOURCE-CANDIDATES", next_task.completed_ids())
        self.assertEqual(next_task.eligible_tasks(), [])

    def test_completed_claim_does_not_block_task_completion_detection(self):
        self.write_queue(
            {
                "id": "C1-GHOT-SOURCE-CANDIDATES",
                "priority": 100,
                "depends_on": [],
                "kind": "source_discovery",
            }
        )
        (next_task.CLAIMS / "C1-GHOT-SOURCE-CANDIDATES.json").write_text(
            json.dumps(
                {
                    "task_id": "C1-GHOT-SOURCE-CANDIDATES",
                    "status": "completed",
                    "agent_id": "agent-old",
                }
            ),
            encoding="utf-8",
        )

        self.assertTrue(next_task.task_completed("C1-GHOT-SOURCE-CANDIDATES"))
        self.assertFalse(next_task.claim_blocks_task("C1-GHOT-SOURCE-CANDIDATES"))
        self.assertEqual(next_task.eligible_tasks(), [])

    def test_released_claim_does_not_block_reclaiming_task(self):
        task = {
            "id": "C1-GETTRSEARCH-post-demo",
            "priority": 100,
            "depends_on": [],
            "kind": "source_boundary_discovery",
            "scope": "demo",
        }
        (next_task.CLAIMS / "C1-GETTRSEARCH-post-demo.json").write_text(
            json.dumps(
                {
                    "task_id": "C1-GETTRSEARCH-post-demo",
                    "status": "released",
                    "agent_id": "agent-old",
                    "claimed_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            encoding="utf-8",
        )

        self.assertFalse(next_task.claim_blocks_task("C1-GETTRSEARCH-post-demo"))
        path = next_task.claim_task(task, "agent-new")
        claim = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(claim["agent_id"], "agent-new")

    def test_release_task_marks_claim_non_blocking(self):
        task_id = "C1-GETTRSEARCH-post-demo"
        claim_path = next_task.CLAIMS / f"{task_id}.json"
        claim_path.write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "status": "in_progress",
                    "agent_id": "agent-owner",
                    "claimed_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            encoding="utf-8",
        )

        next_task.release_task(task_id, "agent-owner", "wrong task type")
        released = json.loads(claim_path.read_text(encoding="utf-8"))

        self.assertEqual(released["status"], "released")
        self.assertEqual(released["release_reason"], "wrong task type")
        self.assertFalse(next_task.claim_blocks_task(task_id))

    def test_expired_static_claim_is_archived_and_reclaimed(self):
        task = {
            "id": "C2-CANDIDATE-PROMOTION",
            "priority": 90,
            "depends_on": [],
            "kind": "candidate_promotion",
            "scope": "promote candidates",
        }
        old_claimed_at = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        old_claim = {
            "task_id": "C2-CANDIDATE-PROMOTION",
            "status": "in_progress",
            "agent_id": "agent-old",
            "claimed_at": old_claimed_at,
        }
        claim_path = next_task.CLAIMS / "C2-CANDIDATE-PROMOTION.json"
        claim_path.write_text(json.dumps(old_claim), encoding="utf-8")

        self.assertFalse(next_task.claim_blocks_task("C2-CANDIDATE-PROMOTION"))
        new_path = next_task.claim_task(task, "agent-new")
        new_claim = json.loads(new_path.read_text(encoding="utf-8"))
        archived = list((next_task.CLAIM_ATTEMPTS / "C2-CANDIDATE-PROMOTION").glob("*.json"))

        self.assertEqual(new_claim["agent_id"], "agent-new")
        self.assertTrue(new_claim["reclaimed_expired_claim"])
        self.assertEqual(len(archived), 1)
        self.assertEqual(json.loads(archived[0].read_text(encoding="utf-8")), old_claim)

    def test_source_boundaries_generate_repeatable_c1_tasks(self):
        boundary_dir = next_task.DATA_CURRENT / "source_boundaries"
        boundary_dir.mkdir(parents=True)
        (boundary_dir / "queue.jsonl").write_text(
            json.dumps(
                {
                    "id": "C1-GWINS-list_2_70",
                    "source_site": "gwins",
                    "boundary_type": "index_page",
                    "natural_boundary": "GWINS list_2_70",
                    "url": "https://www.gwins.org/cn/milesguo/list_2_70.html",
                    "status": "open",
                    "priority": 110,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        tasks = next_task.eligible_tasks()
        self.assertEqual([task["id"] for task in tasks], ["C1-GWINS-list_2_70"])
        self.assertEqual(tasks[0]["kind"], "source_boundary_discovery")

    def test_orphaned_in_progress_boundary_is_reclaimable(self):
        boundary_dir = next_task.DATA_CURRENT / "source_boundaries"
        boundary_dir.mkdir(parents=True)
        (boundary_dir / "queue.jsonl").write_text(
            json.dumps(
                {
                    "id": "C1-GWINS-detail-demo",
                    "source_site": "gwins",
                    "boundary_type": "detail_page",
                    "natural_boundary": "GWINS detail demo",
                    "url": "https://www.gwins.org/cn/milesguo/demo.html",
                    "status": "in_progress",
                    "priority": 110,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        tasks = next_task.eligible_tasks()

        self.assertEqual([task["id"] for task in tasks], ["C1-GWINS-detail-demo"])

    def test_source_boundary_string_dependency_is_not_split_into_characters(self):
        boundary_dir = next_task.DATA_CURRENT / "source_boundaries"
        boundary_dir.mkdir(parents=True)
        (boundary_dir / "queue.jsonl").write_text(
            json.dumps(
                {
                    "id": "C1-GWINS-list_2_69",
                    "source_site": "gwins",
                    "boundary_type": "index_page",
                    "natural_boundary": "GWINS list_2_69",
                    "url": "https://www.gwins.org/cn/milesguo/list_2_69.html",
                    "status": "open",
                    "priority": 110,
                    "depends_on": "C1-GWINS-list_2_70",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        self.assertEqual(next_task.source_boundary_tasks(set())[0]["depends_on"], ["C1-GWINS-list_2_70"])

    def test_c2_is_blocked_while_phase1_source_boundaries_remain_open(self):
        self.write_queue(
            {
                "id": "C2-CANDIDATE-PROMOTION",
                "priority": 90,
                "depends_on": [],
                "kind": "candidate_promotion",
                "scope": "promote candidates",
            }
        )
        next_task.WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
        next_task.WORKFLOW.write_text(
            json.dumps({"current_major_phase": "PHASE_1_COLLECTION"}),
            encoding="utf-8",
        )
        boundary_dir = next_task.DATA_CURRENT / "source_boundaries"
        boundary_dir.mkdir(parents=True)
        (boundary_dir / "queue.jsonl").write_text(
            json.dumps(
                {
                    "id": "C1-GETTRSEARCH-post-demo",
                    "source_site": "gettrsearch",
                    "boundary_type": "detail_page",
                    "natural_boundary": "demo",
                    "url": "https://gettr.com/post/demo",
                    "status": "open",
                    "priority": 105,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        ids = [task["id"] for task in next_task.eligible_tasks()]

        self.assertIn("C1-GETTRSEARCH-post-demo", ids)
        self.assertNotIn("C2-CANDIDATE-PROMOTION", ids)

    def test_completed_phase1_boundary_does_not_keep_c2_blocked(self):
        self.write_queue(
            {
                "id": "C2-CANDIDATE-PROMOTION",
                "priority": 90,
                "depends_on": [],
                "kind": "candidate_promotion",
                "scope": "promote candidates",
            }
        )
        next_task.WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
        next_task.WORKFLOW.write_text(
            json.dumps({"current_major_phase": "PHASE_1_COLLECTION"}),
            encoding="utf-8",
        )
        boundary_dir = next_task.DATA_CURRENT / "source_boundaries"
        boundary_dir.mkdir(parents=True)
        boundary_id = "C1-GETTRSEARCH-post-demo"
        (boundary_dir / "queue.jsonl").write_text(
            json.dumps(
                {
                    "id": boundary_id,
                    "source_site": "gettrsearch",
                    "boundary_type": "detail_page",
                    "natural_boundary": "demo",
                    "url": "https://gettr.com/post/demo",
                    "status": "open",
                    "priority": 105,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (next_task.COMPLETED / f"{boundary_id}.json").write_text(
            json.dumps({"task_id": boundary_id, "status": "completed"}),
            encoding="utf-8",
        )

        ids = [task["id"] for task in next_task.eligible_tasks()]

        self.assertFalse(next_task.has_unfinished_source_boundaries())
        self.assertEqual(ids, ["C2-CANDIDATE-PROMOTION"])

    def test_live_work_items_are_blocked_until_phase1_collection_promotes_candidates(self):
        next_task.WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
        next_task.WORKFLOW.write_text(
            json.dumps({"current_major_phase": "PHASE_1_COLLECTION"}),
            encoding="utf-8",
        )
        work_item_dir = next_task.DATA_CURRENT / "live_work_items"
        work_item_dir.mkdir(parents=True)
        (work_item_dir / "items.jsonl").write_text(
            json.dumps(
                {
                    "id": "WI_LIVE_TEST_metadata_fill",
                    "live_id": "LIVE_TEST",
                    "work_stage": "metadata_fill",
                    "work_status": "open",
                    "natural_boundary": "one live",
                    "instructions": "fill metadata",
                    "priority": 72,
                    "created_at": "2026-09-18T00:00:00Z",
                    "updated_at": "2026-09-18T00:00:00Z",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        self.assertEqual(next_task.live_work_item_tasks(set()), [])

    def test_watch_refreshes_origin_main_before_each_queue_check(self):
        task = {"id": "C1-GWINS-detail-demo"}
        completed = type(
            "CompletedProcess",
            (),
            {"returncode": 0, "stdout": "Already up to date.\n", "stderr": ""},
        )()
        with patch.object(next_task.subprocess, "run", return_value=completed) as run, patch.object(
            next_task, "eligible_tasks", side_effect=[[], [task]]
        ) as eligible, patch.object(next_task.time, "sleep") as sleep:
            result = next_task.watch_for_task(10, None)

        self.assertEqual(result, [task])
        self.assertEqual(run.call_count, 2)
        self.assertEqual(eligible.call_count, 2)
        sleep.assert_called_once_with(10)
        self.assertEqual(
            run.call_args_list[0].args[0],
            ["git", "pull", "--ff-only", "origin", "main"],
        )

    def test_watch_stops_when_origin_main_cannot_be_refreshed(self):
        failed = type(
            "CompletedProcess",
            (),
            {"returncode": 1, "stdout": "", "stderr": "not possible to fast-forward"},
        )()
        with patch.object(next_task.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(SystemExit, "polling stale state"):
                next_task.refresh_main_for_watch()

    def test_candidate_review_moves_through_three_states(self):
        candidate_id = self.write_candidate()
        base_now = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)

        initial = next_task.candidate_review_states(now=base_now)
        self.assertEqual(initial[0]["state"], "unreviewed")
        self.assertEqual(initial[0]["next_generation"], 1)

        task = next_task.candidate_review_tasks()[0]
        claim_path = next_task.claim_task(task, "agent-reviewer")
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        self.assertEqual(claim["entry_mode"], "work")
        claim["claimed_at"] = base_now.isoformat()
        claim_path.write_text(json.dumps(claim), encoding="utf-8")

        active = next_task.candidate_review_states(now=base_now + timedelta(hours=1))
        self.assertEqual(active[0]["state"], "in_progress")

        completion = {
            "task_id": task["id"],
            "kind": "candidate_promotion_review",
            "source_candidate_id": candidate_id,
            "review_generation": 1,
            "completed_at": (base_now + timedelta(hours=2)).isoformat(),
        }
        grandfather_path = self.root / "coordination" / "candidate_review_grandfathered.json"
        grandfather_path.write_text(
            json.dumps({"task_ids": [task["id"]]}), encoding="utf-8"
        )
        (next_task.COMPLETED / f"{task['id']}.json").write_text(
            json.dumps(completion), encoding="utf-8"
        )

        reviewed = next_task.candidate_review_states(now=base_now + timedelta(hours=11))
        self.assertEqual(reviewed[0]["state"], "reviewed")
        self.assertEqual(reviewed[0]["next_generation"], 2)

        still_reviewed = next_task.candidate_review_states(now=base_now + timedelta(days=30))
        self.assertEqual(still_reviewed[0]["state"], "reviewed")

    def test_invalid_candidate_completion_does_not_count_as_reviewed(self):
        self.write_candidate()
        task = next_task.candidate_review_tasks()[0]
        (next_task.COMPLETED / f"{task['id']}.json").write_text(
            json.dumps(
                {
                    "task_id": task["id"],
                    "kind": "candidate_promotion_review",
                    "source_candidate_id": task["source_candidate_id"],
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "outputs": [],
                }
            ),
            encoding="utf-8",
        )

        state = next_task.candidate_review_states()[0]
        self.assertEqual(state["state"], "unreviewed")
        self.assertEqual(state["next_generation"], 2)
        self.assertNotIn(task["id"], next_task.completed_ids())

    def test_in_progress_review_returns_to_unreviewed_after_ten_hours(self):
        self.write_candidate()
        base_now = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)
        task = next_task.candidate_review_tasks()[0]
        claim_path = next_task.claim_task(task, "agent-reviewer")
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        claim["claimed_at"] = base_now.isoformat()
        claim_path.write_text(json.dumps(claim), encoding="utf-8")

        active = next_task.candidate_review_states(now=base_now + timedelta(hours=9))
        self.assertEqual(active[0]["state"], "in_progress")
        self.assertIsNotNone(active[0]["claim_expires_at"])

        expired = next_task.candidate_review_states(now=base_now + timedelta(hours=10))
        self.assertEqual(expired[0]["state"], "unreviewed")
        self.assertEqual(expired[0]["next_generation"], 2)

    def test_candidate_review_missing_or_conflicting_static_lease_still_expires_at_ten_hours(self):
        base_now = datetime.now(timezone.utc).replace(microsecond=0)
        for static_value in (None, 24, "invalid"):
            claim = {
                "task_id": "C2-REVIEW-SC_GWINS_TEST-R001",
                "kind": "candidate_promotion_review",
                "status": "in_progress",
                "claimed_at": base_now.isoformat(),
            }
            if static_value is not None:
                claim["static_claim_lease_hours"] = static_value
            with self.subTest(static_value=static_value):
                self.assertFalse(next_task.claim_expired(
                    claim, now=base_now + timedelta(hours=10) - timedelta(microseconds=1)
                ))
                self.assertTrue(next_task.claim_expired(
                    claim, now=base_now + timedelta(hours=10)
                ))

    def test_non_candidate_static_lease_remains_configurable(self):
        base_now = datetime.now(timezone.utc).replace(microsecond=0)
        claim = {
            "task_id": "C1-GWINS-list_2_1",
            "status": "in_progress",
            "claimed_at": base_now.isoformat(),
            "static_claim_lease_hours": 12,
        }
        self.assertFalse(next_task.claim_expired(
            claim, now=base_now + timedelta(hours=11)
        ))
        self.assertTrue(next_task.claim_expired(
            claim, now=base_now + timedelta(hours=12)
        ))

    def test_candidate_review_claims_are_independent(self):
        first = self.write_candidate("SC_GWINS_A")
        second = self.write_candidate("SC_GWINS_B")
        tasks = next_task.candidate_review_tasks()
        by_candidate = {task["source_candidate_id"]: task for task in tasks}

        next_task.claim_task(by_candidate[first], "agent-a")
        states = {row["candidate_id"]: row["state"] for row in next_task.candidate_review_states()}

        self.assertEqual(states[first], "in_progress")
        self.assertEqual(states[second], "unreviewed")

    def test_candidate_review_batch_claims_one_hundred_and_does_not_top_up(self):
        for index in range(105):
            self.write_candidate(f"SC_GWINS_BATCH_{index:03d}")

        batch = next_task.claim_candidate_review_batch(
            next_task.candidate_review_tasks(), "agent-batch"
        )
        self.assertEqual(batch["target_size"], 100)
        self.assertEqual(batch["claimed_count"], 100)
        self.assertEqual(len(batch["new_paths"]), 100)
        states = next_task.candidate_review_states()
        self.assertEqual(sum(row["state"] == "in_progress" for row in states), 100)
        self.assertEqual(sum(row["state"] == "unreviewed" for row in states), 5)

        first_task = batch["task_ids"][0]
        first_candidate = json.loads(
            (next_task.CLAIMS / f"{first_task}.json").read_text(encoding="utf-8")
        )["source_candidate_id"]
        artifact = self.write_review_artifact(
            first_task, first_candidate, "agent-batch"
        )
        next_task.finish_task(
            task_id=first_task,
            agent_id="agent-batch",
            outputs=[artifact],
            validation="identity checked",
            live_id=None,
            full_archive_decision=None,
        )
        continued = next_task.claim_candidate_review_batch(
            next_task.candidate_review_tasks(), "agent-batch"
        )
        self.assertTrue(continued["continued"])
        self.assertEqual(continued["claimed_count"], 100)
        self.assertEqual(continued["active_count"], 99)
        self.assertEqual(continued["new_paths"], [])
        states = next_task.candidate_review_states()
        self.assertEqual(sum(row["state"] == "reviewed" for row in states), 1)
        self.assertEqual(sum(row["state"] == "in_progress" for row in states), 99)
        self.assertEqual(sum(row["state"] == "unreviewed" for row in states), 5)

    def test_candidate_review_batch_adopts_existing_single_claim(self):
        for index in range(101):
            self.write_candidate(f"SC_GWINS_ADOPT_{index:03d}")
        first = next_task.candidate_review_tasks()[0]
        first_path = next_task.claim_task(first, "agent-adopt")

        batch = next_task.claim_candidate_review_batch(
            next_task.candidate_review_tasks(), "agent-adopt"
        )
        self.assertEqual(batch["claimed_count"], 100)
        self.assertEqual(len(batch["new_paths"]), 99)
        adopted = json.loads(first_path.read_text(encoding="utf-8"))
        self.assertEqual(adopted["review_batch_id"], batch["batch_id"])
        self.assertEqual(adopted["review_batch_position"], 1)
        self.assertEqual(adopted["review_batch_claimed_count"], 100)

    def test_candidate_review_batch_claims_final_remainder(self):
        for index in range(31):
            self.write_candidate(f"SC_GWINS_FINAL_{index:03d}")

        batch = next_task.claim_candidate_review_batch(
            next_task.candidate_review_tasks(), "agent-final"
        )

        self.assertEqual(batch["target_size"], 31)
        self.assertEqual(batch["claimed_count"], 31)
        for task_id in batch["task_ids"]:
            claim = json.loads(
                (next_task.CLAIMS / f"{task_id}.json").read_text(encoding="utf-8")
            )
            self.assertTrue(claim["review_batch_final_remainder"])

    def test_candidate_review_final_remainder_can_finish(self):
        for index in range(31):
            self.write_candidate(f"SC_GWINS_FINAL_{index:03d}")

        batch = next_task.claim_candidate_review_batch(
            next_task.candidate_review_tasks(), "agent-final"
        )
        task_id = batch["task_ids"][0]
        claim = json.loads(
            (next_task.CLAIMS / f"{task_id}.json").read_text(encoding="utf-8")
        )
        artifact = self.write_review_artifact(
            task_id, claim["source_candidate_id"], "agent-final"
        )

        completed_path, marker = next_task.finish_task(
            task_id=task_id,
            agent_id="agent-final",
            outputs=[artifact],
            validation="identity checked",
            live_id=None,
            full_archive_decision=None,
        )
        completed = json.loads(completed_path.read_text(encoding="utf-8"))

        self.assertIsNone(marker)
        self.assertTrue(completed["review_batch_final_remainder"])
        self.assertEqual(completed["review_batch_target_size"], 31)
        self.assertEqual(completed["review_batch_claimed_count"], 31)

    def test_candidate_review_finish_carries_timeout_metadata(self):
        candidate_id = self.write_candidate()
        task = next_task.candidate_review_tasks()[0]
        next_task.claim_task(task, "agent-reviewer")
        self.mark_as_complete_work_batch_member(task["id"])
        artifact = self.write_review_artifact(
            task["id"], candidate_id, "agent-reviewer"
        )

        completed_path, marker = next_task.finish_task(
            task_id=task["id"],
            agent_id="agent-reviewer",
            outputs=[artifact],
            validation="identity checked",
            live_id="LIVE_20261004_001",
            full_archive_decision=None,
        )
        completed = json.loads(completed_path.read_text(encoding="utf-8"))

        self.assertIsNone(marker)
        self.assertEqual(completed["source_candidate_id"], candidate_id)
        self.assertEqual(completed["review_generation"], 1)
        self.assertEqual(completed["review_claim_timeout_hours"], 10)
        self.assertEqual(completed["entry_mode"], "work")
        self.assertNotIn("review_expires_at", completed)
        self.assertEqual(completed["review_artifact"], artifact)
        self.assertEqual(completed["review_decision"], "linked_existing_canonical")

    def test_candidate_review_finish_rejects_empty_outputs(self):
        self.write_candidate()
        task = next_task.candidate_review_tasks()[0]
        next_task.claim_task(task, "agent-reviewer")

        with self.assertRaisesRegex(SystemExit, "empty outputs"):
            next_task.finish_task(
                task_id=task["id"],
                agent_id="agent-reviewer",
                outputs=[],
                validation="generic assertion",
                live_id=None,
                full_archive_decision=None,
            )

    def test_candidate_review_finish_rejects_unverified_decision(self):
        candidate_id = self.write_candidate()
        task = next_task.candidate_review_tasks()[0]
        next_task.claim_task(task, "agent-reviewer")
        relative = self.write_review_artifact(task["id"], candidate_id, "agent-reviewer")
        path = self.root / relative
        artifact = json.loads(path.read_text(encoding="utf-8"))
        artifact["decision"] = "insufficient_public_evidence"
        path.write_text(json.dumps(artifact), encoding="utf-8")

        with self.assertRaisesRegex(SystemExit, "final evidence-backed decision"):
            next_task.finish_task(
                task_id=task["id"],
                agent_id="agent-reviewer",
                outputs=[relative],
                validation="unable to verify",
                live_id=None,
                full_archive_decision=None,
            )

    def test_candidate_review_scope_excludes_later_video_processing(self):
        self.write_candidate()
        scope = next_task.candidate_review_tasks()[0]["scope"]
        self.assertIn("Do not perform playback audit", scope)
        self.assertIn("transcription", scope)
        self.assertIn("segmentation", scope)


if __name__ == "__main__":
    unittest.main()
