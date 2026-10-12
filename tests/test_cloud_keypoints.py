import unittest

from scripts.cloud_keypoint_item import parse_json_array, validate_results


class CloudKeyPointTests(unittest.TestCase):
    def test_parse_fenced_array(self):
        value = parse_json_array('```json\n[{"point_text":"测试"}]\n```')
        self.assertEqual(value[0]["point_text"], "测试")

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

    def test_accepts_multiple_independent_points(self):
        segment = {"text_asr": "先讨论案件进展，然后说明下周召开记者会。"}
        accepted = validate_results(segment, [
            {"point_type": "context", "point_text": "讨论案件进展", "evidence_quote": "讨论案件进展", "topic_ids": ["TOPIC_LAW_JUSTICE"]},
            {"point_type": "instruction", "point_text": "计划下周召开记者会", "evidence_quote": "下周召开记者会", "topic_ids": ["TOPIC_MEDIA_PUBLIC_OPINION"]},
        ])
        self.assertEqual(len(accepted), 2)


if __name__ == "__main__":
    unittest.main()
