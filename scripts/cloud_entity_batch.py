#!/usr/bin/env python3
"""Claim, extract, validate and publish a cloud entity-enrichment batch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cloud_asr_batch import push_with_rebase, run
from cloud_entity_item import process_live


def eligible(repo: Path, limit: int) -> list[tuple[str, str]]:
    completed = repo / "coordination" / "completed"
    claims = repo / "coordination" / "claims"
    values: list[tuple[str, str]] = []
    for segment_done in sorted(completed.glob("WI_LIVE_*_segment_split.json")):
        live_id = segment_done.stem.removeprefix("WI_").removesuffix("_segment_split")
        task_id = f"WI_{live_id}_entity_pass"
        if (completed / f"{task_id}.json").exists() or (claims / f"{task_id}.json").exists():
            continue
        values.append((task_id, live_id))
        if len(values) == limit:
            break
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--model", default="mlx-community/Qwen2.5-7B-Instruct-4bit")
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 10:
        raise SystemExit("cloud entity pilot batch size must be between 1 and 10")
    repo = args.repo.resolve()
    tasks = eligible(repo, args.batch_size)
    if not tasks:
        print("No eligible entity_pass tasks.")
        return 0

    claim_paths: list[str] = []
    for task_id, _live_id in tasks:
        run([sys.executable, "scripts/next_task.py", "--claim", "--task", task_id, "--agent-id", args.agent_id], repo)
        claim_paths.append(f"coordination/claims/{task_id}.json")
    run(["git", "add", *claim_paths], repo)
    run(["git", "commit", "-m", f"claim: reserve cloud entity pilot of {len(tasks)}"], repo)
    push_with_rebase(repo)

    from mlx_lm import generate, load
    model, tokenizer = load(args.model)

    def generate_text(prompt: str) -> str:
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True,
        )
        return generate(model, tokenizer, prompt=rendered, max_tokens=320, verbose=False)

    success: list[tuple[str, str, list[str], dict]] = []
    failed: list[tuple[str, str, str]] = []
    for task_id, live_id in tasks:
        try:
            outputs, stats = process_live(repo, live_id, generate_text)
            success.append((task_id, live_id, outputs, stats))
        except Exception as exc:
            failed.append((task_id, live_id, repr(exc)))

    run([sys.executable, "scripts/build_db.py"], repo)
    run([sys.executable, "scripts/validate_db.py"], repo)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"], repo)

    completion_paths: list[str] = []
    output_paths: list[str] = []
    for task_id, _live_id, outputs, stats in success:
        run([
            sys.executable, "scripts/next_task.py", "--finish", task_id,
            "--agent-id", args.agent_id, "--outputs", *outputs,
            "database/Miles-Guo_public_archive.sqlite3", "--validation",
            "Open-source Qwen entity extraction; exact mention substring guard; build_db/validate_db/tests OK; machine status",
        ], repo)
        completion_paths.append(f"coordination/completed/{task_id}.json")
        output_paths.extend(outputs)
        print(json.dumps({"live_id": _live_id, **stats}, ensure_ascii=False))
    for task_id, _live_id, error in failed:
        print(json.dumps({"live_id": _live_id, "error": error}, ensure_ascii=False))
        run([sys.executable, "scripts/next_task.py", "--release", task_id, "--agent-id", args.agent_id, "--reason", "Cloud entity extraction failed; retained for retry"], repo)

    stage = sorted(set(output_paths + completion_paths + claim_paths + ["database/Miles-Guo_public_archive.sqlite3"]))
    run(["git", "add", *stage], repo)
    run(["git", "diff", "--cached", "--check"], repo)
    run(["git", "commit", "-m", f"data: publish cloud entity pilot ({len(success)} enriched, {len(failed)} retryable)"], repo)
    push_with_rebase(repo)
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
