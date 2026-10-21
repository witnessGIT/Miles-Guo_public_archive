from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cloud_asr_item import (
    CHUNK_DURATION_SEC,
    MODEL,
    assess_transcript_quality,
    output_paths,
    publish,
    sha256_file,
    transcribe_chunked,
)


class CloudAsrOutputTests(unittest.TestCase):
    def test_quality_gate_accepts_dense_continuous_machine_dictation(self) -> None:
        segments = [
            {
                "start_sec": index * 30.0,
                "end_sec": (index + 1) * 30.0,
                "text": f"这是第{index}段内容，讨论不同事实并保留自然语言信息。",
                "avg_logprob": -0.35,
                "no_speech_prob": 0.02,
                "compression_ratio": 1.2,
            }
            for index in range(20)
        ]
        quality = assess_transcript_quality(segments, 600.0)
        self.assertEqual(quality["gate_status"], "pass")
        self.assertEqual(quality["reasons"], [])

    def test_quality_gate_defers_sparse_or_truncated_dictation(self) -> None:
        quality = assess_transcript_quality([
            {"start_sec": 0.0, "end_sec": 8.0, "text": "短句"},
        ], 1200.0)
        self.assertEqual(quality["gate_status"], "deferred_review")
        self.assertIn("transcript_too_sparse_for_audio_duration", quality["reasons"])
        self.assertIn("transcript_ends_too_early_for_audio_duration", quality["reasons"])

    def test_quality_gate_defers_repetition_and_low_confidence_dictation(self) -> None:
        segments = [
            {
                "start_sec": index * 10.0,
                "end_sec": (index + 1) * 10.0,
                "text": "感谢观看请订阅这个频道并打开通知",
                "avg_logprob": -1.8,
                "no_speech_prob": 0.9,
                "compression_ratio": 3.0,
            }
            for index in range(20)
        ]
        quality = assess_transcript_quality(segments, 200.0)
        self.assertIn("probable_repetition_or_hallucination", quality["reasons"])
        self.assertIn("predominantly_low_confidence_dictation", quality["reasons"])
        self.assertIn("probable_speech_transcribed_from_non_speech", quality["reasons"])
        self.assertIn("probable_compressed_repetitive_dictation", quality["reasons"])

    def test_quality_gate_defers_invalid_timestamps(self) -> None:
        quality = assess_transcript_quality([
            {"start_sec": 12.0, "end_sec": 3.0, "text": "时间码不合法但文本长度足够用于检查"},
        ], 30.0)
        self.assertIn("invalid_or_out_of_bounds_timestamps", quality["reasons"])

    def test_chunked_transcription_offsets_timestamps(self) -> None:
        class FakeWhisper:
            calls = 0

            @classmethod
            def transcribe(cls, _path: str, **_kwargs: object) -> dict[str, object]:
                cls.calls += 1
                return {
                    "text": f"chunk {cls.calls}",
                    "language": "zh",
                    "segments": [{
                        "start": 1.0,
                        "end": 2.5,
                        "text": f"part {cls.calls}",
                        "avg_logprob": -0.4,
                        "no_speech_prob": 0.01,
                        "compression_ratio": 1.1,
                    }],
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
            self.assertEqual(segments[0]["avg_logprob"], -0.4)
            self.assertFalse(any(chunk_root.glob("chunk_*.wav")))

    def test_chunked_transcription_resumes_structured_checkpoints(self) -> None:
        class FakeWhisper:
            calls = 0

            @classmethod
            def transcribe(cls, _path: str, **_kwargs: object) -> dict[str, object]:
                cls.calls += 1
                return {
                    "text": "new chunk",
                    "language": "zh",
                    "segments": [{"start": 2.0, "end": 3.0, "text": "new part"}],
                }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audio = root / "audio.ogg"
            audio.touch()
            chunk_root = root / "chunks"
            checkpoints = root / "checkpoints"
            checkpoints.mkdir()
            saved_chunk = root / "saved_chunk.wav"
            saved_chunk.write_bytes(b"stable decoded pcm")
            (checkpoints / "chunk_0000.json").write_text(json.dumps({
                "schema_version": "cloud-asr-chunk-v1",
                "live_id": "LIVE_20200101_001",
                "chunk_index": 0,
                "offset_sec": 0,
                "chunk_audio_sha256": sha256_file(saved_chunk),
                "model": MODEL,
                "language": "zh",
                "text": "saved chunk",
                "segments": [{"start": 1.0, "end": 1.5, "text": "saved part"}],
            }), encoding="utf-8")

            def fake_ffmpeg(*_args: object, **_kwargs: object) -> None:
                chunk_root.mkdir(parents=True, exist_ok=True)
                (chunk_root / "chunk_0000.wav").write_bytes(b"stable decoded pcm")
                (chunk_root / "chunk_0001.wav").write_bytes(b"new decoded pcm")

            with patch("scripts.cloud_asr_item.subprocess.run", side_effect=fake_ffmpeg):
                result = transcribe_chunked(
                    audio, chunk_root, FakeWhisper, checkpoints, "LIVE_20200101_001",
                )

            self.assertEqual(FakeWhisper.calls, 1)
            self.assertEqual(result["resumed_chunk_count"], 1)
            self.assertEqual(result["text"], "saved chunk new chunk")
            self.assertEqual(result["segments"][1]["start"], CHUNK_DURATION_SEC + 2.0)
            written = json.loads((checkpoints / "chunk_0001.json").read_text(encoding="utf-8"))
            self.assertFalse(written["media_committed_to_git"])

    def test_chunked_transcription_recomputes_changed_audio_checkpoint(self) -> None:
        class FakeWhisper:
            calls = 0

            @classmethod
            def transcribe(cls, _path: str, **_kwargs: object) -> dict[str, object]:
                cls.calls += 1
                return {
                    "text": "replacement chunk",
                    "language": "zh",
                    "segments": [{"start": 1.0, "end": 2.0, "text": "replacement part"}],
                }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audio = root / "audio.ogg"
            audio.touch()
            chunk_root = root / "chunks"
            checkpoints = root / "checkpoints"
            checkpoints.mkdir()
            (checkpoints / "chunk_0000.json").write_text(json.dumps({
                "schema_version": "cloud-asr-chunk-v1",
                "live_id": "LIVE_20200101_001",
                "chunk_index": 0,
                "offset_sec": 0,
                "chunk_audio_sha256": "0" * 64,
                "model": MODEL,
                "language": "zh",
                "text": "stale chunk",
                "segments": [{"start": 1.0, "end": 1.5, "text": "stale part"}],
            }), encoding="utf-8")

            def fake_ffmpeg(*_args: object, **_kwargs: object) -> None:
                chunk_root.mkdir(parents=True, exist_ok=True)
                (chunk_root / "chunk_0000.wav").write_bytes(b"changed decoded pcm")

            with patch("scripts.cloud_asr_item.subprocess.run", side_effect=fake_ffmpeg):
                result = transcribe_chunked(
                    audio, chunk_root, FakeWhisper, checkpoints, "LIVE_20200101_001",
                )

            self.assertEqual(FakeWhisper.calls, 1)
            self.assertEqual(result["resumed_chunk_count"], 0)
            self.assertEqual(result["text"], "replacement chunk")
            written = json.loads((checkpoints / "chunk_0000.json").read_text(encoding="utf-8"))
            self.assertEqual(
                written["chunk_audio_sha256"],
                hashlib.sha256(b"changed decoded pcm").hexdigest(),
            )

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
                "audio_duration_sec": 3.0,
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
                "quality": {
                    "schema_version": "cloud-asr-quality-v1",
                    "gate_status": "pass",
                    "quality_score": 0.91,
                    "reasons": [],
                    "warnings": [],
                    "metrics": {},
                },
            }
            outputs = publish(repo, payload)
            paths = output_paths(repo, payload["live_id"])
            self.assertEqual(len(outputs), 4)
            self.assertFalse(any(path.suffix in {".mp4", ".ogg"} for path in repo.rglob("*")))
            manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            self.assertFalse(manifest["media_committed_to_git"])
            self.assertFalse(manifest["paid_api_used"])
            self.assertEqual(manifest["path_persistence"], "ephemeral_deleted_after_job")
            self.assertEqual(manifest["quality"]["gate_status"], "pass")
            self.assertEqual(manifest["audio_duration_sec"], 3.0)
            cue = json.loads(paths["cues"].read_text(encoding="utf-8").strip())
            self.assertEqual((cue["start_sec"], cue["end_sec"]), (1.0, 2.5))
            segment = json.loads(paths["segments"].read_text(encoding="utf-8").strip())
            self.assertEqual(segment["review_status"], "machine")
            self.assertEqual(segment["playback_verified"], 0)


if __name__ == "__main__":
    unittest.main()
