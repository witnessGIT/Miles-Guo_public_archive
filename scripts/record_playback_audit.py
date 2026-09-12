#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from playback_validation import canonical_segment_index, pilot_case_live_map

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


def durable_path_reference(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return path.name


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record one qualifying real playback timing check after audit_media.py "
            "has decoded media on both sides of the canonical timestamp and a reviewer "
            "has inspected the content."
        )
    )
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--live-id", required=True)
    parser.add_argument("--segment-id", required=True)
    parser.add_argument("--expected-start", required=True, type=float)
    parser.add_argument("--observed-position", required=True, type=float)
    parser.add_argument("--media-url", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--observation-mode", required=True, choices=["audio", "video", "both"])
    parser.add_argument("--content-observation", required=True)
    parser.add_argument("--decode-evidence-json", required=True)
    parser.add_argument(
        "--content-match",
        action="store_true",
        help="Required only after decoded content has actually been inspected and matched.",
    )
    args = parser.parse_args()

    if args.expected_start < 0 or args.observed_position < 0:
        parser.error("positions must be >= 0")
    if not args.content_match:
        parser.error(
            "--content-match is required. Do not create a qualifying playback record "
            "until decoded content has actually been inspected and matched."
        )

    segments, segment_problems = canonical_segment_index()
    if segment_problems:
        parser.error("canonical segment index is ambiguous: " + "; ".join(segment_problems[:5]))
    segment = segments.get(args.segment_id)
    if segment is None:
        parser.error(f"segment does not exist in data/live_segments: {args.segment_id}")
    if str(segment.get("live_id")) != args.live_id:
        parser.error(
            f"segment {args.segment_id} belongs to {segment.get('live_id')}, not {args.live_id}"
        )
    if segment.get("start_sec") is None:
        parser.error(f"segment has no canonical start_sec: {args.segment_id}")
    canonical_start = float(segment["start_sec"])
    if abs(canonical_start - args.expected_start) > 0.001:
        parser.error(
            f"--expected-start {args.expected_start} does not match canonical segment "
            f"start_sec {canonical_start}"
        )

    case_live, case_problems = pilot_case_live_map()
    if case_problems:
        parser.error("Pilot case/live mapping is ambiguous: " + "; ".join(case_problems[:5]))
    mapped_live = case_live.get(args.case_id)
    if mapped_live is None:
        parser.error(f"no collection/alignment mapping found for case {args.case_id}")
    if mapped_live != args.live_id:
        parser.error(f"case {args.case_id} maps to {mapped_live}, not {args.live_id}")

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
        parser.error("decode evidence does not prove successful real-media decoding")

    try:
        decode_expected = float(
            decode.get("expected_start_sec", decode.get("requested_start_sec"))
        )
        decode_start = float(decode.get("decode_start_sec", decode_expected))
        decode_window = float(decode.get("decode_window_sec"))
    except (TypeError, ValueError):
        parser.error(
            "decode evidence must contain numeric expected/requested start, decode start, "
            "and decode window"
        )
    decode_end = decode_start + decode_window

    if abs(decode_expected - args.expected_start) > 0.001:
        parser.error("decode evidence expected_start_sec does not match canonical expected start")
    if decode_start > args.expected_start + 0.001 or decode_end < args.expected_start - 0.001:
        parser.error("decoded media window does not contain the canonical expected position")
    if args.observed_position < decode_start - 0.001 or args.observed_position > decode_end + 0.001:
        parser.error(
            f"observed position {args.observed_position} is outside decoded media window "
            f"[{decode_start}, {decode_end}]"
        )
    if str(decode.get("media_source")) != args.media_url:
        parser.error("--media-url must exactly match decode evidence media_source")

    clip_hash = None
    frame_hash = None
    for key, target in (("clip_path", "clip"), ("frame_path", "frame")):
        raw = decode.get(key)
        if not raw:
            continue
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if candidate.exists():
            if target == "clip":
                clip_hash = sha256_file(candidate)
            else:
                frame_hash = sha256_file(candidate)

    signed_error = args.observed_position - args.expected_start
    record = {
        "project": "Miles-Guo_public_archive",
        "evidence_type": "qualifying_playback_timing_check_v1",
        "case_id": args.case_id,
        "live_id": args.live_id,
        "segment_id": args.segment_id,
        "expected_start_sec": args.expected_start,
        "canonical_segment_start_sec": canonical_start,
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
        # Compatibility name retained: this is the expected canonical position used to
        # request the audit, not necessarily the ffmpeg seek point.
        "decode_request_start_sec": decode_expected,
        "decode_start_sec": decode_start,
        "decode_end_sec": decode_end,
        "decode_window_sec": decode_window,
        "decode_resolver": (decode.get("resolution") or {}).get("resolver"),
        "decode_media_source": decode.get("media_source"),
        "decode_evidence_sha256": sha256_file(evidence_path),
        "clip_sha256": clip_hash,
        "frame_sha256": frame_hash,
        "decode_evidence_ref": durable_path_reference(evidence_path),
        "note": (
            "Temporary decoded media remains under cache/. The decoded window may begin "
            "before the canonical timestamp so both negative and positive timing errors can "
            "be measured. This durable record is bound to the canonical segment start."
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
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created qualifying playback check: {out_path.relative_to(ROOT)}")
    print(f"timing_error_sec={signed_error:+.3f} absolute={abs(signed_error):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
