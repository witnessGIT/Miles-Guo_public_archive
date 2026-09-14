#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from playback_validation import (
    canonical_segment_index,
    pilot_case_live_map,
    validate_playback_record,
)

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "coordination" / "claims"
COMPLETED = ROOT / "coordination" / "completed"
ATTEMPTS = ROOT / "coordination" / "playback_attempts"
REQUEST_ROOT = ROOT / "coordination" / "playback_requests"
ACCEPTANCE_ROOT = ROOT / "coordination" / "playback_acceptances"
EVIDENCE_ROOT = ROOT / "data" / "playback_evidence"
PLAYBACK_ROOT = ROOT / "data" / "playback_audits"
PILOT_SELECTION = ROOT / "reports" / "pilot_selection.json"
AUDIT_GATE = ROOT / "scripts" / "audit_gate.py"
SERVICE_WORKFLOW = ROOT / ".github" / "workflows" / "playback-evidence-service.yml"
GATE_ID = "P9-PLAYBACK-GATE"
ACTIVE_QUEUE_GENERATION = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cases() -> list[str]:
    if not PILOT_SELECTION.exists():
        return []
    payload = json.loads(PILOT_SELECTION.read_text(encoding="utf-8"))
    result: list[str] = []
    for cases in payload.get("groups", {}).values():
        for case in cases:
            case_id = case.get("pilot_case_id")
            if case_id:
                result.append(str(case_id))
    return result


def canonical_timed_segments() -> tuple[dict[str, dict], dict[str, set[str]], list[str]]:
    segments, problems = canonical_segment_index()
    by_live: dict[str, set[str]] = {}
    for segment_id, row in segments.items():
        if row.get("start_sec") is None:
            continue
        live_id = str(row.get("live_id") or "")
        if not live_id:
            continue
        by_live.setdefault(live_id, set()).add(segment_id)
    return segments, by_live, problems


def valid_playback_segments() -> tuple[dict[str, set[str]], list[str]]:
    segments, segment_problems = canonical_segment_index()
    case_live, case_problems = pilot_case_live_map()
    problems = [*segment_problems, *case_problems]
    checked: dict[str, set[str]] = {}
    if not PLAYBACK_ROOT.exists():
        return checked, problems

    seen: set[str] = set()
    for path in sorted(PLAYBACK_ROOT.rglob("*.json")):
        rel = str(path.relative_to(ROOT))
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{rel}: invalid JSON: {exc}")
            continue
        if not isinstance(row, dict):
            problems.append(f"{rel}: top-level JSON must be an object")
            continue
        validated, row_problems = validate_playback_record(
            row,
            source_label=rel,
            segments=segments,
            case_live=case_live,
        )
        if row_problems:
            problems.extend(row_problems)
            continue
        assert validated is not None
        segment_id = str(validated["segment_id"])
        if segment_id in seen:
            problems.append(f"{rel}: duplicate qualifying segment_id {segment_id}")
            continue
        seen.add(segment_id)
        checked.setdefault(str(validated["case_id"]), set()).add(segment_id)
    return checked, problems


def _evidence_state(case_id: str, segment_id: str) -> str:
    path = EVIDENCE_ROOT / case_id / segment_id / "evidence.json"
    if not path.exists():
        return "none"
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "invalid"
    return str(row.get("status") or "unknown")


def case_statuses() -> list[dict]:
    case_live, case_problems = pilot_case_live_map()
    _, timed_by_live, segment_problems = canonical_timed_segments()
    checked, playback_problems = valid_playback_segments()
    global_problems = [*case_problems, *segment_problems, *playback_problems]

    rows: list[dict] = []
    for case_id in load_cases():
        live_id = case_live.get(case_id)
        if not live_id:
            continue
        timed = timed_by_live.get(live_id, set())
        if not timed:
            continue
        have = checked.get(case_id, set())
        missing = sorted(timed - have)
        task_id = f"P9-PLAYBACK-{case_id}"
        rows.append(
            {
                "task_id": task_id,
                "case_id": case_id,
                "live_id": live_id,
                "timed_segments": len(timed),
                "qualifying_segments": len(timed & have),
                "missing_segment_ids": missing,
                "evidence_states": {segment_id: _evidence_state(case_id, segment_id) for segment_id in missing},
                "claim_exists": (CLAIMS / f"{task_id}.json").exists(),
                "completed": (COMPLETED / f"{task_id}.json").exists(),
                "global_validation_problems": global_problems,
            }
        )
    return rows


def gate_summary() -> dict:
    process = subprocess.run(
        ["python", str(AUDIT_GATE), "--json"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError:
        return {
            "pilot60_pass": False,
            "qualifying_checks": 0,
            "invalid_records": [
                "audit_gate.py did not emit valid JSON",
                process.stderr[-2000:],
            ],
        }


def capability_status() -> dict:
    return {
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
        "yt_dlp": bool(shutil.which("yt-dlp")),
        "repository_evidence_service": SERVICE_WORKFLOW.exists(),
    }


def print_status() -> None:
    tools = capability_status()
    gate = gate_summary()
    print("Real playback audit queue")
    print(
        "  repository_evidence_service="
        f"{tools['repository_evidence_service']} local_ffmpeg={tools['ffmpeg']} "
        f"local_ffprobe={tools['ffprobe']} local_yt-dlp={tools['yt_dlp']}"
    )
    print(
        f"  Pilot-60: {gate.get('qualifying_checks', 0)}/"
        f"{gate.get('required_checks', 60)} pass={gate.get('pilot60_pass', False)}"
    )
    invalid = gate.get("invalid_records") or []
    if invalid:
        print(f"  invalid playback records: {len(invalid)}")
    for row in case_statuses():
        if not row["missing_segment_ids"]:
            continue
        state = "claimed" if row["claim_exists"] and not row["completed"] else "open"
        evidence_ready = sum(1 for value in row["evidence_states"].values() if value == "ready_for_agent_review")
        print(
            f"  {row['task_id']} [{state}] live={row['live_id']} "
            f"qualified={row['qualifying_segments']}/{row['timed_segments']} "
            f"missing={len(row['missing_segment_ids'])} evidence_ready={evidence_ready}"
        )


def choose_case(agent_id: str, requested_case: str | None) -> dict:
    candidates = [
        row
        for row in case_statuses()
        if row["missing_segment_ids"] and not row["claim_exists"] and not row["completed"]
    ]
    if requested_case:
        candidates = [row for row in candidates if row["case_id"] == requested_case]
    if not candidates:
        raise SystemExit("No unclaimed playback-audit case with missing qualifying segments.")
    candidates.sort(key=lambda row: row["case_id"])
    seed = int(hashlib.sha256(agent_id.encode("utf-8")).hexdigest(), 16)
    return candidates[seed % len(candidates)]


def claim_case(agent_id: str, requested_case: str | None, content_inspection_capable: bool) -> Path:
    tools = capability_status()
    local_capable = bool(tools["ffmpeg"] and tools["ffprobe"] and content_inspection_capable)
    repository_capable = bool(tools["repository_evidence_service"])
    if not local_capable and not repository_capable:
        raise SystemExit(
            "No playback execution path is available. The repository evidence service is absent "
            "and this runtime is not a declared local decoded-content reviewer."
        )
    chosen = choose_case(agent_id, requested_case)
    CLAIMS.mkdir(parents=True, exist_ok=True)
    path = CLAIMS / f"{chosen['task_id']}.json"
    execution_mode = "repository_evidence_service_v1" if repository_capable else "local_manual_v1"
    payload = {
        "task_id": chosen["task_id"],
        "agent_id": agent_id,
        "claimed_at": utc_now(),
        "status": "in_progress",
        "kind": "real_playback_audit",
        "case_id": chosen["case_id"],
        "live_id": chosen["live_id"],
        "missing_segment_ids": chosen["missing_segment_ids"],
        "execution_mode": execution_mode,
        "queue_generation": ACTIVE_QUEUE_GENERATION,
        "repository_evidence_service": repository_capable,
        "local_runtime_tools": tools,
        "local_content_inspection_capable": bool(content_inspection_capable),
        "instructions": (
            "Preferred path: submit coordination/playback_requests/<CASE>/<SEGMENT>.json, "
            "let GitHub Actions decode real media and publish data/playback_evidence, read the "
            "evidence, then submit coordination/playback_acceptances. Local manual playback "
            "remains a fallback. Source-page timestamps alone never count."
        ),
    }
    with path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"Claimed {chosen['task_id']} for {chosen['case_id']} via {execution_mode}")
    print("Missing canonical timed segments:")
    for segment_id in chosen["missing_segment_ids"]:
        print(f"  - {segment_id}")
    return path


def _owned_claim(agent_id: str, case_id: str) -> dict:
    task_id = f"P9-PLAYBACK-{case_id}"
    path = CLAIMS / f"{task_id}.json"
    if not path.exists():
        raise SystemExit(f"Claim not found: {path.relative_to(ROOT)}")
    claim = json.loads(path.read_text(encoding="utf-8"))
    if claim.get("agent_id") != agent_id:
        raise SystemExit(f"Claim belongs to {claim.get('agent_id')!r}, not {agent_id!r}")
    return claim


def request_segment(agent_id: str, case_id: str, segment_id: str, media_url: str, visual_mode: str) -> Path:
    claim = _owned_claim(agent_id, case_id)
    if segment_id not in set(claim.get("missing_segment_ids") or []):
        raise SystemExit(f"Segment is not in this claim's missing set: {segment_id}")
    out_dir = REQUEST_ROOT / case_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{segment_id}.json"
    if out.exists():
        print(f"Playback request already exists: {out.relative_to(ROOT)}")
        return out
    payload = {
        "request_version": "playback-request-v1",
        "request_revision": 1,
        "queue_generation": ACTIVE_QUEUE_GENERATION,
        "task_id": f"P9-PLAYBACK-{case_id}",
        "case_id": case_id,
        "live_id": claim.get("live_id"),
        "segment_id": segment_id,
        "media_url": media_url,
        "requested_by": agent_id,
        "requested_at": utc_now(),
        "pre_roll_sec": 10.0,
        "decode_window_sec": 24.0,
        "language": "zh",
        "visual_mode": visual_mode,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created playback request: {out.relative_to(ROOT)}")
    print("Commit/push it. GitHub Actions will publish durable Agent-readable evidence.")
    return out


def accept_segment(agent_id: str, case_id: str, segment_id: str, content_observation: str) -> Path:
    claim = _owned_claim(agent_id, case_id)
    evidence = EVIDENCE_ROOT / case_id / segment_id / "evidence.json"
    if not evidence.exists():
        raise SystemExit(f"Evidence not found: {evidence.relative_to(ROOT)}")
    row = json.loads(evidence.read_text(encoding="utf-8"))
    if row.get("status") != "ready_for_agent_review":
        raise SystemExit(f"Evidence is not ready for acceptance: status={row.get('status')!r}")
    if str(row.get("live_id")) != str(claim.get("live_id")):
        raise SystemExit("Evidence live_id does not match the playback claim")
    out_dir = ACCEPTANCE_ROOT / case_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{segment_id}.json"
    if out.exists():
        print(f"Playback acceptance already exists: {out.relative_to(ROOT)}")
        return out
    payload = {
        "acceptance_version": "playback-acceptance-v1",
        "case_id": case_id,
        "live_id": claim.get("live_id"),
        "segment_id": segment_id,
        "evidence_ref": str(evidence.relative_to(ROOT)),
        "bundle_id": row.get("bundle_id"),
        "accepted": True,
        "accepted_by": agent_id,
        "accepted_at": utc_now(),
        "content_observation": content_observation,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created playback acceptance: {out.relative_to(ROOT)}")
    print("Commit/push it. GitHub Actions will create the qualifying v2 playback audit record.")
    return out


def finish_case(agent_id: str, case_id: str) -> Path:
    _owned_claim(agent_id, case_id)
    task_id = f"P9-PLAYBACK-{case_id}"
    status = next((row for row in case_statuses() if row["case_id"] == case_id), None)
    if status is None:
        raise SystemExit(f"Unknown or unaligned Pilot case: {case_id}")
    if status["global_validation_problems"]:
        raise SystemExit(
            "Playback evidence has validation problems; report them before completion: "
            + "; ".join(status["global_validation_problems"][:5])
        )
    if status["missing_segment_ids"]:
        raise SystemExit(
            f"Cannot finish {task_id}: {len(status['missing_segment_ids'])} canonical timed "
            "segment(s) still lack qualifying real playback records."
        )
    COMPLETED.mkdir(parents=True, exist_ok=True)
    out = COMPLETED / f"{task_id}.json"
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "completed_at": utc_now(),
        "case_id": case_id,
        "live_id": status["live_id"],
        "qualifying_playback_checks": status["qualifying_segments"],
        "timed_segments": status["timed_segments"],
        "execution_contract": "repository_evidence_or_local_manual_v1",
        "validation": (
            "All currently tracked timed segments for this case have canonical-crosschecked "
            "qualifying real playback records."
        ),
    }
    with out.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"Completed real playback case: {task_id}")
    return out


def block_case(agent_id: str, case_id: str, reason: str) -> Path:
    task_id = f"P9-PLAYBACK-{case_id}"
    claim_path = CLAIMS / f"{task_id}.json"
    claim = _owned_claim(agent_id, case_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ATTEMPTS / case_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{stamp}-{hashlib.sha256(agent_id.encode()).hexdigest()[:8]}.json"
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "blocked_at": utc_now(),
        "case_id": case_id,
        "execution_mode": claim.get("execution_mode"),
        "reason": reason,
        "counts_toward_pilot_60": False,
        "note": "Blocked attempt is preserved, but the case is released for a later retry.",
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    claim_path.unlink()
    print(f"Recorded blocked playback attempt: {out.relative_to(ROOT)}")
    print(f"Released claim: {claim_path.relative_to(ROOT)}")
    return out


def seal_gate(agent_id: str) -> Path:
    summary = gate_summary()
    if not summary.get("pilot60_pass"):
        raise SystemExit(
            f"Cannot seal {GATE_ID}: qualifying_checks={summary.get('qualifying_checks', 0)} "
            f"required={summary.get('required_checks', 60)} pass={summary.get('pilot60_pass', False)}"
        )
    COMPLETED.mkdir(parents=True, exist_ok=True)
    out = COMPLETED / f"{GATE_ID}.json"
    if out.exists():
        print(f"Gate already sealed: {out.relative_to(ROOT)}")
        return out
    payload = {
        "task_id": GATE_ID,
        "agent_id": agent_id,
        "completed_at": utc_now(),
        "validation": summary,
        "notes": "This sentinel exists only after scripts/audit_gate.py reports pilot60_pass=true.",
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sealed Pilot-60 playback gate: {out.relative_to(ROOT)}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage retryable real-playback Pilot audit work.")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--claim", action="store_true")
    parser.add_argument("--finish", metavar="CASE_ID")
    parser.add_argument("--block", metavar="CASE_ID")
    parser.add_argument("--request", metavar="SEGMENT_ID")
    parser.add_argument("--accept", metavar="SEGMENT_ID")
    parser.add_argument("--media-url")
    parser.add_argument("--content-observation")
    parser.add_argument("--visual-mode", choices=["frames_ocr", "smolvlm2_optional"], default="frames_ocr")
    parser.add_argument("--reason")
    parser.add_argument("--seal-gate", action="store_true")
    parser.add_argument("--case-id")
    parser.add_argument("--agent-id")
    parser.add_argument(
        "--content-inspection-capable",
        action="store_true",
        help=(
            "Optional local-manual fallback declaration. It is no longer required when the "
            "repository Playback Evidence Service is present."
        ),
    )
    args = parser.parse_args()

    if args.seal_gate:
        if not args.agent_id:
            raise SystemExit("--seal-gate requires --agent-id")
        seal_gate(args.agent_id)
        return 0
    if args.finish:
        if not args.agent_id:
            raise SystemExit("--finish requires --agent-id")
        finish_case(args.agent_id, args.finish)
        return 0
    if args.block:
        if not args.agent_id or not args.reason:
            raise SystemExit("--block requires --agent-id and --reason")
        block_case(args.agent_id, args.block, args.reason)
        return 0
    if args.request:
        if not args.agent_id or not args.case_id or not args.media_url:
            raise SystemExit("--request requires --agent-id, --case-id, and --media-url")
        request_segment(args.agent_id, args.case_id, args.request, args.media_url, args.visual_mode)
        return 0
    if args.accept:
        if not args.agent_id or not args.case_id or not args.content_observation:
            raise SystemExit("--accept requires --agent-id, --case-id, and --content-observation")
        accept_segment(args.agent_id, args.case_id, args.accept, args.content_observation)
        return 0
    if args.claim:
        if not args.agent_id:
            raise SystemExit("--claim requires --agent-id")
        claim_case(args.agent_id, args.case_id, args.content_inspection_capable)
        return 0

    print_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
