#!/usr/bin/env python3
"""Claim, extract, validate and publish a cloud entity-enrichment batch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cloud_asr_batch import claim_is_unavailable, push_with_rebase, run
from cloud_entity_item import process_live

MAX_LOGICAL_BATCH_SIZE = 150
CHECKPOINT_SIZE = 50


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
            if claim_is_unavailable(claims / f"{task_id}.json", cooldown_hours=0):
                raise RuntimeError(f"requested entity task has an active claim: {live_id}")
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
    repo = args.repo.resolve()
    requested_live_ids = [value.strip() for value in args.live_ids.split(",") if value.strip()]
    if len(requested_live_ids) > args.batch_size:
        raise SystemExit("explicit live-id count cannot exceed batch size")
    tasks = eligible(repo, args.batch_size, args.retry_cooldown_hours, requested_live_ids)
    if not tasks:
        print("No eligible entity_pass tasks.")
        return 0

    from mlx_lm import generate, load
    model, tokenizer = load(args.model)

    def generate_text(prompt: str) -> str:
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True,
        )
        return generate(model, tokenizer, prompt=rendered, max_tokens=320, verbose=False)

    total_success = 0
    total_failed = 0
    for checkpoint_number, start in enumerate(
        range(0, len(tasks), CHECKPOINT_SIZE), start=1,
    ):
        checkpoint = tasks[start : start + CHECKPOINT_SIZE]
        claim_paths: list[str] = []
        for task_id, _live_id in checkpoint:
            run([
                sys.executable, "scripts/next_task.py", "--claim", "--task", task_id,
                "--agent-id", args.agent_id,
            ], repo)
            claim_paths.append(f"coordination/claims/{task_id}.json")
        run(["git", "add", *claim_paths], repo)
        run([
            "git", "commit", "-m",
            f"claim: reserve cloud entity checkpoint {checkpoint_number} of {len(checkpoint)}",
        ], repo)
        push_with_rebase(repo)

        success: list[tuple[str, str, list[str], dict]] = []
        failed: list[tuple[str, str, str]] = []
        for task_id, live_id in checkpoint:
            try:
                outputs, stats = process_live(repo, live_id, generate_text)
                success.append((task_id, live_id, outputs, stats))
            except Exception as exc:
                failed.append((task_id, live_id, repr(exc)))

        run([sys.executable, "scripts/build_db.py"], repo)
        run([sys.executable, "scripts/validate_db.py"], repo)
        run([
            sys.executable, "-m", "unittest", "discover", "-s", "tests",
            "-p", "test_*.py", "-q",
        ], repo)

        completion_paths: list[str] = []
        output_paths: list[str] = []
        for task_id, live_id, outputs, stats in success:
            run([
                sys.executable, "scripts/next_task.py", "--finish", task_id,
                "--agent-id", args.agent_id, "--outputs", *outputs,
                "--validation", "Open-source Qwen entity extraction; exact mention substring guard; build_db/validate_db/tests OK; machine status",
            ], repo)
            completion_paths.append(f"coordination/completed/{task_id}.json")
            output_paths.extend(outputs)
            print(json.dumps({"live_id": live_id, **stats}, ensure_ascii=False))
        for task_id, live_id, error in failed:
            print(json.dumps({"live_id": live_id, "error": error}, ensure_ascii=False))
            run([
                sys.executable, "scripts/next_task.py", "--release", task_id,
                "--agent-id", args.agent_id,
                "--reason", "Cloud entity extraction failed; retained for retry",
            ], repo)

        stage = sorted(set(output_paths + completion_paths + claim_paths))
        run(["git", "add", *stage], repo)
        run(["git", "diff", "--cached", "--check"], repo)
        run([
            "git", "commit", "-m",
            f"data: checkpoint cloud entities {checkpoint_number} "
            f"({len(success)} enriched, {len(failed)} retryable)",
        ], repo)
        push_with_rebase(repo)
        total_success += len(success)
        total_failed += len(failed)

    return 0 if total_success else 2


if __name__ == "__main__":
    raise SystemExit(main())
