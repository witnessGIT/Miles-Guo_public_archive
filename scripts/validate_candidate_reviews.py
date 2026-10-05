#!/usr/bin/env python3
"""Validate all candidate-review completions governed by evidence contract v2."""
from __future__ import annotations

import json
from pathlib import Path

import next_task


def main() -> int:
    failures: list[str] = []
    lease_warnings: list[dict] = []
    checked = 0
    grandfather_path = next_task.ROOT / "coordination" / "candidate_review_grandfathered.json"
    grandfather_payload = next_task.load_json_path(grandfather_path) or {}
    grandfathered = {
        str(task_id) for task_id in grandfather_payload.get("task_ids", []) if str(task_id)
    }
    batches: dict[str, list[tuple[Path, dict]]] = {}
    for path in sorted(next_task.CLAIMS.glob("*.json")):
        payload = next_task.load_json_path(path)
        if not payload or payload.get("candidate_review_contract") != next_task.CANDIDATE_REVIEW_CONTRACT:
            continue
        effective_hours = next_task.claim_lease_hours(payload)
        if effective_hours != next_task.CANDIDATE_REVIEW_CLAIM_TIMEOUT_HOURS:
            failures.append(f"{path.relative_to(next_task.ROOT)}: invalid effective C2 lease")
        # Legacy metadata stays immutable. Report discrepancies, but enforce
        # the same fixed policy used by scheduling and the expiry display.
        for field in ("review_claim_timeout_hours", "static_claim_lease_hours"):
            if field not in payload:
                continue
            value = payload[field]
            try:
                consistent = not isinstance(value, bool) and float(value) == effective_hours
            except (TypeError, ValueError, OverflowError):
                consistent = False
            if not consistent:
                lease_warnings.append({
                    "path": str(path.relative_to(next_task.ROOT)),
                    "field": field,
                    "declared_value": value,
                    "effective_hours": effective_hours,
                })
        batch_id = str(payload.get("review_batch_id") or "")
        if not batch_id:
            failures.append(f"{path.relative_to(next_task.ROOT)}: missing review_batch_id")
            continue
        batches.setdefault(batch_id, []).append((path, payload))

    for batch_id, members in batches.items():
        modes = {payload.get("entry_mode") for _path, payload in members}
        if len(modes) != 1 or next(iter(modes)) not in {"work", "ordinary_chat"}:
            failures.append(f"batch {batch_id}: inconsistent or invalid entry_mode")
            continue
        mode = next(iter(modes))
        expected = (
            next_task.CANDIDATE_REVIEW_BATCH_SIZE
            if mode == "work"
            else next_task.CANDIDATE_REVIEW_CHAT_BATCH_SIZE
        )
        if len(members) != expected:
            failures.append(f"batch {batch_id}: has {len(members)} claims, expected {expected}")
        positions = {payload.get("review_batch_position") for _path, payload in members}
        if positions != set(range(1, expected + 1)):
            failures.append(f"batch {batch_id}: positions are not exactly 1..{expected}")
        for path, payload in members:
            if payload.get("review_batch_target_size") != expected:
                failures.append(f"{path.relative_to(next_task.ROOT)}: invalid batch target")
            if payload.get("review_batch_claimed_count") != expected:
                failures.append(f"{path.relative_to(next_task.ROOT)}: invalid claimed count")

    completion_records: list[tuple[Path, dict]] = []
    for path in sorted(next_task.COMPLETED.glob("*.json")):
        payload = next_task.load_json_path(path)
        if payload:
            completion_records.append((path, payload))
    for path in sorted(next_task.CLAIMS.glob("*.json")):
        payload = next_task.load_json_path(path)
        if payload and str(payload.get("status") or "").lower() == "completed":
            completion_records.append((path, payload))

    seen_completion_tasks: set[str] = set()
    for path, payload in completion_records:
        task_id = str(payload.get("task_id") or "")
        if not task_id.startswith(next_task.CANDIDATE_REVIEW_PREFIX):
            continue
        if task_id in seen_completion_tasks:
            continue
        seen_completion_tasks.add(task_id)
        if task_id in grandfathered:
            continue
        if payload.get("candidate_review_contract") != next_task.CANDIDATE_REVIEW_CONTRACT:
            failures.append(
                f"{path.relative_to(next_task.ROOT)}: non-grandfathered candidate completion "
                f"must use {next_task.CANDIDATE_REVIEW_CONTRACT}"
            )
            continue
        checked += 1
        try:
            artifact_path, artifact = next_task.validate_candidate_review_artifact(
                payload, list(payload.get("outputs") or [])
            )
        except SystemExit as exc:
            failures.append(f"{path.relative_to(next_task.ROOT)}: {exc}")
            continue
        if payload.get("review_artifact") != artifact_path:
            failures.append(f"{path.relative_to(next_task.ROOT)}: review_artifact path mismatch")
        if payload.get("review_decision") != artifact.get("decision"):
            failures.append(f"{path.relative_to(next_task.ROOT)}: review_decision mismatch")

    if failures:
        print(json.dumps({"status": "FAIL", "checked": checked, "errors": failures}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "checked": checked, "batches": len(batches), "lease_warnings": lease_warnings}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
