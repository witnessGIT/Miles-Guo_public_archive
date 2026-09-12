from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "coordination" / "WORK_QUEUE.jsonl"
CLAIMS = ROOT / "coordination" / "claims"
COMPLETED = ROOT / "coordination" / "completed"
READY = ROOT / "coordination" / "ready"
PILOT_SELECTION = ROOT / "reports" / "pilot_selection.json"

WORKFLOW_MODE = "continuous-worker-v2"
CLAIM_PROTOCOL = "claim-protocol-v2"

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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def pilot_case_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    selection = load_pilot_selection()
    for group_name, cases in selection.get("groups", {}).items():
        for case in cases:
            index[case["pilot_case_id"]] = {**case, "group": group_name}
    return index


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
    live_root = ROOT / "data" / "live_videos"
    if not live_root.exists():
        return []
    for path in live_root.rglob("*.jsonl"):
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
    for path in live_root.rglob("*.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(row, dict) and row.get("live_date") == date_hint and row.get("id"):
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
    filtered.sort(key=lambda item: (-int(item.get("priority", 0)), item["id"]))
    return filtered


def candidate_order(
    eligible: list[dict],
    agent_id: str,
    requested_task: str | None,
) -> list[dict]:
    """Preserve priority bands while spreading Agents across same-priority tasks."""
    if requested_task:
        matches = [task for task in eligible if task["id"] == requested_task]
        if not matches:
            raise SystemExit(f"Task {requested_task!r} is not currently eligible.")
        return matches

    if not eligible:
        return []

    seed = int(hashlib.sha256(agent_id.encode("utf-8")).hexdigest(), 16)
    bands: dict[int, list[dict]] = defaultdict(list)
    for task in eligible:
        bands[int(task.get("priority", 0))].append(task)

    ordered: list[dict] = []
    for band_index, priority in enumerate(sorted(bands, reverse=True)):
        band = sorted(bands[priority], key=lambda item: item["id"])
        offset = (seed + band_index) % len(band)
        ordered.extend(band[offset:] + band[:offset])
    return ordered


def claim_task(task: dict, agent_id: str) -> Path:
    CLAIMS.mkdir(parents=True, exist_ok=True)
    path = CLAIMS / f"{task['id']}.json"
    payload = {
        "task_id": task["id"],
        "agent_id": agent_id,
        "claimed_at": utc_now(),
        "base_commit": current_commit(),
        "status": "in_progress",
        "workflow_mode": WORKFLOW_MODE,
        "claim_protocol": CLAIM_PROTOCOL,
        "continue_after_finish": True,
        "stage": task.get("stage"),
        "case_id": task.get("case_id"),
        "live_id": task.get("live_id"),
        "scope": task.get("scope", ""),
    }
    with path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def claim_from_candidates(
    eligible: list[dict],
    agent_id: str,
    requested_task: str | None,
    max_attempts: int,
) -> tuple[dict, Path] | None:
    ordered = candidate_order(eligible, agent_id, requested_task)
    if not ordered:
        return None

    attempt_limit = min(len(ordered), max(1, max_attempts))
    for attempt, task in enumerate(ordered[:attempt_limit], start=1):
        try:
            path = claim_task(task, agent_id)
            if attempt > 1:
                print(
                    f"CLAIM_SUCCESS after {attempt} attempts: {task['id']} "
                    f"({attempt - 1} local claim races skipped)."
                )
            return task, path
        except FileExistsError:
            print(
                f"CLAIM_RACE_LOST: {task['id']} already has a claim locally; "
                "trying another eligible task."
            )
            continue

    return None


def create_ready_marker(
    stage: str,
    case_id: str,
    agent_id: str,
    task_id: str,
    outputs: list[str],
    validation: str,
    live_id: str | None,
) -> Path:
    if stage == "collection" and not live_id:
        raise SystemExit("Collection readiness requires --live-id LIVE_YYYYMMDD_NNN.")
    marker_path = ready_path(stage, case_id)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker = {
        "project": "Miles-Guo_public_archive",
        "workflow_mode": WORKFLOW_MODE,
        "case_id": case_id,
        "live_id": live_id,
        "stage": stage,
        "ready_at": utc_now(),
        "task_id": task_id,
        "agent_id": agent_id,
        "result_commit": current_commit(),
        "outputs": outputs,
        "validation": validation,
    }
    with marker_path.open("x", encoding="utf-8") as fh:
        json.dump(marker, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return marker_path


def legacy_task_for_case(case_id: str) -> str | None:
    case = pilot_case_index().get(case_id)
    if not case:
        return None
    return LEGACY_BATCH_TASKS.get(case.get("group"))


def mark_ready_from_legacy(
    stage: str,
    case_id: str,
    agent_id: str,
    outputs: list[str],
    validation: str,
    live_id: str | None,
) -> Path:
    if stage != "collection":
        raise SystemExit(
            "--mark-ready is intended for grandfathered legacy collectors and currently "
            "supports only stage=collection. Streaming align/audit tasks should use --finish."
        )
    if case_id not in pilot_case_index():
        raise SystemExit(f"Unknown Pilot case: {case_id}")
    legacy_task = legacy_task_for_case(case_id)
    if not legacy_task:
        raise SystemExit(f"No legacy batch mapping for {case_id}.")
    claim_path = CLAIMS / f"{legacy_task}.json"
    if not claim_path.exists():
        raise SystemExit(
            f"Cannot publish legacy readiness: active claim {legacy_task} not found."
        )
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    if claim.get("agent_id") != agent_id:
        raise SystemExit(
            f"Cannot publish readiness for {case_id}: legacy claim belongs to "
            f"{claim.get('agent_id')!r}."
        )
    return create_ready_marker(
        stage="collection",
        case_id=case_id,
        agent_id=agent_id,
        task_id=legacy_task,
        outputs=outputs,
        validation=validation,
        live_id=live_id,
    )


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
        "completed_at": utc_now(),
        "result_commit": current_commit(),
        "outputs": outputs,
        "validation": validation,
        "workflow_mode": claim.get("workflow_mode", "legacy-grandfathered"),
        "claim_protocol": claim.get("claim_protocol", "legacy"),
        "continue_after_finish": claim.get("workflow_mode") == WORKFLOW_MODE,
        "notes": (
            "Task completed. Under continuous-worker-v2, refresh repository state and "
            "claim the next eligible task unless a documented stop condition applies."
        ),
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
        marker_path = create_ready_marker(
            stage=marker_stage,
            case_id=case_id,
            agent_id=agent_id,
            task_id=task_id,
            outputs=outputs,
            validation=validation,
            live_id=resolved_live_id,
        )

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


def choose_task(eligible: list[dict], task_id: str | None) -> dict:
    if not eligible:
        raise SystemExit("No currently eligible unclaimed task.")
    if not task_id:
        return eligible[0]
    matches = [task for task in eligible if task["id"] == task_id]
    if not matches:
        raise SystemExit(f"Task {task_id!r} is not currently eligible.")
    return matches[0]


def watch_for_task(
    poll_seconds: int,
    requested_task: str | None,
) -> list[dict]:
    if poll_seconds < 10:
        raise SystemExit("--poll-seconds must be at least 10 to avoid aggressive polling.")
    print(
        f"Watch mode active ({WORKFLOW_MODE}); polling every {poll_seconds}s. "
        "This process can still be stopped by the host platform or Ctrl+C."
    )
    while True:
        eligible = eligible_tasks()
        if requested_task:
            eligible = [task for task in eligible if task["id"] == requested_task]
        if eligible:
            return eligible
        print(f"[{utc_now()}] no eligible task yet; continuing watch")
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover, claim, finish, and stream Miles-Guo_public_archive tasks."
    )
    parser.add_argument("--list", action="store_true", help="List eligible tasks.")
    parser.add_argument("--claim", action="store_true", help="Claim an eligible task.")
    parser.add_argument("--task", help="Specific eligible task ID to claim/watch for.")
    parser.add_argument("--agent-id", help="Unique agent ID for claim/finish/readiness.")
    parser.add_argument("--finish", metavar="TASK_ID", help="Finish a claimed task.")
    parser.add_argument("--outputs", nargs="*", default=[], help="Durable output paths.")
    parser.add_argument("--validation", help="What was actually validated.")
    parser.add_argument("--live-id", help="Canonical live ID, required for collection readiness.")
    parser.add_argument(
        "--mark-ready",
        choices=["collection", "alignment", "audit"],
        help="Publish per-case readiness from a grandfathered legacy collector.",
    )
    parser.add_argument("--case-id", help="Pilot case ID for --mark-ready.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep scanning until eligible work appears; host suspension can still stop it.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=60,
        help="Watch polling interval; minimum 10 seconds, default 60.",
    )
    parser.add_argument(
        "--max-claim-attempts",
        type=int,
        default=10,
        help=(
            "Maximum eligible candidates tried in one local claim cycle after claim races; "
            "default 10."
        ),
    )
    args = parser.parse_args()

    if args.mark_ready:
        if not args.agent_id or not args.case_id or not args.validation:
            raise SystemExit(
                "--mark-ready requires --agent-id, --case-id, and --validation."
            )
        marker = mark_ready_from_legacy(
            stage=args.mark_ready,
            case_id=args.case_id,
            agent_id=args.agent_id,
            outputs=args.outputs,
            validation=args.validation,
            live_id=args.live_id,
        )
        print(f"Created readiness marker: {marker.relative_to(ROOT)}")
        print(
            "Commit/push this marker now. It unlocks downstream work for this case "
            "without ending the active legacy batch claim."
        )
        return

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
            "Commit and push these coordination records, refresh repository state, then "
            "immediately claim the next eligible task. Finishing one task is not a stop "
            "condition under continuous-worker-v2."
        )
        return

    if args.watch:
        eligible = watch_for_task(args.poll_seconds, args.task)
    else:
        eligible = eligible_tasks()

    if not eligible:
        print("No currently eligible unclaimed task.")
        print(
            "Do not invent work. Check active claims for progress/staleness and follow "
            "coordination/README.md. A repository cannot wake a suspended host session."
        )
        return

    if args.list or (not args.claim and not args.watch):
        print("Eligible tasks (highest priority first):")
        for task in eligible:
            print_task(task)

    if not args.claim:
        print("\nRecommended next task:")
        print_task(choose_task(eligible, args.task))
        print(
            "\nClaim it with:\n"
            "python scripts/next_task.py --claim --agent-id agent-<UTC>-<random>"
        )
        return

    if not args.agent_id:
        raise SystemExit("--claim requires --agent-id.")

    claimed = claim_from_candidates(
        eligible=eligible,
        agent_id=args.agent_id,
        requested_task=args.task,
        max_attempts=args.max_claim_attempts,
    )
    if not claimed:
        raise SystemExit(
            "CLAIM_RACE_LOST: all attempted local candidates became unavailable. "
            "Refresh/pull repository state and run --claim again. This is not a "
            "GITHUB_WRITE_ERROR and not a reason to stop the continuous worker."
        )

    chosen, path = claimed
    print(f"Claim created locally: {path.relative_to(ROOT)}")
    print_task(chosen)
    print(
        f"  workflow_mode={WORKFLOW_MODE} claim_protocol={CLAIM_PROTOCOL} "
        "continue_after_finish=true"
    )
    print(
        "\nIMPORTANT: immediately commit and push the claim before doing the work. "
        "If the remote push/create loses a race, verify the exact remote claim path. "
        "If it now exists, classify CLAIM_RACE_LOST, refresh main, and claim another task."
    )
    print(
        "For GitHub API create_file: HTTP 422 is not automatically a write outage. "
        "Fetch coordination/claims/<TASK_ID>.json first; if it exists, another Agent won. "
        "Only call it GITHUB_WRITE_ERROR after the exact path remains absent across fresh, "
        "bounded retries as documented in coordination/CLAIM_PROTOCOL_V2.md."
    )
    print(
        "After the claim is visible on main: execute the task, validate real outputs, "
        "commit/push outputs, then run --finish. After finishing, refresh and claim the "
        "next task. Stop only for a documented continuous-worker-v2 stop condition."
    )


if __name__ == "__main__":
    main()
