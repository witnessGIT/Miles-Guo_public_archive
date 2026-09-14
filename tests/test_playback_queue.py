import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import playback_queue as queue  # noqa: E402
import playback_service_state as state  # noqa: E402


class PlaybackQueueGenerationTest(unittest.TestCase):
    def setUp(self):
        self.originals = (queue.CLAIMS, queue.REQUEST_ROOT)
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        queue.CLAIMS = root / "coordination" / "claims"
        queue.REQUEST_ROOT = root / "coordination" / "playback_requests"

    def tearDown(self):
        queue.CLAIMS, queue.REQUEST_ROOT = self.originals
        self.tmp.cleanup()

    def test_new_claim_and_request_enter_active_service_generation(self):
        chosen = {
            "task_id": "P9-PLAYBACK-PILOT-X",
            "case_id": "PILOT-X",
            "live_id": "LIVE-X",
            "missing_segment_ids": ["SEG-1"],
        }
        tools = {
            "ffmpeg": False,
            "ffprobe": False,
            "yt_dlp": False,
            "repository_evidence_service": True,
        }
        with patch.object(queue, "choose_case", return_value=chosen), patch.object(
            queue, "capability_status", return_value=tools
        ):
            claim_path = queue.claim_case("agent-test", "PILOT-X", False)

        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        self.assertEqual(claim["queue_generation"], state.ACTIVE_QUEUE_GENERATION)

        request_path = queue.request_segment(
            "agent-test",
            "PILOT-X",
            "SEG-1",
            "https://example.invalid/public-media",
            "frames_ocr",
        )
        request = json.loads(request_path.read_text(encoding="utf-8"))
        self.assertEqual(request["queue_generation"], state.ACTIVE_QUEUE_GENERATION)
        self.assertEqual(request["request_revision"], 1)

        state_originals = (state.REQUEST_ROOT, state.CLAIM_ROOT, state.EVIDENCE_ROOT)
        try:
            state.REQUEST_ROOT = queue.REQUEST_ROOT
            state.CLAIM_ROOT = queue.CLAIMS
            state.EVIDENCE_ROOT = Path(self.tmp.name) / "data" / "playback_evidence"
            pending, problems = state.pending_requests(prepare_retries=False)
        finally:
            state.REQUEST_ROOT, state.CLAIM_ROOT, state.EVIDENCE_ROOT = state_originals

        self.assertEqual(pending, [request_path])
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
