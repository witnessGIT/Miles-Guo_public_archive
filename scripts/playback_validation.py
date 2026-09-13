#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SEGMENT_ROOT = ROOT / "data" / "live_segments"
READY_ROOT = ROOT / "coordination" / "ready"
EVIDENCE_ROOT = ROOT / "data" / "playback_evidence"

MANUAL_EVIDENCE = "qualifying_playback_timing_check_v1"
REPOSITORY_EVIDENCE = "qualifying_playback_timing_check_v2"
SUPPORTED_EVIDENCE = {MANUAL_EVIDENCE, REPOSITORY_EVIDENCE}


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


def _safe_evidence_path(raw: object) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    try:
        resolved = path.resolve()
        root = EVIDENCE_ROOT.resolve()
    except OSError:
        return None
    if resolved != root and root not in resolved.parents:
        return None
    return resolved


def _validate_repository_evidence(row: dict, source_label: str) -> list[str]:
    problems: list[str] = []
    if row.get("inspection_method") != "repository_decoded_evidence_service_v1":
        problems.append(f"{source_label}: invalid repository inspection_method")
    if row.get("agent_evidence_acceptance") is not True:
        problems.append(f"{source_label}: repository evidence lacks explicit Agent acceptance")
    path = _safe_evidence_path(row.get("repository_evidence_ref"))
    if path is None:
        problems.append(f"{source_label}: invalid repository_evidence_ref")
        return problems
    if not path.exists():
        problems.append(f"{source_label}: repository evidence file does not exist")
        return problems
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"{source_label}: invalid repository evidence JSON: {exc}")
        return problems
    if not isinstance(evidence, dict):
        problems.append(f"{source_label}: repository evidence top level must be an object")
        return problems
    if evidence.get("evidence_version") != "repository-playback-evidence-v1":
        problems.append(f"{source_label}: unsupported repository evidence version")
    if evidence.get("status") != "ready_for_agent_review":
        problems.append(f"{source_label}: repository evidence is not ready_for_agent_review")
    if evidence.get("playback_decode_verified") is not True:
        problems.append(f"{source_label}: repository evidence does not prove media decoding")
    if evidence.get("repository_content_inspection") is not True:
        problems.append(f"{source_label}: repository evidence inspection did not run")
    if evidence.get("candidate_content_match") is not True:
        problems.append(f"{source_label}: repository evidence candidate did not match content")
    if str(evidence.get("bundle_id") or "") != str(row.get("repository_evidence_bundle_id") or ""):
        problems.append(f"{source_label}: repository evidence bundle_id mismatch")
    for key in ("case_id", "live_id", "segment_id", "media_url"):
        if str(evidence.get(key) or "") != str(row.get(key) or ""):
            problems.append(f"{source_label}: repository evidence {key} mismatch")
    try:
        e_expected = float(evidence["expected_start_sec"])
        e_observed = float(evidence["candidate_observed_position_sec"])
        e_decode_start = float(evidence["decode_start_sec"])
        e_decode_window = float(evidence["decode_window_sec"])
        r_expected = float(row["expected_start_sec"])
        r_observed = float(row["observed_position_sec"])
        r_decode_start = float(row.get("decode_start_sec", row["decode_request_start_sec"]))
        r_decode_window = float(row["decode_window_sec"])
        minimum = float(evidence.get("minimum_agent_review_score") or 1.0)
    except (KeyError, TypeError, ValueError):
        problems.append(f"{source_label}: repository evidence contains non-numeric timing/score fields")
        return problems
    if abs(e_expected - r_expected) > 0.001:
        problems.append(f"{source_label}: repository evidence expected position mismatch")
    if abs(e_observed - r_observed) > 0.001:
        problems.append(f"{source_label}: repository evidence observed position mismatch")
    if abs(e_decode_start - r_decode_start) > 0.001 or abs(e_decode_window - r_decode_window) > 0.001:
        problems.append(f"{source_label}: repository evidence decode window mismatch")

    match_method = str(evidence.get("candidate_match_method") or "audio_asr")
    if match_method == "audio_asr":
        match = (evidence.get("audio_asr") or {}).get("best_match") or {}
    elif match_method == "frame_ocr":
        match = (evidence.get("visual_evidence") or {}).get("best_match") or {}
    else:
        problems.append(f"{source_label}: unsupported repository candidate_match_method {match_method!r}")
        match = {}
    try:
        score = float(evidence.get("candidate_match_score") or match.get("score") or 0.0)
    except (TypeError, ValueError):
        problems.append(f"{source_label}: invalid repository candidate match score")
        score = 0.0
    if score < minimum:
        problems.append(
            f"{source_label}: repository evidence {match_method} score below review threshold"
        )
    row_method = str(row.get("repository_candidate_match_method") or "audio_asr")
    if row_method != match_method:
        problems.append(f"{source_label}: repository_candidate_match_method mismatch")
    try:
        row_score = float(row.get("repository_candidate_match_score", row.get("repository_asr_match_score")))
    except (TypeError, ValueError):
        problems.append(f"{source_label}: invalid repository_candidate_match_score")
    else:
        if abs(row_score - score) > 0.000001:
            problems.append(f"{source_label}: repository_candidate_match_score mismatch")

    # Preserve separate ASR/OCR diagnostics when present, but only the selected candidate method
    # is required to clear the review threshold.
    if row.get("repository_asr_match_score") is not None:
        try:
            row_asr = float(row.get("repository_asr_match_score"))
            evidence_asr = float(((evidence.get("audio_asr") or {}).get("best_match") or {}).get("score") or 0.0)
        except (TypeError, ValueError):
            problems.append(f"{source_label}: invalid repository_asr_match_score")
        else:
            if abs(row_asr - evidence_asr) > 0.000001:
                problems.append(f"{source_label}: repository_asr_match_score mismatch")
    if row.get("repository_ocr_match_score") is not None:
        try:
            row_ocr = float(row.get("repository_ocr_match_score"))
            evidence_ocr = float(((evidence.get("visual_evidence") or {}).get("best_match") or {}).get("score") or 0.0)
        except (TypeError, ValueError):
            problems.append(f"{source_label}: invalid repository_ocr_match_score")
        else:
            if abs(row_ocr - evidence_ocr) > 0.000001:
                problems.append(f"{source_label}: repository_ocr_match_score mismatch")
    return problems


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

    evidence_type = row.get("evidence_type")
    if evidence_type not in SUPPORTED_EVIDENCE:
        problems.append(f"{source_label}: unsupported evidence_type")
    if row.get("playback_decode_verified") is not True:
        problems.append(f"{source_label}: playback_decode_verified is not true")
    if row.get("content_timing_verified") is not True or row.get("content_match") is not True:
        problems.append(f"{source_label}: content timing/content match not verified")
    if row.get("observation_mode") not in {"audio", "video", "visual", "both"}:
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

    if evidence_type == REPOSITORY_EVIDENCE:
        problems.extend(_validate_repository_evidence(row, source_label))

    if problems:
        return None, problems
    return {**row, "_canonical_segment": segment}, problems
