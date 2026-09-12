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
BUG_REPORTS = ROOT / "coordination" / "bug_reports"

GATE_OR_REPORT_KINDS = {
    "alignment_gate",
    "database_gate",
    "qa_gate",
    "report",
}
CLOSED_BUG_STATUSES = {"resolved", "closed", "dismissed", "fixed"}


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


def ordinary_task_type(task: dict) -> str:
    task_id = str(task.get("id") or "")
    kind = str(task.get("kind") or "")
    if task_id in {"P9-AUDIT-60", "P10-PILOT-DECISION"} or kind in GATE_OR_REPORT_KINDS:
        return "gate_or_report"
    return "business"


def load_admin_bug_queue() -> tuple[list[dict], list[str]]:
    """Return unresolved bug reports plus malformed bug-report files needing admin review."""
    open_reports: list[dict] = []
    invalid: list[str] = []
    if not BUG_REPORTS.exists():
        return open_reports, invalid

    for path in sorted(BUG_REPORTS.glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            invalid.append(f"{path.name}: invalid JSON: {exc}")
            continue
        if not isinstance(row, dict):
            invalid.append(f"{path.name}: top-level JSON must be an object")
            continue
        status = str(row.get("status") or "open").strip().lower()
        if status in CLOSED_BUG_STATUSES:
            continue
        open_reports.append(
            {
                "bug_id": str(row.get("bug_id") or path.stem),
                "status": status,
                "severity": row.get("severity"),
                "category": row.get("category"),
                "summary": row.get("summary"),
                "requires_admin": row.get("requires_admin", True) is not False,
                "path": str(path.relative_to(ROOT)),
            }
        )
    return open_reports, invalid


def build_status(content_inspection_capable: bool, role: str) -> dict:
    role = role.strip().lower()
    if role not in {"worker", "admin"}:
        raise ValueError(f"unsupported role: {role}")

    ordinary = next_task.eligible_tasks()
    ordinary_business = [task for task in ordinary if ordinary_task_type(task) == "business"]
    ordinary_gate_report = [task for task in ordinary if ordinary_task_type(task) == "gate_or_report"]

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

    open_bug_reports, invalid_bug_reports = load_admin_bug_queue()
    admin_queue_has_work = bool(open_bug_reports or invalid_bug_reports)
    admin_work_available_for_session = bool(role == "admin" and admin_queue_has_work)

    runtime_media_tools = bool(tools.get("ffmpeg") and tools.get("ffprobe"))
    runtime_playback_capable = bool(runtime_media_tools and content_inspection_capable)

    p9_playback_gate_completed = exists_completed("P9-PLAYBACK-GATE")
    p9_completed = exists_completed("P9-AUDIT-60")
    p10_record = load_completed("P10-PILOT-DECISION")
    p10_completed = p10_record is not None
    p10_claimed = exists_claim("P10-PILOT-DECISION")
    full_archive_decision = normalize_full_archive_decision(p10_record)
    full_archive_authorized = bool(p10_completed and full_archive_decision == "YES")

    pilot60_pass = bool(gate.get("pilot60_pass"))
    playback_gate_action_available = bool(pilot60_pass and not p9_playback_gate_completed)

    # A passed Pilot-60 gate is a non-media transition. Remaining optional playback cases
    # must not keep a non-media runtime in HOST_STOP once the acceptance threshold is met.
    session_non_playback_work = bool(
        ordinary
        or admin_work_available_for_session
        or playback_gate_action_available
    )
    session_playback_work = bool(runtime_playback_capable and playback_unclaimed)
    session_work_available = bool(session_non_playback_work or session_playback_work)

    repository_has_work = bool(
        ordinary
        or playback_open
        or admin_queue_has_work
        or playback_gate_action_available
    )
    repository_no_eligible_work = bool(not repository_has_work)

    host_stop = bool(
        not session_work_available
        and playback_unclaimed
        and not runtime_playback_capable
        and not pilot60_pass
        and not p9_playback_gate_completed
    )
    role_stop = bool(
        not session_work_available
        and admin_queue_has_work
        and role != "admin"
        and not playback_unclaimed
    )
    wait_for_active_claims = bool(
        not session_work_available
        and playback_claimed
        and not playback_unclaimed
        and not repository_no_eligible_work
    )

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
    elif pilot60_pass:
        state = "PLAYBACK_GATE_READY_TO_SEAL"
    elif playback_open:
        state = "PLAYBACK_AUDIT_REQUIRED"
    else:
        state = "PILOT_WORK_IN_PROGRESS"

    if session_work_available:
        classification = "WORK_AVAILABLE"
    elif host_stop:
        classification = "HOST_STOP"
    elif role_stop:
        classification = "ROLE_STOP"
    elif wait_for_active_claims:
        classification = "WAIT_FOR_ACTIVE_CLAIMS"
    elif repository_no_eligible_work:
        classification = "NO_ELIGIBLE_WORK"
    else:
        classification = "WAIT_FOR_DEPENDENCY"

    if admin_work_available_for_session:
        recommended_action = "ADMIN_REVIEW_BUG_QUEUE"
    elif playback_gate_action_available:
        recommended_action = "SEAL_P9_PLAYBACK_GATE"
    elif ordinary_gate_report:
        recommended_action = "CLAIM_GATE_OR_REPORT_TASK"
    elif ordinary_business:
        recommended_action = "CLAIM_ORDINARY_BUSINESS_TASK"
    elif session_playback_work:
        recommended_action = "CLAIM_REAL_PLAYBACK_TASK"
    elif host_stop:
        recommended_action = "HOST_STOP_FOR_THIS_RUNTIME_ONLY"
    elif role_stop:
        recommended_action = "ROLE_STOP_ADMIN_WORK_REMAINS"
    elif wait_for_active_claims:
        recommended_action = "REFRESH_OR_WAIT_FOR_ACTIVE_CLAIMS"
    else:
        recommended_action = "NO_CURRENT_ACTION"

    return {
        "project": "Miles-Guo_public_archive",
        "state": state,
        "classification": classification,
        "recommended_action": recommended_action,
        "role": role,
        "repository_has_work": repository_has_work,
        "repository_no_eligible_work": repository_no_eligible_work,
        "session_work_available": session_work_available,
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
            "business_eligible_count": len(ordinary_business),
            "gate_or_report_eligible_count": len(ordinary_gate_report),
            "eligible_task_ids": [task.get("id") for task in ordinary],
            "business_task_ids": [task.get("id") for task in ordinary_business],
            "gate_or_report_task_ids": [task.get("id") for task in ordinary_gate_report],
        },
        "playback_queue": {
            "open_case_count": len(playback_open),
            "unclaimed_case_count": len(playback_unclaimed),
            "claimed_case_count": len(playback_claimed),
            "open_task_ids": [row.get("task_id") for row in playback_open],
            "claimable_by_this_runtime": bool(runtime_playback_capable and playback_unclaimed),
        },
        "admin_queue": {
            "open_bug_count": len(open_bug_reports),
            "invalid_bug_report_count": len(invalid_bug_reports),
            "actionable_for_this_role": admin_work_available_for_session,
            "open_bug_ids": [row.get("bug_id") for row in open_bug_reports],
            "invalid_bug_reports": invalid_bug_reports,
        },
        "pilot60": {
            "qualifying_checks": gate.get("qualifying_checks", 0),
            "required_checks": gate.get("required_checks", 60),
            "pilot60_pass": pilot60_pass,
            "invalid_records": gate.get("invalid_records") or [],
        },
        "gates": {
            "P9_PLAYBACK_GATE_completed": p9_playback_gate_completed,
            "P9_PLAYBACK_GATE_ready_to_seal": playback_gate_action_available,
            "P9_AUDIT_60_completed": p9_completed,
            "P10_PILOT_DECISION_claimed": p10_claimed,
            "P10_PILOT_DECISION_completed": p10_completed,
            "P10_full_archive_decision": full_archive_decision,
            "full_archive_authorized": full_archive_authorized,
        },
        "task_types": {
            "ordinary_business": "collection/alignment/source or transcript audit/data work; no real media playback required unless the task explicitly says so",
            "real_playback": "requires ffmpeg+ffprobe plus actual decoded content inspection",
            "gate_or_report": "P9/P10 and aggregate gate/report work; does not itself require replaying media once prerequisites are satisfied",
            "admin_control": "bug reports/control-plane/schema/CI/workflow fixes; admin role only",
        },
        "rules": {
            "legacy_audit_markers_count_toward_pilot60": False,
            "decode_without_content_inspection_counts_toward_pilot60": False,
            "playback_inability_blocks_ordinary_or_gate_tasks": False,
            "playback_inability_blocks_admin_bug_work": False,
            "pilot60_pass_makes_gate_seal_non_media_work_available": True,
            "p10_may_start_before_p9_complete": False,
            "p10_completion_alone_authorizes_full_archive": False,
            "full_archive_requires_explicit_p10_yes": True,
            "full_archive_may_start_before_p10_decision": False,
        },
    }


def print_human(status: dict) -> None:
    print(f"Project: {status['project']}")
    print(f"Role: {status['role']}")
    print(f"State: {status['state']}")
    print(f"Classification: {status['classification']}")
    print(f"Recommended action: {status['recommended_action']}")

    ordinary = status["ordinary_queue"]
    print(
        "Ordinary queue: "
        f"{ordinary['eligible_count']} eligible "
        f"({ordinary['business_eligible_count']} business, "
        f"{ordinary['gate_or_report_eligible_count']} gate/report)"
    )
    print(
        "Playback queue: "
        f"{status['playback_queue']['open_case_count']} open "
        f"({status['playback_queue']['unclaimed_case_count']} unclaimed, "
        f"{status['playback_queue']['claimed_case_count']} claimed)"
    )
    print(
        "Admin queue: "
        f"{status['admin_queue']['open_bug_count']} open bugs, "
        f"{status['admin_queue']['invalid_bug_report_count']} invalid reports, "
        f"actionable-for-role={status['admin_queue']['actionable_for_this_role']}"
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
        f"READY_TO_SEAL={gates['P9_PLAYBACK_GATE_ready_to_seal']} "
        f"P9-AUDIT-60={gates['P9_AUDIT_60_completed']} "
        f"P10={gates['P10_PILOT_DECISION_completed']} "
        f"P10_DECISION={gates['P10_full_archive_decision'] or 'UNRECORDED'} "
        f"FULL_ARCHIVE_AUTHORIZED={gates['full_archive_authorized']}"
    )

    if status["host_stop_for_this_runtime"]:
        print(
            "HOST_STOP: no ordinary/gate/admin work compatible with this session is "
            "currently available, while unclaimed real-playback work remains and this "
            "runtime cannot honestly perform it. This is a session capability limit, "
            "not repository-wide NO_ELIGIBLE_WORK."
        )
    if status["classification"] == "ROLE_STOP":
        print(
            "ROLE_STOP: project work remains, but it is admin-only and this session is "
            "classified as worker. Do not modify the control plane; report/leave it for admin."
        )
    if gates["P9_PLAYBACK_GATE_ready_to_seal"]:
        print(
            "Pilot-60 already passes. Remaining optional playback cases do not block the "
            "acceptance path. Seal P9-PLAYBACK-GATE, then continue to P9/P10 when eligible."
        )
    if gates["P10_PILOT_DECISION_completed"] and gates["P10_full_archive_decision"] is None:
        print(
            "FULL_ARCHIVE remains locked: P10 completion exists but no explicit "
            "full_archive_decision=YES|NO was recorded."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify Miles-Guo_public_archive work by task type, Agent role, runtime "
            "capability, and Pilot gate state without relying on stale chat summaries."
        )
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--role",
        choices=["worker", "admin"],
        default="worker",
        help=(
            "Agent role. Default worker. Use admin only when the authenticated GitHub "
            "identity is verified as an authorized admin (currently witnessGIT)."
        ),
    )
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

    status = build_status(args.content_inspection_capable, args.role)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        print_human(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
