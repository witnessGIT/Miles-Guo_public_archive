from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.cloud_asr_item import output_paths, publish


class CloudAsrOutputTests(unittest.TestCase):
    def test_publish_keeps_media_out_and_writes_timestamped_machine_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            payload = {
                "schema_version": "cloud-asr-result-v1",
                "live_id": "LIVE_20200101_001",
                "status": "transcribed",
                "source_id": "SRC_TEST",
                "media_asset_id": "MA_TEST",
                "source_url": "https://example.test/watch",
                "resolved_media_url": "https://example.test/video.mp4",
                "audio_sha256": "a" * 64,
                "audio_size_bytes": 123,
                "model": "mlx-community/whisper-large-v3-turbo",
                "software": "mlx-whisper",
                "language": "zh",
                "generated_at": "2026-10-12T00:00:00Z",
                "processing_elapsed_sec": 1.25,
                "source_attempt_errors": [],
                "processing_location": "github-hosted-macos-arm64",
                "processing_path": "/ephemeral/audio.ogg",
                "path_persistence": "ephemeral_deleted_after_job",
                "text": "测试文本",
                "segments": [
                    {"start_sec": 1.0, "end_sec": 2.5, "text": "测试文本"},
                ],
            }
            outputs = publish(repo, payload)
            paths = output_paths(repo, payload["live_id"])
            self.assertEqual(len(outputs), 4)
            self.assertFalse(any(path.suffix in {".mp4", ".ogg"} for path in repo.rglob("*")))
            manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            self.assertFalse(manifest["media_committed_to_git"])
            self.assertFalse(manifest["paid_api_used"])
            self.assertEqual(manifest["path_persistence"], "ephemeral_deleted_after_job")
            cue = json.loads(paths["cues"].read_text(encoding="utf-8").strip())
            self.assertEqual((cue["start_sec"], cue["end_sec"]), (1.0, 2.5))
            segment = json.loads(paths["segments"].read_text(encoding="utf-8").strip())
            self.assertEqual(segment["review_status"], "machine")
            self.assertEqual(segment["playback_verified"], 0)


if __name__ == "__main__":
    unittest.main()
