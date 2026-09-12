from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "coordination" / "WORK_QUEUE.jsonl"
CLAIMS = ROOT / "coordination" / "claims"
COMPLETED = ROOT / "coordination" / "completed"
READY = ROOT / "coordination" / "ready"
PILOT_SELECTION = ROOT / "reports" / "pilot_selection.json"

LEGACY_BATCH_TASKS = {
    "early": "P6-PILOT-EARLY-B001",
    "middle": "P6-PILOT-MIDDLE-B001",
    "late": "P6-PILOT-LATE-B001",
}

STREAM_PRIORITIES = {
    "collect": 76,
    "align": 72,
    "audit": 52,
}


def load_queue() -> list[dict]:
    tasks: list[dict] = []
    if not QUEUE.exists():
        return tasks
    for raw in QUEUE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            tasks.append(json.loads(raw))
    return tasks


def load_pilot_selection() -> dict:
    if not PILOT_SELECTION.exists():
        return {"groups": {}}
    return json.loads(PILOT_SELECTION.read_text(encoding="utf-8"))


def has_record(directory: Path, task_id: str) -> bool:
    return (directory / f"{task_id}.json").exists()


def completed_ids() -> set[str]:
    return {p.stem for p in COMPLETED.glob("*.json") if p.is_file()}


def current_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def stream_task_id(stage: str, case_id: str) -> str:
    return f"S-{stage.upper()}-{case_id}"


def ready_path(stage: str, case_id: str) -> Path:
    return READY / stage / f"{case_id}.json"


def load_ready(stage: str, case_id: str) -> dict | None:
    path = ready_path(stage, case_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def scan_live_ids_for_date(date_hint: str | None) -> list[str]:
    if not date_hint:
        return []
    found: list[str] = []
    for path in (ROOT / "data" / "live_videos").rglob("*.jsonl"):
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if row.get("live_date") == date_hint and row.get("id"):
                found.append(str(row["id"]))
    return sorted(set(found))


def infer_live_id(case: dict) -> str | None:
    marker = load_ready("collection", case["pilot_case_id"])
    if marker and marker.get("live_id"):
        return str(marker["live_id"])
    candidates = scan_live_ids_for_date(case.get("date_hint"))
    if len(candidates) == 1:
        return candidates[0]
    return None


def stream_tasks(done: set[str]) -> list[dict]:
    tasks: list[dict] = []
    selection = load_pilot_selection()

    for group_name, cases in selection.get("groups", {}).items():
        legacy_id = LEGACY_BATCH_TASKS.get(group_name)
        legacy_done = bool(legacy_id and legacy_id in done)
        legacy_active = bool(
            legacy_id
            and has_record(CLAIMS, legacy_id)
            and not legacy_done
        )

        for case in cases:
            case_id = case["pilot_case_id"]
            live_id = infer_live_id(case)

            collect_id = stream_task_id("collect", case_id)
            align_id = stream_task_id("align", case_id)
            audit_id = stream_task_id("audit", case_id)

            collection_ready = (
                ready_path("collection", case_id).exists()
                or legacy_done
                or collect_id in done
            )
            alignment_ready = (
                ready_path("alignment", case_id).exists()
                or align_id in done
            )
            audit_ready = (
                ready_path("audit", case_id).exists()
                or audit_id in done
            )

            common = {
                "case_id": case_id,
                "group": group_name,
                "date_hint": case.get("date_hint"),
                "seed_source_site": case.get("seed_source_site"),
                "seed_source_page_id": case.get("seed_source_page_id"),
                "seed_url": case.get("seed_url"),
                "live_id": live_id,
                "stream_task": True,
            }

            if not collection_ready:
                # Do not duplicate a currently active legacy batch collector.
                # A legacy collector can unlock this case early by writing
                # coordination/ready/collection/<CASE_ID>.json.
                if legacy_active:
                    continue
                tasks.append(
                    {
                        **common,
                        "id": collect_id,
                        "stage": "collect",
                        "priority": STREAM_PRIORITIES["collect"],
                        "scope": (
                            f"Collect and identity-resolve {case_id} "
                            f"({case.get('date_hint')}); write independent source data "
                            "and mark this case collection-ready."
                        ),
                    }
                )
                continue

            if not alignment_ready:
                tasks.append(
                    {
                        **common,
                        "id": align_id,
                        "stage": "align",
                        "priority": STREAM_PRIORITIES["align"],
                        "scope": (
                            f"Align curated/ASR text and public time anchors for {case_id}"
                            + (f" / {live_id}" if live_id else "")
                            + "; write independent per-live segment data."
                        ),
                    }
                )
                continue

            if not audit_ready:
                tasks.append(
                    {
                        **common,
                        "id": audit_id,
                        "stage": "audit",
                        "priority": STREAM_PRIORITIES["audit"],
                        "scope": (
                            f"Playback-audit real segments for {case_id}"
                            + (f" / {live_id}" if live_id else "")
                            + "; record actual timing error and provenance."
                        ),
                    }
                )

    return tasks


def static_tasks(done: set[str]) -> list[dict]:
    eligible: list[dict] = []
    for task in load_queue():
        task_id = task["id"]
        if task_id in done or has_record(COMPLETED, task_id):
            continue
        if has_record(CLAIMS, task_id):
            continue
        if any(dep not in done for dep in task.get("depends_on", [])):
            continue
        eligible.append({**task, "stream_task": False})
    return eligible


def eligible_tasks() -> list[dict]:
    done = completed_ids()
    tasks = stream_tasks(done) + static_tasks(done)
    filtered: list[dict] = []
    seen: set[str] = set()
    for task in tasks:
        task_id = task["id"]
        if task_id in seen:
            continue
        seen.add(task_id)
        if task_id in done or has_record(COMPLETED, task_id):
            continue
        if has_record(CLAIMS, task_id):
            continue
        filtered.append(task)
    filtered.sort(
        key=lambda item: (-int(item.get("priority", 0)), item["id"])
    )
    return filtered


def claim_task(task: dict, agent_id: str) -> Path:
    CLAIMS.mkdir(parents=True, exist_ok=True)
    path = CLAIMS / f"{task['id']}.json"
    payload = {
        "task_id": task["id"],
        "agent_id": agent_id,
        "claimed_at": datetime.now(timezone.utc).isoformat(),
        "base_commit": current_commit(),
        "status": "in_progress",
        "stage": task.get("stage"),
        "case_id": task.get("case_id"),
        "live_id": task.get("live_id"),
        "scope": task.get("scope", ""),
    }
    with path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def finish_task(
    task_id: str,
    agent_id: str,
    outputs: list[str],
    validation: str,
    live_id: str | None,
) -> tuple[Path, Path | None]:
    claim_path = CLAIMS / f"{task_id}.json"
    if not claim_path.exists():
        raise SystemExit(f"Cannot finish {task_id}: claim file does not exist.")
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    if claim.get("agent_id") != agent_id:
        raise SystemExit(
            f"Cannot finish {task_id}: claim belongs to {claim.get('agent_id')!r}."
        )

    COMPLETED.mkdir(parents=True, exist_ok=True)
    completed_path = COMPLETED / f"{task_id}.json"
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "result_commit": current_commit(),
        "outputs": outputs,
        "validation": validation,
        "notes": "Streaming task completed; continue by claiming the next eligible task.",
    }
    with completed_path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    marker_path: Path | None = None
    stage = claim.get("stage")
    case_id = claim.get("case_id")
    resolved_live_id = live_id or claim.get("live_id")

    marker_stage = {
        "collect": "collection",
        "align": "alignment",
        "audit": "audit",
    }.get(stage)

    if marker_stage and case_id:
        if stage == "collect" and not resolved_live_id:
            completed_path.unlink(missing_ok=True)
            raise SystemExit(
                "Collection completion requires --live-id LIVE_YYYYMMDD_NNN."
            )
        marker_path = ready_path(marker_stage, case_id)
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker = {
            "project": "Miles-Guo_public_archive",
            "case_id": case_id,
            "live_id": resolved_live_id,
            "stage": marker_stage,
            "ready_at": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_id": agent_id,
            "result_commit": current_commit(),
            "outputs": outputs,
            "validation": validation,
        }
        with marker_path.open("x", encoding="utf-8") as fh:
            json.dump(marker, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    return completed_path, marker_path


def print_task(task: dict) -> None:
    print(f"{task['id']} [priority={task.get('priority', 0)}]")
    print(f"  {task.get('scope', '')}")
    if task.get("case_id"):
        print(
            "  case="
            f"{task.get('case_id')} live_id={task.get('live_id') or 'unresolved'} "
            f"seed={task.get('seed_url') or '-'}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find, claim, and finish the next Miles-Guo_public_archive task."
    )
    parser.add_argument("--list", action="store_true", help="List eligible tasks.")
    parser.add_argument("--claim", action="store_true", help="Claim an eligible task.")
    parser.add_argument("--task", help="Specific eligible task ID to claim.")
    parser.add_argument("--agent-id", help="Unique agent ID for claim/finish.")
    parser.add_argument("--finish", metavar="TASK_ID", help="Finish a claimed task.")
    parser.add_argument("--outputs", nargs="*", default=[], help="Durable output paths.")
    parser.add_argument("--validation", help="What was actually validated.")
    parser.add_argument("--live-id", help="Canonical live ID, required when finishing collection.")
    args = parser.parse_args()

    if args.finish:
        if not args.agent_id:
            raise SystemExit("--finish requires --agent-id.")
        if not args.validation:
            raise SystemExit("--finish requires --validation.")
        completed_path, marker_path = finish_task(
            task_id=args.finish,
            agent_id=args.agent_id,
            outputs=args.outputs,
            validation=args.validation,
            live_id=args.live_id,
        )
        print(f"Created completion record: {completed_path.relative_to(ROOT)}")
        if marker_path:
            print(f"Created readiness marker: {marker_path.relative_to(ROOT)}")
        print(
            "Commit and push these coordination records, then immediately run "
            "`python scripts/next_task.py --claim --agent-id <same-or-new-id>` "
            "to continue."
        )
        return

    eligible = eligible_tasks()
    if not eligible:
        print("No currently eligible unclaimed task.")
        print(
            "Check active claims for genuine progress/staleness. Do not wait on chat; "
            "if a claim is stale, follow coordination/README.md takeover rules."
        )
        return

    if args.list or not args.claim:
        print("Eligible tasks (highest priority first):")
        for task in eligible:
            print_task(task)

    if not args.claim:
        print("\nRecommended next task:")
        print_task(eligible[0])
        print(
            "\nClaim it with:\n"
            "python scripts/next_task.py --claim --agent-id "
            "agent-<UTC>-<random>"
        )
        return

    if not args.agent_id:
        raise SystemExit("--claim requires --agent-id.")

    chosen = eligible[0]
    if args.task:
        matches = [task for task in eligible if task["id"] == args.task]
        if not matches:
            raise SystemExit(f"Task {args.task!r} is not currently eligible.")
        chosen = matches[0]

    try:
        path = claim_task(chosen, args.agent_id)
    except FileExistsError:
        raise SystemExit(
            f"Claim lost: {chosen['id']} was claimed concurrently. "
            "Pull latest state and run the command again."
        )

    print(f"Claim created locally: {path.relative_to(ROOT)}")
    print_task(chosen)
    print(
        "\nIMPORTANT: immediately commit and push the claim before doing the work. "
        "If push loses a race, remove the local claim, pull, and claim another task."
    )
    print(
        "After the claim is visible on main: execute the task, validate real outputs, "
        "commit/push the outputs, then run --finish. After finishing, claim the next task "
        "instead of stopping."
    )


if __name__ == "__main__":
    main()
