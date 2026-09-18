import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
