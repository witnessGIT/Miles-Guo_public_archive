#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from playback_validation import canonical_segment_index, pilot_case_live_map

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "coordination" / "claims"
ACCEPTANCE_ROOT = ROOT / "coordination" / "playback_acceptances"
EVIDENCE_ROOT = ROOT / "data" / "playback_evidence"
OUTPUT_ROOT = ROOT / "data" / "playback_audits"

ACCEPTANCE_VERSION = "playback-acceptance-v1"
EVIDENCE_VERSION = "repository-playback-evidence-v1"
OUTPUT_EVIDENCE_TYPE = "qualifying_playback_timing_check_v2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_repo_path(raw: str, expected_root: Path) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    root = expected_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes allowed root {expected_root.relative_to(ROOT)}: {raw}")
    return resolved


def load_owned_claim(case_id: str, live_id: str, accepted_by: str, segment_id: str) -> dict:
    task_id = f"P9-PLAYBACK-{case_id}"
    claim_path = CLAIMS / f"{task_id}.json"
    if not claim_path.exists():
        raise ValueError(f"active playback claim does not exist: {task_id}")
    try:
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid playback claim JSON: {exc}") from exc
    if str(claim.get("agent_id") or "") != accepted_by:
        raise ValueError(
            f"acceptance says {accepted_by}, but active playback claim belongs to "
            f"{claim.get('agent_id')!r}"
        )
    if str(claim.get("case_id") or "") != case_id or str(claim.get("live_id") or "") != live_id:
        raise ValueError("active playback claim case/live identity does not match acceptance")
    if segment_id not in set(str(x) for x in (claim.get("missing_segment_ids") or [])):
        raise ValueError("segment is not part of the active playback claim's missing segment set")
    return claim


def process_acceptance(path: Path) -> Path:
    acceptance = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(acceptance, dict):
        raise ValueError("acceptance top level must be an object")
    if acceptance.get("acceptance_version") != ACCEPTANCE_VERSION:
        raise ValueError("unsupported acceptance_version")
    required = [
        "case_id", "live_id", "segment_id", "evidence_ref", "bundle_id",
        "accepted_by", "content_observation",
    ]
    missing = [key for key in required if not acceptance.get(key)]
    if missing:
        raise ValueError("missing acceptance fields: " + ", ".join(missing))
    if acceptance.get("accepted") is not True:
        raise ValueError("accepted must be true; a rejection is not a qualifying playback record")

    case_id = str(acceptance["case_id"])
    live_id = str(acceptance["live_id"])
    segment_id = str(acceptance["segment_id"])
    accepted_by = str(acceptance["accepted_by"])
    load_owned_claim(case_id, live_id, accepted_by, segment_id)

    evidence_path = safe_repo_path(str(acceptance["evidence_ref"]), EVIDENCE_ROOT)
    if not evidence_path.exists():
        raise ValueError(f"evidence file not found: {acceptance['evidence_ref']}")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("evidence top level must be an object")
    if evidence.get("evidence_version") != EVIDENCE_VERSION:
        raise ValueError("unsupported repository evidence version")
    if evidence.get("status") != "ready_for_agent_review":
        raise ValueError(
            f"evidence status {evidence.get('status')!r} is not eligible for worker acceptance"
        )
    if evidence.get("playback_decode_verified") is not True:
        raise ValueError("evidence does not prove successful real-media decoding")
    if evidence.get("repository_content_inspection") is not True:
        raise ValueError("repository content inspection did not run")
    if evidence.get("candidate_content_match") is not True:
        raise ValueError("repository evidence did not produce a qualifying content candidate")

    for key, expected in (("case_id", case_id), ("live_id", live_id), ("segment_id", segment_id)):
        if str(evidence.get(key) or "") != expected:
            raise ValueError(f"acceptance {key} does not match evidence")
    if str(evidence.get("bundle_id") or "") != str(acceptance["bundle_id"]):
        raise ValueError("bundle_id does not match current evidence; re-read the evidence")

    segments, segment_problems = canonical_segment_index()
    if segment_problems:
        raise ValueError("canonical segment index is ambiguous: " + "; ".join(segment_problems[:5]))
    segment = segments.get(segment_id)
    if not segment:
        raise ValueError(f"canonical segment not found: {segment_id}")
    if str(segment.get("live_id") or "") != live_id:
        raise ValueError("canonical segment live_id mismatch")
    if segment.get("start_sec") is None:
        raise ValueError("canonical segment has no start_sec")

    case_live, case_problems = pilot_case_live_map()
    if case_problems:
        raise ValueError("case/live mapping is ambiguous: " + "; ".join(case_problems[:5]))
    if case_live.get(case_id) != live_id:
        raise ValueError(f"case {case_id} does not map to {live_id}")

    expected = float(segment["start_sec"])
    evidence_expected = float(evidence["expected_start_sec"])
    observed = float(evidence["candidate_observed_position_sec"])
    if abs(expected - evidence_expected) > 0.001:
        raise ValueError("evidence expected_start_sec does not match canonical segment")
    signed = observed - expected
    absolute = abs(signed)

    match = (evidence.get("audio_asr") or {}).get("best_match") or {}
    score = float(match.get("score") or 0.0)
    minimum = float(evidence.get("minimum_agent_review_score") or 1.0)
    if score < minimum:
        raise ValueError(f"ASR match score {score} is below evidence minimum {minimum}")

    decode_start = float(evidence["decode_start_sec"])
    decode_window = float(evidence["decode_window_sec"])
    decode_end = decode_start + decode_window
    if observed < decode_start - 0.001 or observed > decode_end + 0.001:
        raise ValueError("candidate observed position lies outside decoded media window")

    record = {
        "project": "Miles-Guo_public_archive",
        "evidence_type": OUTPUT_EVIDENCE_TYPE,
        "case_id": case_id,
        "live_id": live_id,
        "segment_id": segment_id,
        "expected_start_sec": expected,
        "canonical_segment_start_sec": expected,
        "observed_position_sec": round(observed, 3),
        "timing_error_sec": round(signed, 3),
        "absolute_timing_error_sec": round(absolute, 3),
        "media_url": str(evidence["media_url"]),
        "observation_mode": "audio" if not (evidence.get("visual_evidence") or {}).get("frames") else "both",
        "content_match": True,
        "content_observation": str(acceptance["content_observation"]),
        "playback_decode_verified": True,
        "content_timing_verified": True,
        "reviewer": accepted_by,
        "reviewed_at": utc_now(),
        "inspection_method": "repository_decoded_evidence_service_v1",
        "repository_evidence_ref": str(evidence_path.relative_to(ROOT)),
        "repository_evidence_bundle_id": str(evidence["bundle_id"]),
        "repository_evidence_engine": str(evidence.get("inspection_engine") or ""),
        "repository_asr_match_score": score,
        "repository_minimum_review_score": minimum,
        "agent_evidence_acceptance": True,
        "acceptance_ref": str(path.resolve().relative_to(ROOT.resolve())),
        "decode_request_start_sec": float(evidence["decode_request_start_sec"]),
        "decode_start_sec": decode_start,
        "decode_end_sec": decode_end,
        "decode_window_sec": decode_window,
        "decode_resolver": evidence.get("decode_resolver"),
        "decode_media_source": str(evidence["media_url"]),
        "decode_evidence_sha256": evidence.get("decode_evidence_sha256"),
        "clip_sha256": evidence.get("temporary_clip_sha256"),
        "note": (
            "Qualifying v2 record produced only after GitHub Actions decoded real media, "
            "offline Whisper located the target inside the decoded window, durable textual/visual "
            "evidence was written to Git, and the active playback claim owner explicitly reviewed "
            "and accepted that exact evidence bundle."
        ),
    }

    out_dir = OUTPUT_ROOT / case_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{segment_id}.json"
    if out.exists():
        current = json.loads(out.read_text(encoding="utf-8"))
        if current == record:
            print(f"Playback record already exists unchanged: {out.relative_to(ROOT)}")
            return out
        raise ValueError(f"playback record already exists and will not be overwritten: {out.relative_to(ROOT)}")
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created qualifying repository-evidence playback check: {out.relative_to(ROOT)}")
    print(f"timing_error_sec={signed:+.3f} score={score:.3f}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Turn active-claim-owner playback evidence acceptances into durable qualifying v2 records."
    )
    parser.add_argument("--acceptance")
    parser.add_argument("--pending", action="store_true")
    args = parser.parse_args()
    if not args.acceptance and not args.pending:
        parser.error("use --acceptance PATH or --pending")

    paths: list[Path] = []
    if args.acceptance:
        path = Path(args.acceptance)
        if not path.is_absolute():
            path = ROOT / path
        paths.append(path)
    if args.pending and ACCEPTANCE_ROOT.exists():
        paths.extend(sorted(ACCEPTANCE_ROOT.rglob("*.json")))

    seen: set[Path] = set()
    failures = 0
    for path in paths:
        path = path.resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            process_acceptance(path)
        except Exception as exc:
            failures += 1
            print(f"ERROR {path}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
