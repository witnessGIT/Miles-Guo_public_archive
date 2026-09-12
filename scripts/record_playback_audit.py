#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "data" / "playback_audits"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record one qualifying real playback timing check after audit_media.py "
            "has decoded the media and a reviewer has inspected the content."
        )
    )
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--live-id", required=True)
    parser.add_argument("--segment-id", required=True)
    parser.add_argument("--expected-start", required=True, type=float)
    parser.add_argument("--observed-position", required=True, type=float)
    parser.add_argument("--media-url", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument(
        "--observation-mode",
        required=True,
        choices=["audio", "video", "both"],
    )
    parser.add_argument(
        "--content-observation",
        required=True,
        help="Concise description of the phrase/event actually observed in decoded media.",
    )
    parser.add_argument(
        "--decode-evidence-json",
        required=True,
        help="JSON emitted by scripts/audit_media.py under cache/audit_media/.",
    )
    parser.add_argument(
        "--content-match",
        action="store_true",
        help="Required for a qualifying check; assert only after inspecting decoded content.",
    )
    args = parser.parse_args()

    if args.expected_start < 0 or args.observed_position < 0:
        parser.error("positions must be >= 0")
    if not args.content_match:
        parser.error(
            "--content-match is required. Do not create a qualifying playback record "
            "until decoded content has actually been inspected and matched."
        )

    evidence_path = Path(args.decode_evidence_json)
    if not evidence_path.is_absolute():
        evidence_path = ROOT / evidence_path
    if not evidence_path.exists():
        parser.error(f"decode evidence JSON not found: {evidence_path}")

    try:
        decode = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"invalid decode evidence JSON: {exc}")

    if not decode.get("ok") or not decode.get("playback_decode_verified"):
        parser.error(
            "decode evidence does not prove successful real-media decoding; "
            "run scripts/audit_media.py first"
        )

    clip_hash = None
    frame_hash = None
    clip_path = decode.get("clip_path")
    frame_path = decode.get("frame_path")
    if clip_path:
        candidate = Path(clip_path)
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if candidate.exists():
            clip_hash = sha256_file(candidate)
    if frame_path:
        candidate = Path(frame_path)
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if candidate.exists():
            frame_hash = sha256_file(candidate)

    signed_error = args.observed_position - args.expected_start
    record = {
        "project": "Miles-Guo_public_archive",
        "evidence_type": "qualifying_playback_timing_check_v1",
        "case_id": args.case_id,
        "live_id": args.live_id,
        "segment_id": args.segment_id,
        "expected_start_sec": args.expected_start,
        "observed_position_sec": args.observed_position,
        "timing_error_sec": signed_error,
        "absolute_timing_error_sec": abs(signed_error),
        "media_url": args.media_url,
        "observation_mode": args.observation_mode,
        "content_match": True,
        "content_observation": args.content_observation,
        "playback_decode_verified": True,
        "content_timing_verified": True,
        "reviewer": args.reviewer,
        "reviewed_at": utc_now(),
        "decode_request_start_sec": decode.get("requested_start_sec"),
        "decode_window_sec": decode.get("decode_window_sec"),
        "decode_resolver": (decode.get("resolution") or {}).get("resolver"),
        "decode_media_source": decode.get("media_source"),
        "clip_sha256": clip_hash,
        "frame_sha256": frame_hash,
        "decode_evidence_json_local": str(evidence_path),
        "note": (
            "The media/clip itself remains temporary under cache/. This durable record "
            "stores the source, observed position, timing error and hashes where available."
        ),
    }

    out_dir = OUTPUT_ROOT / args.case_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.segment_id}.json"
    if out_path.exists():
        raise SystemExit(
            f"Playback record already exists: {out_path.relative_to(ROOT)}. "
            "Do not silently overwrite historical audit evidence."
        )

    out_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Created qualifying playback check: {out_path.relative_to(ROOT)}")
    print(f"timing_error_sec={signed_error:+.3f} absolute={abs(signed_error):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
