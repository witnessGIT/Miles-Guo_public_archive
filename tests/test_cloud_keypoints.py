import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import cloud_keypoint_item
from scripts.cloud_keypoint_runner import write_result
from scripts.cloud_keypoint_item import likely_substantive, locate_evidence, parse_json_array, process_live, prompt_for, validate_results


class CloudKeyPointTests(unittest.TestCase):
    def test_isolated_runner_writes_structured_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            write_result(path, {"outputs": ["one.jsonl"], "stats": {"key_points": 2}})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["stats"]["key_points"], 2)

    def test_parse_fenced_array(self):
        value = parse_json_array('```json\n[{"point_text":"测试"}]\n```')
        self.assertEqual(value[0]["point_text"], "测试")

    def test_prompt_requires_points_for_short_or_personal_content(self):
        prompt = prompt_for({"text_asr": "我正在锻炼，稍后录视频。"})
        self.assertIn("就不得输出[]", prompt)
        self.assertIn("生活内容", prompt)

    def test_repetition_filter_distinguishes_content_from_repeated_subtitles(self):
        self.assertTrue(likely_substantive("昨天发生很多事情，我稍后会录制视频详细说明有关人员和计划。" * 3))
        self.assertFalse(likely_substantive("字幕志愿者 李宗盛 " * 30))

    def test_requires_exact_evidence_and_controlled_topic(self):
        segment = {"text_asr": "他说今天主要讨论法律程序和案件进展。"}
        accepted = validate_results(segment, [{
            "point_type": "context",
            "point_text": "本段讨论法律程序和案件进展",
            "significance": "便于定位法律议题",
            "evidence_quote": "主要讨论法律程序和案件进展",
            "topic_ids": ["TOPIC_LAW_JUSTICE", "NOT_ALLOWED"],
        }])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["topic_ids"], ["TOPIC_LAW_JUSTICE"])
        self.assertEqual(accepted[0]["evidence_start_char"], 4)

    def test_rejects_ungrounded_summary(self):
        segment = {"text_asr": "这里只是简单问候大家。"}
        rejected = validate_results(segment, [{
            "point_type": "takeaway",
            "point_text": "本段讨论了一项重大国际事件",
            "evidence_quote": "重大国际事件",
            "topic_ids": ["TOPIC_INTERNATIONAL_RELATIONS"],
        }])
        self.assertEqual(rejected, [])

    def test_locates_simplified_quote_in_traditional_source(self):
        source = "昨天發生很多事情，特別是我揭發的幾個盜國賊。"
        evidence = "特别是我揭发的几个盗国贼"
        class FakeT2S:
            def convert(self, value):
                return value.translate(str.maketrans("發別幾盜國賊", "发别几盗国贼"))

        with mock.patch.object(cloud_keypoint_item, "_T2S", FakeT2S()):
            span = locate_evidence(source, evidence)
        self.assertIsNotNone(span)
        self.assertEqual(source[slice(*span)], "特別是我揭發的幾個盜國賊")

    def test_accepts_multiple_independent_points(self):
        segment = {"text_asr": "先讨论案件进展，然后说明下周召开记者会。"}
        accepted = validate_results(segment, [
            {"point_type": "context", "point_text": "讨论案件进展", "evidence_quote": "讨论案件进展", "topic_ids": ["TOPIC_LAW_JUSTICE"]},
            {"point_type": "instruction", "point_text": "计划下周召开记者会", "evidence_quote": "下周召开记者会", "topic_ids": ["TOPIC_MEDIA_PUBLIC_OPINION"]},
        ])
        self.assertEqual(len(accepted), 2)

    def test_process_live_records_no_substantive_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            segment_dir = repo / "data" / "current" / "live_segments"
            segment_dir.mkdir(parents=True)
            segment = {
                "id": "LIVE_TEST_001_SEG_000000",
                "text_asr": "这里包含一段可以整理的测试内容。",
                "boundary_method": "natural_asr_v1:test",
            }
            (segment_dir / "asr_live_test_001.jsonl").write_text(
                json.dumps(segment, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            _outputs, stats = process_live(repo, "LIVE_TEST_001", lambda _prompt: "[]")
            self.assertEqual(stats["outcome"], "no_substantive_content")
            self.assertEqual(stats["key_points"], 0)
            self.assertTrue(
                (repo / "data" / "current" / "segment_key_points" / "machine_live_test_001.jsonl").exists()
            )

    def test_process_live_retries_substantive_empty_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            segment_dir = repo / "data" / "current" / "live_segments"
            segment_dir.mkdir(parents=True)
            text = "昨天发生很多事情，我正在锻炼，并计划稍后录制视频详细说明有关人员的行动。" * 2
            segment = {
                "id": "LIVE_TEST_002_SEG_000000",
                "text_asr": text,
                "boundary_method": "natural_asr_v1:test",
            }
            (segment_dir / "asr_live_test_002.jsonl").write_text(
                json.dumps(segment, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            responses = iter([
                "[]",
                json.dumps([{
                    "point_type": "instruction",
                    "point_text": "计划稍后录制视频",
                    "significance": "记录后续行动",
                    "evidence_quote": "计划稍后录制视频",
                    "topic_ids": ["TOPIC_PROJECT_ACTION"],
                }], ensure_ascii=False),
            ])
            _outputs, stats = process_live(repo, "LIVE_TEST_002", lambda _prompt: next(responses))
            self.assertEqual(stats["key_points"], 1)
            self.assertEqual(stats["forced_retries"], 1)

    def test_process_live_retries_rejected_ungrounded_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            segment_dir = repo / "data" / "current" / "live_segments"
            segment_dir.mkdir(parents=True)
            text = "昨天发生很多事情，我正在锻炼，并计划稍后录制视频详细说明有关人员的行动。" * 2
            segment = {
                "id": "LIVE_TEST_003_SEG_000000",
                "text_asr": text,
                "boundary_method": "natural_asr_v1:test",
            }
            (segment_dir / "asr_live_test_003.jsonl").write_text(
                json.dumps(segment, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            responses = iter([
                json.dumps([{
                    "point_type": "takeaway",
                    "point_text": "模型补充了原文没有的信息",
                    "evidence_quote": "原文完全不存在的证据",
                    "topic_ids": ["TOPIC_OTHER"],
                }], ensure_ascii=False),
                json.dumps([{
                    "point_type": "instruction",
                    "point_text": "计划稍后录制视频",
                    "evidence_quote": "计划稍后录制视频",
                    "topic_ids": ["TOPIC_PROJECT_ACTION"],
                }], ensure_ascii=False),
            ])
            _outputs, stats = process_live(repo, "LIVE_TEST_003", lambda _prompt: next(responses))
            self.assertEqual(stats["key_points"], 1)
            self.assertEqual(stats["forced_retries"], 1)
            self.assertEqual(stats["rejected_all"], 0)


if __name__ == "__main__":
    unittest.main()
