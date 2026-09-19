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
import shutil
import subprocess
import secrets
from datetime import datetime, timezone
from pathlib import Path

import next_task
import playback_queue
import playback_retry_guard


ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / ".agent_session.json"
RESERVATIONS = ROOT / "coordination" / "pr_reservations"
DEFAULT_REMOTE = "origin"


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=check,
    )


def require_clean_checkout() -> None:
    dirty = run_git("status", "--porcelain=v1").stdout.splitlines()
    if dirty:
        raise RuntimeError(
            "automatic entry requires a clean checkout; preserve or commit existing work first: "
            + ", ".join(dirty[:10])
        )


def refresh_main(remote: str = DEFAULT_REMOTE) -> None:
    require_clean_checkout()
    branch = run_git("branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError(f"automatic entry must start on main, not {branch or 'detached HEAD'}")
    run_git("pull", "--ff-only", remote, "main")
    local = run_git("rev-parse", "HEAD").stdout.strip()
    upstream = run_git("rev-parse", f"{remote}/main").stdout.strip()
    if local != upstream:
        raise RuntimeError(
            f"local main ({local[:12]}) is not identical to {remote}/main ({upstream[:12]}); "
            "resolve the unpublished/divergent state before taking another task"
        )


def direct_push_available(remote: str = DEFAULT_REMOTE) -> bool:
    # A dry-run of an already up-to-date ref can succeed without proving write access. Build a
    # metadata-only child commit without moving the worktree, then dry-run that exact update to
    # main. This also exercises main-branch protection rather than generic branch creation.
    tree = run_git("rev-parse", "HEAD^{tree}").stdout.strip()
    probe_commit = run_git(
        "-c", "user.name=agent-permission-probe",
        "-c", "user.email=agent-permission-probe@invalid.local",
        "commit-tree", tree, "-p", "HEAD", "-m", f"permission probe {secrets.token_hex(8)}",
    ).stdout.strip()
    result = run_git("push", "--dry-run", remote, f"{probe_commit}:main", check=False)
    return result.returncode == 0


def gh_available() -> bool:
    if shutil.which("gh") is None:
        return False
    result = subprocess.run(
        ["gh", "auth", "status"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def open_pr_rows(remote: str = DEFAULT_REMOTE) -> list[dict]:
    if not gh_available():
        raise RuntimeError("authenticated GitHub CLI is required for PR-mode reservation checks")
    result = subprocess.run(
        ["gh", "pr", "list", "--repo", github_repository_slug(remote), "--state", "open",
         "--limit", "1000", "--json", "number,url,title,body"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    rows = json.loads(result.stdout)
    if not isinstance(rows, list):
        raise RuntimeError("GitHub CLI returned a non-list pull-request payload")
    return rows


def task_id_from_pr(row: dict) -> str | None:
    text = f"{row.get('title') or ''}\n{row.get('body') or ''}"
    for line in text.splitlines():
        if line.strip().startswith("TASK_ID:"):
            task_id = line.partition(":")[2].strip()
            if task_id:
                return task_id
    if "[TASK " in text:
        task_id = text.partition("[TASK ")[2].partition("]")[0].strip()
        if task_id:
            return task_id
    return None


def open_pr_reservations(remote: str = DEFAULT_REMOTE) -> set[str]:
    reserved: set[str] = set()
    for row in open_pr_rows(remote):
        task_id = task_id_from_pr(row)
        if task_id:
            reserved.add(task_id)
    return reserved


def github_repository_slug(remote: str) -> str:
    url = run_git("remote", "get-url", remote).stdout.strip()
    marker = "github.com"
    if marker not in url:
        raise RuntimeError(f"remote {remote!r} is not a GitHub repository: {url}")
    tail = url.split(marker, 1)[1].lstrip(":/")
    slug = tail.removesuffix(".git").strip("/")
    if slug.count("/") != 1:
        raise RuntimeError(f"cannot derive OWNER/REPO from remote URL: {url}")
    return slug


def github_login() -> str:
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    login = result.stdout.strip()
    if not login:
        raise RuntimeError("authenticated GitHub login is empty")
    return login


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


def playback_entry_allowed() -> bool:
    workflow = next_task.load_workflow()
    return workflow.get("current_major_phase") != "PHASE_1_COLLECTION"


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

    if not playback_entry_allowed():
        emit(
            {
                "entry_status": "NO_LOCAL_CLAIM",
                "agent_id": agent_id,
                "reason": "Playback entry is disabled during PHASE_1_COLLECTION; use scripts/next_task.py --list for ordinary collection work or report the ordinary queue state.",
                "next_required_action": "Do not claim playback work in PHASE_1_COLLECTION. Refresh main and continue only with ordinary eligible tasks.",
            }
        )
        return 1

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


def select_pr_task(agent_id: str, reserved: set[str]) -> str | None:
    ordinary = [task for task in next_task.eligible_tasks() if task["id"] not in reserved]
    if ordinary:
        task = next_task.candidate_order(ordinary, agent_id, None)[0]
        return str(task["id"])
    if not playback_entry_allowed():
        return None
    eligible_playback, _ = playback_entry_candidates(agent_id)
    eligible_playback = [row for row in eligible_playback if str(row.get("task_id")) not in reserved]
    return str(eligible_playback[0]["task_id"]) if eligible_playback else None


def pr_entry(agent_id: str) -> int:
    try:
        reserved = open_pr_reservations()
    except (RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        emit({
            "entry_status": "AUTOMATION_BLOCKED",
            "agent_id": agent_id,
            "reason": f"Cannot safely inspect open PR reservations: {exc}",
        })
        return 2
    task_id = select_pr_task(agent_id, reserved)
    if task_id is None:
        emit({
            "entry_status": "NO_PR_RESERVATION", "agent_id": agent_id,
            "reason": "No unreserved autonomous task is currently eligible.",
        })
        return 1
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


def publish_direct_claim(agent_id: str, max_attempts: int, remote: str) -> int:
    before = set(run_git("status", "--porcelain=v1").stdout.splitlines())
    result = direct_entry(agent_id, max_attempts)
    if result != 0:
        return result
    after = set(run_git("status", "--porcelain=v1").stdout.splitlines())
    paths = [line[3:] for line in after - before if len(line) > 3]
    allowed = (
        "coordination/claims/", "coordination/claim_attempts/",
        "coordination/playback_attempts/",
    )
    if not paths or any(not path.startswith(allowed) for path in paths):
        raise RuntimeError(f"entry produced unexpected paths: {paths}")
    run_git("add", "--", *paths)
    run_git(
        "-c", f"user.name={agent_id}",
        "-c", f"user.email={agent_id}@users.noreply.github.com",
        "commit", "-m", f"claim: autonomous entry for {agent_id}",
    )
    pushed = run_git("push", remote, "HEAD:main", check=False)
    if pushed.returncode != 0:
        emit({
            "entry_status": "PUBLISH_RACE_OR_WRITE_ERROR", "agent_id": agent_id,
            "reason": pushed.stderr.strip(),
            "next_required_action": "Classify the push using CLAIM_PROTOCOL_V2; never force-push.",
        })
        return 2
    emit({
        "entry_status": "DURABLE_CLAIM_PUBLISHED", "agent_id": agent_id,
        "mode": "direct", "commit": run_git("rev-parse", "HEAD").stdout.strip(),
        "next_required_action": "Execute the claimed task, validate it, publish completion, and re-enter.",
    })
    return 0


def publish_pr_reservation(agent_id: str, remote: str) -> int:
    if not gh_available():
        emit({
            "entry_status": "AUTOMATION_BLOCKED", "agent_id": agent_id,
            "reason": "No direct push permission and authenticated gh CLI is unavailable.",
            "stop_condition": "SAFETY_OR_ACCESS_BLOCK",
        })
        return 2
    task_id = select_pr_task(agent_id, open_pr_reservations(remote))
    if task_id is None:
        emit({"entry_status": "NO_ELIGIBLE_WORK", "agent_id": agent_id})
        return 1
    safe_agent = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in agent_id)
    safe_task = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in task_id)
    branch = f"agent/{safe_task}-{safe_agent}"
    run_git("checkout", "-b", branch)
    RESERVATIONS.mkdir(parents=True, exist_ok=True)
    reservation = RESERVATIONS / f"{safe_task}-{safe_agent}.json"
    reservation.write_text(json.dumps({
        "task_id": task_id, "agent_id": agent_id, "mode": "external-pr-worker",
        "reserved_at": datetime.now(timezone.utc).isoformat(),
        "base_commit": run_git("rev-parse", "main").stdout.strip(), "status": "reserved",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    relative = str(reservation.relative_to(ROOT))
    run_git("add", "--", relative)
    run_git(
        "-c", f"user.name={agent_id}",
        "-c", f"user.email={agent_id}@users.noreply.github.com",
        "commit", "-m", f"claim: reserve {task_id} for external Agent",
    )
    fork_remote = "agent-fork"
    fork = subprocess.run(
        ["gh", "repo", "fork", "--remote", "--remote-name", fork_remote],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if fork.returncode != 0 and "already exists" not in fork.stderr.lower():
        raise RuntimeError(f"cannot create or select fork: {fork.stderr.strip()}")
    run_git("push", "-u", fork_remote, branch)
    title = f"[TASK {task_id}] autonomous entry — {agent_id}"
    body = f"TASK_ID: {task_id}\nagent_id: {agent_id}\nmode: external-pr-worker"
    repository = github_repository_slug(remote)
    head = f"{github_login()}:{branch}"
    created = subprocess.run(
        ["gh", "pr", "create", "--repo", repository, "--title", title,
         "--body", body, "--head", head],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if created.returncode != 0:
        raise RuntimeError(f"cannot create reservation PR: {created.stderr.strip()}")
    pull_request_url = created.stdout.strip()
    contenders = [
        row for row in open_pr_rows(remote) if task_id_from_pr(row) == task_id
    ]
    winner = min(contenders, key=lambda row: int(row.get("number") or 0)) if contenders else None
    if winner and str(winner.get("url") or "") != pull_request_url:
        subprocess.run(
            ["gh", "pr", "close", pull_request_url,
             "--comment", "Reservation race lost; closing without performing task work."],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        run_git("checkout", "main")
        run_git("branch", "-D", branch)
        emit({
            "entry_status": "PR_RESERVATION_RACE_LOST", "agent_id": agent_id,
            "task_id": task_id, "winning_pull_request": winner.get("url"),
            "next_required_action": "Re-run automatic entry immediately to reserve another task.",
        })
        return 3
    emit({
        "entry_status": "DURABLE_PR_RESERVATION_PUBLISHED", "agent_id": agent_id,
        "task_id": task_id, "branch": branch, "pull_request": pull_request_url,
        "next_required_action": "Execute the task on this branch and update the same PR.",
    })
    return 0


def automatic_entry(agent_id: str, max_attempts: int, remote: str) -> int:
    try:
        refresh_main(remote)
        if direct_push_available(remote):
            return publish_direct_claim(agent_id, max_attempts, remote)
        for _ in range(max(1, max_attempts)):
            result = publish_pr_reservation(agent_id, remote)
            if result != 3:
                return result
        raise RuntimeError("PR reservation races exhausted the bounded candidate attempts")
    except (RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        emit({
            "entry_status": "AUTOMATION_BLOCKED", "agent_id": agent_id,
            "reason": str(exc),
            "next_required_action": "Preserve current Git state and resolve the reported prerequisite; do not fabricate a claim.",
        })
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomously choose and atomically claim the next Miles-Guo archive task."
    )
    parser.add_argument("--mode", choices=["auto", "direct", "pr"], default="auto")
    parser.add_argument("--agent-id")
    parser.add_argument("--max-claim-attempts", type=int, default=10)
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    args = parser.parse_args()

    agent_id = load_or_create_agent_id(args.agent_id)
    if args.mode == "auto":
        return automatic_entry(agent_id, args.max_claim_attempts, args.remote)
    if args.mode == "direct":
        return direct_entry(agent_id, args.max_claim_attempts)
    return pr_entry(agent_id)


if __name__ == "__main__":
    raise SystemExit(main())
