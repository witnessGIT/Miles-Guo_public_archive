#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import next_task
import playback_queue

ROOT = Path(__file__).resolve().parents[1]
COMPLETED = ROOT / "coordination" / "completed"
CLAIMS = ROOT / "coordination" / "claims"


def completed_path(task_id: str) -> Path:
    return COMPLETED / f"{task_id}.json"


def exists_completed(task_id: str) -> bool:
    return completed_path(task_id).exists()


def load_completed(task_id: str) -> dict | None:
    path = completed_path(task_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def exists_claim(task_id: str) -> bool:
    return (CLAIMS / f"{task_id}.json").exists()


def normalize_full_archive_decision(record: dict | None) -> str | None:
    """Return YES/NO only for an explicit machine-readable Pilot decision.

    Completing P10 is not itself authorization. Missing, malformed, or differently named
    fields intentionally resolve to None so FULL_ARCHIVE stays locked by default.
    """
    if not record:
        return None
    value = record.get("full_archive_decision")
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    return normalized if normalized in {"YES", "NO"} else None


def build_status(content_inspection_capable: bool) -> dict:
    ordinary = next_task.eligible_tasks()
    playback_rows = playback_queue.case_statuses()
    gate = playback_queue.gate_summary()
    tools = playback_queue.capability_status()

    playback_open = [
        row
        for row in playback_rows
        if row.get("missing_segment_ids") and not row.get("completed")
    ]
    playback_unclaimed = [row for row in playback_open if not row.get("claim_exists")]
    playback_claimed = [row for row in playback_open if row.get("claim_exists")]

    runtime_media_tools = bool(tools.get("ffmpeg") and tools.get("ffprobe"))
    runtime_playback_capable = bool(runtime_media_tools and content_inspection_capable)

    p9_playback_gate_completed = exists_completed("P9-PLAYBACK-GATE")
    p9_completed = exists_completed("P9-AUDIT-60")
    p10_record = load_completed("P10-PILOT-DECISION")
    p10_completed = p10_record is not None
    p10_claimed = exists_claim("P10-PILOT-DECISION")
    full_archive_decision = normalize_full_archive_decision(p10_record)
    full_archive_authorized = bool(p10_completed and full_archive_decision == "YES")

    repository_has_work = bool(ordinary or playback_open)
    host_stop = bool(
        not ordinary
        and playback_open
        and not runtime_playback_capable
        and not p9_playback_gate_completed
    )
    repository_no_eligible_work = bool(not ordinary and not playback_open)

    if p10_completed and full_archive_decision == "YES":
        state = "PILOT_DECISION_COMPLETED_FULL_ARCHIVE_YES"
    elif p10_completed and full_archive_decision == "NO":
        state = "PILOT_DECISION_COMPLETED_FULL_ARCHIVE_NO"
    elif p10_completed:
        state = "PILOT_DECISION_COMPLETED_DECISION_UNRECORDED"
    elif p9_completed:
        state = "P10_READY_OR_IN_PROGRESS"
    elif p9_playback_gate_completed:
        state = "P9_AGGREGATE_GATE_READY"
    elif playback_open:
        state = "PLAYBACK_AUDIT_REQUIRED"
    elif gate.get("pilot60_pass"):
        state = "PLAYBACK_GATE_READY_TO_SEAL"
    else:
        state = "PILOT_WORK_IN_PROGRESS"

    return {
        "project": "Miles-Guo_public_archive",
        "state": state,
        "repository_has_work": repository_has_work,
        "repository_no_eligible_work": repository_no_eligible_work,
        "host_stop_for_this_runtime": host_stop,
        "runtime": {
            "ffmpeg": bool(tools.get("ffmpeg")),
            "ffprobe": bool(tools.get("ffprobe")),
            "yt_dlp": bool(tools.get("yt_dlp")),
            "content_inspection_capable_declared": content_inspection_capable,
            "playback_capable": runtime_playback_capable,
        },
        "ordinary_queue": {
            "eligible_count": len(ordinary),
            "eligible_task_ids": [task.get("id") for task in ordinary],
        },
        "playback_queue": {
            "open_case_count": len(playback_open),
            "unclaimed_case_count": len(playback_unclaimed),
            "claimed_case_count": len(playback_claimed),
            "open_task_ids": [row.get("task_id") for row in playback_open],
        },
        "pilot60": {
            "qualifying_checks": gate.get("qualifying_checks", 0),
            "required_checks": gate.get("required_checks", 60),
            "pilot60_pass": bool(gate.get("pilot60_pass")),
            "invalid_records": gate.get("invalid_records") or [],
        },
        "gates": {
            "P9_PLAYBACK_GATE_completed": p9_playback_gate_completed,
            "P9_AUDIT_60_completed": p9_completed,
            "P10_PILOT_DECISION_claimed": p10_claimed,
            "P10_PILOT_DECISION_completed": p10_completed,
            "P10_full_archive_decision": full_archive_decision,
            "full_archive_authorized": full_archive_authorized,
        },
        "classification": (
            "HOST_STOP"
            if host_stop
            else "NO_ELIGIBLE_WORK"
            if repository_no_eligible_work
            else "WORK_AVAILABLE"
        ),
        "rules": {
            "legacy_audit_markers_count_toward_pilot60": False,
            "decode_without_content_inspection_counts_toward_pilot60": False,
            "p10_may_start_before_p9_complete": False,
            "p10_completion_alone_authorizes_full_archive": False,
            "full_archive_requires_explicit_p10_yes": True,
            "full_archive_may_start_before_p10_decision": False,
        },
    }


def print_human(status: dict) -> None:
    print(f"Project: {status['project']}")
    print(f"State: {status['state']}")
    print(f"Classification: {status['classification']}")
    print(
        "Ordinary queue: "
        f"{status['ordinary_queue']['eligible_count']} eligible"
    )
    print(
        "Playback queue: "
        f"{status['playback_queue']['open_case_count']} open "
        f"({status['playback_queue']['unclaimed_case_count']} unclaimed, "
        f"{status['playback_queue']['claimed_case_count']} claimed)"
    )
    print(
        "Pilot-60: "
        f"{status['pilot60']['qualifying_checks']}/"
        f"{status['pilot60']['required_checks']} "
        f"pass={status['pilot60']['pilot60_pass']}"
    )
    runtime = status["runtime"]
    print(
        "Runtime: "
        f"ffmpeg={runtime['ffmpeg']} ffprobe={runtime['ffprobe']} "
        f"yt-dlp={runtime['yt_dlp']} "
        f"content-inspection-declared={runtime['content_inspection_capable_declared']} "
        f"playback-capable={runtime['playback_capable']}"
    )
    gates = status["gates"]
    print(
        "Gates: "
        f"P9-PLAYBACK-GATE={gates['P9_PLAYBACK_GATE_completed']} "
        f"P9-AUDIT-60={gates['P9_AUDIT_60_completed']} "
        f"P10={gates['P10_PILOT_DECISION_completed']} "
        f"P10_DECISION={gates['P10_full_archive_decision'] or 'UNRECORDED'} "
        f"FULL_ARCHIVE_AUTHORIZED={gates['full_archive_authorized']}"
    )
    if status["host_stop_for_this_runtime"]:
        print(
            "HOST_STOP: repository work still exists, but this runtime cannot honestly "
            "claim the remaining real-playback work. Do not report repository-wide "
            "NO_ELIGIBLE_WORK."
        )
    if gates["P10_PILOT_DECISION_completed"] and gates["P10_full_archive_decision"] is None:
        print(
            "FULL_ARCHIVE remains locked: P10 completion exists but no explicit "
            "full_archive_decision=YES|NO was recorded."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify current Miles-Guo_public_archive work state across ordinary and "
            "real-playback queues without relying on stale chat summaries."
        )
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--content-inspection-capable",
        action="store_true",
        help=(
            "Declare that this runtime can actually inspect decoded clip/frame/audio "
            "content and determine observed content position. Do not pass merely because "
            "ffmpeg can execute."
        ),
    )
    args = parser.parse_args()

    status = build_status(args.content_inspection_capable)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        print_human(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
