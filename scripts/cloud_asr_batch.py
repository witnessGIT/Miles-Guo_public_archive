#!/usr/bin/env python3
"""Claim, process, validate and publish a conservative cloud ASR pilot batch."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


TASK_RE = re.compile(r"WI_(LIVE_\d{8}_\d{3})_transcript_import")
DEFERRED_STATUS = "cloud_checkpoint_retry_limit_deferred"
CHECKPOINT_RETRY_LIMIT = 2


def attempt_path(repo: Path, live_id: str) -> Path:
    return repo / "data" / "current" / "asr_attempts" / f"cloud_{live_id.lower()}.json"


def read_attempt(repo: Path, live_id: str) -> dict[str, object]:
    path = attempt_path(repo, live_id)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def attempt_is_deferred(repo: Path, live_id: str) -> bool:
    payload = read_attempt(repo, live_id)
    return (
        payload.get("status") == DEFERRED_STATUS
        or payload.get("deferred_until_corpus_tail") is True
    )


def record_failed_resume(
    repo: Path, live_id: str, previous_retry_count: int, resume_timed_out: bool,
) -> tuple[int, bool]:
    """Record a failed resume and defer it after two actual checkpoint timeouts."""
    path = attempt_path(repo, live_id)
    payload = read_attempt(repo, live_id)
    count = previous_retry_count + (1 if resume_timed_out else 0)
    already_deferred = attempt_is_deferred(repo, live_id)
    deferred = already_deferred or count >= CHECKPOINT_RETRY_LIMIT
    payload.update({
        "schema_version": "cloud-asr-attempt-v1",
        "live_id": live_id,
        "checkpoint_retry_count": count,
        "checkpoint_retry_limit": CHECKPOINT_RETRY_LIMIT,
        "deferred_until_corpus_tail": deferred,
        "retry_queue": "corpus_tail" if deferred else "normal",
    })
    if deferred and not already_deferred:
        payload["pre_defer_status"] = payload.get("status")
        payload["status"] = DEFERRED_STATUS
        payload["deferred_reason"] = (
            "two checkpoint resume attempts did not complete; released so the "
            "normal queue can continue and retained for corpus-tail retry"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return count, deferred


def run(
    command: list[str], cwd: Path, check: bool = True, timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=timeout,
    )
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
        rebased = run(["git", "rebase", "--autostash", "origin/main"], repo, check=False)
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


def attempt_is_cooling_down(repo: Path, live_id: str, cooldown_hours: int) -> bool:
    if cooldown_hours <= 0:
        return False
    path = attempt_path(repo, live_id)
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        generated_at = str(payload.get("generated_at") or "").replace("Z", "+00:00")
        attempted_at = datetime.fromisoformat(generated_at)
        if attempted_at.tzinfo is None:
            attempted_at = attempted_at.replace(tzinfo=timezone.utc)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False
    return datetime.now(timezone.utc) - attempted_at < timedelta(hours=cooldown_hours)


def claim_is_unavailable(path: Path, cooldown_hours: int = 24) -> bool:
    """Return whether a claim is active or was released too recently to retry."""
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    status = str(payload.get("status") or "in_progress").lower()
    if status == "in_progress":
        claimed_at_text = str(payload.get("claimed_at") or "").replace("Z", "+00:00")
        try:
            claimed_at = datetime.fromisoformat(claimed_at_text)
            if claimed_at.tzinfo is None:
                claimed_at = claimed_at.replace(tzinfo=timezone.utc)
            lease_hours = float(payload.get("static_claim_lease_hours") or 24)
            return datetime.now(timezone.utc) - claimed_at < timedelta(hours=lease_hours)
        except (ValueError, TypeError):
            return True
    if status != "released" or cooldown_hours <= 0:
        return False
    released_at_text = str(payload.get("released_at") or "").replace("Z", "+00:00")
    try:
        released_at = datetime.fromisoformat(released_at_text)
        if released_at.tzinfo is None:
            released_at = released_at.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False
    return datetime.now(timezone.utc) - released_at < timedelta(hours=cooldown_hours)


def eligible(
    repo: Path, limit: int, retry_cooldown_hours: int = 24,
    requested_live_ids: list[str] | None = None, include_deferred: bool = False,
) -> list[tuple[str, str]]:
    listing = run([sys.executable, "scripts/next_task.py", "--list"], repo).stdout
    listed_live_ids = TASK_RE.findall(listing)
    if requested_live_ids:
        listed = set(listed_live_ids)
        values: list[tuple[str, str]] = []
        for live_id in requested_live_ids:
            if live_id not in listed:
                raise RuntimeError(f"requested ASR task is not currently eligible: {live_id}")
            if attempt_is_deferred(repo, live_id) and not include_deferred:
                raise RuntimeError(
                    f"requested ASR task is deferred until corpus tail: {live_id}; "
                    "use --include-deferred only for the final retry phase"
                )
            values.append((f"WI_{live_id}_transcript_import", live_id))
        return values[:limit]
    values: list[tuple[str, str]] = []
    for live_id in listed_live_ids:
        if attempt_is_deferred(repo, live_id) and not include_deferred:
            continue
        if attempt_is_cooling_down(repo, live_id, retry_cooldown_hours):
            continue
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
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--item-timeout-sec", type=int, default=3000)
    parser.add_argument("--retry-cooldown-hours", type=int, default=24)
    parser.add_argument(
        "--live-ids", default="",
        help="Optional comma-separated eligible LIVE ids to retry explicitly",
    )
    parser.add_argument(
        "--include-deferred", action="store_true",
        help="Include videos deferred after two failed checkpoint resumes",
    )
    parser.add_argument("--agent-id", required=True)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        raise SystemExit("cloud ASR batch size must be between 1 and 100")
    if not 300 <= args.item_timeout_sec <= 18000:
        raise SystemExit("cloud ASR item timeout must be between 300 and 18000 seconds")
    if not 0 <= args.retry_cooldown_hours <= 168:
        raise SystemExit("cloud ASR retry cooldown must be between 0 and 168 hours")
    repo = args.repo.resolve()
    work = args.work_root.resolve()
    requested_live_ids = [value.strip() for value in args.live_ids.split(",") if value.strip()]
    if len(requested_live_ids) > args.batch_size:
        raise SystemExit("explicit live-id count cannot exceed batch size")
    tasks = eligible(
        repo, args.batch_size, args.retry_cooldown_hours, requested_live_ids,
        args.include_deferred,
    )
    if not tasks:
        print("No eligible transcript_import tasks.")
        return 0

    total_success = 0
    total_failed = 0
    checkpoint_size = 10
    for checkpoint_number, start in enumerate(range(0, len(tasks), checkpoint_size), start=1):
        checkpoint = tasks[start : start + checkpoint_size]
        # Claim only the checkpoint that is about to run. Reserving the whole
        # logical batch up front leaves dozens of valid claims stranded when a
        # hosted runner reaches GitHub's hard job timeout.
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
            f"claim: reserve GitHub Actions ASR checkpoint {checkpoint_number} of {len(checkpoint)}",
        ], repo)
        push_with_rebase(repo)
        run([sys.executable, "scripts/build_db.py"], repo)

        success: list[tuple[str, str, list[str]]] = []
        failed: list[tuple[str, str, str]] = []
        attempt_paths: list[str] = []
        for task_id, live_id in checkpoint:
            checkpoint_path = f"data/current/asr_checkpoints/asr_{live_id.lower()}"
            checkpoint_root = repo / checkpoint_path
            had_checkpoint = any(checkpoint_root.glob("chunk_*.json"))
            previous_attempt = read_attempt(repo, live_id)
            previous_retry_count = int(previous_attempt.get("checkpoint_retry_count") or 0)
            item_command = [
                sys.executable, "scripts/cloud_asr_item.py", "--repo", str(repo),
                "--live-id", live_id, "--work-root", str(work),
            ]
            try:
                completed = run(
                    item_command, repo, check=False, timeout=args.item_timeout_sec,
                )
            except subprocess.TimeoutExpired as exc:
                if exc.stdout:
                    print(exc.stdout, end="" if str(exc.stdout).endswith("\n") else "\n", flush=True)
                attempt_path = repo / "data" / "current" / "asr_attempts" / f"cloud_{live_id.lower()}.json"
                attempt_path.parent.mkdir(parents=True, exist_ok=True)
                attempt_path.write_text(json.dumps({
                    "schema_version": "cloud-asr-attempt-v1",
                    "live_id": live_id,
                    "status": "cloud_attempt_timed_out_needs_retry",
                    "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                    "processing_location": "github-hosted-macos-arm64",
                    "paid_api_used": False,
                    "media_committed_to_git": False,
                    "error": f"cloud ASR item exceeded {args.item_timeout_sec} seconds; retained for retry or chunked processing",
                }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                completed = subprocess.CompletedProcess(item_command, 124, "")
            stem = f"asr_{live_id.lower()}"
            outputs = [
                f"data/current/transcript_versions/{stem}.jsonl",
                f"data/current/transcript_cues/{stem}.jsonl",
                f"data/current/live_segments/{stem}.jsonl",
                f"data/current/asr_manifests/{stem}.json",
            ]
            if completed.returncode == 0 and all((repo / path).exists() for path in outputs):
                if (repo / checkpoint_path).exists():
                    attempt_paths.append(checkpoint_path)
                success.append((task_id, live_id, outputs))
            else:
                attempt = f"data/current/asr_attempts/cloud_{live_id.lower()}.json"
                retry_count, deferred = record_failed_resume(
                    repo, live_id, previous_retry_count,
                    had_checkpoint and completed.returncode == 124,
                )
                print(json.dumps({
                    "live_id": live_id,
                    "checkpoint_retry_count": retry_count,
                    "deferred_until_corpus_tail": deferred,
                }, ensure_ascii=False), flush=True)
                if (repo / attempt).exists():
                    attempt_paths.append(attempt)
                if (repo / checkpoint_path).exists():
                    attempt_paths.append(checkpoint_path)
                failed.append((task_id, live_id, attempt))

        run([sys.executable, "scripts/build_db.py"], repo)
        run([sys.executable, "scripts/validate_db.py"], repo)
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"], repo)

        completion_paths: list[str] = []
        output_paths: list[str] = []
        for task_id, _live_id, outputs in success:
            run([
                sys.executable, "scripts/next_task.py", "--finish", task_id,
                "--agent-id", args.agent_id, "--outputs", *outputs,
                "--validation", "GitHub-hosted MLX Whisper; build_db OK; validate_db OK; full tests OK; machine ASR remains unverified",
            ], repo)
            completion_paths.append(f"coordination/completed/{task_id}.json")
            output_paths.extend(outputs)
        for task_id, _live_id, _attempt in failed:
            run([
                sys.executable, "scripts/next_task.py", "--release", task_id,
                "--agent-id", args.agent_id,
                "--reason", "GitHub-hosted runner could not complete media access or ASR; retained for retry",
            ], repo)

        checkpoint_claims = [f"coordination/claims/{task_id}.json" for task_id, _live_id in checkpoint]
        stage = sorted(set(output_paths + attempt_paths + completion_paths + checkpoint_claims))
        run(["git", "add", *stage], repo)
        run(["git", "diff", "--cached", "--check"], repo)
        run([
            "git", "commit", "-m",
            f"data: checkpoint cloud ASR batch {checkpoint_number} ({len(success)} transcribed, {len(failed)} retryable)",
        ], repo)
        push_with_rebase(repo)
        total_success += len(success)
        total_failed += len(failed)
        print(json.dumps({
            "checkpoint": checkpoint_number,
            "claimed": len(checkpoint),
            "transcribed": len(success),
            "retryable": len(failed),
        }, ensure_ascii=False), flush=True)

    print(json.dumps({"claimed": len(tasks), "transcribed": total_success, "retryable": total_failed}, ensure_ascii=False))
    return 0 if total_success else 2


if __name__ == "__main__":
    raise SystemExit(main())
