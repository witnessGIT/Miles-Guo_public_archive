#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import process_playback_request as playback


def main():
    frames = [{
        "local_sec": 10.0,
        "absolute_sec": 158.0,
        "sha256": "abc",
        "ocr_text": "noise line\n是否同意安德森博士当时的评估\n你是否同意安德森 时的",
    }]
    match = playback.best_ocr_match(
        frames,
        "GREENE：雷德菲尔德博士，你是否同意安德森博士当时的评估？",
        "GREENE 雷德菲尔德 安德森 病毒",
    )
    assert match is not None
    assert match["score"] >= playback.MIN_AGENT_REVIEW_SCORE, match
    assert match["absolute_sec"] == 158.0

    noise = playback.best_ocr_match(
        [{"local_sec": 10.0, "absolute_sec": 158.0, "sha256": "def", "ocr_text": "June 2019 random screen"}],
        "GREENE：雷德菲尔德博士，你是否同意安德森博士当时的评估？",
        "GREENE 雷德菲尔德 安德森 病毒",
    )
    assert noise is None or noise["score"] < playback.MIN_AGENT_REVIEW_SCORE, noise
    print("visual match regression: PASS")


if __name__ == "__main__":
    main()
