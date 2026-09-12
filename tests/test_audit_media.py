import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "audit_media.py"


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class AuditMediaSmokeTest(unittest.TestCase):
    def test_synthetic_media_is_really_decoded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "input.mp4"
            output_dir = tmp_path / "audit"

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=320x240:rate=25",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440",
                    "-t",
                    "5",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    str(source),
                ],
                check=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_SCRIPT),
                    "--media",
                    str(source),
                    "--start",
                    "2",
                    "--window",
                    "1",
                    "--output-dir",
                    str(output_dir),
                    "--label",
                    "synthetic",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["playback_decode_verified"])
            self.assertFalse(payload["content_timing_verified"])
            self.assertTrue(Path(payload["clip_path"]).exists())
            self.assertTrue(Path(payload["frame_path"]).exists())


if __name__ == "__main__":
    unittest.main()
