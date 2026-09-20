import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.process_source_fetch_request as service


class SourceFetchServiceTests(unittest.TestCase):
    def test_parse_gwins_page_extracts_complete_title_records(self):
        raw = b'''<html><body>
        <a href="/cn/milesguo/24188.html" class="title">\xe9\x83\xad\xe6\x96\x87\xe8\xb4\xb52023\xe5\xb9\xb41\xe6\x9c\x884\xe6\x97\xa5\xe7\x9b\xb4\xe6\x92\xad 20230104_1 title</a>
        <a href="list_2_2.html">next</a>
        </body></html>'''
        parsed = service.parse_gwins_page(raw, "https://www.gwins.org/cn/milesguo/list_2_3.html")
        self.assertEqual(len(parsed["items"]), 1)
        self.assertEqual(parsed["items"][0]["source_video_id"], "20230104_1")
        self.assertEqual(parsed["items"][0]["candidate_date"], "2023-01-04")
        self.assertEqual(parsed["items"][0]["detail_id"], "24188")
        self.assertIn("https://www.gwins.org/cn/milesguo/list_2_2.html", parsed["pagination_urls"])

    def test_url_allowlist_rejects_credentials_ports_and_other_hosts(self):
        for value in (
            "http://www.gwins.org/cn/milesguo/list_2_3.html",
            "https://user@www.gwins.org/cn/milesguo/list_2_3.html",
            "https://www.gwins.org:443/cn/milesguo/list_2_3.html",
            "https://example.com/cn/milesguo/list_2_3.html",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                service.validate_url(value)

    def test_request_hash_is_canonical(self):
        left = {"b": 2, "a": 1}
        right = {"a": 1, "b": 2}
        self.assertEqual(service.request_sha256(left), service.request_sha256(right))

    def test_request_requires_active_owned_claim(self):
        request = {
            "request_version": service.REQUEST_VERSION,
            "task_id": "C1-GWINS-list_2_3",
            "agent_id": "agent-test",
            "source_site": "gwins",
            "source_page_id": "list_2_3",
            "source_url": "https://www.gwins.org/cn/milesguo/list_2_3.html",
            "requested_at": "2026-09-21T00:00:00Z",
        }
        with tempfile.TemporaryDirectory(dir=service.REQUEST_ROOT) as temp_dir:
            path = Path(temp_dir) / "request.json"
            path.write_text(json.dumps(request), encoding="utf-8")
            claim = {"task_id": request["task_id"], "agent_id": request["agent_id"], "status": "in_progress"}
            with mock.patch.object(Path, "exists", return_value=True), mock.patch.object(
                Path, "read_text", side_effect=[path.read_text(encoding="utf-8"), json.dumps(claim)]
            ):
                loaded, claim_status = service.load_and_validate_request(path)
            self.assertEqual(loaded["agent_id"], "agent-test")
            self.assertEqual(claim_status, "in_progress")

    def test_claimed_status_is_fetchable(self):
        request = {
            "task_id": "T", "agent_id": "A", "source_site": "gwins", "source_page_id": "list_2_2",
            "source_url": "https://www.gwins.org/cn/milesguo/list_2_2.html",
        }
        with mock.patch.object(service, "load_and_validate_request", return_value=(request, "claimed")), mock.patch.object(
            service, "request_sha256", return_value="request-sha"
        ), mock.patch.object(service, "fetch_page", return_value=(b"raw", "https://www.gwins.org/cn/milesguo/list_2_2.html", 200, "text/html")), mock.patch.object(
            service, "parse_gwins_page", return_value={"items": [{"title": "x"}], "pagination_urls": []}
        ):
            with tempfile.TemporaryDirectory(dir=service.ROOT) as temp_dir:
                with mock.patch.object(service, "EVIDENCE_ROOT", Path(temp_dir)):
                    output = service.process_request(Path("ignored.json"))
                    self.assertTrue(output.exists())

    def test_completed_request_with_matching_evidence_is_skipped(self):
        request = {"task_id": "T", "agent_id": "A", "source_site": "gwins", "source_page_id": "list_2_3"}
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_dir = Path(temp_dir) / "gwins" / "list_2_3"
            evidence_dir.mkdir(parents=True)
            evidence_path = evidence_dir / "evidence.json"
            evidence_path.write_text(json.dumps({"request_sha256": "request-sha"}), encoding="utf-8")
            with mock.patch.object(service, "load_and_validate_request", return_value=(request, "completed")), mock.patch.object(
                service, "request_sha256", return_value="request-sha"
            ), mock.patch.object(service, "EVIDENCE_ROOT", Path(temp_dir)), mock.patch.object(service, "fetch_page") as fetch:
                self.assertEqual(service.process_request(Path("ignored.json")), evidence_path)
                fetch.assert_not_called()

    def test_completed_request_cannot_fetch_new_evidence(self):
        request = {"task_id": "T", "agent_id": "A", "source_site": "gwins", "source_page_id": "list_2_3"}
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            service, "load_and_validate_request", return_value=(request, "completed")
        ), mock.patch.object(service, "EVIDENCE_ROOT", Path(temp_dir)), self.assertRaisesRegex(ValueError, "no matching"):
            service.process_request(Path("ignored.json"))


if __name__ == "__main__":
    unittest.main()
