import unittest
from unittest import mock

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_media


class PlaybackAsrMediaSelectionTests(unittest.TestCase):
    def test_decoded_clip_without_audio_is_not_asr_usable(self):
        probe = {
            "streams": [{"index": 0, "codec_type": "video", "codec_name": "h264"}],
            "format": {"duration": "24.0"},
        }
        ok, problem = audit_media._decoded_clip_is_asr_usable(probe)
        self.assertFalse(ok)
        self.assertIn("audio", problem)

    def test_decoded_clip_with_audio_is_asr_usable(self):
        probe = {
            "streams": [
                {"index": 0, "codec_type": "video", "codec_name": "h264"},
                {"index": 1, "codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {"duration": "24.0"},
        }
        ok, problem = audit_media._decoded_clip_is_asr_usable(probe)
        self.assertTrue(ok)
        self.assertEqual("", problem)

    @mock.patch("audit_media.shutil.which", return_value="/usr/local/bin/yt-dlp")
    @mock.patch("audit_media.run")
    def test_ytdlp_resolution_preserves_separate_video_and_audio_inputs(self, run_mock, _which):
        run_mock.return_value = (
            0,
            "https://cdn.example/video.mp4\nhttps://cdn.example/audio.m4a\n",
            "",
        )
        resolved, meta = audit_media.resolve_media("https://gettr.com/post/example")
        self.assertEqual("https://cdn.example/video.mp4", resolved)
        command = run_mock.call_args.args[0]
        self.assertIn("-f", command)
        selector = command[command.index("-f") + 1]
        self.assertEqual("bestvideo+bestaudio/best", selector)
        self.assertEqual("yt-dlp", meta["resolver"])
        self.assertTrue(meta["separate_audio_input"])
        self.assertEqual(
            ["https://cdn.example/video.mp4", "https://cdn.example/audio.m4a"],
            meta["_resolved_inputs"],
        )


if __name__ == "__main__":
    unittest.main()
