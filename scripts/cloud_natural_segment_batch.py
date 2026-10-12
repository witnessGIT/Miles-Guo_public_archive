#!/usr/bin/env python3
"""Validate existing ASR cues, build natural passages, and publish a claimed batch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from build_natural_segments import process_live
    from cloud_asr_batch import push_with_rebase, run
except ModuleNotFoundError:  # Imported as scripts.cloud_natural_segment_batch in tests/tools.
    from scripts.build_natural_segments import process_live
    from scripts.cloud_asr_batch import push_with_rebase, run


def eligible(repo: Path, limit: int) -> list[str]:
    completed = repo / "coordination" / "completed"
    claims = repo / "coordination" / "claims"
    values: list[str] = []
    for transcript_done in sorted(completed.glob("WI_LIVE_*_transcript_import.json")):
        live_id = transcript_done.stem.removeprefix("WI_").removesuffix("_transcript_import")
        cue_task = f"WI_{live_id}_cue_split"
        segment_task = f"WI_{live_id}_segment_split"
        cue_path = repo / "data" / "current" / "transcript_cues" / f"asr_{live_id.lower()}.jsonl"
        if not cue_path.exists() or (completed / f"{segment_task}.json").exists():
            continue
        if (claims / f"{cue_task}.json").exists() or (claims / f"{segment_task}.json").exists():
            continue
        values.append(live_id)
        if len(values) == limit:
            break
    return values


def claim_tasks(repo: Path, task_ids: list[str], agent_id: str, label: str) -> list[str]:
    paths: list[str] = []
    for task_id in task_ids:
        run([sys.executable, "scripts/next_task.py", "--claim", "--task", task_id, "--agent-id", agent_id], repo)
        paths.append(f"coordination/claims/{task_id}.json")
    run(["git", "add", *paths], repo)
    run(["git", "commit", "-m", f"claim: reserve {label} batch of {len(task_ids)}"], repo)
    push_with_rebase(repo)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--agent-id", required=True)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        raise SystemExit("natural-segmentation batch size must be between 1 and 100")
    repo = args.repo.resolve()
    live_ids = eligible(repo, args.batch_size)
    if not live_ids:
        print("No eligible cue/segment tasks.")
        return 0

    cue_tasks = [f"WI_{live_id}_cue_split" for live_id in live_ids]
    cue_claims = claim_tasks(repo, cue_tasks, args.agent_id, "ASR cue validation")
    cue_completions: list[str] = []
    for task_id, live_id in zip(cue_tasks, live_ids):
        cue_path = f"data/current/transcript_cues/asr_{live_id.lower()}.jsonl"
        run([
            sys.executable, "scripts/next_task.py", "--finish", task_id,
            "--agent-id", args.agent_id, "--outputs", cue_path,
            "--validation", "Timestamped ASR cue file exists; source ASR remains machine/unverified",
        ], repo)
        cue_completions.append(f"coordination/completed/{task_id}.json")
    run(["git", "add", *cue_claims, *cue_completions], repo)
    run(["git", "commit", "-m", f"data: validate timestamped cues for {len(live_ids)} lives"], repo)
    push_with_rebase(repo)

    segment_tasks = [f"WI_{live_id}_segment_split" for live_id in live_ids]
    segment_claims = claim_tasks(repo, segment_tasks, args.agent_id, "natural segmentation")
    outputs: list[str] = []
    completions: list[str] = []
    failed: list[tuple[str, str, str]] = []
    for task_id, live_id in zip(segment_tasks, live_ids):
        try:
            path, cue_count, segment_count = process_live(live_id, repo)
            outputs.append(str(path.relative_to(repo)))
            print(json.dumps({"live_id": live_id, "cues": cue_count, "natural_segments": segment_count}, ensure_ascii=False))
        except Exception as exc:
            failed.append((task_id, live_id, repr(exc)))

    run([sys.executable, "scripts/build_db.py"], repo)
    run([sys.executable, "scripts/validate_db.py"], repo)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"], repo)

    successful_ids = set(live_ids) - {live_id for _task_id, live_id, _error in failed}
    for task_id, live_id in zip(segment_tasks, live_ids):
        if live_id not in successful_ids:
            continue
        output = f"data/current/live_segments/asr_{live_id.lower()}.jsonl"
        run([
            sys.executable, "scripts/next_task.py", "--finish", task_id,
            "--agent-id", args.agent_id, "--outputs", output,
            "--validation", "Natural ASR passage boundaries; build_db/validate_db/full tests OK; machine status",
        ], repo)
        completions.append(f"coordination/completed/{task_id}.json")
    for task_id, live_id, error in failed:
        print(json.dumps({"live_id": live_id, "error": error}, ensure_ascii=False))
        run([sys.executable, "scripts/next_task.py", "--release", task_id, "--agent-id", args.agent_id, "--reason", "Natural segmentation failed; retained for retry"], repo)

    run(["git", "add", *sorted(set(segment_claims + outputs + completions))], repo)
    run(["git", "diff", "--cached", "--check"], repo)
    run(["git", "commit", "-m", f"data: publish natural segments ({len(successful_ids)} completed, {len(failed)} retryable)"], repo)
    push_with_rebase(repo)
    return 0 if successful_ids else 2


if __name__ == "__main__":
    raise SystemExit(main())
