#!/usr/bin/env python3
"""Claim, extract, validate and publish a cloud key-point pilot batch."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from cloud_asr_batch import claim_is_unavailable, push_with_rebase, run


def eligible(
    repo: Path, limit: int, retry_cooldown_hours: int = 24,
    requested_live_ids: list[str] | None = None,
) -> list[tuple[str, str]]:
    completed = repo / "coordination" / "completed"
    claims = repo / "coordination" / "claims"
    if requested_live_ids:
        values: list[tuple[str, str]] = []
        for live_id in requested_live_ids:
            task_id = f"WI_{live_id}_key_points_topics"
            segment_done = completed / f"WI_{live_id}_segment_split.json"
            if not segment_done.exists() or (completed / f"{task_id}.json").exists():
                raise RuntimeError(f"requested key-point task is not currently eligible: {live_id}")
            if claim_is_unavailable(claims / f"{task_id}.json", cooldown_hours=0):
                raise RuntimeError(f"requested key-point task has an active claim: {live_id}")
            values.append((task_id, live_id))
        return values[:limit]
    values: list[tuple[str, str]] = []
    for segment_done in sorted(completed.glob("WI_LIVE_*_segment_split.json")):
        live_id = segment_done.stem.removeprefix("WI_").removesuffix("_segment_split")
        task_id = f"WI_{live_id}_key_points_topics"
        if (completed / f"{task_id}.json").exists() or claim_is_unavailable(
            claims / f"{task_id}.json", retry_cooldown_hours,
        ):
            continue
        values.append((task_id, live_id))
        if len(values) == limit:
            break
    return values


def completed_with_empty_output(repo: Path, limit: int) -> list[tuple[str, str]]:
    completed = repo / "coordination" / "completed"
    values: list[tuple[str, str]] = []
    for done in sorted(completed.glob("WI_LIVE_*_key_points_topics.json")):
        live_id = done.stem.removeprefix("WI_").removesuffix("_key_points_topics")
        output = repo / "data" / "current" / "segment_key_points" / f"machine_{live_id.lower()}.jsonl"
        if output.exists() and output.stat().st_size > 0:
            continue
        try:
            completion = json.loads(done.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            completion = {}
        result_stats = completion.get("result_stats", {})
        if (
            result_stats.get("outcome") == "no_substantive_content"
            and result_stats.get("extraction_method") == "qwen2.5-7b-instruct-4bit-grounded-keypoints-v4-forced-retry"
        ):
            continue
        values.append((done.stem, live_id))
        if len(values) == limit:
            break
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--model", default="mlx-community/Qwen2.5-7B-Instruct-4bit")
    parser.add_argument("--reprocess-live-id", default="")
    parser.add_argument("--reprocess-empty", action="store_true")
    parser.add_argument("--retry-cooldown-hours", type=int, default=24)
    parser.add_argument(
        "--live-ids", default="",
        help="Optional comma-separated eligible LIVE ids to retry explicitly",
    )
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 10:
        raise SystemExit("cloud key-point pilot batch size must be between 1 and 10")
    if not 0 <= args.retry_cooldown_hours <= 168:
        raise SystemExit("key-point retry cooldown must be between 0 and 168 hours")
    repo = args.repo.resolve()
    reprocess_live_id = args.reprocess_live_id.strip()
    requested_live_ids = [value.strip() for value in args.live_ids.split(",") if value.strip()]
    if len(requested_live_ids) > args.batch_size:
        raise SystemExit("explicit live-id count cannot exceed batch size")
    if requested_live_ids and (reprocess_live_id or args.reprocess_empty):
        raise SystemExit("explicit retries cannot be combined with reprocessing")
    if reprocess_live_id and args.reprocess_empty:
        raise SystemExit("choose either --reprocess-live-id or --reprocess-empty")
    reprocessing = bool(reprocess_live_id or args.reprocess_empty)
    if reprocess_live_id:
        tasks = [(f"WI_{reprocess_live_id}_key_points_topics", reprocess_live_id)]
    elif args.reprocess_empty:
        tasks = completed_with_empty_output(repo, args.batch_size)
    else:
        tasks = eligible(repo, args.batch_size, args.retry_cooldown_hours, requested_live_ids)
    if not tasks:
        print("No eligible key_points_topics tasks.")
        return 0

    claim_paths: list[str] = []
    if not reprocessing:
        for task_id, _live_id in tasks:
            run([sys.executable, "scripts/next_task.py", "--claim", "--task", task_id, "--agent-id", args.agent_id], repo)
            claim_paths.append(f"coordination/claims/{task_id}.json")
        run(["git", "add", *claim_paths], repo)
        run(["git", "commit", "-m", f"claim: reserve cloud key-point pilot of {len(tasks)}"], repo)
        push_with_rebase(repo)

    success: list[tuple[str, str, list[str], dict]] = []
    failed: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory(prefix="miles-keypoints-") as temporary:
        result_root = Path(temporary)
        for task_id, live_id in tasks:
            result_path = result_root / f"{live_id}.json"
            completed = run([
                sys.executable, "scripts/cloud_keypoint_runner.py",
                "--repo", str(repo), "--live-id", live_id,
                "--model", args.model, "--result", str(result_path),
            ], repo, check=False)
            if completed.returncode == 0 and result_path.exists():
                result = json.loads(result_path.read_text(encoding="utf-8"))
                success.append((task_id, live_id, result["outputs"], result["stats"]))
            else:
                error = (completed.stdout or "isolated key-point worker failed")[-2000:].strip()
                failed.append((task_id, live_id, error))

    run([sys.executable, "scripts/build_db.py"], repo)
    run([sys.executable, "scripts/validate_db.py"], repo)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"], repo)

    stage = [*claim_paths]
    for task_id, live_id, outputs, stats in success:
        if not reprocessing:
            validation = (
                "No substantive content identified after all natural segments returned no key points; "
                "build_db/validate_db/full tests OK; machine status"
                if stats.get("outcome") == "no_substantive_content"
                else "Evidence-quote-grounded variable-count key points; controlled topics; "
                "build_db/validate_db/full tests OK; machine status"
            )
            run([sys.executable, "scripts/next_task.py", "--finish", task_id, "--agent-id", args.agent_id, "--outputs", *outputs, "--validation", validation], repo)
            stage.append(f"coordination/completed/{task_id}.json")
        elif args.reprocess_empty:
            completion_path = repo / "coordination" / "completed" / f"{task_id}.json"
            completion = json.loads(completion_path.read_text(encoding="utf-8"))
            completion["result_stats"] = stats
            completion["validation"] = (
                "Reprocessed empty output; no substantive content identified by the model"
                if stats.get("outcome") == "no_substantive_content"
                else "Reprocessed empty output with evidence-grounded variable-count key points"
            )
            completion_path.write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            stage.append(str(completion_path.relative_to(repo)))
        stage.extend(outputs)
        print(json.dumps({"live_id": live_id, **stats}, ensure_ascii=False))
    for task_id, live_id, error in failed:
        print(json.dumps({"live_id": live_id, "error": error}, ensure_ascii=False))
        if not reprocessing:
            run([sys.executable, "scripts/next_task.py", "--release", task_id, "--agent-id", args.agent_id, "--reason", "Cloud key-point extraction failed; retained for retry"], repo)

    if not stage:
        print("No key-point output was accepted; no repository changes to publish.")
        return 2
    run(["git", "add", *sorted(set(stage))], repo)
    run(["git", "diff", "--cached", "--check"], repo)
    message = (
        f"data: reprocess variable key points for {reprocess_live_id}"
        if reprocess_live_id
        else f"data: repair empty key-point outputs ({len(success)} repaired, {len(failed)} retryable)"
        if args.reprocess_empty
        else f"data: publish cloud key-point pilot ({len(success)} enriched, {len(failed)} retryable)"
    )
    run(["git", "commit", "-m", message], repo)
    push_with_rebase(repo)
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
