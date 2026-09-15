#!/usr/bin/env python3
"""Single-command entry for a fresh ordinary Agent session.

This helper intentionally performs only a local atomic claim.  The caller must refresh before
running it and immediately make the resulting claim visible on ``main`` (or create its task PR).
The first claim/reservation that is durably visible in Git is the authoritative first arrival.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

import next_task
import playback_queue
import playback_retry_guard


ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / ".agent_session.json"


def new_agent_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"agent-{stamp}-{secrets.token_hex(4)}"


def load_or_create_agent_id(explicit: str | None) -> str:
    if explicit:
        return explicit
    try:
        current = json.loads(SESSION.read_text(encoding="utf-8"))
        agent_id = current.get("agent_id")
        if isinstance(agent_id, str) and agent_id:
            return agent_id
    except (OSError, json.JSONDecodeError):
        pass
    agent_id = new_agent_id()
    SESSION.write_text(
        json.dumps(
            {
                "agent_id": agent_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "purpose": "local stable identity for one autonomous repository Agent session",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return agent_id


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def playback_entry_candidates(agent_id: str) -> tuple[list[dict], list[dict]]:
    """Return unclaimed or legally expired playback work in collision-resistant order."""
    candidates = [
        row
        for row in playback_queue.case_statuses()
        if row.get("missing_segment_ids")
        and not row.get("completed")
        and (not row.get("claim_exists") or row.get("claim_expired"))
    ]
    candidates.sort(key=lambda row: str(row.get("case_id") or ""))
    if candidates:
        seed = int(hashlib.sha256(agent_id.encode("utf-8")).hexdigest(), 16)
        offset = seed % len(candidates)
        candidates = candidates[offset:] + candidates[:offset]
    return playback_retry_guard.filter_candidates(candidates)


def direct_entry(agent_id: str, max_attempts: int) -> int:
    ordinary = next_task.eligible_tasks()
    if ordinary:
        claimed = next_task.claim_from_candidates(
            eligible=ordinary,
            agent_id=agent_id,
            requested_task=None,
            max_attempts=max_attempts,
        )
        if claimed:
            task, path = claimed
            emit(
                {
                    "entry_status": "LOCAL_CLAIM_CREATED",
                    "agent_id": agent_id,
                    "task_type": "ordinary_business",
                    "task_id": task["id"],
                    "claim_path": str(path.relative_to(ROOT)),
                    "next_required_action": "Immediately commit/push this exact claim. Work starts only after it is visible on fresh main.",
                }
            )
            return 0

    try:
        eligible_playback, guarded_playback = playback_entry_candidates(agent_id)
        if not eligible_playback:
            guarded_ids = [str(row.get("case_id") or row.get("task_id")) for row in guarded_playback]
            suffix = f" Retry-guarded unchanged cases: {', '.join(guarded_ids)}." if guarded_ids else ""
            raise SystemExit("No autonomous playback case is currently eligible." + suffix)
        chosen = eligible_playback[0]
        case_id = str(chosen["case_id"])
        if chosen.get("claim_exists") and chosen.get("claim_expired"):
            path = playback_queue.reclaim_expired_claim(
                agent_id,
                case_id,
                content_inspection_capable=False,
            )
            claim_action = "expired_claim_reclaimed"
        else:
            path = playback_queue.claim_case(
                agent_id,
                case_id,
                content_inspection_capable=False,
                max_attempts=max_attempts,
            )
            claim_action = "new_claim_created"
    except SystemExit as exc:
        emit(
            {
                "entry_status": "NO_LOCAL_CLAIM",
                "agent_id": agent_id,
                "reason": str(exc),
                "next_required_action": "Refresh main and open PR state; retry only according to CLAIM_PROTOCOL_V2.md.",
            }
        )
        return 1

    claim = json.loads(path.read_text(encoding="utf-8"))
    emit(
        {
            "entry_status": "LOCAL_CLAIM_CREATED",
            "agent_id": agent_id,
            "task_type": "real_playback",
            "task_id": claim["task_id"],
            "case_id": claim["case_id"],
            "claim_action": claim_action,
            "claim_path": str(path.relative_to(ROOT)),
            "next_required_action": "Immediately commit/push this exact claim and any expired-claim archive. Then submit repository-provenance playback requests.",
        }
    )
    return 0


def pr_entry(agent_id: str) -> int:
    ordinary = next_task.eligible_tasks()
    if ordinary:
        task = next_task.candidate_order(ordinary, agent_id, None)[0]
        task_id = task["id"]
    else:
        eligible_playback, guarded_playback = playback_entry_candidates(agent_id)
        if not eligible_playback:
            guarded_ids = [str(row.get("case_id") or row.get("task_id")) for row in guarded_playback]
            emit(
                {
                    "entry_status": "NO_PR_RESERVATION",
                    "agent_id": agent_id,
                    "reason": "No autonomous playback case is currently eligible.",
                    "retry_guarded_cases": guarded_ids,
                }
            )
            return 1
        task_id = eligible_playback[0]["task_id"]
    emit(
        {
            "entry_status": "PR_RESERVATION_REQUIRED",
            "agent_id": agent_id,
            "task_id": task_id,
            "pr_title": f"[TASK {task_id}] autonomous entry — {agent_id}",
            "pr_body_required": [
                f"TASK_ID: {task_id}",
                f"agent_id: {agent_id}",
                "mode: external-pr-worker",
            ],
            "next_required_action": "Create this task PR immediately. Its creation order is the soft-reservation order; if an earlier valid PR exists, refresh and choose another task.",
        }
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomously choose and atomically claim the next Miles-Guo archive task."
    )
    parser.add_argument("--mode", choices=["direct", "pr"], default="direct")
    parser.add_argument("--agent-id")
    parser.add_argument("--max-claim-attempts", type=int, default=10)
    args = parser.parse_args()

    agent_id = load_or_create_agent_id(args.agent_id)
    return (
        direct_entry(agent_id, args.max_claim_attempts)
        if args.mode == "direct"
        else pr_entry(agent_id)
    )


if __name__ == "__main__":
    raise SystemExit(main())
