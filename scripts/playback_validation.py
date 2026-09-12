#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SEGMENT_ROOT = ROOT / "data" / "live_segments"
READY_ROOT = ROOT / "coordination" / "ready"


def _iter_records(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        try:
            if path.suffix.lower() == ".json":
                payload = json.loads(path.read_text(encoding="utf-8"))
                rows = payload if isinstance(payload, list) else [payload]
                for index, row in enumerate(rows, 1):
                    if isinstance(row, dict):
                        yield path, index, row
            else:
                for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    raw = raw.strip()
                    if not raw or raw.startswith("#"):
                        continue
                    row = json.loads(raw)
                    if isinstance(row, dict):
                        yield path, line_no, row
        except (OSError, json.JSONDecodeError):
            continue


def canonical_segment_index() -> tuple[dict[str, dict], list[str]]:
    index: dict[str, dict] = {}
    origins: dict[str, str] = {}
    problems: list[str] = []
    for path, row_no, row in _iter_records(SEGMENT_ROOT) or []:
        segment_id = row.get("id")
        if not segment_id:
            continue
        segment_id = str(segment_id)
        rel = str(path.relative_to(ROOT))
        if segment_id in index:
            problems.append(
                f"duplicate canonical segment id {segment_id}: "
                f"{origins[segment_id]} and {rel}:{row_no}"
            )
            continue
        index[segment_id] = row
        origins[segment_id] = f"{rel}:{row_no}"
    return index, problems


def pilot_case_live_map() -> tuple[dict[str, str], list[str]]:
    mapping: dict[str, str] = {}
    problems: list[str] = []
    for stage in ("collection", "alignment"):
        base = READY_ROOT / stage
        if not base.exists():
            continue
        for path in sorted(base.glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            case_id = row.get("case_id") or row.get("pilot_case_id") or path.stem
            live_id = row.get("live_id")
            if not case_id or not live_id:
                continue
            case_id = str(case_id)
            live_id = str(live_id)
            prior = mapping.get(case_id)
            if prior and prior != live_id:
                problems.append(
                    f"conflicting live_id for {case_id}: {prior} vs {live_id} ({path})"
                )
                continue
            mapping[case_id] = live_id
    return mapping, problems


def is_public_http_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_playback_record(
    row: dict,
    *,
    source_label: str,
    segments: dict[str, dict],
    case_live: dict[str, str],
) -> tuple[dict | None, list[str]]:
    problems: list[str] = []
    required = [
        "case_id",
        "live_id",
        "segment_id",
        "expected_start_sec",
        "observed_position_sec",
        "timing_error_sec",
        "absolute_timing_error_sec",
        "media_url",
        "reviewer",
        "observation_mode",
        "content_observation",
        "decode_request_start_sec",
        "decode_window_sec",
        "decode_media_source",
    ]
    missing = [key for key in required if row.get(key) is None or row.get(key) == ""]
    if missing:
        problems.append(f"{source_label}: missing required fields: {', '.join(missing)}")
        return None, problems

    if row.get("evidence_type") != "qualifying_playback_timing_check_v1":
        problems.append(f"{source_label}: unsupported evidence_type")
    if row.get("playback_decode_verified") is not True:
        problems.append(f"{source_label}: playback_decode_verified is not true")
    if row.get("content_timing_verified") is not True or row.get("content_match") is not True:
        problems.append(f"{source_label}: content timing/content match not verified")
    if row.get("observation_mode") not in {"audio", "video", "both"}:
        problems.append(f"{source_label}: invalid observation_mode")
    if not is_public_http_url(row.get("media_url")):
        problems.append(f"{source_label}: media_url is not a public http(s) URL")

    segment_id = str(row.get("segment_id"))
    live_id = str(row.get("live_id"))
    case_id = str(row.get("case_id"))
    segment = segments.get(segment_id)
    if segment is None:
        problems.append(f"{source_label}: segment_id not found in canonical live_segments: {segment_id}")
    else:
        canonical_live = str(segment.get("live_id") or "")
        if canonical_live != live_id:
            problems.append(
                f"{source_label}: live_id {live_id} does not match canonical segment live_id {canonical_live}"
            )
        if segment.get("start_sec") is None:
            problems.append(f"{source_label}: canonical segment has no start_sec")

    mapped_live = case_live.get(case_id)
    if mapped_live is None:
        problems.append(f"{source_label}: no collection/alignment live mapping for case {case_id}")
    elif mapped_live != live_id:
        problems.append(
            f"{source_label}: case {case_id} maps to {mapped_live}, not playback record live_id {live_id}"
        )

    try:
        expected = float(row["expected_start_sec"])
        observed = float(row["observed_position_sec"])
        signed = float(row["timing_error_sec"])
        absolute = float(row["absolute_timing_error_sec"])
        decode_expected = float(row["decode_request_start_sec"])
        decode_window = float(row["decode_window_sec"])
        decode_start = float(row.get("decode_start_sec", decode_expected))
    except (TypeError, ValueError):
        problems.append(f"{source_label}: non-numeric timing field")
        return None, problems

    decode_end = decode_start + decode_window
    if expected < 0 or observed < 0 or decode_start < 0 or decode_window <= 0:
        problems.append(f"{source_label}: invalid media position/window")
    recomputed = observed - expected
    if abs(recomputed - signed) > 0.001:
        problems.append(f"{source_label}: timing_error_sec inconsistent with observed-expected")
    if abs(abs(signed) - absolute) > 0.001:
        problems.append(f"{source_label}: absolute_timing_error_sec inconsistent")
    if abs(decode_expected - expected) > 0.001:
        problems.append(
            f"{source_label}: decode_request_start_sec does not match expected_start_sec"
        )
    if decode_start > expected + 0.001 or decode_end < expected - 0.001:
        problems.append(f"{source_label}: decoded window does not contain expected_start_sec")
    if observed < decode_start - 0.001 or observed > decode_end + 0.001:
        problems.append(f"{source_label}: observed position lies outside decoded media window")
    if str(row.get("decode_media_source")) != str(row.get("media_url")):
        problems.append(f"{source_label}: decode_media_source does not match media_url")

    if segment is not None and segment.get("start_sec") is not None:
        canonical_start = float(segment["start_sec"])
        if abs(canonical_start - expected) > 0.001:
            problems.append(
                f"{source_label}: expected_start_sec {expected} does not match canonical "
                f"segment start_sec {canonical_start}"
            )

    if problems:
        return None, problems
    return {**row, "_canonical_segment": segment}, problems
