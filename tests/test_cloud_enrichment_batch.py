import tempfile
import unittest
from pathlib import Path

from scripts.select_cloud_enrichment_batch import select_live_ids


class SharedEnrichmentBatchTests(unittest.TestCase):
    def test_supports_a_150_video_logical_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            completed = repo / "coordination" / "completed"
            completed.mkdir(parents=True)
            (repo / "coordination" / "claims").mkdir()
            for index in range(1, 201):
                (completed / f"WI_LIVE_{index:03d}_segment_split.json").write_text("{}")

            selected = select_live_ids(repo, 150)

            self.assertEqual(len(selected), 150)
            self.assertEqual(len(set(selected)), 150)

    def test_selects_one_shared_set_and_skips_fully_completed_videos(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            completed = repo / "coordination" / "completed"
            completed.mkdir(parents=True)
            (repo / "coordination" / "claims").mkdir()
            for live_id in ("LIVE_1", "LIVE_2", "LIVE_3"):
                (completed / f"WI_{live_id}_segment_split.json").write_text("{}")
            (completed / "WI_LIVE_1_entity_pass.json").write_text("{}")
            (completed / "WI_LIVE_2_key_points_topics.json").write_text("{}")
            (completed / "WI_LIVE_2_entity_pass.json").write_text("{}")

            self.assertEqual(select_live_ids(repo, 50), ["LIVE_1", "LIVE_3"])

    def test_batch_limit_applies_to_unique_videos_not_individual_stages(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            completed = repo / "coordination" / "completed"
            completed.mkdir(parents=True)
            (repo / "coordination" / "claims").mkdir()
            for index in range(1, 4):
                (completed / f"WI_LIVE_{index}_segment_split.json").write_text("{}")

            self.assertEqual(select_live_ids(repo, 2), ["LIVE_1", "LIVE_2"])


if __name__ == "__main__":
    unittest.main()
