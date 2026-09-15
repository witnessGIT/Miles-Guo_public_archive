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
    def test_ytdlp_resolution_requests_muxed_audio_video(self, run_mock, _which):
        run_mock.return_value = (0, "https://cdn.example/muxed.mp4\n", "")
        resolved, meta = audit_media.resolve_media("https://gettr.com/post/example")
        self.assertEqual("https://cdn.example/muxed.mp4", resolved)
        command = run_mock.call_args.args[0]
        self.assertIn("-f", command)
        selector = command[command.index("-f") + 1]
        self.assertIn("acodec!=none", selector)
        self.assertIn("vcodec!=none", selector)
        self.assertEqual("yt-dlp", meta["resolver"])


if __name__ == "__main__":
    unittest.main()
