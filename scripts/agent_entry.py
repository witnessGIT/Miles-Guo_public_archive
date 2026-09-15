#!/usr/bin/env python3
"""Single-command entry for a fresh ordinary Agent session.

This helper intentionally performs only a local atomic claim.  The caller must refresh before
running it and immediately make the resulting claim visible on ``main`` (or create its task PR).
The first claim/reservation that is durably visible in Git is the authoritative first arrival.
"""
from __future__ import annotations

import argparse
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

import next_task
import playback_queue


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
        path = playback_queue.claim_case(
            agent_id,
            None,
            content_inspection_capable=False,
            max_attempts=max_attempts,
        )
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
            "claim_path": str(path.relative_to(ROOT)),
            "next_required_action": "Immediately commit/push this exact claim. Then submit repository-provenance playback requests.",
        }
    )
    return 0


def pr_entry(agent_id: str) -> int:
    ordinary = next_task.eligible_tasks()
    if ordinary:
        task = next_task.candidate_order(ordinary, agent_id, None)[0]
        task_id = task["id"]
    else:
        task = playback_queue.choose_case(agent_id, None)
        task_id = task["task_id"]
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
