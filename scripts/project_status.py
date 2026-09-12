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


def exists_completed(task_id: str) -> bool:
    return (COMPLETED / f"{task_id}.json").exists()


def exists_claim(task_id: str) -> bool:
    return (CLAIMS / f"{task_id}.json").exists()


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
    p10_completed = exists_completed("P10-PILOT-DECISION")
    p10_claimed = exists_claim("P10-PILOT-DECISION")

    repository_has_work = bool(ordinary or playback_open)
    host_stop = bool(
        not ordinary
        and playback_open
        and not runtime_playback_capable
        and not p9_playback_gate_completed
    )
    repository_no_eligible_work = bool(not ordinary and not playback_open)

    if p10_completed:
        state = "PILOT_DECISION_COMPLETED"
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
            "full_archive_authorized": p10_completed,
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
        f"FULL_ARCHIVE_AUTHORIZED={gates['full_archive_authorized']}"
    )
    if status["host_stop_for_this_runtime"]:
        print(
            "HOST_STOP: repository work still exists, but this runtime cannot honestly "
            "claim the remaining real-playback work. Do not report repository-wide "
            "NO_ELIGIBLE_WORK."
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
