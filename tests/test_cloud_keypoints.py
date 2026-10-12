import unittest

from scripts.cloud_keypoint_item import parse_json_object, validate_result


class CloudKeyPointTests(unittest.TestCase):
    def test_parse_fenced_object(self):
        value = parse_json_object('```json\n{"point_text":"测试"}\n```')
        self.assertEqual(value["point_text"], "测试")

    def test_requires_exact_evidence_and_controlled_topic(self):
        segment = {"text_asr": "他说今天主要讨论法律程序和案件进展。"}
        accepted = validate_result(segment, {
            "point_type": "context",
            "point_text": "本段讨论法律程序和案件进展",
            "significance": "便于定位法律议题",
            "evidence_quote": "主要讨论法律程序和案件进展",
            "topic_ids": ["TOPIC_LAW_JUSTICE", "NOT_ALLOWED"],
        })
        self.assertIsNotNone(accepted)
        self.assertEqual(accepted["topic_ids"], ["TOPIC_LAW_JUSTICE"])

    def test_rejects_ungrounded_summary(self):
        segment = {"text_asr": "这里只是简单问候大家。"}
        rejected = validate_result(segment, {
            "point_type": "takeaway",
            "point_text": "本段讨论了一项重大国际事件",
            "evidence_quote": "重大国际事件",
            "topic_ids": ["TOPIC_INTERNATIONAL_RELATIONS"],
        })
        self.assertIsNone(rejected)


if __name__ == "__main__":
    unittest.main()
