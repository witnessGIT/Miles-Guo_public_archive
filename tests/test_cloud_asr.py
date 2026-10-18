from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cloud_asr_item import CHUNK_DURATION_SEC, output_paths, publish, transcribe_chunked


class CloudAsrOutputTests(unittest.TestCase):
    def test_chunked_transcription_offsets_timestamps(self) -> None:
        class FakeWhisper:
            calls = 0

            @classmethod
            def transcribe(cls, _path: str, **_kwargs: object) -> dict[str, object]:
                cls.calls += 1
                return {
                    "text": f"chunk {cls.calls}",
                    "language": "zh",
                    "segments": [{"start": 1.0, "end": 2.5, "text": f"part {cls.calls}"}],
                }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audio = root / "audio.ogg"
            audio.touch()
            chunk_root = root / "chunks"

            def fake_ffmpeg(*_args: object, **_kwargs: object) -> None:
                chunk_root.mkdir(parents=True, exist_ok=True)
                (chunk_root / "chunk_0000.wav").touch()
                (chunk_root / "chunk_0001.wav").touch()

            with patch("scripts.cloud_asr_item.subprocess.run", side_effect=fake_ffmpeg):
                result = transcribe_chunked(audio, chunk_root, FakeWhisper)

            self.assertEqual(result["chunk_count"], 2)
            self.assertEqual(result["text"], "chunk 1 chunk 2")
            segments = result["segments"]
            self.assertEqual(segments[0]["start"], 1.0)
            self.assertEqual(segments[1]["start"], CHUNK_DURATION_SEC + 1.0)
            self.assertFalse(any(chunk_root.glob("chunk_*.wav")))

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
