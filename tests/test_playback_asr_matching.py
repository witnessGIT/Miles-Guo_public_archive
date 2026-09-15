import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import process_playback_request as processor


class PlaybackAsrMatchingTests(unittest.TestCase):
    def test_short_target_inside_longer_whisper_cue_is_exact_candidate(self):
        entries = [{
            "start_sec": 12.5,
            "end_sec": 16.0,
            "text": "共匪下令，这回是绝对可以确定的",
        }]
        match = processor.best_asr_match(entries, "共匪下令", "共匪下令")
        self.assertIsNotNone(match)
        self.assertTrue(match["exact_target_substring"])
        self.assertEqual(match["score"], 1.0)
        self.assertEqual(match["local_start_sec"], 12.5)

    def test_unrelated_whisper_cue_is_not_promoted(self):
        entries = [{"start_sec": 1.0, "end_sec": 2.0, "text": "今天天气很好"}]
        match = processor.best_asr_match(entries, "共匪下令", "共匪下令")
        self.assertIsNotNone(match)
        self.assertFalse(match["exact_target_substring"])
        self.assertLess(match["score"], processor.MIN_AGENT_REVIEW_SCORE)

    def test_narrowest_exact_window_controls_observed_time(self):
        entries = [
            {"start_sec": 0.0, "end_sec": 4.0, "text": "前面的内容"},
            {"start_sec": 4.0, "end_sec": 8.0, "text": "还是前面的内容"},
            {"start_sec": 8.0, "end_sec": 12.0, "text": "更多前文"},
            {"start_sec": 12.5, "end_sec": 17.0, "text": "共匪下令，这回确定了"},
        ]
        match = processor.best_asr_match(entries, "共匪下令", "共匪下令")
        self.assertEqual(match["score"], 1.0)
        self.assertEqual(match["entry_count"], 1)
        self.assertEqual(match["local_start_sec"], 12.5)


if __name__ == "__main__":
    unittest.main()
