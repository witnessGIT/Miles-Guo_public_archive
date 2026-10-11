import unittest

from scripts.cloud_entity_item import enrich_segments, entity_id, parse_json_array


class CloudEntityTest(unittest.TestCase):
    def test_parser_accepts_fenced_json(self):
        self.assertEqual(parse_json_array('```json\n[{"canonical_name":"王岐山"}]\n```')[0]["canonical_name"], "王岐山")

    def test_only_exact_mentions_are_published(self):
        segments = [{"id": "LIVE_X_SEG_000000", "text_asr": "王岐山谈到海航"}]
        response = '[{"canonical_name":"王岐山","mention_text":"王岐山","entity_type":"person","mention_role":"mentioned"},{"canonical_name":"习近平","mention_text":"习近平","entity_type":"person","mention_role":"mentioned"}]'
        updated, entities, links, stats = enrich_segments("LIVE_X", segments, lambda _prompt: response)
        self.assertEqual([row["canonical_name"] for row in entities], ["王岐山"])
        self.assertEqual(len(links), 1)
        self.assertEqual(updated[0]["entities_json"], ["王岐山"])
        self.assertEqual(stats["invalid_responses"], 0)

    def test_ids_are_stable_and_live_scoped(self):
        self.assertEqual(entity_id("LIVE_X", "person", "王岐山"), entity_id("LIVE_X", "person", "王岐山"))
        self.assertNotEqual(entity_id("LIVE_X", "person", "王岐山"), entity_id("LIVE_Y", "person", "王岐山"))


if __name__ == "__main__":
    unittest.main()
