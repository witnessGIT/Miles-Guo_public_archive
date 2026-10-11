import hashlib
import unittest

from scripts.build_natural_segments import build_segments, split_cues


def cue(index, start, end, text):
    return {
        "id": f"C{index}", "cue_index": index, "live_id": "LIVE_20200101_001",
        "start_sec": start, "end_sec": end, "text": text,
    }


class NaturalSegmentsTest(unittest.TestCase):
    def test_prefers_discourse_boundary_after_minimum_duration(self):
        cues = [cue(0, 0, 15, "第一件事"), cue(1, 15, 30, "继续说明"), cue(2, 30, 40, "另外谈第二件事")]
        groups = split_cues(cues)
        self.assertEqual([len(group) for group, _ in groups], [2, 1])
        self.assertEqual(groups[1][1], "discourse_marker")

    def test_pause_creates_natural_boundary(self):
        cues = [cue(0, 0, 25, "前一段"), cue(1, 28, 35, "后一段")]
        groups = split_cues(cues)
        self.assertEqual([method for _, method in groups], ["transcript_start", "asr_pause"])

    def test_build_preserves_timing_and_hashes_search_text(self):
        cues = [cue(0, 1, 10, "第一句"), cue(1, 10, 20, "第二句")]
        template = {"created_at": "2026-01-01T00:00:00Z", "asr_source_id": "SRC_1", "time_source_id": "SRC_1", "source_verified": 1}
        rows = build_segments(cues, template)
        self.assertEqual(rows[0]["start_sec"], 1)
        self.assertEqual(rows[0]["end_sec"], 20)
        self.assertEqual(rows[0]["text_asr"], "第一句 第二句")
        self.assertEqual(rows[0]["content_sha256"], hashlib.sha256("第一句 第二句".encode()).hexdigest())
        self.assertEqual(rows[0]["review_status"], "machine")


if __name__ == "__main__":
    unittest.main()
