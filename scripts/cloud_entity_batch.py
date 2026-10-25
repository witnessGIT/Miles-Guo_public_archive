#!/usr/bin/env python3
"""Claim, extract, validate and publish a cloud entity-enrichment batch."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cloud_asr_batch import claim_is_unavailable, push_with_rebase, run

MAX_LOGICAL_BATCH_SIZE = 150


def eligible(
    repo: Path, limit: int, retry_cooldown_hours: int = 24,
    requested_live_ids: list[str] | None = None,
) -> list[tuple[str, str]]:
    completed = repo / "coordination" / "completed"
    claims = repo / "coordination" / "claims"
    if requested_live_ids:
        values: list[tuple[str, str]] = []
        for live_id in requested_live_ids:
            task_id = f"WI_{live_id}_entity_pass"
            if not (completed / f"WI_{live_id}_segment_split.json").exists():
                raise RuntimeError(f"requested entity task is not currently eligible: {live_id}")
            if (completed / f"{task_id}.json").exists():
                continue
            claim_path = claims / f"{task_id}.json"
            if claim_is_unavailable(claim_path, cooldown_hours=0):
                raise RuntimeError(f"requested entity task has an active claim: {live_id}")
            if claim_is_unavailable(claim_path, retry_cooldown_hours):
                continue
            values.append((task_id, live_id))
        return values[:limit]
    values: list[tuple[str, str]] = []
    for segment_done in sorted(completed.glob("WI_LIVE_*_segment_split.json")):
        live_id = segment_done.stem.removeprefix("WI_").removesuffix("_segment_split")
        task_id = f"WI_{live_id}_entity_pass"
        if (completed / f"{task_id}.json").exists() or claim_is_unavailable(
            claims / f"{task_id}.json", retry_cooldown_hours,
        ):
            continue
        values.append((task_id, live_id))
        if len(values) == limit:
            break
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=MAX_LOGICAL_BATCH_SIZE)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--model", default="mlx-community/Qwen2.5-7B-Instruct-4bit")
    parser.add_argument("--retry-cooldown-hours", type=int, default=24)
    parser.add_argument(
        "--max-runtime-minutes", type=int, default=270,
        help="Stop cleanly between videos before the GitHub job timeout",
    )
    parser.add_argument(
        "--item-timeout-sec", type=int, default=2700,
        help="Maximum isolated inference time per livestream before releasing its claim",
    )
    parser.add_argument(
        "--live-ids", default="",
        help="Optional comma-separated LIVE ids shared with the key-point batch",
    )
    args = parser.parse_args()
    if not 1 <= args.batch_size <= MAX_LOGICAL_BATCH_SIZE:
        raise SystemExit(
            f"cloud entity pilot batch size must be between 1 and {MAX_LOGICAL_BATCH_SIZE}"
        )
    if not 0 <= args.retry_cooldown_hours <= 168:
        raise SystemExit("entity retry cooldown must be between 0 and 168 hours")
    if not 300 <= args.item_timeout_sec <= 7200:
        raise SystemExit("entity item timeout must be between 300 and 7200 seconds")
    if not 30 <= args.max_runtime_minutes <= 330:
        raise SystemExit("entity runtime budget must be between 30 and 330 minutes")
    repo = args.repo.resolve()
    requested_live_ids = [value.strip() for value in args.live_ids.split(",") if value.strip()]
    if len(requested_live_ids) > args.batch_size:
        raise SystemExit("explicit live-id count cannot exceed batch size")
    tasks = eligible(repo, args.batch_size, args.retry_cooldown_hours, requested_live_ids)
    if not tasks:
        print("No eligible entity_pass tasks.")
        return 0

    started_at = time.monotonic()
    total_success = 0
    total_failed = 0
    processed_count = 0
    with tempfile.TemporaryDirectory(prefix="miles-entities-") as temporary:
        result_root = Path(temporary)
        for task_id, live_id in tasks:
            elapsed_minutes = (time.monotonic() - started_at) / 60
            if processed_count and elapsed_minutes >= args.max_runtime_minutes:
                print(json.dumps({
                    "checkpoint_stop": "runtime_budget_reached",
                    "processed": processed_count,
                    "remaining": len(tasks) - processed_count,
                    "elapsed_minutes": round(elapsed_minutes, 1),
                }, ensure_ascii=False))
                break

            claim_paths = [f"coordination/claims/{task_id}.json"]
            run([
                sys.executable, "scripts/next_task.py", "--claim", "--task", task_id,
                "--agent-id", args.agent_id,
            ], repo)
            run(["git", "add", *claim_paths], repo)
            run(["git", "commit", "-m", f"claim: reserve cloud entity task {task_id}"], repo)
            push_with_rebase(repo)

            result_path = result_root / f"{live_id}.json"
            try:
                completed = run([
                    sys.executable, "scripts/cloud_entity_runner.py",
                    "--repo", str(repo), "--live-id", live_id,
                    "--model", args.model, "--result", str(result_path),
                ], repo, check=False, timeout=args.item_timeout_sec)
                timed_out = False
            except subprocess.TimeoutExpired:
                completed = None
                timed_out = True

            accepted = completed is not None and completed.returncode == 0 and result_path.exists()
            result = json.loads(result_path.read_text(encoding="utf-8")) if accepted else None

            run([sys.executable, "scripts/build_db.py"], repo)
            run([sys.executable, "scripts/validate_db.py"], repo)
            run([
                sys.executable, "-m", "unittest", "discover", "-s", "tests",
                "-p", "test_*.py", "-q",
            ], repo)

            stage = [*claim_paths]
            if result is not None:
                outputs = result["outputs"]
                stats = result["stats"]
                run([
                    sys.executable, "scripts/next_task.py", "--finish", task_id,
                    "--agent-id", args.agent_id, "--outputs", *outputs,
                    "--validation", "Open-source Qwen entity extraction; exact mention substring guard; build_db/validate_db/tests OK; machine status",
                ], repo)
                stage.append(f"coordination/completed/{task_id}.json")
                stage.extend(outputs)
                total_success += 1
                print(json.dumps({"live_id": live_id, **stats}, ensure_ascii=False))
            else:
                error = (
                    f"isolated entity worker timed out after {args.item_timeout_sec} seconds"
                    if timed_out
                    else (completed.stdout or "isolated entity worker failed")[-2000:].strip()
                )
                total_failed += 1
                print(json.dumps({"live_id": live_id, "error": error}, ensure_ascii=False))
                reason = (
                    f"Cloud entity inference timed out after {args.item_timeout_sec} seconds; retained for retry"
                    if timed_out
                    else "Cloud entity extraction failed; retained for retry"
                )
                run([
                    sys.executable, "scripts/next_task.py", "--release", task_id,
                    "--agent-id", args.agent_id, "--reason", reason,
                ], repo)

            processed_count += 1
            run(["git", "add", *sorted(set(stage))], repo)
            run(["git", "diff", "--cached", "--check"], repo)
            run(["git", "commit", "-m", f"data: checkpoint cloud entities {live_id}"], repo)
            push_with_rebase(repo)

    print(json.dumps({
        "requested": len(tasks),
        "processed": processed_count,
        "enriched": total_success,
        "retryable": total_failed,
    }, ensure_ascii=False))
    return 0 if total_success or (processed_count and not total_failed) else 2


if __name__ == "__main__":
    raise SystemExit(main())
