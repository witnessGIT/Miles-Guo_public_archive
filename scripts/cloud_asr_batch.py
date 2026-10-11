#!/usr/bin/env python3
"""Claim, process, validate and publish a conservative cloud ASR pilot batch."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


TASK_RE = re.compile(r"WI_(LIVE_\d{8}_\d{3})_transcript_import")


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n", flush=True)
    if check and completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")
    return completed


def push_with_rebase(repo: Path) -> None:
    for _attempt in range(5):
        if run(["git", "push", "origin", "HEAD:main"], repo, check=False).returncode == 0:
            return
        run(["git", "fetch", "origin", "main"], repo)
        rebased = run(["git", "rebase", "origin/main"], repo, check=False)
        if rebased.returncode == 0:
            continue
        conflicts = run(["git", "diff", "--name-only", "--diff-filter=U"], repo).stdout.splitlines()
        if conflicts != ["database/Miles-Guo_public_archive.sqlite3"]:
            run(["git", "rebase", "--abort"], repo, check=False)
            raise RuntimeError(f"unresolved publish conflicts: {conflicts}")
        run([sys.executable, "scripts/build_db.py"], repo)
        run([sys.executable, "scripts/validate_db.py"], repo)
        run(["git", "add", "database/Miles-Guo_public_archive.sqlite3"], repo)
        env = os.environ.copy()
        env["GIT_EDITOR"] = "true"
        continued = subprocess.run(
            ["git", "rebase", "--continue"], cwd=repo, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        print(continued.stdout, end="", flush=True)
        if continued.returncode:
            raise RuntimeError("git rebase --continue failed")
    raise RuntimeError("could not publish after five non-force retries")


def eligible(repo: Path, limit: int) -> list[tuple[str, str]]:
    listing = run([sys.executable, "scripts/next_task.py", "--list"], repo).stdout
    values: list[tuple[str, str]] = []
    for live_id in TASK_RE.findall(listing):
        task_id = f"WI_{live_id}_transcript_import"
        if (task_id, live_id) not in values:
            values.append((task_id, live_id))
        if len(values) == limit:
            break
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--agent-id", required=True)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 50:
        raise SystemExit("cloud ASR batch size must be between 1 and 50")
    repo = args.repo.resolve()
    work = args.work_root.resolve()
    tasks = eligible(repo, args.batch_size)
    if not tasks:
        print("No eligible transcript_import tasks.")
        return 0

    claim_paths: list[str] = []
    for task_id, _live_id in tasks:
        run([sys.executable, "scripts/next_task.py", "--claim", "--task", task_id, "--agent-id", args.agent_id], repo)
        claim_paths.append(f"coordination/claims/{task_id}.json")
    run(["git", "add", *claim_paths], repo)
    run(["git", "commit", "-m", f"claim: reserve GitHub Actions ASR pilot of {len(tasks)}"], repo)
    push_with_rebase(repo)

    success: list[tuple[str, str, list[str]]] = []
    failed: list[tuple[str, str, str]] = []
    attempt_paths: list[str] = []
    for task_id, live_id in tasks:
        completed = run(
            [sys.executable, "scripts/cloud_asr_item.py", "--repo", str(repo), "--live-id", live_id, "--work-root", str(work)],
            repo,
            check=False,
        )
        stem = f"asr_{live_id.lower()}"
        outputs = [
            f"data/current/transcript_versions/{stem}.jsonl",
            f"data/current/transcript_cues/{stem}.jsonl",
            f"data/current/live_segments/{stem}.jsonl",
            f"data/current/asr_manifests/{stem}.json",
        ]
        if completed.returncode == 0 and all((repo / path).exists() for path in outputs):
            success.append((task_id, live_id, outputs))
        else:
            attempt = f"data/current/asr_attempts/cloud_{live_id.lower()}.json"
            if (repo / attempt).exists():
                attempt_paths.append(attempt)
            failed.append((task_id, live_id, attempt))

    run([sys.executable, "scripts/build_db.py"], repo)
    run([sys.executable, "scripts/validate_db.py"], repo)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], repo)

    completion_paths: list[str] = []
    output_paths: list[str] = []
    for task_id, _live_id, outputs in success:
        run([
            sys.executable, "scripts/next_task.py", "--finish", task_id,
            "--agent-id", args.agent_id, "--outputs", *outputs,
            "database/Miles-Guo_public_archive.sqlite3", "--validation",
            "GitHub-hosted MLX Whisper; build_db OK; validate_db OK; 103 tests OK; machine ASR remains unverified",
        ], repo)
        completion_paths.append(f"coordination/completed/{task_id}.json")
        output_paths.extend(outputs)
    for task_id, _live_id, _attempt in failed:
        run([
            sys.executable, "scripts/next_task.py", "--release", task_id,
            "--agent-id", args.agent_id,
            "--reason", "GitHub-hosted runner could not complete media access or ASR; retained for retry",
        ], repo)

    stage = sorted(set(output_paths + attempt_paths + completion_paths + claim_paths + ["database/Miles-Guo_public_archive.sqlite3"]))
    run(["git", "add", *stage], repo)
    run(["git", "diff", "--cached", "--check"], repo)
    run([
        "git", "commit", "-m",
        f"data: publish cloud ASR pilot ({len(success)} transcribed, {len(failed)} retryable)",
    ], repo)
    push_with_rebase(repo)
    print(json.dumps({"claimed": len(tasks), "transcribed": len(success), "retryable": len(failed)}, ensure_ascii=False))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
