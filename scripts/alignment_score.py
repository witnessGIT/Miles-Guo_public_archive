#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import unicodedata
from pathlib import Path


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return "".join(ch for ch in text if unicodedata.category(ch)[0] in {"L", "N"})


def char_similarity(left: str, right: str) -> float:
    left_n = normalize_text(left)
    right_n = normalize_text(right)
    if not left_n and not right_n:
        return 1.0
    if not left_n or not right_n:
        return 0.0
    return difflib.SequenceMatcher(None, left_n, right_n, autojunk=False).ratio()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce Pilot curated-text/ASR alignment similarity scores.")
    parser.add_argument("cases", type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise SystemExit("cases file must contain a JSON list")

    failed = 0
    for case in cases:
        score = char_similarity(case["text_curated"], case["text_asr"])
        expected = case.get("expected_score")
        print(f"{case['id']}\t{score:.6f}")
        if expected is not None and abs(score - float(expected)) > args.tolerance:
            failed += 1
            print(f"  expected {expected:.6f}, delta={abs(score-float(expected)):.6g}")

    if failed:
        raise SystemExit(f"{failed} alignment score case(s) failed")


if __name__ == "__main__":
    main()
