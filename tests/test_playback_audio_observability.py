import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import process_playback_request as processor


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class PlaybackAudioObservabilityTests(unittest.TestCase):
    def test_audio_probe_and_activity_prove_non_silent_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "tone.wav"
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                "sine=frequency=440:duration=1", "-ar", "16000", "-ac", "1",
                "-c:a", "pcm_s16le", str(wav),
            ], check=True)
            probe = processor.audio_probe_summary(wav)
            activity = processor.measure_audio_activity(wav)
            self.assertEqual(probe["probe_returncode"], 0)
            self.assertTrue(probe["has_audio_stream"])
            self.assertGreater(probe["duration_sec"], 0.1)
            self.assertTrue(activity["non_silent"])
            self.assertIsNotNone(activity["max_volume_db"])

    def test_missing_wav_probe_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            probe = processor.audio_probe_summary(Path(tmp) / "missing.wav")
            self.assertNotEqual(probe["probe_returncode"], 0)
            self.assertFalse(probe["has_audio_stream"])
            self.assertIsNone(probe["duration_sec"])


if __name__ == "__main__":
    unittest.main()
