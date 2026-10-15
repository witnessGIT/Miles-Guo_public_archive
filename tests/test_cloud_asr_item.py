import unittest
from unittest.mock import patch

from scripts.cloud_asr_item import resolve_media_url


class CloudAsrItemTests(unittest.TestCase):
    def test_rumble_audit_embed_id_is_supported(self):
        asset = {
            "platform": "RUMBLE",
            "url": "https://rumble.com/example.html",
            "metadata_json": '{"embed_id": "v-example"}',
        }
        response = {
            "u": {"mp4": {"url": "https://cdn.example/high.mp4", "meta": {"bitrate": 800}}},
            "ua": {"mp4": {"360": {"url": "https://cdn.example/low.mp4", "meta": {"bitrate": 300}}}},
        }
        with patch("scripts.cloud_asr_item.http_json", return_value=response) as mocked:
            self.assertEqual(resolve_media_url(asset), "https://cdn.example/low.mp4")
        self.assertIn("v=v-example", mocked.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
