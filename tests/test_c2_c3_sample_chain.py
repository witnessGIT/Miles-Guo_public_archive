import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "current"


def iter_jsonl(path: Path):
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if text:
            yield json.loads(text)


class C2C3SampleChainTest(unittest.TestCase):
    def test_sample_lives_have_sources_media_and_work_items(self):
        lives = {row["id"] for row in iter_jsonl(DATA / "live_videos" / "c2_sample_gwins.jsonl")}
        self.assertEqual(
            lives,
            {"LIVE_20171102_001", "LIVE_20171023_001", "LIVE_20170924_001"},
        )

        sources = list(iter_jsonl(DATA / "sources" / "c2_sample_gwins_sources.jsonl"))
        for live_id in lives:
            live_sources = [row for row in sources if row["live_id"] == live_id]
            self.assertEqual(len(live_sources), 3)
            self.assertTrue(any(row["source_site"] == "GWINS" for row in live_sources))
            self.assertTrue(any(row["source_site"] == "YOUTUBE" for row in live_sources))
            self.assertTrue(any(row["source_site"] == "RUMBLE" for row in live_sources))

        assets = list(iter_jsonl(DATA / "media_assets" / "c2_sample_gwins_media_assets.jsonl"))
        for live_id in lives:
            self.assertEqual(len([row for row in assets if row["live_id"] == live_id]), 2)

        items = list(iter_jsonl(DATA / "live_work_items" / "generated.jsonl"))
        sample_items = [row for row in items if row["live_id"] in lives]
        self.assertEqual(len(sample_items), 30)
        self.assertTrue(all(row["work_status"] == "open" for row in sample_items))

    def test_promoted_candidates_keep_live_ids(self):
        promoted = {}
        for row in iter_jsonl(DATA / "source_candidates" / "gwins" / "list_2_68.jsonl"):
            if row["id"] in {
                "SC_GWINS_LIST2_68_20171102",
                "SC_GWINS_LIST2_68_20171023_1",
                "SC_GWINS_LIST2_68_20170924",
            }:
                promoted[row["id"]] = row

        self.assertEqual(promoted["SC_GWINS_LIST2_68_20171102"]["candidate_live_id"], "LIVE_20171102_001")
        self.assertEqual(promoted["SC_GWINS_LIST2_68_20171023_1"]["candidate_live_id"], "LIVE_20171023_001")
        self.assertEqual(promoted["SC_GWINS_LIST2_68_20170924"]["candidate_live_id"], "LIVE_20170924_001")
        self.assertTrue(all(row["status"] == "promoted" for row in promoted.values()))


if __name__ == "__main__":
    unittest.main()
