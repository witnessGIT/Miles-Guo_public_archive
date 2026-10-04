from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.request import Request

SPEC = importlib.util.spec_from_file_location("c2_metadata_evidence", Path(__file__).resolve().parents[1] / "scripts/c2_metadata_evidence.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

class MetadataEvidenceTests(unittest.TestCase):
    def test_allowlist_and_no_media(self):
        self.assertEqual(m.allowed_url("https://www.gwins.org/cn/milesguo/24186.html"), "https://www.gwins.org/cn/milesguo/24186.html")
        for value in ["http://gwins.org/cn/milesguo/24186.html", "https://evil.test/cn/milesguo/24186.html", "https://u:p@gwins.org/cn/milesguo/24186.html", "https://gwins.org:443/cn/milesguo/24186.html", "https://gwins.org/video.mp4", "https://gwins.org/cn/milesguo/24186.html?url=http://localhost", "https://127.0.0.1/cn/milesguo/24186.html"]:
            with self.subTest(value=value), self.assertRaises(ValueError): m.allowed_url(value)

    def test_redirect_cannot_change_host_or_identity(self):
        r = m.SafeRedirect()
        req = Request("https://gwins.org/cn/milesguo/24186.html")
        for url in ["https://example.org/cn/milesguo/24186.html", "https://gwins.org/cn/milesguo/24187.html"]:
            with self.assertRaises(ValueError): r.redirect_request(req, None, 302, "", {}, url)

    def test_extract_actual_targets_not_labels_and_no_script(self):
        raw = ('<title>20230101_1 上半场</title><script>录一段假视频</script><p>今天录一段视频。</p><a href="https://rumble.com/v123-test.html">GETTR</a><a href="https://evil.test/a.mp4">视频</a>').encode()
        result = m.parse_page(raw, "https://gwins.org/cn/milesguo/24186.html", "20230101_1")
        self.assertTrue(result["expected_id_visible"])
        self.assertEqual(result["outbound_links"], ["https://rumble.com/v123-test.html"])
        self.assertNotIn("假视频", str(result))
        self.assertNotIn("decision", result)

    def test_invalid_utf8_is_not_silently_replaced(self):
        raw = b"<script>\xff</script>" + "<title>20230101_1</title><p>今天录一段视频。</p>".encode()
        result = m.parse_page(raw, "https://gwins.org/cn/milesguo/24186.html", "20230101_1")
        self.assertFalse(result["decoding"]["strict"])
        self.assertEqual(result["decoding"]["replacement_count"], 1)
        self.assertTrue(result["decoding"]["title_clean"])
        self.assertEqual(result["identity_type_cues"][0]["excerpt"], "今天录一段视频。")

    def test_owned_claim_and_candidate_binding(self):
        with tempfile.TemporaryDirectory() as td, patch.object(m, "ROOT", Path(td)):
            root = Path(td)
            claims = root / "coordination/claims"
            candidates = root / "data/current/source_candidates"
            claims.mkdir(parents=True); candidates.mkdir(parents=True)
            task = "C2-REVIEW-TEST-R001"
            claim = {"agent_id":"owner", "review_batch_id":"batch", "status":"in_progress", "candidate_review_contract":"candidate-review-evidence-v2", "claimed_at":datetime.now(timezone.utc).isoformat(), "source_candidate_id":"TEST"}
            (claims / (task + ".json")).write_text(json.dumps(claim))
            (candidates / "x.json").write_text(json.dumps({"id":"TEST", "metadata_json":{"detail_url":"https://gwins.org/cn/milesguo/24186.html"}}))
            self.assertEqual(m.validate_member(task, "owner", "batch")[2], "https://gwins.org/cn/milesguo/24186.html")
            with self.assertRaises(ValueError): m.validate_member(task, "other", "batch")
            with self.assertRaises(ValueError): m.validate_member("../bad", "owner", "batch")
            claim["claimed_at"] = "2000-01-01T00:00:00Z"
            (claims / (task + ".json")).write_text(json.dumps(claim))
            with self.assertRaises(ValueError): m.validate_member(task, "owner", "batch")

if __name__ == "__main__": unittest.main()
